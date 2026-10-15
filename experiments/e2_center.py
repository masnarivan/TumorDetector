"""E2 - how readable the medical centre is in the embeddings (protocol in docs/esperimenti.md).

    uv run python experiments/e2_center.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from tumordetector.backbones.base import get_device
from tumordetector.io import code_version, read_json

BACKBONE, SEED = "phikon", 0
N_TILES, N_RI, K, REGION, MIN_REGION_TILES = 200, 100, 10, 8, 16
ROOT = Path("data/embeddings") / BACKBONE
REPORT = Path("data/reports/experiments/e2")


def load(table: pd.DataFrame, rng) -> dict:
    """Per-slide pass over every tile: slide mean, region means, sampled tiles, RI tiles."""
    out = {k: [] for k in ("tile", "tile_slide", "tile_normal", "region", "region_slide", "region_normal",
                           "ri", "ri_slide", "ri_tumor", "mean")}
    sums, counts = {}, {}
    for r in table.itertuples():
        x = np.load(ROOT / f"{r.slide_id}.npy").astype(np.float32)
        t = pd.read_parquet(ROOT / f"{r.slide_id}.parquet")
        out["mean"].append(x.mean(0))
        sums[r.center] = sums.get(r.center, 0) + x.sum(0)
        counts[r.center] = counts.get(r.center, 0) + len(x)
        normal = (t.label == "normal").to_numpy()

        idx = rng.choice(len(x), min(N_TILES, len(x)), replace=False)
        out["tile"].append(x[idx])
        out["tile_slide"] += [r.Index] * len(idx)
        out["tile_normal"].append(normal[idx])

        side = t.size_l0.iloc[0] * REGION
        key = (t.x // side).astype(int).astype(str) + "_" + (t.y // side).astype(int).astype(str)
        for _, rows in t.groupby(key).indices.items():
            if len(rows) >= MIN_REGION_TILES:
                out["region"].append(x[rows].mean(0))
                out["region_slide"].append(r.Index)
                out["region_normal"].append(bool(normal[rows].all()))

        if r.exhaustive_annot or r.label == 0:   # tile labels are complete
            for lab in ("tumor", "normal"):
                cand = np.flatnonzero((t.label == lab).to_numpy())
                pick = rng.choice(cand, min(N_RI, len(cand)), replace=False)
                out["ri"].append(x[pick])
                out["ri_slide"] += [r.Index] * len(pick)
                out["ri_tumor"].append(np.full(len(pick), lab == "tumor"))
    arrays = {k: (np.concatenate(v) if k in ("tile", "tile_normal", "ri", "ri_tumor") else np.array(v))
              for k, v in out.items()}
    arrays["center_mean"] = {c: sums[c] / counts[c] for c in sums}
    return arrays


def probe(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> dict:
    """Logistic regression, 5 folds grouped by slide -> out-of-fold AUROC and balanced accuracy."""
    p = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=5).split(x, y, groups):
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
        p[te] = model.fit(x[tr], y[tr]).predict_proba(x[te])[:, 1]
    return {"n": int(len(y)), "auroc": float(roc_auc_score(y, p)),
            "balanced_accuracy": float(balanced_accuracy_score(y, p >= 0.5))}


def robustness_index(x: np.ndarray, tumor: np.ndarray, slide: np.ndarray, center: np.ndarray, device) -> dict:
    """k nearest neighbours from other slides; RI = same class & other centre / other class & same centre."""
    z = torch.nn.functional.normalize(torch.from_numpy(x).to(device), dim=1)
    s = torch.from_numpy(slide).to(device)
    nn = []
    for a in range(0, len(z), 4096):
        sims = z[a:a + 4096] @ z.T
        sims[s[a:a + 4096, None] == s[None, :]] = -2.0      # never a neighbour from the same slide
        nn.append(sims.topk(K, dim=1).indices.cpu().numpy())
    nn = np.concatenate(nn)
    same_class, same_center = tumor[nn] == tumor[:, None], center[nn] == center[:, None]
    so, os_ = int((same_class & ~same_center).sum()), int((~same_class & same_center).sum())
    return {"n": int(len(x)), "k": K, "same_class_other_center": so, "other_class_same_center": os_,
            "ri": so / max(os_, 1), "same_center_fraction": float(same_center.mean()),
            "same_class_fraction": float(same_class.mean())}


def main():
    t0 = time.time()
    device = get_device("auto")
    rng = np.random.default_rng(SEED)
    table = pd.read_csv("data/manifests/camelyon16.csv")
    table = table[table.slide_id.map(lambda s: (ROOT / f"{s}.npy").exists())].reset_index(drop=True)
    a = load(table, rng)
    center = (table.center == "utrecht").to_numpy().astype(int)   # 1 = utrecht
    print(f"loaded {len(table)} slides, {len(a['tile'])} tiles, {len(a['region'])} regions, "
          f"{len(a['ri'])} RI tiles, {time.time() - t0:.0f} s", flush=True)

    slide_mean, center_mean = a["mean"], np.stack([a["center_mean"][c] for c in table.center])
    variants = {"raw": lambda v, s: v,
                "minus_slide_mean": lambda v, s: v - slide_mean[s],
                "minus_center_mean": lambda v, s: v - center_mean[s]}
    results = {}
    for name, f in variants.items():
        tile, region, ri = f(a["tile"], a["tile_slide"]), f(a["region"], a["region_slide"]), f(a["ri"], a["ri_slide"])
        n, rn = a["tile_normal"], a["region_normal"]
        res = {
            "center_probe": {
                "tile": probe(tile, center[a["tile_slide"]], a["tile_slide"]),
                "tile_normal_only": probe(tile[n], center[a["tile_slide"][n]], a["tile_slide"][n]),
                "region": probe(region, center[a["region_slide"]], a["region_slide"]),
                "region_normal_only": probe(region[rn], center[a["region_slide"][rn]], a["region_slide"][rn]),
            },
            "tumor_probe_tile": probe(ri, a["ri_tumor"].astype(int), a["ri_slide"]),
            "robustness_index": robustness_index(ri, a["ri_tumor"], a["ri_slide"], center[a["ri_slide"]], device),
        }
        if name != "minus_slide_mean":   # a slide minus its own mean is zero
            res["center_probe"]["slide"] = probe(f(slide_mean, np.arange(len(table))), center, np.arange(len(table)))
        results[name] = res
        print(name, json.dumps(res, indent=1), flush=True)

    preds = pd.read_csv(f"data/reports/{BACKBONE}/abmil/predictions.csv")
    shift = (preds.groupby(["group", "center", "y"]).p
             .describe(percentiles=[0.1, 0.5, 0.9])[["count", "10%", "50%", "90%"]].round(3))
    loco = preds[preds.group == "loco"].groupby(["evaluation", "y"]).p.describe(
        percentiles=[0.1, 0.5, 0.9])[["count", "10%", "50%", "90%"]].round(3)

    REPORT.mkdir(parents=True, exist_ok=True)
    shift.to_csv(REPORT / "score_shift.csv")
    loco.to_csv(REPORT / "score_shift_loco.csv")
    summary = {"backbone": BACKBONE, "collection": read_json(ROOT / "collection.json")["collection"],
               "code_version": code_version(), "seed": SEED, "n_slides": len(table),
               "results": results, "seconds": round(time.time() - t0)}
    (REPORT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(shift.to_string(), "\n", loco.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
