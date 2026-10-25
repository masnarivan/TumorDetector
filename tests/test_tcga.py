import pandas as pd
import pytest

from tumordetector.data import tcga
from tumordetector.data.schema import validate_manifest

SITES = sorted(set(tcga.CONTROLLER["sites"]) | set(tcga.NSCLC["sites"]))


def hit(i: int, project: str, site: str, block: str = "DX1", file_id: str | None = None) -> dict:
    patient = f"TCGA-{project[5:7]}-{site[:2].upper()}{i:04d}"
    return {"file_id": file_id or f"{patient}-{block}", "file_name": f"{patient}-01Z-00-{block}.{i:08x}.svs",
            "file_size": 5e8, "md5sum": f"{i:032x}",
            "cases": [{"submitter_id": patient, "project": {"project_id": project},
                       "tissue_source_site": {"name": site}, "diagnoses": [{"primary_diagnosis": "x"}]}]}


def gdc_hits(n: int = 30) -> list[dict]:
    hits, i = [], 0
    for project in sorted(tcga.PROJECTS):
        for site in SITES:
            for _ in range(n):
                hits.append(hit(i, project, site))
                hits.append(hit(i, project, site, block="DX2"))          # another block of the same patient
                i += 1
    hits.append(hit(0, "TCGA-BRCA", SITES[0], file_id="zz-rescan"))   # the same DX1 in a second file
    return hits


def test_one_dx1_slide_per_patient():
    t = tcga.files_table(gdc_hits())
    assert t.file_name.str.contains("-DX1.").all() and t.patient.is_unique


def test_draw_follows_the_design():
    m = tcga.to_manifest(tcga.draw(tcga.files_table(gdc_hits())))
    uses = m.uses.str.split("+").explode()
    assert (uses == "controller").sum() == 192 and (uses == "nsclc").sum() == 200 and (uses == "unseen").sum() == 24
    ctrl = m[m.uses.str.contains("controller")]
    assert (ctrl.groupby(["project_id", "tissue_source_site"]).size() == 12).all()
    assert set(ctrl.tissue_source_site) == set(tcga.CONTROLLER["sites"])        # the site does not tell the organ
    nsclc = m[m.uses.str.contains("nsclc")]
    assert (nsclc.groupby(["project_id", "tissue_source_site"]).size() == 25).all()
    # Lung adenocarcinoma of a site in both designs: the controller's 12 are among the head's 25.
    shared = set(tcga.CONTROLLER["sites"]) & set(tcga.NSCLC["sites"])
    both = m[(m.project_id == "TCGA-LUAD") & m.tissue_source_site.isin(shared)]
    assert both.uses.str.contains("controller").sum() == 12 * len(shared)
    assert both.uses.str.contains("nsclc").all()
    assert set(m.batch[m.uses == "nsclc"]) == {2} and set(m.batch[m.uses != "nsclc"]) == {1}
    assert m.loc[m.project_id == "TCGA-LUSC", "site"].eq("C34.9").all()
    assert m.center.str.fullmatch(r"[a-z0-9_]+").all()
    ok, blocked = validate_manifest(m)
    assert len(ok) == len(m) and blocked.empty


def test_draw_is_fixed_by_the_seed_not_by_the_api_order():
    hits = gdc_hits()
    a = tcga.draw(tcga.files_table(hits)).file_id
    b = tcga.draw(tcga.files_table(hits[::-1])).file_id
    assert sorted(a) == sorted(b)
    assert sorted(tcga.draw(tcga.files_table(hits), seed=1).file_id) != sorted(a)


def test_draw_refuses_a_site_with_too_few_patients():
    with pytest.raises(ValueError, match="nsclc"):
        tcga.draw(tcga.files_table(gdc_hits(n=20)))


def test_slide_url_uses_the_gdc_file_id():
    row = pd.Series({"slide_id": "TCGA-XX", "file_id": "abc"})
    assert tcga.slide_url(row) == "https://api.gdc.cancer.gov/data/abc"
