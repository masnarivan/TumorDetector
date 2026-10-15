"""E1 positive control: does the leakage test flag a rescan of the same slide?

A rescan is simulated by re-embedding a local slide with its tile grid shifted by half a tile in x
and y: same tissue, no tile in common. The pair (original, shifted) must come out with R <= 1.

    uv run python experiments/e1_control.py tumor_031 /path/to/tumor_031.tif
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from omegaconf import OmegaConf

from tumordetector.backbones.base import get_device
from tumordetector.backbones.models import build_backbone
from tumordetector.embed.extract import TileDataset, extract

N_QUERY, SEED = 200, 0
ROOT = Path("data/embeddings/phikon")


def d(a: np.ndarray, b: np.ndarray, same: bool, rng) -> float:
    """Median over N_QUERY sampled tiles of a of the distance to the nearest tile of b."""
    ia = np.sort(rng.choice(len(a), min(N_QUERY, len(a)), replace=False))
    qa = torch.nn.functional.normalize(torch.from_numpy(a[ia].astype(np.float32)), dim=1)
    db = torch.nn.functional.normalize(torch.from_numpy(b.astype(np.float32)), dim=1)
    sims = qa @ db.T
    if same:
        sims[torch.arange(len(ia)), torch.from_numpy(ia)] = -2.0
    return float(np.median(np.sqrt(np.clip(2 - 2 * sims.max(dim=1).values.numpy(), 0, None))))


def main(slide_id: str, tif: str):
    tiles = pd.read_parquet(ROOT / f"{slide_id}.parquet")[["x", "y", "level", "read_px", "tile_px", "size_l0"]]
    shifted = tiles.assign(x=(tiles.x + tiles.size_l0 / 2).round().astype(int),
                           y=(tiles.y + tiles.size_l0 / 2).round().astype(int))
    backbone = build_backbone(OmegaConf.load("conf/backbone/phikon.yaml"))
    backbone.load(get_device("auto"))
    feats, _ = extract(backbone, TileDataset(Path(tif), shifted, backbone.transform), 64, 4)
    orig = np.load(ROOT / f"{slide_id}.npy")

    rng = np.random.default_rng(SEED)
    d_oo, d_ss = d(orig, orig, True, rng), d(feats, feats, True, rng)
    d_os, d_so = d(orig, feats, False, rng), d(feats, orig, False, rng)
    ratio = pd.read_parquet("data/experiments/e1/ratio.parquet")
    nearest_real = ratio.loc[slide_id].drop(slide_id)
    out = {"slide_id": slide_id, "n_tiles": len(tiles), "d_self": d_oo, "d_self_shifted": d_ss,
           "r_original_to_shifted": d_os / d_oo, "r_shifted_to_original": d_so / d_ss,
           "nearest_other_slide": nearest_real.idxmin(), "r_nearest_other_slide": float(nearest_real.min())}
    Path("data/reports/experiments/e1/positive_control.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:])
