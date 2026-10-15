"""Pipeline stages, one per `task`, configured by Hydra (conf/). Each task is a module in
tumordetector/tasks/, so a DVC stage depends only on the code it runs (tests/test_dvc.py).

  td task=manifest                     data/manifests/<dataset>.csv
  td task=tile                         tissue mask, QC verdict and tile grid per local slide (development)
  td task=embed backbone=phikon        embeddings per local slide, resumable (development)
  td task=stream backbone=phikon       download -> tile -> embed -> delete, slide by slide: the full dataset
  td task=index backbone=phikon        embeddings -> pgvector
  td task=splits                       data/manifests/<dataset>_splits.csv (cross-validation folds)
  td task=train backbone=phikon        ABMIL baseline, validation report, model registry
  td task=verify backbone=phikon       outputs on disk agree with their per-slide provenance

Any config value can be overridden on the command line, e.g. `data.slides=[tumor_031]`.
"""
import importlib
import os
import sys
from pathlib import Path

from hydra import compose, initialize_config_dir

CONF_DIR = Path(os.environ.get("TD_CONF", Path(__file__).resolve().parents[2] / "conf"))
TASKS = ("manifest", "tile", "embed", "stream", "index", "splits", "train", "verify")


def main(argv: list[str] | None = None):
    with initialize_config_dir(str(CONF_DIR), version_base=None):
        cfg = compose("config", overrides=sys.argv[1:] if argv is None else argv)
    if cfg.get("task") not in TASKS:
        raise SystemExit(f"task must be one of {sorted(TASKS)}, e.g. `td task=tile`")
    importlib.import_module(f"tumordetector.tasks.{cfg.task}").run(cfg)


if __name__ == "__main__":
    main()
