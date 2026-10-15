"""`td task=manifest`: data/manifests/<dataset>.csv, validated (rows that fail go to <dataset>_blocked.csv)."""
from pathlib import Path

from omegaconf import DictConfig


def run(cfg: DictConfig):
    from tumordetector.data import camelyon16
    from tumordetector.data.schema import validate_manifest

    builders = {"camelyon16": camelyon16.build_manifest}
    ok, blocked = validate_manifest(builders[cfg.data.name]())
    out = Path(cfg.data.manifest)
    out.parent.mkdir(parents=True, exist_ok=True)
    ok.to_csv(out, index=False)
    blocked_path = out.with_name(out.stem + "_blocked.csv")
    if len(blocked):
        blocked.to_csv(blocked_path, index=False)
    else:
        blocked_path.unlink(missing_ok=True)
    print(f"{len(ok)} slides -> {out}; {len(blocked)} blocked" + (f" -> {blocked_path}" if len(blocked) else ""))
