"""`td task=index`: embeddings on disk -> the collection's pgvector table, incrementally."""
import time
from pathlib import Path

from omegaconf import DictConfig

from tumordetector.io import read_json, write_json
from tumordetector.tasks.common import load_manifest, select_slides


def run(cfg: DictConfig):
    """Load the embeddings on disk into the collection's table. With `data.slides` null: every
    manifest slide with embeddings, wherever its .tif is (task=stream deletes them)."""
    from tumordetector.embed import store
    from tumordetector.vectordb import pg

    out, db = Path(cfg.paths.out), cfg.vectordb
    root = out / "embeddings" / cfg.backbone.name
    ident = read_json(root / "collection.json")
    done, manifest = set(store.list_slides(root)), load_manifest(cfg)
    if cfg.data.slides is None:
        rows = manifest[manifest.slide_id.isin(done)]
        print(f"{len(rows)} slides with embeddings, {len(manifest) - len(rows)} manifest slides without "
              "(referred by QC, failed or not extracted yet)")
    else:
        rows = select_slides(cfg, manifest)
        for sid in sorted(set(rows.slide_id) - done):
            print(f"{sid}: no embeddings (referred or failed), not indexed")
        rows = rows[rows.slide_id.isin(done)]
    conn = pg.connect(db.dsn)
    table = pg.ensure_collection(conn, ident, rebuild=db.rebuild)
    loaded = pg.indexed(conn, table)
    todo = [r for r in rows.itertuples()
            if loaded.get(r.slide_id) != read_json(root / f"{r.slide_id}.json")["embedding_sha256"]]
    print(f"{len(todo)} slides to load, {len(rows) - len(todo)} already in {table}", flush=True)
    if len(todo) > len(loaded):   # bulk load: building the index once at the end is far faster
        pg.drop_index(conn, table)
    for row in todo:
        emb = store.read_slide(root, row.slide_id)
        n = pg.upsert_slide(conn, table, row.slide_id, emb.features, emb.tiles, row.center,
                            emb.meta["embedding_sha256"])
        print(f"{row.slide_id}: {n} vectors -> {table}", flush=True)
    t0 = time.time()
    if pg.build_index(conn, table, db.maintenance_work_mem, db.index_workers):
        print(f"HNSW index built in {time.time() - t0:.0f} s", flush=True)
    (out / "index").mkdir(parents=True, exist_ok=True)
    write_json(out / "index" / f"{cfg.backbone.name}.json",
               {**ident, "table": table, "slides": pg.indexed(conn, table), "rows_in_table": pg.count(conn, table)})
