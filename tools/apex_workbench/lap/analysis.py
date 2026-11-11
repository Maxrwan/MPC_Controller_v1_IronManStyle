"""Native-window racing metrics; no interpolation of scientific telemetry or new score."""

import bisect
import copy
import math

from tools.apex_workbench import nmpc_analysis as short

from . import config


def _lap_duration(value):
    """Accept native binary floating scalars without widening global JSON validation."""
    import numpy as np

    if type(value) in (np.float16, np.float32, np.float64):
        value = float(value)  # Exact for these binary formats; JSON receives a built-in scalar.
    if not short.numeric(value) or value <= 0:
        raise ValueError("Invalid native lap-crossing interval")
    return value


def laps(raw, length, initial_s=1.0):
    times, crossings, total = raw.get("lap_times", []), [], 0.0
    first = (int(initial_s / length) + 1) * length
    for index, duration in enumerate(times):
        duration = _lap_duration(duration)
        total += duration
        crossings.append(
            {
                "s_abs_m": first + index * length,
                "time_s": total,
                "complete_circuit": index > 0,
                "interval_s": duration,
            }
        )
    return {
        "track_length_m": length,
        "initial_s_abs_m": initial_s,
        "native_crossings": crossings,
        "completed_laps": max(0, len(times) - 1),
        "lap_time_s": crossings[1]["interval_s"] if len(times) > 1 else None,
        "first_crossing_is_partial": bool(times),
        "status": "complete" if len(times) > 1 else "incomplete",
        "stop_reason": raw.get("stop_reason"),
        "failure": raw.get("failure"),
        "rule": "Native boundary-to-same-boundary interval; partial launch crossing excluded",
    }


def crossing(segments, progress):
    for segment in segments:
        a, b = segment["state_before"][4], segment["state_after"][4]
        if a <= progress <= b and b > a:
            return segment["start"] + (segment["end"] - segment["start"]) * (progress - a) / (b - a)
    return None


def sectors(view, segments):
    length = view["request"]["capture"]["resolved"]["track_length_m"]
    initial = view["request"]["capture"]["resolved"]["initial_state"][4]
    boundary = (int(initial / length) + 1) * length
    result = []
    for index, (a, b) in enumerate(
        zip(config.PROFILE["sectors_fraction"], config.PROFILE["sectors_fraction"][1:])
    ):
        start, end = (
            crossing(segments, boundary + a * length),
            crossing(segments, boundary + b * length),
        )
        states = [
            r
            for r in view["raw"]["states"]
            if boundary + a * length <= r["s_abs"] < boundary + b * length
        ]
        derived = [
            d
            for r, d in zip(view["raw"]["states"], view["presentation"]["states"], strict=True)
            if boundary + a * length <= r["s_abs"] < boundary + b * length
        ]
        controls = [
            r
            for r in view["raw"]["controls"]
            if start is not None and end is not None and start <= r["application_time"] < end
        ]
        plans = [
            p
            for p in view["raw"]["plans"]
            if start is not None and end is not None and start <= p["release_time"] < end
        ]
        result.append(
            {
                "sector": index + 1,
                "phase_start_m": a * length,
                "phase_end_m": b * length,
                "start_time_s": start,
                "end_time_s": end,
                "time_s": end - start if start is not None and end is not None else None,
                "coverage": "complete" if start is not None and end is not None else "incomplete",
                "speed_mps": short.summary([r["vx"] for r in states]),
                "racing_error_m": short.summary([r["racing_error_y_m"] for r in derived]),
                "steering_rad": short.command_metrics(controls, "delta"),
                "preparation_host_s": short.summary([r.get("planner_total_time") for r in plans]),
                "iterations": short.summary([r.get("iterations") for r in plans]),
                "solver_failures": sum(p.get("success") is False for p in plans),
                "maximum_slack_m": max(
                    (p["max_slack"] for p in plans if short.numeric(p.get("max_slack"))),
                    default=None,
                ),
                "slack_observations_available": sum(
                    short.numeric(p.get("max_slack")) for p in plans
                ),
                "slack_observations_missing": sum(
                    not short.numeric(p.get("max_slack")) for p in plans
                ),
                "front_utilization": short.summary([r["front_utilization"] for r in states]),
                "rear_utilization": short.summary([r["rear_utilization"] for r in states]),
            }
        )
    return {
        "rows": result,
        "clock": (
            "Linear progress-crossing time within genuine native integration segments, "
            "same convention as AsyncRunner lap crossings; no interpolated telemetry"
        ),
        "measurement": "First complete finish-line circuit after partial launch crossing",
    }


def metrics(view):
    raw, display = view["raw"], view["presentation"]
    base = short.metrics(view)
    base["requested_duration_s"] = view["request"]["effective"]["maximum_simulation_s"]
    resolved = view["request"]["capture"]["resolved"]
    base["lap"] = laps(raw, resolved["track_length_m"], resolved["initial_state"][4])
    base["yaw_rate_radps"] = short.summary([r["r"] for r in raw["states"]])
    base["body_acceleration_mps2"] = {
        axis: short.summary([r[axis] for r in display["states"]])
        for axis in ("body_ax_mps2", "body_ay_mps2")
    }
    base["chronology_counts"] = {
        k: len(raw.get(k, []))
        for k in ("handoffs", "misses", "fallbacks", "releases", "codriver_misses")
    }
    base["failed_preparations"] = sum(p.get("success") is False for p in raw["plans"])
    if view.get("recovery"):
        base["recovery"] = dict(view["recovery"])
        crossings = base["lap"]["native_crossings"]
        base["complete_circuit_lateral_error_m"] = short.summary(
            [
                r["racing_error_y_m"]
                for r in display["states"]
                if len(crossings) >= 2
                and crossings[0]["time_s"] <= r["time"] < crossings[1]["time_s"]
            ]
        )
    return base


