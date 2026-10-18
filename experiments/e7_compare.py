"""E7: each mitigation against E6 with the adoption criterion fixed in docs/esperimenti.md.

Run the variants first (same code, same seeds, nothing registered):

  td task=train_head "head.recipe=[balanced]" mil.register=false mil.report_dir=data/reports/experiments/e7/<name>

for each <name> in VARIANTS (the recipe is the name split on "+"), or experiments/e7_run.sh;

then `uv run python experiments/e7_compare.py` -> data/reports/experiments/e7/summary.md.
"""
from pathlib import Path

from tumordetector.io import read_json

E6 = Path("data/reports/experiments/e6/metrics.json")     # frozen copy: the DVC stage is rewritten on adoption
E7 = Path("data/reports/experiments/e7")
VARIANTS = ["balanced", "balanced+group_dro", "balanced+stat_mix"]   # protocol order: simplest first

# (metric path in metrics.json "spread", label, better direction, role, margin)
#   primary: improves by at least `margin`; constraint: does not get worse by more than `margin`
CRITERIA = [
    ("loco_worst_ece", "ECE calibrata peggiore LOCO", "down", "primary", 0.03),
    ("robustness/center_probe_auroc", "Probe sul centro (negativi)", "down", "primary", 0.10),
    ("loco_worst_auroc", "AUROC peggiore LOCO", "up", "constraint", 0.01),
    ("cv/auroc", "AUROC CV", "up", "constraint", 0.01),
    ("loco_worst_specificity", "Specificità peggiore LOCO", "up", "constraint", 0.02),
    ("attention_auroc_mean", "AUROC attenzione", "up", "constraint", 0.02),
]
SECONDARY = [("robustness/robustness_index", "Robustness Index"),
             ("loco_worst_ece_raw", "ECE grezza peggiore LOCO"),
             ("loco/held-out utrecht/specificity", "Specificità, Utrecht escluso"),
             ("loco/held-out cwz/specificity", "Specificità, CWZ escluso"),
             ("temperature/global", "Temperatura globale")]


def judge(ref: dict, var: dict) -> tuple[bool, list[str], list[str]]:
    """-> (adoptable, primaries met, constraints broken), on means over seeds."""
    met, broken = [], []
    for path, label, better, role, margin in CRITERIA:
        delta = var["spread"][path]["mean"] - ref["spread"][path]["mean"]
        gain = -delta if better == "down" else delta
        if role == "primary" and gain >= margin:
            met.append(label)
        if role == "constraint" and gain < -margin:
            broken.append(label)
    return bool(met) and not broken, met, broken


def row(label: str, path: str, ref: dict, runs: dict) -> str:
    def cell(m):
        s = m["spread"].get(path)
        return "n/d" if s is None else f"{s['mean']:.3f} ({'; '.join(f'{v:.3f}' for v in s['values'])})"
    deltas = [f"{runs[v]['spread'][path]['mean'] - ref['spread'][path]['mean']:+.3f}" for v in runs]
    cells = [f"{cell(runs[v])} | {d}" for v, d in zip(runs, deltas, strict=True)]
    return f"| {label} | {cell(ref)} | " + " | ".join(cells) + " |"


def main():
    ref = read_json(E6)
    runs = {v: read_json(E7 / v / "metrics.json") for v in VARIANTS if (E7 / v / "metrics.json").exists()}
    if missing := [v for v in VARIANTS if v not in runs]:
        raise SystemExit(f"variants not run yet: {missing}")
    head = "| Metrica | E6 | " + " | ".join(f"{v} | Δ" for v in runs) + " |"
    lines = ["# E7 — confronto con E6", "", "Media sui semi (valori dei semi tra parentesi); Δ = variante − E6.", "",
             head, "|" + "---|" * (2 + 2 * len(runs))]
    lines += [row(label, path, ref, runs) for path, label, *_ in CRITERIA]
    lines += [row(label, path, ref, runs) for path, label in SECONDARY]
    lines += ["", "## Criterio di adozione", ""]
    adoptable = []
    for v, m in runs.items():
        ok, met, broken = judge(ref, m)
        gate = m["gate"]["status"]
        lines.append(f"- **{v}**: {'adottabile' if ok else 'non adottabile'}; primari raggiunti: "
                     f"{', '.join(met) or 'nessuno'}; vincoli violati: {', '.join(broken) or 'nessuno'}; gate: {gate}.")
        if ok:
            adoptable.append((gate != "passed", VARIANTS.index(v), v))   # passes the gate first, then simplest
    choice = min(adoptable)[2] if adoptable else None
    verdict = f"adottata {choice}" if choice else "nessuna variante adottata, si tiene la ricetta vuota"
    lines += ["", f"**Esito: {verdict}.**", ""]
    (E7 / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
