"""`td task=tile`: tissue mask, QC verdict and tile grid of each slide in raw_dir -> data/tiles, data/qc.

For development on the few slides on this machine: it needs the slide files, so it is not a DVC stage
(the full dataset goes through `task=stream`, which calls `tile_slide` on each downloaded slide).
"""
from pathlib import Path

import numpy as np
import openslide
import pandas as pd
from omegaconf import DictConfig, OmegaConf
from PIL import Image
from skimage.segmentation import find_boundaries

from tumordetector.io import atomic_write, md5sum, write_json
from tumordetector.tasks.common import load_manifest, select_slides, slide_file, tiling_identity


def qc_overlay(thumbnail: np.ndarray, mask: np.ndarray) -> Image.Image:
    img = thumbnail.copy()
    img[find_boundaries(mask, mode="outer")] = (0, 255, 0)
    return Image.fromarray(img)


def tile_slide(cfg: DictConfig, row, tif: Path, out: Path) -> dict:
    """Tissue mask, tile grid, tile labels and QC verdict of one slide -> out/tiles, out/qc."""
    from tumordetector.data.camelyon_annotations import label_tiles, load_tumor_geometry, tumor_fraction
    from tumordetector.qc.tissue import assess, compute_tissue_mask
    from tumordetector.wsi.tiling import make_tile_grid, slide_mpp

    sid, tiles_dir, qc_dir = row.slide_id, out / "tiles", out / "qc"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    qc_dir.mkdir(parents=True, exist_ok=True)
    slide = openslide.OpenSlide(tif)
    mpp = slide_mpp(slide)
    tissue = compute_tissue_mask(slide, cfg.tiling.mask_downsample, cfg.tiling.mask_margin, cfg.data.glass_quantile)
    tiles = make_tile_grid(slide, tissue, cfg.tiling.target_mpp, cfg.tiling.tile_px, cfg.tiling.min_tissue)

    xml = tif.with_suffix(".xml")
    if xml.exists():
        tiles["tumor_frac"] = tumor_fraction(tiles, load_tumor_geometry(xml))
    elif row.label == 0:
        tiles["tumor_frac"] = 0.0              # negative slide: no tumor anywhere
    else:
        tiles["tumor_frac"] = np.nan           # positive slide without its annotation file
    tiles["label"] = np.where(tiles.tumor_frac.isna(), "unknown", label_tiles(tiles.tumor_frac.to_numpy()))

    qc = assess(sid, tissue, mpp, len(tiles), cfg.qc.min_tiles, cfg.qc.min_tissue_mm2)
    atomic_write(tiles_dir / f"{sid}.parquet", tiles.to_parquet)
    atomic_write(qc_dir / f"{sid}.npz", lambda f: np.savez_compressed(
        f, thumbnail=tissue.thumbnail, mask=tissue.mask, downsample=tissue.downsample))
    qc_overlay(tissue.thumbnail, tissue.mask).save(qc_dir / f"{sid}.png")
    write_json(qc_dir / f"{sid}.json", {
        **qc.to_dict(), "file_md5": row.file_md5, "level0_px": list(slide.dimensions),
        "vendor": slide.properties.get(openslide.PROPERTY_NAME_VENDOR),
        "objective_power": slide.properties.get(openslide.PROPERTY_NAME_OBJECTIVE_POWER),
        "tiling": tiling_identity(cfg), "qc": OmegaConf.to_container(cfg.qc)})
    print(f"{sid}: {qc.n_tiles} tiles, {qc.tissue_mm2:.0f} mm2, QC {qc.status} {qc.reason}", flush=True)
    return qc.to_dict()


def run(cfg: DictConfig):
    out = Path(cfg.paths.out)
    summary = []
    for row in select_slides(cfg, load_manifest(cfg)).itertuples():
        tif = slide_file(cfg, row.slide_id)
        if not tif.exists():
            raise SystemExit(f"{tif} not found")
        if cfg.data.verify_md5 and md5sum(tif) != row.file_md5:
            raise SystemExit(f"{tif}: md5 differs from the manifest")
        summary.append(tile_slide(cfg, row, tif, out))
    pd.DataFrame(summary).to_csv(out / "qc" / "summary.csv", index=False)
