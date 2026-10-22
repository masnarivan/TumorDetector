"""Prediction sets of a binary head, per class (experiment E10, variant chosen by its criterion).

The non-conformity of a slide with true label y is 1 - p(y), p the calibrated probability. For each
class, its quantile q_y is the ceil((n_y + 1)(1 - alpha))-th smallest score of the calibration slides of
that class; a new slide's set holds every label y with 1 - p(y) <= q_y. Sets: {0} or {1} are answers,
{0, 1} (uncertain) and {} (unlike either class) are referrals. The coverage guarantee holds for slides
exchangeable with the calibration ones: a centre never seen breaks it, which leave-one-centre-out measures.
"""
import math

import numpy as np


def quantile(scores: np.ndarray, alpha: float) -> float:
    """The ceil((n+1)(1-alpha))-th smallest score; 1 (the label always enters) if that index exceeds n."""
    n = len(scores)
    k = math.ceil((n + 1) * (1 - alpha))
    return 1.0 if n == 0 or k > n else float(np.sort(scores)[k - 1])


def nonconformity(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.where(np.asarray(y) == 1, 1 - np.asarray(p), np.asarray(p))


def class_quantiles(p: np.ndarray, y: np.ndarray, alpha: float) -> dict:
    """{q0, q1, n0, n1}: the quantile of each class from its own calibration slides."""
    y = np.asarray(y)
    s = nonconformity(p, y)
    return {"q0": quantile(s[y == 0], alpha), "q1": quantile(s[y == 1], alpha),
            "n0": int((y == 0).sum()), "n1": int((y == 1).sum())}


def prediction_set(p: np.ndarray, q0: float, q1: float) -> tuple[np.ndarray, np.ndarray]:
    """(label 0 in the set, label 1 in the set) per slide."""
    p = np.asarray(p, dtype=float)
    return p <= q0, 1 - p <= q1


def coverage(p: np.ndarray, y: np.ndarray, q0: float, q1: float) -> dict:
    """Share of positives / negatives whose set holds their label, and share of slides referred."""
    y = np.asarray(y)
    has0, has1 = prediction_set(p, q0, q1)
    referred = has0 == has1
    return {"positive_coverage": float(has1[y == 1].mean()) if (y == 1).any() else None,
            "negative_coverage": float(has0[y == 0].mean()) if (y == 0).any() else None,
            "referral": float(referred.mean()) if len(y) else None}
