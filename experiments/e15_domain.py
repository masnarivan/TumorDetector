"""E15: recognising an unseen domain from the embeddings, with the criterion fixed in docs/esperimenti.md.

  uv run python experiments/e15_domain.py               -> data/reports/experiments/e15/summary.md, scores.csv
  uv run python experiments/e15_domain.py h_optimus_0   -> data/reports/experiments/e15/h_optimus_0/...: the same
      protocol on H-optimus-0, with E17's held-out predictions in place of E6's (rerun of 25/10/2026)

Per slide (cached in data/reports/experiments/e15/summaries.npz): the mean of its unit tiles, 200 unit tiles at
random (seed 0) and its 256 k-center prototypes (vectordb/reduce.kcenter, as in the vector DB). Per rotation:
reference folds 0-2, calibration fold 3, in-distribution fold 4 of the training centres, out of distribution
the held-out centre; two more rotations hold out the CAMELYON16 slides of Radboud and of Utrecht (secondary).
"""
import math
import sys
from pathlib import Path

import e10_conformal
import numpy as np
import pandas as pd
import torch
from e12_tile_score import load_table
from e16b_slide import roots

from tumordetector.heads.conformal import quantile
from tumordetector.vectordb.reduce import kcenter, unit

BACKBONES = {"phikon": e10_conformal.RERUN,     # backbone -> its E6 held-out predictions (rerun of E10, E17)
             "h_optimus_0": Path("data/reports/h_optimus_0/heads/ln_metastasis/predictions.csv")}
E15 = Path("data/reports/experiments/e15")      # phikon; other backbones in a subfolder (set in main)
CACHE = E15 / "summaries.npz"
ROOTS = roots("phikon")
RERUN = BACKBONES["phikon"]
HEAD = {"phikon": "E6", "h_optimus_0": "E17"}    # the experiment whose head errors the score must catch
YEARS = Path("data/reports/experiments/e3b/scan_metadata.csv")
CANDIDATES = ["V", "T"]                  # protocol order: simplest first
ALPHA = 0.05
K_SLIDES, N_PROTO, N_TILES = 5, 256, 200
REF_FOLDS, CAL_FOLD, IN_FOLD = (0, 1, 2), 3, 4
MAX_FALSE, MAX_FALSE_POS, MIN_FP_CAUGHT, MIN_UTRECHT = 0.08, 0.10, 0.90, 0.95
WITHIN = ["radboud", "utrecht"]          # centres with slides of both datasets: CAMELYON16 held out (secondary)
THREADS = 4


def summarise(table: pd.DataFrame) -> dict:
    """slide_id -> (mean, tiles, prototypes), unit vectors; prototypes only for reference-fold slides."""
    if CACHE.exists():
        z = np.load(CACHE)
        return {s: (z[f"{s}/mean"], z[f"{s}/tiles"], z[f"{s}/proto"] if f"{s}/proto" in z else None)
                for s in table.slide_id}
    out, flat = {}, {}
    for i, r in enumerate(table.itertuples()):
        x = unit(np.load(ROOTS[r.dataset] / f"{r.slide_id}.npy"))
        rng = np.random.default_rng(0)
        tiles = x[np.sort(rng.choice(len(x), min(N_TILES, len(x)), replace=False))]
        proto = x[kcenter(x, N_PROTO).tiles[:N_PROTO]] if r.cv_fold in REF_FOLDS else None
        mean = x.mean(0)
        out[r.slide_id] = (mean, tiles, proto)
        flat[f"{r.slide_id}/mean"], flat[f"{r.slide_id}/tiles"] = mean.astype(np.float16), tiles.astype(np.float16)
        if proto is not None:
            flat[f"{r.slide_id}/proto"] = proto.astype(np.float16)
        if i % 100 == 0:
            print(f"summaries {i}/{len(table)}", flush=True)
    E15.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE, **flat)
    return out


def score_v(means: np.ndarray, ref_means: np.ndarray) -> np.ndarray:
    """Mean Euclidean distance of each slide mean from its K_SLIDES nearest reference slide means."""
    d = torch.cdist(torch.from_numpy(means.astype(np.float32)), torch.from_numpy(ref_means.astype(np.float32)))
    return d.topk(K_SLIDES, largest=False).values.mean(1).numpy()


def score_t(tiles: list[np.ndarray], protos: np.ndarray) -> np.ndarray:
    """Per slide, mean over its sampled tiles of the distance to the nearest reference prototype (unit vectors)."""
    p = torch.from_numpy(protos.astype(np.float32))
    out = []
    for t in tiles:
        sim = (torch.from_numpy(t.astype(np.float32)) @ p.T).max(1).values
        out.append(float(torch.sqrt((2 - 2 * sim).clamp(min=0)).mean()))
    return np.array(out)


def rotations(table: pd.DataFrame) -> list[tuple[str, np.ndarray]]:
    """(name, held-out mask): one per centre, then the CAMELYON16 slides of each centre in WITHIN."""
    out = [(f"held-out {c}", (table.center == c).to_numpy()) for c in sorted(table.center.unique())]
    out += [(f"held-out {c} camelyon16", ((table.center == c) & (table.dataset == "camelyon16")).to_numpy())
            for c in WITHIN]
    return out


