"""On-disk embedding store: one folder per backbone, three files per slide, aligned row by row.

  <dir>/collection.json     backbone name, version and dim: a folder never mixes versions
  <dir>/<slide>.parquet     level-0 coords, tissue_frac, labels, colour/sharpness stats
  <dir>/<slide>.json        provenance: file hash, backbone, tiling, embedding hash
  <dir>/<slide>.npy         (n_tiles, dim) embeddings; written last = "done" marker
"""
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from tumordetector.io import array_sha256, atomic_write, read_json, write_json

if TYPE_CHECKING:  # annotation only: index and train read the store without the backbone code
    from tumordetector.backbones.base import Backbone


@dataclass
class SlideEmbeddings:
    features: np.ndarray
    tiles: pd.DataFrame
    meta: dict


def collection_name(name: str, version: str) -> str:
    return f"{name}__{version[:12]}"


def open_collection(root: Path, backbone: "Backbone") -> dict:
    """Create the folder's identity file, or refuse to write into another version's folder."""
    root.mkdir(parents=True, exist_ok=True)
    ident = {"backbone": backbone.name, "version": backbone.version, "dim": backbone.dim,
             "collection": collection_name(backbone.name, backbone.version)}
    path = root / "collection.json"
    if path.exists():
        if (found := read_json(path)) != ident:
            raise RuntimeError(f"{root} holds {found['collection']}, not {ident['collection']}: "
                               "embeddings of different backbone versions are never mixed")
    else:
        write_json(path, ident)
    return ident


def is_done(root: Path, slide_id: str) -> bool:
    return (root / f"{slide_id}.npy").exists()


def write_slide(root: Path, slide_id: str, features: np.ndarray, tiles: pd.DataFrame, meta: dict,
                dtype: str = "float16") -> dict:
    assert features.shape[0] == len(tiles) and not np.isnan(features).any()
    features = features.astype(dtype)   # float16 halves the size; cosine to float32 >= 0.9999998
    meta = {**meta, "slide_id": slide_id, "n_tiles": len(tiles), "dtype": dtype,
            "embedding_sha256": array_sha256(features)}
    atomic_write(root / f"{slide_id}.parquet", tiles.to_parquet)
    write_json(root / f"{slide_id}.json", meta)
    atomic_write(root / f"{slide_id}.npy", lambda f: np.save(f, features))
    return meta


def read_slide(root: Path, slide_id: str) -> SlideEmbeddings:
    return SlideEmbeddings(features=np.load(root / f"{slide_id}.npy"),
                           tiles=pd.read_parquet(root / f"{slide_id}.parquet"),
                           meta=read_json(root / f"{slide_id}.json"))


def list_slides(root: Path) -> list[str]:
    return sorted(p.stem for p in root.glob("*.npy"))
