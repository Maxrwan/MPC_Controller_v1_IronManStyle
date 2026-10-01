"""Isolated native controls and actual frozen-controller numerical parity."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from threading_study.analysis import parity  # noqa: E402
from threading_study.config import environment, thread_count  # noqa: E402


@pytest.mark.parametrize("value", [1, 2, 4, 8, "4"])
def test_permitted_counts(value):
    assert thread_count(value, maximum=8) == int(value)


@pytest.mark.parametrize("value", [0, -1, 9, "2.5", 2.0, True, None])
def test_invalid_counts(value):
    with pytest.raises(ValueError):
        thread_count(value, maximum=8)


def test_environment_isolation(monkeypatch):
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "99")
    monkeypatch.setenv("OMP_NUM_THREADS", "99")
    monkeypatch.setenv("VECLIB_MAXIMUM_THREADS", "99")
    a, b = environment(1), environment(2)
    assert a["VECLIB_MAXIMUM_THREADS"] == "1" and b["VECLIB_MAXIMUM_THREADS"] == "2"
    assert "OMP_NUM_THREADS" not in a and "OPENBLAS_NUM_THREADS" not in b
    import os

    assert os.environ["VECLIB_MAXIMUM_THREADS"] == "99"


def test_parity_rejects_changed_or_nonfinite_solutions():
    a = {
        "success": True,
        "status": "Solve_Succeeded",
        "primal_infeasibility": 0,
        "objective": 1.0,
        "first_control": [0.0, 0.0],
        "states": [[1.0]],
        "controls": [[0.0]],
        "slacks": [[0.0]],
    }
    assert parity([a], [a])["pass"]
    assert not parity([a], [{**a, "first_control": [0.001, 0.0]}])["pass"]
    assert not parity([a], [{**a, "states": [[float("nan")]]}])["pass"]
    assert not parity([a], [{**a, "primal_infeasibility": 1e-3}])["pass"]


@pytest.mark.skipif(
    sys.platform != "darwin", reason="Installed Accelerate experiment is macOS-specific"
)
def test_fresh_process_single_and_threaded_parity(tmp_path):
    outputs = []
    for i, n in enumerate([1, 2, 1]):
        folder = tmp_path / str(i)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/run_mpc_threading_study.py"),
                "worker",
                "--workload",
                "C",
                "--threads",
                str(n),
                "--samples",
                "3",
                "--warmup",
                "2",
                "--folder",
                str(folder),
            ],
            cwd=ROOT,
            env=environment(n),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        summary = json.loads((folder / "summary.json").read_text())
        assert summary["all_success"]
        assert summary["native_control"]["blas_threading_mode"] == (1 if n == 1 else 0)
        outputs.append(json.loads((folder / "solutions.json").read_text()))
    assert parity(outputs[0], outputs[1])["pass"]
    for a, b in zip(outputs[0], outputs[2]):
        np.testing.assert_array_equal(a["first_control"], b["first_control"])
        np.testing.assert_array_equal(a["states"], b["states"])


@pytest.mark.parametrize("threads", [1, 2, 4, 8])
def test_retained_closed_loop_consistency(threads):
    folder = ROOT / "results/mpc_threading_study/closed_loop" / f"C_t{threads}_r0"
    if not (folder / "summary.json").exists():
        pytest.skip("Retained measured-latency study is not available")
    r = json.loads((folder / "summary.json").read_text())
    assert r["failure"] is None and len(r["lap_times"]) == 2
    assert r["solver_failures"] == r["fallbacks"] == r["boundary_violations"] == 0
    assert r["full_run"]["rms_e_y"] < 0.005
    assert r["full_run"]["rms_e_psi"] < 0.02
    assert r["full_run"]["rms_speed_error"] < 0.04
    assert r["max_slack"] < 1e-4 and r["maximum_primal_residual"] < 1e-6
    assert max(r["max_front_combined_utilization"], r["max_rear_combined_utilization"]) <= 1
    assert r["timing"]["completed_solves"] + r["timing"]["missed_deadlines"] == 325
    # Observed misses are retained; desktop timing is not a zero-miss CI assertion.
