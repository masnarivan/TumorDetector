"""Head spec and cohort: several datasets into one table of labels, domains, roles and folds."""
from pathlib import Path

import pandas as pd
import pytest
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf
from pydantic import ValidationError

from tumordetector import cli
from tumordetector.config import CONF_DIR, dataset_cfg
from tumordetector.heads.cohort import assemble, assign_folds, check_unchanged, cohort_path, embedding_roots
from tumordetector.heads.spec import HeadSpec
from tumordetector.io import write_json

ROOT = Path(__file__).resolve().parents[1]
SPEC = {"id": "ln", "version": 1, "module": "M4", "task": "binary", "sites": ["C77.3"],
        "datasets": ["d1", "d2"], "labels": {"negative": 0, "macro": 1}, "domain": ["dataset", "center"],
        "roles": {"external": {"center": ["z"]}}}


def rows(manifest_row, dataset, specs):
    """specs: (slide, patient, centre, diagnosis[, site])."""
    return pd.DataFrame([{**manifest_row, "dataset": dataset, "slide_id": s, "patient_pseudo_id": p, "center": c,
                          "reference_diagnosis": d, "site": site[0] if site else "C77.3"}
                         for s, p, c, d, *site in specs])


@pytest.fixture
def manifests(manifest_row):
    d1 = rows(manifest_row, "d1", [(f"a{i}", f"pa{i}", "x", ["negative", "macro"][i % 2]) for i in range(12)]
              + [("a_itc", "pa_itc", "x", "itc"), ("a_breast", "pa_b", "x", "negative", "C50.9")])
    d2 = rows(manifest_row, "d2", [(f"b{i}", f"pb{i // 2}", "x", ["negative", "macro"][i % 2]) for i in range(12)]
              + [(f"z{i}", f"pz{i}", "z", ["negative", "macro"][i % 2]) for i in range(4)])
    return {"d1": d1, "d2": d2}


def test_spec_refuses_what_it_cannot_mean():
    HeadSpec(**SPEC)
    with pytest.raises(ValidationError, match="extra"):
        HeadSpec(**SPEC, label={"negative": 0})                       # misspelt key
    with pytest.raises(ValidationError, match="0 and 1"):
        HeadSpec(**{**SPEC, "labels": {"negative": 0, "macro": 2}})
    with pytest.raises(ValidationError, match="ICD-O"):
        HeadSpec(**{**SPEC, "sites": ["lymph node"]})


def test_cohort_labels_domains_roles_and_says_why_it_left_slides_out(manifests):
    cohort, excluded = assemble(HeadSpec(**SPEC), manifests)
    assert len(cohort) == 28 and set(cohort.columns) >= {"label", "domain", "role"}
    assert dict(zip(excluded.slide_id, excluded.excluded_reason, strict=True)) == {
        "a_itc": "reference_diagnosis 'itc' not in the head's labels",
        "a_breast": "site C50.9 not in the head's sites ['C77.3']"}
    assert set(cohort.domain) == {"d1/x", "d2/x", "d2/z"}
    assert set(cohort[cohort.role == "external"].slide_id) == {"z0", "z1", "z2", "z3"}

    folded = assign_folds(cohort, 3, seed=0)
    assert (folded[folded.role == "external"].cv_fold == -1).all()
    dev = folded[folded.role == "dev"]
    assert sorted(dev.cv_fold.unique()) == [0, 1, 2]
    assert (dev.groupby("patient_pseudo_id").cv_fold.nunique() == 1).all()     # 2 slides per patient in d2
    assert (assign_folds(cohort, 3, seed=0).cv_fold == folded.cv_fold).all()


def test_cohort_refuses_ambiguous_data(manifests, manifest_row):
    spec = HeadSpec(**SPEC)
    clash = {**manifests, "d2": pd.concat([manifests["d2"], rows(manifest_row, "d2", [("a0", "q", "x", "negative")])])}
    with pytest.raises(ValueError, match="more than one dataset"):
        assemble(spec, clash)
    extra = rows(manifest_row, "d2", [("y", "pz0", "x", "negative")])       # patient pz0 is external (centre z)
    straddle = {**manifests, "d2": pd.concat([manifests["d2"], extra])}
    with pytest.raises(ValueError, match="both roles"):
        assemble(spec, straddle)


def test_a_saved_cohort_must_still_match_its_manifests(manifests):
    spec = HeadSpec(**SPEC)
    saved = assign_folds(assemble(spec, manifests)[0], 3, seed=0)
    check_unchanged(saved, spec, manifests)
    relabelled = {**manifests, "d1": manifests["d1"].assign(reference_diagnosis="negative")}
    with pytest.raises(SystemExit, match="changed"):
        check_unchanged(saved, spec, relabelled)


def test_embeddings_of_different_backbone_versions_are_never_mixed(tmp_path):
    for name, version in (("d1", "v1"), ("d2", "v2")):
        root = tmp_path / name / "embeddings/dummy"
        root.mkdir(parents=True)
        write_json(root / "collection.json",
                   {"backbone": "dummy", "version": version, "collection": f"dummy__{version}"})
    with pytest.raises(SystemExit, match="different backbone versions"):
        embedding_roots({"d1": tmp_path / "d1", "d2": tmp_path / "d2"}, "dummy")
    roots, ident = embedding_roots({"d1": tmp_path / "d1"}, "dummy")
    assert ident["version"] == "v1" and roots["d1"] == tmp_path / "d1/embeddings/dummy"


def test_cli_cohort_of_the_lymph_node_head(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)                          # dataset configs name their manifests from the repo root
    cli.main(["task=cohort", f"paths.heads={tmp_path}"])
    cohort = pd.read_csv(tmp_path / "ln_metastasis.csv")
    assert (cohort.role == "dev").sum() == 771 and set(cohort[cohort.role == "external"].center) == {"lpon"}
    assert set(pd.read_csv(tmp_path / "ln_metastasis_excluded.csv").reference_diagnosis) == {"itc"}
    pair = cohort.set_index("slide_id").loc[["test_116", "tumor_091"]]
    assert pair.patient_pseudo_id.nunique() == 1 and pair.cv_fold.nunique() == 1   # same patient (E3b)
    with pytest.raises(SystemExit, match="never rewritten implicitly"):
        cli.main(["task=cohort", f"paths.heads={tmp_path}"])


def test_the_versioned_cohorts_match_the_manifests(monkeypatch):
    monkeypatch.chdir(ROOT)
    for path in sorted((CONF_DIR / "head").glob("*.yaml")):
        with initialize_config_dir(str(CONF_DIR), version_base=None):
            cfg = compose("config", overrides=[f"head={path.stem}"])
        spec = HeadSpec(**OmegaConf.to_container(cfg.head, resolve=True))
        saved = cohort_path(Path(cfg.paths.heads), spec)
        assert saved.exists(), f"no cohort for head {spec.id}: run `td task=cohort head={spec.id}`"
        manifests = {n: pd.read_csv(dataset_cfg(n).manifest) for n in spec.datasets}
        check_unchanged(pd.read_csv(saved), spec, manifests)
