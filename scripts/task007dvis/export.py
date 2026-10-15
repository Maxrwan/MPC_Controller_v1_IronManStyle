"""Versioned provisional scientific exports; raw evidence is never rewritten."""

import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

from apex.state import STATE_NAMES
from task007dvis.interface import (
    REQUEST_COVERAGE,
    SCHEMA,
    authority_intervals,
    event_rows,
    missing_reasons,
)


def write(path, value):
    def convert(v):
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, np.generic):
            return v.item()
        raise TypeError(f"Unsupported scientific JSON value: {type(v).__name__}")

    # Serialize before creating the exclusive file: never leave a partial JSON document.
    text = json.dumps(value, indent=2, default=convert, allow_nan=False) + "\n"
    with path.open("x") as stream:
        stream.write(text)


def hashes(paths):
    return {
        str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths if Path(p).is_file()
    }


def csv_rows(path, rows, columns=()):
    keys = list(dict.fromkeys([*columns, *(k for r in rows for k in r)]))
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {k: json.dumps(v) if isinstance(v, (dict, list, tuple)) else v for k, v in r.items()}
            for r in rows
        )


def flatten(value, prefix=""):
    out = {}
    for key, v in value.items():
        name = prefix + key
        if isinstance(v, dict):
            out.update(flatten(v, name + "."))
        elif not isinstance(v, list):
            out[name] = v
    return out


