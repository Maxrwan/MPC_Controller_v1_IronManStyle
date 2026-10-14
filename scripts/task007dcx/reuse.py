"""Audit retained C1 applicability; replay recorded packets, never rerun accepted NMPC."""

import argparse
import copy
import json
from pathlib import Path

import numpy as np
from task007d.forensics import packet_from_record
from task007dc.export import write

from apex.control.trajectory.tracker import TrackerConfig, TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner
from apex.simulation.diagnostic_timing import DiagnosticTiming
from task007dcx.worker import FIXTURE, VEHICLE, RecordedPlant, geometry, hashes


def audit(folder):
    s = json.loads((folder / "summary.json").read_text())
    raw = json.loads((folder / "raw.json").read_text())
    contexts = json.loads((folder / "release_contexts.json").read_text())
    mismatch = [p for p, h in s["source_sha256"].items() if hashes([Path(p)]).get(p) != h]
    assert set(mismatch) == {
        "src/apex/simulation/asynchronous.py",
        "src/apex/simulation/fixed_handoff.py",
    }
    assert hashes(FIXTURE.glob("*")) == s["fixture_sha256"]
    assert hashes([VEHICLE])[str(VEHICLE)] == s["vehicle_sha256"]
    assert raw["urgent_demands"] == [] and raw["triggers"] == []
    track, _, p = geometry()
    c = contexts[0]
    tracker = TrajectoryTracker(p, c["lower"], c["upper"], TrackerConfig(**c["tracker_config"]))
    packets = {r["plan_id"]: packet_from_record(r) for r in raw["packets"]}
    events = {r["plan_id"]: r for r in raw["plans"]}
    checked = []

    class RetainedPlanner:
        def prepare(self, pid, state, time, estimate, buffer, tracker, *, startup=False):
            original = events[pid]
            assert np.array_equal(state, original["source_state"]), (pid, "release_state")
            assert time == original["release_time"] and estimate == original["estimated_delay"]
            if not startup:
                context = next(c for c in contexts if c["plan_id"] == pid)
                assert np.array_equal(tracker.previous, context["prefix"]["applied_control"])
                assert buffer.active.plan_id == context["packet"]["plan_id"]
            checked.append(pid)
            return packets[pid], copy.deepcopy(original)

    plant = RecordedPlant(p, track, tire_physics=RACING_TIRE_PHYSICS)
    got = AsyncRunner(
        plant,
        RetainedPlanner(),
        tracker,
        track,
        AsyncConfig(**s["simulation"]),
        timing=DiagnosticTiming(**s["timing"]),
    ).run(s["initial_state"])
    exact = {
        k: got[k] == raw[k]
        for k in [
            "states",
            "releases",
            "handoffs",
            "reserves",
            "fixed_handoffs",
            "urgent_demands",
            "misses",
            "fallbacks",
        ]
    }
    exact["segments"] = plant.segments == json.loads((folder / "segments.json").read_text())
    measured = {
        "interpolation_time",
        "feedback_time",
        "command_validation_time",
        "kernel_time",
        "cpu_time",
        "total_time",
        "computational_deadline_exceeded",
    }

    def strip(rows):
        return [{k: v for k, v in r.items() if k not in measured} for r in rows]

    exact["controls_excluding_wall_telemetry"] = strip(got["controls"]) == strip(raw["controls"])
    assert all(exact.values()), exact
    return dict(
        case=folder.name,
        capture_sha=s["git_sha"],
        source_count=len(s["source_sha256"]),
        source_mismatches=mismatch,
        fixture_and_vehicle_exact=True,
        no_urgent_demand=True,
        replay_exact=exact,
        checked_preparation_inputs=len(checked),
        note="Recorded packet replay checks current scheduling/plant/TVLQR and release inputs; "
        "no optimization or new measured experiment. Unchanged predictor/NMPC hashes "
        "plus matched release inputs support retained deterministic C1 applicability.",
        retained_hashes=hashes(folder.glob("*.json")),
        current_source_hashes=hashes(Path(f) for f in s["source_sha256"]),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    write(
        a.output,
        {
            case: audit(Path("results/task007d/c/amended") / case)
            for case in ["C1_steady", "C1_jitter"]
        },
    )
