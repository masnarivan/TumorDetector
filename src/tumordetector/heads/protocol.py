"""Validation protocol of a head on its cohort's development slides (experiment E6).

  cv      the cohort's folds; their out-of-fold logits give the head's one global temperature
  loco    one centre out at a time, both datasets; its temperature comes from inner folds of the
          training centres only, so the held-out centre never calibrates itself
  final   one model on every development slide, with the global temperature
  robust  on the final model: linear probe of the centre from the slide representation z, and the
          Robustness Index on the tile representations h

External slides are never passed in: the locked test is read by its own task, once per version.
A run that cannot be trained (one class only) is reported with its reason, never silently skipped.
"""
import numpy as np
import pandas as pd
import torch
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from tumordetector.mil.abmil import ABMIL, fit, predict_logits
from tumordetector.mil.evaluate import attention_auroc, binary_metrics

RI_K, RI_TILES = 10, 100        # neighbours; tiles per class per slide (as in experiment E2)
T_RANGE = (0.05, 20.0)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.asarray(x, dtype=float)))


def fit_temperature(logits: np.ndarray, y: np.ndarray) -> float:
    """The T minimising the negative log-likelihood of sigmoid(logit / T)."""
    logits, y = np.asarray(logits, dtype=float), np.asarray(y, dtype=float)

    def nll(log_t):
        z = logits / np.exp(log_t)
        return float(np.mean(np.maximum(z, 0) - z * y + np.log1p(np.exp(-np.abs(z)))))   # stable BCE

    res = minimize_scalar(nll, bounds=tuple(np.log(T_RANGE)), method="bounded")
    return float(np.exp(res.x))


def slide_representations(model: ABMIL, bags: list[np.ndarray], device: str = "cpu") -> np.ndarray:
    with torch.inference_mode():
        return np.stack([model.encode(torch.from_numpy(b.astype(np.float32)).to(device))[2].cpu().numpy()
                         for b in bags])


def center_probe(z: np.ndarray, center: np.ndarray, patient: np.ndarray, seed: int) -> float | None:
    """Multinomial logistic regression z -> centre, 5 folds grouped by patient and stratified by
    centre: out-of-fold AUROC, macro one-vs-rest. 0.5 = the centre is not linearly readable."""
    classes = np.unique(center)
    if len(classes) < 2 or len(center) < 10:
        return None
    proba = np.zeros((len(center), len(classes)))
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in splitter.split(z, center, groups=patient):
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(z[tr], center[tr])
        cols = np.searchsorted(classes, model.classes_)
        proba[np.ix_(te, cols)] = model.predict_proba(z[te])
    if len(classes) == 2:
        return float(roc_auc_score(center == classes[1], proba[:, 1]))
    return float(roc_auc_score(center, proba, multi_class="ovr", average="macro", labels=classes))


def robustness_index(h: np.ndarray, tumor: np.ndarray, slide: np.ndarray, center: np.ndarray,
                     k: int = RI_K) -> dict:
    """k nearest neighbours by cosine from other slides; RI = same class & other centre / other
    class & same centre (de Jong et al., 2025; as in experiment E2). RI > 1: biology dominates."""
    z = torch.nn.functional.normalize(torch.from_numpy(np.asarray(h, dtype=np.float32)), dim=1)
    s = torch.from_numpy(slide)
    nn = []
    for a in range(0, len(z), 1024):
        sims = z[a:a + 1024] @ z.T
        sims[s[a:a + 1024, None] == s[None, :]] = -2.0     # never a neighbour from the same slide
        nn.append(sims.topk(k, dim=1).indices.numpy())
    nn = np.concatenate(nn)
    same_class, same_center = tumor[nn] == tumor[:, None], center[nn] == center[:, None]
    so, os_ = int((same_class & ~same_center).sum()), int((~same_class & same_center).sum())
    return {"n_tiles": int(len(h)), "ri": so / max(os_, 1), "same_center_fraction": float(same_center.mean()),
            "same_class_fraction": float(same_class.mean())}


