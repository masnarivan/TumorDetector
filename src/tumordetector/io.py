"""File helpers shared by every pipeline stage: hashes, atomic writes, resumable downloads.

Ported from prototype 02 (mil-camelyon16, scripts/extract_all.py).
"""
import fcntl
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np


def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


def array_sha256(a: np.ndarray) -> str:
    """Hash of an array's dtype, shape and bytes: the identity of a slide's embeddings."""
    h = hashlib.sha256(f"{a.dtype.str}{a.shape}".encode())
    h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


def atomic_write(path: Path, write):
    """Write via a temp file in the same folder, flush it to disk, then rename.

    The rename is atomic on POSIX (same filesystem): `path` is either absent or complete.
    fsync first, otherwise after a power cut the renamed file could still be missing data;
    on macOS only F_FULLFSYNC also flushes the drive's own cache (it does not exist on Linux).
    """
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        write(f)
        f.flush()
        if hasattr(fcntl, "F_FULLFSYNC"):
            fcntl.fcntl(f.fileno(), fcntl.F_FULLFSYNC)
        else:
            os.fsync(f.fileno())
    os.replace(tmp, path)


def write_json(path: Path, obj):
    atomic_write(path, lambda f: f.write(json.dumps(obj, indent=1, sort_keys=True).encode()))


def read_json(path: Path):
    return json.loads(Path(path).read_text())


def curl(url: str, out: Path, attempts: int = 10, min_speed: int = 1_000_000):
    """curl with resume, retried. A connection can stay open while sending little or nothing, and
    curl has no timeout for that by default: one download hung for 30+ min, and on Colab single
    S3 connections dropped to a few kB/s while a new one gets ~15 MB/s. So abort below `min_speed`
    bytes/s averaged over 60 s and resume from where it stopped (-C -) on a new connection.
    `attempts` counts only the retries that downloaded nothing, so a slow but moving link finishes."""
    failures = 0
    while True:
        before = out.stat().st_size if out.exists() else 0
        r = subprocess.run(["curl", "-fsSL", "-C", "-", "--speed-limit", str(min_speed), "--speed-time", "60",
                            "--connect-timeout", "30", "-o", out, url])
        if r.returncode == 0:
            return
        moved = (out.stat().st_size if out.exists() else 0) > before
        failures = 0 if moved else failures + 1
        print(f"  curl exit {r.returncode} on {url.rsplit('/', 1)[-1]} ({'resuming' if moved else 'no progress'}), "
              f"retry {failures}/{attempts}", flush=True)
        if failures >= attempts:
            raise OSError(f"download failed after {attempts} attempts without progress: {url}")
        time.sleep(1 if moved else min(60, 5 * 2 ** failures))


def code_version() -> str:
    """Git commit of the code that produced an output ('+dirty' with uncommitted changes)."""
    try:
        root = Path(__file__).resolve().parent
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
        return sha.stdout.strip() + ("+dirty" if dirty.stdout.strip() else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
