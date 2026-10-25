"""`td task=verify`: the outputs on disk agree with the provenance each slide carries.

Run before `dvc commit`: DVC then records the outputs as produced by the pipeline, so they must be
what the current manifest, tiling and QC settings say they are. For every manifest slide:

  data/qc/<slide>.json             same file md5, tiling and QC thresholds as now
  data/tiles/<slide>.parquet       present
  data/embeddings/<b>/<slide>.*    present if and only if QC passed; same file md5 and tiling;
                                   made from this tile grid; embedding hash matches the .npy
  data/index/<b>.json              lists exactly the embedded slides, with their embedding hash

and no output folder holds files of slides outside the manifest. Exits non-zero on any mismatch.
"""
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from tumordetector.io import array_sha256, read_json
from tumordetector.tasks.common import load_manifest, tiles_sha256, tiling_identity

# Files in the output folders that do not belong to a slide.
NOT_SLIDES = {"embeddings": {"collection.json", "extract_log.csv"}, "qc": set(), "tiles": set()}


def verdict(qc: dict, qc_cfg: dict) -> str:
    """The verdict the current thresholds give on the recorded measurements. Records written before
    the thresholds were stored with them (Oct 2026, 12 slides) are checked this way."""
    ok = qc["n_tiles"] >= qc_cfg["min_tiles"] and qc["tissue_mm2"] >= qc_cfg["min_tissue_mm2"]
    return "pass" if ok else "refer"


def check_slide(row, out: Path, root: Path, tiling: dict, qc_cfg: dict) -> list[str]:
    sid, bad = row.slide_id, []
    qc_path, grid_path = out / "qc" / f"{sid}.json", out / "tiles" / f"{sid}.parquet"
    if not qc_path.exists() or not grid_path.exists():
        return [f"{sid}: no QC verdict or tile grid"]
    qc = read_json(qc_path)
    if qc["file_md5"] != row.file_md5:
        bad.append(f"{sid}: QC made from another file")
    if qc["tiling"] != tiling:
        bad.append(f"{sid}: QC made with another tiling")
    if qc.get("qc", qc_cfg) != qc_cfg or qc["status"] != verdict(qc, qc_cfg):
        bad.append(f"{sid}: QC verdict made with other thresholds")
    if missing := [s for s in (".npz", ".png") if not (out / "qc" / f"{sid}{s}").exists()]:
        bad.append(f"{sid}: QC files missing {missing}")
    embedded = (root / f"{sid}.npy").exists()
    if qc["status"] != "pass":
        return bad + ([f"{sid}: referred by QC but has embeddings"] if embedded else [])
    if not embedded:
        return bad + [f"{sid}: passed QC but has no embeddings"]
    meta = read_json(root / f"{sid}.json")
    if meta["file_md5"] != row.file_md5:
        bad.append(f"{sid}: embeddings made from another file")
    if meta["tiling"] != tiling:
        bad.append(f"{sid}: embeddings made with another tiling")
    if meta["tiles_sha256"] != tiles_sha256(pd.read_parquet(grid_path)):
        bad.append(f"{sid}: embeddings made from another tile grid")
    feats = np.load(root / f"{sid}.npy", mmap_mode="r")
    if array_sha256(feats) != meta["embedding_sha256"] or len(feats) != meta["n_tiles"]:
        bad.append(f"{sid}: .npy does not match its recorded hash")
    if len(pd.read_parquet(root / f"{sid}.parquet")) != meta["n_tiles"]:
        bad.append(f"{sid}: tile table and embeddings differ in length")
    return bad


def run(cfg: DictConfig):
    out = Path(cfg.paths.out)
    root = out / "embeddings" / cfg.backbone.name
    manifest = load_manifest(cfg)
    tiling, qc_cfg = tiling_identity(cfg), OmegaConf.to_container(cfg.qc)
    bad = []
    for row in manifest.itertuples():
        bad += check_slide(row, out, root, tiling, qc_cfg)

    known = set(manifest.slide_id)
    for name, folder in {"embeddings": root, "qc": out / "qc", "tiles": out / "tiles"}.items():
        extra = sorted(p.name for p in folder.iterdir()
                       if p.name not in NOT_SLIDES[name] and p.name.split(".")[0] not in known)
        if extra:
            bad.append(f"{folder}: files of no manifest slide {extra[:5]}{' ...' if len(extra) > 5 else ''}")

    embedded = {s: read_json(root / f"{s}.json")["embedding_sha256"]
                for s in manifest.slide_id if (root / f"{s}.npy").exists()}
    index = out / "index" / f"{cfg.backbone.name}.json"
    if index.exists() and read_json(index)["slides"] != embedded:
        bad.append(f"{index}: does not list the embedded slides with their current hash")

    versions = Counter(read_json(root / f"{s}.json").get("code_version", "unknown") for s in embedded)
    print(f"{len(manifest)} manifest slides, {len(embedded)} embedded; code versions of the embeddings:")
    for v, n in versions.most_common():
        print(f"  {v}: {n} slides")
    if bad:
        print(*bad, sep="\n")
        raise SystemExit(f"{len(bad)} mismatch(es): the outputs do not match their provenance")
    print("outputs agree with their provenance")
