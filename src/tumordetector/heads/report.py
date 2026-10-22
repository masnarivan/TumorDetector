"""Validation report (Markdown) of a head, generated at every training run and attached to the model."""
import pandas as pd

from tumordetector.heads.conformal import at_prevalence
from tumordetector.mil.report import VERDICT, _fmt, _metric_rows

BATTERY = [
    ("Leave-one-center-out, risultato peggiore", "sì, 4 centri, probabilità calibrate"),
    ("Test esterno bloccato", "no: è un task a parte, una consultazione per versione"),
    ("Robustezza al centro (Robustness Index, probe lineare sul centro)", "sì, sul modello finale"),
    ("Calibrazione (ECE)", "sì: temperatura globale; in leave-one-center-out stimata senza il centro escluso"),
    ("Copertura conformal", "sì: insiemi per classe (E10); copertura dei positivi sul centro escluso peggiore"),
    ("OOD", "no"),
    ("Metriche alla prevalenza reale, tasso di rinvio", "sì: rinvii, PPV e NPV degli insiemi sul centro escluso, "
     "prevalenza 5–30%; senza soglia"),
    ("Sottogruppi (scanner, tipo di campione)", "per centro, per dominio (dataset × centro) e per diagnosi "
     "(micro e macrometastasi)"),
    ("Regressione sui casi difficili", "no"),
]
SPREAD = ["cv/auroc", "cv/ece", "loco_worst_auroc", "loco_worst_ece", "loco_worst_ece_raw", "loco_worst_specificity",
          "robustness/center_probe_auroc", "robustness/center_probe_auroc_all", "robustness/robustness_index",
          "temperature/global", "attention_auroc_mean", "loco_worst_positive_coverage"]
SPREAD_SUFFIX = ("/auroc", "/ece", "/specificity", "/sensitivity")
PREVALENCES = [0.05, 0.10, 0.20, 0.30]   # share of positive slides: in CAMELYON17 about 0.35, in practice lower


def _diagnosis_lines(m: dict) -> list[str]:
    """Positives per diagnosis: the subgroup every correction of E9-E11 lost first (micrometastases)."""
    groups = {"Cross-validation": m.get("cv_by_diagnosis", {}), **m.get("loco_by_diagnosis", {})}
    if not any(groups.values()):
        return []
    rows = [f"| {g} | {d} | {_fmt(v.get('n'))} | {_fmt(v.get('sensitivity'))} | {_fmt(v.get('answered_positive'))} | "
            f"{_fmt(v.get('referred'))} | {_fmt(v.get('missed'))} |" for g, by in groups.items() for d, v in by.items()]
    worst = m.get("loco_worst_sensitivity_by_diagnosis", {})
    return ["### Positivi per diagnosi", "",
            "Sensibilità alla soglia 0,5 e, con gli insiemi conformal, quota con risposta «positivo», rinviata e "
            "persa (risposta «negativo»). In cross-validation i quantili sono stimati sulle stesse predizioni: "
            "ottimista. Sensibilità sul centro escluso peggiore: "
            + (", ".join(f"{d} **{_fmt(v)}**" for d, v in worst.items()) or "n/d") + ".", "",
            "| Valutazione | Diagnosi | Vetrini | Sensibilità | Risposta positivo | Rinviati | Persi |",
            "|---|---|---|---|---|---|---|", *rows, ""]


def _prevalence_lines(conformal: dict) -> list[str]:
    """Rates of the sets on each held-out centre, moved to a prevalence other than the cohort's."""
    held = {k: v for k, v in conformal.items() if k != "global" and v.get("a1") is not None}
    if not held:
        return []
    rows = []
    for k, r in held.items():
        cells = [at_prevalence(r, pi) for pi in PREVALENCES]
        rows.append(f"| {k} | " + " | ".join(f"{_fmt(c['referral'])} / {_fmt(c['ppv'])} / {_fmt(c['npv'])}"
                                            for c in cells) + " |")
    return ["### Alla prevalenza (insiemi conformal, centro escluso)", "",
            "Rinvii / PPV / NPV delle risposte se la quota di vetrini positivi fosse quella in colonna: tassi del "
            "centro escluso per classe, ricombinati (E10). Nessuna soglia: il tasso di rinvio accettabile lo "
            "decidono i patologi.", "",
            "| Rotazione | " + " | ".join(f"{pi:.0%}" for pi in PREVALENCES) + " |",
            "|" + "---|" * (1 + len(PREVALENCES)),
            *rows, ""]


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
        *_prevalence_lines(m.get("conformal", {})),
        *_diagnosis_lines(m),
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
