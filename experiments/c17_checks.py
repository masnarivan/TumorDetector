"""CAMELYON17 checks before using its labels and splits (results in docs/esperimenti.md, "Controlli CAMELYON17").

    uv run python experiments/c17_checks.py annotations   # annotated tumour vs the tile grid, all 50 XML
    uv run python experiments/c17_checks.py overlays SLIDE ...   # images: annotation (red) on tiles (green)
    uv run python experiments/c17_checks.py headers       # LPON (Philips) acquisition metadata
    uv run python experiments/c17_checks.py overlap       # near-identical slides between CAMELYON16 and 17

Slides are read remotely over HTTP ranges (only the pyramid tiles needed), nothing is downloaded.
"""
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
import tifffile
import torch
from e3b_scan_metadata import RangeFile, attributes
from PIL import Image, ImageDraw

from tumordetector.backbones.base import get_device
from tumordetector.data import camelyon17
from tumordetector.data.camelyon_annotations import load_tumor_geometry
from tumordetector.io import code_version

C17 = Path("data/camelyon17")
XML = Path("data/raw/camelyon17")
REPORT = Path("data/reports/experiments/c17_checks")
FULL_OUT = Path("data/experiments/c17_checks")     # large outputs, not in git
N_QUERY, SEED, CHUNK = 200, 0, 8192                # as E1


def annotations():
    m = pd.read_csv("data/manifests/camelyon17.csv").set_index("slide_id")
    rows = []
    for p in sorted(XML.glob("*.xml")):
        sid = p.stem
        t = pd.read_parquet(C17 / "tiles" / f"{sid}.parquet")
        mpp = json.loads((C17 / "qc" / f"{sid}.json").read_text())["mpp"]
        g = load_tumor_geometry(p)
        grid = shapely.union_all(shapely.box(t.x, t.y, t.x + t.size_l0, t.y + t.size_l0))
        parts = shapely.area(shapely.get_parts(g))
        mm2 = mpp ** 2 / 1e6
        rows.append({"slide_id": sid, "center": m.loc[sid, "center"], "diagnosis": m.loc[sid, "reference_diagnosis"],
                     "tumor_mm2": g.area * mm2, "largest_part_mm2": parts.max() * mm2, "parts": len(parts),
                     "tile_mm2": float(t.size_l0.iloc[0] ** 2 * mm2),
                     "annotated_in_tile_grid": g.intersection(grid).area / g.area,
                     "tumor_tiles": int((t.label == "tumor").sum()),
                     "boundary_tiles": int((t.label == "boundary").sum())})
    r = pd.DataFrame(rows)
    REPORT.mkdir(parents=True, exist_ok=True)
    r.round(5).to_csv(REPORT / "annotations.csv", index=False)
    pd.set_option("display.width", 200)
    print(r.round(4).to_string(index=False))


def decode_jpeg(data: bytes, tables: bytes | None) -> np.ndarray:
    """A TIFF JPEG tile with PIL: the shared tables (SOI ... EOI) go in front of the tile's own stream."""
    if tables:
        data = tables[:-2] + data[2:]
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))