def evaluate(table: pd.DataFrame, summ: dict) -> pd.DataFrame:
    rows = []
    for name, out_mask in rotations(table):
        train = table[~out_mask]
        ref = train[train.cv_fold.isin(REF_FOLDS)]
        roles = {"calibrazione": train[train.cv_fold == CAL_FOLD], "in distribuzione": train[train.cv_fold == IN_FOLD],
                 "fuori distribuzione": table[out_mask]}
        ref_means = np.stack([summ[s][0] for s in ref.slide_id])
        protos = np.concatenate([summ[s][2] for s in ref.slide_id])
        scored = {}
        for role, g in roles.items():
            scored[role] = g.assign(
                V=score_v(np.stack([summ[s][0] for s in g.slide_id]), ref_means),
                T=score_t([summ[s][1] for s in g.slide_id], protos))
        thr = {c: quantile(scored["calibrazione"][c].to_numpy(), ALPHA) for c in CANDIDATES}
        for role, g in scored.items():
            g = g.assign(rotation=name, role=role, **{f"refer_{c}": g[c] > thr[c] for c in CANDIDATES},
                         **{f"threshold_{c}": thr[c] for c in CANDIDATES})
            rows.append(g)
        print(f"{name}: reference {len(ref)} slides, {len(protos)} prototypes; thresholds "
              + ", ".join(f"{c} {thr[c]:.4f}" for c in CANDIDATES), flush=True)
    return pd.concat(rows, ignore_index=True)


def head_errors(scores: pd.DataFrame, rerun: pd.DataFrame) -> pd.DataFrame:
    """Per seed and candidate: share of E6's held-out false positives / false negatives the score refers."""
    out = scores[(scores.role == "fuori distribuzione") & ~scores.rotation.str.endswith("camelyon16")]
    loco = rerun[rerun.group == "loco"]
    rows = []
    for seed, g in loco.groupby("seed"):
        g = g.merge(out[["slide_id", "rotation", *[f"refer_{c}" for c in CANDIDATES]]],
                    left_on=["slide_id", "evaluation"], right_on=["slide_id", "rotation"], validate="one_to_one")
        fp, fn = g[(g.logit >= 0) & (g.y == 0)], g[(g.logit < 0) & (g.y == 1)]
        for c in CANDIDATES:
            rows.append({"seed": seed, "candidate": c, "n_fp": len(fp), "fp_referred": fp[f"refer_{c}"].mean(),
                         "n_fn": len(fn), "fn_referred": fn[f"refer_{c}"].mean() if len(fn) else math.nan})
    return pd.DataFrame(rows)


def missed_referred(scores: pd.DataFrame, rerun: pd.DataFrame) -> dict:
    """{(rotation, candidate): share of E6's held-out false negatives the score refers, over the seeds}."""
    out = scores[(scores.role == "fuori distribuzione") & ~scores.rotation.str.endswith("camelyon16")]
    loco = rerun[(rerun.group == "loco") & (rerun.logit < 0) & (rerun.y == 1)]
    g = loco.merge(out[["slide_id", "rotation", *[f"refer_{c}" for c in CANDIDATES]]],
                   left_on=["slide_id", "evaluation"], right_on=["slide_id", "rotation"], validate="many_to_one")
    return {(rot, c): r[f"refer_{c}"].mean() for rot, r in g.groupby("rotation") for c in CANDIDATES}


def judge(m: dict) -> list[str]:
    fails = []
    if m["false"] > MAX_FALSE:
        fails.append(f"falsi rinvii {m['false']:.3f} > {MAX_FALSE}")
    if m["false_pos"] > MAX_FALSE_POS:
        fails.append(f"falsi rinvii sui positivi {m['false_pos']:.3f} > {MAX_FALSE_POS}")
    if m["fp_caught"] < MIN_FP_CAUGHT:
        fails.append(f"falsi positivi di {HEAD} rinviati {m['fp_caught']:.3f} < {MIN_FP_CAUGHT}")
    if m["utrecht"] < MIN_UTRECHT:
        fails.append(f"Utrecht escluso rilevato {m['utrecht']:.3f} < {MIN_UTRECHT}")
    return fails


