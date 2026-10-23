import subprocess

import pytest

from tumordetector import io


def fake_curl(monkeypatch, steps):
    """Each call of curl appends steps[i][0] bytes to the output and exits with steps[i][1]."""
    calls = iter(steps)

    def run(cmd, **kw):
        grow, code = next(calls)
        out = cmd[cmd.index("-o") + 1]
        with open(out, "ab") as f:
            f.write(b"x" * grow)
        return subprocess.CompletedProcess(cmd, code)

    monkeypatch.setattr(io.subprocess, "run", run)
    monkeypatch.setattr(io.time, "sleep", lambda s: None)


def test_curl_resumes_a_slow_download_however_many_times_it_moves(tmp_path, monkeypatch):
    out = tmp_path / "slide.tif.part"
    fake_curl(monkeypatch, [(10, 28)] * 15 + [(10, 0)])   # 15 aborts below the speed limit, all with progress
    io.curl("https://example.org/slide.tif", out, attempts=3)
    assert out.stat().st_size == 160


def test_curl_gives_up_after_attempts_without_progress(tmp_path, monkeypatch):
    out = tmp_path / "slide.tif.part"
    fake_curl(monkeypatch, [(10, 28), (0, 28), (0, 7), (0, 28)])
    with pytest.raises(OSError, match="without progress"):
        io.curl("https://example.org/slide.tif", out, attempts=3)
