"""E16: H-optimus-0 against Phikon at tile level, with the criterion fixed in docs/esperimenti.md.

The same tiles for both backbones (E12's sample, seeds 0-2; the grids are the same): a leave-one-centre-out
tumour/normal tile detector (specificity, AUROC and normal shift on the held-out centre), a probe on the centre
(tiles and slide means, 10-NN same-centre share) and the precision@10 of the nearest tiles across centres.
LPON is never read. -> data/reports/experiments/e16/{metrics.csv, summary.md}

    uv run python experiments/e16_backbone.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from e12_tile_score import NORMAL_PER_SLIDE, SEEDS, SENS_TARGET, TUMOR_PER_SLIDE, fit_folded, load_table
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from tumordetector.io import code_version, read_json

BACKBONES = {"phikon": "057cc0295895", "h_optimus_0": "b145cc1e6c6b"}
REPORT = Path("data/reports/experiments/e16")
SPEC_GAIN, AUROC_LOSS = 0.10, 0.01
PROBE_FOLDS, NN_TILES, K = 5, 20_000, 10
QUERY_PER_CLASS = 2_000


def root(backbone: str, dataset: str) -> Path:
    return Path("data/embeddings" if dataset == "camelyon16" else "data/camelyon17/embeddings") / backbone


def check(table: pd.DataFrame):
    """Every slide embedded by both backbones, with the expected weights and the same tile grid."""
    for b, version in BACKBONES.items():
        for ds in table.dataset.unique():
            col = read_json(root(b, ds) / "collection.json")
            if not col["version"].startswith(version):
                raise SystemExit(f"{b} {ds}: weights {col['version'][:12]}, expected {version}")
    for r in table.itertuples():
        grids = {read_json(root(b, r.dataset) / f"{r.slide_id}.json")["tiles_sha256"] for b in BACKBONES}
        if len(grids) != 1:
            raise SystemExit(f"{r.slide_id}: the backbones were not run on the same tile grid")


def sample_index(table: pd.DataFrame) -> dict:
    """seed -> slide_id -> (tile indices, label): E12's sample (same rng), computed once for both backbones."""
    out = {s: {} for s in SEEDS}
    for row in table.itertuples():
        if row.label == 1 and not row.exhaustive_annot:
            continue
        labels = pd.read_parquet(root("phikon", row.dataset) / f"{row.slide_id}.parquet").label.to_numpy()
        pool = np.flatnonzero(labels == ("tumor" if row.label == 1 else "normal"))
        cap = TUMOR_PER_SLIDE if row.label == 1 else NORMAL_PER_SLIDE
        for seed in SEEDS:
            rng = np.random.default_rng([seed, int.from_bytes(row.slide_id.encode()[:8], "little")])
            idx = np.sort(rng.choice(pool, min(cap, len(pool)), replace=False)) if len(pool) else pool
            out[seed][row.slide_id] = (idx, row.label)
    return out


def load_samples(table: pd.DataFrame, index: dict, backbone: str) -> dict:
    """seed -> slide_id -> (tile embeddings, labels), one read of each slide for all seeds."""
    out = {s: {} for s in SEEDS}
    for row in table.itertuples():
        if row.slide_id not in index[SEEDS[0]]:
            continue
        x = np.load(root(backbone, row.dataset) / f"{row.slide_id}.npy", mmap_mode="r")
        for seed in SEEDS:
            idx, label = index[seed][row.slide_id]
            out[seed][row.slide_id] = (np.asarray(x[idx], dtype=np.float32), np.full(len(idx), label))
    return out


def scores(s: dict, ids, label: int, w: np.ndarray, b: float) -> list[np.ndarray]:
    """Tile log-odds, one array per slide of `ids` with tiles of this label."""
    return [s[i][0] @ w + b for i in ids if i in s and len(s[i][0]) and s[i][1][0] == label]


