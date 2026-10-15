"""Tile embeddings in PostgreSQL + pgvector: similar-case retrieval and, later, OOD scores.

One table per collection (backbone + version), so vectors from different backbone versions
can never end up in the same nearest-neighbour search. Vectors are stored as halfvec (float16,
as on disk): half the space of float32, no measurable loss for cosine search.
"""
import re

import numpy as np
import pandas as pd
import psycopg
from pgvector import HalfVector
from pgvector.psycopg import register_vector
from psycopg import sql

META_COLS = ["slide_id", "tile_idx", "x", "y", "size_l0", "center", "label", "tumor_frac"]


def table_name(collection: str) -> str:
    return "emb_" + re.sub(r"[^a-z0-9_]", "_", collection.lower())


def connect(dsn: str) -> psycopg.Connection:
    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def ensure_collection(conn: psycopg.Connection, ident: dict, rebuild: bool = False) -> str:
    """Create the registry row and table of a collection if they are missing. The HNSW index is
    built separately (`build_index`), after loading. `rebuild` drops the table first."""
    table = table_name(ident["collection"])
    conn.execute("""CREATE TABLE IF NOT EXISTS collections (
        name text PRIMARY KEY, backbone text NOT NULL, version text NOT NULL, dim int NOT NULL,
        table_name text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())""")
    conn.execute("INSERT INTO collections (name, backbone, version, dim, table_name) VALUES (%s, %s, %s, %s, %s) "
                 "ON CONFLICT (name) DO NOTHING",
                 (ident["collection"], ident["backbone"], ident["version"], ident["dim"], table))
    conn.execute("""CREATE TABLE IF NOT EXISTS indexed_slides (
        table_name text NOT NULL, slide_id text NOT NULL, embedding_sha256 text, n_rows int NOT NULL,
        indexed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (table_name, slide_id))""")
    t = sql.Identifier(table)
    if rebuild:
        conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(t))
    expected = f"halfvec({ident['dim']})"
    found = conn.execute("SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                         "WHERE attrelid = to_regclass(%s) AND attname = 'embedding'", (table,)).fetchone()
    if found and found[0] != expected:
        raise RuntimeError(f"{table} stores {found[0]}, this code writes {expected}: "
                           "rebuild it with `td task=index vectordb.rebuild=true`")
    if not found:   # new (or dropped) table: whatever the registry says about it is stale
        conn.execute("DELETE FROM indexed_slides WHERE table_name = %s", (table,))
    conn.execute(sql.SQL("""CREATE TABLE IF NOT EXISTS {} (
        id bigserial PRIMARY KEY, slide_id text NOT NULL, tile_idx int NOT NULL,
        x int NOT NULL, y int NOT NULL, size_l0 real NOT NULL,
        center text, label text, tumor_frac real,
        embedding halfvec({}) NOT NULL, UNIQUE (slide_id, tile_idx))""").format(t, sql.Literal(ident["dim"])))
    return table


def _index(table: str) -> sql.Identifier:
    return sql.Identifier(table + "_hnsw")


def drop_index(conn: psycopg.Connection, table: str):
    """Before a bulk load: inserting into an HNSW index row by row is far slower than building it once."""
    conn.execute(sql.SQL("DROP INDEX IF EXISTS {}").format(_index(table)))


def build_index(conn: psycopg.Connection, table: str, work_mem: str, workers: int) -> bool:
    """HNSW cosine index; no-op if it exists. -> True if it was built. The parallel build keeps the
    graph in shared memory: the container's shm_size must exceed `work_mem`."""
    if conn.execute("SELECT to_regclass(%s)", (table + "_hnsw",)).fetchone()[0]:
        return False
    conn.execute(sql.SQL("SET maintenance_work_mem = {}").format(sql.Literal(work_mem)))
    conn.execute(sql.SQL("SET max_parallel_maintenance_workers = {}").format(sql.Literal(workers)))
    conn.execute(sql.SQL("CREATE INDEX {} ON {} USING hnsw (embedding halfvec_cosine_ops)")
                 .format(_index(table), sql.Identifier(table)))
    return True


def indexed(conn: psycopg.Connection, table: str) -> dict[str, str | None]:
    """slide_id -> embedding hash of what is in the table, to load only new or changed slides."""
    return dict(conn.execute("SELECT slide_id, embedding_sha256 FROM indexed_slides WHERE table_name = %s",
                             (table,)).fetchall())


def upsert_slide(conn: psycopg.Connection, table: str, slide_id: str, features: np.ndarray,
                 tiles: pd.DataFrame, center: str | None, embedding_sha256: str | None = None) -> int:
    """Replace every row of one slide (idempotent: indexing twice leaves one copy)."""
    t = sql.Identifier(table)
    rows = pd.DataFrame({
        "slide_id": slide_id, "tile_idx": np.arange(len(tiles)), "x": tiles["x"].to_numpy(),
        "y": tiles["y"].to_numpy(), "size_l0": tiles["size_l0"].to_numpy(), "center": center,
        "label": tiles["label"].to_numpy() if "label" in tiles else None,
        "tumor_frac": tiles["tumor_frac"].to_numpy() if "tumor_frac" in tiles else None,
    })[META_COLS]
    feats = features.astype(np.float16)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(sql.SQL("DELETE FROM {} WHERE slide_id = %s").format(t), (slide_id,))
        cols = sql.SQL(", ").join(map(sql.Identifier, [*META_COLS, "embedding"]))
        with cur.copy(sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT BINARY)").format(t, cols)) as copy:
            copy.set_types(["text", "int4", "int4", "int4", "float4", "text", "text", "float4", "halfvec"])
            for meta, vec in zip(rows.itertuples(index=False), feats, strict=True):
                copy.write_row([*(None if pd.isna(v) else v for v in meta), HalfVector(vec)])
        cur.execute("INSERT INTO indexed_slides (table_name, slide_id, embedding_sha256, n_rows) "
                    "VALUES (%s, %s, %s, %s) ON CONFLICT (table_name, slide_id) DO UPDATE SET "
                    "embedding_sha256 = excluded.embedding_sha256, n_rows = excluded.n_rows, indexed_at = now()",
                    (table, slide_id, embedding_sha256, len(rows)))
    return len(rows)


def search(conn: psycopg.Connection, table: str, query: np.ndarray, k: int = 10,
           exclude_slide: str | None = None, ef_search: int = 200) -> pd.DataFrame:
    """k nearest tiles by cosine distance. `exclude_slide` drops the query's own slide, whose
    neighbouring tiles would otherwise always win. HNSW filters after its candidate list, which
    can be all from the excluded slide: iterative scan keeps searching until k rows remain.
    `ef_search` 200: recall@10 0.96 against exact search with exclusion (0.91 at pgvector's 40),
    measured on 210k Phikon tiles, ~6 ms per query."""
    where = sql.SQL("WHERE slide_id <> %(ex)s") if exclude_slide else sql.SQL("")
    q = sql.SQL("SELECT {}, embedding <=> %(q)s AS distance FROM {} {} "
                "ORDER BY embedding <=> %(q)s LIMIT %(k)s").format(
        sql.SQL(", ").join(map(sql.Identifier, META_COLS)), sql.Identifier(table), where)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("SET LOCAL hnsw.iterative_scan = strict_order")
        cur.execute(sql.SQL("SET LOCAL hnsw.ef_search = {}").format(sql.Literal(ef_search)))
        cur.execute(q, {"q": HalfVector(query.astype(np.float16)), "k": k, "ex": exclude_slide})
        return pd.DataFrame(cur.fetchall(), columns=[*META_COLS, "distance"])


def count(conn: psycopg.Connection, table: str) -> int:
    return conn.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))).fetchone()[0]

