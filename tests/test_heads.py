"""Head spec and cohort: several datasets into one table of labels, domains, roles and folds."""
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import pytest
import torch
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf
from pydantic import ValidationError

from tumordetector import cli
from tumordetector.config import CONF_DIR, dataset_cfg
from tumordetector.embed import store
from tumordetector.heads.cohort import assemble, assign_folds, check_unchanged, cohort_path, embedding_roots
from tumordetector.heads.mitigations import GroupDRO, StatMix, balanced_weights, fit_recipe
from tumordetector.heads.protocol import (
    center_probe,
    fit_temperature,
    head_gate,
    robustness_index,
    run_head_protocol,
    sigmoid,
)
from tumordetector.heads.spec import HeadSpec
from tumordetector.io import read_json, write_json
from tumordetector.mil.evaluate import across_seeds

ROOT = Path(__file__).resolve().parents[1]
SPEC = {"id": "ln", "version": 1, "module": "M4", "task": "binary", "sites": ["C77.3"],
        "datasets": ["d1", "d2"], "labels": {"negative": 0, "macro": 1}, "domain": ["dataset", "center"],
        "roles": {"external": {"center": ["z"]}},
        "gate": {"min_slides": 20, "min_cv_auroc": 0.9, "min_loco_worst_auroc": 0.85, "max_ece": 0.5,
                 "max_loco_ece": 0.5, "min_loco_specificity": 0.5, "max_center_probe_auroc": 1.0,
                 "min_robustness_index": 0.0}}


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
    assert set(cohort.domain) == {"d1:x", "d2:x", "d2:z"}
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


# --- training on a head's cohort -------------------------------------------------------------------

DIM = 16
MIL = OmegaConf.create({"hidden": 32, "dropout": 0.0, "lr": 2e-3, "weight_decay": 0.0, "epochs": 8,
                        "max_tiles": 256, "threshold": 0.5, "device": "cpu", "normalize": "none", "threads": 1})


