"""Diagnostic integration and interpolation conventions, not invented vehicle laws."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from task007c_resume.physics import prediction_errors, variable_step

from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.state import STATE_NAMES


def test_diagnostic_step_matches_existing_rk4(dynamic_vehicle):
    model = SymbolicBicycle(dynamic_vehicle, RACING_TIRE_PHYSICS)
    diagnostic = variable_step(model)
    x = np.array([2, 0.03, 0.04, 0.02, 1, 0.05])
    u = np.array([0.01, 0.2])
    for dt in [0.001, 0.005, 0.01]:
        expected, _ = model.rk4(dt, 1)(x, u, 0.02)
        np.testing.assert_allclose(diagnostic(x, u, 0.02, dt), expected, atol=1e-14, rtol=1e-14)


def test_packet_errors_no_extrapolation_and_wrapped_heading():
    # Pure extraction/interpolation test vectors; no dynamics asserted.
    state = pd.DataFrame([[1, 0, 0, 3.13, 0, 0], [1, 0, 0, -3.13, 1, 0]], columns=STATE_NAMES)
    state["time"] = [0, 1]
    packet = dict(
        plan_id=2,
        timestamps=[-0.1, 0.5, 1.1],
        states=[[1, 0, 0, 0, 0, 0], [1, 0, 0, np.pi, 0.5, 0], [1, 0, 0, 0, 0, 0]],
    )
    errors = prediction_errors(state, [packet])
    assert len(errors) == 1 and errors.iloc[0]["step"] == 1
    np.testing.assert_allclose(errors[list(STATE_NAMES)].to_numpy(), 0, atol=1e-12)


def test_common_coverage_keeps_native_endpoints_without_forward_tail(tmp_path):
    """Tabular extraction vectors only; no physical dynamics are asserted."""
    import json

    from task007c_resume.common_coverage import compare

    folders = []
    for name, times in [("long", [0, 0.5, 1, 1.5, 2]), ("short", [0, 0.5, 1, 1.4])]:
        folder = tmp_path / name
        folder.mkdir()
        folders.append(folder)
        t = pd.DataFrame(
            dict(
                time=times,
                s_abs=times,
                lap=1,
                sector="segment",
                interval=np.diff([*times, times[-1]]),
            )
        )
        for prefix in ["reference_", "actual_"]:
            for field in ["e_psi", "e_y", "vy", "r"]:
                t[prefix + field] = 0.0
        for field in [
            "actual_beta",
            "planned_beta",
            "front_utilization",
            "rear_utilization",
            "predicted_slack",
            "error_e_y",
            "nominal_delta",
            "delta",
            "steering_rate",
        ]:
            t[field] = 0.0
        t["clearance"] = 0.5
        t.to_csv(folder / "telemetry.csv", index=False)
        pd.DataFrame(dict(s_abs=times, boundary_violation=0)).to_csv(
            folder / "states.csv", index=False
        )
        (folder / "summary.json").write_text(
            json.dumps(dict(lap_times=[], stop_reason="diagnostic_trace_exhausted"))
        )
    result = compare(folders, tmp_path / "common.json")
    long, short = result["cases"]
    assert long["shared_end_m"] == short["shared_end_m"] == 1.4
    assert long["sampled_end_m"] == 1.0
    assert short["sampled_end_m"] == 1.4
    assert long["lap_prefixes"][0]["duration_s"] == 1.0
    assert short["lap_prefixes"][0]["duration_s"] == 1.4
    assert long["complete_laps"] == short["complete_laps"] == 0
