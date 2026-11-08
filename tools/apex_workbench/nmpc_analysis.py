"""Descriptive, sample-based control analysis; no controller execution or certification."""

import copy
import math
from statistics import mean


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def summary(values):
    values = [v for v in values if numeric(v)]
    return {
        "samples": len(values),
        "peak_abs": max(map(abs, values), default=None),
        "rms": math.sqrt(mean(v * v for v in values)) if values else None,
        "mean": mean(values) if values else None,
    }


def settling(rows, *, start_s, band_m=0.01, minimum_tail_s=0.25):
    """First native sample whose entire observed tail stays in a user-specified zero-error band."""
    if (
        not all(numeric(v) for v in (start_s, band_m, minimum_tail_s))
        or min(band_m, minimum_tail_s) <= 0
    ):
        raise ValueError("Analysis band and observed-tail duration must be finite positive")
    if any(not numeric(r["time"]) or not numeric(r["racing_error_y_m"]) for r in rows):
        raise ValueError("Nonfinite recorded response")
    samples = [(r["time"], r["racing_error_y_m"]) for r in rows if r["time"] >= start_s]
    result = {
        "band_m": band_m,
        "minimum_observed_tail_s": minimum_tail_s,
        "target_error_m": 0.0,
        "settling_time_s": None,
        "definition": (
            "Observed within-window settling of racing-reference lateral "
            "error; not future stability"
        ),
    }
    if any(not numeric(t) or not numeric(e) for t, e in samples):
        raise ValueError("Nonfinite recorded response")
    if any(b[0] <= a[0] for a, b in zip(samples, samples[1:])):
        raise ValueError("Response timestamps must increase")
    if not samples or samples[-1][0] - start_s < minimum_tail_s:
        return {**result, "status": "insufficient observation window"}
    for i, (time, _) in enumerate(samples):
        if samples[-1][0] - time >= minimum_tail_s and all(
            abs(e) <= band_m for _, e in samples[i:]
        ):
            return {
                **result,
                "status": "observed within-window settling",
                "settling_time_s": time - start_s,
            }
    return {**result, "status": "settling not established in this window"}


