"""Offline candidates and scoring only: no NMPC solves or closed-loop execution."""

from dataclasses import asdict, replace

import numpy as np
import pytest
from task007dp.candidates import Candidate, intervals, read_release
from task007dp.evaluation import authority_events, preceding_truth, statistics

from apex.control.trajectory.packet import TrajectoryPacket
from apex.control.trajectory.prediction import CommittedControlPrefix
from apex.control.trajectory.tracker import LATERAL, TVLQR, TrackerConfig
from apex.coordinates.angles import wrap_angle
from apex.simulation.prediction_capture import PredictionRelease


def release(parameters, *, duration=0.017, pending=None, due=None, error=None):
    times = np.arange(9) * 0.1
    x = np.zeros((9, 6))
    x[:, 0], x[:, 4] = 2.0, 1.0 + 2 * times
    packet = TrajectoryPacket(
        0,
        0,
        0,
        0,
        0,
        times,
        x,
        np.tile([0.1, 0.2], (8, 1)),
        x[0],
        x[0],
        "fixture",
        0,
        0,
        np.arange(80) * 0.01,
        np.tile([1.0, 2.0, 0.1, 0.1], (80, 1)),
        np.zeros(9),
    )
    state = x[0] + (np.zeros(6) if error is None else error)
    return PredictionRelease(
        1,
        tuple(state),
        duration,
        CommittedControlPrefix(0.0, [0.0, 0.0], 0.0, pending, due),
        packet,
        parameters,
        TrackerConfig(),
        (-0.4, -2.0),
        (0.4, 2.0),
    )


@pytest.mark.parametrize("method", ["P0", "P1a", "P1b"])
def test_nodes_order_and_determinism(dynamic_vehicle, straight_geometry, method):
    r = release(dynamic_vehicle, duration=0.1)
    predictor = Candidate(method, dynamic_vehicle, straight_geometry)
    x, u = predictor(r)
    np.testing.assert_array_equal(x, r.packet.states[1])
    x2, u2 = predictor(r)
    np.testing.assert_array_equal(x, x2)
    np.testing.assert_array_equal(u, u2)
    assert list(LATERAL) == [5, 3, 1, 2]


def test_all_six_states_are_affine_between_nodes_and_input_is_held(
    dynamic_vehicle, straight_geometry
):
    r = release(dynamic_vehicle, duration=0.025)
    states = r.packet.states.copy()
    states[1] = [2.2, 0.03, 0.1, 0.04, 1.2, 0.02]
    r = replace(r, packet=replace(r.packet, states=states))
    x, u = Candidate("P0", dynamic_vehicle, straight_geometry)(r)
    np.testing.assert_allclose(x, 0.75 * states[0] + 0.25 * states[1], rtol=0, atol=1e-12)
    # Feasible preview follows nominal input through the real per-tick steering limit.
    np.testing.assert_allclose(u, [0.02, 0.2], rtol=0, atol=1e-12)
    assert r.packet.sample(0.025)[1][0] == 0.1  # Never mistaken for actually applied steering.


def test_p1a_wraps_release_error_and_target_heading(dynamic_vehicle, straight_geometry):
    r = release(dynamic_vehicle, duration=0.05)
    states = r.packet.states.copy()
    states[:, 3] = np.deg2rad([179, -179, -177, -175, -173, -171, -169, -167, -165])
    packet = replace(r.packet, states=states)
    actual = packet.sample(0)[0].copy()
    actual[3] = np.deg2rad(-179)
    actual[5] = 0.02
    r = replace(r, packet=packet, state=tuple(actual))
    x, _ = Candidate("P1a", dynamic_vehicle, straight_geometry)(r)
    assert x[3] == pytest.approx(np.deg2rad(-178), rel=0, abs=1e-12)
    assert x[5] == 0.02
    assert packet.sample(0.05)[0][3] == pytest.approx(np.pi, rel=0, abs=1e-12)


def test_p1b_uses_existing_jacobian_lateral_gain_order_and_partial_step(
    dynamic_vehicle, straight_geometry
):
    error = np.array([0.02, 0.001, 0.002, 0.003, 0.01, 0.004])
    r = release(dynamic_vehicle, error=error)
    c = Candidate("P1b", dynamic_vehicle, straight_geometry)
    c.precompute([r])
    assert set(c.jacobians) == {0.01, 0.007}
    full_a, full_b = TVLQR(c.model, straight_geometry).jacobian(*r.packet.sample(0)[:2], 0)
    a, b = c.jacobians[0.01](*r.packet.sample(0)[:2], 0)
    np.testing.assert_array_equal(a, full_a)
    np.testing.assert_array_equal(b, full_b)
    expected = error.copy()
    for t, h in [(0, 0.01), (0.01, 0.007)]:
        nominal, u, k = r.packet.sample(t)
        a, b = map(np.asarray, TVLQR(c.model, straight_geometry, dt=h).jacobian(nominal, u, 0))
        assert a.shape == (6, 6) and b.shape == (6, 2) and k.shape == (4,)
        expected[LATERAL] = (a[np.ix_(LATERAL, LATERAL)] - b[LATERAL, :1] @ k[None, :]) @ expected[
            LATERAL
        ]
        expected[3] = wrap_angle(expected[3])
    x, _ = c(r)
    actual = x - r.packet.sample(0.017)[0]
    actual[3] = wrap_angle(actual[3])
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-12)
    assert actual[0] == pytest.approx(error[0], rel=0, abs=1e-12)
    assert actual[4] == pytest.approx(error[4], rel=0, abs=1e-12)


