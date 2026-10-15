"""Validation protocol for a slide-level model: fixed splits in, metrics and a gate verdict out.

Three evaluations, all on embeddings that already exist:
  cv    k-fold cross-validation inside the development split, folds read from the versioned
        splits file (stratified by label and centre, grouped by patient)
  loco  leave-one-centre-out inside the development split: the worst centre is what counts
  test  one model trained on the whole development split, scored once on the held-out split

A fold that cannot be trained or scored is reported with its reason, never silently skipped.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

from tumordetector.mil.abmil import fit, predict


def make_cv_folds(manifest: pd.DataFrame, n_folds: int, seed: int) -> pd.DataFrame:
    """Fold of every development-split slide; held-out slides get fold -1."""
    dev = manifest[manifest.split == "train"]
    strata = dev.label.astype(str) + "_" + dev.center
    folds = pd.Series(-1, index=manifest.index)
    splitter = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    for k, (_, test) in enumerate(splitter.split(dev, strata, groups=dev.patient_pseudo_id)):
        folds.loc[dev.index[test]] = k
    return pd.DataFrame({"slide_id": manifest.slide_id, "cv_fold": folds})


def ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error: mean |observed positive rate - mean probability| over
    equal-width probability bins, weighted by bin size."""
    idx = np.minimum((p * bins).astype(int), bins - 1)
    return float(sum((idx == b).mean() * abs(y[idx == b].mean() - p[idx == b].mean())
                     for b in range(bins) if (idx == b).any()))


def binary_metrics(y: np.ndarray, p: np.ndarray, threshold: float = 0.5) -> dict:
    y, p = np.asarray(y).astype(int), np.asarray(p, dtype=float)
    pred, pos, neg = p >= threshold, y == 1, y == 0
    both = pos.any() and neg.any()
    sens = float(pred[pos].mean()) if pos.any() else None
    spec = float((~pred[neg]).mean()) if neg.any() else None
    return {"n": int(len(y)), "n_pos": int(pos.sum()),
            "auroc": float(roc_auc_score(y, p)) if both else None,   # undefined with one class
            "sensitivity": sens, "specificity": spec,
            "balanced_accuracy": (sens + spec) / 2 if both else None,
            "brier": float(np.mean((p - y) ** 2)), "ece": ece(y, p)}


def attention_auroc(attention: np.ndarray, tile_labels: np.ndarray) -> float | None:
    """Does attention rank tumor tiles above normal ones? Boundary tiles are left out."""
    keep = np.isin(tile_labels, ["tumor", "normal"])
    y = tile_labels[keep] == "tumor"
    return float(roc_auc_score(y, attention[keep])) if y.any() and (~y).any() else None


def _run(table: pd.DataFrame, bags: dict, train_ids, test_ids, cfg, seed: int, name: str):
    """Train on train_ids, score test_ids. -> (status dict, predictions, model, attention by slide)."""
    y = table.set_index("slide_id").label
    info = {"name": name, "n_train": len(train_ids), "n_test": len(test_ids), "status": "ok", "reason": ""}
    if len(test_ids) == 0:
        return {**info, "status": "skipped", "reason": "no slide to score"}, None, None, {}
    if y[train_ids].nunique() < 2:
        return {**info, "status": "skipped", "reason": "training slides of one class only"}, None, None, {}
    model = fit([bags[s] for s in train_ids], y[train_ids].to_numpy(), cfg, seed, cfg.device)
    p, att = predict(model, [bags[s] for s in test_ids], cfg.device)
    preds = pd.DataFrame({"slide_id": test_ids, "evaluation": name, "y": y[test_ids].to_numpy(), "p": p})
    return info, preds, model, dict(zip(test_ids, att, strict=True))


