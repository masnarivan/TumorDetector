"""One pass over a slide's tiles: backbone embedding plus simple per-tile image statistics
(colour, stain, sharpness), because the slide file may be deleted afterwards.

Ported from prototype 02 (mil-camelyon16, src/mil/extract.py), made backbone-independent.
"""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import openslide
import pandas as pd
import torch
from skimage import color, filters

from tumordetector.backbones.base import Backbone
from tumordetector.wsi.tiling import read_tile

STAT_NAMES = [
    "r_mean", "g_mean", "b_mean", "r_std", "g_std", "b_std",
    "sat_mean", "val_mean",                          # HSV saturation and brightness
    "hema_mean", "hema_std", "eosin_mean", "eosin_std",  # colour deconvolution (H&E)
    "sharpness",                                     # variance of the Laplacian: low = blurred
]


def tile_stats(rgb: np.ndarray) -> np.ndarray:
    """Hand-crafted descriptors of one uint8 RGB tile, used as a colour baseline for the
    centre probe and for quality control."""
    # Colour statistics on a 2x-subsampled tile: 3x cheaper, same values (r >= 0.995 on
    # tumor_031). Sharpness depends on fine detail, so it uses the full-resolution tile.
    small = rgb[::2, ::2]
    x = small.reshape(-1, 3).astype(np.float32) / 255
    hsv = color.rgb2hsv(small).reshape(-1, 3)
    hed = color.rgb2hed(small).reshape(-1, 3)
    sharp = filters.laplace(color.rgb2gray(rgb)).var()
    return np.array([*x.mean(0), *x.std(0), hsv[:, 1].mean(), hsv[:, 2].mean(),
                     hed[:, 0].mean(), hed[:, 0].std(), hed[:, 1].mean(), hed[:, 1].std(),
                     sharp], dtype=np.float32)


class TileDataset:
    """Serves (model input, index, statistics) for each row of a tile table, reading each
    tile from the slide once."""

    def __init__(self, slide_path: Path, tiles: pd.DataFrame, transform):
        self.slide = openslide.OpenSlide(slide_path)   # one handle, shared by the reader threads
        self.tiles = tiles.reset_index(drop=True)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.tiles)

    def __getitem__(self, idx: int):
        img = read_tile(self.slide, self.tiles.iloc[idx])
        return self.transform(img), idx, torch.from_numpy(tile_stats(np.asarray(img)))


def iter_batches(dataset: TileDataset, batch_size: int, n_threads: int, prefetch: int = 8):
    """Yield collated batches (images, idx, stats), read by a pool of threads.

    Why threads and not DataLoader workers: on macOS each worker is a fresh Python process
    that re-imports torch/transformers/skimage, which cost ~35 s per slide with 4 workers,
    i.e. hours over 399 slides. OpenSlide is thread-safe and its C code (like PIL's resize)
    releases the GIL, so 4 threads already read ~500 tiles/s, 4x faster than the model.
    At most `prefetch` batches are in flight, so memory stays bounded on large slides.
    """
    def load(idxs):
        items = [dataset[i] for i in idxs]
        return (torch.stack([it[0] for it in items]), torch.tensor([it[1] for it in items]),
                torch.stack([it[2] for it in items]))

    starts = range(0, len(dataset), batch_size)
    with ThreadPoolExecutor(n_threads) as pool:
        pending = deque()
        for s in starts:
            pending.append(pool.submit(load, range(s, min(s + batch_size, len(dataset)))))
            if len(pending) >= prefetch:
                yield pending.popleft().result()
        while pending:
            yield pending.popleft().result()


def extract(backbone: Backbone, dataset: TileDataset, batch_size: int = 64,
            n_threads: int = 4) -> tuple[np.ndarray, pd.DataFrame]:
    """-> embeddings (n, dim) float32 and a stats DataFrame (n, len(STAT_NAMES)), in dataset order."""
    n = len(dataset)
    feats = np.zeros((n, backbone.dim), dtype=np.float32)
    stats = np.zeros((n, len(STAT_NAMES)), dtype=np.float32)
    for images, idx, st in iter_batches(dataset, batch_size, n_threads):
        i = idx.numpy()
        feats[i] = backbone.encode(images).numpy()
        stats[i] = st.numpy()
    return feats, pd.DataFrame(stats, columns=STAT_NAMES)
