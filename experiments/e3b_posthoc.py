"""E3b, post-hoc (not in the protocol): are the referred Radboud test tumour slides far because of their
tumour? S0 (mean nearest-neighbour distance, k-center 256 reference) recomputed on the normal tiles
only, with the same conformal threshold.

    uv run python experiments/e3b_posthoc.py
"""
import json

import numpy as np
import pandas as pd
from e3_ood import ROOT, conformal, load_roles, nearest, query_tiles, unit
from e3b_ood_score import PROTOTYPES, REPORT

from tumordetector.backbones.base import get_device
from tumordetector.vectordb import reduce


def main():
    device, roles = get_device("auto"), load_roles()
    ref = roles[roles.role == "reference"]
    protos = []
    for sid in ref.slide_id:
        x = np.load(ROOT / f"{sid}.npy")
        protos.append(x[reduce.kcenter(x, PROTOTYPES).tiles])
    z = unit(np.concatenate(protos), device)
    picks, rows = query_tiles(roles), []
    for r in roles[roles.role != "reference"].itertuples():
        idx = picks[r.slide_id]
        x = np.load(ROOT / f"{r.slide_id}.npy", mmap_mode="r")
        label = pd.read_parquet(ROOT / f"{r.slide_id}.parquet", columns=["label"]).label.to_numpy()[idx]
        d, _ = nearest(unit(np.asarray(x[idx]), device), z)
        rows.append({"slide_id": r.slide_id, "role": r.role, "label": r.label, "S0": float(d.mean()),
                     "S0_normal_tiles": float(d[label == "normal"].mean()),
                     "tumor_tiles": int((label == "tumor").sum())})
    s = pd.DataFrame(rows)
    thr = conformal(s[s.role == "calibration"].S0.to_numpy())
    above = lambda col: {int(k): int(v) for k, v in (s.assign(a=s[col] > thr).groupby(["role", "label"]).a.sum()  # noqa: E731
                                                     .loc["eval_id"].items())}
    out = {"threshold": thr,
           "median": s.groupby(["role", "label"])[["S0", "S0_normal_tiles"]].median().round(3)
                      .reset_index().to_dict("records"),
           "eval_id_referred_by_label": {"S0": above("S0"), "S0_normal_tiles": above("S0_normal_tiles")},
           "calibration_above_threshold_by_label": {int(k): int(v) for k, v in s[s.role == "calibration"]
                                                    .assign(a=lambda t: t.S0 > thr).groupby("label").a.sum().items()},
           "eval_id_referred": s[(s.role == "eval_id") & (s.S0 > thr)].round(3).to_dict("records")}
    (REPORT / "posthoc.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
