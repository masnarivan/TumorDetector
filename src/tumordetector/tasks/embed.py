"""`td task=embed`: embeddings of each slide in raw_dir (resumable) -> data/embeddings/<backbone>.

For development, like `task=tile`; `EmbedSession` is shared with `task=stream`.
"""
import time
import traceback
from pathlib import Path

import pandas as pd
from omegaconf import DictConfig, OmegaConf

from tumordetector.io import code_version, read_json
from tumordetector.tasks.common import load_manifest, select_slides, tiles_sha256

# Seconds per slide in the log. task=stream adds the download (in a background thread, overlapped
# with the previous slide), the time the loop waited for it, and tiling + QC; task=embed only embeds.
TIMES = ["t_download_s", "t_wait_s", "t_tile_s", "t_embed_s"]


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
        self.write_log()
        return self

    def write_log(self) -> pd.DataFrame:
        """Rewritten after every slide: readable during a long run and kept if the machine stops."""
        log = pd.DataFrame(self.log, columns=["slide_id", "status", "n_tiles", *TIMES, "error"])
        log.to_csv(self.root / "extract_log.csv", index=False)
        return log

    def __exit__(self, *exc):
        log = self.write_log()
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

    def is_referred(self, row) -> bool:
        """QC already referred this file with this tiling and these thresholds: no need to fetch it again."""
        path = self.out / "qc" / f"{row.slide_id}.json"
        if not path.exists():
            return False
        qc = read_json(path)
        return (qc["status"] != "pass" and qc["file_md5"] == row.file_md5 and qc["tiling"] == self.tiling
                and qc.get("qc") == OmegaConf.to_container(self.cfg.qc))

    def record(self, slide_id: str, **rec):
        rec = {"slide_id": slide_id, "status": "", "n_tiles": 0, **dict.fromkeys(TIMES, 0.0), "error": "", **rec}
        self.log.append(rec)
        self.write_log()
        print(f"{slide_id}: {rec['status']} ({rec['n_tiles']} tiles; download {rec['t_download_s']} s, "
              f"wait {rec['t_wait_s']} s, tiling {rec['t_tile_s']} s, embedding {rec['t_embed_s']} s) {rec['error']}",
              flush=True)

    def embed_slide(self, row, tif: Path, **times):
        from tumordetector.embed.extract import TileDataset, extract

        sid, cfg = row.slide_id, self.cfg
        try:
            qc = read_json(self.out / "qc" / f"{sid}.json")
            tiles = pd.read_parquet(self.out / "tiles" / f"{sid}.parquet")
            grid = tiles_sha256(tiles)
            if qc["status"] != "pass":
                return self.record(sid, status=f"referred by QC: {qc['reason']}", **times)
            if self.is_current(row, grid):
                return self.record(sid, status="cached", n_tiles=len(tiles), **times)
            t0 = time.time()
            dataset = TileDataset(tif, tiles, self.backbone.transform)
            feats, stats = extract(self.backbone, dataset, cfg.embed.batch_size, cfg.embed.threads)
            self.store.write_slide(self.root, sid, feats, pd.concat([dataset.tiles, stats], axis=1), {
                **self.ident, "dataset": cfg.data.name, "file_md5": row.file_md5, "tiles_sha256": grid,
                "tiling": self.tiling, "code_version": self.code}, cfg.embed.dtype)
            t = round(time.time() - t0, 1)
            self.mlflow.log_metrics({"n_tiles": len(tiles), "t_embed_s": t, "tiles_per_s": len(tiles) / max(t, 1e-9)},
                                    step=len(self.log))
            self.record(sid, status="embedded", n_tiles=len(tiles), t_embed_s=t, **times)
        except Exception as e:  # log and move on: one bad slide must not stop an overnight run
            traceback.print_exc()
            self.record(sid, status="error", error=repr(e), **times)

    def check(self):
        if n := sum(r["status"] == "error" for r in self.log):
            raise SystemExit(f"{n} slide(s) failed, see {self.root / 'extract_log.csv'}")


def run(cfg: DictConfig):
    raw = Path(cfg.data.raw_dir)
    with EmbedSession(cfg) as session:
        for row in select_slides(cfg, load_manifest(cfg)).itertuples():
            session.embed_slide(row, raw / f"{row.slide_id}.tif")
    session.check()
