"""End-to-end checks on a synthetic slide: tiling, QC, embedding, store, CLI stages."""
import shutil

import numpy as np
import openslide
import pandas as pd
import pytest
from omegaconf import OmegaConf

from conftest import MPP, TISSUE
from tumordetector import cli
from tumordetector.backbones.models import REGISTRY, build_backbone
from tumordetector.data.schema import validate_manifest
from tumordetector.embed import store
from tumordetector.embed.extract import TileDataset, extract
from tumordetector.io import md5sum
from tumordetector.qc.tissue import assess, compute_tissue_mask
from tumordetector.tasks import stream
from tumordetector.wsi.tiling import make_tile_grid, read_tile, slide_mpp

DUMMY = OmegaConf.create({"name": "dummy", "input_px": 224, "mpp": 0.5, "dim": 32, "seed": 0})


@pytest.fixture(scope="module")
def tiled(slide_path):
    slide = openslide.OpenSlide(slide_path)
    tissue = compute_tissue_mask(slide)
    return slide, tissue, make_tile_grid(slide, tissue)


def test_slide_opens_with_resolution(slide_path):
    slide = openslide.OpenSlide(slide_path)
    assert slide.level_count == 6
    assert slide_mpp(slide) == pytest.approx(MPP, rel=1e-3)


def test_grid_covers_the_tissue_and_nothing_else(tiled):
    slide, tissue, tiles = tiled
    x0, y0, x1, y1 = TISSUE
    step = 224 * 0.5 / MPP                       # tile side in level-0 px
    assert tiles.size_l0.iloc[0] == pytest.approx(step)
    # 448 px grid over a 4096 x 3072 px rectangle starting at 2048: 9 columns x 6 rows are >= 50% tissue.
    assert len(tiles) == 54
    cx, cy = tiles.x + step / 2, tiles.y + step / 2
    assert ((cx > x0) & (cx < x1) & (cy > y0) & (cy < y1)).all()
    assert read_tile(slide, tiles.iloc[0]).size == (224, 224)


def test_qc_passes_tissue_and_refers_an_empty_slide(tiled):
    _, tissue, tiles = tiled
    x0, y0, x1, y1 = TISSUE
    qc = assess("s", tissue, MPP, len(tiles), min_tiles=50, min_tissue_mm2=0.5)
    assert qc.status == "pass" and qc.reason == ""
    assert qc.tissue_mm2 == pytest.approx((x1 - x0) * (y1 - y0) * (MPP / 1000) ** 2, rel=0.05)
    empty = assess("s", tissue, MPP, 3, min_tiles=50, min_tissue_mm2=0.5)
    assert empty.status == "refer" and "3 tiles" in empty.reason


def test_extraction_is_deterministic(slide_path, tiled):
    _, _, tiles = tiled
    backbone = build_backbone(DUMMY)
    backbone.load("cpu")
    runs = [extract(backbone, TileDataset(slide_path, tiles, backbone.transform), batch_size=16, n_threads=t)[0]
            for t in (1, 4)]
    assert runs[0].shape == (len(tiles), 32)
    assert np.array_equal(runs[0], runs[1])     # thread count and batch arrival order do not matter


def test_registry_has_the_configured_backbones():
    assert set(REGISTRY) == {"dummy", "phikon", "h_optimus_0"}
    with pytest.raises(KeyError):
        build_backbone(OmegaConf.create({"name": "nope"}))


def test_store_roundtrip_and_no_version_mixing(tmp_path, tiled):
    _, _, tiles = tiled
    backbone = build_backbone(DUMMY)
    backbone.load("cpu")
    feats = np.random.default_rng(0).normal(size=(len(tiles), 32)).astype(np.float32)
    ident = store.open_collection(tmp_path, backbone)
    meta = store.write_slide(tmp_path, "s", feats, tiles, {**ident, "file_md5": "x"})
    got = store.read_slide(tmp_path, "s")
    assert got.features.dtype == np.float16 and got.features.shape == feats.shape
    assert got.meta["embedding_sha256"] == meta["embedding_sha256"]
    assert got.tiles.equals(tiles)
    assert store.list_slides(tmp_path) == ["s"]

    backbone.version = "seed1"
    with pytest.raises(RuntimeError, match="never mixed"):
        store.open_collection(tmp_path, backbone)


