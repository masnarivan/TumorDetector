"""CAMELYON17 manifest: one row per labelled slide, in the common schema plus dataset-specific columns.

1000 slides of sentinel lymph nodes, 5 per patient, 200 patients from 5 Dutch centres (licence CC0).
Only the official training set (patients 0-99, 20 per centre) has public labels and centres; the 500
test slides (patients 100-199) have neither, so they are not in the manifest.

Sources (all public, no login), same bucket as CAMELYON16:
- stages.csv       slide label (negative / itc / micro / macro), patient pN stage, centre 0-4
- bucket listing   slide file sizes, which slides have an annotation XML (10 per centre, all positive)
- checksums.md5    to verify each download later
"""
import io

import pandas as pd

from tumordetector.data.camelyon16 import BUCKET, _fetch, _list_bucket

PREFIX = "CAMELYON17"

# Centre index in stages.csv -> centre, and its scanner. From the challenge paper (Bandi et al.,
# IEEE TMI 2019, table I), not from the files: to check against the resolution read at tiling.
CENTERS = {0: "radboud", 1: "cwz", 2: "utrecht", 3: "rijnstate", 4: "lpon"}
SCANNERS = {
    0: "3DHistech Pannoramic Flash II 250",
    1: "3DHistech Pannoramic Flash II 250",
    2: "Hamamatsu NanoZoomer-XR C12000-01",
    3: "3DHistech Pannoramic Flash II 250",
    4: "Philips IntelliSite Ultra Fast Scanner",
}
# File format, read from the TIFF headers (experiment C17, section 2): LPON files are native Philips
# TIFFs with scan date and scanner; the other centres' are converted TIFFs with no metadata.
PHILIPS_TIFF = {"lpon"}
# Isolated tumour cells (pN0(i+)): node-negative for staging, yet tumour cells are present. A binary
# tumour/normal label would be wrong either way, so it is left empty: excluded from binary
# training and evaluation until the rule is agreed with the pathologists.
LABELS = {"negative": 0, "itc": None, "micro": 1, "macro": 1}


def to_manifest(stages: pd.DataFrame, sizes: dict[str, int], xmls: dict[str, int], md5: dict[str, str]) -> pd.DataFrame:
    """Pure part of the build (no network), so it can be tested."""
    slides = stages[stages["patient"].str.endswith(".tif")]
    sid = slides["patient"].str.removesuffix(".tif")
    patient = sid.str.rsplit("_node_", n=1).str[0]
    zips = stages[stages["patient"].str.endswith(".zip")]
    pn = pd.Series(zips["stage"].to_numpy(), index=zips["patient"].str.removesuffix(".zip"))   # patient pN stage
    m = pd.DataFrame({
        "slide_id": sid,
        "dataset": "camelyon17",
        "file_md5": sid.map(lambda s: md5.get(f"images/{s}.tif")),
        "patient_pseudo_id": "c17_" + patient,              # 5 lymph nodes per patient: split by patient
        "case_id": "c17_" + patient,
        "center": slides["center"].map(CENTERS),
        "scanner": slides["center"].map(SCANNERS),
        "stain": "H&E",
        "site": "C77.3",                                    # axillary lymph nodes
        "procedure": "sentinel lymph node biopsy",
        "specimen_type": "resection",
        "reference_diagnosis": slides["stage"],             # negative / itc / micro / macro
        "diagnosis_source": "histology",
        "split": "train",                                   # official training set: the only one labelled
        "label": slides["stage"].map(LABELS).astype("Int64"),
        "patient_pn_stage": patient.map(pn),
        "size_gb": sid.map(lambda s: sizes.get(f"{s}.tif", 0) / 1e9).round(3),
        "has_xml": sid.map(lambda s: f"{s}.xml" in xmls),
        "file_format": slides["center"].map(CENTERS).isin(PHILIPS_TIFF).map(
            {True: "philips_tiff", False: "generic_tiff"}),
    })
    # Usable as tile-level ground truth: negatives, and the annotated slides ("exhaustively
    # annotated" in the bucket README).
    m["exhaustive_annot"] = (m["reference_diagnosis"] == "negative") | m["has_xml"]
    return m.sort_values("slide_id").reset_index(drop=True)


def build_manifest() -> pd.DataFrame:
    stages = pd.read_csv(io.BytesIO(_fetch(f"{PREFIX}/stages.csv")))
    sizes = _list_bucket(f"{PREFIX}/images/")
    xmls = _list_bucket(f"{PREFIX}/annotations/")
    md5 = {}
    for line in _fetch(f"{PREFIX}/checksums.md5").decode().splitlines():
        digest, name = line.split(maxsplit=1)
        md5[name.lstrip("*")] = digest
    m = to_manifest(stages, sizes, xmls, md5)
    # Sanity checks: 100 labelled slides per centre, all with a file and a checksum; every
    # annotation belongs to a positive labelled slide.
    assert len(m) == 500 and (m.groupby("center").size() == 100).all(), m.groupby("center").size()
    assert m["file_md5"].notna().all() and (m["size_gb"] > 0).all()
    assert m["has_xml"].sum() == len(xmls) == 50 and (m[m["has_xml"]]["reference_diagnosis"] != "negative").all()
    return m


def slide_url(slide_id: str) -> str:
    return f"{BUCKET}/{PREFIX}/images/{slide_id}.tif"


def annotation_url(slide_id: str) -> str:
    return f"{BUCKET}/{PREFIX}/annotations/{slide_id}.xml"
