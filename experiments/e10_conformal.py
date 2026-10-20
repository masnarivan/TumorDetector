"""E10: conformal sets and referral on the held-out centre, with the criterion fixed in docs/esperimenti.md.

Rerun E6 first (experiments/e10_run.sh: it also saves the inner LOCO logits), then
`uv run python experiments/e10_conformal.py` -> data/reports/experiments/e10/summary.md and metrics.csv.
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd

E10 = Path("data/reports/experiments/e10")
RERUN = E10 / "e6" / "predictions.csv"
E6 = Path("data/reports/phikon/heads/ln_metastasis/predictions.csv")
COHORT = Path("data/manifests/heads/ln_metastasis.csv")
VARIANTS = ["marginale", "per classe", "per classe × centro"]   # protocol order: simplest first
ALPHAS = [0.05, 0.10]
PRIMARY_ALPHA = 0.05
COVERAGE_TOLERANCE = 0.05     # usable: positive coverage >= 1 - alpha - tolerance on every held-out centre
TIE = 0.02                    # referral rates within this are a tie, broken by simplicity
PREVALENCES = [0.05, 0.10, 0.20, 0.30]
THRESHOLD = 0.5               # the E6 decision, for the false positives it gives as answers
MATCH_ATOL = 1e-6


def quantile(scores: np.ndarray, alpha: float) -> float:
    """The ceil((n+1)(1-alpha))-th smallest score; 1 (every label enters) if that index exceeds n."""
    n = len(scores)
    k = math.ceil((n + 1) * (1 - alpha))
    return 1.0 if n == 0 or k > n else float(np.sort(scores)[k - 1])


def scores(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Non-conformity of the true label: 1 - p(y)."""
    return np.where(y == 1, 1 - p, p)


def thresholds(cal: pd.DataFrame, variant: str, alpha: float, center: str | None) -> tuple[float, float]:
    """(q0, q1) for a test slide. `center`: its own centre if it is in `cal` (seen), None if held out."""
    s = scores(cal.p.to_numpy(), cal.y.to_numpy())
    if variant == "marginale":
        q = quantile(s, alpha)
        return q, q
    if variant == "per classe":
        return tuple(quantile(s[cal.y.to_numpy() == y], alpha) for y in (0, 1))
    qs = {(c, y): quantile(s[((cal.center == c) & (cal.y == y)).to_numpy()], alpha)
          for c in cal.center.unique() for y in (0, 1)}
    if center is not None:
        return qs[(center, 0)], qs[(center, 1)]
    return tuple(max(q for (_, yy), q in qs.items() if yy == y) for y in (0, 1))   # held out: the most prudent


def outcomes(test: pd.DataFrame, q0: float, q1: float) -> pd.DataFrame:
    """Per slide: which labels enter the set ({0}, {1}, {0,1}, {})."""
    p = test.p.to_numpy()
    return test.assign(has0=p <= q0, has1=1 - p <= q1)


def rates(o: pd.DataFrame) -> dict:
    pos, neg = o[o.y == 1], o[o.y == 0]
    only1, only0 = o.has1 & ~o.has0, o.has0 & ~o.has1
    both, empty = o.has0 & o.has1, ~o.has0 & ~o.has1
    single = only1 | only0
    wrong = (only1 & (o.y == 0)) | (only0 & (o.y == 1))

    def frac(mask, sub):
        return float(mask[sub.index].mean()) if len(sub) else float("nan")

    return {"n0": len(neg), "n1": len(pos),
            "cov1": frac(o.has1, pos), "cov0": frac(o.has0, neg),
            "a1": frac(only1, pos), "f0": frac(only1, neg), "a0": frac(only0, neg), "f1": frac(only0, pos),
            "r1": frac(both | empty, pos), "r0": frac(both | empty, neg),
            "refer": float((both | empty).mean()), "refer_uncertain": float(both.mean()),
            "refer_empty": float(empty.mean()), "size": float((o.has0.astype(int) + o.has1.astype(int)).mean()),
            "single_error": float(wrong.sum() / single.sum()) if single.any() else float("nan"),
            "e6_fp": frac(o.p >= THRESHOLD, neg)}


