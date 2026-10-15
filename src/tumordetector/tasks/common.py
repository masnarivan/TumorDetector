"""Helpers shared by the tasks: manifest, slide selection, splits path, tile-grid identity."""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from omegaconf import DictConfig


def load_manifest(cfg: DictConfig) -> pd.DataFrame:
    return pd.read_csv(cfg.data.manifest)


def select_slides(cfg: DictConfig, manifest: pd.DataFrame) -> pd.DataFrame:
    """Manifest rows to process: the configured ids, or every slide present in raw_dir."""
    raw = Path(cfg.data.raw_dir)
    if cfg.data.slides is None:
        return manifest[manifest.slide_id.map(lambda s: (raw / f"{s}.tif").exists())]
    wanted = list(cfg.data.slides)
    if unknown := sorted(set(wanted) - set(manifest.slide_id)):
        raise SystemExit(f"not in {cfg.data.manifest}: {unknown}")
    return manifest.set_index("slide_id").loc[wanted].reset_index()


def splits_path(cfg: DictConfig) -> Path:
    manifest = Path(cfg.data.manifest)
    return manifest.with_name(manifest.stem + "_splits.csv")


def tiles_sha256(tiles: pd.DataFrame) -> str:
    """Identity of a tile grid: embeddings are reused only if they were made from the same tiles."""
    cols = tiles[["x", "y", "level", "read_px", "tile_px"]].to_numpy(dtype=np.int64)
    return hashlib.sha256(cols.tobytes()).hexdigest()
