"""Exact deterministic C3 compatibility audit; excludes only host-time telemetry."""

import json
from pathlib import Path

from task007dvis.export import hashes

CONTROL_TIMING = {
    "interpolation_time",
    "feedback_time",
    "command_validation_time",
    "kernel_time",
    "cpu_time",
    "total_time",
    "computational_deadline_exceeded",
}


def historical(case):
    name = "C3_g2.0_fixed70" if case.architecture == "C70" else "C3_g2.0_variable"
    return Path("results/task007d/c/amended") / name


def serialized_equal(retained, current):
    """Compare retained JSON with live config, preserving every serialized value."""
    return retained == json.loads(json.dumps(current, allow_nan=False))


def applicability(case, configuration, simulation, fixture, vehicle):
    folder = historical(case)
    old = json.loads((folder / "summary.json").read_text())
    raw = json.loads((folder / "raw.json").read_text())
    mismatches = [p for p, h in old["source_sha256"].items() if hashes([p]).get(p) != h]
    allowed = {"src/apex/simulation/asynchronous.py", "src/apex/simulation/fixed_handoff.py"}
    checks = dict(
        configuration=serialized_equal(old["configuration"], configuration),
        simulation=serialized_equal(old["simulation"], simulation),
        fixture=old["fixture_sha256"] == hashes(fixture.glob("*")),
        vehicle=old["vehicle_sha256"] == hashes([vehicle])[str(vehicle)],
        source=set(mismatches) == allowed,
        no_urgent=not raw["triggers"] and not raw.get("urgent_demands", []),
    )
    return dict(
        passed=all(checks.values()),
        checks=checks,
        source_mismatches=mismatches,
        source_change_reason="Previously reviewed urgent-demand bookkeeping; no trigger in C3",
        old_revision=old["git_sha"],
        retained_hashes=hashes(folder.glob("*.json")),
    )


def compare(case, raw, segments):
    folder = historical(case)
    old = json.loads((folder / "raw.json").read_text())
    previous_segments = json.loads((folder / "segments.json").read_text())
    fields = [
        "states",
        "handoffs",
        "reserves",
        "releases",
        "misses",
        "codriver_misses",
        "triggers",
        "fallbacks",
        "lap_times",
        "stop_reason",
        "failure",
        "end_time",
        "pending_at_end",
    ]
    checks = {k: raw[k] == old[k] for k in fields}
    for k in ["fixed_handoffs", "urgent_demands"]:
        checks[k] = raw.get(k) == old.get(k)
    checks["RK4_segments"] = segments == previous_segments

    def strip(rows, omitted):
        return [{k: v for k, v in r.items() if k not in omitted} for r in rows]

    checks["physical_controls"] = strip(raw["controls"], CONTROL_TIMING) == strip(
        old["controls"], CONTROL_TIMING
    )
    checks["packet_contents"] = strip(
        raw["packets"], {"solve_duration", "total_computation_duration"}
    ) == strip(old["packets"], {"solve_duration", "total_computation_duration"})
    inputs = [
        "plan_id",
        "release_time",
        "estimated_delay",
        "source_state",
        "predicted_state",
        "predicted_previous_control",
        "completion_time",
        "success",
    ]
    checks["NMPC_inputs"] = [[p[k] for k in inputs] for p in raw["plans"]] == [
        [p[k] for k in inputs] for p in old["plans"]
    ]
    return dict(passed=all(checks.values()), exact=checks)
