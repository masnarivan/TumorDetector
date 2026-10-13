"""Pipeline stages, one per `task`, configured by Hydra (conf/).

  td task=manifest                     data/manifests/<dataset>.csv
  td task=tile                         tissue mask, QC verdict and tile grid per slide
  td task=embed backbone=phikon        embeddings per slide (resumable)
  td task=index backbone=phikon        embeddings -> pgvector
  td task=stream backbone=h_optimus_0  download -> tile -> embed -> delete, slide by slide (Colab)

Any config value can be overridden on the command line, e.g. `data.slides=[tumor_031]`.
"""
import hashlib
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import openslide
import pandas as pd
from hydra import compose, initialize_config_dir
from omegaconf import DictConfig, OmegaConf
from PIL import Image
from skimage.segmentation import find_boundaries

from tumordetector.io import atomic_write, code_version, md5sum, read_json, write_json

CONF_DIR = Path(os.environ.get("TD_CONF", Path(__file__).resolve().parents[2] / "conf"))


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


def tiles_sha256(tiles: pd.DataFrame) -> str:
    """Identity of a tile grid: embeddings are reused only if they were made from the same tiles."""
    cols = tiles[["x", "y", "level", "read_px", "tile_px"]].to_numpy(dtype=np.int64)
    return hashlib.sha256(cols.tobytes()).hexdigest()


def task_manifest(cfg: DictConfig):
    from tumordetector.data import camelyon16
    from tumordetector.data.schema import validate_manifest

    builders = {"camelyon16": camelyon16.build_manifest}
    ok, blocked = validate_manifest(builders[cfg.data.name]())
    out = Path(cfg.data.manifest)
    out.parent.mkdir(parents=True, exist_ok=True)
    ok.to_csv(out, index=False)
    blocked_path = out.with_name(out.stem + "_blocked.csv")
    if len(blocked):
        blocked.to_csv(blocked_path, index=False)
    else:
        blocked_path.unlink(missing_ok=True)
    print(f"{len(ok)} slides -> {out}; {len(blocked)} blocked" + (f" -> {blocked_path}" if len(blocked) else ""))


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
    tissue = compute_tissue_mask(slide, cfg.tiling.mask_downsample, cfg.tiling.mask_margin)
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
        "tiling": OmegaConf.to_container(cfg.tiling)})
    print(f"{sid}: {qc.n_tiles} tiles, {qc.tissue_mm2:.0f} mm2, QC {qc.status} {qc.reason}", flush=True)
    return qc.to_dict()


def task_tile(cfg: DictConfig):
    raw, out = Path(cfg.data.raw_dir), Path(cfg.paths.out)
    summary = []
    for row in select_slides(cfg, load_manifest(cfg)).itertuples():
        tif = raw / f"{row.slide_id}.tif"
        if not tif.exists():
            raise SystemExit(f"{tif} not found")
        if cfg.data.verify_md5 and md5sum(tif) != row.file_md5:
            raise SystemExit(f"{tif}: md5 differs from the manifest")
        summary.append(tile_slide(cfg, row, tif, out))
    pd.DataFrame(summary).to_csv(out / "qc" / "summary.csv", index=False)


