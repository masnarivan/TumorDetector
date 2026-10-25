"""`td task=stream`: download -> tile -> QC -> embed -> delete, slide by slide, for the whole manifest.

The DVC stage of the full dataset: its outputs are persistent and it redoes only the slides whose
file, tiling, QC thresholds or tile grid changed.

Slides already in raw_dir are used as they are (never downloaded again, never deleted unless
`stream.delete_raw`): so `td task=fetch` can fill raw_dir first, e.g. on Google Drive from a CPU runtime,
and this task only embeds. `stream.stage_dir` copies each slide to a local disk before tiling it:
OpenSlide reads a slide in many small random reads, slow on a network filesystem like Drive.
"""
import shutil
import time
import traceback
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from omegaconf import DictConfig

from tumordetector.io import md5sum
from tumordetector.tasks.common import load_manifest, slide_file
from tumordetector.tasks.embed import EmbedSession
from tumordetector.tasks.tile import tile_slide


def download(cfg: DictConfig, row, raw: Path) -> tuple[Path, bool]:
    """Download (or reuse) the slide and its annotation; raise if the md5 does not match.
    -> (path, fresh): fresh is False for a file that was already there."""
    from tumordetector.data import camelyon16, camelyon17, tcga
    from tumordetector.io import curl

    source = {"camelyon16": camelyon16, "camelyon17": camelyon17, "tcga": tcga}[cfg.data.name]

    path = slide_file(cfg, row.slide_id, raw)
    fresh = not path.exists()
    if fresh:
        part = path.with_name(path.name + ".part")
        curl(source.slide_url(row), part)
        if md5sum(part) != row.file_md5:
            part.unlink()  # corrupted: start from scratch next time
            raise OSError(f"md5 mismatch for {row.slide_id}")
        part.rename(path)
    if row.has_xml and not (xml := path.with_suffix(".xml")).exists():
        curl(source.annotation_url(row), xml)
    return path, fresh


def stage(path: Path, stage_dir: Path) -> Path:
    """Copy a slide (and its annotation) to the local stage folder -> the local copy."""
    stage_dir.mkdir(parents=True, exist_ok=True)
    local = stage_dir / path.name
    part = local.with_name(local.name + ".part")
    shutil.copyfile(path, part)
    part.rename(local)
    if (xml := path.with_suffix(".xml")).exists():
        shutil.copyfile(xml, local.with_suffix(".xml"))
    return local


def run(cfg: DictConfig):
    """For machines with a GPU but little disk (Colab, Kaggle): the disk never holds more than
    stream.prefetch + 1 slides. Resumable: slides whose embeddings are current are skipped without
    downloading."""
    manifest = load_manifest(cfg)
    if cfg.data.slides is not None:
        manifest = manifest.set_index("slide_id").loc[list(cfg.data.slides)].reset_index()
    raw, out = Path(cfg.data.raw_dir), Path(cfg.paths.out)
    stage_dir = Path(cfg.stream.stage_dir) if cfg.stream.stage_dir else None
    raw.mkdir(parents=True, exist_ok=True)
    with EmbedSession(cfg) as session:
        todo = [r for r in manifest.itertuples() if not session.is_current(r)]
        referred = [r.slide_id for r in todo if session.is_referred(r)]
        todo = [r for r in todo if r.slide_id not in referred]
        print(f"{len(todo)} slides to process ({len(manifest) - len(todo) - len(referred)} already done, "
              f"{len(referred)} already referred by QC)", flush=True)

        def fetch(row):
            box, t0 = {}, time.time()
            try:
                box["path"], box["fresh"] = download(cfg, row, raw)
                if stage_dir:
                    box["local"] = stage(box["path"], stage_dir)
            except Exception as e:  # reported by the main loop
                box["error"] = e
            box["t_download_s"] = round(time.time() - t0, 1)
            return box

        # Download `ahead` slides while the current one is tiled and embedded: on Colab one S3 stream
        # gives ~30 MB/s, slower than an A100 embeds (61 s to download vs 51 s to process test_003).
        ahead = max(1, int(cfg.stream.prefetch))
        with ThreadPoolExecutor(ahead) as pool:
            pending = deque(pool.submit(fetch, r) for r in todo[:ahead])
            for i, row in enumerate(todo):
                if i + ahead < len(todo):
                    pending.append(pool.submit(fetch, todo[i + ahead]))
                t0 = time.time()
                box = pending.popleft().result()
                times = {"t_wait_s": round(time.time() - t0, 1), "t_download_s": box["t_download_s"]}
                if "error" in box:
                    session.record(row.slide_id, status="error", error=repr(box["error"]), **times)
                    continue
                path = box.get("local", box["path"])
                t0 = time.time()
                try:
                    tile_slide(cfg, row, path, out)
                except Exception as e:
                    traceback.print_exc()
                    session.record(row.slide_id, status="error", error=repr(e), **times)
                else:
                    times["t_tile_s"] = round(time.time() - t0, 1)
                    session.embed_slide(row, path, **times)
                if "local" in box:
                    box["local"].unlink()
                    box["local"].with_suffix(".xml").unlink(missing_ok=True)
                done = session.log[-1]["status"] != "error"
                # The annotation stays: it is small and its slide may be downloaded again.
                if not cfg.data.keep_slides and (box["fresh"] or (cfg.stream.delete_raw and done)):
                    box["path"].unlink(missing_ok=True)
    session.check()
