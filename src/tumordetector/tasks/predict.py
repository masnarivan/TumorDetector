"""`td task=predict head=<id> predict.slides=[...]`: the answer of a registered head for slides already
embedded (contract M4). One JSON per slide: calibrated probability, conformal set, domain check (E15),
decision with every reason for a referral, and the tiles with most attention.

Slides of the locked external test are refused: it is read only by its own task, once per version.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from tumordetector.config import dataset_cfg
from tumordetector.io import code_version, write_json


def external_mask(spec, rows: pd.DataFrame) -> np.ndarray:
    """Rows matching the head's external role, by the manifest's own columns (also slides outside the cohort)."""
    mask = np.zeros(len(rows), dtype=bool)
    for column, values in spec.roles.get("external", {}).items():
        mask |= rows[column].isin(values).to_numpy()
    return mask


def run(cfg: DictConfig):
    import torch

    from tumordetector.embed import store
    from tumordetector.heads.cohort import cohort_path, embedding_roots
    from tumordetector.heads.spec import HeadSpec
    from tumordetector.serve import registry
    from tumordetector.serve.answer import answer

    spec = HeadSpec(**OmegaConf.to_container(cfg.head, resolve=True))
    p = cfg.predict
    if not p.slides:
        raise SystemExit("no slide given: predict.slides=[<slide_id>, ...]")
    if p.alias not in ("validated", "candidate"):
        raise SystemExit(f"predict.alias must be validated or candidate, not {p.alias!r}")
    datasets = {name: dataset_cfg(name) for name in spec.datasets}
    manifest = pd.concat([pd.read_csv(d.manifest) for d in datasets.values()], ignore_index=True)
    rows = manifest[manifest.slide_id.isin(list(p.slides))]
    if missing := sorted(set(p.slides) - set(rows.slide_id)):
        raise SystemExit(f"not in the manifests of {spec.datasets}: {missing}")
    if (ext := rows[external_mask(spec, rows)]).shape[0]:
        raise SystemExit(f"slides of the locked external test {sorted(ext.slide_id)}: they are read only by "
                         "`td task=external`, once per validated version")
    if (off := rows[~rows.site.isin(spec.sites)]).shape[0]:
        raise SystemExit(f"slides outside the head's sites {spec.sites}: {sorted(off.slide_id)}")
    roots, ident = embedding_roots({name: d.out for name, d in datasets.items()}, cfg.backbone.name)
    if todo := sorted(r.slide_id for r in rows.itertuples() if not store.is_done(roots[r.dataset], r.slide_id)):
        raise SystemExit(f"no {ident['collection']} embeddings for {todo}: embed them first")
    path = cohort_path(Path(cfg.paths.heads), spec)
    dev = set(pd.read_csv(path).query("role == 'dev'").slide_id) if path.exists() else set()

    model_name = f"head-{spec.id}-{cfg.backbone.name}"
    head = registry.load(cfg.mlflow.tracking_uri, model_name, ident["collection"], alias=p.alias)
    torch.set_num_threads(cfg.mil.threads)

    out = Path(p.out) if p.out else Path(cfg.paths.out) / "reports" / cfg.backbone.name / "predictions" / spec.id
    out.mkdir(parents=True, exist_ok=True)
    code = code_version()
    for r in rows.itertuples():
        slide = store.read_slide(roots[r.dataset], r.slide_id)
        logit, prob, att = head.score(slide.features)
        dist = head.domain_score(slide.features)
        a = answer(prob, head.q0, head.q1, head.validated, r.center in head.centers if p.seen_only else None,
                   r.scanner in head.scanners if p.seen_only else None,
                   dist <= head.domain_threshold if p.domain_check else None)
        top = np.argsort(-att)[:p.top_tiles]
        result = {
            "slide_id": r.slide_id, "dataset": r.dataset, "center": r.center, "scanner": r.scanner,
            "head": f"{spec.id} v{spec.version}", "model": model_name, "model_version": head.version,
            "alias": p.alias, "validated": head.validated, "collection": ident["collection"], "code_version": code,
            "logit": logit, "temperature": head.temperature, "probability": prob,
            "conformal": {"alpha": head.alpha, "q0": head.q0, "q1": head.q1},
            "domain": {"distance": dist, "threshold": head.domain_threshold, "k": head.domain_k},
            **a,
            "in_development": r.slide_id in dev,   # a training slide of this version: not an independent answer
                                                   # (and its own mean is in the domain reference)
            "top_tiles": [{"tile": int(i), "x": int(slide.tiles.x.iloc[i]), "y": int(slide.tiles.y.iloc[i]),
                           "attention": float(att[i])} for i in top],
        }
        write_json(out / f"{r.slide_id}.json", result)
        why = f" ({'; '.join(a['reasons'])})" if a["reasons"] else ""
        print(f"{r.slide_id}: {a['decision']}{why}, p = {prob:.3f}, insieme {a['set']}")
    print(f"answers -> {out}")
