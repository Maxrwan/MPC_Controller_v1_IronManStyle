"""Explicit separately invoked G0/G1 single-attempt genuine correctness prerequisites."""

import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def attempt(case):
    output = ROOT / "results/preintegration/w1" / (case.lower() + "-" + uuid4().hex)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.update(PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    command = [
        sys.executable,
        "-P",
        "-S",
        str(ROOT / "scripts/preintegration/launch.py"),
        "--case",
        case,
        "--output",
        str(output),
    ]
    result = subprocess.run(command, env=env, cwd=ROOT, capture_output=True, text=True, timeout=65)
    assert result.returncode == 0, (str(output), result.stdout, result.stderr)
    raw = json.loads((output / "raw.json").read_text())
    assert raw["failure"] is None and raw["end_time"] == 0.24
    assert raw["plans"][0]["startup"] and not raw["fallbacks"]
    assert json.loads((output / "worker-result.json").read_text())["complete"]
    return raw


def test_g0_genuine_zero_delay():
    raw = attempt("G0")
    assert len(raw["controls"]) > 1
    assert all(c["physical_latency"] == 0 for c in raw["controls"])


def test_g1_genuine_injected_delay():
    raw = attempt("G1")
    assert raw["codriver_misses"]
    assert any(p.get("physical_delay") == 0.06 for p in raw["plans"] if not p["startup"])
    assert all(abs(c["application_time"] - c["time"] - 0.025) < 1e-9 for c in raw["controls"])
