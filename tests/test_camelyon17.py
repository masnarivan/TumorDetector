import pandas as pd

from tumordetector.data.camelyon17 import to_manifest
from tumordetector.data.schema import validate_manifest


def stages() -> pd.DataFrame:
    rows = [("patient_000.zip", "pN0", 0), ("patient_000_node_0.tif", "negative", 0),
            ("patient_000_node_1.tif", "negative", 0),
            ("patient_041.zip", "pN1mi", 2), ("patient_041_node_0.tif", "micro", 2),
            ("patient_041_node_1.tif", "itc", 2), ("patient_041_node_2.tif", "negative", 2)]
    return pd.DataFrame(rows, columns=["patient", "stage", "center"])


def test_manifest_rows():
    ids = ["patient_000_node_0", "patient_000_node_1", "patient_041_node_0", "patient_041_node_1", "patient_041_node_2"]
    md5 = {f"images/{s}.tif": f"{i:032x}" for i, s in enumerate(ids)}
    m = to_manifest(stages(), {f"{s}.tif": 2e9 for s in ids}, {"patient_041_node_1.xml": 1}, md5).set_index("slide_id")
    assert list(m.index) == ids                                   # zip rows are patients, not slides
    assert m.patient_pseudo_id.nunique() == 2 and m.loc["patient_041_node_2", "patient_pseudo_id"] == "c17_patient_041"
    assert m.loc["patient_041_node_0", "patient_pn_stage"] == "pN1mi"
    assert m.loc["patient_041_node_0", "center"] == "utrecht"
    assert set(m.file_format) == {"generic_tiff"}                  # only LPON files are native Philips TIFFs
    assert m.label.tolist()[:3] == [0, 0, 1] and pd.isna(m.loc["patient_041_node_1", "label"])   # itc: no binary label
    # tile-level ground truth: negatives and annotated slides, not an unannotated positive
    assert m.exhaustive_annot.tolist() == [True, True, False, True, True]
    ok, blocked = validate_manifest(m.reset_index())
    assert len(ok) == 5 and blocked.empty
