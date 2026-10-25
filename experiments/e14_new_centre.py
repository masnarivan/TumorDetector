"""E14: slides of a new centre added to the head training, with the criterion fixed in docs/esperimenti.md.

  uv run python experiments/e14_new_centre.py train <seed> [backbone]   the 48 models of one seed (resumable: one
                                      logit file per model in data/reports/experiments/e14[/<backbone>]/logits)
  uv run python experiments/e14_new_centre.py analyse [backbone]       -> summary.md, metrics.csv, draws.csv

Backbone phikon (default, E14) or h_optimus_0 (E14b, in data/reports/experiments/e14/h_optimus_0). The references
(centre never seen, centre seen, E9 offset) come from the backbone's E6 with the inner LOCO logits: the E6 rerun
(experiments/e10_run.sh) for Phikon, E17's head for H-optimus-0. Seed 0 also trains a control: Utrecht held out with
no slide added, which must give those LOCO logits exactly (same training slides in the same order, same seed, one
thread); training stops if it does not. E14b's draws must be E14's (they depend only on the cohort).
"""
import math
import sys
import time
from pathlib import Path

import e10_conformal
import numpy as np
import pandas as pd
from e12_tile_score import load_table
from e16b_slide import roots

from tumordetector.mil.evaluate import binary_metrics

BACKBONES = {"phikon": (e10_conformal.RERUN, "E6"),   # backbone -> (its E6 predictions, the experiment)
             "h_optimus_0": (Path("data/reports/h_optimus_0/heads/ln_metastasis/predictions.csv"), "E17")}
PHIKON = Path("data/reports/experiments/e14")         # E14; other backbones in a subfolder
E14, LOGITS, ROOTS, RERUN, REF = PHIKON, PHIKON / "logits", roots("phikon"), *BACKBONES["phikon"]
NS = [5, 10, 20, 40]
DRAWS, DRAW_SEED = 3, 0
SEEDS = [0, 1, 2]
SPEC_LOSS, SENS_LOSS, MICRO_LOSS = 0.05, 0.05, 0.10   # against the seen centre (CV of E6 / E17)
GATE_SPEC = 0.80                                     # no single model below the gate's specificity
MICRO_GAIN = 0.05                                    # retraining beats the offset when both pass
CLOSED_MIN = 0.05                                    # gap closed only reported where the gap is at least this
CONTROL = "utrecht"


def use(backbone: str):
    global E14, LOGITS, ROOTS, RERUN, REF
    if backbone not in BACKBONES:
        raise SystemExit(__doc__)
    E14 = PHIKON if backbone == "phikon" else PHIKON / backbone
    LOGITS, ROOTS = E14 / "logits", roots(backbone)
    RERUN, REF = BACKBONES[backbone]
    if not RERUN.exists():
        raise SystemExit(f"{RERUN} missing: run experiments/e10_run.sh (phikon) or train the head (E17) first")


