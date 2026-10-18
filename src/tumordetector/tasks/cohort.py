"""`td task=cohort head=<id>`: data/manifests/heads/<id>.csv (slides, labels, domains, roles, folds)."""
from pathlib import Path

import pandas as pd
from omegaconf import DictConfig, OmegaConf

from tumordetector.config import dataset_cfg


def run(cfg: DictConfig):
    """Written once and versioned in git, like the splits: a fold never changes because code or data did."""
    from tumordetector.heads.cohort import assemble, assign_folds, cohort_path
    from tumordetector.heads.spec import HeadSpec

    spec = HeadSpec(**OmegaConf.to_container(cfg.head, resolve=True))
    out = cohort_path(Path(cfg.paths.heads), spec)
    if out.exists() and not spec.overwrite:
        raise SystemExit(f"{out} exists; a cohort is never rewritten implicitly (head.overwrite=true)")
    manifests = {name: pd.read_csv(dataset_cfg(name).manifest) for name in spec.datasets}
    cohort, excluded = assemble(spec, manifests)
    cohort = assign_folds(cohort, cfg.mil.folds, cfg.seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    cohort.to_csv(out, index=False)
    excluded.to_csv(out.with_name(f"{spec.id}_excluded.csv"), index=False)
    summary = pd.crosstab([cohort.role, cohort.domain], cohort.label, margins=True)
    print(summary.to_string(), f"\n{len(cohort)} slides -> {out}; {len(excluded)} excluded",
          *excluded.excluded_reason.value_counts().to_string().splitlines(), sep="\n")