def robustness(model: ABMIL, table: pd.DataFrame, bags: dict, tile_labels, seed: int, device: str = "cpu") -> dict:
    """Centre probe (negatives: primary, as composition differs by centre; all slides: secondary) and
    Robustness Index on h of tiles whose label is complete (negatives, exhaustively annotated)."""
    model = model.eval()
    z = slide_representations(model, [bags[s] for s in table.slide_id], device)
    neg = (table.label == 0).to_numpy()
    out = {"center_probe_auroc": center_probe(z[neg], table.center.to_numpy()[neg],
                                              table.patient_pseudo_id.to_numpy()[neg], seed),
           "center_probe_auroc_all": center_probe(z, table.center.to_numpy(), table.patient_pseudo_id.to_numpy(), seed)}

    rng = np.random.default_rng(seed)
    hs, tumor, slide, center = [], [], [], []
    for i, r in enumerate(table.itertuples()):
        if not (r.label == 0 or r.exhaustive_annot):
            continue
        labels = tile_labels(r.slide_id)
        for lab in ("tumor", "normal"):
            cand = np.flatnonzero(labels == lab)
            if not len(cand):
                continue
            pick = np.sort(rng.choice(cand, min(RI_TILES, len(cand)), replace=False))
            with torch.inference_mode():
                hs.append(model.embed(torch.from_numpy(bags[r.slide_id][pick].astype(np.float32)).to(device)).cpu().numpy())
            tumor.append(np.full(len(pick), lab == "tumor"))
            slide.append(np.full(len(pick), i))
            center.append(np.full(len(pick), r.center, dtype=object))
    tumor = np.concatenate(tumor) if tumor else np.zeros(0, dtype=bool)
    if tumor.any() and (~tumor).any() and len(set(table.center)) > 1:
        ri = robustness_index(np.concatenate(hs), tumor, np.concatenate(slide), np.concatenate(center))
        out.update({"robustness_index": ri["ri"], "ri_same_center_fraction": ri["same_center_fraction"],
                    "ri_tiles": ri["n_tiles"]})
    else:
        out.update({"robustness_index": None, "ri_same_center_fraction": None, "ri_tiles": int(len(tumor))})
    return out


def run_head_protocol(table: pd.DataFrame, bags: dict, tile_labels, cfg, seed: int, inner_folds: int) -> dict:
    """`table`: one row per development slide with embeddings (slide_id, label, center, domain,
    dataset, patient_pseudo_id, cv_fold, exhaustive_annot). `cfg`: the mil section."""
    if (table.role != "dev").any():
        raise ValueError("only development slides enter the protocol: the external test is read on its own")
    t = table.set_index("slide_id")
    runs, preds, att_scores = [], [], []

    def train_score(train_ids: list, test_ids: list, name: str, group: str, keep: bool = True):
        """-> (model, logits) or (None, None) if it cannot be trained."""
        info = {"group": group, "name": name, "n_train": len(train_ids), "n_test": len(test_ids),
                "status": "ok", "reason": ""}
        if not test_ids or t.label[train_ids].nunique() < 2:
            runs.append({**info, "status": "skipped",
                         "reason": "no slide to score" if not test_ids else "training slides of one class only"})
            return None, None
        model = fit([bags[s] for s in train_ids], t.label[train_ids].to_numpy(), cfg, seed, cfg.device)
        logits, att = predict_logits(model, [bags[s] for s in test_ids], cfg.device)
        runs.append(info)
        if keep:
            for sid, a in zip(test_ids, att, strict=True):   # localisation only where annotation is complete
                if t.label[sid] != 1 or not t.exhaustive_annot[sid]:
                    continue
                if (s := attention_auroc(a, tile_labels(sid))) is not None:
                    att_scores.append({"slide_id": sid, "group": group, "attention_auroc": s})
        return model, logits

    def record(test_ids, logits, temperature, name, group):
        preds.append(pd.DataFrame({"slide_id": test_ids, "evaluation": name, "group": group,
                                   "y": t.label[test_ids].to_numpy(), "logit": logits, "temperature": temperature,
                                   "p_raw": sigmoid(logits), "p": sigmoid(np.asarray(logits) / temperature)}))

    oof_ids, oof_logits = [], []
    for k in sorted(table.cv_fold.unique()):
        test_ids = list(table[table.cv_fold == k].slide_id)
        _, logits = train_score(list(table[table.cv_fold != k].slide_id), test_ids, f"fold{k}", "cv")
        if logits is not None:
            oof_ids += test_ids
            oof_logits.append(logits)
    temperatures = {}
    if oof_logits:
        oof_logits = np.concatenate(oof_logits)
        temperatures["global"] = fit_temperature(oof_logits, t.label[oof_ids].to_numpy())
        record(oof_ids, oof_logits, temperatures["global"], "cv", "cv")

    for c in sorted(table.center.unique()):
        train = table[table.center != c]
        inner_ids, inner_logits = [], []
        for j in range(inner_folds):        # the temperature of this rotation, from its training centres
            fold = train.cv_fold % inner_folds == j
            ids = list(train[fold].slide_id)
            _, logits = train_score(list(train[~fold].slide_id), ids, f"held-out {c}, inner {j}", "loco-calibration",
                                    keep=False)
            if logits is not None:
                inner_ids += ids
                inner_logits.append(logits)
        test_ids = list(table[table.center == c].slide_id)
        _, logits = train_score(list(train.slide_id), test_ids, f"held-out {c}", "loco")
        if logits is not None and inner_logits:
            temperatures[f"held-out {c}"] = fit_temperature(np.concatenate(inner_logits), t.label[inner_ids].to_numpy())
            record(test_ids, logits, temperatures[f"held-out {c}"], f"held-out {c}", "loco")

    final = None
    if table.label.nunique() == 2:
        final = fit([bags[s] for s in table.slide_id], table.label.to_numpy(), cfg, seed, cfg.device)
        runs.append({"group": "final", "name": "all development slides", "n_train": len(table), "n_test": 0,
                     "status": "ok", "reason": ""})

    cols = ["slide_id", "evaluation", "group", "y", "logit", "temperature", "p_raw", "p"]
    preds = pd.concat(preds) if preds else pd.DataFrame(columns=cols)
    preds = preds.merge(table[["slide_id", "center", "domain", "dataset"]], on="slide_id")

    def metrics(g: pd.DataFrame, col: str = "p") -> dict:
        return binary_metrics(g.y, g[col], cfg.threshold) if len(g) else {}

    cv, loco = preds[preds.group == "cv"], preds[preds.group == "loco"]
    loco_cal = {k: metrics(g) for k, g in loco.groupby("evaluation")}
    loco_raw = {k: metrics(g, "p_raw") for k, g in loco.groupby("evaluation")}

    def worst(d: dict, key: str, fn):
        """Worst held-out centre; None unless every centre was measured."""
        values = [m[key] for m in d.values() if m.get(key) is not None]
        return fn(values) if len(values) == table.center.nunique() > 1 else None

    att = pd.DataFrame(att_scores, columns=["slide_id", "group", "attention_auroc"])
    return {
        "n_dev": int(len(table)), "runs": runs, "predictions": preds, "attention": att, "model": final,
        "temperature": temperatures.get("global"),
        "metrics": {
            "cv": metrics(cv), "cv_raw": metrics(cv, "p_raw"),
            "cv_by_center": {k: metrics(g) for k, g in cv.groupby("center")},
            "cv_by_domain": {k: metrics(g) for k, g in cv.groupby("domain")},
            "loco": loco_cal, "loco_raw": loco_raw,
            "loco_by_domain": {k: {d: metrics(gd) for d, gd in g.groupby("domain")}
                               for k, g in loco.groupby("evaluation")},
            "loco_worst_auroc": worst(loco_cal, "auroc", min),
            "loco_worst_ece": worst(loco_cal, "ece", max),
            "loco_worst_ece_raw": worst(loco_raw, "ece", max),
            "loco_worst_specificity": worst(loco_cal, "specificity", min),
            "temperature": temperatures,
            "robustness": robustness(final, table, bags, tile_labels, seed, cfg.device) if final is not None else {},
            "attention_auroc_mean": float(att[att.group == "cv"].attention_auroc.mean())
            if (att.group == "cv").any() else None,
        },
    }


