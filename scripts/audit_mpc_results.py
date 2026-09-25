"""Audit saved physical/control clocks and staleness independently of the runner."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from apex.config import load_vehicle_parameters
from apex.state import STATE_NAMES

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/mpc_baseline")
    root = parser.parse_args().output
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    audit = {}
    for path in sorted(root.glob("*/summary.json")):
        folder = path.parent
        summary = json.loads(path.read_text())
        period = (summary.get("mpc_config") or {}).get("dt", 0.05)
        steering_rate = (summary.get("mpc_config") or {}).get("steering_rate", 1.0)
        increment_limit = period * steering_rate
        state = pd.read_csv(folder / "states.csv", float_precision="round_trip")
        controls = (
            pd.read_csv(folder / "controls.csv", float_precision="round_trip")
            if (folder / "controls.csv").exists()
            else pd.DataFrame()
        )
        assert np.isfinite(state[list(STATE_NAMES) + ["time", "delta", "a_cmd"]].to_numpy()).all()
        assert np.all(np.diff(state.time) > 0) and np.max(np.diff(state.time)) <= 0.005 + 1e-12
        assert (abs(state.delta) <= p.maximum_steering_angle).all()
        assert (state.a_cmd >= -p.maximum_braking_deceleration).all()
        assert (state.a_cmd <= p.maximum_acceleration).all()
        expected = np.zeros((len(state), 2))
        if not controls.empty:
            idx = np.searchsorted(controls.time, state.time, side="right") - 1
            active = idx >= 0
            expected[active] = controls[["delta", "a_cmd"]].to_numpy()[idx[active]]
        np.testing.assert_array_equal(state[["delta", "a_cmd"]].to_numpy(), expected)
        record = {
            "plant_rows": len(state),
            "applied_updates": len(controls),
            "finite_plant": True,
            "held_commands_match": True,
            "plant_step_max": float(np.diff(state.time).max()),
        }
        changes = np.diff(np.r_[0.0, controls.delta]) if not controls.empty else np.array([])
        activity = {
            "max_steering_increment": float(abs(changes).max()) if len(changes) else 0.0,
            "steering_bound_active_updates": int(
                np.isclose(abs(controls.delta), p.maximum_steering_angle, atol=1e-6, rtol=0).sum()
            )
            if not controls.empty
            else 0,
            "acceleration_bound_active_updates": int(
                (
                    np.isclose(controls.a_cmd, p.maximum_acceleration, atol=1e-6, rtol=0)
                    | np.isclose(controls.a_cmd, -p.maximum_braking_deceleration, atol=1e-6, rtol=0)
                ).sum()
            )
            if not controls.empty
            else 0,
        }
        event_path = folder / "solver_events.csv"
        if event_path.exists():
            events = pd.read_csv(event_path, float_precision="round_trip")
            assert (
                summary["timing"]["nominal_releases"] == len(events) + events.missed_releases.sum()
            )
            applied = events[events.applied]
            assert len(applied) == len(controls)
            assert (abs(changes) <= increment_limit + 1e-6).all()
            activity["steering_rate_bound_active_updates"] = int(
                np.isclose(abs(changes), increment_limit, atol=1e-6, rtol=0).sum()
            )
            errors = []
            for event in applied.itertuples():
                sample = np.array([getattr(event, f"x_sample_{name}") for name in STATE_NAMES])
                actual = np.array([getattr(event, f"x_apply_{name}") for name in STATE_NAMES])
                drift = np.array([getattr(event, f"delta_{name}") for name in STATE_NAMES])
                np.testing.assert_allclose(actual - sample, drift, atol=1e-13, rtol=0)
                index = np.linalg.norm(drift[[0, 1, 2, 3, 5]] / [0.5, 0.5, 1, 0.1, 0.1])
                assert abs(index - event.staleness_index) < 1e-12
                assert abs(event.application_time - event.release_time - event.latency) < 1e-12
                for time, vector in (
                    (event.release_time, sample),
                    (event.application_time, actual),
                ):
                    i = np.argmin(abs(state.time.to_numpy() - time))
                    assert abs(state.time.iloc[i] - time) < 1e-12
                    error = float(abs(state[list(STATE_NAMES)].iloc[i].to_numpy() - vector).max())
                    errors.append(error)
                    assert error < 1e-12
            record.update(
                staleness_and_clocks_verified=True,
                max_state_log_discrepancy=max(errors, default=0.0),
                solver_events=len(events),
            )
        if summary.get("tire_physics", {}).get("model") == "smooth_combined_grip":
            for axle in ("front", "rear"):
                utilization = state[f"tire_{axle}_combined_utilization"].to_numpy()
                assert np.isfinite(utilization).all() and np.max(utilization) <= 1 + 1e-12
                record[f"max_{axle}_combined_utilization"] = float(np.max(utilization))
        summary["control_activity"] = activity
        summary["plant_validity_failures"] = int(summary["stop_reason"] == "model_validity_failure")
        summary["controller_application_failures"] = int(
            summary["stop_reason"] == "controller_application_failure"
        )
        path.write_text(json.dumps(summary, indent=2) + "\n")
        audit[folder.name] = record
    (root / "verification.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": len(audit),
                "plant_rows": sum(r["plant_rows"] for r in audit.values()),
                "applied_updates": sum(r["applied_updates"] for r in audit.values()),
            }
        )
    )


if __name__ == "__main__":
    main()