def command_metrics(rows, channel):
    applied = [
        (r["application_time"], r[channel])
        for r in rows
        if numeric(r.get("application_time")) and numeric(r.get(channel))
    ]
    increments = [abs(b[1] - a[1]) for a, b in zip(applied, applied[1:])]
    rates = [abs(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(applied, applied[1:]) if b[0] > a[0]]
    return {
        **summary([v for _, v in applied]),
        "total_variation": sum(increments),
        "maximum_observed_increment_rate": max(rates, default=None),
        "application_window_s": [applied[0][0], applied[-1][0]] if applied else None,
        "rows_without_applied_measurement": len(rows) - len(applied),
    }


def metrics(view, *, band_m=0.01, minimum_tail_s=0.25):
    raw, display = view["raw"] or {}, view["presentation"] or {}
    rows = display.get("states", [])
    native = raw.get("states", [])
    if len(rows) != len(native) or any(a["time"] != b["time"] for a, b in zip(rows, native)):
        raise ValueError("Derived racing errors must match original state samples exactly")
    controls, plans = raw.get("controls", []), raw.get("plans", [])
    errors = [r["racing_error_y_m"] for r in rows]
    signs = [1 if x > 0 else -1 for x in errors if x != 0]
    kick = display.get("applied_disturbances", [])
    start = kick[0]["application_time_s"] if len(kick) == 1 else (rows[0]["time"] if rows else 0)
    response = settling(rows, start_s=start, band_m=band_m, minimum_tail_s=minimum_tail_s)
    utilization = {
        side: summary([r.get(side + "_utilization") for r in native]) for side in ("front", "rear")
    }
    return {
        "definition": (
            "Equal-weight RMS over actual recorded samples in the displayed "
            "native window; no resampling"
        ),
        "observation_window_s": [rows[0]["time"], rows[-1]["time"]] if rows else None,
        "requested_duration_s": 2.0,
        "native_end_time_s": raw.get("end_time"),
        "stop_reason": raw.get("stop_reason"),
        "failure": raw.get("failure"),
        "racing_lateral_error_m": summary(errors),
        "racing_heading_error_rad": summary([r["racing_error_heading_rad"] for r in rows]),
        "centerline_e_y_m": summary([r["e_y"] for r in native]),
        "active_packet_lateral_error_m": summary([r.get("error_e_y") for r in controls]),
        "observed_lateral_zero_crossings": sum(a != b for a, b in zip(signs, signs[1:])),
        "steering_rad": command_metrics(controls, "delta"),
        "longitudinal_a_cmd_mps2": command_metrics(controls, "a_cmd"),
        "solver_host_seconds": summary([r.get("solve_time") for r in plans]),
        "preparation_host_seconds": summary([r.get("planner_total_time") for r in plans]),
        "iterations": summary([r.get("iterations") for r in plans]),
        "successful_native_preparations": sum(r.get("success") is True for r in plans),
        "preparation_count": len(plans),
        "max_native_slack": max(
            (r["max_slack"] for r in plans if numeric(r.get("max_slack"))), default=None
        ),
        "max_primal_infeasibility": max(
            (r["primal_infeasibility"] for r in plans if numeric(r.get("primal_infeasibility"))),
            default=None,
        ),
        "grip_utilization": utilization,
        "minimum_combined_utilization_margin": {
            side: (1 - value["peak_abs"] if value["peak_abs"] is not None else None)
            for side, value in utilization.items()
        },
        "recorded_boundary_violation_rows": sum(
            r.get("boundary_violation") is True for r in native
        ),
        "requested_applied_steering_differences": sum(
            numeric(r.get("delta"))
            and numeric(r.get("requested_delta"))
            and r["delta"] != r["requested_delta"]
            for r in controls
        ),
        "settling": response,
        "disturbance_recovery": response
        if len(kick) == 1
        else {"status": "No single recorded disturbance application"},
        "disturbance_response": {
            "before": summary([r["racing_error_y_m"] for r in rows if r["time"] < start]),
            "after": summary([r["racing_error_y_m"] for r in rows if r["time"] >= start]),
        }
        if len(kick) == 1
        else None,
        "overshoot": {
            "value": None,
            "reason": (
                "No steady reference-step experiment; do not assign step overshoot "
                "to a state perturbation"
            ),
        },
    }


def linear_indicators(record):
    import numpy as np

    if (
        record.get("state_order") != ["e_y", "e_psi", "vy", "r"]
        or record.get("feedback") != "u = nominal - K @ error"
        or record.get("dt_s") != 0.01
    ):
        raise ValueError("Local linearization ordering, feedback sign or discretization differs")
    rows = record.get("rows", [])
    if not rows:
        return {"status": "Native Jacobian/gain associations unavailable", "rows": []}
    product, previous_k, previous_time = np.eye(4), None, None
    result = []
    for row in rows:
        a, b, k = (np.asarray(row[name], dtype=float) for name in ("A", "B", "K"))
        if (
            a.shape != (4, 4)
            or b.shape != (4, 1)
            or k.shape != (1, 4)
            or not all(np.isfinite(v).all() for v in (a, b, k))
        ):
            raise ValueError("Malformed native local matrices")
        if not numeric(row["time"]) or (
            previous_time is not None
            and not math.isclose(
                row["time"] - previous_time, record["dt_s"], rel_tol=0, abs_tol=1e-9
            )
        ):
            raise ValueError("Local matrix schedule timestamp/discretization mismatch")
        f = a - b @ k
        eigenvalues = np.linalg.eigvals(f)
        product = f @ product
        result.append(
            {
                "time": row["time"],
                "spectral_radius": float(max(abs(eigenvalues))),
                "eigenvalues_real_imag": [[float(v.real), float(v.imag)] for v in eigenvalues],
                "finite_horizon_amplification_2norm": float(np.linalg.norm(product, 2)),
                "gain_change_2norm": float(np.linalg.norm(k - previous_k))
                if previous_k is not None
                else None,
            }
        )
        previous_k, previous_time = k, row["time"]
    return {
        "status": "Local nominal-packet lateral indicators only",
        "rows": result,
        "definition": (
            "F=A-BK; chronological product F_last ... F_first; Euclidean norm "
            "uses mixed SI coordinates"
        ),
        "limitations": (
            "Instantaneous eigenvalues do not prove "
            "time-varying/nonlinear/hybrid stability. Clamps, handoffs and "
            "longitudinal coupling are excluded."
        ),
    }


def differences(a, b, prefix=""):
    if type(a) is dict and type(b) is dict:
        return [
            item
            for key in sorted(set(a) | set(b))
            for item in differences(a.get(key), b.get(key), prefix + "/" + key)
        ]
    return [] if a == b else [{"field": prefix, "left": a, "right": b}]


def comparison(a, b):
    left, right = [v["request"]["scratch_capture"] for v in (a, b)]
    snapshots = []
    for capture in (left, right):
        snapshot = copy.deepcopy(capture["resolved"])
        snapshot.pop("effective", None)
        snapshot["configuration"].pop("costs")
        snapshots.append(snapshot)
    common = (
        left["source"] == right["source"]
        and left["source_sha256"] == right["source_sha256"]
        and left["environment"] == right["environment"]
        and snapshots[0] == snapshots[1]
    )
    windows = [[r["time"] for r in (v["presentation"] or {}).get("states", [])] for v in (a, b)]
    common = common and windows[0] == windows[1] and bool(windows[0])
    compatible_disturbance = (a["presentation"] or {}).get("applied_disturbances") == (
        b["presentation"] or {}
    ).get("applied_disturbances")
    return {
        "classification": "Controlled cost-configuration comparison / experimental, unqualified"
        if common
        else "Illustrative comparison: scenario, source, environment or coverage differs",
        "configuration_differences": differences(
            a["request"]["effective"], b["request"]["effective"]
        ),
        "recovery_metrics_comparable": compatible_disturbance,
        "objective_note": "Raw totals from different cost weights are not performance rankings",
        "timing_note": "Simulated application clocks and host solver durations remain separate",
    }