def detector(table: pd.DataFrame, samples: dict) -> pd.DataFrame:
    """Measure 1: per seed and held-out centre, the tile detector trained on the other three centres."""
    rows = []
    for seed in SEEDS:
        s = samples[seed]
        for c in sorted(table.center.unique()):
            train, held = table[table.center != c], table[table.center == c]
            w, b = fit_folded(s, list(train.slide_id), seed)
            tau = np.quantile(np.concatenate(scores(s, train.slide_id, 1, w, b)), 1 - SENS_TARGET)
            train_normal = np.concatenate(scores(s, train.slide_id, 0, w, b))
            held_normal = scores(s, held.slide_id, 0, w, b)
            hn, ht = np.concatenate(held_normal), np.concatenate(scores(s, held.slide_id, 1, w, b))
            rows.append({"seed": seed, "held_out": c,
                         "tile_specificity": float((hn < tau).mean()),
                         "slide_specificity_median": float(np.median([(v < tau).mean() for v in held_normal])),
                         "tile_auroc": roc_auc_score(np.r_[np.ones(len(ht)), np.zeros(len(hn))], np.r_[ht, hn]),
                         "normal_shift": float(np.median(hn) - np.median(train_normal))})
            print(f"  seed {seed}, held-out {c}: specificity {rows[-1]['tile_specificity']:.3f}", file=sys.stderr)
    return pd.DataFrame(rows)


def unit(x: np.ndarray) -> torch.Tensor:
    t = torch.from_numpy(x)
    return t / t.norm(dim=1, keepdim=True).clamp_min(1e-12)


def knn(query: np.ndarray, base: np.ndarray, k: int, exclude: np.ndarray | None = None,
        q_group: np.ndarray | None = None) -> np.ndarray:
    """Indices of the k nearest base rows by cosine; rows of the same group as the query are skipped."""
    q, b = unit(query), unit(base)
    out = []
    for i in range(0, len(q), 1024):
        sim = q[i:i + 1024] @ b.T
        if exclude is not None:
            sim[torch.from_numpy(q_group[i:i + 1024, None] == exclude[None, :])] = -2
        out.append(sim.topk(k, dim=1).indices.numpy())
    return np.concatenate(out)


def probe(table: pd.DataFrame, samples: dict, backbone: str) -> dict:
    """Measure 2: how readable the centre is, from normal tiles of negatives (seed 0) and from slide means."""
    s, rng = samples[0], np.random.default_rng(0)
    neg = table[(table.label == 0) & table.slide_id.isin(list(s))]
    x = np.concatenate([s[i][0] for i in neg.slide_id])
    n = [len(s[i][0]) for i in neg.slide_id]
    centre, patient, slide = (np.repeat(neg[col].to_numpy(), n) for col in ("center", "patient_pseudo_id", "slide_id"))

    def fit(x, y, groups):
        proba = np.zeros((len(y), len(np.unique(y))))
        for tr, te in GroupKFold(PROBE_FOLDS).split(x, y, groups):
            m = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000)).fit(x[tr], y[tr])
            proba[te] = m.predict_proba(x[te])
        classes = np.unique(y)
        return (roc_auc_score(y, proba, multi_class="ovr", average="macro"),
                balanced_accuracy_score(y, classes[proba.argmax(1)]))

    out = {}
    out["probe_tile_auroc"], out["probe_tile_bal_acc"] = fit(x, centre, patient)
    means = np.stack([np.load(root(backbone, r.dataset) / f"{r.slide_id}.npy", mmap_mode="r").astype(np.float32).mean(0)
                      for r in table.itertuples()])
    out["probe_slide_auroc"], out["probe_slide_bal_acc"] = fit(means, table.center.to_numpy(),
                                                               table.patient_pseudo_id.to_numpy())
    pick = rng.choice(len(x), min(NN_TILES, len(x)), replace=False)
    nn = knn(x[pick], x[pick], K, exclude=slide[pick], q_group=slide[pick])
    out["nn_same_centre"] = float((centre[pick][nn] == centre[pick][:, None]).mean())
    return out


def retrieval(table: pd.DataFrame, samples: dict) -> dict:
    """Measure 3: precision@10 of the nearest training-centre tiles for tiles of the held-out centre (seed 0)."""
    s, rng, out = samples[0], np.random.default_rng(0), {}
    for c in sorted(table.center.unique()):
        ids = [i for i in s if len(s[i][0])]
        held = set(table[table.center == c].slide_id)
        base = np.concatenate([s[i][0] for i in ids if i not in held])
        base_y = np.concatenate([s[i][1] for i in ids if i not in held])
        q = np.concatenate([s[i][0] for i in ids if i in held])
        q_y = np.concatenate([s[i][1] for i in ids if i in held])
        prec = []
        for label in (0, 1):
            pool = np.flatnonzero(q_y == label)
            pick = rng.choice(pool, min(QUERY_PER_CLASS, len(pool)), replace=False)
            prec.append(float((base_y[knn(q[pick], base, K)] == label).mean()))
        out[c] = float(np.mean(prec))
    return out