def synthetic_cohort(manifest_row, n_per_center: int = 12, seed: int = 0):
    """Two datasets, four development centres and one external; each centre shifts every tile along
    its own axis (the centre is readable, as in E2), a positive slide has ~10% tumour tiles."""
    rng = np.random.default_rng(seed)
    centers = {"a": "d1", "b": "d1", "c": "d2", "d": "d2", "z": "d2"}
    rows, bags, labels = [], {}, {}
    for ci, (c, ds) in enumerate(centers.items()):
        for i in range(n_per_center):
            sid, y = f"{c}{i:02d}", i % 2
            x = rng.normal(size=(rng.integers(40, 100), DIM)).astype(np.float32)
            x[:, 1 + ci] += 1.5
            tumor = np.zeros(len(x), dtype=bool)
            if y:
                tumor[rng.choice(len(x), max(len(x) // 10, 3), replace=False)] = True
                x[tumor, 0] += 4.0
            bags[sid], labels[sid] = x, np.where(tumor, "tumor", "normal")
            rows.append({**manifest_row, "slide_id": sid, "dataset": ds, "center": c, "patient_pseudo_id": f"p{sid}",
                         "reference_diagnosis": ["negative", "macro"][y], "label": y, "exhaustive_annot": True})
    return pd.DataFrame(rows), bags, labels


def test_temperature_recovers_the_scale_of_overconfident_logits():
    rng = np.random.default_rng(0)
    logits = rng.normal(0, 6, 20000)
    y = rng.random(len(logits)) < sigmoid(logits / 3.0)
    assert fit_temperature(logits, y) == pytest.approx(3.0, rel=0.08)


def test_center_probe_and_robustness_index_see_a_centre_effect():
    rng = np.random.default_rng(0)
    center = np.repeat(np.array(["a", "b", "c"]), 40)
    patient = np.arange(len(center)).astype(str)
    noise = rng.normal(size=(len(center), 8))
    shifted = noise + (center[:, None] == np.array(["a", "b", "c"])) @ np.eye(3, 8) * 3
    assert center_probe(shifted, center, patient, seed=0) > 0.95
    assert 0.3 < center_probe(noise, center, patient, seed=0) < 0.7
    # tiles cluster by class only: every neighbour has the same class, from any centre -> RI >> 1
    tumor = np.tile([True, False], 60)
    h = noise + tumor[:, None] * 10
    biology = robustness_index(h, tumor, np.arange(len(h)) // 4, center)
    assert biology["ri"] > 10
    # tiles cluster by centre only -> RI < 1
    by_center = robustness_index(shifted * 5, tumor, np.arange(len(h)) // 4, center)
    assert by_center["ri"] < 1 and by_center["same_center_fraction"] > 0.9


def test_head_protocol_runs_loco_on_every_centre_and_calibrates_without_it(manifest_row):
    manifest, bags, labels = synthetic_cohort(manifest_row)
    spec = HeadSpec(**{**SPEC, "datasets": ["d1", "d2"]})
    cohort, _ = assemble(spec, {d: manifest[manifest.dataset == d] for d in ("d1", "d2")})
    table = assign_folds(cohort, 3, seed=0).merge(manifest[["slide_id", "exhaustive_annot"]], on="slide_id")
    with pytest.raises(ValueError, match="external"):
        run_head_protocol(table, bags, labels.get, MIL, seed=0, inner_folds=2)
    dev = table[table.role == "dev"].reset_index(drop=True)
    out = run_head_protocol(dev, bags, labels.get, MIL, seed=0, inner_folds=2)
    m = out["metrics"]
    assert set(m["loco"]) == {f"held-out {c}" for c in "abcd"} and "z" not in set(out["predictions"].center)
    assert set(m["temperature"]) == {"global", *m["loco"]} and all(t > 0 for t in m["temperature"].values())
    assert m["cv"]["auroc"] > 0.9 and m["loco_worst_auroc"] is not None
    assert m["cv"]["auroc"] == m["cv_raw"]["auroc"]                      # a temperature never reorders
    loco = out["predictions"][out["predictions"].group == "loco"]
    assert ((loco.p >= 0.5) == (loco.p_raw >= 0.5)).all()               # nor moves the 0.5 decision
    mean, _ = across_seeds([m, m])                                      # domain keys survive the averaging
    assert mean["loco_by_domain"]["held-out a"]["d1:a"]["n"] == m["loco_by_domain"]["held-out a"]["d1:a"]["n"] > 0
    rob = m["robustness"]
    assert rob["center_probe_auroc"] > 0.8 and rob["robustness_index"] is not None
    assert (pd.DataFrame(out["runs"]).group == "loco-calibration").sum() == 8   # 4 centres x 2 inner folds
    verdict = head_gate(m, len(dev), HeadSpec(**SPEC).gate)
    assert verdict["status"] in ("passed", "failed") and all(isinstance(r, str) for r in verdict["reasons"])


def test_cli_train_head_reads_the_cohort_and_never_the_external_slides(tmp_path, monkeypatch, manifest_row):
    manifest, bags, labels = synthetic_cohort(manifest_row, n_per_center=10)
    cfgs = {}
    for ds in ("d1", "d2"):
        manifest[manifest.dataset == ds].to_csv(tmp_path / f"{ds}.csv", index=False)
        root = tmp_path / ds / "embeddings/dummy"
        root.mkdir(parents=True)
        ident = {"backbone": "dummy", "version": "seed0", "dim": DIM, "collection": "dummy__seed0"}
        write_json(root / "collection.json", ident)
        for sid in manifest[manifest.dataset == ds].slide_id:
            if sid != "c00":                                   # one slide not extracted yet
                store.write_slide(root, sid, bags[sid], pd.DataFrame({"label": labels[sid]}), ident)
        cfgs[ds] = OmegaConf.create({"manifest": str(tmp_path / f"{ds}.csv"), "out": str(tmp_path / ds)})
    for module in ("tumordetector.tasks.cohort", "tumordetector.tasks.train_head"):
        monkeypatch.setattr(f"{module}.dataset_cfg", cfgs.__getitem__)
    loaded = []
    real_load = np.load
    monkeypatch.setattr(np, "load", lambda p, *a, **k: loaded.append(Path(p).stem) or real_load(p, *a, **k))

    monkeypatch.chdir(tmp_path)
    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    head = ["head.datasets=[d1,d2]", "head.roles.external.center=[z]", "head.calibration.inner_folds=2",
            f"paths.heads={tmp_path / 'heads'}"]
    cli.main(["task=cohort", *head, "mil.folds=3"])
    cli.main(["task=train_head", "backbone=dummy", *head, f"paths.out={tmp_path / 'out'}", f"mlflow.tracking_uri={uri}",
              "mil.epochs=6", "mil.hidden=32", "mil.lr=0.002", "mil.seeds=[0]", "mil.workers=1"])

    assert not [s for s in loaded if s.startswith("z")]           # the locked external test is never read
    rep = tmp_path / "out/reports/dummy/heads/ln_metastasis"
    text = (rep / "report.md").read_text()
    assert "DATI INSUFFICIENTI" in text and "held-out d" in text and "Robustness Index" in text
    assert pd.read_csv(rep / "excluded.csv").slide_id.tolist() == ["c00"]
    assert read_json(rep / "calibration.json")["temperature"] > 0
    client = mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)
    version = client.get_model_version_by_alias("head-ln_metastasis-dummy", "candidate")
    assert version.tags["head_version"] == "1" and float(version.tags["temperature"]) > 0

    # a relabelled manifest no longer matches the cohort: training refuses
    manifest.assign(reference_diagnosis="negative").pipe(lambda m: m[m.dataset == "d1"]).to_csv(
        tmp_path / "d1.csv", index=False)
    with pytest.raises(SystemExit, match="no longer matches"):
        cli.main(["task=train_head", "backbone=dummy", *head, f"paths.out={tmp_path / 'out'}"])


# --- mitigations (experiment E7) -------------------------------------------------------------------

def test_balanced_weights_give_every_domain_and_class_the_same_total():
    domains = np.array(["a"] * 4 + ["b"] * 6)
    labels = np.array([0, 0, 0, 1, 0, 0, 1, 1, 1, 1])
    w = balanced_weights(labels, domains)
    assert w.mean() == pytest.approx(1.0)
    totals = pd.Series(w).groupby([domains, labels]).sum()
    assert np.allclose(totals, totals.iloc[0])


def test_group_dro_raises_the_weight_of_the_domain_that_loses_more():
    dro = GroupDRO(np.array(["a", "b"]), eta=0.5)
    for _ in range(5):
        dro.scale(torch.tensor(2.0), "a")
        dro.scale(torch.tensor(0.1), "b")
    assert dro.q[dro.index["a"]] > dro.q[dro.index["b"]]
    assert float(dro.scale(torch.tensor(1.0), "a")) > 1.0     # the worse domain's step counts more


class _Rng:
    """Stands in for numpy's generator: always mixes, always the first other slide, lambda = 0."""
    def random(self):
        return 0.0

    def choice(self, a):
        return a[0]

    def beta(self, a, b):
        return 0.0


def test_stat_mix_gives_a_slide_the_statistics_of_another_domain():
    rng = np.random.default_rng(0)
    bags = [rng.normal(0, 1, (200, 4)).astype(np.float32), rng.normal(5, 3, (300, 4)).astype(np.float32),
            rng.normal(0, 1, (100, 4)).astype(np.float32)]
    mix = StatMix(bags, np.array(["a", "b", "a"]), _Rng(), p=1.0)
    out = mix(torch.from_numpy(bags[0]), 0).numpy()                 # lambda 0: entirely slide 1's statistics
    assert np.allclose(out.mean(0), bags[1].mean(0), atol=1e-3)
    assert np.allclose(out.std(0), bags[1].std(0), rtol=1e-2)
    alone = StatMix(bags[:1], np.array(["a"]), _Rng(), p=1.0)       # no other domain: unchanged
    assert torch.equal(alone(torch.from_numpy(bags[0]), 0), torch.from_numpy(bags[0]))


def test_recipes_are_checked_and_every_one_still_learns(manifest_row):
    with pytest.raises(ValidationError):
        HeadSpec(**{**SPEC, "recipe": ["dann"]})
    with pytest.raises(ValueError, match="non-empty"):
        fit_recipe([np.zeros((4, DIM))], np.array([0]), np.array(["a"]), MIL, 0, [])
    manifest, bags, labels = synthetic_cohort(manifest_row)
    spec = HeadSpec(**{**SPEC, "datasets": ["d1", "d2"], "recipe": ["balanced", "group_dro", "stat_mix"]})
    cohort, _ = assemble(spec, {d: manifest[manifest.dataset == d] for d in ("d1", "d2")})
    table = assign_folds(cohort, 3, seed=0).merge(manifest[["slide_id", "exhaustive_annot"]], on="slide_id")
    dev = table[table.role == "dev"].reset_index(drop=True)
    for recipe in (["balanced"], ["balanced", "group_dro"], ["balanced", "stat_mix"]):
        out = run_head_protocol(dev, bags, labels.get, MIL, seed=0, inner_folds=2, recipe=recipe)
        assert out["metrics"]["cv"]["auroc"] > 0.9, recipe
    plain = run_head_protocol(dev, bags, labels.get, MIL, seed=0, inner_folds=2)
    # every domain here has as many negatives as positives: balancing changes nothing, mixing does
    same = run_head_protocol(dev, bags, labels.get, MIL, seed=0, inner_folds=2, recipe=["balanced"])
    mixed = run_head_protocol(dev, bags, labels.get, MIL, seed=0, inner_folds=2, recipe=["balanced", "stat_mix"])
    assert np.allclose(plain["predictions"].logit, same["predictions"].logit, atol=1e-4)
    assert not np.allclose(plain["predictions"].logit, mixed["predictions"].logit)
