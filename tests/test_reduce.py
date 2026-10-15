import numpy as np
import pandas as pd

from tumordetector.vectordb import reduce


def test_kcenter_keeps_a_rare_cluster_and_covers_every_tile():
    rng = np.random.default_rng(0)
    common = rng.normal([5, 0, 0], 0.1, size=(990, 3))
    rare = rng.normal([0, 5, 0], 0.1, size=(10, 3))       # e.g. a few tumour tiles
    p = reduce.kcenter(np.vstack([common, rare]), 8)
    assert len(p.tiles) == 8 and len(set(p.tiles)) == 8
    assert (p.tiles >= 990).any(), "the rare cluster has a prototype"
    assert p.represented.sum() == 1000
    z = reduce.unit(np.vstack([common, rare]))
    d = np.linalg.norm(z[:, None] - z[p.tiles][None], axis=2).min(1)
    assert np.isclose(d.max(), p.radius, atol=1e-5)


def test_kcenter_is_deterministic_and_nested():
    x = np.random.default_rng(1).normal(size=(500, 16))
    a, b = reduce.kcenter(x, 32), reduce.kcenter(x, 64)
    assert (a.tiles == b.tiles[:32]).all()                  # the first n of a longer run are the n-set
    assert b.radius <= a.radius


def test_kcenter_small_slide_keeps_all_tiles():
    p = reduce.kcenter(np.eye(5), 256)
    assert sorted(p.tiles) == list(range(5)) and p.radius == 0 and (p.represented == 1).all()


def test_regions_mean_and_minimum_tiles():
    size = 448.0
    xy = [(i, j) for i in range(8) for j in range(8)] + [(8, 0)]   # one full region + 1 stray tile
    tiles = pd.DataFrame({"x": [i * size for i, _ in xy], "y": [j * size for _, j in xy], "size_l0": size,
                          "label": ["tumor"] * 3 + ["normal"] * (len(xy) - 3)})
    x = np.arange(len(xy), dtype=np.float32)[:, None].repeat(4, 1)
    vec, meta = reduce.regions(x, tiles, side=8, min_tiles=16)
    assert len(vec) == 1 and np.allclose(vec[0], x[:64].mean(0))
    assert meta.iloc[0].to_dict() == {"x": 0, "y": 0, "size_l0": 8 * size, "n_tiles": 64,
                                      "tumor_tiles": 3, "boundary_tiles": 0}
