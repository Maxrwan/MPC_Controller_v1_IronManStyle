"""CX analysis boundary cases and frozen measured dispatch; no racing campaign."""

import copy
import importlib
import json
import sys
from math import pi
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
a = importlib.import_module("task007dcx.analysis")
w = importlib.import_module("task007dcx.worker")
ROOT = Path(__file__).resolve().parents[2]


def test_frozen_configuration_matches_retained_c1():
    from dataclasses import asdict

    old = json.loads((ROOT / "docs/task007d/c/amended/tables_v2/provenance.json").read_text())[
        "C1_steady"
    ]
    assert asdict(w.frozen_config()) == old["configuration"]


@pytest.mark.parametrize("architecture,offset", [("A", None), ("C70", 0.07), ("C80", 0.08)])
def test_measured_uses_actual_preparation_not_a_replay_or_future_value(architecture, offset):
    p = json.loads((ROOT / "docs/task007d/cx/protocol.json").read_text())
    sim, timing = w.availability(p, f"S2_{architecture}_01")
    assert timing is None and sim.latency_mode == "measured"
    assert sim.delay(1, 0.073) == 0.073 and sim.fixed_handoff_offset == offset
    assert sim.codriver_delay == 0.005 and not sim.committed_prefix_prediction


def test_matched_jitter_reuses_exact_retained_delays():
    p = json.loads((ROOT / "docs/task007d/cx/protocol.json").read_text())
    prior = json.loads((ROOT / "docs/task007d/c/amended/protocol.json").read_text())
    for name in ["steady", "jitter"]:
        sim, timing = w.availability(p, "S1_A_" + name)
        assert list(timing.planner) == prior["cases"]["C1_" + name]["planner"]
        assert sim.fixed_handoff_offset is None and sim.duration == 2.0


def row(status, ready, target=0.17):
    return dict(
        status=status,
        t_ready=ready,
        valid_from=target,
        deadline_margin=None if ready is None else target - ready,
        consecutive_misses=1 if status == "missed" else 0,
        measured_preparation_duration=0.075,
        wait_duration=None,
        accepted_latency=None,
    )


def test_misses_hits_rejection_and_censoring_are_distinct():
    rows = [
        row("accepted", 0.16),
        row("missed", 0.175),
        row("pending", None),
        row("rejected", 0.15),
    ]
    s = a.timing_summary(rows, True)
    assert (s["resolved"], s["censored"], s["hits"], s["misses"], s["accepted"], s["rejected"]) == (
        3,
        1,
        2,
        1,
        1,
        1,
    )
    assert s["miss_fraction"] == 1 / 3 and s["preparation"]["n"] == 4
    assert a.timing_summary(rows, False)["miss_fraction"] is None


def test_small_sample_p99_and_empty_distribution_remain_null():
    assert a.distribution([])["mean"] is None
    assert a.distribution(range(99))["p99"] is None
    assert a.distribution(range(100))["p99"] == pytest.approx(98.01)
    assert a.wilson(0, 0) is None
    assert a.wilson(0, 10)[1] > 0  # zero observed misses is not a guarantee


def test_recorded_pair_wraps_heading_and_censors_noncommon_coverage():
    keys = ("vx", "vy", "r", "e_psi", "s_abs", "e_y", "delta", "a_cmd")

    def raw(angle, last):
        return dict(
            states=[
                dict(time=t, plan_id=0, **{k: angle if k == "e_psi" else 0 for k in keys})
                for t in [0, 0.003, last]
            ],
            reserves=[dict(time=t, reserve=0.8 - t) for t in [0, 0.003, last]],
        )

    x, y = raw(pi - 0.01, 0.01), raw(-pi + 0.01, 0.02)
    saved = copy.deepcopy(x)
    rows, s = a.paired_samples(x, y)
    assert len(rows) == 1 and rows[0]["time"] == 0
    assert s["e_psi"]["max_abs"] == pytest.approx(0.02, abs=1e-12)
    assert s["e_psi"]["first_engineering"] == 0 and x == saved
    with pytest.raises(ValueError, match="coverage"):
        a.paired_samples(dict(states=[], reserves=[]), y)


