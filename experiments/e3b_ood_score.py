"""E3b - an OOD slide score that does not measure tissue composition (protocol in docs/esperimenti.md).

Same roles, the same 500 query tiles per slide and the same conformal threshold as E3. Tile score
d = Euclidean distance (L2-normalised embeddings) to the nearest reference tile. Slide scores:

  S0 mean of d (E3)      S1 median of d      S2 25th percentile of d
  S3 mean of d(q, v) / rho(v), v = nearest reference tile of q, rho(v) = distance of v to its nearest
     reference tile in another slide (within the same reference)

Two references: 256 k-center prototypes per slide (vectordb/reduce.py, as in the vector DB) and,
for comparison, every tile.

    uv run python experiments/e3b_ood_score.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from e3_ood import ROOT, SEED, conformal, load_roles, nearest, query_tiles, ranks, unit
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from tumordetector.backbones.base import get_device
from tumordetector.io import code_version, read_json
from tumordetector.vectordb import reduce

PROTOTYPES = 256
SCORES = ("S0", "S1", "S2", "S3")
PREFERENCE = ("S1", "S2", "S3")               # first acceptable one is chosen (simplest first)
MAIN = "kcenter_256"                          # the criterion is read on this reference
LOW_TISSUE = 0.8                              # tissue_frac below this: loose tissue, fat (approximation)
CRITERION = {"false_referral": (0.02, 0.08), "tumor_false_referrals_max": 2, "detection_min": 0.95,
             "auroc_min": 0.98}
REPORT = Path("data/reports/experiments/e3b")


def nearest_other_slide(z: torch.Tensor, slide: torch.Tensor, qc: int = 1024, rc: int = 131072) -> np.ndarray:
    """rho: for every reference vector, Euclidean distance to the nearest one from another slide."""
    best = torch.full((len(z),), -2.0, device=z.device)
    for a in range(0, len(z), qc):
        for b in range(0, len(z), rc):
            s = z[a:a + qc] @ z[b:b + rc].T
            s[slide[a:a + qc, None] == slide[None, b:b + rc]] = -2.0
            best[a:a + qc] = torch.maximum(best[a:a + qc], s.max(dim=1).values)
    return torch.sqrt(torch.clamp(2 - 2 * best, min=0)).cpu().numpy()


def slide_scores(tiles: pd.DataFrame) -> pd.DataFrame:
    g = tiles.groupby(["slide_id", "role"])
    return pd.DataFrame({"S0": g.d.mean(), "S1": g.d.median(), "S2": g.d.quantile(0.25),
                         "S3": g.ratio.mean()}).reset_index()


def evaluate(s: pd.DataFrame, comp: pd.DataFrame, col: str) -> dict:
    thr = conformal(s[s.role == "calibration"][col].to_numpy())
    ev = s[s.role.isin(["eval_id", "eval_ood"])]
    y, p = (ev.role == "eval_ood").to_numpy(), ev[col].to_numpy()
    rid = s[s.role == "eval_id"].merge(comp, on="slide_id")
    ref = rid[col] > thr
    tum = rid.label == 1
    rho_t = spearmanr(rid[tum][col], rid[tum].tumor_frac)[0]
    rho_l = spearmanr(rid[col], rid.low_tissue_frac)[0]
    return {"threshold": thr, "false_referral": float(ref.mean()),
            "false_referrals": int(ref.sum()), "normal_false_referrals": int(ref[~tum].sum()),
            "tumor_false_referrals": int(ref[tum].sum()), "n_normal": int((~tum).sum()), "n_tumor": int(tum.sum()),
            "detection": float((p[y] > thr).mean()), "auroc": float(roc_auc_score(y, ranks(p))),
            "spearman_tumor_frac": float(rho_t), "spearman_low_tissue_frac": float(rho_l),
            "referred": sorted(rid[ref].slide_id)}


def acceptable(r: dict) -> bool:
    lo, hi = CRITERION["false_referral"]
    return (lo <= r["false_referral"] <= hi and r["tumor_false_referrals"] <= CRITERION["tumor_false_referrals_max"]
            and r["detection"] >= CRITERION["detection_min"] and r["auroc"] >= CRITERION["auroc_min"])


def main():
    device, t0 = get_device("auto"), time.time()
    roles = load_roles()
    ref = roles[roles.role == "reference"]
    full, full_slide, proto, proto_slide = [], [], [], []
    for i, sid in enumerate(ref.slide_id):
        x = np.load(ROOT / f"{sid}.npy")
        full.append(x)
        full_slide.append(np.full(len(x), i))
        k = reduce.kcenter(x, PROTOTYPES).tiles
        proto.append(x[k])
        proto_slide.append(np.full(len(k), i))
    references = {MAIN: (np.concatenate(proto), np.concatenate(proto_slide)),
                  "full": (np.concatenate(full), np.concatenate(full_slide))}
    del full, proto
    print(f"references built, {time.time() - t0:.0f} s", flush=True)

    picks = query_tiles(roles)
    queried = roles[roles.role != "reference"]
    q_meta, q_vec, comp = [], [], []
    for r in queried.itertuples():
        x = np.load(ROOT / f"{r.slide_id}.npy", mmap_mode="r")
        q_vec.append(np.asarray(x[picks[r.slide_id]]))
        q_meta.append(pd.DataFrame({"slide_id": r.slide_id, "role": r.role, "tile_idx": picks[r.slide_id]}))
        t = pd.read_parquet(ROOT / f"{r.slide_id}.parquet", columns=["label", "tissue_frac"])
        comp.append({"slide_id": r.slide_id, "label": r.label, "tumor_frac": float((t.label == "tumor").mean()),
                     "low_tissue_frac": float((t.tissue_frac < LOW_TISSUE).mean())})
    q = unit(np.concatenate(q_vec), device)
    base, comp = pd.concat(q_meta, ignore_index=True), pd.DataFrame(comp)

    results, all_scores, timing = {}, [], {}
    for name, (vec, slide) in references.items():
        ts = time.time()
        z = unit(vec, device)
        rho = nearest_other_slide(z, torch.from_numpy(slide).to(device))
        d, arg = nearest(q, z)
        tiles = base.assign(d=d, rho=rho[arg], ratio=d / np.maximum(rho[arg], 1e-6))
        s = slide_scores(tiles)
        results[name] = {c: evaluate(s, comp, c) for c in SCORES}
        results[name]["rho"] = {"median": float(np.median(rho)), "p10": float(np.quantile(rho, 0.1)),
                                "p90": float(np.quantile(rho, 0.9))}
        all_scores.append(s.assign(reference=name))
        timing[name] = round(time.time() - ts)
        print(f"{name}: {len(vec)} vectors, {timing[name]} s", flush=True)
        del z
        if device.type == "mps":
            torch.mps.empty_cache()

    main_res = results[MAIN]
    chosen = next((c for c in PREFERENCE if acceptable(main_res[c])), None)
    summary = {"code_version": code_version(), "seed": SEED,
               "collection": read_json(ROOT / "collection.json")["collection"],
               "prototypes": PROTOTYPES, "criterion": CRITERION, "criterion_reference": MAIN,
               "acceptable": {c: acceptable(main_res[c]) for c in SCORES}, "chosen": chosen,
               "results": results, "seconds": timing, "device": str(device)}
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "summary.json").write_text(json.dumps(summary, indent=1))
    pd.concat(all_scores).merge(comp, on="slide_id").to_csv(REPORT / "slide_scores.csv", index=False)
    cols = ["false_referral", "normal_false_referrals", "tumor_false_referrals", "detection", "auroc",
            "spearman_tumor_frac", "spearman_low_tissue_frac"]
    for name in references:
        print(f"\n{name}")
        print(pd.DataFrame({c: results[name][c] for c in SCORES}).loc[cols].T.round(3).to_string())
    print(f"\nacceptable on {MAIN}: {summary['acceptable']}; chosen: {chosen}")


if __name__ == "__main__":
    main()
