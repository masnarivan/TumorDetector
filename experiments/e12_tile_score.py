"""E12: a slide score from its most suspicious tiles, with the criterion fixed in docs/esperimenti.md.

Two steps. (1) The tile classifier: per seed and leave-one-centre-out rotation, a logistic regression
tumour/normal on the tile embeddings of the training centres (inner folds for their calibration scores),
scoring every tile; the top 20 per slide go to data/reports/experiments/e12/tile_classifier.csv (cached).
(2) Needs the E6 rerun with the top instance logits (experiments/e12_run.sh): the comparison of the slide
logit, the ABMIL instance top-k and the classifier top-k -> data/reports/experiments/e12/summary.md.
"""
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

E12 = Path("data/reports/experiments/e12")
RERUN = E12 / "e6"
E6 = Path("data/reports/phikon/heads/ln_metastasis/predictions.csv")
COHORT = Path("data/manifests/heads/ln_metastasis.csv")
MANIFESTS = [Path("data/manifests/camelyon16.csv"), Path("data/manifests/camelyon17.csv")]
ROOTS = {"camelyon16": Path("data/embeddings/phikon"), "camelyon17": Path("data/camelyon17/embeddings/phikon")}
CLASSIFIER = E12 / "tile_classifier.csv"
SEEDS = [0, 1, 2]
INNER = 3                       # inner folds: cv_fold mod 3, as in E6
TOP = 20                        # top tile scores kept per slide
K_MAIN, KS = 5, [1, 5, 20]
TUMOR_PER_SLIDE, NORMAL_PER_SLIDE = 500, 200
C = 1.0
SENS_TARGET = 0.95              # tau keeps this share of the training centres' positives above it
MICRO_GAIN, SPEC_LOSS, AUROC_LOSS, TIE = 0.10, 0.05, 0.01, 0.02
BLIND_SPOT = ["patient_068_node_1", "patient_064_node_0", "patient_067_node_4", "patient_060_node_3",
              "patient_021_node_3"]   # C17 §1: less than 90% of the annotated tumour in a tile (development only)
LOGIT, INSTANCE, CLASSIF = "logit del vetrino", "istanza ABMIL", "classificatore di tile"


def load_table() -> pd.DataFrame:
    cohort = pd.read_csv(COHORT)
    annot = pd.concat(pd.read_csv(m) for m in MANIFESTS)[["slide_id", "exhaustive_annot"]]
    return cohort[cohort.role == "dev"].merge(annot, on="slide_id", validate="one_to_one").reset_index(drop=True)


def tile_labels(row) -> np.ndarray:
    return pd.read_parquet(ROOTS[row.dataset] / f"{row.slide_id}.parquet").label.to_numpy()


def bag(row) -> np.ndarray:
    return np.load(ROOTS[row.dataset] / f"{row.slide_id}.npy", mmap_mode="r")


def sample_tiles(table: pd.DataFrame) -> dict:
    """seed -> slide_id -> (tile embeddings, 1 tumour / 0 normal): one read of every slide for all seeds.
    Tumour tiles only from annotated positives; normal tiles only from negatives; boundary tiles never."""
    out = {s: {} for s in SEEDS}
    for row in table.itertuples():
        if row.label == 1 and not row.exhaustive_annot:
            continue
        labels = tile_labels(row)
        pool = np.flatnonzero(labels == ("tumor" if row.label == 1 else "normal"))
        cap = TUMOR_PER_SLIDE if row.label == 1 else NORMAL_PER_SLIDE
        x = bag(row)
        for seed in SEEDS:
            rng = np.random.default_rng([seed, int.from_bytes(row.slide_id.encode()[:8], "little")])
            idx = np.sort(rng.choice(pool, min(cap, len(pool)), replace=False)) if len(pool) else pool
            out[seed][row.slide_id] = (np.asarray(x[idx], dtype=np.float32), np.full(len(idx), row.label))
    return out


