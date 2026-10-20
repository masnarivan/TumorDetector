"""E9: offset correction from k negatives of the new centre, with the criterion fixed in docs/esperimenti.md.

Needs the E6 rerun with the inner LOCO logits (experiments/e10_run.sh), then
`uv run python experiments/e9_offset.py` -> data/reports/experiments/e9/summary.md and metrics.csv.
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
from e10_conformal import E6, RERUN, check_rerun

from tumordetector.mil.evaluate import binary_metrics

E9 = Path("data/reports/experiments/e9")
VARIANTS = ["offset", "offset solo in discesa"]   # tie-break prefers the second
KS = [3, 5, 10, 20]
DRAWS = 200
DRAW_SEED = 0
THRESHOLD = 0.5
SPEC_GAIN, ECE_GAIN = 0.10, 0.03      # primaries, as in E7 and E8
SENS_LOSS = 0.05                      # constraint on every held-out centre, against its seen (CV) sensitivity
TRANSFER_CENTERS = ["radboud", "utrecht"]   # centres with slides of both datasets


def offset(variant: str, m_k: float, m_ref: float) -> float:
    b = m_k - m_ref
    return max(b, 0.0) if variant == "offset solo in discesa" else b


def score(test: pd.DataFrame, b: float) -> dict:
    """Metrics of `test` after moving every logit by -b, with the rotation temperature."""
    z = (test.logit.to_numpy() - b) / test.temperature.to_numpy()
    m = binary_metrics(test.y.to_numpy(), 1 / (1 + np.exp(-z)), THRESHOLD)
    neg = test.y.to_numpy() == 0
    return {"specificity": m["specificity"], "sensitivity": m["sensitivity"], "ece": m["ece"], "auroc": m["auroc"],
            "neg_median_logit": float(np.median(test.logit.to_numpy()[neg] - b)) if neg.any() else math.nan}


def rows_for(test: pd.DataFrame, pool: pd.DataFrame, m_ref: float, k: int, rng, base: dict,
             eval_rest: bool) -> list[dict]:
    """DRAWS draws of k negatives from `pool`; evaluated on the rest of `test` (eval_rest) or on all of it."""
    neg_ids = pool[pool.y == 0].slide_id.to_numpy()
    out = []
    for d in range(DRAWS):
        drawn = rng.choice(neg_ids, size=k, replace=False)
        ev = test[~test.slide_id.isin(drawn)] if eval_rest else test
        m_k = float(np.median(pool.set_index("slide_id").logit[drawn]))
        ref = score(ev, 0.0)
        for v in VARIANTS:
            b = offset(v, m_k, m_ref)
            out.append({**base, "variant": v, "k": k, "draw": d, "b": b, "m_ref": m_ref, **score(ev, b),
                        **{f"e6_{key}": val for key, val in ref.items()}})
            if eval_rest:   # per domain, the secondary
                for dom, g in ev.groupby("domain"):
                    s = score(g, b)
                    out[-1][f"{dom}/sensitivity"], out[-1][f"{dom}/specificity"] = s["sensitivity"], s["specificity"]
    return out


def evaluate(preds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(DRAW_SEED)
    main, transfer = [], []
    for seed, ps in preds.groupby("seed"):
        for ev, test in ps[ps.group == "loco"].groupby("evaluation"):
            cal = ps[(ps.group == "loco-calibration") & (ps.evaluation == ev)]
            if cal.empty:
                raise SystemExit(f"no calibration logits for {ev}, seed {seed}: rerun E6 with experiments/e10_run.sh")
            m_ref = float(cal[cal.y == 0].logit.median())
            center = test.center.iloc[0]
            seen = ps[(ps.group == "cv") & (ps.center == center) & (ps.y == 1)]   # the centre seen in training
            base = {"seed": seed, "center": center, "seen_sensitivity": float((seen.p >= THRESHOLD).mean())}
            for k in KS:
                main += rows_for(test, test, m_ref, k, rng, base, eval_rest=True)
            if center in TRANSFER_CENTERS:
                for src, dst in [(a, b) for a in test.dataset.unique() for b in test.dataset.unique() if a != b]:
                    for k in KS:
                        transfer += rows_for(test[test.dataset == dst], test[test.dataset == src], m_ref, k, rng,
                                             {"seed": seed, "center": center, "from": src, "to": dst},
                                             eval_rest=False)
    return pd.DataFrame(main), pd.DataFrame(transfer)


def summarise(main: pd.DataFrame) -> pd.DataFrame:
    """Per variant x k x centre: mean over draws then seeds; the 10th percentile over draws, mean over seeds."""
    per_seed = main.groupby(["variant", "k", "center", "seed"]).agg(
        specificity=("specificity", "mean"), spec_p10=("specificity", lambda s: float(np.percentile(s, 10))),
        sensitivity=("sensitivity", "mean"), ece=("ece", "mean"), auroc=("auroc", "mean"),
        neg_median_logit=("neg_median_logit", "mean"), b=("b", "mean"), b_sd=("b", "std"), m_ref=("m_ref", "mean"),
        e6_specificity=("e6_specificity", "mean"), e6_sensitivity=("e6_sensitivity", "mean"),
        seen_sensitivity=("seen_sensitivity", "mean"),
        e6_ece=("e6_ece", "mean"), e6_auroc=("e6_auroc", "mean"), e6_neg_median_logit=("e6_neg_median_logit", "mean"))
    return per_seed.groupby(["variant", "k", "center"]).mean()


def judge(s: pd.DataFrame) -> tuple[bool, dict]:
    """`s`: one variant and k, one row per centre."""
    worst = s.specificity.idxmin()
    spec_gain = s.specificity.min() - s.e6_specificity.min()
    ece_gain = s.e6_ece.max() - s.ece.max()
    # against the centre seen in training, not E6 held out: there the shift inflates it (amended 20/10/2026)
    sens_loss = (s.seen_sensitivity - s.sensitivity).max()
    e6_worst = s.e6_specificity.idxmin()    # the centre the correction is for (protocol amended 20/10/2026)
    p10_ok = s.spec_p10[e6_worst] >= s.e6_specificity[e6_worst]
    ok = (spec_gain >= SPEC_GAIN or ece_gain >= ECE_GAIN) and sens_loss <= SENS_LOSS and p10_ok
    return ok, {"worst": worst, "spec_gain": spec_gain, "ece_gain": ece_gain, "sens_loss": sens_loss,
                "sens_loss_center": (s.seen_sensitivity - s.sensitivity).idxmax(), "e6_worst": e6_worst,
                "e6_sens_loss": (s.e6_sensitivity - s.sensitivity).max(),
                "p10": s.spec_p10[e6_worst], "e6_spec_worst": s.e6_specificity[e6_worst]}


def fmt(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def main():
    if not RERUN.exists():
        raise SystemExit(f"{RERUN} missing: run experiments/e10_run.sh first")
    new = pd.read_csv(RERUN)
    E9.mkdir(parents=True, exist_ok=True)
    rows, transfer = evaluate(new)
    rows.to_csv(E9 / "metrics.csv", index=False)
    transfer.to_csv(E9 / "transfer.csv", index=False)
    s = summarise(rows)

    lines = ["# E9 — correzione dell'offset con k negativi del centro nuovo", "",
             f"Controllo della riesecuzione di E6 (come in E10): {check_rerun(new, pd.read_csv(E6))}.", "",
             f"{DRAWS} estrazioni per seme, centro e k; media sulle estrazioni, poi sui semi. E6 = nessuna correzione "
             "sugli stessi vetrini di valutazione. p10 = 10° percentile della specificità sulle estrazioni.", "",
             "| Variante | k | Centro | Specificità (E6) | p10 | Sensibilità (E6; visto) | ECE (E6) | AUROC (E6) | "
             "Mediana logit negativi (E6; rif.) | b (DS) |", "|" + "---|" * 10]
    for (v, k, c), r in s.iterrows():
        lines.append(f"| {v} | {k} | {c} | {fmt(r.specificity)} ({fmt(r.e6_specificity)}) | {fmt(r.spec_p10)} | "
                     f"{fmt(r.sensitivity)} ({fmt(r.e6_sensitivity)}; {fmt(r.seen_sensitivity)}) | "
                     f"{fmt(r.ece)} ({fmt(r.e6_ece)}) | "
                     f"{fmt(r.auroc)} ({fmt(r.e6_auroc)}) | {r.neg_median_logit:.1f} ({r.e6_neg_median_logit:.1f}; "
                     f"{r.m_ref:.1f}) | {r.b:.1f} ({r.b_sd:.1f}) |")

    dom_cols = sorted(c for c in rows.columns if c.endswith(("/sensitivity", "/specificity")))
    lines += ["", "## Per dominio (media su estrazioni e semi)", "",
              "| Variante | k | Centro | " + " | ".join(dom_cols) + " |", "|" + "---|" * (3 + len(dom_cols))]
    for (v, k, c), g in rows.groupby(["variant", "k", "center"]):
        per_seed = g.groupby("seed")[dom_cols].mean().mean()
        lines.append(f"| {v} | {k} | {c} | " + " | ".join(fmt(per_seed[d]) for d in dom_cols) + " |")

    if transfer.empty:
        raise SystemExit(f"no slide of both datasets in {TRANSFER_CENTERS}: the transfer secondary cannot run")
    t = transfer.groupby(["variant", "k", "center", "from", "to", "seed"])[
        ["specificity", "sensitivity", "e6_specificity", "e6_sensitivity", "b"]].mean().groupby(
        ["variant", "k", "center", "from", "to"]).mean()
    lines += ["", "## Offset trasferito tra dataset dello stesso centro (secondario)", "",
              "k negativi da un dataset, valutazione su tutti i vetrini dell'altro.", "",
              "| Variante | k | Centro | Da → a | Specificità (E6) | Sensibilità (E6) | b |", "|" + "---|" * 7]
    for (v, k, c, a, b), r in t.iterrows():
        lines.append(f"| {v} | {k} | {c} | {a} → {b} | {fmt(r.specificity)} ({fmt(r.e6_specificity)}) | "
                     f"{fmt(r.sensitivity)} ({fmt(r.e6_sensitivity)}) | {r.b:.1f} |")

    lines += ["", "## Criterio", "",
              f"Proponibile: specificità peggiore +{SPEC_GAIN:.2f} o ECE peggiore −{ECE_GAIN:.2f} rispetto a E6; "
              f"sensibilità di nessun centro più di {SENS_LOSS:.2f} sotto quella del centro visto in CV; p10 della "
              "specificità sul centro peggiore di E6 non sotto la specificità di E6 su quel centro.", ""]
    minimal = {}
    for v in VARIANTS:
        for k in KS:
            ok, d = judge(s.loc[(v, k)])
            lines.append(f"- **{v}, k = {k}**: {'proponibile' if ok else 'non proponibile'}; specificità peggiore "
                         f"{d['worst']} Δ {d['spec_gain']:+.3f}; ECE peggiore Δ {-d['ece_gain']:+.3f}; perdita di "
                         f"sensibilità massima {d['sens_loss']:.3f} rispetto al centro visto "
                         f"({d['sens_loss_center']}), "
                         f"{d['e6_sens_loss']:.3f} rispetto a E6; p10 su {d['e6_worst']} "
                         f"(peggiore in E6) {fmt(d['p10'])} contro E6 {fmt(d['e6_spec_worst'])}.")
            if ok and v not in minimal:
                minimal[v] = k
    if minimal:
        k_best = min(minimal.values())
        choice = [v for v in VARIANTS if minimal.get(v) == k_best][-1]   # tie: the second
        verdict = f"proponibile «{choice}» da k = {k_best}" + "".join(
            f"; «{v}» da k = {kk}" for v, kk in minimal.items() if v != choice)
    else:
        verdict = "nessun k proponibile: la correzione dell'offset non si porta ai patologi in questa forma"
    lines += ["", f"**Esito: {verdict}.**", ""]
    (E9 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
