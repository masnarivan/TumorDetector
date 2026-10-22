"""Whether a slide comes from a domain the head's development covers (experiment E15, candidate V).

A slide is summarised by the mean of its unit-norm tile embeddings; its score is the mean Euclidean distance
from the k nearest summaries of the reference (development slides outside one calibration fold, by patient).
The threshold is the conformal quantile of the calibration fold's scores: a slide above it is referred. In
E15 this recognised every unseen centre (also with a known scanner) and CAMELYON16 against CAMELYON17 of the
same hospital, which the metadata call the same centre; it recognises the centre, not the head's errors.
"""
import numpy as np

from tumordetector.heads.conformal import quantile


def slide_mean(features: np.ndarray) -> np.ndarray:
    """Mean of the L2-normalised tiles, float32 (computed in chunks: a bag can be memory-mapped)."""
    total = np.zeros(features.shape[1], dtype=np.float64)
    for i in range(0, len(features), 4096):
        x = np.asarray(features[i:i + 4096], dtype=np.float32)
        total += (x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)).sum(0)
    return (total / len(features)).astype(np.float32)


def score(means: np.ndarray, reference: np.ndarray, k: int) -> np.ndarray:
    """Mean distance of each summary from its k nearest reference summaries."""
    means, reference = np.atleast_2d(means).astype(np.float64), reference.astype(np.float64)
    d2 = (means ** 2).sum(1)[:, None] + (reference ** 2).sum(1)[None, :] - 2 * means @ reference.T
    d = np.sqrt(np.clip(d2, 0, None))
    return np.sort(d, axis=1)[:, :k].mean(1)


def fit(means: np.ndarray, folds: np.ndarray, calibration_fold: int, k: int, alpha: float) -> dict:
    """{reference, threshold, n_reference, n_calibration}: reference = slides outside the calibration fold."""
    folds = np.asarray(folds)
    cal = folds == calibration_fold
    if cal.sum() == 0 or (~cal).sum() < k:
        raise ValueError(f"calibration fold {calibration_fold}: {cal.sum()} slides, {(~cal).sum()} reference "
                         f"slides (need at least {k})")
    reference = means[~cal]
    return {"reference": reference, "threshold": quantile(score(means[cal], reference, k), alpha),
            "n_reference": int((~cal).sum()), "n_calibration": int(cal.sum())}
