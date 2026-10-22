"""`td task=external head=<id> external.version=<n>`: the locked external test of a head, once per version.

Only a version holding the 'validated' alias, and only once: every consultation is a row of the log
(external.log, versioned in git), written *before* any external embedding is read, so a run that
stops halfway still counts. A second consultation of the same version is refused.

Three measures (docs/training-multicentro.md): whether the external slides are referred as an unseen
centre or scanner (the first step of a new centre's entry), the answers the version would give if it
answered anyway (day zero: discrimination, calibration, conformal coverage), per scanner.
"""
import datetime
from pathlib import Path

import pandas as pd
from omegaconf import DictConfig, OmegaConf

from tumordetector.config import dataset_cfg
from tumordetector.io import code_version, write_json

LOG_COLUMNS = ["date", "head", "head_version", "model", "model_version", "collection", "code_version", "status",
               "n_slides", "auroc", "sensitivity", "specificity", "ece", "positive_coverage", "referral_unseen"]


def _fmt(x) -> str:
    return "n/d" if x is None or pd.isna(x) else f"{x:.3f}"


def run(cfg: DictConfig):
    from tumordetector.embed import store
    from tumordetector.heads.cohort import check_unchanged, cohort_path, embedding_roots
    from tumordetector.heads.conformal import coverage
    from tumordetector.heads.spec import HeadSpec
    from tumordetector.mil.evaluate import binary_metrics
    from tumordetector.serve import registry
    from tumordetector.serve.answer import answer

    spec = HeadSpec(**OmegaConf.to_container(cfg.head, resolve=True))
    if cfg.external.version is None:
        raise SystemExit("which version? external.version=<n>: it must hold the 'validated' alias")
    model_name = f"head-{spec.id}-{cfg.backbone.name}"
    log_path = Path(cfg.external.log)
    log = pd.read_csv(log_path) if log_path.exists() else pd.DataFrame(columns=LOG_COLUMNS)
    done = log[(log.model == model_name) & (log.model_version == int(cfg.external.version))]
    if len(done):
        raise SystemExit(f"{model_name} v{cfg.external.version} already consulted the external test on "
                         f"{done.date.iloc[0]} (status {done.status.iloc[0]}): once per version")

    path = cohort_path(Path(cfg.paths.heads), spec)
    if not path.exists():
        raise SystemExit(f"no cohort for {spec.id}: run `td task=cohort head={spec.id}` first")
    cohort = pd.read_csv(path)
    datasets = {name: dataset_cfg(name) for name in spec.datasets}
    manifests = {name: pd.read_csv(d.manifest) for name, d in datasets.items()}
    check_unchanged(cohort, spec, manifests)
    scanner = pd.concat(manifests.values())[["slide_id", "scanner"]]
    ext = cohort[cohort.role == "external"].merge(scanner, on="slide_id", validate="one_to_one")
    if ext.empty:
        raise SystemExit(f"{spec.id} has no external slides")
    roots, ident = embedding_roots({name: d.out for name, d in datasets.items()}, cfg.backbone.name)
    if todo := sorted(r.slide_id for r in ext.itertuples() if not store.is_done(roots[r.dataset], r.slide_id)):
        raise SystemExit(f"{len(todo)} external slides without {ident['collection']} embeddings (e.g. {todo[:3]}): "
                         "the test is consulted on all of them or not at all")
    head = registry.load(cfg.mlflow.tracking_uri, model_name, ident["collection"], version=int(cfg.external.version))
    if not head.validated:
        raise SystemExit(f"{model_name} v{head.version} does not hold the 'validated' alias: "
                         "only a version that passed its battery consults the external test")

    code = code_version()
    row = {"date": datetime.date.today().isoformat(), "head": spec.id, "head_version": spec.version,
           "model": model_name, "model_version": head.version, "collection": ident["collection"],
           "code_version": code, "status": "avviata", "n_slides": len(ext)}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = pd.concat([log, pd.DataFrame([row])], ignore_index=True)[LOG_COLUMNS]
    log.to_csv(log_path, index=False)                  # counted from here on, whatever happens next

    preds = []
    for r in ext.itertuples():
        logit, p, _ = head.score(store.read_slide(roots[r.dataset], r.slide_id).features)
        seen = answer(p, head.q0, head.q1, head.validated, r.center in head.centers, r.scanner in head.scanners)
        day0 = answer(p, head.q0, head.q1, head.validated, None, None)
        preds.append({"slide_id": r.slide_id, "center": r.center, "scanner": r.scanner, "y": r.label,
                      "reference_diagnosis": r.reference_diagnosis, "logit": logit, "p": p,
                      "decision": seen["decision"], "unseen": any("non visto" in x for x in seen["reasons"]),
                      "set": "".join(map(str, day0["set"])) or "vuoto", "decision_day0": day0["decision"]})
    preds = pd.DataFrame(preds)

    def measure(g: pd.DataFrame) -> dict:
        m = binary_metrics(g.y, g.p)
        c = coverage(g.p, g.y, head.q0, head.q1)
        return {**m, **c, "referral_unseen": float(g.unseen.mean())}

    overall = measure(preds)
    by_scanner = {s: measure(g) for s, g in preds.groupby("scanner")}
    rep = Path(cfg.paths.out) / "reports" / cfg.backbone.name / "external" / spec.id / f"v{head.version}"
    rep.mkdir(parents=True, exist_ok=True)
    preds.to_csv(rep / "predictions.csv", index=False)
    write_json(rep / "metrics.json", {"overall": overall, "by_scanner": by_scanner, "model": model_name,
                                      "model_version": head.version, "code_version": code})
    cols = ["n", "n_pos", "auroc", "sensitivity", "specificity", "ece", "positive_coverage", "negative_coverage",
            "referral", "referral_unseen"]
    lines = [f"# Test esterno — {model_name} v{head.version}", "",
             f"Consultazione del {row['date']}, l'unica per questa versione (registro: `{log_path}`). "
             f"Codice `{code}`, collezione `{ident['collection']}`, testa {spec.id} v{spec.version}.", "",
             f"- **Rinvio come centro o scanner non visto**: {_fmt(overall['referral_unseen'])} dei vetrini "
             f"(centri della versione: {', '.join(sorted(head.centers))}; "
             f"scanner: {', '.join(sorted(head.scanners))}).",
             "- **Giorno zero** (se la versione rispondesse comunque): soglia 0,5 sulla probabilità calibrata "
             f"(temperatura {head.temperature:.3f}); insiemi conformal per classe, alpha {head.alpha}.", "",
             "| Gruppo | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1),
             *[f"| {k} | " + " | ".join(_fmt(v.get(c)) if c not in ("n", "n_pos") else str(v.get(c)) for c in cols)
               + " |" for k, v in {"tutti": overall, **{f"scanner {s}": m for s, m in by_scanner.items()}}.items()],
             "", "Solo uso di ricerca."]
    (rep / "report.md").write_text("\n".join(lines) + "\n")

    log.loc[log.index[-1], ["status", "auroc", "sensitivity", "specificity", "ece", "positive_coverage",
                            "referral_unseen"]] = ["conclusa", overall["auroc"], overall["sensitivity"],
                                                   overall["specificity"], overall["ece"],
                                                   overall["positive_coverage"], overall["referral_unseen"]]
    log.to_csv(log_path, index=False)
    print(f"{model_name} v{head.version} on the external test: AUROC {_fmt(overall['auroc'])}, "
          f"referred as unseen {_fmt(overall['referral_unseen'])}")
    print(f"report -> {rep / 'report.md'}; log -> {log_path}")
