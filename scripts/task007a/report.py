"""Readable result tables from completed, independently audited Task 007A logs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from threading_study.config import ROOT
from threading_study.report import table


def reference_residuals(output, track, ref):
    from apex.config import load_vehicle_parameters
    from apex.control.mpc.preview import make_preview
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.state import STATE_NAMES

    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    rows = []
    for s in ref.s[:-1:10]:
        # Offset the seam sample to avoid irrelevant numerical-negative progress at zero.
        s = max(float(s), 1e-6)
        preview = make_preview(track, p, ref, s, 1, 0.01, racing_reference=ref)
        v = preview.values
        states = np.array([v[3], v[4], v[5], v[8], preview.progress, v[7]]).T
        control = np.array([v[6, 0], v[10, 0]])
        actual = plant.step(plant.step(states[0], control, 0.005), control, 0.005)
        rows.append(dict(s_track_m=s, **dict(zip(STATE_NAMES, actual - states[1]))))
    result = pd.DataFrame(rows)
    result.to_csv(output / "reference_model_residuals.csv", index=False)
    return {key: float(result[key].abs().max()) for key in STATE_NAMES}


def generate(output, track, ref):
    output = Path(output)
    sectors = pd.read_csv(output / "sector_metrics.csv")
    laps = pd.read_csv(output / "lap_metrics.csv")
    measured = json.loads((output / "measured/racing_analysis.json").read_text())
    errors = [
        "racing_lateral_error_rms",
        "racing_heading_error_rms",
        "racing_speed_error_rms",
        "racing_lateral_error_max_abs",
    ]
    sections = [
        "# Task 007A measured results",
        "Errors use SI units. Primary comparison uses complete laps 2 and 3; "
        "lap 1 is the s=1m rolling-launch transient. Zero/injected runs are supporting checks.",
        "## Lap metrics",
        table(laps[["case", "lap", "phase", *errors]]),
        "## Comparable-lap sector errors",
        table(sectors[sectors.case == "measured"][["sector", *errors]]),
        "## Sector actuator, tire and corridor use",
        table(
            sectors[sectors.case == "measured"][
                [
                    "sector",
                    "delta_max_abs",
                    "steering_rate_utilization_max_abs",
                    "acceleration_max",
                    "braking_min",
                    "front_utilization_max_abs",
                    "rear_utilization_max_abs",
                    "boundary_clearance_min",
                    "margin_activity_seconds",
                ]
            ]
        ),
        "## Sector timing and reserve",
        table(
            sectors[sectors.case == "measured"][
                [
                    "sector",
                    "solve_time_mean",
                    "solve_time_p95",
                    "planner_total_time_mean",
                    "planner_total_time_p95",
                    "codriver_time_mean",
                    "codriver_time_p95",
                    "reserve_min",
                ]
            ]
        ),
        "Sector timing values interpolate logged work onto physical state times and use "
        "time-weighted means; p95 uses samples. Raw timing distributions follow.",
    ]
    timings = []
    for component, group in [
        ("planner", measured["planner_timing"]),
        ("codriver", measured["codriver_timing"]),
    ]:
        for name, values in group.items():
            timings.append(
                dict(
                    component=component,
                    measurement=name,
                    **{k: values[k] * 1000 for k in ["mean", "p50", "p95", "p99", "max", "std"]},
                )
            )
    pd.DataFrame(timings).to_csv(output / "timing_ms.csv", index=False)
    sections += [
        "## Raw measured timing distributions, milliseconds",
        table(pd.DataFrame(timings)),
        "## Candidate supervisor signal ranges (observations only)",
        table(
            pd.DataFrame(
                [dict(signal=k, **v) for k, v in measured["observed_supervisor_ranges"].items()]
            )
        ),
        "Lateral acceleration estimates d(vy)/dt+vx*r by finite differences. No switching. "
        "Difficulty logs also retain completed-plan lateral/heading prediction errors.",
        "## Local APEX-packet tracking",
        table(
            pd.DataFrame([dict(channel=k, **v) for k, v in measured["tracker_envelope"].items()])
        ),
        "## Offline reference-state model residual",
        "At 310 sampled nominal points, propagate the independent nonlinear plant for 10ms with "
        "the geometric nominal state/feedforward and compare with the next supplied nominal. "
        "Maximum absolute residuals by canonical channel:",
        table(pd.DataFrame([reference_residuals(output, track, ref)])),
        "These diagnose the approximation, not optimizer violations. The reference is "
        "not claimed dynamically exact; APEX still enforces its local shooting dynamics.",
        "## Combined turning and longitudinal demand",
        table(
            pd.DataFrame(
                [
                    {
                        k: v
                        for k, v in measured["combined_demand_observations"].items()
                        if k != "thresholds"
                    }
                ]
            )
        ),
        "Thresholds: abs(estimated ay)>0.3 m/s² and abs(a_cmd)>0.1 m/s².",
        "## Interpretation",
        "The baseline completes two comparable measured laps after launch. "
        "Review the interface and reference-state approximation before Task 007B. Timing tails, "
        "synthetic parameters and perfect state preclude a deployment or near-limit guarantee.",
    ]
    (ROOT / "docs/TASK007A_RESULTS.md").write_text("\n\n".join(sections) + "\n")
