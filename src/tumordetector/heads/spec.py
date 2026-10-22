"""What a head is: which slides it covers, how their diagnoses become labels, what counts as a domain
and which slides are held out. One YAML file per head in conf/head/, checked here before any data is read.

Also part of a head: its training recipe (mitigations against the centre effect, experiment E7), how
its scores are calibrated, how it recognises a domain its development does not cover (E15) and the
battery it must pass.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Calibration(BaseModel):
    """One global temperature (docs/training-multicentro.md: a new centre gives no slides). In
    leave-one-centre-out it is estimated with `inner_folds` folds of the training centres only."""
    model_config = ConfigDict(extra="forbid")

    method: Literal["temperature"] = "temperature"
    inner_folds: int = Field(default=3, ge=2)


class Conformal(BaseModel):
    """Prediction sets per class (experiment E10): quantiles of 1 - p(y) for each true class, from the
    out-of-fold logits of the cross-validation, applied to the final model like the temperature."""
    model_config = ConfigDict(extra="forbid")

    method: Literal["per_class"] = "per_class"
    alpha: float = Field(default=0.05, gt=0, lt=0.5)


class DomainCheck(BaseModel):
    """Referral of slides from a domain the development does not cover (experiment E15, candidate V): mean
    distance of the slide's mean unit tile from its k nearest development slides; conformal threshold with
    `alpha` from the cohort fold `calibration_fold`, which is left out of the reference."""
    model_config = ConfigDict(extra="forbid")

    method: Literal["slide_mean_knn"] = "slide_mean_knn"
    k: int = Field(default=5, ge=1)
    alpha: float = Field(default=0.05, gt=0, lt=0.5)
    calibration_fold: int = Field(default=3, ge=0)


class Gate(BaseModel):
    """Promotion battery of the head: initial proposals, to be agreed with the pathologists. The
    worst held-out centre counts; ECE is on calibrated probabilities, as the model is used."""
    model_config = ConfigDict(extra="forbid")

    min_slides: int
    min_cv_auroc: float
    min_loco_worst_auroc: float
    max_ece: float
    max_loco_ece: float
    min_loco_specificity: float
    min_robustness_index: float        # neighbours of the same class elsewhere vs other class here
    # Linear probe of the centre from the head's slide representation: None = reported, no threshold
    # (after E8). It must not exceed the 'validated' version's probe by more than max_probe_regression.
    max_center_probe_auroc: float | None = None
    max_probe_regression: float | None = 0.01
    # Conformal sets (E10): share of positives whose set holds 1, on the worst held-out centre. None = not
    # checked. E10's rule: >= 1 - alpha - 0.05.
    min_loco_positive_coverage: float | None = None


class HeadSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")   # a misspelt key must fail, not be ignored

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: int = Field(ge=1)
    module: Literal["M4", "M5"]
    task: Literal["binary"]
    sites: list[str] = Field(min_length=1)
    datasets: list[str] = Field(min_length=1)
    labels: dict[str, int] = Field(min_length=1)
    domain: list[str] = Field(min_length=1)
    roles: dict[Literal["external"], dict[str, list[str]]] = {}
    recipe: list[Literal["balanced", "group_dro", "stat_mix", "adversarial", "adversarial_negatives"]] = []
    # ^ mitigations, heads/mitigations.py; empty = the training of E6
    calibration: Calibration = Calibration()
    conformal: Conformal = Conformal()
    domain_check: DomainCheck = DomainCheck()
    gate: Gate
    overwrite: bool = False

    @field_validator("sites")
    @classmethod
    def _icd_o(cls, sites):
        bad = [s for s in sites if not (len(s) >= 3 and s[0] == "C" and s[1:3].isdigit())]
        if bad:
            raise ValueError(f"not ICD-O-3 topography codes: {bad}")
        return sites

    @model_validator(mode="after")
    def _labels_fit_the_task(self):
        if self.task == "binary" and sorted(set(self.labels.values())) != [0, 1]:
            raise ValueError(f"a binary head maps diagnoses onto 0 and 1, not {sorted(set(self.labels.values()))}")
        if len(set(self.recipe)) != len(self.recipe):
            raise ValueError(f"mitigations listed twice: {self.recipe}")
        if len(set(self.datasets)) != len(self.datasets):
            raise ValueError(f"datasets listed twice: {self.datasets}")
        return self
