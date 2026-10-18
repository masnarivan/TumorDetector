"""A head's cohort: the slides of several datasets it covers, with label, domain, role and fold.

Written once as data/manifests/heads/<head>.csv and versioned in git, like the splits file; every
excluded slide goes to <head>_excluded.csv with the reason. The cohort does not depend on the
backbone: slides without embeddings are left out at training time, and reported there.

  domain   the spec's `domain` columns joined (camelyon16/radboud, camelyon17/radboud, ...): finer than
           the centre, because the same centre in two datasets is prepared and converted differently
           (experiments E3b and C17). Balancing and group DRO work on domains.
  role     dev, or external (locked test) if the slide matches the spec's `roles.external`.
  cv_fold  folds of the development slides, grouped by patient and stratified by label x domain;
           -1 for external slides. Leave-one-centre-out is computed from `center`, not stored.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from tumordetector.heads.spec import HeadSpec
from tumordetector.io import read_json

COLUMNS = ["slide_id", "dataset", "center", "domain", "patient_pseudo_id", "reference_diagnosis", "label", "role"]


def cohort_path(root: Path, spec: HeadSpec) -> Path:
    return Path(root) / f"{spec.id}.csv"


def assemble(spec: HeadSpec, manifests: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """-> (cohort rows in COLUMNS, without folds; excluded slides with `excluded_reason`)."""
    if missing := sorted(set(spec.datasets) - set(manifests)):
        raise ValueError(f"no manifest for {missing}")
    parts = []
    for name in spec.datasets:
        m = manifests[name]
        if (wrong := set(m["dataset"]) - {name}):
            raise ValueError(f"manifest given as {name} holds rows of {sorted(wrong)}")
        parts.append(m)
    m = pd.concat(parts, ignore_index=True)
    if (dup := m.slide_id[m.slide_id.duplicated()]).any():
        raise ValueError(f"slide ids in more than one dataset: {sorted(dup)[:5]}")
    if absent := sorted({c for c in [*spec.domain, *(c for v in spec.roles.values() for c in v)]} - set(m.columns)):
        raise ValueError(f"spec names columns the manifests do not have: {absent}")

    reason = pd.Series("", index=m.index)
    off_site = ~m.site.isin(spec.sites)
    reason[off_site] = "site " + m.site[off_site] + f" not in the head's sites {spec.sites}"
    label = m.reference_diagnosis.map(spec.labels)
    unmapped = ~off_site & label.isna()
    reason[unmapped] = "reference_diagnosis '" + m.reference_diagnosis[unmapped] + "' not in the head's labels"
    excluded = m[reason != ""].assign(excluded_reason=reason[reason != ""])

    c = m[reason == ""].assign(label=label[reason == ""].astype(int))
    c["domain"] = c[spec.domain].astype(str).agg("/".join, axis=1)
    external = np.zeros(len(c), dtype=bool)
    for column, values in spec.roles.get("external", {}).items():
        external |= c[column].isin(values).to_numpy()
    c["role"] = np.where(external, "external", "dev")
    mixed = c.groupby("patient_pseudo_id").role.nunique()
    if (mixed > 1).any():
        raise ValueError(f"patients in both roles: {sorted(mixed[mixed > 1].index)[:5]}")
    return (c[COLUMNS].sort_values(["dataset", "slide_id"]).reset_index(drop=True),
            excluded[["slide_id", "dataset", "center", "site", "reference_diagnosis", "excluded_reason"]])


def assign_folds(cohort: pd.DataFrame, n_folds: int, seed: int) -> pd.DataFrame:
    """Folds of the development slides: a patient's slides stay together (5 nodes per patient in
    CAMELYON17), each fold gets every label in every domain as far as the counts allow."""
    dev = cohort[cohort.role == "dev"]
    folds = pd.Series(-1, index=cohort.index)
    splitter = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    strata = dev.label.astype(str) + "_" + dev.domain
    for k, (_, test) in enumerate(splitter.split(dev, strata, groups=dev.patient_pseudo_id)):
        folds.loc[dev.index[test]] = k
    return cohort.assign(cv_fold=folds)


def check_unchanged(saved: pd.DataFrame, spec: HeadSpec, manifests: dict[str, pd.DataFrame]):
    """The saved cohort still agrees with today's manifests and spec: a slide added, removed or
    relabelled since it was written must be a deliberate new cohort, not a silent drift."""
    now, _ = assemble(spec, manifests)
    a = saved[COLUMNS].set_index("slide_id").sort_index()
    b = now.set_index("slide_id").sort_index()
    problems = []
    if gone := sorted(set(a.index) - set(b.index)):
        problems.append(f"only in the saved cohort: {gone[:5]}")
    if new := sorted(set(b.index) - set(a.index)):
        problems.append(f"not in the saved cohort: {new[:5]}")
    common = a.index.intersection(b.index)
    changed = (a.loc[common].astype(str) != b.loc[common].astype(str)).any(axis=1)
    if changed.any():
        problems.append(f"changed: {sorted(common[changed])[:5]}")
    if problems:
        raise SystemExit(f"cohort of {spec.id} v{spec.version} no longer matches the manifests or the spec "
                         f"({'; '.join(problems)}): write a new one on purpose (head.overwrite=true)")


def embedding_roots(out_dirs: dict[str, Path], backbone: str) -> tuple[dict[str, Path], dict]:
    """Each dataset's embedding folder for the backbone, refusing folders of different backbone
    versions: embeddings of different versions are never mixed, not even across datasets."""
    roots = {name: Path(out) / "embeddings" / backbone for name, out in out_dirs.items()}
    idents = {}
    for name, root in roots.items():
        if not (root / "collection.json").exists():
            raise SystemExit(f"{name}: no embeddings for {backbone} in {root}")
        idents[name] = read_json(root / "collection.json")
    if len({i["collection"] for i in idents.values()}) > 1:
        raise SystemExit("embeddings of different backbone versions: "
                         + ", ".join(f"{n} {i['collection']}" for n, i in idents.items()))
    return roots, next(iter(idents.values()))
