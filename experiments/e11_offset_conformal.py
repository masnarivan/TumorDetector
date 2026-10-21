"""E11: offset from k negatives of the new centre, then per-class conformal sets on the corrected logits, with
the criterion fixed in docs/esperimenti.md.

Needs the E6 rerun with the inner LOCO logits (experiments/e10_run.sh), then
`uv run python experiments/e11_offset_conformal.py` -> data/reports/experiments/e11/summary.md and metrics.csv.
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
from e9_offset import offset
from e10_conformal import COHORT, E6, PREVALENCES, RERUN, at_prevalence, check_rerun, quantile, thresholds

E11 = Path("data/reports/experiments/e11")
OFFSET = "offset solo in discesa"
V1, V2 = "offset + per classe", "offset + per classe, negativi locali"
E10_REF, E9_REF, E6_REF = "E10 per classe", "E9 offset", "E6"
VARIANTS = [V1, V2]               # tie-break prefers the first
KS = [3, 5, 10, 20]
LOCAL_K = 20                      # the local negative quantile needs >= 19 slides at alpha = 0.05
ALPHAS = [0.05, 0.10]
PRIMARY_ALPHA = 0.05
DRAWS = 200
DRAW_SEED = 0
THRESHOLD = 0.5
COVERAGE_FLOOR = 0.90             # 1: positive coverage on every held-out centre (E10)
SENS_LOSS = 0.05                  # 2: positives not lost vs the centre seen in training (E9)
FP_GAIN = 0.10                    # 3: negatives answered {1} on the worst centre, below E10
BAD_DRAW = 90                     # 4: percentile of negatives answered {1} (amended 21/10/2026: high is bad)
REFER_MARGIN = 0.10               # 5: referral rate of every centre at most E10 + this


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def set_rates(y: np.ndarray, micro: np.ndarray, has0: np.ndarray, has1: np.ndarray) -> dict:
    """Outcomes of the sets of one evaluation; `micro` flags micrometastases among the positives."""
    pos, neg = y == 1, y == 0
    only1, only0 = has1 & ~has0, has0 & ~has1
    refer = ~(only1 | only0)
    single = only1 | only0
    wrong = (only1 & neg) | (only0 & pos)

    def frac(mask, sub):
        return float(mask[sub].mean()) if sub.any() else math.nan

    mic, mac = pos & micro, pos & ~micro
    return {"cov1": frac(has1, pos), "cov0": frac(has0, neg), "a1": frac(only1, pos), "f0": frac(only1, neg),
            "a0": frac(only0, neg), "f1": frac(only0, pos), "r1": frac(refer, pos), "r0": frac(refer, neg),
            "refer": float(refer.mean()), "size": float((has0.astype(int) + has1.astype(int)).mean()),
            "single_error": float(wrong.sum() / single.sum()) if single.any() else math.nan,
            "lost_micro": frac(only0, mic), "refer_micro": frac(refer, mic),
            "lost_macro": frac(only0, mac), "refer_macro": frac(refer, mac)}


def conformal(p: np.ndarray, q0: float, q1: float) -> tuple[np.ndarray, np.ndarray]:
    return p <= q0, 1 - p <= q1


def at_threshold(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return p < THRESHOLD, p >= THRESHOLD


def evaluate(preds: pd.DataFrame, micro_ids: set) -> pd.DataFrame:
    rng = np.random.default_rng(DRAW_SEED)
    out = []
    for seed, ps in preds.groupby("seed"):
        for ev, test in ps[ps.group == "loco"].groupby("evaluation"):
            cal = ps[(ps.group == "loco-calibration") & (ps.evaluation == ev)]
            if cal.empty:
                raise SystemExit(f"no calibration logits for {ev}, seed {seed}: rerun E6 with experiments/e10_run.sh")
            center = test.center.iloc[0]
            m_ref = float(cal[cal.y == 0].logit.median())
            seen = ps[(ps.group == "cv") & (ps.center == center) & (ps.y == 1)]
            seen_sens = float((seen.p >= THRESHOLD).mean())
            q = {a: thresholds(cal, "per classe", a, None) for a in ALPHAS}
            logit, y, t = test.logit.to_numpy(), test.y.to_numpy(), test.temperature.to_numpy()
            micro = test.slide_id.isin(micro_ids).to_numpy()
            neg_idx = np.flatnonzero(y == 0)
            p_raw = sigmoid(logit / t)
            for k in KS:
                for d in range(DRAWS):
                    drawn = rng.choice(neg_idx, size=k, replace=False)
                    keep = np.ones(len(y), bool)
                    keep[drawn] = False
                    b = offset(OFFSET, float(np.median(logit[drawn])), m_ref)
                    p_cor = sigmoid((logit - b) / t)
                    base = {"seed": seed, "center": center, "k": k, "draw": d, "b": b, "seen_sensitivity": seen_sens}
                    ye, me = y[keep], micro[keep]
                    for name, (h0, h1) in [(E9_REF, at_threshold(p_cor[keep])), (E6_REF, at_threshold(p_raw[keep]))]:
                        out.append({**base, "method": name, "alpha": math.nan, **set_rates(ye, me, h0, h1)})
                    for a in ALPHAS:
                        q0, q1 = q[a]
                        sets = [(E10_REF, conformal(p_raw[keep], q0, q1)), (V1, conformal(p_cor[keep], q0, q1))]
                        if k == LOCAL_K:   # q0 from the k drawn negatives, corrected; their score is p
                            sets.append((V2, conformal(p_cor[keep], quantile(p_cor[drawn], a), q1)))
                        for name, (h0, h1) in sets:
                            out.append({**base, "method": name, "alpha": a, **set_rates(ye, me, h0, h1)})
    return pd.DataFrame(out)


def summarise(res: pd.DataFrame) -> pd.DataFrame:
    """Per method x alpha x k x centre: mean over draws then seeds; the bad-draw percentile of f0 likewise."""
    keys = ["method", "alpha", "k", "center"]
    cols = [c for c in res.columns if c not in keys + ["seed", "draw"]]
    r = res.fillna({"alpha": -1})   # threshold references have no alpha
    per_seed = r.groupby(keys + ["seed"])[cols].mean()
    per_seed["f0_bad"] = r.groupby(keys + ["seed"]).f0.quantile(BAD_DRAW / 100)
    return per_seed.groupby(keys).mean()


def judge(s: pd.DataFrame, v: str, k: int) -> tuple[bool, dict]:
    m, ref = s.loc[(v, PRIMARY_ALPHA, k)], s.loc[(E10_REF, PRIMARY_ALPHA, k)]
    e10_worst = ref.f0.idxmax()
    checks = {
        "copertura": bool((m.cov1 >= COVERAGE_FLOOR).all()),
        "tumori persi": bool(((1 - m.f1) >= m.seen_sensitivity - SENS_LOSS).all()),
        "falsi positivi": bool(m.f0.max() <= ref.f0.max() - FP_GAIN),
        "estrazione sfortunata": bool(m.f0_bad[e10_worst] <= ref.f0[e10_worst]),
        "rinvii": bool((m.refer <= ref.refer + REFER_MARGIN).all()),
    }
    detail = {"cov_worst": m.cov1.min(), "cov_center": m.cov1.idxmin(),
              "kept_margin": ((1 - m.f1) - m.seen_sensitivity).min(),       # < -SENS_LOSS fails check 2
              "kept_center": ((1 - m.f1) - m.seen_sensitivity).idxmin(),
              "fp_worst": m.f0.max(), "fp_center": m.f0.idxmax(), "e10_fp_worst": ref.f0.max(),
              "bad": m.f0_bad[e10_worst], "e10_worst": e10_worst, "e10_fp_there": ref.f0[e10_worst],
              "refer_excess": (m.refer - ref.refer).max(), "refer_center": (m.refer - ref.refer).idxmax()}
    return all(checks.values()), {"checks": checks, **detail}


def fmt(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def main():
    if not RERUN.exists():
        raise SystemExit(f"{RERUN} missing: run experiments/e10_run.sh first")
    new = pd.read_csv(RERUN)
    cohort = pd.read_csv(COHORT)
    dev = cohort[cohort.role == "dev"]
    micro_ids = set(dev[(dev.label == 1) & (dev.reference_diagnosis == "micro")].slide_id)
    cohort_pi = float(dev.label.mean())
    E11.mkdir(parents=True, exist_ok=True)
    res = evaluate(new, micro_ids)
    res.to_csv(E11 / "metrics.csv", index=False)
    s = summarise(res)

    lines = ["# E11 — offset e insiemi conformal insieme", "",
             f"Controllo della riesecuzione di E6 (come in E10): {check_rerun(new, pd.read_csv(E6))}.", "",
             f"{DRAWS} estrazioni per seme, centro e k; media sulle estrazioni, poi sui semi. Offset «{OFFSET}». "
             f"Riferimenti sugli stessi vetrini: {E10_REF} (senza offset), {E9_REF} e {E6_REF} alla soglia "
             f"{THRESHOLD}. f0 cattiva = {BAD_DRAW}° percentile sulle estrazioni.", ""]
    cols = [("cov1", "Copertura positivi"), ("f1", "Tumori persi"), ("seen_sensitivity", "Sens. centro visto"),
            ("f0", "Negativi con {1}"), ("f0_bad", "f0 cattiva"), ("refer", "Rinvii"), ("cov0", "Copertura negativi"),
            ("size", "Dimensione media"), ("single_error", "Errore sulle risposte"), ("b", "b medio")]
    for alpha in ALPHAS:
        lines += [f"## α = {alpha:.2f}", "", "| Metodo | k | Centro | " + " | ".join(c[1] for c in cols) + " |",
                  "|" + "---|" * (3 + len(cols))]
        for meth in [V1, V2, E10_REF, E9_REF, E6_REF]:
            a = alpha if meth in (V1, V2, E10_REF) else -1
            if meth in (E9_REF, E6_REF) and alpha != PRIMARY_ALPHA:
                continue
            for (mm, aa, k, c), r in s.iterrows():
                if mm == meth and aa == a:
                    lines.append(f"| {meth} | {k} | {c} | " + " | ".join(fmt(r[x]) for x, _ in cols) + " |")
        lines.append("")

    lines += [f"## Micrometastasi e macrometastasi (α = {PRIMARY_ALPHA:.2f})", "",
              "| Metodo | k | Centro | Micro persi | Micro rinviati | Macro persi | Macro rinviati |", "|" + "---|" * 7]
    for meth in [V1, V2, E10_REF, E9_REF]:
        a = PRIMARY_ALPHA if meth != E9_REF else -1
        for (mm, aa, k, c), r in s.iterrows():
            if mm == meth and aa == a:
                lines.append(f"| {meth} | {k} | {c} | {fmt(r.lost_micro)} | {fmt(r.refer_micro)} | "
                             f"{fmt(r.lost_macro)} | {fmt(r.refer_macro)} |")

    prevs = [*PREVALENCES, cohort_pi]
    lines += ["", f"## Alla prevalenza (α = {PRIMARY_ALPHA:.2f}, media sui semi)", "",
              "| Metodo | k | Centro | " + " | ".join(f"π = {pi:.2f}: rinvii / PPV / NPV" for pi in prevs) + " |",
              "|" + "---|" * (3 + len(prevs))]
    per_seed = res[res.alpha == PRIMARY_ALPHA].groupby(["method", "k", "center", "seed"]).mean(numeric_only=True)
    for (meth, k, c), g in per_seed.groupby(["method", "k", "center"]):
        if meth not in (V1, V2):
            continue
        vals = []
        for pi in prevs:
            v = pd.DataFrame([at_prevalence(r, pi) for r in g.to_dict("records")]).mean()
            vals.append(f"{fmt(v.refer)} / {fmt(v.ppv)} / {fmt(v.npv)}")
        lines.append(f"| {meth} | {k} | {c} | " + " | ".join(vals) + " |")

    lines += ["", "## Criterio", "",
              f"Proponibile (α = {PRIMARY_ALPHA:.2f}) se: 1) copertura dei positivi ≥ {COVERAGE_FLOOR:.2f} su ogni "
              f"centro; 2) positivi non persi ≥ sensibilità del centro visto − {SENS_LOSS:.2f} su ogni centro; "
              f"3) negativi con {{1}} sul centro peggiore almeno {FP_GAIN:.2f} sotto {E10_REF}; 4) {BAD_DRAW}° "
              f"percentile dei negativi con {{1}} sul centro peggiore di {E10_REF} non sopra {E10_REF} lì; "
              f"5) rinvii di nessun centro oltre {E10_REF} + {REFER_MARGIN:.2f}.", ""]
    minimal = {}
    for v in VARIANTS:
        for k in (KS if v == V1 else [LOCAL_K]):
            ok, d = judge(s, v, k)
            failed = [n for n, passed in d["checks"].items() if not passed]
            lines.append(
                f"- **{v}, k = {k}**: {'proponibile' if ok else 'non proponibile'}"
                f"{'' if ok else ' (non superate: ' + ', '.join(failed) + ')'}; copertura peggiore "
                f"{fmt(d['cov_worst'])} ({d['cov_center']}); positivi non persi meno sensibilità del centro visto, "
                f"minimo {d['kept_margin']:+.3f} ({d['kept_center']}); negativi con {{1}} sul peggiore "
                f"{fmt(d['fp_worst'])} "
                f"({d['fp_center']}) contro {E10_REF} {fmt(d['e10_fp_worst'])}; {BAD_DRAW}° percentile su "
                f"{d['e10_worst']} {fmt(d['bad'])} contro {fmt(d['e10_fp_there'])}; rinvii fino a "
                f"{d['refer_excess']:+.3f} oltre {E10_REF} ({d['refer_center']}).")
            if ok and v not in minimal:
                minimal[v] = k
    if minimal:
        k_best = min(minimal.values())
        choice = next(v for v in VARIANTS if minimal.get(v) == k_best)
        verdict = f"proponibile «{choice}» da k = {k_best}" + "".join(
            f"; «{v}» da k = {kk}" for v, kk in minimal.items() if v != choice)
    else:
        verdict = "nessuna combinazione proponibile"
    lines += ["", f"**Esito: {verdict}.**", ""]
    (E11 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
