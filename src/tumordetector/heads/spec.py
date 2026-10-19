"""What a head is: which slides it covers, how their diagnoses become labels, what counts as a domain
and which slides are held out. One YAML file per head in conf/head/, checked here before any data is read.

Also part of a head: its training recipe (mitigations against the centre effect, experiment E7), how
its scores are calibrated and the battery it must pass.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Calibration(BaseModel):
    """One global temperature (docs/training-multicentro.md: a new centre gives no slides). In
    leave-one-centre-out it is estimated with `inner_folds` folds of the training centres only."""
    model_config = ConfigDict(extra="forbid")

    method: Literal["temperature"] = "temperature"
    inner_folds: int = Field(default=3, ge=2)


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