class EmbedSession:
    """A loaded backbone, its collection folder and one MLflow run, shared by `embed` and `stream`."""

    def __init__(self, cfg: DictConfig):
        import mlflow

        from tumordetector.backbones.base import get_device
        from tumordetector.backbones.models import build_backbone
        from tumordetector.embed import store

        self.cfg, self.mlflow, self.store = cfg, mlflow, store
        self.backbone = build_backbone(cfg.backbone)
        if (self.backbone.input_px, self.backbone.mpp) != (cfg.tiling.tile_px, cfg.tiling.target_mpp):
            raise SystemExit(f"tiling ({cfg.tiling.tile_px} px @ {cfg.tiling.target_mpp} um/px) does not match "
                             f"{self.backbone.name} ({self.backbone.input_px} px @ {self.backbone.mpp} um/px)")
        self.out = Path(cfg.paths.out)
        self.root = self.out / "embeddings" / self.backbone.name
        self.device = get_device(cfg.embed.device)
        self.backbone.load(self.device)
        self.ident = store.open_collection(self.root, self.backbone)
        self.code = code_version()
        self.tiling = OmegaConf.to_container(cfg.tiling)
        self.log = []

    def __enter__(self):
        b = self.backbone
        self.mlflow.set_tracking_uri(self.cfg.mlflow.tracking_uri)
        self.mlflow.set_experiment(self.cfg.mlflow.experiment)
        self.mlflow.start_run(run_name=f"{self.cfg.task}-{self.ident['collection']}")
        self.mlflow.log_params({
            "backbone": b.name, "backbone_version": b.version, "dim": b.dim, "collection": self.ident["collection"],
            "dataset": self.cfg.data.name, "device": self.device.type, "dtype": self.cfg.embed.dtype,
            "batch_size": self.cfg.embed.batch_size, "code_version": self.code,
            **{f"tiling.{k}": v for k, v in self.tiling.items()}})
        return self

    def __exit__(self, *exc):
        log = pd.DataFrame(self.log, columns=["slide_id", "status", "n_tiles", "t_embed_s", "error"])
        log.to_csv(self.root / "extract_log.csv", index=False)
        self.mlflow.log_artifact(str(self.root / "extract_log.csv"))
        self.mlflow.log_metrics({"slides_embedded": int((log.status == "embedded").sum()),
                                 "slides_cached": int((log.status == "cached").sum()),
                                 "slides_referred": int(log.status.str.startswith("referred").sum()),
                                 "slides_error": int((log.status == "error").sum())})
        self.mlflow.end_run()

    def is_current(self, row, grid: str | None = None) -> bool:
        """Embeddings exist and were made from this file, this tiling and (if given) this grid."""
        if not self.store.is_done(self.root, row.slide_id):
            return False
        m = read_json(self.root / f"{row.slide_id}.json")
        return (m["file_md5"] == row.file_md5 and m["tiling"] == self.tiling
                and (grid is None or m["tiles_sha256"] == grid))

    def record(self, slide_id: str, **rec):
        rec = {"slide_id": slide_id, "status": "", "n_tiles": 0, "t_embed_s": 0.0, "error": "", **rec}
        self.log.append(rec)
        print(f"{slide_id}: {rec['status']} ({rec['n_tiles']} tiles, {rec['t_embed_s']} s) {rec['error']}", flush=True)

    def embed_slide(self, row, tif: Path):
        from tumordetector.embed.extract import TileDataset, extract

        sid, cfg = row.slide_id, self.cfg
        try:
            qc = read_json(self.out / "qc" / f"{sid}.json")
            tiles = pd.read_parquet(self.out / "tiles" / f"{sid}.parquet")
            grid = tiles_sha256(tiles)
            if qc["status"] != "pass":
                return self.record(sid, status=f"referred by QC: {qc['reason']}")
            if self.is_current(row, grid):
                return self.record(sid, status="cached", n_tiles=len(tiles))
            t0 = time.time()
            dataset = TileDataset(tif, tiles, self.backbone.transform)
            feats, stats = extract(self.backbone, dataset, cfg.embed.batch_size, cfg.embed.threads)
            self.store.write_slide(self.root, sid, feats, pd.concat([dataset.tiles, stats], axis=1), {
                **self.ident, "dataset": cfg.data.name, "file_md5": row.file_md5, "tiles_sha256": grid,
                "tiling": self.tiling, "code_version": self.code}, cfg.embed.dtype)
            t = round(time.time() - t0, 1)
            self.mlflow.log_metrics({"n_tiles": len(tiles), "t_embed_s": t, "tiles_per_s": len(tiles) / max(t, 1e-9)},
                                    step=len(self.log))
            self.record(sid, status="embedded", n_tiles=len(tiles), t_embed_s=t)
        except Exception as e:  # log and move on: one bad slide must not stop an overnight run
            traceback.print_exc()
            self.record(sid, status="error", error=repr(e))

    def check(self):
        if n := sum(r["status"] == "error" for r in self.log):
            raise SystemExit(f"{n} slide(s) failed, see {self.root / 'extract_log.csv'}")


def task_embed(cfg: DictConfig):
    raw = Path(cfg.data.raw_dir)
    with EmbedSession(cfg) as session:
        for row in select_slides(cfg, load_manifest(cfg)).itertuples():
            session.embed_slide(row, raw / f"{row.slide_id}.tif")
    session.check()


