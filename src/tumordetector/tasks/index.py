"""`td task=index`: embeddings on disk -> regions + k-center prototypes per slide -> Qdrant, incrementally.

The tiles themselves stay on disk (data/embeddings): the database holds the reduced set only
(vectordb/reduce.py), small enough for the free Qdrant cluster.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from omegaconf import DictConfig

from tumordetector.io import read_json, write_json
from tumordetector.tasks.common import load_manifest, select_slides


def reduce_slide(emb, row, cfg: DictConfig) -> tuple[np.ndarray, pd.DataFrame, float]:
    """One slide -> (vectors, one payload row per vector, prototype coverage radius)."""
    from tumordetector.vectordb import reduce

    tiles = emb.tiles
    reg_vec, reg = reduce.regions(emb.features, tiles, cfg.index.region_tiles, cfg.index.min_region_tiles)
    reg = reg.assign(level="region", idx=np.arange(len(reg)))
    proto = reduce.kcenter(emb.features, cfg.index.prototypes)
    pt = tiles.iloc[proto.tiles]
    pro = pd.DataFrame({
        "level": "prototype", "idx": np.arange(len(pt)), "tile_idx": proto.tiles,
        "x": pt.x.to_numpy(), "y": pt.y.to_numpy(), "size_l0": pt.size_l0.to_numpy(),
        "represented": proto.represented,
        "label": pt["label"].to_numpy() if "label" in pt else None,
        "tumor_frac": pt["tumor_frac"].to_numpy() if "tumor_frac" in pt else None,
    })
    slide = {"slide_id": row.slide_id, "dataset": row.dataset, "center": row.center,
             "slide_label": None if pd.isna(row.label) else int(row.label),
             "diagnosis": row.reference_diagnosis, "embedding_sha256": emb.meta["embedding_sha256"]}
    payload = pd.concat([reg, pro], ignore_index=True).assign(**slide)
    return np.concatenate([reg_vec, emb.features[proto.tiles].astype(np.float32)]), payload, proto.radius


def run(cfg: DictConfig):
    """With `data.slides` null: every manifest slide with embeddings, wherever its .tif is (task=stream
    deletes them). A slide is uploaded again when its embeddings changed or the server does not hold
    the points recorded for it (an interrupted upload)."""
    from tumordetector.embed import store
    from tumordetector.vectordb import qdrant

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
    client = qdrant.connect(db.url)
    name = qdrant.ensure_collection(client, ident, rebuild=db.rebuild)
    path = out / "index" / f"{cfg.backbone.name}.json"
    reduction = dict(cfg.index)
    state = read_json(path) if path.exists() and not db.rebuild else {}
    slides = state.get("slides", {}) if state.get("reduction") == reduction else {}
    head = {**ident, "url": db.url, "collections": qdrant.names(name), "reduction": reduction}
    on_server = qdrant.counts(client, name)
    todo = [r for r in rows.itertuples()
            if (s := slides.get(r.slide_id)) is None
            or s["embedding_sha256"] != read_json(root / f"{r.slide_id}.json")["embedding_sha256"]
            or on_server.get(r.slide_id) != s["points"]]
    print(f"{len(todo)} slides to upload, {len(rows) - len(todo)} already in {name}", flush=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    for row in todo:
        emb = store.read_slide(root, row.slide_id)
        vectors, payload, radius = reduce_slide(emb, row, cfg)
        n = qdrant.upsert_slide(client, name, row.slide_id, vectors, payload, db.batch)
        slides[row.slide_id] = {"embedding_sha256": emb.meta["embedding_sha256"], "points": n,
                                "regions": int((payload.level == "region").sum()),
                                "prototypes": int((payload.level == "prototype").sum()),
                                "n_tiles": len(emb.tiles), "radius": round(radius, 4)}
        print(f"{row.slide_id}: {len(emb.tiles)} tiles -> {n} points (radius {radius:.3f})", flush=True)
        write_json(path, {**head, "slides": slides})   # resumable
    write_json(path, {**head, "slides": slides, "points_in_collection": qdrant.count(client, name)})
