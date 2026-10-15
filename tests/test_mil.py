"""ABMIL baseline and validation protocol on synthetic bags with a planted signal."""
import mlflow
import numpy as np
import pandas as pd
import pytest
from omegaconf import OmegaConf

from tumordetector import cli
from tumordetector.embed import store
from tumordetector.mil.abmil import ABMIL
from tumordetector.mil.evaluate import binary_metrics, ece, gate, make_cv_folds, run_protocol

DIM = 16
MIL = OmegaConf.create({"hidden": 32, "dropout": 0.0, "lr": 2e-3, "weight_decay": 0.0, "epochs": 12,
                        "max_tiles": 256, "threshold": 0.5, "folds": 4, "device": "cpu", "normalize": "none"})
GATE = OmegaConf.create({"min_slides": 20, "min_cv_auroc": 0.9, "min_loco_worst_auroc": 0.85,
                         "min_test_auroc": 0.9, "max_ece": 0.5})


def synthetic(n: int = 64, seed: int = 0):
    """Slides of 40-120 tiles; in a positive slide ~10% of the tiles are shifted along one axis."""
    rng = np.random.default_rng(seed)
    rows, bags, labels = [], {}, {}
    for i in range(n):
        sid, y = f"s{i:03d}", i % 2
        x = rng.normal(size=(rng.integers(40, 120), DIM)).astype(np.float32)
        tumor = np.zeros(len(x), dtype=bool)
        if y:
            tumor[rng.choice(len(x), max(len(x) // 10, 3), replace=False)] = True
            x[tumor, 0] += 4.0
        bags[sid], labels[sid] = x.astype(np.float16), np.where(tumor, "tumor", "normal")
        rows.append({"slide_id": sid, "label": y, "center": "a" if (i // 2) % 2 else "b",
                     "split": "test" if i >= n - 16 else "train", "patient_pseudo_id": f"p{i}",
                     "exhaustive_annot": True})
    table = pd.DataFrame(rows)
    return table.merge(make_cv_folds(table, MIL.folds, seed=0), on="slide_id"), bags, labels


def test_folds_are_stable_stratified_and_keep_the_test_split_out():
    table, _, _ = synthetic()
    again = make_cv_folds(table.drop(columns="cv_fold"), MIL.folds, seed=0)
    assert (again.cv_fold.to_numpy() == table.cv_fold.to_numpy()).all()
    assert (table[table.split == "test"].cv_fold == -1).all()
    dev = table[table.split == "train"]
    assert sorted(dev.cv_fold.unique()) == [0, 1, 2, 3]
    assert (dev.groupby("cv_fold").label.nunique() == 2).all() and (dev.groupby("cv_fold").center.nunique() == 2).all()


def test_calibration_and_metrics():
    assert ece(np.array([0, 1]), np.array([0.0, 1.0])) == 0
    assert ece(np.array([0, 0]), np.array([1.0, 1.0])) == 1
    m = binary_metrics([0, 0, 1, 1], [0.1, 0.6, 0.4, 0.9])
    assert (m["auroc"], m["sensitivity"], m["specificity"]) == (0.75, 0.5, 0.5)
    assert binary_metrics([1, 1], [0.9, 0.8])["auroc"] is None     # one class: undefined, not 0 or 1


def test_protocol_learns_the_planted_signal_and_passes_the_gate():
    table, bags, labels = synthetic()
    result = run_protocol(table, bags, labels.__getitem__, MIL, seed=0)
    m = result["metrics"]
    assert m["cv"]["n"] == 48 and m["test"]["n"] == 16
    assert m["cv"]["auroc"] > 0.95 and m["test"]["auroc"] > 0.95 and m["loco_worst_auroc"] > 0.9
    assert set(m["loco"]) == {"held-out a", "held-out b"}
    assert m["attention_auroc_mean"] > 0.85                       # attention finds the shifted tiles
    assert all(r["status"] == "ok" for r in result["runs"])
    assert gate(m, result["n_slides"], GATE) == {"status": "passed", "reasons": []}

    strict = OmegaConf.merge(GATE, {"max_ece": 0.0})
    verdict = gate(m, result["n_slides"], strict)
    assert verdict["status"] == "failed" and "ECE" in verdict["reasons"][0]


def test_slide_mean_normalisation_ignores_what_every_tile_shares():
    torch = pytest.importorskip("torch")
    x = torch.randn(50, DIM)
    shift = 3 * torch.randn(1, DIM)                       # a centre: the same offset on every tile
    norm, raw = ABMIL(DIM, 32, 0.0, "slide_mean").eval(), ABMIL(DIM, 32, 0.0).eval()
    assert torch.allclose(norm(x)[0], norm(x + shift)[0], atol=1e-5)
    assert not torch.allclose(raw(x)[0], raw(x + shift)[0], atol=1e-3)
    with pytest.raises(ValueError):
        ABMIL(DIM, normalize="centre")


def test_protocol_learns_the_planted_signal_with_slide_mean_normalisation():
    table, bags, labels = synthetic()
    result = run_protocol(table, bags, labels.__getitem__, OmegaConf.merge(MIL, {"normalize": "slide_mean"}), seed=0)
    assert result["metrics"]["test"]["auroc"] > 0.95


def test_protocol_reports_what_it_cannot_run():
    table, bags, labels = synthetic()
    few = table[(table.split == "train") & (table.label == 1)].head(4)   # one class, no test split
    result = run_protocol(few, bags, labels.__getitem__, MIL, seed=0)
    assert {r["status"] for r in result["runs"]} == {"skipped"}
    assert all(r["reason"] for r in result["runs"])
    assert result["model"] is None and result["metrics"]["loco_worst_auroc"] is None
    assert gate(result["metrics"], result["n_slides"], GATE)["status"] == "insufficient_data"


def test_cli_train_writes_report_and_registers_a_candidate(tmp_path, monkeypatch, manifest_row):
    table, bags, labels = synthetic(40)
    manifest = pd.DataFrame([{**manifest_row, **r} for r in table.drop(columns="cv_fold").to_dict("records")])
    manifest.to_csv(tmp_path / "manifest.csv", index=False)
    root = tmp_path / "out/embeddings/dummy"
    root.mkdir(parents=True)
    ident = {"backbone": "dummy", "version": "seed0", "dim": DIM, "collection": "dummy__seed0"}
    cli.write_json(root / "collection.json", ident)
    for sid, x in bags.items():
        store.write_slide(root, sid, x, pd.DataFrame({"label": labels[sid]}), ident)

    monkeypatch.chdir(tmp_path)
    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    common = ["backbone=dummy", f"data.manifest={tmp_path / 'manifest.csv'}", f"paths.out={tmp_path / 'out'}",
              f"mlflow.tracking_uri={uri}", "mil.epochs=8", "mil.hidden=32", "mil.lr=0.002", "mil.folds=3",
              "gate.min_slides=1000"]
    cli.main(["task=splits", *common])
    with pytest.raises(SystemExit, match="never regenerated implicitly"):
        cli.main(["task=splits", *common])
    cli.main(["task=train", *common])

    rep = tmp_path / "out/reports/dummy/abmil"
    text = (rep / "report.md").read_text()
    assert "DATI INSUFFICIENTI" in text and "dummy__seed0" in text
    assert cli.read_json(rep / "metrics.json")["gate"]["status"] == "insufficient_data"
    assert len(pd.read_csv(rep / "predictions.csv")) > 0

    client = mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)
    version = client.get_model_version_by_alias("abmil-camelyon16-dummy", "candidate")
    assert version.tags["validation_status"] == "insufficient_data"
    with pytest.raises(mlflow.exceptions.MlflowException):          # not validated: the alias does not exist
        client.get_model_version_by_alias("abmil-camelyon16-dummy", "validated")

    # an experiment run: its own report folder, nothing added to the registry
    cli.main(["task=train", *common, "mil.register=false", "mil.normalize=slide_mean",
              f"mil.report_dir={tmp_path / 'exp'}"])
    assert (tmp_path / "exp/report.md").exists() and "slide_mean" in (tmp_path / "exp/report.md").read_text()
    assert len(client.search_model_versions("name='abmil-camelyon16-dummy'")) == 1
