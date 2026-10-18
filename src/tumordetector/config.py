"""Where the Hydra configuration lives, and a dataset's own config for tasks that read several datasets."""
import os
from pathlib import Path

from omegaconf import DictConfig, OmegaConf

CONF_DIR = Path(os.environ.get("TD_CONF", Path(__file__).resolve().parents[2] / "conf"))


def dataset_cfg(name: str) -> DictConfig:
    """conf/data/<name>.yaml on its own, outside the composed config."""
    path = CONF_DIR / "data" / f"{name}.yaml"
    if not path.exists():
        raise SystemExit(f"unknown dataset {name!r}: no {path}")
    return OmegaConf.load(path)
