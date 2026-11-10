"""Presentation adapters over existing verified readers; no scientific execution/imports."""

import bisect
import csv
import hashlib
import io
import json
import math
from functools import lru_cache

from tools.apex_workbench import nmpc_scratch as transient
from tools.apex_workbench import nmpc_scratch_panels as short
from tools.apex_workbench import scratch_replay, storage

from . import analysis, evidence, panels

BASE_DELIVERY = "afa85389ccdb532816702f0ab5d3a4a49e54918f"
REFERENCE = "configs/planning/task007b/gamma_2p000/planning_reference.csv"
MAX_SAMPLES = 4096
MAX_PACKETS = 512
MAX_PAYLOAD_BYTES = 8 * 2**20


def recordings(family=None):
    roots = [("V2", panels.records()), ("Transient", short.records())]
    return [
        {"family": kind, "directory": path}
        for kind, paths in roots
        for path in paths
        if (family is None or kind == family) and not path.is_symlink()
    ]


def label(record):
    try:
        request = storage.read_json(record["directory"] / "request.json")
        value = request["effective"]
        selected = value["scratch"] if record["family"] == "V2" else value
        name = selected["configuration_id"].replace("_", " ")
        duration = value["maximum_simulation_s"] if record["family"] == "V2" else 2
        return (
            f"{name.title()} · {duration:g} s · {record['family']} · "
            f"{record['directory'].name[:19]}"
        )
    except (OSError, ValueError, KeyError, TypeError):
        return record["directory"].name + " · metadata unavailable"


def read(record):
    if record["family"] == "V2":
        view = evidence.read_run(record["directory"])
        if "raw" in view:
            view["packets"] = [
                {"plan_id": packet["plan_id"], "packet": packet, "prediction_xy": xy}
                for packet, xy in zip(
                    view["raw"]["packets"],
                    evidence.rows(view, "prediction_xy", "derived"),
                    strict=True,
                )
            ]
    elif record["family"] == "Transient":
        view = transient.read_run(record["directory"])
    else:
        raise ValueError("Unsupported recording family")
    view["ui_family"] = record["family"]
    return view


def current(view):
    evidence.current(view) if view["ui_family"] == "V2" else transient.current(view)


def capture(view):
    return view["request"]["capture" if view["ui_family"] == "V2" else "scratch_capture"]


def windows(view):
    """Overlapping native windows cover every observation; never resample state/control data."""
    times = [row["time"] for row in view["raw"]["states"]]
    if (
        len(times) < 2
        or any(not scratch_replay.finite(t) for t in times)
        or any(b <= a for a, b in zip(times, times[1:]))
    ):
        raise ValueError("Native recording has insufficient or nonincreasing time coverage")
    result, start = [], 0
    while start < len(times) - 1:
        end = min(bisect.bisect_right(times, times[start] + 10), start + MAX_SAMPLES, len(times))
        if end <= start + 1:
            raise ValueError("Native time gap exceeds the bounded replay window")
        result.append((start, end))
        start = end - 1
    return result


def window(view, selected):
    start, end = selected
    if (
        type(start) is not int
        or type(end) is not int
        or not 0 <= start < end - 1 <= len(view["raw"]["states"]) - 1
    ):
        raise ValueError("Invalid native replay window")
    if end - start > MAX_SAMPLES:
        raise ValueError("Select a bounded native replay window")
    return {
        **view,
        "raw": {**view["raw"], "states": view["raw"]["states"][start:end]},
        "presentation": {
            **view["presentation"],
            "states": view["presentation"]["states"][start:end],
        },
        "ui_full_count": len(view["raw"]["states"]),
    }


@lru_cache(maxsize=4)
def reference(source, expected):
    """Immutable Git blob, bound to the original execution's scientific-source inventory."""
    content = transient.frozen.git("show", source + ":" + REFERENCE)
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("Recorded Planning reference source hash differs")
    result = [
        [float(row["x_ref_m"]), float(row["y_ref_m"])]
        for row in csv.DictReader(io.StringIO(content.decode()))
    ]
    if not result or any(not all(map(math.isfinite, row)) for row in result):
        raise ValueError("Recorded Planning reference XY unavailable")
    return result