def test_time_varying_gain_is_sampled_on_each_recurrence_interval(
    dynamic_vehicle, straight_geometry
):
    r = release(dynamic_vehicle, error=np.array([0, 0.001, 0.002, 0.003, 0, 0.004]))
    gains = r.packet.gains.copy()
    gains[1] = 0
    changed = replace(r, packet=replace(r.packet, gains=gains))
    c = Candidate("P1b", dynamic_vehicle, straight_geometry)
    assert not np.array_equal(c(r)[0][LATERAL], c(changed)[0][LATERAL])


@pytest.mark.parametrize("method", ["P0", "P1a", "P1b"])
@pytest.mark.parametrize("target,expected", [(0.014, 0.0), (0.015, 0.015), (0.017, 0.015)])
def test_pending_busy_timing_and_target_application_clamp(
    dynamic_vehicle, straight_geometry, method, target, expected
):
    r = release(dynamic_vehicle, duration=target, pending=[0.2, 0.3], due=0.015)
    _, u = Candidate(method, dynamic_vehicle, straight_geometry)(r)
    np.testing.assert_allclose(u, [expected, 0 if target < 0.015 else 0.3], rtol=0, atol=1e-12)


def test_due_now_and_no_feedback_at_target(dynamic_vehicle, straight_geometry):
    r = release(dynamic_vehicle, duration=0, pending=[0.2, 0.3], due=0)
    _, u = Candidate("P0", dynamic_vehicle, straight_geometry)(r)
    np.testing.assert_array_equal(u, [0, 0.3])
    r = release(dynamic_vehicle, duration=0.01)
    np.testing.assert_array_equal(Candidate("P0", dynamic_vehicle, straight_geometry)(r)[1], [0, 0])


@pytest.mark.parametrize("method", ["A", "P0", "P1a", "P1b", "P2"])
def test_missing_horizon_and_input_nonmutation(dynamic_vehicle, straight_geometry, method):
    r = release(dynamic_vehicle)
    before = asdict(r)
    c = Candidate(method, dynamic_vehicle, straight_geometry)
    c(r)
    after = asdict(r)
    for key in before["packet"]:
        np.testing.assert_array_equal(before["packet"][key], after["packet"][key])
    assert before["state"] == after["state"] and before["prefix"] == after["prefix"]
    with pytest.raises(ValueError):
        c(replace(r, packet=None))
    with pytest.raises(ValueError):
        c(replace(r, estimated_delay=0.801))
    with pytest.raises(ValueError):
        c(replace(r, state=(float("nan"), *r.state[1:])))


def test_serialized_release_only_no_history_interface(dynamic_vehicle, straight_geometry):
    r = release(dynamic_vehicle)
    record = asdict(r)
    record["packet"] = r.packet.as_dict()
    reconstructed = read_release(record)
    c = Candidate("P1a", dynamic_vehicle, straight_geometry)
    np.testing.assert_array_equal(c(reconstructed)[0], c(r)[0])
    with pytest.raises(TypeError):
        c(r, future_truth=[99] * 6)
    assert intervals(replace(r, estimated_delay=0.017)) == [0.0, 0.01, 0.017]


def test_scoring_excludes_new_zero_latency_feedback_at_target(dynamic_vehicle):
    r = release(dynamic_vehicle)
    raw = dict(
        states=[dict(time=0), dict(time=0.1)],
        controls=[
            dict(time=0, application_time=0.015, delta=0.015, a_cmd=0.3),
            dict(time=0.02, application_time=0.02, delta=0.9, a_cmd=1.0),
        ],
    )
    np.testing.assert_array_equal(preceding_truth(raw, r, 0.02), [0.015, 0.3])
    assert preceding_truth(raw, r, 0.11) is None
    raw.update(handoffs=[dict(time=0.02, accepted=True)], fallbacks=[], triggers=[])
    assert not authority_events(raw, r, 0.02)
    assert authority_events(raw, r, 0.03)


def test_accounting_keeps_failures_and_first_release_separate():
    rows = []
    for i in range(1, 4):
        predictions = {
            m: dict(error=[float(i)] * 8, failure=None) for m in ["A", "P0", "P1a", "P1b", "P2"]
        }
        if i == 1:
            predictions["P0"] = dict(error=None, failure="outside domain")
        rows.append(
            dict(case="fixture_A", release_time=i * 0.1, predictions=predictions, contamination=[])
        )
    stats = statistics(rows)
    all_p0 = next(
        r for r in stats if (r["phase"], r["method"], r["channel"]) == ("all", "P0", "e_y")
    )
    assert all_p0["total"] == 3 and all_p0["comparable"] == 2 and all_p0["failures"] == 1
    assert all_p0["tie_vs_A"] == 2 and all_p0["p95_abs"] is None
    first = next(
        r for r in stats if (r["phase"], r["method"], r["channel"]) == ("first", "P0", "e_y")
    )
    assert first["rms"] is None


def test_benchmark_selection_and_absolute_distribution_accounting():
    from types import SimpleNamespace

    from task007dp.benchmark import distribution, select_contexts

    cases = {
        f"D4-R{i}_{h}": dict(releases=[SimpleNamespace(plan_id=j) for j in range(1, 20)])
        for i in range(1, 5)
        for h in ("A", "B")
    }
    cases["D3-ref_A"] = cases["D4-R1_A"]
    selected = select_contexts(cases)
    assert len(selected) == 32 and {r.plan_id for _, r in selected} == {1, 2, 10, 18}
    assert all(name.startswith("D4-") for name, _ in selected)
    stats = distribution([1.0, 2.0, 3.0, 4.0, 5.0])
    assert stats == dict(count=5, median=3.0, p95=4.8, maximum=5.0)
