"""Pipeline stages, one per `task`, configured by Hydra (conf/). Each task is a module in
tumordetector/tasks/, so a DVC stage depends only on the code it runs (tests/test_dvc.py).

  td task=manifest                     data/manifests/<dataset>.csv
  td task=tile                         tissue mask, QC verdict and tile grid per local slide (development)
  td task=embed backbone=phikon        embeddings per local slide, resumable (development)
  td task=stream backbone=phikon       download -> tile -> embed -> delete, slide by slide: the full dataset
  td task=index backbone=phikon        regions + k-center prototypes per slide -> Qdrant
  td task=splits                       data/manifests/<dataset>_splits.csv (cross-validation folds)
  td task=cohort head=ln_metastasis    data/manifests/heads/<head>.csv: the head's slides, roles and folds
  td task=train backbone=phikon        ABMIL baseline, validation report, model registry
  td task=verify backbone=phikon       outputs on disk agree with their per-slide provenance

Any config value can be overridden on the command line, e.g. `data.slides=[tumor_031]`.
"""
import importlib
import os
import sys
from pathlib import Path

from hydra import compose, initialize_config_dir

from tumordetector.config import CONF_DIR

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
TASKS = ("manifest", "tile", "embed", "stream", "index", "splits", "cohort", "train", "verify")


def load_env(path: Path = ENV_FILE):
    """KEY=value lines of the repo's .env (gitignored: credentials) into the environment, without
    overriding variables already set."""
    if path.exists():
        for line in path.read_text().splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and not key.startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def main(argv: list[str] | None = None):
    load_env()
    with initialize_config_dir(str(CONF_DIR), version_base=None):
        cfg = compose("config", overrides=sys.argv[1:] if argv is None else argv)
    if cfg.get("task") not in TASKS:
        raise SystemExit(f"task must be one of {sorted(TASKS)}, e.g. `td task=tile`")
    importlib.import_module(f"tumordetector.tasks.{cfg.task}").run(cfg)


if __name__ == "__main__":
    main()
