"""E8: the adversarial recipes against E6 with the adoption criterion fixed in docs/esperimenti.md.

Run the variants first (experiments/e8_run.sh), then `uv run python experiments/e8_compare.py`
-> data/reports/experiments/e8/summary.md.
"""
from pathlib import Path

import pandas as pd
from e7_compare import E6, row

from tumordetector.io import read_json

E8 = Path("data/reports/experiments/e8")
VARIANTS = ["balanced+adversarial", "balanced+adversarial_negatives"]   # tie-break prefers the second
CENTERS = ["cwz", "radboud", "rijnstate", "utrecht"]
PREDICTIONS = {"E6": Path("data/reports/phikon/heads/ln_metastasis/predictions.csv")}

# (metric path in "spread", label, better direction, role, margin), as in e7_compare
CRITERIA = [
    ("loco_worst_ece", "ECE calibrata peggiore LOCO", "down", "primary", 0.03),
    ("loco_worst_specificity", "Specificità peggiore LOCO", "up", "primary", 0.10),
    ("loco_worst_auroc", "AUROC peggiore LOCO", "up", "constraint", 0.01),
    ("cv/auroc", "AUROC CV", "up", "constraint", 0.01),
    ("attention_auroc_mean", "AUROC attenzione", "up", "constraint", 0.02),
    *[(f"loco/held-out {c}/specificity", f"Specificità, {c} escluso", "up", "constraint", 0.05) for c in CENTERS],
]
SECONDARY = [("robustness/center_probe_auroc", "Probe sul centro (negativi)"),
             ("robustness/robustness_index", "Robustness Index"),
             ("loco_worst_ece_raw", "ECE grezza peggiore LOCO"),
             ("temperature/global", "Temperatura globale")]


def judge(ref: dict, var: dict) -> tuple[bool, list[str], list[str]]:
    met, broken = [], []
    for path, label, better, role, margin in CRITERIA:
        delta = var["spread"][path]["mean"] - ref["spread"][path]["mean"]
        gain = -delta if better == "down" else delta
        if role == "primary" and gain >= margin:
            met.append(label)
        if role == "constraint" and gain < -margin:
            broken.append(label)
    return bool(met) and not broken, met, broken


def negative_logits(paths: dict) -> str:
    """Median logit of the negative slides of each centre, seen (CV) and held out (LOCO): the E6 measure."""
    cols = [f"{c} {g}" for c in CENTERS for g in ("cv", "loco")]
    lines = ["| Variante | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for name, path in paths.items():
        if not path.exists():
            continue
        p = pd.read_csv(path)
        med = p[p.y == 0].groupby(["center", "group"]).logit.median()
        lines.append(f"| {name} | " + " | ".join(f"{med.get((c, g), float('nan')):.1f}" for c, g in
                                                (x.split() for x in cols)) + " |")
    return "\n".join(lines)


def main():
    ref = read_json(E6)
    runs = {v: read_json(E8 / v / "metrics.json") for v in VARIANTS if (E8 / v / "metrics.json").exists()}
    if missing := [v for v in VARIANTS if v not in runs]:
        raise SystemExit(f"variants not run yet: {missing}")
    lines = ["# E8 — confronto con E6", "", "Media sui semi (valori dei semi tra parentesi); Δ = variante − E6.", "",
             "| Metrica | E6 | " + " | ".join(f"{v} | Δ" for v in runs) + " |", "|" + "---|" * (2 + 2 * len(runs))]
    lines += [row(label, path, ref, runs) for path, label, *_ in CRITERIA]
    lines += [row(label, path, ref, runs) for path, label in SECONDARY]
    lines += ["", "## Logit mediana dei negativi (centro visto in CV, centro escluso in LOCO)", "",
              negative_logits({**PREDICTIONS, **{v: E8 / v / "predictions.csv" for v in runs}}),
              "", "## Criterio di adozione", ""]
    adoptable = []
    for v, m in runs.items():
        ok, met, broken = judge(ref, m)
        gate = m["gate"]["status"]
        lines.append(f"- **{v}**: {'adottabile' if ok else 'non adottabile'}; primari raggiunti: "
                     f"{', '.join(met) or 'nessuno'}; vincoli violati: {', '.join(broken) or 'nessuno'}; gate: {gate}.")
        if ok:
            adoptable.append((gate != "passed", -VARIANTS.index(v), v))   # passes the gate, then the second
    choice = min(adoptable)[2] if adoptable else None
    verdict = f"adottata {choice}" if choice else "nessuna variante adottata, si tiene la ricetta vuota"
    lines += ["", f"**Esito: {verdict}.**", ""]
    (E8 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