def predictions(view, plan_id):
    packet = next(p for p in view["raw"]["packets"] if p["plan_id"] == plan_id)
    states = view["raw"]["states"]
    times = [row["time"] for row in states]
    result = []
    for time, predicted in zip(packet["timestamps"], packet["states"], strict=True):
        i = bisect.bisect_left(times, time)
        candidates = [j for j in (i - 1, i) if 0 <= j < len(times)]
        i = min(candidates, key=lambda j: abs(times[j] - time)) if candidates else None
        actual = states[i] if i is not None and abs(times[i] - time) <= 1e-9 else None
        result.append(
            {
                "target_time_s": time,
                "actual_native_time_s": actual["time"] if actual else None,
                "predicted": dict(zip(("vx", "vy", "r", "e_psi", "s_abs", "e_y"), predicted)),
                "actual": actual,
                "availability": "native timestamp match (1ns float roundoff only)"
                if actual
                else "not recorded at target timestamp; no interpolation",
            }
        )
    return {
        "plan_id": plan_id,
        "completion_time_s": packet.get("actual_completion_time"),
        "handoffs": [h for h in view["raw"]["handoffs"] if h["plan_id"] == plan_id],
        "nodes": result,
        "meaning": (
            "Nominal prediction versus later realized evolution; "
            "not causal prediction isolation or controller validation"
        ),
    }


def comparison(a, b):
    def conditions(view):
        data = copy.deepcopy(view["request"]["capture"])
        data.pop("producer_sha256", None)  # Presentation source is still independently retained.
        data.pop("runtime", None)

        def scrub(value):
            if isinstance(value, dict):
                return {
                    k: scrub(v)
                    for k, v in value.items()
                    if k not in {"costs", "configuration_id", "version"}
                }
            return [scrub(v) for v in value] if isinstance(value, list) else value

        return scrub(data)

    ma, mb = metrics(a), metrics(b)
    full = a["request"]["effective"]["mode"] == b["request"]["effective"]["mode"] == "full_lap"
    coverage = (
        (ma["lap"]["completed_laps"] == mb["lap"]["completed_laps"] == 1)
        if full
        else (
            a["summary"]["coverage_completed"]
            and b["summary"]["coverage_completed"]
            and a["raw"].get("end_time") == b["raw"].get("end_time")
        )
    )
    controlled = (
        conditions(a) == conditions(b)
        and coverage
        and not a["raw"].get("failure")
        and not b["raw"].get("failure")
        and all(
            v["status"].get("state") == "completed"
            and v["status"].get("scientific_outcome") == "completed"
            and v["status"].get("evidence_state") == "valid"
            and v["status"].get("returncode") == 0
            and not v.get("recovery")
            for v in (a, b)
        )
    )
    return {
        "classification": "Controlled weight comparison / experimental, unqualified"
        if controlled
        else "Noncontrolled comparison: conditions, coverage, source or scheduling differ",
        "configuration_differences": short.differences(
            a["request"]["effective"], b["request"]["effective"]
        ),
        "coverage": "Complete same-phase circuit"
        if full and coverage
        else "Recorded native windows",
        "objective_ranking": "Differently weighted raw objective totals are not performance ranks",
        "interpretation": "A faster lap is not automatically safer or more robust",
    }


def resource_budget(pilot):
    status = pilot["status"]
    if (
        not config.baseline_pilot(pilot["request"]["effective"])
        or not pilot["summary"]["coverage_completed"]
        or pilot["raw"].get("failure")
        or status.get("state") != "completed"
        or status.get("scientific_outcome") != "completed"
        or status.get("evidence_state") != "valid"
        or status.get("returncode") != 0
    ):
        raise ValueError("Full-lap preflight requires the successful exact baseline10s pilot")
    limits = config.limits(config.defaults("full_lap"))
    ratio = 80 / 10
    status, summary = pilot["status"], pilot["summary"]
    estimate = {
        "wall_s": 2 * ratio * status["wall_runtime_s"],
        "cpu_s": 2 * ratio * summary["worker_cpu_s"],
        "sampled_rss_bytes": status["sampled_peak_worker_rss_bytes"]
        + 2 * ratio * summary["retained_native_bytes"],
        "sampled_output_bytes": 2 * ratio * summary["total_recorded_bytes"],
    }
    if not all(math.isfinite(v) and 0 < v <= limits[k] for k, v in estimate.items()):
        raise ValueError("Pilot extrapolation does not fit the declared finite full-lap ceilings")
    return {
        "limits": limits,
        "conservative_extrapolation": estimate,
        "basis": (
            "2x pilot80/10 duration scaling (including fixed startup); RSS adds2x scaled "
            "retained native bytes to observed peak. Investigation bound, not a guarantee."
        ),
        "simulation_ceiling_s": 80,
        "pilot_run": pilot["directory"].name,
    }
