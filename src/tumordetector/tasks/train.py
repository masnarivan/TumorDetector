"""`td task=train`: ABMIL baseline, validation report, model registry."""
from pathlib import Path

import numpy as np
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from tumordetector.io import code_version, read_json, write_json
from tumordetector.tasks.common import load_manifest, splits_path


def _train_seed(root: str, table: pd.DataFrame, mil: dict, seed: int) -> dict:
    """The whole validation protocol for one seed; module level so a worker process can run it."""
    import torch

    from tumordetector.mil.evaluate import run_protocol

    # Same seed, same thread count -> same model; a different count changes the summation order and,
    # through 30 epochs, the model (experiment E4: up to 0.5 on a slide's probability).
    torch.set_num_threads(mil["threads"])
    torch.use_deterministic_algorithms(True)
    root = Path(root)
    # memory-mapped: parallel workers share one copy of the embeddings in the page cache
    bags = {s: np.load(root / f"{s}.npy", mmap_mode="r") for s in table.slide_id}
    return run_protocol(table, bags, lambda s: pd.read_parquet(root / f"{s}.parquet").label.to_numpy(),
                        OmegaConf.create(mil), seed)


def run(cfg: DictConfig):
    """The gate judges the training recipe, not one draw of it: the protocol runs once per seed
    (mil.seeds) and the battery reads the mean. The model kept is the first seed's."""
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor

    import mlflow
    import torch
    from mlflow.models import ModelSignature
    from mlflow.types import Schema, TensorSpec

    from tumordetector.embed import store
    from tumordetector.mil import report
    from tumordetector.mil.evaluate import across_seeds, gate

    code = code_version()   # at the start: a commit made while training must not be credited

    out = Path(cfg.paths.out)
    root = out / "embeddings" / cfg.backbone.name
    ident = read_json(root / "collection.json")
    table = load_manifest(cfg).merge(pd.read_csv(splits_path(cfg)), on="slide_id", validate="one_to_one")
    table = table[table.slide_id.isin(store.list_slides(root))].reset_index(drop=True)
    if table.empty:
        raise SystemExit(f"no embeddings in {root}")
    seeds = list(cfg.mil.seeds)
    if not seeds:
        raise SystemExit("mil.seeds is empty")
    args = (str(root), table, OmegaConf.to_container(cfg.mil, resolve=True))
    workers = min(cfg.mil.workers, len(seeds))
    if workers > 1:
        with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            runs = [f.result() for f in [pool.submit(_train_seed, *args, s) for s in seeds]]
    else:
        runs = [_train_seed(*args, s) for s in seeds]

    metrics, spread = across_seeds([r["metrics"] for r in runs])
    result = {**runs[0], "metrics": metrics, "spread": spread, "seeds": seeds,
              "predictions": pd.concat([r["predictions"].assign(seed=s) for r, s in zip(runs, seeds, strict=True)]),
              "attention": pd.concat([r["attention"].assign(seed=s) for r, s in zip(runs, seeds, strict=True)])}
    verdict = gate(metrics, result["n_slides"], cfg.gate)
    model_name = f"abmil-{cfg.data.name}-{cfg.backbone.name}"
    hyper = {k: cfg.mil[k] for k in ("hidden", "dropout", "lr", "weight_decay", "epochs", "max_tiles", "threshold",
                                     "normalize", "threads")}
    context = {"Modello": model_name, "Collezione embedding": ident["collection"],
               "Versione backbone": ident["version"], "Split": f"{splits_path(cfg)} (seed {cfg.seed})",
               "Iperparametri": hyper, "Semi": f"{seeds} (modello salvato: seme {seeds[0]})",
               "Versione codice": code}

    rep = Path(cfg.mil.report_dir) if cfg.mil.report_dir else out / "reports" / cfg.backbone.name / "abmil"
    rep.mkdir(parents=True, exist_ok=True)
    (rep / "report.md").write_text(report.render(result, verdict, context))
    write_json(rep / "metrics.json", {"gate": verdict, "n_slides": result["n_slides"], "seeds": seeds,
                                      **metrics, "spread": spread})
    result["predictions"].to_csv(rep / "predictions.csv", index=False)
    result["attention"].to_csv(rep / "attention.csv", index=False)

    mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)
    mlflow.set_experiment(cfg.mil.experiment)
    with mlflow.start_run(run_name=model_name):
        mlflow.log_params({"backbone": cfg.backbone.name, "backbone_version": ident["version"],
                           "collection": ident["collection"], "dataset": cfg.data.name, "split_seed": cfg.seed,
                           "n_slides": result["n_slides"], "code_version": context["Versione codice"],
                           **{f"mil.{k}": v for k, v in cfg.mil.items()}})
        flat = {"cv_auroc": "cv/auroc", "cv_ece": "cv/ece", "loco_worst_auroc": "loco_worst_auroc",
                "test_auroc": "test/auroc", "attention_auroc_mean": "attention_auroc_mean"}
        for name, path in flat.items():   # mean over seeds, and its spread
            if path in spread:
                mlflow.log_metrics({name: spread[path]["mean"], f"{name}_sd": spread[path]["sd"],
                                    f"{name}_min": spread[path]["min"]})
        mlflow.set_tag("validation_status", verdict["status"])
        mlflow.set_tag("registered", str(bool(cfg.mil.register)).lower())
        mlflow.log_artifacts(str(rep), artifact_path="validation")
        if result["model"] is not None:
            torch.save(result["model"].state_dict(), rep / "model.pt")
        if result["model"] is not None and cfg.mil.register:
            # A few real tiles as the input example: the saved graph keeps the number of tiles free.
            example = np.load(root / f"{table.slide_id[0]}.npy", mmap_mode="r")[:8].astype(np.float32)
            # The signature is given explicitly: MLflow cannot infer one from a model that returns
            # two tensors (slide logit, attention weights).
            signature = ModelSignature(inputs=Schema([TensorSpec(np.dtype("float32"), (-1, example.shape[1]))]))
            info = mlflow.pytorch.log_model(result["model"], name="model", input_example=example,
                                            signature=signature, registered_model_name=model_name)
            # Registry states are aliases: every trained model is a 'candidate'; 'validated' is
            # set only by a passed battery, and 'production' is never set from here.
            client = mlflow.MlflowClient()
            version = info.registered_model_version
            client.set_registered_model_alias(model_name, "candidate", version)
            if verdict["status"] == "passed":
                client.set_registered_model_alias(model_name, "validated", version)
            for k, v in {"validation_status": verdict["status"], "collection": ident["collection"]}.items():
                client.set_model_version_tag(model_name, version, k, v)
    print(f"{model_name}: {result['n_slides']} slides, battery {verdict['status']}", *verdict["reasons"], sep="\n  ")
    print(f"report -> {rep / 'report.md'}")
