"""`td task=fetch`: download the manifest's slides into raw_dir, md5-checked, several at a time; nothing else.

For machines where the download is the slow part: on Colab, fetch on a CPU runtime into Google Drive
(the GPU is not paid while it waits for the network), then run `td task=stream` on a GPU runtime with the
same raw_dir: it uses the files already there (docs/mvp.md). Not a DVC stage: its output is raw_dir.

Resumable: a slide is skipped if its file is in raw_dir (a file is renamed into place only after its md5
matched), or if it was already embedded with the configured backbone, or referred by QC, from the same
file. A failed slide does not stop the others; the task fails at the end if any did.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from omegaconf import DictConfig

from tumordetector.io import read_json
from tumordetector.tasks.common import load_manifest, slide_file
from tumordetector.tasks.stream import download


def processed(row, out: Path, backbone: str) -> bool:
    """Embedded with this backbone, or referred by QC, from this very file: no need to fetch it again."""
    meta = out / "embeddings" / backbone / f"{row.slide_id}.json"
    if meta.exists() and read_json(meta).get("file_md5") == row.file_md5:
        return True
    qc = out / "qc" / f"{row.slide_id}.json"
    if qc.exists():
        q = read_json(qc)
        return q["status"] != "pass" and q["file_md5"] == row.file_md5
    return False


def run(cfg: DictConfig):
    manifest = load_manifest(cfg)
    if cfg.data.slides is not None:
        manifest = manifest.set_index("slide_id").loc[list(cfg.data.slides)].reset_index()
    if cfg.fetch.batch is not None:
        manifest = manifest[manifest.batch == cfg.fetch.batch]
    raw, out = Path(cfg.data.raw_dir), Path(cfg.paths.out)
    raw.mkdir(parents=True, exist_ok=True)
    rows = list(manifest.itertuples())
    done = {r.slide_id for r in rows if processed(r, out, cfg.backbone.name)}
    here = {r.slide_id for r in rows if r.slide_id not in done and slide_file(cfg, r.slide_id, raw).exists()}
    todo = [r for r in rows if r.slide_id not in done | here]
    gb = sum(getattr(r, "size_gb", 0) or 0 for r in todo)
    print(f"{len(todo)} slides to fetch ({gb:.0f} GB) into {raw} with {cfg.fetch.workers} workers; "
          f"{len(here)} already there, {len(done)} already processed with {cfg.backbone.name}", flush=True)

    def one(row):
        t0 = time.time()
        path, _ = download(cfg, row, raw)
        return path.stat().st_size, time.time() - t0

    failed, total, t0 = [], 0, time.time()
    with ThreadPoolExecutor(max(1, int(cfg.fetch.workers))) as pool:
        futures = {pool.submit(one, r): r for r in todo}
        for i, f in enumerate(as_completed(futures), 1):
            row = futures[f]
            try:
                size, t = f.result()
            except Exception as e:
                failed.append(row.slide_id)
                print(f"[{i}/{len(todo)}] {row.slide_id}: error {e!r}", flush=True)
                continue
            total += size
            elapsed = time.time() - t0
            print(f"[{i}/{len(todo)}] {row.slide_id}: {size / 1e9:.2f} GB in {t:.0f} s "
                  f"({size / 1e6 / max(t, 1e-9):.0f} MB/s); total {total / 1e9:.1f} GB at "
                  f"{total / 1e6 / max(elapsed, 1e-9):.0f} MB/s", flush=True)
    if failed:
        raise SystemExit(f"{len(failed)} slide(s) not fetched (run again to retry): {failed}")
