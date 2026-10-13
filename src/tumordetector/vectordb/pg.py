"""Tile embeddings in PostgreSQL + pgvector: similar-case retrieval and, later, OOD scores.

One table per collection (backbone + version), so vectors from different backbone versions
can never end up in the same nearest-neighbour search.
"""
import re

import numpy as np
import pandas as pd
import psycopg
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


def ensure_collection(conn: psycopg.Connection, ident: dict) -> str:
    """Create the registry row, table and indexes for a collection if they are missing."""
    table = table_name(ident["collection"])
    conn.execute("""CREATE TABLE IF NOT EXISTS collections (
        name text PRIMARY KEY, backbone text NOT NULL, version text NOT NULL, dim int NOT NULL,
        table_name text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())""")
    conn.execute("INSERT INTO collections (name, backbone, version, dim, table_name) VALUES (%s, %s, %s, %s, %s) "
                 "ON CONFLICT (name) DO NOTHING",
                 (ident["collection"], ident["backbone"], ident["version"], ident["dim"], table))
    t = sql.Identifier(table)
    conn.execute(sql.SQL("""CREATE TABLE IF NOT EXISTS {} (
        id bigserial PRIMARY KEY, slide_id text NOT NULL, tile_idx int NOT NULL,
        x int NOT NULL, y int NOT NULL, size_l0 real NOT NULL,
        center text, label text, tumor_frac real,
        embedding vector({}) NOT NULL, UNIQUE (slide_id, tile_idx))""").format(t, sql.Literal(ident["dim"])))
    conn.execute(sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} USING hnsw (embedding vector_cosine_ops)")
                 .format(sql.Identifier(table + "_hnsw"), t))
    return table


def upsert_slide(conn: psycopg.Connection, table: str, slide_id: str, features: np.ndarray,
                 tiles: pd.DataFrame, center: str | None) -> int:
    """Replace every row of one slide (idempotent: indexing twice leaves one copy)."""
    t = sql.Identifier(table)
    rows = pd.DataFrame({
        "slide_id": slide_id, "tile_idx": np.arange(len(tiles)), "x": tiles["x"].to_numpy(),
        "y": tiles["y"].to_numpy(), "size_l0": tiles["size_l0"].to_numpy(), "center": center,
        "label": tiles["label"].to_numpy() if "label" in tiles else None,
        "tumor_frac": tiles["tumor_frac"].to_numpy() if "tumor_frac" in tiles else None,
    })[META_COLS]
    feats = features.astype(np.float32)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(sql.SQL("DELETE FROM {} WHERE slide_id = %s").format(t), (slide_id,))
        cols = sql.SQL(", ").join(map(sql.Identifier, [*META_COLS, "embedding"]))
        with cur.copy(sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT BINARY)").format(t, cols)) as copy:
            copy.set_types(["text", "int4", "int4", "int4", "float4", "text", "text", "float4", "vector"])
            for meta, vec in zip(rows.itertuples(index=False), feats, strict=True):
                copy.write_row([*(None if pd.isna(v) else v for v in meta), vec])
    return len(rows)


def search(conn: psycopg.Connection, table: str, query: np.ndarray, k: int = 10,
           exclude_slide: str | None = None) -> pd.DataFrame:
    """k nearest tiles by cosine distance. `exclude_slide` drops the query's own slide, whose
    neighbouring tiles would otherwise always win."""
    where = sql.SQL("WHERE slide_id <> %(ex)s") if exclude_slide else sql.SQL("")
    q = sql.SQL("SELECT {}, embedding <=> %(q)s AS distance FROM {} {} "
                "ORDER BY embedding <=> %(q)s LIMIT %(k)s").format(
        sql.SQL(", ").join(map(sql.Identifier, META_COLS)), sql.Identifier(table), where)
    with conn.cursor() as cur:
        cur.execute(q, {"q": query.astype(np.float32), "k": k, "ex": exclude_slide})
        return pd.DataFrame(cur.fetchall(), columns=[*META_COLS, "distance"])


def count(conn: psycopg.Connection, table: str) -> int:
    return conn.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))).fetchone()[0]
