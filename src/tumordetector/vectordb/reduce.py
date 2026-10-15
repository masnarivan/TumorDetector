"""What of a slide goes into the vector database: two levels, a few hundred vectors instead of ~10k tiles.

- regions: mean embedding of each square of `side` x `side` tiles (8 x 8 = ~0.9 mm at 0.5 mpp) with at
  least `min_tiles` tissue tiles. Areas larger than a tile, for case retrieval; a micrometastasis
  smaller than a region vanishes in its mean, which is what the second level is for.
- prototypes: greedy k-center over the slide's tiles. Each new prototype is the tile farthest from
  those already chosen, so every tile is within the coverage radius of one of them, rare tissue
  (tumour included) is kept. In E3 the 256 prototypes per slide scored OOD as the full reference.

Deterministic, no seed: the first prototype is the tile closest to the slide mean.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


def unit(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    return x / np.linalg.norm(x, axis=1, keepdims=True).clip(min=1e-12)


@dataclass
class Prototypes:
    tiles: np.ndarray        # tile rows, in k-center order: the first n are the n-prototype set
    represented: np.ndarray  # tiles whose nearest prototype is this one
    radius: float            # largest distance (unit vectors, Euclidean) from a tile to its prototype


def kcenter(x: np.ndarray, n: int) -> Prototypes:
    z = unit(x)
    if len(z) <= n:
        order = np.arange(len(z))
    else:
        order = [int(np.argmax(z @ unit(z.mean(0, keepdims=True))[0]))]
        sim = z @ z[order[0]]                      # cosine to the nearest chosen tile
        for _ in range(n - 1):
            order.append(nxt := int(np.argmin(sim)))
            sim = np.maximum(sim, z @ z[nxt])
        order = np.array(order)
    best = np.zeros(len(z), dtype=np.int64)
    top = np.full(len(z), -2.0, dtype=np.float32)
    for i in range(0, len(order), 64):             # nearest prototype of every tile, in chunks
        s = z @ z[order[i:i + 64]].T
        j = s.argmax(1)
        better = s[np.arange(len(z)), j] > top
        best[better], top[better] = j[better] + i, s[np.arange(len(z)), j][better]
    radius = float(np.sqrt(np.clip(2 - 2 * top.min(), 0, None)))
    return Prototypes(order, np.bincount(best, minlength=len(order)), radius)


def regions(x: np.ndarray, tiles: pd.DataFrame, side: int, min_tiles: int) -> tuple[np.ndarray, pd.DataFrame]:
    """-> (mean embedding per region, one row per region: level-0 origin and size, tile counts)."""
    span = float(tiles.size_l0.iloc[0]) * side
    gx, gy = (tiles.x // span).astype(int).to_numpy(), (tiles.y // span).astype(int).to_numpy()
    label = tiles["label"].to_numpy() if "label" in tiles else np.full(len(tiles), None)
    groups = pd.DataFrame({"gx": gx, "gy": gy}).groupby(["gx", "gy"]).indices
    vecs, rows = [], []
    for (i, j), idx in sorted(groups.items()):
        if len(idx) < min_tiles:
            continue
        vecs.append(np.asarray(x[idx], dtype=np.float32).mean(0))
        rows.append({"x": int(i * span), "y": int(j * span), "size_l0": span, "n_tiles": len(idx),
                     "tumor_tiles": int((label[idx] == "tumor").sum()),
                     "boundary_tiles": int((label[idx] == "boundary").sum())})
    return np.array(vecs, dtype=np.float32).reshape(-1, x.shape[1]), pd.DataFrame(rows)
