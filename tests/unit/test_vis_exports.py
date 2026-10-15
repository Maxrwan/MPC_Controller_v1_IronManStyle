"""VIS-only coverage, chronology and schema checks; no racing/NMPC experiments."""

import copy
import importlib
import json
import sys
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
coverage = importlib.import_module("task007dvis.coverage")
protocol = importlib.import_module("task007dvis.protocol")
interface = importlib.import_module("task007dvis.interface")
exporter = importlib.import_module("task007dvis.export")
ROOT = Path(__file__).resolve().parents[2]


def test_retained_json_config_comparison_preserves_values():
    from task007dvis.parity import serialized_equal

    sim, _ = protocol.availability(protocol.CASES[0])
    current = asdict(sim)
    retained = json.loads(json.dumps(current))
    assert current["failed_plan_ids"] == () and retained["failed_plan_ids"] == []
    assert serialized_equal(retained, current)
    for key, value in [("failed_plan_ids", [1]), ("codriver_delay", 0.015), ("laps", 1)]:
        changed = dict(retained, **{key: value})
        assert not serialized_equal(changed, current)


@pytest.mark.parametrize("name", [c.name for c in protocol.CASES])
def test_frozen_case_timing_and_matrix(name):
    c = protocol.case_named(name)
    sim, timing = protocol.availability(c)
    assert sim.laps == 2 and sim.codriver_delay == 0.005
    assert not sim.committed_prefix_prediction
    assert sim.fixed_handoff_offset == (None if c.architecture == "A" else 0.07)
    if c.phase == "measured":
        assert timing is None and sim.delay(1, 0.091) == 0.091
    else:
        assert len(timing.planner) == 8001 and timing.planner[:4] == protocol.PATTERN
        assert timing.planner_delay(1) == 0.035 and sim.duration == (
            2 if c.phase == "parity" else 80
        )
    with pytest.raises(FrozenInstanceError):
        c.duration = 1


def segments():
    return [
        dict(
            start=i * 0.1,
            end=(i + 1) * 0.1,
            dt=0.1,
            state_before=[2, 0, 0, 0, s, 0],
            state_after=[2, 0, 0, 0, s + 1, 0],
            control=[0, 0],
        )
        for i, s in enumerate([1.0, 2.0, 3.0, 4.0])
    ]


def test_two_crossings_are_one_complete_lap_and_initial_partial():
    raw = dict(stop_reason="target_laps", end_time=0.4)
    c = coverage.lap_coverage(raw, segments(), 2.0)
    assert c["crossing_count"] == 2 and c["complete_laps"] == 1
    assert [w["status"] for w in c["windows"]] == ["initial_partial", "complete"]
    assert [w["end"] for w in c["windows"]] == pytest.approx([0.1, 0.3], abs=1e-12)


def test_censored_window_never_invents_completed_lap():
    c = coverage.lap_coverage(dict(stop_reason="duration", end_time=0.2), segments()[:2], 2.0)
    assert c["complete_laps"] == 0 and c["windows"][-1]["status"] == "censored_partial"
    assert c["windows"][-1]["end_s"] == 3


def test_crossing_brackets_no_extrapolation():
    r = coverage.crossings(segments(), [0, 1.5, 8])
    assert len(r) == 1 and r[0]["time"] == pytest.approx(0.05)
    assert (r[0]["bracket_start"], r[0]["bracket_end"]) == (0, 0.1)
    assert coverage.crossings([], [1]) == []


def test_nonmonotonic_segments_rejected():
    s = segments()
    s[1]["state_after"][4] = s[1]["state_before"][4]
    with pytest.raises(ValueError, match="forward progress"):
        coverage.crossings(s, [2])


def test_sector_traversals_reset_at_seam():
    rows = coverage.sector_windows(
        dict(end_time=0.4),
        segments(),
        2.0,
        [dict(name="first", start_s_m=0), dict(name="second", start_s_m=1)],
    )
    assert [(r["lap_index"], r["sector"]) for r in rows] == [
        (0, "second"),
        (1, "first"),
        (1, "second"),
        (2, "first"),
    ]
    assert not rows[0]["complete"] and rows[1]["complete"]


