"""E16b: H-optimus-0 against Phikon at slide level with E12's tile classifier (top-5 over all tiles), with the
criterion fixed in docs/esperimenti.md. E12's code unchanged, only the embedding folders differ; the Phikon arm must
reproduce E12's cached scores before H-optimus-0 is looked at. LPON is never read.
-> data/reports/experiments/e16b/{tile_classifier_<backbone>.csv, metrics.csv, summary.md}

    uv run python experiments/e16b_slide.py
"""
import sys
from pathlib import Path

import e12_tile_score as e12
import pandas as pd

E16B = Path("data/reports/experiments/e16b")
BACKBONES = ["phikon", "h_optimus_0"]
K = e12.K_MAIN
SPEC_GAIN, MICRO_LOSS, AUROC_LOSS = 0.10, 0.05, 0.01
MAX_DIFF = 1e-4


def roots(backbone: str) -> dict:
    return {"camelyon16": Path("data/embeddings") / backbone,
            "camelyon17": Path("data/camelyon17/embeddings") / backbone}


def tops(table: pd.DataFrame, backbone: str) -> pd.DataFrame:
    path = E16B / f"tile_classifier_{backbone}.csv"
    if path.exists():
        return pd.read_csv(path)
    e12.ROOTS = roots(backbone)          # bag() and tile_labels() read this
    out = e12.classifier_tops(table)
    out.to_csv(path, index=False)
    return out


def control(phikon: pd.DataFrame) -> float:
    key = ["seed", "evaluation", "group", "slide_id", "rank"]
    m = phikon.merge(pd.read_csv(e12.CLASSIFIER)[key + ["logit"]], on=key, suffixes=("", "_e12"), how="outer")
    if m.logit.isna().any() or m.logit_e12.isna().any():
        raise SystemExit("Phikon arm: rows without a match in E12's scores")
    return float((m.logit - m.logit_e12).abs().max())


def main():
    E16B.mkdir(parents=True, exist_ok=True)
    table = e12.load_table()
    res = {}
    for b in BACKBONES:
        clf = tops(table, b)
        if b == "phikon":
            diff = control(clf)
            print(f"Phikon against E12: max difference {diff:.2e}", file=sys.stderr)
            if diff > MAX_DIFF:
                raise SystemExit(f"the Phikon arm does not reproduce E12 ({diff:.2e} > {MAX_DIFF}): stop")
        e12.ROOTS = roots(b)
        res[b] = e12.evaluate(e12.tops_to_scores(clf, K), table, clf)
    pd.concat([r.assign(backbone=b) for b, r in res.items()]).to_csv(E16B / "metrics.csv", index=False)
    mean = {b: r.groupby("center").mean(numeric_only=True) for b, r in res.items()}
    p, h = mean["phikon"], mean["h_optimus_0"]
    spec = h.specificity.min() - p.specificity.min()
    micro = h.sens_micro.min() - p.sens_micro.min()
    auroc = h.auroc.min() - p.auroc.min()
    ok = spec >= SPEC_GAIN and micro >= -MICRO_LOSS and auroc >= -AUROC_LOSS
    yes = {True: "sì", False: "no"}
    f = e12.fmt
    lines = ["# E16b — H-optimus-0 contro Phikon, classificatore di tile top-5 per vetrino", "",
             f"Controllo: il braccio Phikon coincide con E12 (differenza massima {diff:.2e}). Media sui semi "
             f"{e12.SEEDS}; τ al {e12.SENS_TARGET:.0%} dei positivi dei centri di training, fuori fold. "
             "LPON non letto.",
             "", "## Criterio", "",
             "| Centro escluso peggiore | Phikon | H-optimus-0 | Differenza | Soglia | Rispettato |",
             "|---|---|---|---|---|---|",
             f"| Specificità | {f(p.specificity.min())} ({p.specificity.idxmin()}) | {f(h.specificity.min())} "
             f"({h.specificity.idxmin()}) | {spec:+.3f} | ≥ +{SPEC_GAIN} | {yes[spec >= SPEC_GAIN]} |",
             f"| Sensibilità micro | {f(p.sens_micro.min())} ({p.sens_micro.idxmin()}) | {f(h.sens_micro.min())} "
             f"({h.sens_micro.idxmin()}) | {micro:+.3f} | ≥ −{MICRO_LOSS} | {yes[micro >= -MICRO_LOSS]} |",
             f"| AUROC | {f(p.auroc.min())} | {f(h.auroc.min())} | {auroc:+.3f} | ≥ −{AUROC_LOSS} | "
             f"{yes[auroc >= -AUROC_LOSS]} |",
             "", f"**Esito: H-optimus-0 {'promettente' if ok else 'non promettente'} a livello di vetrino.**", "",
             "## Per centro escluso", "",
             "| Centro | Backbone | Specificità (semi) | Sens. micro (semi) | Sens. macro | AUROC | AUROC micro | "
             "Mediana negativi (training) | Localizzazione |", "|" + "---|" * 9]
    for c in sorted(p.index):
        for b in BACKBONES:
            m, g = mean[b].loc[c], res[b][res[b].center == c].sort_values("seed")
            sp, mi = ", ".join(f(v) for v in g.specificity), ", ".join(f(v) for v in g.sens_micro)
            lines.append(f"| {c} | {b} | {f(m.specificity)} ({sp}) | {f(m.sens_micro)} ({mi}) | "
                         f"{f(m.sens_macro)} | {f(m.auroc)} | {f(m.auroc_micro)} | "
                         f"{m.neg_median:.2f} ({m.cal_neg_median:.2f}) | {f(m.localised)} |")
    (E16B / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
