"""Tissue mask relative to each slide's own background, and the slide-level QC verdict (M1).

Why not Otsu: it assumes a two-mode saturation histogram (glass vs tissue). Lymph-node slides
often have three: glass (~0.01), pale tissue such as fat, stroma and capsule (~0.03-0.10),
and dense lymphoid/tumor tissue (~0.2-0.4). Otsu then splits dense tissue from everything
else and drops the pale tissue (normal_027: 3 mm^2 of tissue found; tumor_094: 91 vs 203 mm^2).
Here a pixel is tissue if it is clearly more saturated than this slide's glass.

The glass level is the median saturation of the scanned area: right for CAMELYON, where the scanner
covers the whole slide and glass is most of it. TCGA scanners cover only a box around the tissue, often
more tissue than glass, and the median is then pale tissue (breast stroma dropped, TCGA-A8-A084: 12% of
the thumbnail kept instead of 23%). There `glass_quantile` = 0.1 takes the glass from the palest tenth.

Ported from prototype 02 (mil-camelyon16, src/mil/tissue.py). This is the first QC backend;
an artifact-aware one (e.g. GrandQC) can replace `compute_tissue_mask` behind the same types.
"""
from dataclasses import asdict, dataclass

import numpy as np
import openslide
from scipy import ndimage as ndi
from skimage import color, morphology

from tumordetector.wsi.tiling import TissueMask


def mask_from_thumbnail(thumb: np.ndarray, margin: float = 0.03, min_object_px: int = 200,
                        glass_quantile: float = 0.5) -> np.ndarray:
    hsv = color.rgb2hsv(thumb)
    sat = ndi.median_filter(hsv[..., 1], size=3)          # remove single-pixel noise
    not_black = hsv[..., 2] > 0.2                         # slide edges, marker crosses
    # Glass level of THIS slide: median (or `glass_quantile`) saturation of the scanned area. Pure
    # white (255) is the unscanned part of the slide and would pull the estimate towards 0.
    scanned = (thumb.min(axis=-1) < 250) & not_black
    if not scanned.any():
        background = 0.0
    elif glass_quantile == 0.5:
        background = np.median(sat[scanned])
    else:
        background = np.quantile(sat[scanned], glass_quantile)
    mask = (sat > background + margin) & not_black
    # Opening removes 1-2 px wide lines (glass edges, label borders) before the usual clean-up.
    mask = morphology.opening(mask, morphology.disk(1))
    mask = morphology.closing(mask, morphology.disk(2))
    mask = morphology.remove_small_holes(mask, max_size=min_object_px)
    mask = morphology.remove_small_objects(mask, max_size=min_object_px)
    return mask


def compute_tissue_mask(slide: openslide.OpenSlide, target_downsample: float = 64,
                        margin: float = 0.03, glass_quantile: float = 0.5) -> TissueMask:
    level = slide.get_best_level_for_downsample(target_downsample)
    thumb = np.asarray(slide.read_region((0, 0), level, slide.level_dimensions[level]).convert("RGB"))
    return TissueMask(mask=mask_from_thumbnail(thumb, margin, glass_quantile=glass_quantile),
                      downsample=slide.level_downsamples[level], thumbnail=thumb)


@dataclass
class QCResult:
    slide_id: str
    backend: str
    mpp: float
    tissue_mm2: float
    n_tiles: int
    status: str   # "pass" | "refer"
    reason: str   # empty when status == "pass"

    def to_dict(self) -> dict:
        return asdict(self)


def assess(slide_id: str, tissue: TissueMask, mpp: float, n_tiles: int,
           min_tiles: int, min_tissue_mm2: float) -> QCResult:
    """A slide with too little usable tissue is referred with an explicit reason, never dropped."""
    px_mm = tissue.downsample * mpp / 1000                # side of one mask pixel in mm
    tissue_mm2 = float(tissue.mask.sum() * px_mm ** 2)
    reasons = []
    if n_tiles < min_tiles:
        reasons.append(f"{n_tiles} tiles < {min_tiles}")
    if tissue_mm2 < min_tissue_mm2:
        reasons.append(f"{tissue_mm2:.2f} mm2 of tissue < {min_tissue_mm2}")
    return QCResult(slide_id=slide_id, backend="saturation-v1", mpp=mpp, tissue_mm2=round(tissue_mm2, 3),
                    n_tiles=n_tiles, status="refer" if reasons else "pass", reason="; ".join(reasons))
