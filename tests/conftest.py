import numpy as np
import pandas as pd
import pytest
import tifffile

MPP = 0.25          # level-0 resolution of the synthetic slide (40x)
SIZE = 8192         # level-0 side in pixels
TISSUE = (2048, 2048, 6144, 5120)   # x0, y0, x1, y1 of the stained rectangle, level-0 px


@pytest.fixture(scope="session")
def slide_path(tmp_path_factory):
    """A small pyramidal TIFF that OpenSlide opens like a scanner file: grey glass with one
    pink 'tissue' rectangle, 6 levels (downsample 1..32), resolution tags giving 0.25 um/px."""
    rng = np.random.default_rng(0)
    img = np.full((SIZE, SIZE, 3), 235, dtype=np.uint8)
    x0, y0, x1, y1 = TISSUE
    img[y0:y1, x0:x1] = (200, 110, 170)
    img = np.clip(img + rng.integers(-6, 7, img.shape, dtype=np.int16), 0, 255).astype(np.uint8)

    path = tmp_path_factory.mktemp("wsi") / "synthetic.tif"
    px_per_cm = 1e4 / MPP
    with tifffile.TiffWriter(path, bigtiff=True) as tif:
        for level in range(6):
            f = 2 ** level
            tif.write(img[::f, ::f], tile=(256, 256), photometric="rgb", compression="deflate",
                      resolution=(px_per_cm / f, px_per_cm / f), resolutionunit="CENTIMETER",
                      subfiletype=1 if level else 0)
    return path


@pytest.fixture
def manifest_row():
    return {
        "slide_id": "synthetic", "dataset": "test", "file_md5": "0" * 32, "patient_pseudo_id": "p1",
        "case_id": "c1", "center": "a", "scanner": "s", "stain": "H&E", "site": "C77.3",
        "procedure": "biopsy", "specimen_type": "resection", "reference_diagnosis": "negative",
        "diagnosis_source": "histology", "split": "train",
    }


@pytest.fixture
def manifest(manifest_row):
    return pd.DataFrame([manifest_row])
