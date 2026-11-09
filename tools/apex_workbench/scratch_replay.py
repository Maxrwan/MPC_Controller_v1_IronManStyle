"""Verified, read-only replay payload and a small browser component; no scientific imports."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from time import monotonic_ns

import streamlit as st
from streamlit.components.v1 import declare_component

from tools.apex_workbench import nmpc_scratch as scratch

ASSETS = Path(__file__).with_name("scratch_replay_web")


def finite(value):
    import math

    return type(value) in (int, float) and math.isfinite(value)


def point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or not all(map(finite, value)):
        raise ValueError("Malformed recorded global position")
    return list(value)


def payload(view):
    """Copy only display channels from the already verified buffers, with exact native clocks."""
    raw, display = view["raw"], view["presentation"]
    if not raw or not display or not raw.get("states"):
        raise ValueError("Native trajectory unavailable; partial journals remain retained")
    rows, native = display["states"], raw["states"]
    if len(rows) != len(native):
        raise ValueError("Recorded display/native sample coverage differs")
    states = []
    for i, (row, source) in enumerate(zip(rows, native, strict=True)):
        time = row["time"]
        if not finite(time) or time != source["time"] or (i and time <= rows[i - 1]["time"]):
            raise ValueError("Recorded native sample timestamps differ or do not increase")
        position = point([row["x"], row["y"]])
        states.append(
            {
                "time": time,
                "x": position[0],
                "y": position[1],
                **{
                    k: source.get(k)
                    for k in (
                        "vx",
                        "vy",
                        "r",
                        "e_psi",
                        "s_abs",
                        "e_y",
                        "delta",
                        "a_cmd",
                        "plan_id",
                        "mode",
                    )
                },
                "error_y": row["racing_error_y_m"],
            }
        )
    packets = []
    scheduled = {p["plan_id"]: p for p in raw["packets"]}
    for observed in view["packets"]:
        p = observed.get("packet")
        if p is None:
            continue
        times, xs, us = (p[k] for k in ("timestamps", "states", "controls"))
        if (
            len(xs) != len(times)
            or len(us) != len(xs) - 1
            or not times
            or any(not finite(t) for t in times)
            or any(b <= a for a, b in zip(times, times[1:]))
            or any(len(x) != 6 or not all(map(finite, x)) for x in xs)
            or any(len(u) != 2 or not all(map(finite, u)) for u in us)
        ):
            raise ValueError("Malformed retained solver horizon")
        xy = [point(v) for v in observed["prediction_xy"]]
        reference = [point(v) for v in observed.get("reference_xy") or []]
        if len(xy) != len(xs) or (reference and len(reference) != len(xs)):
            raise ValueError("Prediction/reference position coverage differs")
        final = scheduled.get(observed["plan_id"], {})
        plan = next((r for r in raw["plans"] if r.get("plan_id") == observed["plan_id"]), {})
        packets.append(
            {
                "id": observed["plan_id"],
                "times": times,
                "states": xs,
                "controls": us,
                "xy": xy,
                "reference": reference,
                "completion": final.get("actual_completion_time"),
                "valid": final.get("valid"),
                "reason": final.get("validation_reason"),
                "diagnostics": {
                    k: plan.get(k)
                    for k in (
                        "status",
                        "iterations",
                        "primal_infeasibility",
                        "max_slack",
                        "solve_time",
                        "planner_total_time",
                        "objective_components",
                        "predicted_completion_time",
                        "completion_time",
                        "prediction_error",
                    )
                },
                "handoffs": [h for h in raw["handoffs"] if h.get("plan_id") == observed["plan_id"]],
            }
        )
    controls = []
    for c in raw.get("controls", []):
        if not finite(c.get("time")) or not finite(c.get("application_time")):
            raise ValueError("Recorded command clocks unavailable")
        controls.append(
            {
                k: c.get(k)
                for k in (
                    "time",
                    "application_time",
                    "delta",
                    "a_cmd",
                    "requested_delta",
                    "requested_a_cmd",
                )
            }
        )
    if any(
        b["time"] < a["time"] or b["application_time"] < a["application_time"]
        for a, b in zip(controls, controls[1:])
    ):
        raise ValueError("Recorded command clocks do not increase")
    geometry = display["geometry"]
    if len(geometry) < 2:
        raise ValueError("Canonical track geometry unavailable")
    result = {
        "run_id": view["directory"].name,
        "states": states,
        "packets": packets,
        "controls": controls,
        "track": {
            name: [point([r[x], r[y]]) for r in geometry]
            for name, x, y in (
                ("center", "x", "y"),
                ("left", "left_x", "left_y"),
                ("right", "right_x", "right_y"),
            )
        },
        "jumps": [d["application_time_s"] for d in display.get("applied_disturbances", [])],
        "coverage": {
            "samples": len(states),
            "native_end_time_s": raw.get("end_time"),
            "stop_reason": raw.get("stop_reason"),
            "failure": raw.get("failure"),
        },
    }
    json.dumps(result, allow_nan=False)
    scratch.current(view)
    return result


@lru_cache(maxsize=1)
def component():
    return declare_component("apex_scratch_native_replay", path=str(ASSETS))


def replay(view):
    key = "native_replay_" + view["directory"].name
    quarantine_key = key + "_quarantine"
    if st.session_state.get(quarantine_key):
        st.error(st.session_state[quarantine_key])
        if st.button("Reopen verified recording", key=key + "_reopen"):
            del st.session_state[quarantine_key]
            st.session_state.pop(key + "_ack", None)
            st.rerun()
        return
    data = payload(view)
    epoch = hashlib.sha256(json.dumps(view["anchor"], sort_keys=True).encode()).hexdigest()

    @st.fragment(run_every=1.0)
    def present():
        try:
            scratch.current(view)
            # Acknowledged data stays in the browser; only its epoch/validity is resent.
            ack = st.session_state.get(key + "_ack")
            result = component()(
                payload=data if ack != epoch else None,
                epoch=epoch,
                valid=True,
                error=None,
                heartbeat=monotonic_ns(),  # Ensure identical validity messages are not elided.
                key=key,
                default=None,
            )
            scratch.current(view)
            if isinstance(result, dict):
                st.session_state[key + "_ack"] = (
                    epoch if result.get("epoch") == epoch and result.get("loaded") is True else None
                )
        except (OSError, ValueError, RuntimeError) as problem:
            st.session_state[quarantine_key] = "Evidence changed or unavailable: " + str(problem)
            # Full rerun unmounts the component. The latch blocks automatic re-admission,
            # even if the original bytes are restored before the next validation boundary.
            st.rerun()

    present()
