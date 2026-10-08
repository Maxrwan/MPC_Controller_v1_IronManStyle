"""End-to-end progress telemetry with deliberately skipped planner deadlines."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from async_study.analysis import audit  # noqa: E402
from task007b.analysis import analyze_case  # noqa: E402


def test_progress_export_and_delayed_physical_chronology(tmp_path):
    subprocess.run(
        [
            sys.executable,
            "scripts/run_task007b.py",
            "run",
            "--output",
            str(tmp_path),
            "--case",
            "smoke",
            "--progress-weight",
            "2",
            "--mode",
            "injected",
            "--injected-delay",
            ".15",
            "--duration",
            ".5",
        ],
        cwd=ROOT,
        env={**os.environ, "MPLCONFIGDIR": str(tmp_path / "mpl")},
        check=True,
        capture_output=True,
        text=True,
    )
    folder = tmp_path / "smoke"
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["planner_misses"] > 0
    assert summary["codriver_misses"] == 0
    assert summary["fallback_events"] == 0
    assert summary["failure"] is None
    report, telemetry, nodes, *_ = analyze_case(folder)
    required = {
        "actual_beta",
        "planned_beta",
        "error_e_y",
        "error_e_psi",
        "error_vy",
        "error_r",
        "node_adaptation_e_y",
        "node_adaptation_vx",
        "front_utilization",
        "rear_utilization",
        "steering_utilization",
        "steering_rate_utilization",
        "acceleration_utilization",
        "lateral_acceleration",
        "reserve",
        "age",
        "centerline_curvature",
        "curvature_ahead",
        "forecast_residual_vy",
        "planner_planner_total_time",
        "predicted_slack",
        "cost_state_tracking",
        "cost_input_reference",
        "cost_input_increment",
        "cost_terminal_tracking",
        "cost_slack_linear",
        "cost_slack_quadratic",
        "cost_progress_reward",
        "cost_total",
        "application_s_abs",
    }
    assert required <= set(telemetry.columns)
    assert telemetry.s_abs.iloc[-1] > telemetry.s_abs.iloc[0]
    assert len(telemetry) >= 49
    assert np.isfinite(telemetry[list(required)].dropna()).all().all()
    assert nodes.s_abs.max() > telemetry.s_abs.max()
    assert report["costs"]["progress_reward"]["mean"] < 0
    assert report["objective_accounting_max_error"] < 1e-9
    audit(tmp_path)