def test_recorded_plant_observer_has_exact_rk4_parity(dynamic_vehicle, straight_geometry):
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle

    p = w.RecordedPlant(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    baseline = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    x = np.array([2.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    u = np.array([0.01, 0.0])
    y = x.copy()
    for dt in [0.003, 0.002, 0.005]:
        x = p.step(x, u, dt)
        y = baseline.step(y, u, dt)
        assert np.array_equal(x, y)
    assert [s["dt"] for s in p.segments] == [0.003, 0.002, 0.005]


def test_cycle_completion_and_acceptance_not_conflated():
    raw = dict(
        fixed_handoffs=[
            dict(
                plan_id=1,
                t_release=0.1,
                t_ready=None,
                valid_from=0.17,
                t_accept=None,
                first_TVLQR_use=None,
                status="missed",
                consecutive_misses=1,
                deadline_margin=None,
                wait_duration=None,
            )
        ],
        plans=[
            dict(
                plan_id=1,
                release_time=0.1,
                planner_total_time=0.09,
                predicted_completion_time=0.17,
                completed=False,
            )
        ],
    )
    r = a.cycle_rows(raw)[0]
    assert r["measured_preparation_duration"] == 0.09
    assert r["preparation_finish"] is None and r["preparation_finish_censored"]
    assert r["accepted_latency"] is None


@pytest.mark.parametrize("duration", [0.65, 0.5])
def test_miss_consequences_isolated_fixture_has_recorded_recovery(
    dynamic_vehicle, straight_geometry, duration
):
    from test_fixed_handoff_scheduler import simulate

    from apex.simulation.diagnostic_timing import DiagnosticTiming

    timing = DiagnosticTiming("replay", (0.03, 0.03, 0.03, 0.075, 0.03, 0.03), (0.0,) * 100)
    raw = simulate(dynamic_vehicle, straight_geometry, timing=timing, duration=duration)
    # StraightPlanner omits this diagnostic; its packet's target is explicit.
    for event in raw["plans"]:
        event["predicted_completion_time"] = event["release_time"] + event["estimated_delay"]
    misses = a.miss_consequences(raw, straight_geometry, [{"name": "straight", "start_s_m": 0.0}])
    assert len(misses) == 1
    m = misses[0]
    assert m["plan_id"] == 4 and m["time"] == pytest.approx(0.47)
    assert m["late_discard_time"] == pytest.approx(0.475)
    assert m["old_plan_id"] == 3 and m["minimum_reserve_to_recovery"] > 0
    if duration == 0.65:
        assert m["recovery_time"] == pytest.approx(0.57)
        assert m["authority_gap"] == pytest.approx(0.2)
        assert not m["recovery_censored"]
    else:
        assert m["recovery_time"] is None and m["authority_gap"] is None
        assert m["recovery_censored"]


def test_common_quality_has_six_states_and_no_extrapolation(dynamic_vehicle, straight_geometry):
    from types import SimpleNamespace

    from test_fixed_handoff_scheduler import simulate

    raw = simulate(dynamic_vehicle, straight_geometry, duration=0.3)
    reference = SimpleNamespace(
        sample=lambda s: dict(v_ref_mps=2.0, e_psi_ref_rad=0.0, e_y_ref_m=0.0)
    )
    q = a.quality(raw, straight_geometry, reference, end=0.29)
    assert q["samples"] == 30 and q["complete_common_coverage"]
    assert set(q["tracking"]) == {"vx", "vy", "r", "e_psi", "s_abs", "e_y"}
    assert q["planning_to_apex"]["e_y"]["max_abs"] == 0.0
    assert a.quality(raw, straight_geometry, reference, 0.4)["complete_common_coverage"] is False