def at_prevalence(r: dict, pi: float) -> dict:
    ppv_den = pi * r["a1"] + (1 - pi) * r["f0"]
    npv_den = (1 - pi) * r["a0"] + pi * r["f1"]
    return {"refer": pi * r["r1"] + (1 - pi) * r["r0"],
            "ppv": pi * r["a1"] / ppv_den if ppv_den > 0 else float("nan"),
            "npv": (1 - pi) * r["a0"] / npv_den if npv_den > 0 else float("nan")}


def evaluate(preds: pd.DataFrame, folds: pd.Series) -> pd.DataFrame:
    """One row per setting x variant x alpha x seed x centre."""
    out = []
    for seed, ps in preds.groupby("seed"):
        loco, cal_all, cv = (ps[ps.group == g] for g in ("loco", "loco-calibration", "cv"))
        for ev, test in loco.groupby("evaluation"):
            cal = cal_all[cal_all.evaluation == ev]
            if cal.empty:
                raise SystemExit(f"no calibration logits for {ev}, seed {seed}: rerun E6 with experiments/e10_run.sh")
            for variant in VARIANTS:
                for alpha in ALPHAS:
                    q0, q1 = thresholds(cal, variant, alpha, None)
                    out.append({"setting": "escluso", "variant": variant, "alpha": alpha, "seed": seed,
                                "center": test.center.iloc[0], "q0": q0, "q1": q1,
                                **rates(outcomes(test, q0, q1))})
        fold = cv.slide_id.map(folds)
        for variant in VARIANTS:
            for alpha in ALPHAS:
                parts = []
                for k in sorted(fold.unique()):
                    cal, test = cv[fold != k], cv[fold == k]
                    for c, tc in test.groupby("center"):
                        parts.append(outcomes(tc, *thresholds(cal, variant, alpha, c)))
                o = pd.concat(parts)
                for c, oc in o.groupby("center"):
                    out.append({"setting": "visto", "variant": variant, "alpha": alpha, "seed": seed,
                                "center": c, "q0": float("nan"), "q1": float("nan"), **rates(oc)})
    return pd.DataFrame(out)


def check_rerun(new: pd.DataFrame, old: pd.DataFrame) -> str:
    key = ["slide_id", "evaluation", "group", "seed"]
    m = new[new.group.isin(["cv", "loco"])].merge(old[key + ["logit"]], on=key, suffixes=("", "_e6"), how="outer")
    if m.logit.isna().any() or m.logit_e6.isna().any():
        return f"**non coincide**: {int(m.logit.isna().sum() + m.logit_e6.isna().sum())} righe senza corrispondenza"
    d = float((m.logit - m.logit_e6).abs().max())
    ok = d <= MATCH_ATOL
    return f"{'coincide' if ok else '**non coincide**'}: differenza massima delle logit {d:.2e} su {len(m)} righe"


def fmt(x: float) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def cell(g: pd.DataFrame, col: str) -> str:
    return f"{fmt(g[col].mean())} ({', '.join(fmt(v) for v in g.sort_values('seed')[col])})"