def draws_table(table: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([{"center": x["center"], "draw": x["draw"], "n": n, "slide_id": sid}
                         for x in draws(table) for n in NS for sid in x["added"][n]])


def check_draws(table: pd.DataFrame):
    """Another backbone must add the same slides as E14 (paired comparison)."""
    if E14 == PHIKON:
        return
    if not (PHIKON / "draws.csv").exists():
        raise SystemExit(f"{PHIKON / 'draws.csv'} missing: E14's draws are the reference")
    if not draws_table(table).equals(pd.read_csv(PHIKON / "draws.csv")):
        raise SystemExit("draws differ from E14's: the comparison would not be paired")


def draws(table: pd.DataFrame) -> list[dict]:
    """Per centre and draw: a random order of its patients; for each n the slides of the first patients
    until at least n (nested); evaluation = the centre's slides of the patients left out at the largest n."""
    rng = np.random.default_rng(DRAW_SEED)
    table = table.assign(patient=table.dataset + ":" + table.patient_pseudo_id.astype(str))
    out = []
    for c in sorted(table.center.unique()):
        t = table[table.center == c]
        patients = sorted(t.patient.unique())
        for d in range(DRAWS):
            order = rng.permutation(patients)
            slides = [list(t[t.patient == p].slide_id) for p in order]
            counts = np.cumsum([len(s) for s in slides])
            added = {n: [s for ss in slides[:int(np.searchsorted(counts, n)) + 1] for s in ss] for n in NS}
            taken = set(added[max(NS)])
            out.append({"center": c, "draw": d, "added": added,
                        "eval": [s for s in t.slide_id if s not in taken]})
    return out


def logit_path(c: str, d: int | None, n: int, seed: int) -> Path:
    return LOGITS / (f"{c}_control_s{seed}.csv" if d is None else f"{c}_d{d}_n{n}_s{seed}.csv")


def train(seed: int):
    import torch
    from omegaconf import OmegaConf

    from tumordetector.mil.abmil import fit, predict_logits

    cfg = OmegaConf.load("conf/config.yaml").mil
    torch.set_num_threads(cfg.threads)      # as in td task=train_head: same seed and threads -> same model
    torch.use_deterministic_algorithms(True)
    table = load_table()
    check_draws(table)
    rerun = pd.read_csv(RERUN)
    bags = {r.slide_id: np.load(ROOTS[r.dataset] / f"{r.slide_id}.npy", mmap_mode="r") for r in table.itertuples()}
    label = table.set_index("slide_id").label
    LOGITS.mkdir(parents=True, exist_ok=True)

    jobs = [(CONTROL, None, 0, [], list(table[table.center == CONTROL].slide_id))] if seed == 0 else []
    jobs += [(x["center"], x["draw"], n, x["added"][n], x["eval"]) for x in draws(table) for n in NS]
    for c, d, n, added, ev in jobs:
        path = logit_path(c, d, n, seed)
        if path.exists():
            if d is None:
                stop_unless_control(rerun)
            continue
        start = time.time()
        added = set(added)   # cohort order, as the protocol: n = 0 is exactly E6's leave-one-centre-out
        ids = [s for s, cc in zip(table.slide_id, table.center, strict=True) if cc != c or s in added]
        model = fit([bags[s] for s in ids], label[ids].to_numpy(), cfg, seed, cfg.device)
        logits, _ = predict_logits(model, [bags[s] for s in ev], cfg.device)
        tmp = path.with_suffix(".tmp")
        pd.DataFrame({"slide_id": ev, "logit": logits}).to_csv(tmp, index=False)
        tmp.rename(path)
        print(f"{time.strftime('%F %T')} seed {seed} {path.stem}: {len(ids)} training slides, "
              f"{time.time() - start:.0f} s", flush=True)
        if d is None:
            stop_unless_control(rerun)


def score(ev: pd.DataFrame, logit: np.ndarray, temperature: float) -> dict:
    """Threshold 0.5 on sigmoid(logit / T), i.e. logit >= 0: rates do not depend on T, the ECE does."""
    y, diag = ev.y.to_numpy(), ev.reference_diagnosis.to_numpy()
    m = binary_metrics(y, 1 / (1 + np.exp(-logit / temperature)))
    pred = logit >= 0
    out = {"specificity": m["specificity"], "sensitivity": m["sensitivity"], "auroc": m["auroc"], "ece": m["ece"],
           "micro": float(pred[diag == "micro"].mean()) if (diag == "micro").any() else math.nan,
           "macro": float(pred[diag == "macro"].mean()) if (diag == "macro").any() else math.nan,
           "neg_median": float(np.median(logit[y == 0])), "pos_median": float(np.median(logit[y == 1]))}
    for dom in sorted(ev.domain.unique()):
        neg = (ev.domain.to_numpy() == dom) & (y == 0)
        out[f"{dom}/specificity"] = float((~pred[neg]).mean()) if neg.any() else math.nan
    return out


def evaluate(table: pd.DataFrame, rerun: pd.DataFrame) -> pd.DataFrame:
    """One row per centre, draw, seed and n: retrained (n > 0), never seen (n = 0), seen (CV), offset."""
    t = table.set_index("slide_id")
    rows = []
    for x in draws(table):
        c, d = x["center"], x["draw"]
        ev = t.loc[x["eval"]].reset_index().rename(columns={"label": "y"})
        for s in SEEDS:
            r = rerun[rerun.seed == s]
            loco = r[(r.group == "loco") & (r.evaluation == f"held-out {c}")].set_index("slide_id")
            cv = r[r.group == "cv"].set_index("slide_id")
            cal = r[(r.group == "loco-calibration") & (r.evaluation == f"held-out {c}")]
            temp = float(loco.temperature.iloc[0])
            m_ref = float(np.median(cal[cal.y == 0].logit))
            base = {"center": c, "draw": d, "seed": s, "n_eval": len(ev), "n_eval_pos": int(ev.y.sum()),
                    "n_eval_micro": int((ev.reference_diagnosis == "micro").sum())}
            loco_logit = loco.logit[ev.slide_id].to_numpy()
            rows.append({**base, "method": "mai visto", "n": 0, **score(ev, loco_logit, temp)})
            rows.append({**base, "method": "visto", "n": 0,
                         **score(ev, cv.logit[ev.slide_id].to_numpy(), float(cv.temperature.iloc[0]))})
            for n in NS:
                added = t.loc[x["added"][n]]
                info = {"n_added": len(added), "n_added_pos": int(added.label.sum())}
                path = logit_path(c, d, n, s)
                if path.exists():
                    lg = pd.read_csv(path).set_index("slide_id").logit[ev.slide_id].to_numpy()
                    rows.append({**base, **info, "method": "riaddestrato", "n": n, **score(ev, lg, temp)})
                negs = [sid for sid in x["added"][n] if t.label[sid] == 0]
                if negs:   # E9, variant "solo in discesa", with the negatives among the added slides
                    b = max(float(np.median(loco.logit[negs])) - m_ref, 0.0)
                    rows.append({**base, **info, "method": "offset", "n": n, "b": b, "k": len(negs),
                                 **score(ev, loco_logit - b, temp)})
    return pd.DataFrame(rows)


def summarise(rows: pd.DataFrame) -> pd.DataFrame:
    """Mean over the 9 models (seeds x draws), and the worst specificity among them."""
    keys = ["method", "n", "center"]
    cols = [c for c in rows.columns if c not in keys + ["draw", "seed"]]
    s = rows.groupby(keys)[cols].mean()
    s["spec_min"] = rows.groupby(keys).specificity.min()
    s["runs"] = rows.groupby(keys).size()
    return s


def judge(s: pd.DataFrame, method: str, n: int, c: str) -> tuple[bool, list[str]]:
    seen, r = s.loc[("visto", 0, c)], s.loc[(method, n, c)]
    fails = []
    if r.specificity < seen.specificity - SPEC_LOSS:
        fails.append(f"specificità {r.specificity:.3f} < visto {seen.specificity:.3f} − {SPEC_LOSS}")
    if r.sensitivity < seen.sensitivity - SENS_LOSS:
        fails.append(f"sensibilità {r.sensitivity:.3f} < visto {seen.sensitivity:.3f} − {SENS_LOSS}")
    if r.micro < seen.micro - MICRO_LOSS:
        fails.append(f"micrometastasi {r.micro:.3f} < visto {seen.micro:.3f} − {MICRO_LOSS}")
    if r.spec_min < GATE_SPEC:
        fails.append(f"specificità minima {r.spec_min:.3f} < {GATE_SPEC}")
    return not fails, fails


def first_three(fails: list[str]) -> bool:
    """Conditions 1-3 of the criterion hold (the 4th, on the worst model, is left out)."""
    return not [f for f in fails if not f.startswith("specificità minima")]


def fmt(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def control_diff(rerun: pd.DataFrame) -> float:
    new = pd.read_csv(logit_path(CONTROL, None, 0, 0)).set_index("slide_id").logit
    old = rerun[(rerun.seed == 0) & (rerun.group == "loco") & (rerun.evaluation == f"held-out {CONTROL}")]
    return float(np.abs(old.set_index("slide_id").logit[new.index] - new).max())


def stop_unless_control(rerun: pd.DataFrame):
    print(f"control: {check_control(rerun)}", flush=True)
    if control_diff(rerun) != 0:
        raise SystemExit(f"the control does not give {REF}'s LOCO logits: stopping")


def check_control(rerun: pd.DataFrame) -> str:
    if not logit_path(CONTROL, None, 0, 0).exists():
        return "modello di controllo assente"
    return (f"{CONTROL} escluso senza vetrini aggiunti, seme 0: differenza massima dalle logit LOCO di {REF} "
            f"{control_diff(rerun):.2e}")


def paired(s: pd.DataFrame, centers: list[str]) -> list[str]:
    """Secondary of E14b: difference from E14 (Phikon) on the same draws and evaluation slides."""
    if E14 == PHIKON or not (PHIKON / "metrics.csv").exists():
        return []
    p = summarise(pd.read_csv(PHIKON / "metrics.csv"))
    lines = ["", "## Confronto appaiato con E14 su Phikon (secondario)", "",
             "Differenza questo backbone − Phikon, stessi vetrini di valutazione ed estrazioni.", "",
             "| Centro | Metodo | n | Specificità | Spec. min | Sensibilità | Micro |", "|" + "---|" * 7]
    for c in centers:
        for method, n in [("mai visto", 0), ("visto", 0)] + [("riaddestrato", n) for n in NS]:
            if (method, n, c) in s.index and (method, n, c) in p.index:
                a, b = s.loc[(method, n, c)], p.loc[(method, n, c)]
                lines.append(f"| {c} | {method} | {n} | " + " | ".join(
                    f"{a[k] - b[k]:+.3f}" for k in ("specificity", "spec_min", "sensitivity", "micro")) + " |")
    return lines


def analyse():
    table, rerun = load_table(), pd.read_csv(RERUN)
    check_draws(table)
    rows = evaluate(table, rerun)
    missing = len(SEEDS) * DRAWS * len(NS) * table.center.nunique() - (rows.method == "riaddestrato").sum()
    E14.mkdir(parents=True, exist_ok=True)
    rows.to_csv(E14 / "metrics.csv", index=False)
    draws_table(table).to_csv(E14 / "draws.csv", index=False)
    s = summarise(rows)
    centers = sorted(table.center.unique())

    title = "E14" if E14 == PHIKON else f"E14b ({E14.name})"
    lines = [f"# {title} — vetrini di un centro nuovo aggiunti al training", "",
             f"Controllo del codice: {check_control(rerun)}.", "",
             f"Modelli riaddestrati mancanti: {missing}." if missing else "Tutti i 144 modelli riaddestrati presenti.",
             "", "Media su 3 semi × 3 estrazioni, sugli stessi vetrini di valutazione per centro ed estrazione. "
             f"Soglia 0,5. «mai visto» = LOCO di {REF}, «visto» = CV di {REF}, «offset» = E9 solo in discesa con i "
             "negativi tra i vetrini aggiunti. Spec. min = la peggiore dei 9 modelli.", "",
             "| Centro | Metodo | n (aggiunti; positivi) | Specificità (min) | Sensibilità | Micro | Macro | AUROC | "
             "ECE | Mediana negativi / positivi |", "|" + "---|" * 10]
    for c in centers:
        e = s.loc[("mai visto", 0, c)]
        lines.append(f"| {c} | valutazione | {e.n_eval:.0f} vetrini, {e.n_eval_pos:.0f} positivi, "
                     f"{e.n_eval_micro:.0f} micro | | | | | | | |")
        for method, n in [("mai visto", 0), ("visto", 0)] + [(m, n) for n in NS for m in ("riaddestrato", "offset")]:
            if (method, n, c) not in s.index:
                continue
            r = s.loc[(method, n, c)]
            size = f"{n} ({r.n_added:.1f}; {r.n_added_pos:.1f})" if n else "—"
            lines.append(f"| {c} | {method} | {size} | {fmt(r.specificity)} ({fmt(r.spec_min)}) | "
                         f"{fmt(r.sensitivity)} | {fmt(r.micro)} | {fmt(r.macro)} | {fmt(r.auroc)} | {fmt(r.ece)} | "
                         f"{r.neg_median:.1f} / {r.pos_median:.1f} |")

    lines += ["", "## Frazione di distanza chiusa (specificità, riaddestrato)", "",
              "| Centro | Distanza visto − mai visto | " + " | ".join(f"n = {n}" for n in NS) + " |",
              "|" + "---|" * (2 + len(NS))]
    for c in centers:
        gap = s.loc[("visto", 0, c)].specificity - s.loc[("mai visto", 0, c)].specificity
        cells = [fmt((s.loc[("riaddestrato", n, c)].specificity - s.loc[("mai visto", 0, c)].specificity) / gap)
                 if gap >= CLOSED_MIN and ("riaddestrato", n, c) in s.index else "—" for n in NS]
        lines.append(f"| {c} | {gap:+.3f} | " + " | ".join(cells) + " |")

    dom_cols = sorted(c for c in s.columns if c.endswith("/specificity"))
    lines += ["", "## Specificità per dominio (secondario)", "",
              "| Centro | Metodo | n | " + " | ".join(dom_cols) + " |", "|" + "---|" * (3 + len(dom_cols))]
    for (method, n, c), r in s.iterrows():
        if method in ("mai visto", "visto", "riaddestrato") and not all(math.isnan(r[d]) for d in dom_cols):
            lines.append(f"| {c} | {method} | {n} | " + " | ".join(fmt(r[d]) for d in dom_cols) + " |")

    lines += ["", "## Criterio", "",
              f"n sufficiente: specificità e sensibilità entro {SPEC_LOSS} dal centro visto, micrometastasi entro "
              f"{MICRO_LOSS}, nessuno dei 9 modelli con specificità sotto {GATE_SPEC}. Costo d'ingresso = il più "
              "piccolo n sufficiente (0 se lo è già il centro mai visto).", ""]
    cost = {}
    for c in centers:
        ok0, fails0 = judge(s, "mai visto", 0, c)
        lines.append(f"- **{c}, mai visto**: {'sufficiente' if ok0 else 'no: ' + '; '.join(fails0)}.")
        if ok0:
            cost[c] = 0
        for n in NS:
            if ("riaddestrato", n, c) not in s.index:
                continue
            ok, fails = judge(s, "riaddestrato", n, c)
            if ("offset", n, c) in s.index:
                ok_o, fails_o = judge(s, "offset", n, c)
                r3, o3 = first_three(fails), first_three(fails_o)   # conditions 1-3 only
                better = r3 and (not o3 or s.loc[("riaddestrato", n, c)].micro
                                 - s.loc[("offset", n, c)].micro >= MICRO_GAIN)
                vs = (f" Offset: {'sufficiente' if ok_o else 'no: ' + '; '.join(fails_o)}. Riaddestrare "
                      f"{'rende' if better else 'non rende'} più dell'offset.")
            else:
                vs = " Offset: nessun negativo tra i vetrini aggiunti."
            lines.append(f"- **{c}, n = {n}**: {'sufficiente' if ok else 'no: ' + '; '.join(fails)}.{vs}")
            if ok and c not in cost:
                cost[c] = n
    lines += ["", "**Costo d'ingresso:** " + "; ".join(f"{c} {cost.get(c, 'oltre ' + str(max(NS)))}"
                                                    for c in centers) + ".", ""]
    lines += paired(s, centers)
    (E14 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    if sys.argv[1:2] == ["train"] and len(sys.argv) in (3, 4):
        use(sys.argv[3] if len(sys.argv) == 4 else "phikon")
        train(int(sys.argv[2]))
    elif sys.argv[1:2] == ["analyse"] and len(sys.argv) in (2, 3):
        use(sys.argv[2] if len(sys.argv) == 3 else "phikon")
        analyse()
    else:
        raise SystemExit(__doc__)
