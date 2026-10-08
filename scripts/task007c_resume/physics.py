"""Offline independent-backend and realized-horizon diagnostics, never plant feedback."""

import json
from dataclasses import asdict
from pathlib import Path

import casadi as ca
import numpy as np
import pandas as pd
from task007b.metrics import distribution

from apex.config import load_vehicle_parameters
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.coordinates.angles import wrap_angle
from apex.models.constants import STANDARD_GRAVITY
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track
from apex.state import STATE_NAMES


def variable_step(model):
    """One RK4 step of the existing symbolic law, with frozen interval curvature."""
    x, u, k, h = ca.SX.sym("x", 6), ca.SX.sym("u", 2), ca.SX.sym("k"), ca.SX.sym("h")
    a = model.derivative(x, u, k)
    b = model.derivative(x + h * a / 2, u, k)
    c = model.derivative(x + h * b / 2, u, k)
    d = model.derivative(x + h * c, u, k)
    return ca.Function("diagnostic_step", [x, u, k, h], [x + h * (a + 2 * b + 2 * c + d) / 6])


def prediction_errors(states, packets):
    """Realized future versus retained nominal packet: includes replans and changed controls."""
    times = states.time.to_numpy()
    actual = states[list(STATE_NAMES)].to_numpy()
    actual[:, 3] = np.unwrap(actual[:, 3])
    rows = []
    for packet in packets:
        predictions = np.asarray(packet["states"])
        stamp = np.asarray(packet["timestamps"])
        if predictions.shape != (len(stamp), 6):
            raise ValueError("Unexpected packet state ordering")
        for step, (t, predicted) in enumerate(zip(stamp, predictions)):
            if t < times[0] or t > times[-1]:
                continue  # No extrapolation or invented post-termination state.
            observed = np.array([np.interp(t, times, actual[:, j]) for j in range(6)])
            error = observed - predicted
            error[3] = wrap_angle(error[3])
            rows.append(
                dict(
                    plan_id=packet["plan_id"],
                    step=step,
                    time=t,
                    horizon_offset=t - stamp[0],
                    prediction_s_abs=predicted[4],
                    **dict(zip(STATE_NAMES, error.tolist())),
                )
            )
    return pd.DataFrame(rows)