def main():
    if not RERUN.exists():
        raise SystemExit(f"{RERUN} missing: run experiments/e10_run.sh first")
    new, old = pd.read_csv(RERUN), pd.read_csv(E6)
    cohort = pd.read_csv(COHORT)
    folds = cohort.set_index("slide_id").cv_fold
    dev = cohort[cohort.role == "dev"]
    cohort_pi = float(dev.label.mean())
    res = evaluate(new, folds)
    res.to_csv(E10 / "metrics.csv", index=False)

    lines = ["# E10 — insiemi conformal e rinvio", "",
             f"Controllo preliminare (CV e LOCO della riesecuzione contro E6): {check_rerun(new, old)}.", "",
             "Media sui semi (valori dei semi tra parentesi). Centro escluso: quantili dai fold interni dei soli "
             "centri di training.", ""]
    cols = [("cov1", "Copertura positivi"), ("f0", "Negativi con risposta {1}"), ("e6_fp", "1 − specificità E6"),
            ("cov0", "Copertura negativi"), ("f1", "Tumori persi"), ("refer", "Rinvii"),
            ("refer_empty", "di cui {}"), ("size", "Dimensione media"), ("single_error", "Errore sulle risposte")]
    for setting in ("escluso", "visto"):
        for alpha in ALPHAS:
            lines += [f"## Centro {setting}, α = {alpha:.2f}", "",
                      "| Variante | Centro | " + " | ".join(c[1] for c in cols) + " |",
                      "|" + "---|" * (2 + len(cols))]
            sub = res[(res.setting == setting) & (res.alpha == alpha)]
            for v in VARIANTS:
                for c, g in sub[sub.variant == v].groupby("center"):
                    lines.append(f"| {v} | {c} | " + " | ".join(cell(g, k) for k, _ in cols) + " |")
            lines.append("")

    primary = res[(res.setting == "escluso") & (res.alpha == PRIMARY_ALPHA)]
    mean = primary.groupby(["variant", "center"]).mean(numeric_only=True)
    lines += [f"## Alla prevalenza (centro escluso, α = {PRIMARY_ALPHA:.2f}, media sui semi)", "",
              "| Variante | Centro | " + " | ".join(f"π = {pi:.2f}: rinvii / PPV / NPV" for pi in
                                                     [*PREVALENCES, cohort_pi]) + " |",
              "|" + "---|" * (3 + len(PREVALENCES))]
    for v in VARIANTS:
        for c, g in primary[primary.variant == v].groupby("center"):
            vals = []
            for pi in [*PREVALENCES, cohort_pi]:
                per_seed = pd.DataFrame([at_prevalence(r, pi) for r in g.to_dict("records")]).mean()
                vals.append(f"{fmt(per_seed.refer)} / {fmt(per_seed.ppv)} / {fmt(per_seed.npv)}")
            lines.append(f"| {v} | {c} | " + " | ".join(vals) + " |")

    floor = 1 - PRIMARY_ALPHA - COVERAGE_TOLERANCE
    lines += ["", "## Criterio", "", f"Utilizzabile: copertura media dei positivi ≥ {floor:.2f} su ogni centro "
              f"escluso (α = {PRIMARY_ALPHA:.2f}). Scelta: rinvii più bassi sul centro escluso che ne ha di più; "
              f"a parità entro {TIE:.2f}, la più semplice.", ""]
    usable = {}
    for v in VARIANTS:
        m = mean.loc[v]
        worst_cov, worst_refer = float(m.cov1.min()), float(m.refer.max())
        ok = bool((m.cov1 >= floor).all())
        if ok:
            usable[v] = worst_refer
        lines.append(f"- **{v}**: {'utilizzabile' if ok else 'non utilizzabile'}; copertura dei positivi peggiore "
                     f"{fmt(worst_cov)} ({m.cov1.idxmin()}); rinvii sul centro peggiore {fmt(worst_refer)} "
                     f"({m.refer.idxmax()}); negativi con risposta {{1}} sul centro peggiore {fmt(float(m.f0.max()))} "
                     f"({m.f0.idxmax()}), 1 − specificità E6 lì {fmt(float(m.e6_fp[m.f0.idxmax()]))}.")
    if usable:
        best = min(usable.values())
        choice = next(v for v in VARIANTS if v in usable and usable[v] <= best + TIE)
        verdict = f"scelta la variante «{choice}»"
    else:
        verdict = "nessuna variante utilizzabile: insiemi e rinvii rimandati a E9"
    lines += ["", f"**Esito: {verdict}.**", ""]
    (E10 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