def fit_folded(samples: dict, ids: list, seed: int) -> tuple[np.ndarray, float]:
    """Standardised L2 logistic regression, folded into one linear map: score = x @ w + b (tile log-odds)."""
    xs = [samples[s][0] for s in ids if s in samples]
    ys = [samples[s][1] for s in ids if s in samples]
    x, y = np.concatenate(xs), np.concatenate(ys)
    sc = StandardScaler().fit(x)
    lr = LogisticRegression(C=C, class_weight="balanced", max_iter=1000, random_state=seed)
    lr.fit(sc.transform(x), y)
    w = lr.coef_[0] / sc.scale_
    return w.astype(np.float32), float(lr.intercept_[0] - (sc.mean_ * w).sum())


def classifier_tops(table: pd.DataFrame) -> pd.DataFrame:
    """Every slide scored, in every rotation, by the one model that never saw it: the rotation's model for
    the held-out centre (`loco`), the inner-fold model for the training centres (`loco-calibration`)."""
    t0 = time.time()
    samples = sample_tiles(table)
    print(f"tiles sampled in {time.time() - t0:.0f} s", file=sys.stderr)
    models, cols = [], []           # (seed, centre, inner fold or None)
    for seed in SEEDS:
        for c in sorted(table.center.unique()):
            train = table[table.center != c]
            for j in range(INNER):
                models.append(fit_folded(samples[seed], list(train[train.cv_fold % INNER != j].slide_id), seed))
                cols.append((seed, c, j))
            models.append(fit_folded(samples[seed], list(train.slide_id), seed))
            cols.append((seed, c, None))
            print(f"seed {seed}, held-out {c}: fitted ({time.time() - t0:.0f} s)", file=sys.stderr)
    w = np.stack([m[0] for m in models], axis=1)
    b = np.array([m[1] for m in models], dtype=np.float32)
    col = {key: i for i, key in enumerate(cols)}
    rows, t1 = [], time.time()
    for row in table.itertuples():
        scores = np.asarray(bag(row), dtype=np.float32) @ w + b
        for seed in SEEDS:
            for c in sorted(table.center.unique()):
                held = row.center == c
                i = col[(seed, c, None if held else row.cv_fold % INNER)]
                s = scores[:, i]
                top = np.argsort(-s)[:TOP]
                rows.append(pd.DataFrame({"slide_id": row.slide_id, "evaluation": f"held-out {c}",
                                          "group": "loco" if held else "loco-calibration", "seed": seed,
                                          "rank": np.arange(len(top)), "tile": top, "logit": s[top]}))
    per_slide = (time.time() - t1) / len(table) / len(cols)
    print(f"scored in {time.time() - t1:.0f} s ({per_slide * 1000:.2f} ms per slide and model)", file=sys.stderr)
    out = pd.concat(rows)
    out.attrs["ms_per_slide"] = per_slide * 1000
    return out


def tops_to_scores(tops: pd.DataFrame, k: int) -> pd.DataFrame:
    """Slide score = mean of its k highest tile scores."""
    return (tops[tops["rank"] < k].groupby(["seed", "evaluation", "group", "slide_id"]).logit.mean()
            .rename("score").reset_index())


def tau(cal_pos: np.ndarray) -> float:
    """The floor((n + 1)(1 - SENS_TARGET))-th smallest positive score (-inf when that index is 0)."""
    i = math.floor((len(cal_pos) + 1) * (1 - SENS_TARGET))
    return -math.inf if i == 0 else float(np.sort(cal_pos)[i - 1])


