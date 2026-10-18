"""CAMELYON16 manifest: one row per slide, in the common schema plus dataset-specific columns.

Sources (all public, no login):
- evaluation/reference.csv  slide label (negative / macro / micro) and centre (0 Radboud, 1 Utrecht)
- bucket listing            slide file sizes, which slides have an annotation XML
- checksums.md5             to verify each download later
- README.md of the bucket   slides whose tumor annotations are NOT exhaustive (hard-coded below)

Ported from prototype 02 (mil-camelyon16, scripts/make_manifest.py).
"""
import io
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import certifi
import pandas as pd

BUCKET = "https://camelyon-dataset.s3.amazonaws.com"
PREFIX = "CAMELYON16"

# From the bucket README ("Notes about the data"): these tumor slides may contain tumor
# areas that were not annotated. Fine for MIL (slide label only), but they must not be
# used as tile-level ground truth (baseline training, attention evaluation).
NOT_EXHAUSTIVE = {
    "tumor_010", "tumor_015", "tumor_018", "tumor_020", "tumor_025", "tumor_029",
    "tumor_033", "tumor_034", "tumor_044", "tumor_046", "tumor_051", "tumor_054",
    "tumor_055", "tumor_056", "tumor_067", "tumor_079", "tumor_085", "tumor_092",
    "tumor_095", "tumor_110",
}

# Slides of one patient, found in the pathology case number of the original file name (experiment
# E3b, TIFF headers): slide -> the slide whose patient it shares. The only repeat among 398 headers.
SAME_PATIENT = {"test_116": "tumor_091"}   # Utrecht case T13-15766

# Every CAMELYON16 file is a Philips-converted TIFF except this one, a generic TIFF like the
# CAMELYON17 files of CWZ, Radboud and Rijnstate (experiment C17, section 4): probably a later
# rescan or reconversion, a different "domain" from the other Radboud slides.
GENERIC_TIFF = {"normal_144"}

CENTERS = {0: "radboud", 1: "utrecht"}
SCANNERS = {0: "3DHistech Pannoramic Flash II 250", 1: "Hamamatsu NanoZoomer-XR C12000-01"}


def _fetch(path: str) -> bytes:
    # python.org builds of Python on macOS ship without system CA certificates.
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(f"{BUCKET}/{path}", context=ctx) as r:
        return r.read()


def _list_bucket(prefix: str) -> dict[str, int]:
    """file name -> size in bytes for every object under prefix (S3 ListObjectsV2, paginated)."""
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    out, token = {}, None
    while True:
        query = f"?list-type=2&prefix={prefix}" + (f"&continuation-token={urllib.parse.quote(token)}" if token else "")
        root = ET.fromstring(_fetch(query))
        for obj in root.findall("s3:Contents", ns):
            key = obj.find("s3:Key", ns).text
            out[key.rsplit("/", 1)[-1]] = int(obj.find("s3:Size", ns).text)
        token = root.findtext("s3:NextContinuationToken", namespaces=ns)
        if not token:
            return out


def to_manifest(ref: pd.DataFrame, sizes: dict[str, int], xmls: dict[str, int], md5: dict[str, str]) -> pd.DataFrame:
    """Pure part of the build (no network), so it can be tested."""
    sid = ref["image"].str.removesuffix(".tif")
    label = (ref["class"] != "negative").astype(int)
    m = pd.DataFrame({
        "slide_id": sid,
        "dataset": "camelyon16",
        "file_md5": sid.map(lambda s: md5.get(f"images/{s}.tif")),
        # CAMELYON16 does not publish patient ids: one slide is one patient, except the slides
        # found to share a patient (SAME_PATIENT), so that splits by patient keep them together.
        "patient_pseudo_id": "c16_" + sid.replace(SAME_PATIENT),
        "case_id": "c16_" + sid.replace(SAME_PATIENT),
        "center": ref["center"].map(CENTERS),
        "scanner": ref["center"].map(SCANNERS),
        "stain": "H&E",
        "site": "C77.3",                                    # axillary lymph nodes
        "procedure": "sentinel lymph node biopsy",
        "specimen_type": "resection",
        "reference_diagnosis": ref["class"],                # negative / macro / micro
        "diagnosis_source": "histology",
        # normal_* / tumor_* are the official training set, test_* the official test set
        "split": sid.str.startswith("test_").map({True: "test", False: "train"}),
        "label": label,                                     # slide label used by MIL
        "size_gb": sid.map(lambda s: sizes.get(f"{s}.tif", 0) / 1e9).round(3),
        "has_xml": sid.map(lambda s: f"{s}.xml" in xmls),
        "file_format": sid.isin(GENERIC_TIFF).map({True: "generic_tiff", False: "philips_tiff"}),
    })
    # Usable as tile-level ground truth: negatives (no tumor anywhere) and tumor slides
    # with exhaustive annotations. Not the 20 slides listed above.
    m["exhaustive_annot"] = (m["label"] == 0) | (m["has_xml"] & ~m["slide_id"].isin(NOT_EXHAUSTIVE))
    return m.sort_values(["split", "slide_id"]).reset_index(drop=True)


def build_manifest() -> pd.DataFrame:
    ref = pd.read_csv(io.BytesIO(_fetch(f"{PREFIX}/evaluation/reference.csv")))
    sizes = _list_bucket(f"{PREFIX}/images/")
    xmls = _list_bucket(f"{PREFIX}/annotations/")
    md5 = {}
    for line in _fetch(f"{PREFIX}/checksums.md5").decode().splitlines():
        digest, name = line.split(maxsplit=1)
        md5[name.lstrip("*")] = digest
    m = to_manifest(ref, sizes, xmls, md5)
    # Sanity checks: every slide has a file, every positive slide has an XML, no negative has one.
    assert len(m) == len(sizes) == 399, (len(m), len(sizes))
    assert (m["has_xml"] == (m["label"] == 1)).all()
    assert m["slide_id"].isin(NOT_EXHAUSTIVE).sum() == len(NOT_EXHAUSTIVE)
    return m


def slide_url(slide_id: str) -> str:
    return f"{BUCKET}/{PREFIX}/images/{slide_id}.tif"


def annotation_url(slide_id: str) -> str:
    return f"{BUCKET}/{PREFIX}/annotations/{slide_id}.xml"
