"""`td task=splits`: data/manifests/<dataset>_splits.csv (cross-validation folds)."""
from omegaconf import DictConfig

from tumordetector.tasks.common import load_manifest, splits_path


def run(cfg: DictConfig):
    """Written once and versioned in git: a fold never changes because code or data did."""
    from tumordetector.mil.evaluate import make_cv_folds

    out = splits_path(cfg)
    if out.exists() and not cfg.mil.overwrite_splits:
        raise SystemExit(f"{out} exists; splits are never regenerated implicitly (mil.overwrite_splits=true)")
    folds = make_cv_folds(load_manifest(cfg), cfg.mil.folds, cfg.seed)
    folds.to_csv(out, index=False)
    print(folds.cv_fold.value_counts().sort_index().to_string(), f"\n-> {out}")
