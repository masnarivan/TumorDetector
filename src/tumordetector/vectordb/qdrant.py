"""Reduced slide embeddings (regions + k-center prototypes, see reduce.py) in Qdrant.

Two collections per backbone version, `<collection>__region` and `<collection>__prototype`: vectors
of different versions are never searched together, and a search never filters by level. A filter
keeping half the points (the level, in one collection) cut Qdrant's HNSW recall@10 to 0.55-0.61
against exact search, from 0.99-1.0 unfiltered or excluding one slide (399 CAMELYON16 slides).
Every point carries its slide, dataset and centre as payload, indexed for filtering. Vectors are
float16, as on disk, and stay on disk on the server: the free cluster has ~1 GB of RAM.
The API key is read from the environment (TD_QDRANT_API_KEY, the repo's .env), never from the
config, so it is never printed or written with it.
"""
import os
import ssl
import uuid

import numpy as np
import pandas as pd
import truststore
from qdrant_client import QdrantClient, models

LEVELS = ("region", "prototype")
KEYWORDS = ["slide_id", "center", "dataset"]
NAMESPACE = uuid.UUID("5f0c6b1e-3d2a-4b8e-9c71-2a6e0d9f4b13")


def connect(url: str) -> QdrantClient:
    """TLS is verified against the operating system's trust store, not certifi's: on a network that
    inspects TLS (here Cato Networks) the server certificate is signed by a CA installed in the system."""
    return QdrantClient(url=url, api_key=os.environ.get("TD_QDRANT_API_KEY"), timeout=120, check_compatibility=False,
                        verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT))


def names(collection: str) -> dict[str, str]:
    return {level: f"{collection}__{level}" for level in LEVELS}


def ensure_collection(client: QdrantClient, ident: dict, rebuild: bool = False) -> str:
    """Create the collection's two level collections if missing -> the collection name."""
    for name in names(ident["collection"]).values():
        if rebuild and client.collection_exists(name):
            client.delete_collection(name)
        if client.collection_exists(name):
            vec = client.get_collection(name).config.params.vectors
            if vec.size != ident["dim"] or vec.distance != models.Distance.COSINE:
                raise RuntimeError(f"{name} holds {vec.size}-d {vec.distance} vectors, this code writes "
                                   f"{ident['dim']}-d cosine: rebuild it with `td task=index vectordb.rebuild=true`")
            continue
        client.create_collection(name, vectors_config=models.VectorParams(
            size=ident["dim"], distance=models.Distance.COSINE, datatype=models.Datatype.FLOAT16, on_disk=True))
        for key in KEYWORDS:
            client.create_payload_index(name, key, models.PayloadSchemaType.KEYWORD)
    return ident["collection"]


def point_id(slide_id: str, level: str, i: int) -> str:
    """Stable: uploading a slide again overwrites its points instead of adding copies."""
    return str(uuid.uuid5(NAMESPACE, f"{slide_id}/{level}/{i}"))


def _slide(slide_id: str) -> models.Filter:
    return models.Filter(must=[models.FieldCondition(key="slide_id", match=models.MatchValue(value=slide_id))])


def upsert_slide(client: QdrantClient, collection: str, slide_id: str, vectors: np.ndarray, payloads: pd.DataFrame,
                 batch: int = 256) -> int:
    """Replace every point of one slide. `payloads` has one row per vector, with `level` and `idx`."""
    rows = [{k: (None if pd.isna(v) else v.item() if isinstance(v, np.generic) else v) for k, v in r.items()}
            for r in payloads.to_dict("records")]
    for level, name in names(collection).items():
        client.delete(name, points_selector=models.FilterSelector(filter=_slide(slide_id)), wait=True)
        keep = [i for i, r in enumerate(rows) if r["level"] == level]
        for a in range(0, len(keep), batch):
            part = keep[a:a + batch]
            client.upsert(name, wait=True, points=models.Batch(
                ids=[point_id(slide_id, level, rows[i]["idx"]) for i in part],
                vectors=vectors[part].astype(np.float32).tolist(), payloads=[rows[i] for i in part]))
    return len(rows)


def counts(client: QdrantClient, collection: str) -> dict[str, int]:
    """slide_id -> points on the server, both levels (exact)."""
    total: dict[str, int] = {}
    for name in names(collection).values():
        for h in client.facet(name, key="slide_id", limit=100_000, exact=True).hits:
            total[h.value] = total.get(h.value, 0) + h.count
    return total


def search(client: QdrantClient, collection: str, query: np.ndarray, level: str, k: int = 10,
           exclude_slide: str | None = None, exact: bool = False, hnsw_ef: int = 128) -> pd.DataFrame:
    """k nearest points of one level by cosine distance (1 - similarity), with their payload. Qdrant
    filters while traversing the graph, so excluding the query's slide does not empty the result as
    pgvector's post-filter did (E3)."""
    must_not = [models.FieldCondition(key="slide_id", match=models.MatchValue(value=exclude_slide))] \
        if exclude_slide else []
    res = client.query_points(names(collection)[level], query=np.asarray(query, dtype=np.float32).tolist(),
                              limit=k, query_filter=models.Filter(must_not=must_not), with_payload=True,
                              search_params=models.SearchParams(hnsw_ef=hnsw_ef, exact=exact)).points
    return pd.DataFrame([{**p.payload, "distance": 1 - p.score} for p in res])


def count(client: QdrantClient, collection: str) -> int:
    return sum(client.count(name, exact=True).count for name in names(collection).values())