def test_manifest_blocks_incomplete_rows(manifest_row):
    bad_site = {**manifest_row, "slide_id": "b", "site": "lymph node"}
    no_center = {**manifest_row, "slide_id": "c", "center": None}
    ok, blocked = validate_manifest(pd.DataFrame([manifest_row, bad_site, no_center]))
    assert list(ok.slide_id) == ["synthetic"]
    assert list(blocked.slide_id) == ["b", "c"]
    assert "site" in blocked.blocked_reason.iloc[0] and "center" in blocked.blocked_reason.iloc[1]

    _, dup = validate_manifest(pd.DataFrame([manifest_row, manifest_row]))
    assert len(dup) == 2 and "duplicated" in dup.blocked_reason.iloc[0]


def test_cli_tile_then_embed_is_resumable(tmp_path, slide_path, manifest, monkeypatch):
    raw = slide_path.parent
    manifest = manifest.assign(file_md5=md5sum(slide_path), label=0)
    manifest.to_csv(tmp_path / "manifest.csv", index=False)
    monkeypatch.chdir(tmp_path)
    common = ["backbone=dummy", f"data.manifest={tmp_path / 'manifest.csv'}", f"data.raw_dir={raw}",
              "data.slides=null", f"paths.out={tmp_path / 'out'}", "embed.device=cpu",
              f"mlflow.tracking_uri=sqlite:///{tmp_path / 'mlflow.db'}"]

    root = tmp_path / "out/embeddings/dummy"
    cli.main(["task=tile", *common])            # 0.79 mm2 of tissue: below the default QC threshold
    cli.main(["task=embed", *common])
    assert pd.read_csv(root / "extract_log.csv").status.iloc[0].startswith("referred by QC")
    assert not store.is_done(root, "synthetic")

    common += ["qc.min_tissue_mm2=0.5", "qc.min_tiles=10"]
    cli.main(["task=tile", *common])
    qc = pd.read_csv(tmp_path / "out/qc/summary.csv")
    assert list(qc.status) == ["pass"]
    tiles = pd.read_parquet(tmp_path / "out/tiles/synthetic.parquet")
    assert (tiles.label == "normal").all()

    cli.main(["task=embed", *common])
    first = store.read_slide(root, "synthetic")
    assert first.features.shape == (len(tiles), 32)
    assert first.meta["file_md5"] == manifest.file_md5.iloc[0]
    assert list(pd.read_csv(root / "extract_log.csv").status) == ["embedded"]

    cli.main(["task=embed", *common])           # same tiles, same file -> nothing recomputed
    assert list(pd.read_csv(root / "extract_log.csv").status) == ["cached"]

    cli.main(["task=tile", *common, "tiling.min_tissue=0.99"])   # different grid -> re-embedded
    cli.main(["task=embed", *common])
    assert list(pd.read_csv(root / "extract_log.csv").status) == ["embedded"]


def test_cli_refuses_a_tiling_the_backbone_was_not_trained_on(tmp_path, manifest, monkeypatch):
    manifest.to_csv(tmp_path / "manifest.csv", index=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="does not match"):
        cli.main(["task=embed", "backbone=dummy", f"data.manifest={tmp_path / 'manifest.csv'}",
                  f"paths.out={tmp_path / 'out'}", "tiling.tile_px=256"])


def test_cli_stream_deletes_only_what_it_downloaded(tmp_path, slide_path, manifest, monkeypatch):
    manifest = manifest.assign(file_md5=md5sum(slide_path), label=0, has_xml=False)
    manifest = pd.concat([manifest, manifest.assign(slide_id="already_here")])
    manifest.to_csv(tmp_path / "manifest.csv", index=False)
    raw = tmp_path / "raw"
    raw.mkdir()
    shutil.copy(slide_path, raw / "already_here.tif")

    def fake_download(cfg, row, raw):
        tif = raw / f"{row.slide_id}.tif"
        fresh = not tif.exists()
        if fresh:
            shutil.copy(slide_path, tif)
        return tif, fresh

    monkeypatch.setattr(stream, "download", fake_download)
    monkeypatch.chdir(tmp_path)
    args = ["task=stream", "backbone=dummy", f"data.manifest={tmp_path / 'manifest.csv'}", f"data.raw_dir={raw}",
            "data.slides=null", f"paths.out={tmp_path / 'out'}", "embed.device=cpu", "qc.min_tissue_mm2=0.5",
            f"mlflow.tracking_uri=sqlite:///{tmp_path / 'mlflow.db'}"]
    cli.main(args)
    root = tmp_path / "out/embeddings/dummy"
    assert store.list_slides(root) == ["already_here", "synthetic"]
    assert not (raw / "synthetic.tif").exists()          # downloaded by the run -> removed
    assert (raw / "already_here.tif").exists()           # was there before -> untouched

    cli.main(args)                                       # everything current: nothing to download
    assert len(pd.read_csv(root / "extract_log.csv")) == 0