def payload(view):
    base = scratch_replay.payload(view)
    for displayed, source, derived in zip(
        base["states"], view["raw"]["states"], view["presentation"]["states"], strict=True
    ):
        if not scratch_replay.finite(source.get("delta")):
            raise ValueError("Recorded held front steering is unavailable")
        for key in ("front_utilization", "rear_utilization", "boundary_violation"):
            displayed[key] = source.get(key)
        for key in ("body_ax_mps2", "body_ay_mps2"):
            displayed[key] = derived.get(key)
    for displayed, source in zip(base["controls"], view["raw"].get("controls", []), strict=True):
        displayed["nominal_delta"] = source.get("nominal_delta")
        displayed["plan_id"] = source.get("plan_id")
    start, end = base["states"][0]["time"], base["states"][-1]["time"]
    controls = base["controls"]
    if controls:
        lower = min(
            max(0, bisect.bisect_right([r[k] for r in controls], start) - 1)
            for k in ("time", "application_time")
        )
        upper = max(
            bisect.bisect_right([r[k] for r in controls], end) for k in ("time", "application_time")
        )
        base["controls"] = controls[lower:upper]
    active_ids = {state["plan_id"] for state in base["states"]}
    base["packets"] = [
        p
        for p in base["packets"]
        if p["id"] in active_ids or p["times"][0] <= end and p["times"][-1] >= start
    ]
    if len(base["states"]) > MAX_SAMPLES or len(base["packets"]) > MAX_PACKETS:
        raise ValueError("Recording requires a smaller display window")
    recorded = capture(view)
    length = view["presentation"]["geometry"][-1].get("s")
    if not scratch_replay.finite(length) or length <= 0:
        raise ValueError("Recorded canonical track length unavailable")
    if recorded["resolved"].get("track_length_m", length) != length:
        raise ValueError("Recorded track-length sources disagree")
    initial = recorded["resolved"]["initial_state"][4]
    laps = analysis.laps(view["raw"], length, initial)
    ref_hash = recorded["source_sha256"].get(REFERENCE)
    base["planning_reference"] = (
        reference(view["request"]["effective"]["scientific_source"], ref_hash) if ref_hash else []
    )
    base["meta"] = {
        "track_length_m": length,
        "initial_s_abs_m": initial,
        "horizon": recorded["resolved"]["configuration"]["horizon"],
        "reference_source_sha256": ref_hash,
        "reference_label": "Retained offline Planning nodes; not new optimizer samples",
        "lap_crossings": laps["native_crossings"],
        "native_samples_total": view.get("ui_full_count", len(base["states"])),
        "classification": "Synthetic / experimental / unqualified",
        "front_angle_source": (
            "Latest actual application event; initial held native angle before first application"
        ),
        "nominal_source": (
            "Native tracking nominal associated with the applied request; not an applied command"
        ),
    }
    if view["ui_family"] == "V2":
        base["meta"]["sectors"] = [
            {k: row[k] for k in ("sector", "coverage", "start_time_s", "end_time_s", "time_s")}
            for row in analysis.sectors(view, evidence.rows(view, "segments", "journal"))["rows"]
        ]
    else:
        base["meta"]["sectors"] = []
    if len(json.dumps(base, allow_nan=False, separators=(",", ":")).encode()) > MAX_PAYLOAD_BYTES:
        raise ValueError("Display payload exceeds the bounded transport limit")
    current(view)
    return base


def full_lap_gate():
    """Retained budget decision, explicitly historical; never an execution override."""
    record = json.loads(
        transient.frozen.git("show", BASE_DELIVERY + ":docs/workbench_v2_lap/work_record.json")
    )
    return record["full_lap_resource_preflight"]
