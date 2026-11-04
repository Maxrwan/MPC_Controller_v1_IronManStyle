"""Explicit one-shot conditional genuine prerequisites and smoke, never a routine regression.

Requires current Primary budget AND independent PASS. Consumed claims prohibit rerunning.
The single live driver owns successor grants; disk receipts alone cannot resume execution.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def test_genuine_conditional_g0_g1_smoke_sequence():
    output = ROOT / "results/preintegration/w1" / ("replacement-" + uuid4().hex)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.update(PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    command = [
        sys.executable,
        "-P",
        "-S",
        str(ROOT / "scripts/preintegration/launch.py"),
        "--case",
        "conditional-sequence",
        "--output",
        str(output),
    ]
    result = subprocess.run(command, env=env, cwd=ROOT, capture_output=True, text=True, timeout=185)
    assert result.returncode == 0, (str(output), result.stdout, result.stderr)
    for case, duration in (("G0", 0.24), ("G1", 0.24), ("measured-smoke", 2.0)):
        folder = output / case
        raw = json.loads((folder / "raw.json").read_text())
        assert raw["failure"] is None and raw["end_time"] == duration
        assert raw["plans"][0]["startup"] and not raw["fallbacks"]
        assert json.loads((folder / "scientific-audit.json").read_text())["valid_prerequisite"]
        if case == "G0":
            assert len(raw["controls"]) > 1
            assert all(c["physical_latency"] == 0 for c in raw["controls"])
        if case == "G1":
            assert raw["codriver_misses"]
            assert all(p.get("physical_delay") == 0.06 for p in raw["plans"] if not p["startup"])
            assert all(
                abs(c["application_time"] - c["time"] - 0.025) < 1e-9 for c in raw["controls"]
            )
