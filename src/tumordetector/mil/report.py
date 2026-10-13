"""Validation report (Markdown) generated at every training run and attached to the model."""
import pandas as pd

VERDICT = {"passed": "SUPERATA", "failed": "NON SUPERATA", "insufficient_data": "DATI INSUFFICIENTI"}

# The plan's promotion battery, and what this report covers of it.
BATTERY = [
    ("Leave-one-center-out, risultato peggiore", "sì"),
    ("Test esterno bloccato", "sì, quando gli embedding dello split di test sono disponibili"),
    ("Robustezza al centro (Robustness Index, probe lineare sul centro)", "no"),
    ("Calibrazione (ECE)", "sì, aggregata; per centro nella tabella per centro"),
    ("Copertura conformal", "no: il modello non produce ancora insiemi di predizione"),
    ("OOD", "no"),
    ("Metriche alla prevalenza reale, tasso di rinvio", "no"),
    ("Sottogruppi (scanner, tipo di campione)", "solo per centro"),
    ("Regressione sui casi difficili", "no"),
]


def _fmt(v) -> str:
    return "n/d" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)


def _metric_rows(named: dict) -> str:
    cols = ["n", "n_pos", "auroc", "sensitivity", "specificity", "balanced_accuracy", "brier", "ece"]
    head = "| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |"
    lines = [head, "|" + "---|" * 9]
    for name, m in named.items():
        lines.append(f"| {name} | " + " | ".join(_fmt(m.get(c)) for c in cols) + " |" if m
                     else f"| {name} | 0 | | | | | | | |")
    return "\n".join(lines)


def render(result: dict, verdict: dict, context: dict) -> str:
    m = result["metrics"]
    runs = pd.DataFrame(result["runs"])
    out = [
        f"# Report di validazione — {context['Modello']}",
        "",
        f"**Esito della batteria: {VERDICT[verdict['status']]}**",
        "",
        *[f"- {r}" for r in verdict["reasons"]],
        "",
        "Solo uso di ricerca. Le soglie della batteria sono proposte iniziali, da fissare con i patologi.",
        "",
        "## Provenienza",
        "",
        "| | |",
        "|---|---|",
        *[f"| {k} | `{v}` |" for k, v in context.items()],
        f"| Vetrini con embedding | {result['n_slides']} ({result['n_dev']} sviluppo, "
        f"{result['n_held_out']} test bloccato) |",
        "",
        "## Risultati",
        "",
        _metric_rows({"Cross-validation (predizioni fuori fold, aggregate)": m["cv"],
                      **{f"Leave-one-center-out, {k}": v for k, v in m["loco"].items()},
                      "Split di test bloccato": m["test"]}),
        "",
        f"AUROC peggiore tra i centri esclusi: **{_fmt(m['loco_worst_auroc'])}**.",
        "",
        "### Per centro",
        "",
        _metric_rows({**{f"Cross-validation, {k}": v for k, v in m["cv_by_center"].items()},
                      **{f"Test bloccato, {k}": v for k, v in m["test_by_center"].items()}}),
        "",
        "### Localizzazione",
        "",
        f"AUROC dell'attenzione nel distinguere tile tumorali da normali, media sui vetrini positivi con "
        f"annotazione completa (fuori fold): **{_fmt(m['attention_auroc_mean'])}** "
        f"su {int((result['attention'].group == 'cv').sum())} vetrini.",
        "",
        "## Esecuzioni",
        "",
        "| Gruppo | Valutazione | Vetrini di training | Vetrini valutati | Stato | Motivo |",
        "|---|---|---|---|---|---|",
        *[f"| {r.group} | {r['name']} | {r.n_train} | {r.n_test} | {r.status} | {r.reason} |"
          for _, r in runs.iterrows()],
        "",
        "## Copertura della batteria di promozione",
        "",
        "| Voce del piano | Coperta da questo report |",
        "|---|---|",
        *[f"| {a} | {b} |" for a, b in BATTERY],
        "",
    ]
    return "\n".join(out)