def evaluate(scores: pd.DataFrame, table: pd.DataFrame, tops: pd.DataFrame | None) -> pd.DataFrame:
    """One row per seed x held-out centre."""
    t = table.set_index("slide_id")
    s = scores.join(t[["label", "center", "reference_diagnosis", "exhaustive_annot", "dataset"]], on="slide_id")
    out = []
    for (seed, ev), g in s.groupby(["seed", "evaluation"]):
        cal, test = g[g.group == "loco-calibration"], g[g.group == "loco"]
        th = tau(cal[cal.label == 1].score.to_numpy())
        pos, neg = test[test.label == 1], test[test.label == 0]
        micro, macro = pos[pos.reference_diagnosis == "micro"], pos[pos.reference_diagnosis == "macro"]
        call = test.score >= th
        r = {"seed": seed, "center": test.center.iloc[0], "tau": th,
             "sens_micro": float((micro.score >= th).mean()), "sens_macro": float((macro.score >= th).mean()),
             "sensitivity": float((pos.score >= th).mean()), "specificity": float((neg.score < th).mean()),
             "auroc": float(roc_auc_score(test.label, test.score)),
             "auroc_micro": float(roc_auc_score(np.r_[np.ones(len(micro)), np.zeros(len(neg))],
                                                np.r_[micro.score, neg.score])),
             "neg_median": float(neg.score.median()), "cal_neg_median": float(cal[cal.label == 0].score.median()),
             "blind_spot_found": float(call[test.slide_id.isin(BLIND_SPOT)].mean())
             if test.slide_id.isin(BLIND_SPOT).any() else math.nan}
        if tops is not None:   # localisation: an annotated positive whose top-5 tiles include a tumour tile
            ann = pos[pos.exhaustive_annot.astype(bool)]
            tt = tops[(tops.seed == seed) & (tops.evaluation == ev) & (tops.group == "loco") & (tops["rank"] < K_MAIN)]
            hits = []
            for a in ann.itertuples():
                labels = tile_labels(a)
                hits.append(bool((labels[tt[tt.slide_id == a.slide_id].tile.to_numpy()] == "tumor").any()))
            r["localised"] = float(np.mean(hits)) if hits else math.nan
            r["n_localised"] = len(hits)
        out.append(r)
    return pd.DataFrame(out)


def judge(m: dict) -> dict:
    """`m`: score name -> mean over seeds, one row per centre (k = K_MAIN for the tile scores)."""
    ref = m[LOGIT]
    verdict = {}
    for name in (INSTANCE, CLASSIF):
        s = m[name]
        gain = s.sens_micro.min() - ref.sens_micro.min()
        spec = s.specificity.min() - ref.specificity.min()
        auroc = s.auroc.min() - ref.auroc.min()
        ok = gain >= MICRO_GAIN and spec >= -SPEC_LOSS and auroc >= -AUROC_LOSS
        verdict[name] = {"ok": ok, "gain": gain, "spec": spec, "auroc": auroc}
    return verdict


