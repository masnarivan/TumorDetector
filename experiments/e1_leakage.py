"""E1 - data leakage: near-identical slides across splits (protocol in docs/esperimenti.md).

For every pair of slides (i, j): D(i, j) = median over 200 sampled tiles of i of the distance to the
nearest tile of j (L2-normalised embeddings, Euclidean, exact). D(i, i) excludes the tile itself.
R(i, j) = D(i, j) / D(i, i); a pair is suspect if R <= 1 in either direction.

    uv run python experiments/e1_leakage.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from tumordetector.backbones.base import get_device
from tumordetector.io import code_version, read_json

BACKBONE, N_QUERY, SEED, CHUNK = "phikon", 200, 0, 8192
ROOT = Path("data/embeddings") / BACKBONE
FULL_OUT = Path("data/experiments/e1")                      # large outputs, not in git
REPORT = Path("data/reports/experiments/e1")                # small outputs, in git


def normalised(x: np.ndarray, device) -> torch.Tensor:
    t = torch.from_numpy(np.asarray(x, dtype=np.float32)).to(device)
    return torch.nn.functional.normalize(t, dim=1)


def main():
    device = get_device("auto")
    manifest = pd.read_csv("data/manifests/camelyon16.csv")
    table = manifest.merge(pd.read_csv("data/manifests/camelyon16_splits.csv"), on="slide_id")
    table = table[table.slide_id.map(lambda s: (ROOT / f"{s}.npy").exists())].reset_index(drop=True)
    slides = list(table.slide_id)
    print(f"{len(slides)} slides, device {device}", flush=True)

    # 1. identical files
    dup_md5 = manifest[manifest.file_md5.duplicated(keep=False)].sort_values("file_md5")

    # 2. sampled query tiles of every slide
    rng = np.random.default_rng(SEED)
    owner, local, queries = [], [], []
    for i, sid in enumerate(slides):
        x = np.load(ROOT / f"{sid}.npy", mmap_mode="r")
        idx = np.sort(rng.choice(len(x), min(N_QUERY, len(x)), replace=False))
        queries.append(np.asarray(x[idx]))
        owner.append(np.full(len(idx), i))
        local.append(idx)
    owner, local = np.concatenate(owner), np.concatenate(local)
    q = normalised(np.concatenate(queries), device)

    # nearest-tile similarity of every query in every slide
    best = np.empty((len(q), len(slides)), dtype=np.float32)
    t0 = time.time()
    for j, sid in enumerate(slides):
        db = normalised(np.load(ROOT / f"{sid}.npy"), device)
        mine = torch.from_numpy(np.flatnonzero(owner == j)).to(device)
        col = torch.empty(len(q), device=device)
        for a in range(0, len(q), CHUNK):
            sims = q[a:a + CHUNK] @ db.T
            rows = mine[(mine >= a) & (mine < a + CHUNK)]
            if len(rows):   # a tile is not its own neighbour
                sims[rows - a, torch.from_numpy(local[rows.cpu().numpy()]).to(device)] = -2.0
            col[a:a + CHUNK] = sims.max(dim=1).values
        best[:, j] = col.cpu().numpy()
        if j % 50 == 0:
            print(f"{j}/{len(slides)} slides searched, {time.time() - t0:.0f} s", flush=True)

    dist = np.sqrt(np.clip(2 - 2 * best, 0, None))
    d = np.stack([np.median(dist[owner == i], axis=0) for i in range(len(slides))])   # D[i, j]
    r = d / np.diag(d)[:, None]
    FULL_OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(r, index=slides, columns=slides).to_parquet(FULL_OUT / "ratio.parquet")

    # pairs i < j, with the lower of the two directions
    info = table.set_index("slide_id")[["split", "cv_fold", "center", "label"]]
    iu, ju = np.triu_indices(len(slides), k=1)
    pairs = pd.DataFrame({"slide_a": np.array(slides)[iu], "slide_b": np.array(slides)[ju],
                          "r_ab": r[iu, ju], "r_ba": r[ju, iu]})
    pairs["r_min"] = pairs[["r_ab", "r_ba"]].min(axis=1)
    for side in "ab":
        for c in info.columns:
            pairs[f"{c}_{side}"] = info.loc[pairs[f"slide_{side}"], c].to_numpy()
    pairs["relation"] = np.select(
        [pairs.split_a != pairs.split_b, (pairs.split_a == "train") & (pairs.cv_fold_a != pairs.cv_fold_b)],
        ["dev-test", "cross-fold"], "same-fold-or-both-test")
    pairs = pairs.sort_values("r_min").reset_index(drop=True)

    REPORT.mkdir(parents=True, exist_ok=True)
    suspect = pairs[pairs.r_min <= 1.0]
    suspect.to_csv(REPORT / "suspect_pairs.csv", index=False)
    top = pd.concat([pairs[pairs.relation == rel].head(10) for rel in ["dev-test", "cross-fold"]])
    top.to_csv(REPORT / "lowest_pairs.csv", index=False)
    summary = {
        "backbone": BACKBONE, "collection": read_json(ROOT / "collection.json")["collection"],
        "code_version": code_version(), "n_slides": len(slides), "n_query_tiles_per_slide": N_QUERY,
        "seed": SEED, "identical_md5_files": dup_md5.slide_id.tolist(),
        "n_suspect_pairs": {k: int(v) for k, v in suspect.relation.value_counts().items()},
        "r_min_quantiles": {str(p): float(np.quantile(pairs.r_min, p)) for p in (0, 0.001, 0.01, 0.05, 0.5)},
        "d_self_median": float(np.median(np.diag(d))),
        "search_seconds": round(time.time() - t0),
    }
    (REPORT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    print(top[["slide_a", "slide_b", "r_ab", "r_ba", "relation", "center_a", "center_b"]].to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
