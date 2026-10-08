"""Diagnostic schedules preserve the existing physical event semantics."""

import sys
from pathlib import Path

import numpy as np
import pytest
from test_async_chronology import StraightPlanner

from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner
from apex.simulation.diagnostic_timing import DiagnosticTiming, ReplayExhausted

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


def simulate(p, track, timing=None, **kwargs):
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    tracker = TrajectoryTracker(p, [-0.4, -2], [0.4, 2])
    config = AsyncConfig(duration=0.35, laps=2, latency_mode="injected", **kwargs)
    return AsyncRunner(plant, StraightPlanner(), tracker, track, config, timing=timing).run(
        [2, 0, 0, 0, 0, 0]
    )


def test_fixed_matches_existing_injected_chronology(dynamic_vehicle, straight_geometry):
    old = simulate(dynamic_vehicle, straight_geometry, injected_delay=0.035, codriver_delay=0.001)
    new = simulate(
        dynamic_vehicle, straight_geometry, DiagnosticTiming("fixed", (0.035,), (0.001,))
    )
    assert old["failure"] is new["failure"] is None
    np.testing.assert_array_equal(
        [[r[k] for k in ["time", "s_abs", "delta", "a_cmd"]] for r in old["states"]],
        [[r[k] for k in ["time", "s_abs", "delta", "a_cmd"]] for r in new["states"]],
    )
    assert new["states"][-1]["s_abs"] > 0.68


def test_recorded_sequence_and_skipped_releases(dynamic_vehicle, straight_geometry):
    schedule = DiagnosticTiming("replay", (0.15, 0.025, 0.025), tuple([0.015] * 50))
    r = simulate(dynamic_vehicle, straight_geometry, schedule)
    assert r["failure"] is None and r["misses"] and r["codriver_misses"]
    assert [p["physical_delay"] for p in r["plans"][1:]] == [0.15, 0.025]
    for c in r["controls"]:
        assert c["application_time"] - c["time"] == pytest.approx(0.015)


def test_exhaustion_stops_without_fabricated_tail(dynamic_vehicle, straight_geometry):
    r = simulate(dynamic_vehicle, straight_geometry, DiagnosticTiming("replay", (0.035,), (0.001,)))
    assert r["stop_reason"] == "diagnostic_trace_exhausted"
    assert "codriver" in r["failure"]
    assert r["end_time"] == pytest.approx(0.01)


def test_timing_perturbation_is_one_event_and_immutable():
    original = DiagnosticTiming("replay", (0.03, 0.04, 0.05), (0.001,))
    changed = original.perturb(1, -0.002)
    assert changed.planner == (0.03, 0.038, 0.05)
    assert original.planner == (0.03, 0.04, 0.05)
    with pytest.raises(ValueError):
        original.perturb(1, -0.1)
    with pytest.raises(ReplayExhausted):
        original.planner_delay(4)


def test_default_measured_dispatch_is_preserved():
    c = AsyncConfig(latency_mode="measured", codriver_delay=None)
    assert c.delay(1, 0.123) == 0.123
    assert c.codriver_delay is None


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.1])
def test_invalid_schedule_rejected(bad):
    with pytest.raises(ValueError):
        DiagnosticTiming("fixed", (bad,), (0.001,))


def test_fresh_worker_seed_environment_is_explicit():
    from threading_study.config import environment

    assert environment(1)["PYTHONHASHSEED"] == "0"


def test_existing_results_cannot_be_overwritten(tmp_path):
    import hashlib
    from types import SimpleNamespace

    from task007cr.run import dispatch

    folder = tmp_path / "historical"
    folder.mkdir()
    historical = folder / "summary.json"
    historical.write_text('{"retained":true}')
    before = hashlib.sha256(historical.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Preserve existing"):
        dispatch(SimpleNamespace(output=tmp_path, case="historical", worker=False))
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == before


def test_comparison_reports_unequal_coverage():
    from task007cr.compare import difference

    report = difference([0, 1, 2], [0, 1], 1e-9)
    assert not report["lengths_equal"]
    assert report["rows_compared"] == 2
    assert report["max_abs"] == 0


def test_default_measured_runner_uses_actual_timers(
    dynamic_vehicle, straight_geometry, monkeypatch
):
    import itertools

    import apex.simulation.asynchronous as scheduling

    ticks = itertools.count(0, 0.001)
    monkeypatch.setattr(scheduling, "perf_counter", lambda: next(ticks))
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    tracker = TrajectoryTracker(dynamic_vehicle, [-0.4, -2], [0.4, 2])
    c = AsyncConfig(duration=0.25, laps=2, latency_mode="measured", codriver_delay=None)
    result = AsyncRunner(plant, StraightPlanner(), tracker, straight_geometry, c).run(
        [2, 0, 0, 0, 0, 0]
    )
    assert result["failure"] is None
    for plan in result["plans"][1:]:
        assert plan["physical_delay"] == plan["planner_total_time"] == 0.017
    for row in result["controls"]:
        assert row["physical_latency"] == row["total_time"]
        assert row["physical_latency"] == pytest.approx(0.003)
        assert row["application_time"] - row["time"] == pytest.approx(0.003)
