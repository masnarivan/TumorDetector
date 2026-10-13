"""Licence gate for CI: walk the RUNTIME dependency closure of tumordetector and fail on a
strong-copyleft or unidentified licence. Development tools (dvc, pytest, ...) are not shipped
and are not checked.

Usage: uv run scripts/check_licenses.py [--list]
"""
import re
import sys
from importlib import metadata

from packaging.requirements import Requirement

# Packages whose metadata carries no usable licence field, checked by hand (licence, source).
REVIEWED = {
    "huey": "MIT",        # https://github.com/coleifer/huey/blob/master/LICENSE
    "skops": "MIT",       # https://github.com/skops-dev/skops/blob/main/LICENSE
}
# GPL/AGPL is a blocker unless it is LGPL, one side of an "OR", or carries a linking exception.
BLOCKED = re.compile(r"(?<![L])A?GPL", re.I)


def licence_of(dist: metadata.Distribution) -> str:
    name = dist.metadata["Name"].lower()
    if name in REVIEWED:
        return REVIEWED[name]
    meta = dist.metadata
    classifiers = [c.split(" :: ")[-1] for c in meta.get_all("Classifier", []) if c.startswith("License ::")]
    text = meta.get("License-Expression") or "; ".join(classifiers) or (meta.get("License") or "").strip()
    return text.splitlines()[0][:120] if text else "UNKNOWN"


def runtime_closure(root: str) -> dict[str, metadata.Distribution]:
    seen, todo = {}, [root]
    while todo:
        name = re.sub(r"[-_.]+", "-", todo.pop()).lower()
        if name in seen:
            continue
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue   # optional dependency that is not installed on this platform
        seen[name] = dist
        for req in map(Requirement, dist.requires or []):
            if req.marker is None or req.marker.evaluate({"extra": ""}):
                todo.append(req.name)
    return seen


def main():
    dists = runtime_closure("tumordetector")
    dists.pop("tumordetector")
    bad = []
    for name, dist in sorted(dists.items()):
        lic = licence_of(dist)
        blocked = lic == "UNKNOWN" or (BLOCKED.search(lic) and " OR " not in lic and "exception" not in lic.lower())
        if "--list" in sys.argv:
            print(f"{name}=={dist.version}\t{lic}")
        if blocked:
            bad.append(f"{name}=={dist.version}: {lic}")
    print(f"{len(dists)} runtime dependencies checked, {len(bad)} blocked")
    if bad:
        raise SystemExit("\n".join(bad))


if __name__ == "__main__":
    main()
