"""`td task=stream`: download -> tile -> QC -> embed -> delete, slide by slide, for the whole manifest.

The DVC stage of the full dataset: its outputs are persistent and it redoes only the slides whose
file, tiling, QC thresholds or tile grid changed.
"""
import time
import traceback
from pathlib import Path

from omegaconf import DictConfig

from tumordetector.io import md5sum
from tumordetector.tasks.common import load_manifest
from tumordetector.tasks.embed import EmbedSession
from tumordetector.tasks.tile import tile_slide


def download(cfg: DictConfig, row, raw: Path) -> tuple[Path, bool]:
    """Download (or reuse) the slide and its annotation; raise if the md5 does not match.
    -> (path, fresh): fresh is False for a file that was already there, which is never deleted."""
    from tumordetector.data import camelyon16, camelyon17
    from tumordetector.io import curl

    source = {"camelyon16": camelyon16, "camelyon17": camelyon17}[cfg.data.name]

    tif = raw / f"{row.slide_id}.tif"
    fresh = not tif.exists()
    if fresh:
        part = tif.with_suffix(".tif.part")
        curl(source.slide_url(row.slide_id), part)
        if md5sum(part) != row.file_md5:
            part.unlink()  # corrupted: start from scratch next time
            raise OSError(f"md5 mismatch for {row.slide_id}")
        part.rename(tif)
    if row.has_xml and not (xml := tif.with_suffix(".xml")).exists():
        curl(source.annotation_url(row.slide_id), xml)
    return tif, fresh


def run(cfg: DictConfig):
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
        referred = [r.slide_id for r in todo if session.is_referred(r)]
        todo = [r for r in todo if r.slide_id not in referred]
        print(f"{len(todo)} slides to process ({len(manifest) - len(todo) - len(referred)} already done, "
              f"{len(referred)} already referred by QC)", flush=True)

        def fetch(row, box):
            t0 = time.time()
            try:
                box["tif"], box["fresh"] = download(cfg, row, raw)
            except Exception as e:  # reported by the main loop
                box["error"] = e
            box["t_download_s"] = round(time.time() - t0, 1)

        def start(row):
            box = {}
            thread = threading.Thread(target=fetch, args=(row, box))
            thread.start()
            return thread, box

        nxt = start(todo[0]) if todo else None
        for i, row in enumerate(todo):
            (thread, box), nxt = nxt, start(todo[i + 1]) if i + 1 < len(todo) else None  # prefetch the next slide
            t0 = time.time()
            thread.join()
            times = {"t_wait_s": round(time.time() - t0, 1), "t_download_s": box["t_download_s"]}
            if "error" in box:
                session.record(row.slide_id, status="error", error=repr(box["error"]), **times)
                continue
            t0 = time.time()
            try:
                tile_slide(cfg, row, box["tif"], out)
            except Exception as e:
                traceback.print_exc()
                session.record(row.slide_id, status="error", error=repr(e), **times)
            else:
                times["t_tile_s"] = round(time.time() - t0, 1)
                session.embed_slide(row, box["tif"], **times)
            if box["fresh"] and not cfg.data.keep_slides:
                box["tif"].unlink(missing_ok=True)
    session.check()