def run_protocol(table: pd.DataFrame, bags: dict, tile_labels, cfg, seed: int) -> dict:
    """`table`: one row per slide WITH embeddings (slide_id, label, center, split, cv_fold,
    exhaustive_annot). `tile_labels(slide_id)` -> array of tile labels, for the attention check."""
    dev, held_out = table[table.split == "train"], table[table.split == "test"]
    runs, preds, att_scores = [], [], []

    def record(info, p, att, group: str):
        runs.append({"group": group, **info})
        if p is None:
            return
        preds.append(p.assign(group=group))
        for sid, a in att.items():   # localisation only where the annotation is complete
            row = table.set_index("slide_id").loc[sid]
            if row.label == 1 and row.exhaustive_annot and (s := attention_auroc(a, tile_labels(sid))) is not None:
                att_scores.append({"slide_id": sid, "group": group, "attention_auroc": s})

    for k in sorted(dev.cv_fold.unique()):
        test_ids = list(dev[dev.cv_fold == k].slide_id)
        info, p, _, att = _run(table, bags, list(dev[dev.cv_fold != k].slide_id), test_ids, cfg, seed, f"fold{k}")
        record(info, p, att, "cv")
    for c in sorted(dev.center.unique()):
        info, p, _, att = _run(table, bags, list(dev[dev.center != c].slide_id), list(dev[dev.center == c].slide_id),
                               cfg, seed, f"held-out {c}")
        record(info, p, att, "loco")
    info, p, final, att = _run(table, bags, list(dev.slide_id), list(held_out.slide_id), cfg, seed, "held-out split")
    record(info, p, att, "test")
    if final is None and dev.label.nunique() == 2:   # nothing to score, but the model is still wanted
        final = fit([bags[s] for s in dev.slide_id], dev.label.to_numpy(), cfg, seed, cfg.device)

    preds = pd.concat(preds) if preds else pd.DataFrame(columns=["slide_id", "evaluation", "y", "p", "group"])
    preds = preds.merge(table[["slide_id", "center"]], on="slide_id")

    def group_metrics(group: str, by: str | None = None) -> dict:
        g = preds[preds.group == group]
        if by is None:
            return binary_metrics(g.y, g.p, cfg.threshold) if len(g) else {}
        return {str(k): binary_metrics(v.y, v.p, cfg.threshold) for k, v in g.groupby(by)}

    loco = group_metrics("loco", "evaluation")

    def loco_worst(key: str, worst):
        """Worst held-out centre for one metric; None unless every centre was measured."""
        values = [m[key] for m in loco.values() if m.get(key) is not None]
        return worst(values) if len(values) == dev.center.nunique() > 1 else None

    att = pd.DataFrame(att_scores, columns=["slide_id", "group", "attention_auroc"])
    return {
        "n_slides": int(len(table)), "n_dev": int(len(dev)), "n_held_out": int(len(held_out)),
        "runs": runs, "predictions": preds, "attention": att, "model": final,
        "metrics": {
            "cv": group_metrics("cv"),                       # pooled out-of-fold predictions
            "cv_by_center": group_metrics("cv", "center"),
            "loco": loco,
            "loco_worst_auroc": loco_worst("auroc", min),
            "loco_worst_ece": loco_worst("ece", max),
            "loco_worst_specificity": loco_worst("specificity", min),
            "test": group_metrics("test"),
            "test_by_center": group_metrics("test", "center"),
            "attention_auroc_mean": float(att[att.group == "cv"].attention_auroc.mean())
            if (att.group == "cv").any() else None,
        },
    }


def gate(metrics: dict, n_slides: int, cfg) -> dict:
    """Promotion verdict: 'passed', 'failed' or 'insufficient_data', each with its reasons
    (in Italian: they go straight into the report)."""
    if n_slides < cfg.min_slides:
        return {"status": "insufficient_data",
                "reasons": [f"{n_slides} vetrini, ne servono almeno {cfg.min_slides}: "
                            "questa esecuzione verifica solo che il codice funzioni"]}
    checks = [
        ("AUROC in cross-validation", metrics["cv"].get("auroc"), ">=", cfg.min_cv_auroc),
        ("AUROC peggiore in leave-one-center-out", metrics["loco_worst_auroc"], ">=", cfg.min_loco_worst_auroc),
        ("AUROC sullo split di test bloccato", metrics["test"].get("auroc"), ">=", cfg.min_test_auroc),
        ("ECE in cross-validation", metrics["cv"].get("ece"), "<=", cfg.max_ece),
        # A centre never seen in training: the score must stay calibrated and the normals normal.
        ("ECE peggiore in leave-one-center-out", metrics["loco_worst_ece"], "<=", cfg.max_loco_ece),
        ("Specificità peggiore in leave-one-center-out", metrics["loco_worst_specificity"], ">=",
         cfg.min_loco_specificity),
    ]
    reasons = []
    for name, value, op, limit in checks:
        if value is None:
            reasons.append(f"{name}: non misurabile")
        elif (value < limit) if op == ">=" else (value > limit):
            reasons.append(f"{name} {value:.3f}, richiesto {op} {limit}")
    return {"status": "failed" if reasons else "passed", "reasons": reasons}


def _leaves(d: dict, prefix: str = "") -> dict:
    """Nested metrics -> {"loco/held-out radboud/ece": value} for every number or None."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_leaves(v, f"{prefix}{k}/"))
        elif v is None or isinstance(v, (int, float)):
            out[prefix + k] = v
    return out


def _nest(flat: dict) -> dict:
    out = {}
    for path, v in flat.items():
        *parents, leaf = path.split("/")
        node = out
        for p in parents:
            node = node.setdefault(p, {})
        node[leaf] = v
    return out


def across_seeds(per_seed: list[dict]) -> tuple[dict, dict]:
    """Metrics of several seeds -> (mean metrics, same shape as one seed's; spread per metric path:
    mean, sd, min, max and the value of every seed). A metric missing in any seed is None."""
    flat = [_leaves(m) for m in per_seed]
    mean, spread = {}, {}
    for path in flat[0]:
        values = [f.get(path) for f in flat]
        if any(v is None for v in values):
            mean[path] = None
            continue
        a = np.asarray(values, dtype=float)
        mean[path] = int(a[0]) if path.endswith(("/n", "/n_pos")) else float(a.mean())
        spread[path] = {"mean": float(a.mean()), "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
                        "min": float(a.min()), "max": float(a.max()), "values": a.tolist()}
    return _nest(mean), spread
