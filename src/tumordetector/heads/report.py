"""Validation report (Markdown) of a head, generated at every training run and attached to the model."""
import pandas as pd

from tumordetector.mil.report import VERDICT, _fmt, _metric_rows

BATTERY = [
    ("Leave-one-center-out, risultato peggiore", "sì, 4 centri, probabilità calibrate"),
    ("Test esterno bloccato", "no: è un task a parte, una consultazione per versione"),
    ("Robustezza al centro (Robustness Index, probe lineare sul centro)", "sì, sul modello finale"),
    ("Calibrazione (ECE)", "sì: temperatura globale; in leave-one-center-out stimata senza il centro escluso"),
    ("Copertura conformal", "sì: insiemi per classe (E10); copertura dei positivi sul centro escluso peggiore"),
    ("OOD", "no"),
    ("Metriche alla prevalenza reale, tasso di rinvio", "no"),
    ("Sottogruppi (scanner, tipo di campione)", "per centro e per dominio (dataset × centro)"),
    ("Regressione sui casi difficili", "no"),
]
SPREAD = ["cv/auroc", "cv/ece", "loco_worst_auroc", "loco_worst_ece", "loco_worst_ece_raw", "loco_worst_specificity",
          "robustness/center_probe_auroc", "robustness/center_probe_auroc_all", "robustness/robustness_index",
          "temperature/global", "attention_auroc_mean", "loco_worst_positive_coverage"]
SPREAD_SUFFIX = ("/auroc", "/ece", "/specificity", "/sensitivity")


def _spread_rows(spread: dict, seeds: list) -> str:
    paths = SPREAD + [p for p in spread if p.startswith(("loco/", "loco_by_domain/")) and p.endswith(SPREAD_SUFFIX)]
    lines = ["| Metrica | Media | DS | Min | Max | " + " | ".join(f"Seme {s}" for s in seeds) + " |",
             "|" + "---|" * (5 + len(seeds))]
    for p in paths:
        if p in spread:
            v = spread[p]
            lines.append(f"| {p} | " + " | ".join(_fmt(v[k]) for k in ("mean", "sd", "min", "max"))
                         + " | " + " | ".join(_fmt(x) for x in v["values"]) + " |")
    return "\n".join(lines)


def _conformal_lines(conformal: dict, worst: float | None) -> list[str]:
    """Quantiles per class and, per held-out centre, the coverage of its sets (mean over seeds)."""
    if not conformal:
        return []
    g = conformal.get("global", {})
    rows = [f"| {k} | {_fmt(v.get('q0'))} | {_fmt(v.get('q1'))} | {_fmt(v.get('positive_coverage'))} | "
            f"{_fmt(v.get('negative_coverage'))} | {_fmt(v.get('referral'))} |"
            for k, v in conformal.items() if k != "global"]
    return ["### Insiemi conformal per classe", "",
            f"Quantili del modello finale (CV fuori fold): q0 {_fmt(g.get('q0'))}, q1 {_fmt(g.get('q1'))}. "
            "Insieme {0} o {1}: risposta; {0, 1} o vuoto: rinvio. In leave-one-center-out i quantili vengono "
            f"dai fold interni della rotazione. Copertura dei positivi sul centro escluso peggiore: "
            f"**{_fmt(worst)}**.", "",
            "| Rotazione | q0 | q1 | Copertura positivi | Copertura negativi | Rinvii |", "|---|---|---|---|---|---|",
            *rows, ""]


def render(result: dict, verdict: dict, context: dict) -> str:
    m, seeds = result["metrics"], result["seeds"]
    rob, temp = m.get("robustness", {}), m.get("temperature", {})
    runs = pd.DataFrame(result["runs"])
    excluded = result["excluded"]
    out = [
        f"# Report di validazione — {context['Modello']}",
        "",
        f"**Esito della batteria: {VERDICT[verdict['status']]}** (media su {len(seeds)} semi)",
        "",
        *[f"- {r}" for r in verdict["reasons"]],
        *[f"- *{n}*" for n in verdict.get("notes", [])],
        "",
        "Solo uso di ricerca. Le soglie della batteria sono proposte iniziali, da fissare con i patologi.",
        "",
        "## Provenienza",
        "",
        "| | |",
        "|---|---|",
        *[f"| {k} | `{v}` |" for k, v in context.items()],
        f"| Vetrini di sviluppo con embedding | {result['n_dev']} |",
        f"| Vetrini del cohort lasciati fuori | {len(excluded)}"
        + (f": {', '.join(sorted(excluded.reason.unique()))}" if len(excluded) else "") + " |",
        "",
        "## Risultati",
        "",
        f"Media su {len(seeds)} semi ({', '.join(map(str, seeds))}). Probabilità calibrate con la temperatura "
        "(in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della "
        "rotazione, stimata senza il centro escluso).",
        "",
        _metric_rows({"Cross-validation, calibrata": m["cv"], "Cross-validation, grezza": m["cv_raw"],
                      **{f"Leave-one-center-out, {k}": v for k, v in m["loco"].items()}}),
        "",
        f"Centro escluso peggiore (per seme, poi media): AUROC **{_fmt(m['loco_worst_auroc'])}**, "
        f"ECE calibrata **{_fmt(m['loco_worst_ece'])}** (grezza {_fmt(m['loco_worst_ece_raw'])}), "
        f"specificità **{_fmt(m['loco_worst_specificity'])}**.",
        "",
        "Temperature (media sui semi): " + ", ".join(f"{k} {_fmt(v)}" for k, v in temp.items()) + ".",
        "",
        *_conformal_lines(m.get("conformal", {}), m.get("loco_worst_positive_coverage")),
        "### Per centro e per dominio",
        "",
        _metric_rows({**{f"Cross-validation, {k}": v for k, v in m["cv_by_center"].items()},
                      **{f"Cross-validation, {k}": v for k, v in m["cv_by_domain"].items()},
                      **{f"{e}, {d}": v for e, by in m["loco_by_domain"].items() for d, v in by.items()}}),
        "",
        "### Robustezza al centro (modello finale)",
        "",
        f"- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: "
        f"**{_fmt(rob.get('center_probe_auroc'))}** sui vetrini negativi, {_fmt(rob.get('center_probe_auroc_all'))} "
        "su tutti (0,5 = centro non leggibile).",
        f"- Robustness Index sulle tile: **{_fmt(rob.get('robustness_index'))}** (> 1: domina la biologia); "
        f"vicini dallo stesso centro {_fmt(rob.get('ri_same_center_fraction'))}, "
        f"su {int(rob['ri_tiles']) if rob.get('ri_tiles') is not None else 'n/d'} tile.",
        "",
        "### Localizzazione",
        "",
        f"AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori "
        f"fold): **{_fmt(m['attention_auroc_mean'])}**.",
        "",
        "## Variabilità tra semi",
        "",
        _spread_rows(result["spread"], seeds),
        "",
        f"## Esecuzioni (seme {seeds[0]})",
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