def head_gate(metrics: dict, n_slides: int, gate) -> dict:
    """Promotion verdict of a head: 'passed', 'failed' or 'insufficient_data', with reasons in Italian."""
    if n_slides < gate.min_slides:
        return {"status": "insufficient_data",
                "reasons": [f"{n_slides} vetrini, ne servono almeno {gate.min_slides}: "
                            "questa esecuzione verifica solo che il codice funzioni"]}
    rob = metrics.get("robustness", {})
    checks = [
        ("AUROC in cross-validation", metrics["cv"].get("auroc"), ">=", gate.min_cv_auroc),
        ("AUROC peggiore in leave-one-center-out", metrics["loco_worst_auroc"], ">=", gate.min_loco_worst_auroc),
        ("ECE calibrata in cross-validation", metrics["cv"].get("ece"), "<=", gate.max_ece),
        ("ECE calibrata peggiore in leave-one-center-out", metrics["loco_worst_ece"], "<=", gate.max_loco_ece),
        ("Specificità peggiore in leave-one-center-out", metrics["loco_worst_specificity"], ">=",
         gate.min_loco_specificity),
        ("AUROC del probe sul centro (vetrini negativi)", rob.get("center_probe_auroc"), "<=",
         gate.max_center_probe_auroc),
        ("Robustness Index", rob.get("robustness_index"), ">=", gate.min_robustness_index),
    ]
    reasons = []
    for name, value, op, limit in checks:
        if value is None:
            reasons.append(f"{name}: non misurabile")
        elif (value < limit) if op == ">=" else (value > limit):
            reasons.append(f"{name} {value:.3f}, richiesto {op} {limit}")
    return {"status": "failed" if reasons else "passed", "reasons": reasons}
