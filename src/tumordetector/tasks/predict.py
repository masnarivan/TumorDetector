"""`td task=predict head=<id> predict.slides=[...]`: the answer of a registered head for slides already
embedded (contract M4). One JSON per slide: calibrated probability, conformal set, decision with every
reason for a referral, and the tiles with most attention.

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
    import mlflow
    import torch

    from tumordetector.embed import store
    from tumordetector.heads.cohort import cohort_path, embedding_roots
    from tumordetector.heads.protocol import sigmoid
    from tumordetector.heads.spec import HeadSpec
    from tumordetector.mil.abmil import predict_logits
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
    mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)
    client = mlflow.MlflowClient()
    try:
        version = client.get_model_version_by_alias(model_name, p.alias)
    except mlflow.exceptions.MlflowException as e:
        raise SystemExit(f"no version of {model_name} with alias {p.alias!r}") from e
    tags = version.tags
    if tags.get("collection") != ident["collection"]:
        raise SystemExit(f"{model_name} v{version.version} was trained on {tags.get('collection')}, "
                         f"the slides are embedded with {ident['collection']}")
    if "conformal_q0" not in tags or tags["conformal_q0"] == "None":
        raise SystemExit(f"{model_name} v{version.version} has no conformal sets: train it again")
    temperature, q0, q1 = (float(tags[k]) for k in ("temperature", "conformal_q0", "conformal_q1"))
    validated = "validated" in client.get_registered_model(model_name).aliases and \
        client.get_model_version_by_alias(model_name, "validated").version == version.version
    centers, scanners = set(tags.get("centers", "").split(",")), set(tags.get("scanners", "").split(","))
    model = mlflow.pytorch.load_model(f"models:/{model_name}@{p.alias}", map_location="cpu")
    if hasattr(model, "module"):   # "pt2" (MLflow 3): an exported graph, traced in eval mode; its callable form
        model = model.module()
    torch.set_num_threads(cfg.mil.threads)

    out = Path(p.out) if p.out else Path(cfg.paths.out) / "reports" / cfg.backbone.name / "predictions" / spec.id
    out.mkdir(parents=True, exist_ok=True)
    code = code_version()
    for r in rows.itertuples():
        slide = store.read_slide(roots[r.dataset], r.slide_id)
        logits, att = predict_logits(model, [slide.features], "cpu")
        logit = float(logits[0])
        prob = float(sigmoid(np.array(logit / temperature)))
        a = answer(prob, q0, q1, validated, r.center in centers if p.seen_only else None,
                   r.scanner in scanners if p.seen_only else None)
        top = np.argsort(-att[0])[:p.top_tiles]
        result = {
            "slide_id": r.slide_id, "dataset": r.dataset, "center": r.center, "scanner": r.scanner,
            "head": f"{spec.id} v{spec.version}", "model": model_name, "model_version": int(version.version),
            "alias": p.alias, "validated": validated, "collection": ident["collection"], "code_version": code,
            "logit": logit, "temperature": temperature, "probability": prob,
            "conformal": {"alpha": float(tags.get("conformal_alpha", "nan")), "q0": q0, "q1": q1},
            **a,
            "in_development": r.slide_id in dev,   # a training slide of this version: not an independent answer
            "top_tiles": [{"tile": int(i), "x": int(slide.tiles.x.iloc[i]), "y": int(slide.tiles.y.iloc[i]),
                           "attention": float(att[0][i])} for i in top],
        }
        write_json(out / f"{r.slide_id}.json", result)
        why = f" ({'; '.join(a['reasons'])})" if a["reasons"] else ""
        print(f"{r.slide_id}: {a['decision']}{why}, p = {prob:.3f}, insieme {a['set']}")
    print(f"answers -> {out}")