def crop(tif: tifffile.TiffFile, page: tifffile.TiffPage, x0: int, y0: int, x1: int, y1: int) -> Image.Image:
    """Region of one pyramid page (its own pixel coordinates), decoding only the tiles it covers."""
    tw, th = page.tilewidth, page.tilelength
    # Philips pyramids declare more rows than they store at low levels: trust the stored tiles
    across = -(-page.imagewidth // tw)
    down = len(page.dataoffsets) // across
    out = np.full((y1 - y0, x1 - x0, 3), 255, np.uint8)
    for ty in range(max(y0, 0) // th, min(y1 // th + 1, down)):
        for tx in range(max(x0, 0) // tw, min(x1, page.imagewidth - 1) // tw + 1):
            i = ty * across + tx
            tif.filehandle.seek(page.dataoffsets[i])
            data = tif.filehandle.read(page.databytecounts[i])
            tile = decode_jpeg(data, page.jpegtables)
            ax, ay = tx * tw, ty * th
            sx0, sy0 = max(x0, ax), max(y0, ay)
            sx1, sy1 = min(x1, ax + tw, page.imagewidth), min(y1, ay + th, page.imagelength)
            if sx1 > sx0 and sy1 > sy0:
                out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = tile[sy0 - ay:sy1 - ay, sx0 - ax:sx1 - ax, :3]
    return Image.fromarray(out)


def draw(img: Image.Image, ds: float, ox: float, oy: float, tiles: pd.DataFrame, geom, width: int = 2):
    d = ImageDraw.Draw(img)
    for r in tiles.itertuples():
        colour = {"tumor": (255, 0, 255), "boundary": (255, 165, 0)}.get(r.label, (0, 170, 0))
        d.rectangle([(r.x - ox) / ds, (r.y - oy) / ds, (r.x + r.size_l0 - ox) / ds, (r.y + r.size_l0 - oy) / ds],
                    outline=colour, width=1)
    for poly in shapely.get_parts(geom):
        for ring in [poly.exterior, *poly.interiors]:
            d.line([((x - ox) / ds, (y - oy) / ds) for x, y in ring.coords], fill=(230, 0, 0), width=width)


def overlays(slides: list[str]):
    out = REPORT / "overlays"
    out.mkdir(parents=True, exist_ok=True)
    for sid in slides:
        f = RangeFile(camelyon17.slide_url(sid))
        with tifffile.TiffFile(io.BufferedReader(f, 1 << 18)) as tif:
            levels = [lv.pages[0] for lv in tif.series[0].levels]
            full_w = levels[0].imagewidth
            tiles = pd.read_parquet(C17 / "tiles" / f"{sid}.parquet")
            geom = load_tumor_geometry(XML / f"{sid}.xml")
            # overview: the level closest to 1600 px wide, whole slide
            scale = lambda p, w=full_w: 2 ** round(np.log2(w / p.imagewidth))   # noqa: E731 - levels halve exactly
            ov = min(levels, key=lambda p: abs(p.imagewidth - 1600))
            ds = scale(ov)
            img = crop(tif, ov, 0, 0, ov.imagewidth, ov.imagelength)
            draw(img, ds, 0, 0, tiles, geom, width=3)
            d = ImageDraw.Draw(img)
            for poly in shapely.get_parts(geom):   # rings around annotations too small to see
                cx, cy = poly.centroid.x / ds, poly.centroid.y / ds
                d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=(230, 0, 0), width=2)
            img.save(out / f"{sid}_overview.jpg", quality=85)
            # zoom: ~1 um/px around the three largest annotated parts
            zl = min(levels, key=lambda p: abs(scale(p) - 4))
            zds = scale(zl)
            parts = sorted(shapely.get_parts(geom), key=lambda p: -p.area)[:3]
            panels = []
            for poly in parts:
                cx, cy, half = poly.centroid.x / zds, poly.centroid.y / zds, 400
                x0, y0 = int(cx - half), int(cy - half)
                z = crop(tif, zl, x0, y0, x0 + 2 * half, y0 + 2 * half)
                near = tiles[(tiles.x + tiles.size_l0 > x0 * zds) & (tiles.x < (x0 + 2 * half) * zds)
                             & (tiles.y + tiles.size_l0 > y0 * zds) & (tiles.y < (y0 + 2 * half) * zds)]
                draw(z, zds, x0 * zds, y0 * zds, near, geom)
                panels.append(z)
            strip = Image.new("RGB", (sum(p.width for p in panels) + 10 * (len(panels) - 1), 800), "white")
            for i, p in enumerate(panels):
                strip.paste(p, (i * (p.width + 10), 0))
            strip.save(out / f"{sid}_zoom.jpg", quality=85)
        print(f"{sid}: overview 1/{ds:.0f}, zoom 1/{zds:.0f}, {len(f.cache) * f.block / 1e6:.0f} MB read", flush=True)


def headers():
    m = pd.read_csv("data/manifests/camelyon17.csv")
    keys = ["DICOM_ACQUISITION_DATETIME", "DICOM_DATE_OF_LAST_CALIBRATION", "DICOM_DEVICE_SERIAL_NUMBER",
            "DICOM_MANUFACTURER", "DICOM_SOFTWARE_VERSIONS"]
    rows = []
    for sid in m[m.center == "lpon"].slide_id:
        a = attributes(sid, camelyon17.slide_url(sid))
        rows.append({"slide_id": sid, **{k: a.get(k) for k in keys}})
        print(sid, rows[-1]["DICOM_ACQUISITION_DATETIME"], flush=True)
    r = pd.DataFrame(rows).merge(m[["slide_id", "patient_pseudo_id", "reference_diagnosis"]])
    REPORT.mkdir(parents=True, exist_ok=True)
    r.to_csv(REPORT / "lpon_headers.csv", index=False)


def overlap():
    """E1's measure across datasets: D(i, j) = median over N_QUERY tiles of i of the distance to the nearest
    tile of j, R(i, j) = D(i, j) / D(i, i). Suspect if R <= 1 in either direction."""
    device, rng = get_device("auto"), np.random.default_rng(SEED)
    sets = {"camelyon16": (Path("data/embeddings/phikon"), pd.read_csv("data/manifests/camelyon16.csv")),
            "camelyon17": (C17 / "embeddings/phikon", pd.read_csv("data/manifests/camelyon17.csv"))}
    slides, roots, queries, owner, local = [], [], [], [], []
    for name, (root, man) in sets.items():
        for sid in man.slide_id:
            if not (root / f"{sid}.npy").exists():
                continue
            x = np.load(root / f"{sid}.npy", mmap_mode="r")
            idx = np.sort(rng.choice(len(x), min(N_QUERY, len(x)), replace=False))
            owner.append(np.full(len(idx), len(slides)))
            local.append(idx)
            queries.append(np.asarray(x[idx]))
            slides.append((name, sid))
            roots.append(root)
    owner, local = np.concatenate(owner), np.concatenate(local)
    q = torch.nn.functional.normalize(torch.from_numpy(np.concatenate(queries).astype(np.float32)).to(device), dim=1)
    best = np.empty((len(q), len(slides)), dtype=np.float32)
    t0 = time.time()
    for j, (_, sid) in enumerate(slides):
        db = torch.nn.functional.normalize(torch.from_numpy(np.load(roots[j] / f"{sid}.npy").astype(np.float32))
                                           .to(device), dim=1)
        mine = torch.from_numpy(np.flatnonzero(owner == j)).to(device)
        col = torch.empty(len(q), device=device)
        for a in range(0, len(q), CHUNK):
            sims = q[a:a + CHUNK] @ db.T
            rows = mine[(mine >= a) & (mine < a + CHUNK)]
            if len(rows):   # a tile is not its own neighbour
                sims[rows - a, torch.from_numpy(local[rows.cpu().numpy()]).to(device)] = -2.0
            col[a:a + CHUNK] = sims.max(dim=1).values
        best[:, j] = col.cpu().numpy()
        if j % 100 == 0:
            print(f"{j}/{len(slides)} slides searched, {time.time() - t0:.0f} s", flush=True)
    dist = np.sqrt(np.clip(2 - 2 * best, 0, None))
    d = np.stack([np.median(dist[owner == i], axis=0) for i in range(len(slides))])
    r = d / np.diag(d)[:, None]
    names = [f"{a}/{b}" for a, b in slides]
    FULL_OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(r, index=names, columns=names).to_parquet(FULL_OUT / "ratio.parquet")
    ds = np.array([a for a, _ in slides])
    centre = {**dict(zip(sets["camelyon16"][1].slide_id, sets["camelyon16"][1].center, strict=True)),
              **dict(zip(sets["camelyon17"][1].slide_id, sets["camelyon17"][1].center, strict=True))}
    patient = dict(zip(sets["camelyon17"][1].slide_id, sets["camelyon17"][1].patient_pseudo_id, strict=True))
    iu, ju = np.triu_indices(len(slides), k=1)
    pairs = pd.DataFrame({"a": np.array(names)[iu], "b": np.array(names)[ju],
                          "r_min": np.minimum(r[iu, ju], r[ju, iu])})
    sid = lambda col: pairs[col].str.split("/").str[1]   # noqa: E731
    pairs["center_a"], pairs["center_b"] = sid("a").map(centre), sid("b").map(centre)
    pairs["relation"] = np.select(
        [ds[iu] != ds[ju], (ds[iu] == "camelyon17") & (sid("a").map(patient) == sid("b").map(patient)),
         ds[iu] == "camelyon17"], ["c16-c17", "c17 same patient", "c17 other patient"], "c16-c16")
    pairs = pairs.sort_values("r_min").reset_index(drop=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    pd.concat([pairs[pairs.relation == rel].head(15) for rel in pairs.relation.unique()]).to_csv(
        REPORT / "overlap_lowest_pairs.csv", index=False)
    summary = {"code_version": code_version(), "n_slides": {k: int((ds == k).sum()) for k in sets},
               "n_query_tiles_per_slide": N_QUERY, "seed": SEED,
               "suspect_pairs_r_le_1": {k: int(v) for k, v in pairs[pairs.r_min <= 1].relation.value_counts().items()},
               "r_min_quantiles": {rel: {str(p): float(np.quantile(g.r_min, p)) for p in (0, 0.001, 0.01, 0.5)}
                                   for rel, g in pairs.groupby("relation")},
               "search_seconds": round(time.time() - t0)}
    (REPORT / "overlap_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


def main():
    steps = {"annotations": annotations, "headers": headers, "overlap": overlap}
    if len(sys.argv) >= 2 and sys.argv[1] == "overlays":
        overlays(sys.argv[2:])
    elif len(sys.argv) == 2 and sys.argv[1] in steps:
        steps[sys.argv[1]]()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
