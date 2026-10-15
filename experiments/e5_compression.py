"""E5: how much do int8 and PCA change nearest neighbours among the k-center prototypes in the vector DB?

Prototypes: 256 per slide (vectordb/reduce.py), 399 CAMELYON16 Phikon slides, unit vectors.
Queries: 10 random tiles from every 4th slide, searched among the other slides' prototypes.
Truth: exact Euclidean distance (= cosine ranking) in 768-d. PCA is fitted on unit vectors and
searched with Euclidean distance (centring changes cosine, not Euclidean distance).

  uv run python experiments/e5_compression.py
"""
import json
from pathlib import Path

import numpy as np
import torch
from scipy.stats import spearmanr

from tumordetector.vectordb import reduce

ROOT = Path("data/embeddings/phikon")
SEED, PROTOTYPES, K = 0, 256, 10


def int8(a: np.ndarray) -> np.ndarray:
    """Per-dimension min/max scalar quantization to 256 levels, decoded back (as Qdrant's int8)."""
    lo, hi = a.min(0), a.max(0)
    return np.round((a - lo) / (hi - lo) * 255) / 255 * (hi - lo) + lo


def main():
    slides = sorted(json.loads(Path("data/index/phikon.json").read_text())["slides"])
    rng = np.random.default_rng(SEED)
    P, owner, Q, qown = [], [], [], []
    for i, s in enumerate(slides):
        x = np.load(ROOT / f"{s}.npy")
        P.append(x[reduce.kcenter(x, PROTOTYPES).tiles])
        owner.append(np.full(len(P[-1]), i))
        if i % 4 == 0:
            Q.append(x[rng.choice(len(x), 10, replace=False)])
            qown.append(np.full(10, i))
    P, Q = reduce.unit(np.vstack(P)), reduce.unit(np.vstack(Q))
    same = torch.from_numpy(np.concatenate(qown))[:, None] == torch.from_numpy(np.concatenate(owner))[None]
    print(f"{len(P)} prototypes, {len(Q)} queries")

    def topk(q, p):
        d = torch.cdist(torch.from_numpy(np.ascontiguousarray(q, np.float32)),
                        torch.from_numpy(np.ascontiguousarray(p, np.float32)))
        d[same] = np.inf                                   # other slides only
        v, i = d.topk(K, dim=1, largest=False)
        return i.numpy(), v[:, 0].numpy()

    truth, d_true = topk(Q, P)

    def report(name, q, p, nbytes):
        got, d = topk(q, p)
        recall = np.mean([len(set(a) & set(b)) / K for a, b in zip(got, truth, strict=True)])
        print(f"{name:16s} {nbytes:5d} B/vector  recall@{K} {recall:.3f}  top-1 {np.mean(got[:, 0] == truth[:, 0]):.3f}"
              f"  NN-distance Spearman {spearmanr(d, d_true)[0]:.4f}")

    report("float16 768", Q, P, 1536)
    report("int8 768", Q, int8(P), 768)
    fit = P[rng.choice(len(P), 50_000, replace=False)]
    mu = fit.mean(0)
    _, s, vt = np.linalg.svd(fit - mu, full_matrices=False)
    var = np.cumsum(s ** 2) / np.sum(s ** 2)
    for k in (384, 256, 128, 64):
        w = vt[:k].T
        print(f"PCA {k}: {var[k - 1]:.3f} of the variance")
        report(f"PCA {k} float16", (Q - mu) @ w, (P - mu) @ w, 2 * k)
        report(f"PCA {k} int8", (Q - mu) @ w, int8((P - mu) @ w), k)


if __name__ == "__main__":
    main()
