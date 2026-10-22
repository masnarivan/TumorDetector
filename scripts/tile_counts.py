"""Tiles per slide of the local tile grids -> notebooks/tile_counts.csv.

The grid depends only on the tiling (224 px at 0.5 um/px), not on the backbone, so the counts of the
Phikon extraction are those of H-optimus-0: notebooks/hoptimus_timing.ipynb uses them to project
the time of the whole extraction from a few measured slides.

    uv run python scripts/tile_counts.py
"""
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

DATASETS = {"camelyon16": Path("data"), "camelyon17": Path("data/camelyon17")}   # paths.out of each dataset


def main():
    rows = []
    for name, out in DATASETS.items():
        manifest = pd.read_csv(f"data/manifests/{name}.csv")
        for r in manifest.itertuples():
            tiles = out / "tiles" / f"{r.slide_id}.parquet"
            if not tiles.exists():
                raise SystemExit(f"{tiles} missing: run the tiling of {name} first")
            rows.append({"slide_id": r.slide_id, "dataset": name, "center": r.center, "scanner": r.scanner,
                         "size_gb": r.size_gb, "n_tiles": pq.ParquetFile(tiles).metadata.num_rows})
    df = pd.DataFrame(rows)
    df.to_csv("notebooks/tile_counts.csv", index=False)
    print(df.groupby("dataset").agg(slides=("slide_id", "size"), tiles=("n_tiles", "sum"), gb=("size_gb", "sum")))


if __name__ == "__main__":
    main()
