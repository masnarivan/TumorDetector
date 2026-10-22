"""A registered head version, as inference uses it: model, temperature, conformal quantiles, what it has seen
and the reference of its domain check (E15)."""
from dataclasses import dataclass

import numpy as np


@dataclass
class HeadVersion:
    name: str
    version: int
    model: object            # callable: tiles -> (logit, attention)
    temperature: float
    alpha: float
    q0: float
    q1: float
    validated: bool          # holds the 'validated' alias
    centers: set
    scanners: set
    collection: str
    domain_reference: np.ndarray   # one mean unit tile per development slide outside the calibration fold
    domain_k: int
    domain_threshold: float

    def score(self, features: np.ndarray) -> tuple[float, float, np.ndarray]:
        """-> (logit, calibrated probability, attention over every tile)."""
        from tumordetector.mil.abmil import predict_logits

        logits, att = predict_logits(self.model, [features], "cpu")
        logit = float(logits[0])
        return logit, float(1 / (1 + np.exp(-logit / self.temperature))), att[0]

    def domain_score(self, features: np.ndarray) -> float:
        """Distance of the slide from the development (E15, V); above `domain_threshold` it is referred."""
        from tumordetector.heads import domain

        return float(domain.score(domain.slide_mean(features), self.domain_reference, self.domain_k)[0])


def load(tracking_uri: str, name: str, collection: str, alias: str | None = None,
         version: int | None = None) -> HeadVersion:
    """One version, by alias or by number. Refuses a version trained on another embedding collection, and
    one registered before the conformal sets or the domain check (it cannot give a set or check the domain)."""
    import mlflow

    mlflow.set_tracking_uri(tracking_uri)
    client = mlflow.MlflowClient()
    try:
        mv = client.get_model_version_by_alias(name, alias) if alias else client.get_model_version(name, str(version))
    except mlflow.exceptions.MlflowException as e:
        raise SystemExit(f"no version of {name} " + (f"with alias {alias!r}" if alias else f"v{version}")) from e
    tags = mv.tags
    if tags.get("collection") != collection:
        raise SystemExit(f"{name} v{mv.version} was trained on {tags.get('collection')}, "
                         f"the slides are embedded with {collection}")
    if tags.get("conformal_q0") in (None, "None"):
        raise SystemExit(f"{name} v{mv.version} has no conformal sets: train it again")
    if tags.get("domain_threshold") in (None, "None"):
        raise SystemExit(f"{name} v{mv.version} has no domain check (E15): train it again")
    ref = np.load(mlflow.artifacts.download_artifacts(run_id=mv.run_id, artifact_path="validation/domain.npz"))
    aliases = client.get_registered_model(name).aliases
    model = mlflow.pytorch.load_model(f"models:/{name}/{mv.version}", map_location="cpu")
    if hasattr(model, "module"):   # "pt2" (MLflow 3): an exported graph, traced in eval mode; its callable form
        model = model.module()
    return HeadVersion(name=name, version=int(mv.version), model=model, temperature=float(tags["temperature"]),
                       alpha=float(tags.get("conformal_alpha", "nan")), q0=float(tags["conformal_q0"]),
                       q1=float(tags["conformal_q1"]), validated=str(aliases.get("validated")) == str(mv.version),
                       centers=set(tags.get("centers", "").split(",")) - {""},
                       scanners=set(tags.get("scanners", "").split(",")) - {""}, collection=collection,
                       domain_reference=ref["reference"], domain_k=int(tags["domain_k"]),
                       domain_threshold=float(tags["domain_threshold"]))
