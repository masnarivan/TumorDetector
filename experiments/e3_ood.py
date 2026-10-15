"""E3 - OOD by nearest-neighbour distance: full reference vs k-center subset, regions, HNSW
(protocol in docs/esperimenti.md).

Score of a tile = Euclidean distance (L2-normalised embeddings) to its nearest neighbour in the
reference; score of a slide = mean over its tiles. Steps, each resumable, then the report:

    uv run python experiments/e3_ood.py exact          # configurations 1-3, exact search
    uv run python experiments/e3_ood.py pg-filtered    # 4: existing HNSW index, filter on the reference
    uv run python experiments/e3_ood.py pg-reference   # 4b: HNSW built on the reference only
    uv run python experiments/e3_ood.py report
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from pgvector import HalfVector
from psycopg import sql
from sklearn.metrics import roc_auc_score

from tumordetector.backbones.base import get_device
from tumordetector.io import code_version, read_json
from tumordetector.vectordb.pg import connect, table_name

BACKBONE, SEED = "phikon", 0
N_QUERY, N_PG = 500, 100                   # sampled tiles per queried slide (exact / pgvector)
SUBSETS, MAIN_SUBSET = (64, 256, 1024), 256
REGION, MIN_REGION_TILES = 8, 16
ALPHA, EF_SEARCH, PG_WORKERS, N_BOOT = 0.05, 200, 8, 2000
DSN = "postgresql://td:td_dev@localhost:5433/tumordetector"
REF_TABLE = "e3_reference"                 # temporary table of configuration 4b
ROOT = Path("data/embeddings") / BACKBONE
FULL_OUT = Path("data/experiments/e3")     # per-tile scores, not in git
REPORT = Path("data/reports/experiments/e3")
ROLES = ("reference", "calibration", "eval_id", "eval_ood")


def load_roles() -> pd.DataFrame:
    t = pd.read_csv("data/manifests/camelyon16.csv").merge(pd.read_csv("data/manifests/camelyon16_splits.csv"))
    radboud, test = t.center == "radboud", t.split == "test"
    t["role"] = np.select([radboud & t.cv_fold.isin([0, 1, 2]), radboud & t.cv_fold.isin([3, 4]),
                           radboud & test, ~radboud & test], ROLES, "unused")
    t = t[t.role != "unused"].sort_values(["role", "slide_id"]).reset_index(drop=True)
    assert t.role.value_counts().to_dict() == {"reference": 102, "calibration": 69, "eval_id": 74, "eval_ood": 55}
    assert all((ROOT / f"{s}.npy").exists() for s in t.slide_id)
    return t


def query_tiles(roles: pd.DataFrame) -> dict[str, np.ndarray]:
    """N_QUERY random tiles (random order) of every queried slide; the first N_PG are the pgvector queries."""
    rng = np.random.default_rng(SEED)
    out = {}
    for sid in roles[roles.role != "reference"].slide_id:
        n = read_json(ROOT / f"{sid}.json")["n_tiles"]
        out[sid] = rng.choice(n, min(N_QUERY, n), replace=False)
    return out


def regions(x: np.ndarray, tiles: pd.DataFrame) -> np.ndarray:
    """Means of the 8x8-tile regions with at least MIN_REGION_TILES tiles."""
    side = tiles.size_l0.iloc[0] * REGION
    key = (tiles.x // side).astype(int).astype(str) + "_" + (tiles.y // side).astype(int).astype(str)
    means = [x[rows].mean(0) for rows in tiles.groupby(key).indices.values() if len(rows) >= MIN_REGION_TILES]
    return np.array(means).reshape(-1, x.shape[1])


def unit(x: np.ndarray, device) -> torch.Tensor:
    return torch.nn.functional.normalize(torch.from_numpy(np.asarray(x, dtype=np.float32)).to(device), dim=1)


def kcenter(z: torch.Tensor, n_max: int, rng) -> tuple[np.ndarray, dict, dict]:
    """Greedy k-center: each new centre is the tile farthest from those chosen. The first N of the
    sequence are the N-subset. -> order, coverage radius per N, tiles represented by each centre per N."""
    if len(z) <= min(SUBSETS):
        order = np.arange(len(z))
    else:
        first = int(rng.integers(len(z)))
        order, dist = [first], torch.linalg.vector_norm(z - z[first], dim=1)
        for _ in range(min(n_max, len(z)) - 1):
            nxt = int(dist.argmax())
            order.append(nxt)
            dist = torch.minimum(dist, torch.linalg.vector_norm(z - z[nxt], dim=1))
        order = np.array(order)
    radius, represented = {}, {}
    for n in SUBSETS:
        centres = z[torch.from_numpy(order[:n]).to(z.device)]
        d = torch.cdist(z, centres)
        nearest = d.min(dim=1)
        radius[n] = float(nearest.values.max())
        represented[n] = np.bincount(nearest.indices.cpu().numpy(), minlength=len(centres))
    return order, radius, represented


def nearest(q: torch.Tensor, ref: torch.Tensor, qc: int = 1024, rc: int = 131072) -> tuple[np.ndarray, np.ndarray]:
    """Exact nearest neighbour by brute force -> (Euclidean distance, reference row)."""
    best, arg = torch.full((len(q),), -2.0, device=q.device), torch.zeros(len(q), dtype=torch.long, device=q.device)
    for a in range(0, len(q), qc):
        for b in range(0, len(ref), rc):
            v, i = (q[a:a + qc] @ ref[b:b + rc].T).max(dim=1)
            better = v > best[a:a + qc]
            best[a:a + qc] = torch.where(better, v, best[a:a + qc])
            arg[a:a + qc] = torch.where(better, i + b, arg[a:a + qc])
    return torch.sqrt(torch.clamp(2 - 2 * best, min=0)).cpu().numpy(), arg.cpu().numpy()


def step_exact(roles: pd.DataFrame):
    device, t0 = get_device("auto"), time.time()
    rng = np.random.default_rng(SEED)
    ref = roles[roles.role == "reference"]
    full, full_slide, reg, subset, cover = [], [], [], {n: [] for n in SUBSETS}, []
    kc_seconds = 0.0
    for i, sid in enumerate(ref.slide_id):
        x = np.load(ROOT / f"{sid}.npy")
        z = unit(x, device)
        full.append(z)
        full_slide.append(np.full(len(z), i))
        reg.append(unit(regions(x, pd.read_parquet(ROOT / f"{sid}.parquet")), device))
        tk = time.time()
        order, radius, represented = kcenter(z, max(SUBSETS), rng)
        kc_seconds += time.time() - tk
        for n in SUBSETS:
            subset[n].append(z[torch.from_numpy(order[:n]).to(device)])
            cover.append({"slide_id": sid, "n_tiles": len(z), "N": n, "selected": min(n, len(z)),
                          "radius": radius[n], "represented_median": float(np.median(represented[n])),
                          "represented_max": int(represented[n].max())})
    full, full_slide = torch.cat(full), np.concatenate(full_slide)
    references = {"full": full, "regions": torch.cat(reg), **{f"kcenter_{n}": torch.cat(subset[n]) for n in SUBSETS}}
    pd.DataFrame(cover).to_csv(REPORT / "coverage.csv", index=False)
    print(f"reference built: {len(full)} tiles, k-center {kc_seconds:.0f} s, {time.time() - t0:.0f} s", flush=True)

    region_rows = []
    picks = query_tiles(roles)
    q_tiles, q_meta, q_regions = [], [], []
    for r in roles[roles.role != "reference"].itertuples():
        x = np.load(ROOT / f"{r.slide_id}.npy")
        q_tiles.append(x[picks[r.slide_id]])
        q_meta.append(pd.DataFrame({"slide_id": r.slide_id, "role": r.role, "tile_idx": picks[r.slide_id],
                                    "rank": np.arange(len(picks[r.slide_id]))}))
        rg = regions(x, pd.read_parquet(ROOT / f"{r.slide_id}.parquet"))
        q_regions.append(rg)
        region_rows.append(pd.DataFrame({"slide_id": r.slide_id, "role": r.role, "region": np.arange(len(rg))}))
    q, q_reg = unit(np.concatenate(q_tiles), device), unit(np.concatenate(q_regions), device)
    tiles, regs = pd.concat(q_meta, ignore_index=True), pd.concat(region_rows, ignore_index=True)

    seconds = {}
    for name, refv in references.items():
        ts = time.time()
        if name == "regions":
            regs["score"], _ = nearest(q_reg, refv)
        else:
            tiles[name], arg = nearest(q, refv)
            if name == "full":
                tiles["full_nn_slide"] = ref.slide_id.to_numpy()[full_slide[arg]]
        if device.type == "mps":
            torch.mps.synchronize()
        seconds[name] = round(time.time() - ts, 1)
        print(f"{name}: {len(refv)} vectors, {seconds[name]} s", flush=True)

    FULL_OUT.mkdir(parents=True, exist_ok=True)
    tiles.to_parquet(FULL_OUT / "exact_tiles.parquet")
    regs.to_parquet(FULL_OUT / "exact_regions.parquet")
    sizes = {name: {"vectors": len(v), "mb_float16": round(len(v) * v.shape[1] * 2 / 2**20, 1)}
             for name, v in references.items()}
    (FULL_OUT / "exact_meta.json").write_text(json.dumps(
        {"sizes": sizes, "search_seconds": seconds, "kcenter_seconds": round(kc_seconds),
         "n_query_tiles": len(tiles), "n_query_regions": len(regs), "device": str(device)}, indent=1))


def pg_query(conn, table: str, vectors: np.ndarray, ref_ids: list[str] | None) -> list[float]:
    """Nearest neighbour through the HNSW index -> Euclidean distance, NaN if the scan finds none."""
    where = sql.SQL("WHERE slide_id = ANY(%(ref)s)") if ref_ids else sql.SQL("")
    q = sql.SQL("SELECT embedding <=> %(q)s FROM {} {} ORDER BY embedding <=> %(q)s LIMIT 1").format(
        sql.Identifier(table), where)
    out = []
    with conn.transaction():
        conn.execute("SET LOCAL hnsw.iterative_scan = strict_order")
        conn.execute(sql.SQL("SET LOCAL hnsw.ef_search = {}").format(sql.Literal(EF_SEARCH)))
        for v in vectors:
            row = conn.execute(q, {"q": HalfVector(v.astype(np.float16)), "ref": ref_ids}).fetchone()
            out.append(float(np.sqrt(max(2 * row[0], 0))) if row else float("nan"))
    return out


def run_pg(roles: pd.DataFrame, name: str, table: str, ref_ids: list[str] | None) -> float:
    """Query N_PG tiles of every queried slide on PG_WORKERS connections; one file per slide (resumable)."""
    out = FULL_OUT / name
    out.mkdir(parents=True, exist_ok=True)
    picks = query_tiles(roles)
    todo = [r for r in roles[roles.role != "reference"].itertuples() if not (out / f"{r.slide_id}.parquet").exists()]

    def work(rows):
        conn = connect(DSN)
        for r in rows:
            idx = picks[r.slide_id][:N_PG]
            x = np.load(ROOT / f"{r.slide_id}.npy", mmap_mode="r")[idx]
            ts = time.time()
            d = pg_query(conn, table, np.asarray(x), ref_ids)
            res = pd.DataFrame({"slide_id": r.slide_id, "role": r.role, "tile_idx": idx, "rank": np.arange(len(idx)),
                                "score": d, "seconds": (time.time() - ts) / len(idx)})
            res.to_parquet(out / f"{r.slide_id}.parquet")
            print(f"{name} {r.slide_id}: {np.isnan(d).mean():.0%} without neighbour, "
                  f"{(time.time() - ts) / len(idx):.2f} s/query", flush=True)
        conn.close()

    t0 = time.time()
    with ThreadPoolExecutor(PG_WORKERS) as pool:
        list(pool.map(work, [todo[i::PG_WORKERS] for i in range(PG_WORKERS)]))
    return time.time() - t0


def step_pg_filtered(roles: pd.DataFrame):
    collection = read_json(ROOT / "collection.json")["collection"]
    run_pg(roles, "pg_filtered", table_name(collection), list(roles[roles.role == "reference"].slide_id))


def step_pg_reference(roles: pd.DataFrame):
    """A table and HNSW index of the reference tiles only (same index parameters as the main one)."""
    conn = connect(DSN)
    meta_path = FULL_OUT / "pg_reference_meta.json"
    if not conn.execute("SELECT to_regclass(%s)", (REF_TABLE + "_hnsw",)).fetchone()[0]:
        main = sql.Identifier(table_name(read_json(ROOT / "collection.json")["collection"]))
        conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(REF_TABLE)))
        t0 = time.time()
        conn.execute(sql.SQL("CREATE TABLE {} AS SELECT slide_id, tile_idx, embedding FROM {} "
                             "WHERE slide_id = ANY(%s)").format(sql.Identifier(REF_TABLE), main),
                     (list(roles[roles.role == "reference"].slide_id),))
        copy_s = time.time() - t0
        conn.execute("SET maintenance_work_mem = '4GB'")
        conn.execute("SET max_parallel_maintenance_workers = 7")
        t0 = time.time()
        conn.execute(sql.SQL("CREATE INDEX {} ON {} USING hnsw (embedding halfvec_cosine_ops)").format(
            sql.Identifier(REF_TABLE + "_hnsw"), sql.Identifier(REF_TABLE)))
        build_s = time.time() - t0
        n, idx_size, tab_size = conn.execute(
            "SELECT (SELECT count(*) FROM e3_reference), pg_relation_size('e3_reference_hnsw'), "
            "pg_relation_size('e3_reference')").fetchone()
        FULL_OUT.mkdir(parents=True, exist_ok=True)
        meta = {"vectors": n, "index_mb": round(idx_size / 2**20), "table_mb": round(tab_size / 2**20),
                "copy_seconds": round(copy_s), "build_seconds": round(build_s)}
        meta_path.write_text(json.dumps(meta, indent=1))
        print(meta_path.read_text(), flush=True)
    conn.close()
    run_pg(roles, "pg_reference", REF_TABLE, None)
    if len(list((FULL_OUT / "pg_reference").glob("*.parquet"))) == (roles.role != "reference").sum():
        with connect(DSN) as conn:
            conn.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(REF_TABLE)))
        print(f"all slides queried: {REF_TABLE} dropped")


def conformal(cal: np.ndarray) -> float:
    k = int(np.ceil((len(cal) + 1) * (1 - ALPHA)))
    return float(np.sort(cal)[k - 1])


def ranks(v) -> np.ndarray:
    """+inf (no neighbour) ranks above every distance; sklearn refuses infinities."""
    return np.nan_to_num(np.asarray(v, dtype=float), posinf=1e9)


def evaluate(scores: pd.DataFrame, col: str) -> tuple[dict, pd.DataFrame]:
    """Slide score = mean of its tile (or region) scores; +inf (no neighbour) stays +inf."""
    s = scores.groupby(["slide_id", "role"])[col].mean().reset_index()
    ev = s[s.role.isin(["eval_id", "eval_ood"])]
    y, p = (ev.role == "eval_ood").to_numpy(), ev[col].to_numpy()
    thr = conformal(s[s.role == "calibration"][col].to_numpy())
    t = scores[scores.role.isin(["eval_id", "eval_ood"])]
    tile_auc = roc_auc_score(t.role == "eval_ood", ranks(t[col]))
    return {"auroc": float(roc_auc_score(y, ranks(p))), "threshold": thr,
            "false_referral": float((p[~y] > thr).mean()), "detection": float((p[y] > thr).mean()),
            "tile_auroc": float(tile_auc),
            "median_score": {r: float(s[s.role == r][col].median()) for r in ROLES[1:]}}, ev


def boot_delta(a: pd.DataFrame, b: pd.DataFrame, col_a: str, col_b: str) -> list[float]:
    """95% bootstrap interval of AUROC(b) - AUROC(a) on the same slides, resampled within class."""
    rng = np.random.default_rng(SEED)
    m = a[["slide_id", "role", col_a]].merge(b[["slide_id", col_b]], on="slide_id")
    y = (m.role == "eval_ood").to_numpy()
    pos, neg, va, vb = np.flatnonzero(y), np.flatnonzero(~y), m[col_a].to_numpy(), m[col_b].to_numpy()
    d = []
    for _ in range(N_BOOT):
        i = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        d.append(roc_auc_score(y[i], ranks(vb[i])) - roc_auc_score(y[i], ranks(va[i])))
    return [float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))]


def step_report(roles: pd.DataFrame):
    tiles = pd.read_parquet(FULL_OUT / "exact_tiles.parquet")
    regs = pd.read_parquet(FULL_OUT / "exact_regions.parquet")
    meta = json.loads((FULL_OUT / "exact_meta.json").read_text())
    results, slide_scores = {}, {}
    for name in ["full", *(f"kcenter_{n}" for n in SUBSETS)]:
        results[name], slide_scores[name] = evaluate(tiles, name)
    results["regions"], slide_scores["regions"] = evaluate(regs.rename(columns={"score": "regions"}), "regions")
    for name in ["kcenter_256", "kcenter_64", "kcenter_1024", "regions"]:
        results[name]["delta_auroc_vs_full"] = results[name]["auroc"] - results["full"]["auroc"]
        results[name]["delta_auroc_ci95"] = boot_delta(slide_scores["full"], slide_scores[name], "full", name)

    # the k-center bound: 0 <= d(q, subset) - d(q, all) <= coverage radius of the full neighbour's slide
    cover = pd.read_csv(REPORT / "coverage.csv")
    bound = {}
    for n in SUBSETS:
        r = cover[cover.N == n].set_index("slide_id").radius
        excess = tiles[f"kcenter_{n}"] - tiles.full
        over = excess > r[tiles.full_nn_slide].to_numpy() + 1e-3
        bound[n] = {"min_excess": float(excess.min()), "violations": int(over.sum()),
                    "median_excess": float(excess.median())}

    pg = {}
    for name in ("pg_filtered", "pg_reference"):
        files = sorted((FULL_OUT / name).glob("*.parquet"))
        if len(files) < (roles.role != "reference").sum():
            print(f"{name}: {len(files)} slides queried, not complete: skipped")
            continue
        d = pd.concat(map(pd.read_parquet, files)).merge(tiles[["slide_id", "rank", "full"]], on=["slide_id", "rank"])
        exact100 = d.rename(columns={"full": "full_100"})
        missing = d.score.isna()
        d["score"] = d.score.fillna(np.inf)
        res, s = evaluate(d, "score")
        ref_res, ref_s = evaluate(exact100, "full_100")
        res["no_neighbour_fraction"] = {r: float(missing[d.role == r].mean()) for r in ROLES[1:]}
        found = ~missing
        res["recall_at_1"] = float((d.score[found] - d.full[found] <= 1e-3).sum() / len(d))
        res["seconds_per_query_median"] = float(d.seconds.median())
        res["exact_same_tiles"] = ref_res
        res["delta_auroc_vs_exact_same_tiles"] = res["auroc"] - ref_res["auroc"]
        pg[name] = res
    if (p := FULL_OUT / "pg_reference_meta.json").exists():
        pg.setdefault("pg_reference", {})["index"] = json.loads(p.read_text())

    REPORT.mkdir(parents=True, exist_ok=True)
    pd.concat([s.assign(config=n).rename(columns={n: "score"}) for n, s in slide_scores.items()]).to_csv(
        REPORT / "slide_scores.csv", index=False)
    cov = cover.groupby("N")[["radius", "represented_median", "represented_max"]].describe(
        percentiles=[0.1, 0.5, 0.9]).round(3)
    cov.to_csv(REPORT / "coverage_summary.csv")
    summary = {"backbone": BACKBONE, "collection": read_json(ROOT / "collection.json")["collection"],
               "code_version": code_version(), "seed": SEED, "alpha": ALPHA,
               "slides": roles.role.value_counts().to_dict(), "query_tiles_per_slide": N_QUERY,
               "results": results, "kcenter_bound": bound, "pgvector": pg, **meta}
    (REPORT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    print(cov.to_string())


def main():
    steps = {"exact": step_exact, "pg-filtered": step_pg_filtered, "pg-reference": step_pg_reference,
             "report": step_report}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        sys.exit(f"usage: {sys.argv[0]} {{{','.join(steps)}}}")
    REPORT.mkdir(parents=True, exist_ok=True)
    steps[sys.argv[1]](load_roles())
    return 0


if __name__ == "__main__":
    sys.exit(main())
