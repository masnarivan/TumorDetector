"""What a head is: which slides it covers, how their diagnoses become labels, what counts as a domain
and which slides are held out. One YAML file per head in conf/head/, checked here before any data is read.

The training recipe, the aggregator and the gate join the spec when training moves onto heads.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
        if len(set(self.datasets)) != len(self.datasets):
            raise ValueError(f"datasets listed twice: {self.datasets}")
        return self
