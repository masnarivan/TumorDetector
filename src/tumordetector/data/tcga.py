"""TCGA manifest: a fixed sample of diagnostic slides for the MVP (docs/mvp.md), in the common schema.

Source: the GDC API (open access, no login): diagnostic slides (FFPE, `DX`), SVS, one `DX1` slide per
patient. Every TCGA diagnostic slide is a primary tumour, so the sample serves two uses, not a
tumour / normal task:

- controller (M3): breast, colon, prostate and lung adenocarcinoma from the 4 tissue source sites that
  have all four organs, 12 patients per organ and site, so that the site does not tell the organ;
- head `nsclc_subtype` (M5): lung adenocarcinoma against squamous cell carcinoma, 25 patients per class
  from each of the 4 sites with most of both;
- unseen tissue: kidney clear cell carcinoma, never in the controller's reference, to measure its OOD.

The sample is drawn once (fixed seed, patient order from a hash, not from the API's order) and the
manifest is versioned in git: rebuilding it from a GDC that changed would draw different slides.
"""
import hashlib
import json
import re
import ssl
import urllib.parse
import urllib.request

import pandas as pd
import truststore

API = "https://api.gdc.cancer.gov"
SEED = 0

# project -> (ICD-O-3 topography, reference diagnosis). The TCGA project is the diagnosis of the
# slide's tumour as classified by TCGA's pathology review; GDC's `primary_diagnosis` is kept beside it.
PROJECTS = {
    "TCGA-BRCA": ("C50.9", "breast invasive carcinoma"),
    "TCGA-COAD": ("C18.9", "colon adenocarcinoma"),
    "TCGA-PRAD": ("C61.9", "prostate adenocarcinoma"),
    "TCGA-LUAD": ("C34.9", "lung adenocarcinoma"),
    "TCGA-LUSC": ("C34.9", "lung squamous cell carcinoma"),
    "TCGA-KIRC": ("C64.9", "kidney clear cell carcinoma"),
}
CONTROLLER = {"projects": ["TCGA-BRCA", "TCGA-COAD", "TCGA-PRAD", "TCGA-LUAD"], "per_site": 12,
              "sites": ["Indivumed", "University of Pittsburgh", "International Genomics Consortium",
                        "Roswell Park"]}
NSCLC = {"projects": ["TCGA-LUAD", "TCGA-LUSC"], "per_site": 25,
         "sites": ["International Genomics Consortium", "Asterand", "Indivumed", "Prince Charles Hospital"]}
UNSEEN = {"projects": ["TCGA-KIRC"], "n": 24}
FIELDS = ["file_id", "file_name", "file_size", "md5sum", "cases.submitter_id", "cases.project.project_id",
          "cases.tissue_source_site.name", "cases.diagnoses.primary_diagnosis"]


def _get(path: str, params: dict) -> dict:
    # The operating system's trust store, as for Qdrant: on a network that inspects TLS the server
    # certificate is signed by a CA installed in the system, not in certifi.
    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(params)}", context=ctx, timeout=120) as r:
        return json.load(r)


def fetch_files() -> list[dict]:
    """Every open diagnostic SVS of the projects above (one GDC request: ~3,300 files)."""
    filters = {"op": "and", "content": [
        {"op": "in", "content": {"field": "cases.project.project_id", "value": sorted(PROJECTS)}},
        {"op": "=", "content": {"field": "experimental_strategy", "value": "Diagnostic Slide"}},
        {"op": "=", "content": {"field": "data_format", "value": "SVS"}},
        {"op": "=", "content": {"field": "access", "value": "open"}}]}
    out = _get("files", {"filters": json.dumps(filters), "fields": ",".join(FIELDS), "size": 10000,
                         "format": "json"})
    hits = out["data"]["hits"]
    assert len(hits) == out["data"]["pagination"]["total"], "GDC returned a partial page"
    return hits


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _order(patient: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}/{patient}".encode()).hexdigest()


