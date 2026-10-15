"""Four bounded export views of retained evidence, never new racing outcomes."""

import argparse
import copy
import json
from dataclasses import asdict
from pathlib import Path

from task007dcx.analysis import cycle_rows
from task007dcx.worker import FIXTURE, RecordedPlant, geometry

from apex.models.tire.config import RACING_TIRE_PHYSICS
from task007dvis.analysis import enrich, window_metrics
from task007dvis.coverage import lap_coverage, native_states
from task007dvis.export import export, hashes, write
from task007dvis.protocol import case_named
from task007dvis.validation import validate


def prefix(raw, segments, end):
    """Censor only at an existing physical endpoint. Never integrate or invent outcomes."""
    if end and not any(abs(s["end"] - end) <= 1e-10 for s in segments):
        raise ValueError("Fixture cutoff must be a recorded endpoint")
    r = copy.deepcopy(raw)
    for channel in [
        "states",
        "handoffs",
        "releases",
        "misses",
        "codriver_misses",
        "triggers",
        "fallbacks",
        "reserves",
    ]:
        r[channel] = [v for v in r[channel] if v["time"] <= end + 1e-10]
    r["controls"] = [v for v in r["controls"] if v["application_time"] <= end + 1e-10]
    r["plans"] = [p for p in r["plans"] if p["release_time"] <= end + 1e-10]
    pids = {p["plan_id"] for p in r["plans"]}
    r["packets"] = [p for p in r["packets"] if p["plan_id"] in pids]
    for p in r["plans"]:
        if not p.get("startup") and p["completion_time"] > end + 1e-10:
            p["completed"] = False
            for key in [
                "actual_state",
                "prediction_error",
                "active_reserve_at_completion",
                "new_reserve_at_completion",
            ]:
                p.pop(key, None)
    if "fixed_handoffs" in r:
        r["fixed_handoffs"] = [c for c in r["fixed_handoffs"] if c["t_release"] <= end + 1e-10]
        for c in r["fixed_handoffs"]:
            for key in ["t_ready", "t_accept", "first_TVLQR_use", "miss_time", "late_discard_time"]:
                if c[key] is not None and c[key] > end + 1e-10:
                    c[key] = None
            if c["valid_from"] > end + 1e-10:
                c.update(
                    status="pending",
                    packet_age=None,
                    reserve_at_acceptance=None,
                    consecutive_misses=None,
                )
            if c["t_ready"] is None:
                c.update(preparation_duration=None, wait_duration=None, deadline_margin=None)
    r.update(
        end_time=end,
        stop_reason="duration",
        lap_times=[],
        failure=None,
        pending_at_end=any(not p.get("completed") for p in r["plans"] if not p.get("startup")),
    )
    return r, [s for s in segments if s["end"] <= end + 1e-10]


def build(output):
    output.mkdir(exist_ok=False, parents=True)
    track, ref, p = geometry()
    plant = RecordedPlant(p, track, tire_physics=RACING_TIRE_PHYSICS)
    specs = [
        ("nominal_A", "C3_g2.0_variable", 0.21, "A"),
        ("C70_miss", "C2_miss", 0.50, "C70"),
        ("censored_A", "C3_g2.0_variable", 0.19, "A"),
        ("empty_optional_A", "C3_g2.0_variable", 0.0, "A"),
    ]
    result = {}
    for name, source, end, architecture in specs:
        folder = Path("results/task007d/c/amended") / source
        source_hash = hashes(folder.glob("*.json"))
        original = json.loads((folder / "raw.json").read_text())
        segments = json.loads((folder / "segments.json").read_text())
        raw, segments = prefix(original, segments, end)
        states = native_states(raw, segments, plant)
        rows = enrich(raw, states, track, ref)
        cycles = cycle_rows(raw)
        summary = json.loads((folder / "summary.json").read_text())
        summary.update(
            case=name,
            spec=asdict(case_named("controlled_" + architecture)),
            evidence_kind="retained_evidence_censored_view; not_new_experiment",
            raw_sha256=source_hash,
        )
        coverage = lap_coverage(raw, segments, track.length)
        windows = []
        if end:
            windows = [
                window_metrics(
                    rows,
                    raw,
                    dict(
                        kind="run",
                        index=0,
                        start=0.0,
                        end=end,
                        start_s=rows[0]["s_abs"],
                        end_s=rows[-1]["s_abs"],
                        complete=False,
                        status="censored_fixture",
                    ),
                )
            ]
        report = dict(coverage=coverage, windows=windows, stop_gate=[])
        if name == "empty_optional_A":
            raw.pop("reserves")
        package = output / name
        export(folder, raw, segments, rows, cycles, report, summary, FIXTURE, output=package)
        checks = validate(package)
        assert hashes(folder.glob("*.json")) == source_hash
        result[name] = dict(checks, source=str(folder), cutoff=end, source_hashes_unchanged=True)
    write(output / "validation.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