def fmt(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def check_rerun(new: pd.DataFrame, old: pd.DataFrame) -> str:
    key = ["slide_id", "evaluation", "group", "seed"]
    m = new[new.group.isin(["cv", "loco"])].merge(old[key + ["logit"]], on=key, suffixes=("", "_e6"), how="outer")
    if m.logit.isna().any() or m.logit_e6.isna().any():
        return "**non coincide**: righe senza corrispondenza"
    d = float((m.logit - m.logit_e6).abs().max())
    return f"{'coincide' if d <= 1e-6 else '**non coincide**'}: differenza massima {d:.2e} su {len(m)} righe"


def main():
    E12.mkdir(parents=True, exist_ok=True)
    table = load_table()
    if CLASSIFIER.exists():
        clf = pd.read_csv(CLASSIFIER)
        ms = float((E12 / "tile_classifier_ms.txt").read_text())
    else:
        clf = classifier_tops(table)
        ms = clf.attrs["ms_per_slide"]
        clf.to_csv(CLASSIFIER, index=False)
        (E12 / "tile_classifier_ms.txt").write_text(f"{ms:.4f}")
    if not (RERUN / "instances.csv").exists():
        raise SystemExit(f"classifier scores in {CLASSIFIER}; {RERUN}/instances.csv missing: finish the E6 rerun")
    preds, inst = pd.read_csv(RERUN / "predictions.csv"), pd.read_csv(RERUN / "instances.csv")
    logit = preds[preds.group.isin(["loco", "loco-calibration"])][
        ["seed", "evaluation", "group", "slide_id", "logit"]].rename(columns={"logit": "score"})
    inst = inst[inst.group.isin(["loco", "loco-calibration"])]

    res = {(LOGIT, None): evaluate(logit, table, None)}
    for k in KS:
        res[(INSTANCE, k)] = evaluate(tops_to_scores(inst, k), table, inst if k == K_MAIN else None)
        res[(CLASSIF, k)] = evaluate(tops_to_scores(clf, k), table, clf if k == K_MAIN else None)
    pd.concat([r.assign(score=n, k=k) for (n, k), r in res.items()]).to_csv(E12 / "metrics.csv", index=False)
    mean = {key: r.groupby("center").mean(numeric_only=True) for key, r in res.items()}

    lines = ["# E12 — punteggio del vetrino dalle tile più sospette", "",
             f"Controllo della riesecuzione di E6: {check_rerun(preds, pd.read_csv(E6))}.", "",
             f"Soglia τ per rotazione: lascia sopra il {SENS_TARGET:.0%} dei positivi dei centri di training (punteggi "
             "fuori fold). Media sui tre semi (valori dei semi tra parentesi per i primari).", "",
             "| Punteggio | k | Centro | Sens. micro | Sens. macro | Specificità | AUROC | AUROC micro | "
             "Mediana negativi (training) | Localizzazione | Punto cieco trovato |", "|" + "---|" * 11]
    for (n, k), r in res.items():
        for c, g in r.groupby("center"):
            mm = mean[(n, k)].loc[c]
            def seeds(col, g=g):
                return ", ".join(fmt(v) for v in g.sort_values("seed")[col])
            lines.append(f"| {n} | {k or '—'} | {c} | {fmt(mm.sens_micro)} ({seeds('sens_micro')}) | "
                         f"{fmt(mm.sens_macro)} | {fmt(mm.specificity)} ({seeds('specificity')}) | {fmt(mm.auroc)} | "
                         f"{fmt(mm.auroc_micro)} | {mm.neg_median:.2f} ({mm.cal_neg_median:.2f}) | "
                         f"{fmt(mm.get('localised', math.nan))} | {fmt(mm.blind_spot_found)} |")
    lines += ["", f"Tempo del classificatore di tile: {ms:.2f} ms per vetrino e modello (prodotto matrice, "
              "embedding già in memoria esclusi i tempi di lettura).", "",
              "## Criterio", "",
              f"Segnale candidato (k = {K_MAIN}) rispetto alla {LOGIT}: sensibilità sulle micrometastasi del centro "
              f"peggiore +{MICRO_GAIN:.2f}; specificità peggiore non oltre −{SPEC_LOSS:.2f}; AUROC peggiore non oltre "
              f"−{AUROC_LOSS:.2f}.", ""]
    m = {LOGIT: mean[(LOGIT, None)], INSTANCE: mean[(INSTANCE, K_MAIN)], CLASSIF: mean[(CLASSIF, K_MAIN)]}
    v = judge(m)
    for name, d in v.items():
        lines.append(f"- **{name}**: {'candidato' if d['ok'] else 'non candidato'}; sensibilità micro peggiore "
                     f"{fmt(m[name].sens_micro.min())} ({m[name].sens_micro.idxmin()}) contro "
                     f"{fmt(m[LOGIT].sens_micro.min())}, Δ {d['gain']:+.3f}; specificità peggiore Δ {d['spec']:+.3f}; "
                     f"AUROC peggiore Δ {d['auroc']:+.3f}.")
    cands = [n for n in (INSTANCE, CLASSIF) if v[n]["ok"]]
    if cands:
        best = max(m[n].sens_micro.min() for n in cands)
        choice = next(n for n in (INSTANCE, CLASSIF) if n in cands and m[n].sens_micro.min() >= best - TIE)
        verdict = f"segnale candidato: «{choice}»"
    else:
        verdict = "nessun segnale candidato"
    lines += ["", f"**Esito: {verdict}.**", ""]
    (E12 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