def download(cfg: DictConfig, row, raw: Path) -> tuple[Path, bool]:
    """Download (or reuse) the slide and its annotation; raise if the md5 does not match.
    -> (path, fresh): fresh is False for a file that was already there, which is never deleted."""
    from tumordetector.data import camelyon16
    from tumordetector.io import curl

    tif = raw / f"{row.slide_id}.tif"
    fresh = not tif.exists()
    if fresh:
        part = tif.with_suffix(".tif.part")
        curl(camelyon16.slide_url(row.slide_id), part)
        if md5sum(part) != row.file_md5:
            part.unlink()  # corrupted: start from scratch next time
            raise OSError(f"md5 mismatch for {row.slide_id}")
        part.rename(tif)
    if row.has_xml and not (xml := tif.with_suffix(".xml")).exists():
        curl(camelyon16.annotation_url(row.slide_id), xml)
    return tif, fresh


def task_stream(cfg: DictConfig):
    """For machines with a GPU but little disk (Colab, Kaggle): the disk never holds more than
    ~2 slides. Resumable: slides whose embeddings are current are skipped without downloading."""
    import threading

    manifest = load_manifest(cfg)
    if cfg.data.slides is not None:
        manifest = manifest.set_index("slide_id").loc[list(cfg.data.slides)].reset_index()
    raw, out = Path(cfg.data.raw_dir), Path(cfg.paths.out)
    raw.mkdir(parents=True, exist_ok=True)
    with EmbedSession(cfg) as session:
        todo = [r for r in manifest.itertuples() if not session.is_current(r)]
        print(f"{len(todo)} slides to process ({len(manifest) - len(todo)} already done)", flush=True)

        def fetch(row, box):
            try:
                box["tif"], box["fresh"] = download(cfg, row, raw)
            except Exception as e:  # reported by the main loop
                box["error"] = e

        def start(row):
            box = {}
            thread = threading.Thread(target=fetch, args=(row, box))
            thread.start()
            return thread, box

        nxt = start(todo[0]) if todo else None
        for i, row in enumerate(todo):
            (thread, box), nxt = nxt, start(todo[i + 1]) if i + 1 < len(todo) else None  # prefetch the next slide
            thread.join()
            if "error" in box:
                session.record(row.slide_id, status="error", error=repr(box["error"]))
                continue
            try:
                tile_slide(cfg, row, box["tif"], out)
            except Exception as e:
                traceback.print_exc()
                session.record(row.slide_id, status="error", error=repr(e))
            else:
                session.embed_slide(row, box["tif"])
            if box["fresh"] and not cfg.data.keep_slides:
                box["tif"].unlink(missing_ok=True)
    session.check()


def task_index(cfg: DictConfig):
    from tumordetector.embed import store
    from tumordetector.vectordb import pg

    out = Path(cfg.paths.out)
    root = out / "embeddings" / cfg.backbone.name
    ident = read_json(root / "collection.json")
    conn = pg.connect(cfg.vectordb.dsn)
    table = pg.ensure_collection(conn, ident)
    done = set(store.list_slides(root))
    counts = {}
    for row in select_slides(cfg, load_manifest(cfg)).itertuples():
        if row.slide_id not in done:
            print(f"{row.slide_id}: no embeddings (referred or failed), not indexed")
            continue
        emb = store.read_slide(root, row.slide_id)
        counts[row.slide_id] = pg.upsert_slide(conn, table, row.slide_id, emb.features, emb.tiles, row.center)
        print(f"{row.slide_id}: {counts[row.slide_id]} vectors -> {table}", flush=True)
    (out / "index").mkdir(parents=True, exist_ok=True)
    write_json(out / "index" / f"{cfg.backbone.name}.json",
               {**ident, "table": table, "slides": counts, "rows_in_table": pg.count(conn, table)})


TASKS = {"manifest": task_manifest, "tile": task_tile, "embed": task_embed, "index": task_index,
         "stream": task_stream}


def main(argv: list[str] | None = None):
    with initialize_config_dir(str(CONF_DIR), version_base=None):
        cfg = compose("config", overrides=sys.argv[1:] if argv is None else argv)
    if cfg.get("task") not in TASKS:
        raise SystemExit(f"task must be one of {sorted(TASKS)}, e.g. `td task=tile`")
    TASKS[cfg.task](cfg)


if __name__ == "__main__":
    main()