def export(folder, raw, segments, rows, cycles, report, summary, fixture, *, output=None):
    out = folder / "scientific" if output is None else output
    out.mkdir(exist_ok=False, parents=True)
    run_id = summary["case"]
    architecture = summary["spec"]["architecture"]
    availability = {}

    def emit(name, data, columns=(), provenance="native"):
        exported = [
            dict(
                {
                    "run_id": run_id,
                    "export_row": i,
                    "sample_provenance": provenance,
                    "missing_reasons": missing_reasons(r, architecture),
                    **r,
                }
            )
            for i, r in enumerate(data)
        ]
        csv_rows(
            out / (name + ".csv"),
            exported,
            columns=("run_id", "export_row", "sample_provenance", "missing_reasons", *columns),
        )
        availability[name] = dict(
            status="available" if data else "empty",
            reason=None if data else "no_events_in_coverage",
        )

    emit(
        "states",
        rows,
        ("time", *STATE_NAMES, "delta", "a_cmd", "plan_id", "applied_source_plan_id"),
    )
    emit("segments", segments, ("start", "end", "dt", "state_before", "state_after", "control"))
    emit(
        "controls",
        raw["controls"],
        (
            "time",
            "application_time",
            "plan_id",
            "requested_delta",
            "requested_a_cmd",
            "delta",
            "a_cmd",
        ),
    )
    emit("cycles", cycles, ("plan_id", "t_release", "t_ready", "valid_from", "t_accept", "status"))
    if "reserves" in raw:
        emit("reserves", raw["reserves"], ("time", "reserve"))
    else:
        availability["reserves"] = dict(status="unavailable", reason="not_recorded")
    emit(
        "boundaries",
        report["coverage"]["crossings"],
        ("s_abs", "time", "method", "bracket_start", "bracket_end"),
        "reconstructed",
    )
    emit(
        "metrics",
        [
            dict(
                flatten(w),
                metric_definition_id="vis1.native_window.v1",
                aggregation_scope=w["kind"],
            )
            for w in report["windows"]
        ],
        ("kind", "index", "status", "metric_definition_id", "aggregation_scope"),
        "reconstructed",
    )
    emit(
        "events",
        event_rows(raw),
        ("time", "phase", "within_phase_order", "source_stream", "source_row", "event_kind"),
    )
    write(out / "packets.json", raw["packets"])
    shutil.copytree(fixture, out / "fixture")
    shutil.copyfile(fixture / "planning_reference.csv", out / "planning.csv")
    artifacts = {}
    for path in sorted(out.rglob("*")):
        if path.is_file():
            count = None
            if path.suffix == ".csv":
                with path.open(newline="") as f:
                    count = sum(1 for _ in csv.DictReader(f))
            artifacts[str(path.relative_to(out))] = dict(
                sha256=hashes([path])[str(path)], bytes=path.stat().st_size, rows=count
            )
    cycle_status = {c["plan_id"]: c["status"] for c in cycles}
    manifest = dict(
        schema=SCHEMA,
        review_status="candidate_pending_representative_Workbench_ingestion",
        run_id=run_id,
        architecture=architecture,
        status=(
            "incomplete_duration"
            if raw["stop_reason"] == "duration" and summary["spec"]["phase"] != "parity"
            else "completed"
            if not report["stop_gate"]
            else "stopped_gate"
        ),
        termination=dict(
            reason=raw["stop_reason"],
            failure=raw["failure"],
            stop_gate=report["stop_gate"],
            simulated_end=raw.get("end_time"),
            native_start=rows[0]["time"] if rows else None,
            native_end=rows[-1]["time"] if rows else None,
            intended_duration=summary.get("simulation", {}).get("duration"),
            requested_crossings=summary.get("simulation", {}).get("laps"),
        ),
        coverage=report["coverage"],
        canonical_state=list(STATE_NAMES),
        state_units=["m/s", "m/s", "rad/s", "rad", "m", "m"],
        controls=["delta", "a_cmd"],
        control_units=["rad", "m/s^2"],
        clock="simulated physical seconds; host timings separate",
        a_cmd="Fx/m, not dvx/dt",
        geometry=dict(
            position="x=c_x(s)-e_y*sin(psi_c); y=c_y(s)+e_y*cos(psi_c)",
            heading="psi_world=psi_c(s)+e_psi",
            s="unwrapped centerline arc length; geometry uses s modulo L",
            frame="world XY metres, CCW radians, Frenet left positive",
            source="hashed fixture/track_source.json; existing periodic centerline",
        ),
        request_coverage=REQUEST_COVERAGE,
        accepted_authority_intervals=authority_intervals(raw),
        packet_status={
            str(p["plan_id"]): cycle_status.get(
                p["plan_id"], "startup" if p["plan_id"] == 0 else "prepared_pending"
            )
            for p in raw["packets"]
        },
        provenance=dict(
            scientific_revision=summary["git_sha"],
            scientific_source_sha256=summary["source_sha256"],
            export_revision=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            export_source_sha256=hashes(Path("scripts/task007dvis").glob("*.py")),
            dirty_status=subprocess.check_output(["git", "status", "--short"], text=True),
            evidence_kind=summary.get("evidence_kind", "scientific_run"),
        ),
        fixture_sha256=summary["fixture_sha256"],
        raw_sha256=summary.get(
            "raw_sha256",
            hashes(folder / p for p in ["raw.json", "segments.json", "release_contexts.json"]),
        ),
        artifacts=artifacts,
        channel_availability=availability,
        field_provenance=dict(
            physical_state="native",
            recorded_step_endpoints="native",
            world_coordinates="reconstructed",
            reference_sampling="reconstructed",
            planning="native_offline_reference",
            display_interpolated="not_used_in_acceptance_metrics",
        ),
        metric_definitions={
            "vis1.native_window.v1": dict(
                source="analysis.window_metrics",
                extrema="native physical evidence including recorded terminal endpoint",
                rms="left-held time weights over native sample intervals; angular residual wrapped",
                variation="native adjacent differences within scope; heading wrapped",
                crossing_duration="linear progress in recorded step bracket",
            )
        },
        null_policy=(
            "JSON null / empty CSV cell; row missing_reasons and channel_availability; "
            "absent event-type fields not_applicable"
        ),
        unavailable_channels=[
            "exhaustive_unapplied_command_tail",
            "independent_world_position_truth",
        ],
        phase_semantics={
            "1": "due actuator application",
            "2": "completion and immediate variable handoff",
            "3": "waiting/fixed handoff eligibility and miss",
            "4": "disturbance/fallback",
            "5": "codriver sampling/busy/urgent trigger",
            "6": "planner release/busy",
        },
        ordering=(
            "partial order only; same-time loop continuations cannot be globally ranked "
            "from these logs"
        ),
    )
    write(out / "manifest.json", manifest)
    (out / "manifest.sha256").write_text(
        hashes([out / "manifest.json"])[str(out / "manifest.json")] + "  manifest.json\n"
    )
    return manifest
