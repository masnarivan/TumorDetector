"""Minimum per-slide metadata (M0). A slide missing a mandatory field is blocked with a
reason; it never enters the pipeline half-described.

Magnification is not here on purpose: it is read from the file itself (mpp) at tiling time.
"""
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class SlideRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")   # datasets may carry extra columns

    slide_id: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    file_md5: str = Field(pattern=r"^[0-9a-f]{32}$")
    patient_pseudo_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    center: str = Field(min_length=1)
    scanner: str = Field(min_length=1)
    stain: Literal["H&E"]
    site: str = Field(pattern=r"^C\d{2}(\.\d)?$")          # ICD-O-3 topography
    procedure: str = Field(min_length=1)
    specimen_type: str = Field(min_length=1)
    reference_diagnosis: str = Field(min_length=1)
    diagnosis_source: Literal["histology", "ihc", "molecular", "consensus"]
    split: Literal["train", "test", "external"]


REQUIRED = list(SlideRecord.model_fields)


def validate_manifest(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """-> (valid rows, blocked rows with a `blocked_reason` column)."""
    reasons = {}
    for i, row in enumerate(df.to_dict("records")):
        try:
            # NaN is how pandas reads an empty cell: treat it as missing.
            SlideRecord(**{k: v for k, v in row.items() if not (isinstance(v, float) and pd.isna(v))})
        except ValidationError as e:
            reasons[i] = "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())
    dup = df["slide_id"].duplicated(keep=False).to_numpy() if "slide_id" in df else []
    for i in [i for i, d in enumerate(dup) if d]:
        reasons[i] = "; ".join(filter(None, [reasons.get(i), "slide_id: duplicated"]))
    blocked = df.iloc[sorted(reasons)].copy()
    blocked["blocked_reason"] = [reasons[i] for i in sorted(reasons)]
    return df.drop(index=df.index[sorted(reasons)]), blocked
