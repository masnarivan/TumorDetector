"""E3b follow-up: were the CAMELYON16 test slides scanned in another batch than the training ones?

Reads the first page of every CAMELYON16 .tif over HTTP range requests (a few MB per slide, the
image is not downloaded): the Philips XML in ImageDescription carries the DICOM attributes of the
scan (dates, device, software). One row per slide.

    uv run python experiments/e3b_scan_metadata.py dump [ATTRIBUTE ...]   # all attributes of 2 slides
    uv run python experiments/e3b_scan_metadata.py fetch                  # every slide, resumable
    uv run python experiments/e3b_scan_metadata.py report                 # case year vs E3b scores

The source file name is the pathology case number (Radboud: T<yy>-<number>-<block>): the report keeps
only its year and whether the case has another slide, not the number itself.
"""
import io
import json
import re
import ssl
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
import truststore

from tumordetector.data import camelyon16

CTX = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
OUT = Path("data/experiments/e3b/scan_metadata")      # one json per slide, not in git
REPORT = Path("data/reports/experiments/e3b")
RETRIES = 8


def _open(req: urllib.request.Request) -> bytes:
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
                return r.read() if req.get_method() != "HEAD" else r.headers
        except OSError:
            if attempt == RETRIES - 1:
                raise
            time.sleep(2 ** attempt)


class RangeFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests, blocks cached."""

    def __init__(self, url: str, block: int = 1 << 18):
        self.url, self.block, self.pos, self.cache = url, block, 0, {}
        self.size = int(_open(urllib.request.Request(url, method="HEAD"))["Content-Length"])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def _block(self, i: int) -> bytes:
        if i not in self.cache:
            a = i * self.block
            b = min(a + self.block, self.size) - 1
            self.cache[i] = _open(urllib.request.Request(self.url, headers={"Range": f"bytes={a}-{b}"}))
        return self.cache[i]

    def readinto(self, buf):
        n = min(len(buf), self.size - self.pos)
        if n <= 0:
            return 0
        out = bytearray()
        while len(out) < n:
            i, o = divmod(self.pos + len(out), self.block)
            out += self._block(i)[o:o + n - len(out)]
        buf[:n] = out
        self.pos += n
        return n


def attributes(slide_id: str) -> dict[str, str]:
    """Every leaf attribute of the Philips XML; repeated names (one per scanned image) get a suffix."""
    f = RangeFile(camelyon16.slide_url(slide_id))
    with tifffile.TiffFile(io.BufferedReader(f, 1 << 18)) as t:
        page = t.pages.first
        desc, software, datetime = page.description, page.software, page.tags.valueof("DateTime")
    out = {"tiff_software": software, "tiff_datetime": datetime, "mb_read": round(len(f.cache) * f.block / 1e6, 1)}
    for a in ET.fromstring(desc).iter("Attribute"):
        value = (a.text or "").strip()
        if value and len(value) < 300:
            name, i = a.get("Name"), 1
            while (key := name if i == 1 else f"{name}#{i}") in out:
                i += 1
            out[key] = value
    return out


def report():
    rows = []
    for p in sorted(OUT.glob("*.json")):
        a = json.loads(p.read_text())
        src = re.search(r'sourceFilename="([^"]*)"', a.get("DICOM_DERIVATION_DESCRIPTION", ""))
        src = src.group(1) if src else ""
        year, case = re.match(r"T(\d+)", src), re.match(r"(T\d+-\d+)", src)
        rows.append({"slide_id": p.stem, "case_year": 2000 + int(year.group(1)) if year else None,
                     "case": case.group(1) if case else None, "manufacturer": a.get("DICOM_MANUFACTURER"),
                     "software": a.get("DICOM_SOFTWARE_VERSIONS"), "pixel_spacing": a.get("DICOM_PIXEL_SPACING")})
    t = pd.DataFrame(rows).merge(pd.read_csv("data/manifests/camelyon16.csv")[["slide_id", "center", "split", "label"]])
    t["case_has_other_slide"] = t.case.notna() & t.case.duplicated(keep=False)
    shared = t[t.case_has_other_slide].groupby("case").slide_id.apply(sorted).tolist()
    folds = pd.read_csv("data/manifests/camelyon16_splits.csv")[["slide_id", "cv_fold"]]
    t = t.merge(folds, how="left")
    rad = t[t.center == "radboud"]
    rad = rad.assign(role=np.select([rad.split == "test", rad.cv_fold.isin([0, 1, 2])],
                                    ["eval_id", "reference"], "calibration"))
    s = pd.read_csv(REPORT / "slide_scores.csv")
    s = s[s.reference == "kcenter_256"][["slide_id", "S0"]]
    thr = json.loads((REPORT / "posthoc.json").read_text())["threshold"]
    ev = rad[rad.role == "eval_id"].merge(s)
    ev["referred"] = ev.S0 > thr
    years = {f"{role} label {lab}": g.case_year.value_counts().sort_index().astype(int).to_dict()
             for (role, lab), g in rad.groupby(["role", "label"])}
    manifest = set(pd.read_csv("data/manifests/camelyon16.csv").slide_id)
    out = {"slides_read": len(t), "missing": sorted(manifest - set(t.slide_id)),
           "manufacturer_by_center": t.groupby("center").manufacturer.value_counts().unstack().fillna(0).astype(int)
                                      .to_dict("index"),
           "software": t.software.value_counts().to_dict(),
           "radboud_case_years": years,
           "eval_id_referred_by_label_year": {f"label {lab}": {int(y): [int(g.referred.sum()), len(g)]
                                                               for y, g in gl.groupby("case_year")}
                                              for lab, gl in ev.groupby("label")},
           "cases_with_several_slides": shared}
    t.drop(columns="case").to_csv(REPORT / "scan_metadata.csv", index=False)
    (REPORT / "scan_metadata.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "dump":
        for sid in ("tumor_001", "test_011"):
            print("==", sid)
            for k, v in attributes(sid).items():
                print(f"  {k} = {v}")
    elif step == "fetch":
        OUT.mkdir(parents=True, exist_ok=True)
        slides = pd.read_csv("data/manifests/camelyon16.csv").slide_id
        todo = [s for s in slides if not (OUT / f"{s}.json").exists()]
        print(f"{len(todo)} slides to read, {len(slides) - len(todo)} done", flush=True)
        for sid in todo:
            try:
                (OUT / f"{sid}.json").write_text(json.dumps(attributes(sid), indent=1))
                print(sid, flush=True)
            except Exception as e:   # noqa: BLE001 - report and move on, rerun picks it up
                print(f"{sid}: FAILED {e!r}", flush=True)
    elif step == "report":
        report()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