def fmt(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def auroc(inside: np.ndarray, outside: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(np.r_[np.zeros(len(inside)), np.ones(len(outside))], np.r_[inside, outside]))


def main(backbone: str = "phikon"):
    global E15, CACHE, ROOTS, RERUN, HEAD
    HEAD = HEAD[backbone]
    if backbone != "phikon":
        E15, ROOTS, RERUN = E15 / backbone, roots(backbone), BACKBONES[backbone]
        CACHE = E15 / "summaries.npz"
    torch.set_num_threads(THREADS)
    if not RERUN.exists():
        raise SystemExit(f"{RERUN} missing: run experiments/e10_run.sh (phikon) or train the head (E17) first")
    table = load_table()
    summ = summarise(table)
    scores = evaluate(table, summ)
    E15.mkdir(parents=True, exist_ok=True)
    scores.drop(columns=["exhaustive_annot"]).to_csv(E15 / "scores.csv", index=False)
    errors = head_errors(scores, pd.read_csv(RERUN))
    missed = missed_referred(scores, pd.read_csv(RERUN))
    main_rot = ~scores.rotation.str.endswith("camelyon16")
    ind = scores[main_rot & (scores.role == "in distribuzione")]
    out = scores[main_rot & (scores.role == "fuori distribuzione")]

    lines = [f"# E15 — riconoscere un dominio non visto dagli embedding ({backbone})", "",
             f"α = {ALPHA}; soglia dai vetrini di calibrazione (fold {CAL_FOLD}) di ogni rotazione; riferimento fold "
             f"{', '.join(map(str, REF_FOLDS))}; in distribuzione fold {IN_FOLD}. V = media del vetrino, {K_SLIDES} "
             f"vicini; T = {N_TILES} tile, distanza dal più vicino dei {N_PROTO} prototipi k-center per vetrino.", "",
             "## Primari", "",
             f"| Candidato | Falsi rinvii in distribuzione | sui positivi | Falsi positivi di {HEAD} rinviati (semi) | "
             "Utrecht escluso rilevato | Esito |", "|---|---|---|---|---|---|"]
    verdicts = {}
    for c in CANDIDATES:
        e = errors[errors.candidate == c]
        m = {"false": ind[f"refer_{c}"].mean(), "false_pos": ind[ind.label == 1][f"refer_{c}"].mean(),
             "fp_caught": e.fp_referred.mean(), "utrecht": out[out.center == "utrecht"][f"refer_{c}"].mean()}
        fails = judge(m)
        verdicts[c] = fails
        lines.append(f"| {c} | {fmt(m['false'])} ({len(ind)}) | {fmt(m['false_pos'])} | {fmt(m['fp_caught'])} "
                     f"({', '.join(fmt(v) for v in e.fp_referred)}; {', '.join(str(n) for n in e.n_fp)} FP) | "
                     f"{fmt(m['utrecht'])} | {'adottabile' if not fails else 'no: ' + '; '.join(fails)} |")

    lines += ["", "## Per rotazione (secondari)", "",
              "| Rotazione | Candidato | Falsi rinvii in distribuzione | Rilevamento fuori distribuzione | AUROC | "
              f"Falsi negativi di {HEAD} rinviati | Positivi fuori distribuzione rinviati: micro / macro |",
              "|---|---|---|---|---|---|---|"]
    for rot, g in scores.groupby("rotation", sort=False):
        gi, go = g[g.role == "in distribuzione"], g[g.role == "fuori distribuzione"]
        for c in CANDIDATES:
            fn = missed.get((rot, c), math.nan)
            micro = go[go.reference_diagnosis == "micro"][f"refer_{c}"].mean()
            macro = go[go.reference_diagnosis == "macro"][f"refer_{c}"].mean()
            lines.append(f"| {rot} | {c} | {fmt(gi[f'refer_{c}'].mean())} | {fmt(go[f'refer_{c}'].mean())} | "
                         f"{fmt(auroc(gi[c].to_numpy(), go[c].to_numpy()))} | {fmt(fn)} | "
                         f"{fmt(micro)} / {fmt(macro)} |")

    lines += ["", "## Falsi rinvii in distribuzione per dominio e per diagnosi (rotazioni principali)", "",
              "| Gruppo | Vetrini | " + " | ".join(CANDIDATES) + " |", "|" + "---|" * (2 + len(CANDIDATES))]
    for col in ("domain", "reference_diagnosis"):
        for k, g in ind.groupby(col):
            lines.append(f"| {k} | {len(g)} | " + " | ".join(fmt(g[f'refer_{c}'].mean()) for c in CANDIDATES) + " |")

    if YEARS.exists():
        years = pd.read_csv(YEARS)[["slide_id", "case_year"]]
        rad = scores[(scores.center == "radboud") & (scores.dataset == "camelyon16")].merge(years, on="slide_id")
        lines += ["", "## Radboud, casi del 2015 (secondario, E3b)", "",
                  "| Valutazione | Positivi del 2015 | Positivi di altri anni | Negativi del 2015 | "
                  "Negativi di altri anni |",
                  "|---|---|---|---|---|"]
        for (rot, role), g in rad[rad.role != "calibrazione"].groupby(["rotation", "role"], sort=False):
            for c in CANDIDATES:
                cells = []
                for y in (1, 0):
                    for is15 in (True, False):
                        s = g[(g.label == y) & ((g.case_year == 2015) == is15)]
                        cells.append(f"{fmt(s[f'refer_{c}'].mean())} ({len(s)})")
                lines.append(f"| {rot}, {role}, {c} | " + " | ".join(cells) + " |")

    adopted = [c for c in CANDIDATES if not verdicts[c]]
    verdict = (f"adottabile {adopted[0]}" if adopted
               else "nessun candidato adottabile: `predict` resta con il controllo sui metadati")
    lines += ["", f"**Esito: {verdict}.**", ""]
    (E15 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in BACKBONES):
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