def summary(det: pd.DataFrame, probes: dict, retr: dict) -> str:
    per = det.groupby(["backbone", "held_out"])[["tile_specificity", "slide_specificity_median", "tile_auroc",
                                                 "normal_shift"]].mean()
    worst = per.groupby("backbone").agg(spec=("tile_specificity", "min"), auroc=("tile_auroc", "min"))
    gain = worst.loc["h_optimus_0", "spec"] - worst.loc["phikon", "spec"]
    loss = worst.loc["phikon", "auroc"] - worst.loc["h_optimus_0", "auroc"]
    ok = gain >= SPEC_GAIN and loss <= AUROC_LOSS
    yes = {True: "sì", False: "no"}
    lines = ["# E16 — H-optimus-0 contro Phikon a livello di tile", "",
             f"Codice `{code_version()}`. Media sui semi {SEEDS}; LPON non letto.", "",
             "## Criterio", "",
             "| | Phikon | H-optimus-0 | Differenza | Soglia | Rispettato |", "|---|---|---|---|---|---|",
             f"| Specificità per tile, centro peggiore | {worst.loc['phikon', 'spec']:.3f} | "
             f"{worst.loc['h_optimus_0', 'spec']:.3f} | {gain:+.3f} | ≥ +{SPEC_GAIN} | {yes[gain >= SPEC_GAIN]} |",
             f"| AUROC per tile, centro peggiore | {worst.loc['phikon', 'auroc']:.3f} | "
             f"{worst.loc['h_optimus_0', 'auroc']:.3f} | {-loss:+.3f} | ≥ −{AUROC_LOSS} | {yes[loss <= AUROC_LOSS]} |",
             "", f"**Esito: H-optimus-0 {'promettente' if ok else 'non promettente'} a livello di tile.**", "",
             "## Per centro escluso", "",
             "| Centro escluso | Backbone | Specificità per tile | Specificità per vetrino (mediana) | "
             "AUROC per tile | Spostamento dei normali | Precisione@10 |", "|---|---|---|---|---|---|---|"]
    for (b, c), r in per.iterrows():
        lines.append(f"| {c} | {b} | {r.tile_specificity:.3f} | {r.slide_specificity_median:.3f} | "
                     f"{r.tile_auroc:.3f} | {r.normal_shift:+.2f} | {retr[b][c]:.3f} |")
    lines += ["", "## Centro negli embedding", "",
              "| Backbone | Probe tile AUROC | Probe tile acc. bil. | Probe vetrino AUROC | Probe vetrino acc. bil. | "
              "10 vicini dello stesso centro |", "|---|---|---|---|---|---|"]
    for b, p in probes.items():
        lines.append(f"| {b} | {p['probe_tile_auroc']:.3f} | {p['probe_tile_bal_acc']:.3f} | "
                     f"{p['probe_slide_auroc']:.3f} | {p['probe_slide_bal_acc']:.3f} | {p['nn_same_centre']:.3f} |")
    return "\n".join(lines) + "\n"


def main():
    torch.set_num_threads(8)
    table = load_table()
    table = table[table.role == "dev"].reset_index(drop=True)
    check(table)
    index = sample_index(table)
    REPORT.mkdir(parents=True, exist_ok=True)
    dets, probes, retr = [], {}, {}
    for b in BACKBONES:
        t0 = time.time()
        samples = load_samples(table, index, b)
        print(f"{b}: tiles loaded in {time.time() - t0:.0f} s", file=sys.stderr)
        dets.append(detector(table, samples).assign(backbone=b))
        retr[b] = retrieval(table, samples)
        probes[b] = probe(table, samples, b)
        print(f"{b}: done in {time.time() - t0:.0f} s", file=sys.stderr)
        del samples
    det = pd.concat(dets)
    det.to_csv(REPORT / "metrics.csv", index=False)
    (REPORT / "summary.md").write_text(summary(det, probes, retr))
    print((REPORT / "summary.md").read_text())


if __name__ == "__main__":
    main()