def test_cli_stream_does_not_fetch_a_referred_slide_again(tmp_path, slide_path, manifest, monkeypatch):
    manifest.assign(file_md5=md5sum(slide_path), label=0, has_xml=False).to_csv(tmp_path / "manifest.csv", index=False)
    fetched = []

    def fake_download(cfg, row, raw):
        fetched.append(row.slide_id)
        shutil.copy(slide_path, raw / f"{row.slide_id}.tif")
        return raw / f"{row.slide_id}.tif", True

    monkeypatch.setattr(stream, "download", fake_download)
    monkeypatch.chdir(tmp_path)
    args = ["task=stream", "backbone=dummy", f"data.manifest={tmp_path / 'manifest.csv'}",
            f"data.raw_dir={tmp_path / 'raw'}", "data.slides=null", f"paths.out={tmp_path / 'out'}",
            "embed.device=cpu", f"mlflow.tracking_uri=sqlite:///{tmp_path / 'mlflow.db'}"]
    cli.main([*args, "qc.min_tissue_mm2=1000"])            # referred
    cli.main([*args, "qc.min_tissue_mm2=1000"])            # same verdict on record: not fetched again
    assert fetched == ["synthetic"]
    cli.main([*args, "qc.min_tissue_mm2=0.5"])             # thresholds changed: the verdict is redone
    assert fetched == ["synthetic", "synthetic"]
    assert store.list_slides(tmp_path / "out/embeddings/dummy") == ["synthetic"]


def test_vectordb_upsert_is_idempotent_and_search_finds_itself(tiled):
    from qdrant_client import QdrantClient

    from tumordetector.vectordb import qdrant

    client = QdrantClient(":memory:")             # the same API as the server, in process
    _, _, tiles = tiled
    feats = np.random.default_rng(0).normal(size=(len(tiles), 32)).astype(np.float32)
    ident = {"collection": "pytest__tmp", "backbone": "pytest", "version": "tmp", "dim": 32}
    name = qdrant.ensure_collection(client, ident)
    level = np.where(np.arange(len(tiles)) < 3, "region", "prototype")
    payload = lambda sid: pd.DataFrame({"slide_id": sid, "level": level, "idx": np.arange(len(tiles)),  # noqa: E731
                                        "label": np.where(np.arange(len(tiles)) == 7, "tumor", None)})
    for _ in range(2):
        assert qdrant.upsert_slide(client, name, "s1", feats, payload("s1"), batch=5) == len(tiles)
    qdrant.upsert_slide(client, name, "s2", feats + 0.01, payload("s2"))
    assert qdrant.count(client, name) == 2 * len(tiles)
    assert qdrant.counts(client, name) == {"s1": len(tiles), "s2": len(tiles)}
    assert client.count(qdrant.names(name)["region"]).count == 2 * 3
    hit = qdrant.search(client, name, feats[7], "prototype", k=1)
    assert (hit.slide_id[0], hit.idx[0], hit.label[0]) == ("s1", 7, "tumor")
    assert hit.distance[0] == pytest.approx(0, abs=1e-3)       # float16 vectors
    assert set(qdrant.search(client, name, feats[7], "prototype", k=3, exclude_slide="s1").slide_id) == {"s2"}
    assert 7 not in set(qdrant.search(client, name, feats[7], "region", k=10).idx)    # levels apart
    with pytest.raises(RuntimeError, match="rebuild"):                    # same collection, other dim
        qdrant.ensure_collection(client, {**ident, "dim": 16})
    qdrant.ensure_collection(client, ident, rebuild=True)
    assert qdrant.count(client, name) == 0