def export(folder):
    folder = Path(folder)
    state = pd.read_csv(folder / "states.csv", float_precision="round_trip")
    track, _, identity = load_track(folder / "fixture/track_source.json")
    ref = PlanningReference(folder / "fixture", track, identity, feasibility_policy="advisory")
    p = load_vehicle_parameters("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    symbolic = SymbolicBicycle(p, RACING_TIRE_PHYSICS)
    transition = variable_step(symbolic)
    rows = []
    x = state[list(STATE_NAMES)].to_numpy()
    u = state[["delta", "a_cmd"]].to_numpy()
    for i, (time, xx, uu) in enumerate(zip(state.time, x, u)):
        d = plant.diagnostics(xx, uu)
        dx = plant.derivative(xx, uu)
        sx = np.asarray(symbolic.derivative(xx, uu, d.curvature)).ravel()
        goal = ref.sample(xx[4])
        row = dict(
            time=time,
            progress=xx[4] % track.length,
            **dict(zip(STATE_NAMES, xx)),
            delta=uu[0],
            **asdict(d),
        )
        row.update(
            ay_force=(d.fyf + d.fyr) / p.mass,
            ay_balance=dx[1] + xx[2] * xx[0],
            beta=np.arctan2(xx[1], xx[0]),
            yaw_pseudo_reference=xx[0] * goal["kappa_ref_1pm"],
            normalized_lateral_demand=abs((d.fyf + d.fyr) / p.mass) / (d.mu * STANDARD_GRAVITY),
            normalized_front_x=d.fx_front / (d.mu * d.fzf),
            normalized_front_y=d.fyf / (d.mu * d.fzf),
            normalized_rear_x=d.fx_rear / (d.mu * d.fzr),
            normalized_rear_y=d.fyr / (d.mu * d.fzr),
        )
        row.update(
            {"derivative_residual_" + k: float(a - b) for k, a, b in zip(STATE_NAMES, sx, dx)}
        )
        if i + 1 < len(x):
            dt = state.time.iloc[i + 1] - time
            prediction = np.asarray(transition(xx, uu, d.curvature, dt)).ravel()
            err = x[i + 1] - prediction
            err[3] = wrap_angle(err[3])
            row["step_dt"] = dt
            row.update({"one_step_" + k: float(v) for k, v in zip(STATE_NAMES, err)})
        rows.append(row)
    frame = pd.DataFrame(rows)
    # Actual samples include close event times. Exclude derivative stencils crossing input jumps
    # or extremely short intervals from the primary finite-difference consistency summary.
    frame["ay_finite_difference"] = (
        np.gradient(frame.vy, frame.time, edge_order=2) + frame.r * frame.vx
    )
    frame["ay_fd_error"] = frame.ay_finite_difference - frame.ay_force
    steps = np.diff(frame.time)
    valid = np.zeros(len(frame), dtype=bool)
    valid[1:-1] = (
        (np.minimum(steps[:-1], steps[1:]) > 1e-6)
        & np.all(u[:-2] == u[1:-1], axis=1)
        & np.all(u[1:-1] == u[2:], axis=1)
    )
    frame["fd_smooth_stencil"] = valid
    frame["low_slip"] = np.maximum(abs(frame.alpha_f), abs(frame.alpha_r)) < 0.03
    frame.to_csv(folder / "physics_telemetry.csv", index=False)
    errors = prediction_errors(state, json.loads((folder / "trajectory_packets.json").read_text()))
    handoffs = json.loads((folder / "events.json").read_text())["handoffs"]
    status = {h["plan_id"]: "accepted" if h["accepted"] else "rejected" for h in handoffs}
    status[0] = "accepted"  # Gated startup packet.
    errors["packet_status"] = errors.plan_id.map(status).fillna("pending")
    errors["handoff_accepted"] = errors.packet_status == "accepted"
    errors.to_csv(folder / "horizon_prediction_error.csv", index=False)
    report = dict(
        schema_version=2,
        synthetic_only=True,
        prediction_rows_by_packet_status=errors.packet_status.value_counts().to_dict(),
        derivative_residual={
            k: distribution(frame["derivative_residual_" + k]) for k in STATE_NAMES
        },
        one_step_residual={k: distribution(frame["one_step_" + k]) for k in STATE_NAMES},
        ay_force_balance=distribution(frame.ay_balance - frame.ay_force),
        ay_finite_difference_all=distribution(frame.ay_fd_error),
        ay_finite_difference_smooth=distribution(frame.loc[valid, "ay_fd_error"]),
        fd_smooth_count=int(valid.sum()),
        low_slip_definition=(
            "max(abs(alpha_f),abs(alpha_r)) < 0.03 rad; descriptive split, not a safety threshold"
        ),
        yaw_comparison={
            name: distribution(frame.loc[mask, "r"] - frame.loc[mask, "yaw_pseudo_reference"])
            for name, mask in [
                ("low_slip", frame.low_slip),
                ("high_slip_or_transient", ~frame.low_slip),
            ]
        },
        horizon_errors={
            str(step): {k: distribution(group[k]) for k in ["vx", "vy", "r", "e_psi", "e_y"]}
            for step, group in errors[errors.handoff_accepted].groupby("step")
        },
        horizon_errors_all_prepared={
            str(step): {k: distribution(group[k]) for k in ["vx", "vy", "r", "e_psi", "e_y"]}
            for step, group in errors.groupby("step")
        },
        caveats=[
            "Independent CasADi and NumPy derivative transcriptions evaluated at "
            "identical state/input/curvature.",
            "One-step symbolic map freezes starting curvature; physical plant "
            "reevaluates curvature at RK4 stages. Actual held command and event step "
            "retained.",
            "Finite differences on nonuniform event grids are sensitive near input "
            "switches; primary subset excludes crossing jumps and dt <=1 microsecond.",
            "Future actual states use linear temporal interpolation with unwrapped "
            "heading and no extrapolation. Horizon error includes later replans, TVLQR "
            "feedback and forecast/preview differences; it is not pure model error.",
            "Primary horizon_errors use accepted packets only. All prepared, rejected and "
            "pending packet samples remain in the CSV and all-prepared companion summary.",
            "No real-vehicle validation; parameters remain explicitly synthetic.",
        ],
    )
    (folder / "physics_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    return frame, errors, report