def files_table(hits: list[dict]) -> pd.DataFrame:
    """GDC hits -> one row per DX1 slide of a patient (the first diagnostic slide; DX2.. are other blocks)."""
    rows = []
    for h in hits:
        case = h["cases"][0]
        diagnoses = case.get("diagnoses") or [{}]
        rows.append({"file_id": h["file_id"], "file_name": h["file_name"], "size": h["file_size"],
                     "md5": h["md5sum"], "patient": case["submitter_id"], "project": case["project"]["project_id"],
                     "tss": case["tissue_source_site"]["name"],
                     "primary_diagnosis": diagnoses[0].get("primary_diagnosis")})
    t = pd.DataFrame(rows)
    t = t[t.file_name.str.contains(r"-DX1\.", regex=True)]
    # A few patients have the same DX1 in two files (rescans): keep one, by file id.
    return t.sort_values("file_id").drop_duplicates("patient").reset_index(drop=True)


def draw(t: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """The sample, with the uses of each slide. Pure (no network), so it can be tested."""
    t = t.assign(order=t.patient.map(lambda p: _order(p, seed))).sort_values("order")
    pick = {}                                                     # file_id -> set of uses

    def take(rows: pd.DataFrame, n: int, use: str):
        if len(rows) < n:
            raise ValueError(f"{use}: {len(rows)} patients, {n} needed ({rows.project.unique()}, {rows.tss.unique()})")
        for fid in rows.file_id.iloc[:n]:
            pick.setdefault(fid, set()).add(use)

    # The lung head first: where a site gives lung adenocarcinoma to both uses, the controller's
    # 12 are the first 12 of the head's 25 (same patient order), so the overlap is as large as it can be.
    for project in NSCLC["projects"]:
        for site in NSCLC["sites"]:
            take(t[(t.project == project) & (t.tss == site)], NSCLC["per_site"], "nsclc")
    for project in CONTROLLER["projects"]:
        for site in CONTROLLER["sites"]:
            take(t[(t.project == project) & (t.tss == site)], CONTROLLER["per_site"], "controller")
    for project in UNSEEN["projects"]:
        take(t[t.project == project], UNSEEN["n"], "unseen")

    s = t[t.file_id.isin(pick)].copy()
    s["uses"] = s.file_id.map(lambda f: "+".join(sorted(pick[f])))
    return s


def to_manifest(s: pd.DataFrame) -> pd.DataFrame:
    """Drawn slides -> manifest rows in the common schema."""
    m = pd.DataFrame({
        "slide_id": s.file_name.str.removesuffix(".svs"),
        "dataset": "tcga",
        "file_md5": s.md5,
        "patient_pseudo_id": s.patient,                    # TCGA barcodes are already de-identified
        "case_id": s.patient,
        "center": s.tss.map(slug),                          # tissue source site
        "scanner": "Aperio",                                # TCGA diagnostic slides; vendor recorded at tiling
        "stain": "H&E",
        "site": s.project.map(lambda p: PROJECTS[p][0]),
        "procedure": "resection",
        "specimen_type": "FFPE diagnostic slide",
        "reference_diagnosis": s.project.map(lambda p: PROJECTS[p][1]),
        "diagnosis_source": "histology",
        "split": "train",
        "label": pd.array([pd.NA] * len(s), dtype="Int64"),   # no slide-level tumour label: every slide is a tumour
        "project_id": s.project,
        "primary_diagnosis": s.primary_diagnosis,
        "tissue_source_site": s.tss,
        "file_id": s.file_id,
        "size_gb": (s["size"] / 1e9).round(3),
        "has_xml": False,
        "exhaustive_annot": False,
        "file_format": "svs",
        "uses": s.uses,
        # download batches (docs/mvp.md): 1 = controller and unseen tissue, 2 = what only the lung head needs
        "batch": s.uses.map(lambda u: 2 if u == "nsclc" else 1),
    })
    return m.sort_values(["batch", "project_id", "center", "slide_id"]).reset_index(drop=True)


def build_manifest() -> pd.DataFrame:
    m = to_manifest(draw(files_table(fetch_files())))
    # Sanity checks on the design: counts per use, one slide per patient, every file with a checksum.
    uses = m.uses.str.split("+").explode().value_counts()
    assert uses["controller"] == 4 * 4 * 12 and uses["nsclc"] == 2 * 4 * 25 and uses["unseen"] == 24, uses
    assert m.patient_pseudo_id.is_unique and m.file_md5.str.fullmatch(r"[0-9a-f]{32}").all()
    return m


def slide_url(row) -> str:
    return f"{API}/data/{row.file_id}"


def annotation_url(row) -> str:
    raise ValueError("TCGA slides have no annotation files")