def test_endpoint_is_recorded_native_and_observer_does_not_change_physics(
    dynamic_vehicle, straight_geometry
):
    from task007dcx.worker import RecordedPlant

    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle

    p = RecordedPlant(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    base = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    x = np.array([2.0, 0, 0, 0, 1, 0])
    u = np.array([0.01, 0])
    y = x.copy()
    for dt in [0.003, 0.002, 0.005]:
        x = p.step(x, u, dt)
        y = base.step(y, u, dt)
        assert np.array_equal(x, y)
    first = dict(
        time=0.0,
        vx=2.0,
        vy=0.0,
        r=0.0,
        e_psi=0.0,
        s_abs=1.0,
        e_y=0.0,
        delta=0.01,
        a_cmd=0.0,
        plan_id=0,
        mode="trajectory",
    )
    raw = dict(states=[first], end_time=0.01)
    saved = copy.deepcopy(raw)
    saved_segments = copy.deepcopy(p.segments)
    rows = coverage.native_states(raw, p.segments, p)
    assert len(rows) == 2 and rows[-1]["sample_kind"] == "recorded_RK4_endpoint_before_next_events"
    assert np.array_equal([rows[-1][k] for k in ["vx", "vy", "r", "e_psi", "s_abs", "e_y"]], y)
    assert raw == saved and p.segments == saved_segments


def test_terminal_time_mismatch_rejected(dynamic_vehicle, straight_geometry):
    from task007dcx.worker import RecordedPlant

    p = RecordedPlant(dynamic_vehicle, straight_geometry)
    with pytest.raises(ValueError, match="Terminal physical coverage"):
        coverage.native_states(dict(states=[dict(time=0)], end_time=0.3), segments(), p)


def test_old_command_provenance_survives_new_packet():
    states = [dict(time=t, plan_id=2) for t in [0.16, 0.17, 0.175, 0.18]]
    controls = [dict(time=0.16, application_time=0.175, plan_id=1)]
    assert coverage.command_sources(states, controls) == [0, 0, 1, 1]
    assert all(r["plan_id"] == 2 for r in states)


def test_coincident_event_phases_keep_source_identity():
    raw = dict(
        controls=[dict(time=0.16, application_time=0.17, plan_id=0)],
        plans=[dict(plan_id=1, startup=False, completed=True, completion_time=0.17)],
        handoffs=[dict(time=0.17, plan_id=1, accepted=True)],
        fixed_handoffs=[],
        releases=[dict(time=0.17, plan_id=2)],
        triggers=[],
    )
    rows = interface.event_rows(raw)
    same = [r for r in rows if r["time"] == 0.17]
    assert [r["phase"] for r in same] == [1, 2, 3, 6]
    assert same[0]["source_stream"] == "controls" and same[0]["plan_id"] == 0
    assert all(r["within_phase_order"] is None for r in same)


def test_availability_and_request_tail_are_not_invented():
    assert interface.REQUEST_COVERAGE["unapplied_tail_complete"] is False
    assert interface.REQUEST_COVERAGE["terminal_unobserved_request"] == "unknown"
    r = interface.missing_reasons(dict(status="pending", t_ready=None, valid_from=None), "A")
    assert r == dict(t_ready="censored", valid_from="not_applicable")


def test_empty_csv_has_valid_header_and_null_is_empty(tmp_path):
    import csv

    p = tmp_path / "empty.csv"
    exporter.csv_rows(p, [], ("time", "phase", "plan_id"))
    with p.open() as f:
        r = csv.DictReader(f)
        assert r.fieldnames == ["time", "phase", "plan_id"] and list(r) == []
    p = tmp_path / "null.csv"
    exporter.csv_rows(p, [dict(time=None, reason="censored")])
    with p.open() as f:
        assert list(csv.DictReader(f))[0] == dict(time="", reason="censored")


def test_scientific_json_preserves_numpy_and_refuses_overwrite_or_nonfinite(tmp_path):
    path = tmp_path / "snapshot.json"
    array = np.array([[1.0, 2.0], [3.0, 4.0]])
    array.setflags(write=False)
    exporter.write(path, dict(array=array, scalar=np.int64(7), missing=None))
    assert json.loads(path.read_text()) == dict(
        array=[[1.0, 2.0], [3.0, 4.0]], scalar=7, missing=None
    )
    assert not array.flags.writeable and array.tolist() == [[1.0, 2.0], [3.0, 4.0]]
    saved = path.read_bytes()
    with pytest.raises(FileExistsError):
        exporter.write(path, {})
    assert path.read_bytes() == saved
    for value, error in [(np.array([np.nan]), ValueError), (object(), TypeError)]:
        with pytest.raises(error):
            exporter.write(tmp_path / "invalid.json", value)
        assert not (tmp_path / "invalid.json").exists()


def test_frozen_configuration_matches_reviewed_source():
    from task007dcx.worker import frozen_config

    prior = json.loads((ROOT / "docs/task007d/c/amended/tables_v2/provenance.json").read_text())
    assert asdict(frozen_config()) == prior["C1_steady"]["configuration"]


def test_launcher_blocks_missing_predecessor_and_stale_tests(tmp_path, monkeypatch):
    launcher = importlib.import_module("run_task007dvis")
    monkeypatch.setattr(launcher, "source_hashes", lambda: {"x": "hash"})
    (tmp_path / "prerequisites.json").write_text(
        json.dumps(dict(passed=True, source_sha256={"x": "hash"}))
    )
    launcher.check_prerequisites(tmp_path, protocol.CASES[0])
    with pytest.raises(RuntimeError, match="Previous case missing"):
        launcher.check_prerequisites(tmp_path, protocol.CASES[2])
    (tmp_path / "prerequisites.json").write_text(json.dumps(dict(passed=True, source_sha256={})))
    with pytest.raises(RuntimeError, match="stale"):
        launcher.check_prerequisites(tmp_path, protocol.CASES[0])


@pytest.mark.parametrize(
    "offset,delay,duration,missing",
    [
        (None, 0.035, 0.25, False),
        (0.07, 0.075, 0.25, False),
        (None, 0.035, 0.12, False),
        (None, 0.035, 0.005, True),
    ],
)
def test_export_validation_with_isolated_scheduler(
    dynamic_vehicle, straight_geometry, tmp_path, offset, delay, duration, missing
):
    from task007dcx.analysis import cycle_rows
    from task007dcx.worker import RecordedPlant
    from task007dvis.validation import validate
    from test_async_chronology import StraightPlanner

    from apex.control.trajectory.tracker import TrajectoryTracker
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

    plant = RecordedPlant(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    sim = AsyncConfig(
        duration=duration,
        latency_mode="injected",
        injected_delay=delay,
        codriver_delay=0.005,
        fixed_handoff_offset=offset,
    )
    captured = []
    raw = AsyncRunner(
        plant,
        StraightPlanner(),
        TrajectoryTracker(dynamic_vehicle, [-0.4, -2], [0.4, 2]),
        straight_geometry,
        sim,
        release_observer=captured.append,
    ).run([2, 0, 0, 0, 0, 0])
    # Exercise the actual packet arrays in a detached release snapshot, as the worker does.
    exporter.write(tmp_path / "release_contexts.json", [asdict(r) for r in captured])
    saved_contexts = json.loads((tmp_path / "release_contexts.json").read_text())
    assert len(saved_contexts) == len(captured)
    for saved, release in zip(saved_contexts, captured):
        assert saved["packet"]["states"] == release.packet.states.tolist()
        assert saved["prefix"]["applied_control"] == list(release.prefix.applied_control)
    for p in raw["plans"]:
        p["predicted_completion_time"] = p["release_time"] + p["estimated_delay"]
    states = coverage.native_states(raw, plant.segments, plant)
    sources = coverage.command_sources(states, raw["controls"])
    rows = [dict(r, applied_source_plan_id=pid) for r, pid in zip(states, sources)]
    cycles = cycle_rows(raw)
    if missing:
        raw.pop("reserves")
    old = copy.deepcopy(raw)
    fixture = tmp_path / "fixture_source"
    fixture.mkdir()
    (fixture / "planning_reference.csv").write_text("s_track_m,v_ref_mps\n0,2\n")
    (fixture / "track_source.json").write_text(
        json.dumps(dict(kind="isolated_test_straight_geometry", length=straight_geometry.length))
    )
    report = dict(
        coverage=coverage.lap_coverage(raw, plant.segments, straight_geometry.length),
        windows=[],
        stop_gate=[],
    )
    summary = dict(
        case="isolated",
        spec=dict(architecture="C70" if offset else "A", phase="parity"),
        git_sha="isolated-fixture",
        source_sha256={},
        fixture_sha256=exporter.hashes(fixture.glob("*")),
        simulation=asdict(sim),
        evidence_kind="isolated_scheduling_fixture_not_racing",
    )
    m = exporter.export(tmp_path, raw, plant.segments, rows, cycles, report, summary, fixture)
    assert validate(tmp_path / "scientific")["passed"]
    assert raw == old and m["request_coverage"]["terminal_unobserved_request"] == "unknown"
    if offset:
        assert m["packet_status"]["1"] == "missed"
        assert all(x["plan_id"] != 1 for x in m["accepted_authority_intervals"])
    if missing:
        assert m["channel_availability"]["reserves"]["status"] == "unavailable"
        assert not (tmp_path / "scientific/reserves.csv").exists()
        assert m["channel_availability"]["events"]["status"] == "empty"


def test_native_metric_aggregation_wraps_heading_and_censors_empty():
    a = importlib.import_module("task007dvis.analysis")
    from math import pi

    assert a.physical_difference(
        [dict(time=0, vx=1, vy=0, r=0, e_psi=pi - 0.01, s_abs=0, e_y=0, delta=0, a_cmd=0)],
        [dict(time=0, vx=1, vy=0, r=0, e_psi=-pi + 0.01, s_abs=0, e_y=0, delta=0, a_cmd=0)],
    )["errors"]["e_psi"]["max_abs"] == pytest.approx(0.02, abs=1e-12)
    assert a.physical_difference([], [])["count"] == 0
    assert a.window_metrics([], {}, dict(start=0, end=1))["metric_status"] == "insufficient_samples"


def test_retained_view_censors_unapplied_request_without_mutating_source():
    from task007dvis.fixtures import prefix

    raw = {
        k: []
        for k in [
            "states",
            "handoffs",
            "releases",
            "misses",
            "codriver_misses",
            "triggers",
            "fallbacks",
            "reserves",
        ]
    }
    raw.update(
        controls=[dict(time=0.1, application_time=0.105, plan_id=0)],
        plans=[dict(plan_id=0, startup=True, release_time=0, completion_time=0)],
        packets=[dict(plan_id=0)],
    )
    original = copy.deepcopy(raw)
    view, seg = prefix(raw, segments(), 0.1)
    assert view["controls"] == [] and len(seg) == 1 and raw == original
    assert interface.REQUEST_COVERAGE["terminal_unobserved_request"] == "unknown"


def test_report_distinguishes_failed_worker_from_unexecuted_case(tmp_path):
    from task007dvis.report import build

    source = tmp_path / "runs"
    case = source / "parity_A"
    case.mkdir(parents=True)
    (case / "raw.json").write_text("{}")
    (case / "exit.json").write_text('{"exit_code":1}')
    output = tmp_path / "report"
    result = build(source, output)
    assert result["parity_A"]["status"] == "WORKER_FAILED_AFTER_PHYSICAL_RUN"
    assert result["parity_C70"]["status"] == "NOT_EXECUTED"
    assert json.loads((output / "figures.json").read_text())["status"] == "NOT_GENERATED"
    assert list(output.glob("*.png")) == []
