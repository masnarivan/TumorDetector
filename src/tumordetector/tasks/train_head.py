"""`td task=train_head head=<id>`: a head trained on its cohort, validation report, model registry."""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from tumordetector.config import dataset_cfg
from tumordetector.io import code_version, write_json


def _train_seed(roots: dict, table: pd.DataFrame, mil: dict, seed: int, inner_folds: int, recipe: list) -> dict:
    """The whole protocol for one seed; module level so a worker process can run it."""
    import torch

    from tumordetector.heads.protocol import run_head_protocol

    torch.set_num_threads(mil["threads"])      # same seed and thread count -> same model (experiment E4)
    torch.use_deterministic_algorithms(True)
    root_of = {r.slide_id: Path(roots[r.dataset]) for r in table.itertuples()}
    # memory-mapped: parallel workers share one copy of the embeddings in the page cache
    bags = {s: np.load(root / f"{s}.npy", mmap_mode="r") for s, root in root_of.items()}
    return run_head_protocol(table, bags, lambda s: pd.read_parquet(root_of[s] / f"{s}.parquet").label.to_numpy(),
                             OmegaConf.create(mil), seed, inner_folds, recipe)


def run(cfg: DictConfig):
    """Development slides of the cohort only: the external ones are never loaded here. The gate
    reads the mean over seeds (mil.seeds); the model and temperature kept are the first seed's."""
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor

    import mlflow
    import torch
    from mlflow.models import ModelSignature
    from mlflow.types import Schema, TensorSpec

    from tumordetector.embed import store
    from tumordetector.heads import report
    from tumordetector.heads.cohort import check_unchanged, cohort_path, embedding_roots
    from tumordetector.heads.protocol import head_gate
    from tumordetector.heads.spec import HeadSpec
    from tumordetector.mil.evaluate import across_seeds

    code = code_version()   # at the start: a commit made while training must not be credited

    spec = HeadSpec(**OmegaConf.to_container(cfg.head, resolve=True))
    path = cohort_path(Path(cfg.paths.heads), spec)
    if not path.exists():
        raise SystemExit(f"no cohort for {spec.id}: run `td task=cohort head={spec.id}` first")
    cohort = pd.read_csv(path)
    datasets = {name: dataset_cfg(name) for name in spec.datasets}
    manifests = {name: pd.read_csv(d.manifest) for name, d in datasets.items()}
    check_unchanged(cohort, spec, manifests)
    roots, ident = embedding_roots({name: d.out for name, d in datasets.items()}, cfg.backbone.name)

    annot = pd.concat(manifests.values())[["slide_id", "exhaustive_annot"]]
    dev = cohort[cohort.role == "dev"].merge(annot, on="slide_id", validate="one_to_one")
    done = {s for name, root in roots.items() for s in store.list_slides(root)}
    excluded = dev[~dev.slide_id.isin(done)].assign(reason=f"nessun embedding {ident['collection']}")
    table = dev[dev.slide_id.isin(done)].reset_index(drop=True)
    if table.empty:
        raise SystemExit(f"no development slide of {spec.id} has embeddings")
    seeds = list(cfg.mil.seeds)
    if not seeds:
        raise SystemExit("mil.seeds is empty")
    args = ({k: str(v) for k, v in roots.items()}, table, OmegaConf.to_container(cfg.mil, resolve=True))
    workers = min(cfg.mil.workers, len(seeds))
    if workers > 1:
        with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            runs = [f.result() for f in [pool.submit(_train_seed, *args, s, spec.calibration.inner_folds, spec.recipe)
                                         for s in seeds]]
    else:
        runs = [_train_seed(*args, s, spec.calibration.inner_folds, spec.recipe) for s in seeds]

    metrics, spread = across_seeds([r["metrics"] for r in runs])
    result = {**runs[0], "metrics": metrics, "spread": spread, "seeds": seeds, "excluded": excluded,
              "predictions": pd.concat([r["predictions"].assign(seed=s) for r, s in zip(runs, seeds, strict=True)]),
              "attention": pd.concat([r["attention"].assign(seed=s) for r, s in zip(runs, seeds, strict=True)])}
    model_name = f"head-{spec.id}-{cfg.backbone.name}"
    mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)
    try:   # the probe of the version currently validated, for the non-regression rule
        validated = mlflow.MlflowClient().get_model_version_by_alias(model_name, "validated")
        previous_probe = float(validated.tags["center_probe_auroc"])
    except (mlflow.exceptions.MlflowException, KeyError, ValueError):
        previous_probe = None
    verdict = head_gate(metrics, result["n_dev"], spec.gate, previous_probe)
    cohort_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    hyper = {k: cfg.mil[k] for k in ("hidden", "dropout", "lr", "weight_decay", "epochs", "max_tiles", "threshold",
                                     "normalize", "threads")}
    context = {"Modello": model_name, "Testa": f"{spec.id} v{spec.version} ({spec.module})",
               "Cohort": f"{path} (sha256 {cohort_sha[:12]})", "Collezione embedding": ident["collection"],
               "Versione backbone": ident["version"], "Iperparametri": hyper,
               "Ricetta": ", ".join(spec.recipe) or "nessuna mitigazione",
               "Calibrazione": f"{spec.calibration.method}, {spec.calibration.inner_folds} fold interni nel LOCO",
               "Semi": f"{seeds} (modello e temperatura salvati: seme {seeds[0]})", "Versione codice": code}

    rep = (Path(cfg.mil.report_dir) if cfg.mil.report_dir
           else Path(cfg.paths.out) / "reports" / cfg.backbone.name / "heads" / spec.id)
    rep.mkdir(parents=True, exist_ok=True)
    (rep / "report.md").write_text(report.render(result, verdict, context))
    write_json(rep / "metrics.json", {"gate": verdict, "n_dev": result["n_dev"], "seeds": seeds,
                                      **metrics, "spread": spread})
    # The model returns a logit; the probability shown is sigmoid(logit / temperature).
    calibration = {"method": spec.calibration.method, "temperature": runs[0]["temperature"], "seed": seeds[0],
                   "fitted_on": "out-of-fold logits of the cross-validation", "n_slides": result["n_dev"],
                   "cohort_sha256": cohort_sha}
    write_json(rep / "calibration.json", calibration)
    result["predictions"].to_csv(rep / "predictions.csv", index=False)
    result["attention"].to_csv(rep / "attention.csv", index=False)
    excluded.to_csv(rep / "excluded.csv", index=False)

    mlflow.set_experiment(f"head-{spec.id}")
    with mlflow.start_run(run_name=model_name):
        mlflow.log_params({"backbone": cfg.backbone.name, "backbone_version": ident["version"],
                           "collection": ident["collection"], "head": spec.id, "head_version": spec.version,
                           "cohort_sha256": cohort_sha, "n_dev": result["n_dev"], "code_version": code,
                           "inner_folds": spec.calibration.inner_folds, "recipe": ",".join(spec.recipe) or "none",
                           **{f"mil.{k}": v for k, v in cfg.mil.items()}})
        flat = {"cv_auroc": "cv/auroc", "cv_ece": "cv/ece", "loco_worst_auroc": "loco_worst_auroc",
                "loco_worst_ece": "loco_worst_ece", "center_probe_auroc": "robustness/center_probe_auroc",
                "robustness_index": "robustness/robustness_index", "attention_auroc_mean": "attention_auroc_mean"}
        for name, key in flat.items():   # mean over seeds, and its spread
            if key in spread:
                mlflow.log_metrics({name: spread[key]["mean"], f"{name}_sd": spread[key]["sd"],
                                    f"{name}_min": spread[key]["min"]})
        mlflow.set_tag("validation_status", verdict["status"])
        mlflow.set_tag("registered", str(bool(cfg.mil.register)).lower())
        mlflow.log_artifacts(str(rep), artifact_path="validation")
        if result["model"] is not None:
            torch.save(result["model"].state_dict(), rep / "model.pt")
        if result["model"] is not None and cfg.mil.register:
            first = table.iloc[0]
            example = np.load(roots[first.dataset] / f"{first.slide_id}.npy", mmap_mode="r")[:8].astype(np.float32)
            signature = ModelSignature(inputs=Schema([TensorSpec(np.dtype("float32"), (-1, example.shape[1]))]))
            info = mlflow.pytorch.log_model(result["model"], name="model", input_example=example,
                                            signature=signature, registered_model_name=model_name)
            client = mlflow.MlflowClient()
            version = info.registered_model_version
            client.set_registered_model_alias(model_name, "candidate", version)
            if verdict["status"] == "passed":
                client.set_registered_model_alias(model_name, "validated", version)
            tags = {"validation_status": verdict["status"], "collection": ident["collection"],
                    "head_version": spec.version, "cohort_sha256": cohort_sha,
                    "recipe": ",".join(spec.recipe) or "none",
                    "center_probe_auroc": metrics.get("robustness", {}).get("center_probe_auroc"),
                    "temperature": calibration["temperature"]}
            for k, v in tags.items():
                client.set_model_version_tag(model_name, version, k, str(v))
    print(f"{model_name}: {result['n_dev']} development slides, battery {verdict['status']}",
          *verdict["reasons"], sep="\n  ")
    print(f"report -> {rep / 'report.md'}")
