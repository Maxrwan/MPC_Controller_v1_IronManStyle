"""Physical timestamps, interpolation, local feedback and approved-model derivatives."""

from dataclasses import replace

import numpy as np
import pytest

from apex.control.mpc.problem import MPCConfig, MPCProblem
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.control.trajectory.packet import TrajectoryBuffer, TrajectoryPacket
from apex.control.trajectory.prediction import ActuationPredictor, RollingDelay, UrgentReplan
from apex.control.trajectory.tracker import TVLQR, TrackerConfig, TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle


def packet(plan_id=1, start=0.0, completion=0.0, heading=None):
    times = start + np.arange(5) * 0.1
    states = np.zeros((5, 6))
    states[:, 0], states[:, 4] = 2, times * 2
    if heading is not None:
        states[:, 3] = heading
    return TrajectoryPacket(
        plan_id,
        0,
        0,
        start,
        completion,
        times,
        states,
        np.array([[i * 0.01, i * 0.1] for i in range(4)]),
        states[0],
        states[0],
        "Solve_Succeeded",
        0.01,
        0.017,
        times[:-1],
        np.tile([1.0, 2.0, 0.1, 0.1], (4, 1)),
    )


def tracker(p, feedback=True):
    return TrajectoryTracker(p, [-0.4, -2.0], [0.4, 2.0], TrackerConfig(feedback=feedback))


@pytest.mark.parametrize("times", [[0, 0.1, 0.1, 0.3, 0.4], [0, 0.2, 0.1, 0.3, 0.4]])
def test_monotonic_timestamp_validation(times):
    with pytest.raises(ValueError):
        replace(packet(), timestamps=times)


@pytest.mark.parametrize(
    "field,value",
    [
        ("states", np.zeros((5, 5))),
        ("controls", np.zeros((5, 2))),
        ("gains", np.zeros((4, 2))),
        ("states", np.full((5, 6), np.nan)),
        ("actual_completion_time", -0.1),
    ],
)
def test_packet_rejects_invalid_arrays_and_metadata(field, value):
    with pytest.raises(ValueError):
        replace(packet(), **{field: value})


def test_interpolation_heading_progress_and_zoh():
    p = packet(heading=np.deg2rad([179, -179, -177, -175, -173]))
    x, u, gain = p.sample(0.05)
    assert x[3] == pytest.approx(np.pi)
    assert x[4] == pytest.approx(0.1)
    np.testing.assert_array_equal(u, [0, 0])
    np.testing.assert_array_equal(p.sample(0.15)[1], [0.01, 0.1])
    assert gain.shape == (4,)
    with pytest.raises(ValueError):
        p.sample(0.401)
    with pytest.raises(ValueError):
        p.sample(-0.001)


def test_packet_owns_copies():
    p = packet()
    assert not p.states.flags.writeable
    state, control, gain = p.sample(0.1)
    state[:] = control[:] = gain[:] = 99
    assert p.states[1, 0] == 2


def test_trim_reserve_and_newer_handoff():
    b = TrajectoryBuffer()
    assert b.insert(packet(), 0.15)[0]
    assert b.active.timestamps[0] == 0.15
    assert b.reserve(0.15) == pytest.approx(0.25)
    np.testing.assert_allclose(b.sample(0.15)[0], packet().sample(0.15)[0])
    np.testing.assert_allclose(b.sample(0.15)[1], packet().sample(0.15)[1])
    assert b.insert(packet(), 0.2) == (False, "stale_plan")
    assert b.insert(packet(2, 0.2, 0.2), 0.2)[0]
    assert b.active_plan_id == 2
    assert b.category(0.5) == "warning"
    assert b.category(0.57) == "critical"
    assert b.category(0.6) == "exhausted"
    with pytest.raises(ValueError):
        b.sample(0.601)


def test_reject_future_expired_and_failed():
    b = TrajectoryBuffer()
    assert b.insert(packet(start=0.1), 0.0)[1] == "not_available_yet"
    assert b.insert(packet(), 0.39)[1] == "insufficient_reserve"
    assert not b.insert(replace(packet(), valid=False), 0)[0]


def test_delay_estimator_and_urgent_request():
    delay = RollingDelay(initial=0.017, window=3)
    assert delay.estimate() == 0.017
    for v in [0.025, 0.03, 0.15]:
        delay.observe(v)
    assert delay.estimate() == 0.03
    with pytest.raises(ValueError):
        delay.observe(float("nan"))
    urgent = UrgentReplan()
    error = np.array([0.0, 0, 0, 0, 0, 0.051])
    assert not urgent.observe(error)
    assert urgent.observe(error) and urgent.pending
    assert not urgent.observe(error)  # one request, not an unbounded queue
    assert urgent.consume() and not urgent.pending
    urgent.observe(np.zeros(6))
    assert not urgent.observe(error)


def test_feedback_sign_saturation_rate_and_determinism(dynamic_vehicle):
    t = tracker(dynamic_vehicle)
    ref = np.array([2.0, 0, 0, 0, 0, 0])
    x = ref.copy()
    x[5], x[0] = 0.1, 2.1
    a = t.command(x, ref, np.zeros(2), np.array([1.0, 2.0, 0.1, 0.1]))
    assert a[0][0] == pytest.approx(-0.01)
    assert a[0][1] == pytest.approx(-0.1)
    duplicate = tracker(dynamic_vehicle)
    np.testing.assert_array_equal(
        a[0], duplicate.command(x, ref, np.zeros(2), np.array([1.0, 2.0, 0.1, 0.1]))[0]
    )
    for _ in range(60):
        u, *_ = t.command(x, ref, [4, 100], np.zeros(4))
    np.testing.assert_allclose(u, [0.4, 2])
    assert tracker(dynamic_vehicle, False).command(x, ref, [0, 0.3], np.ones(4))[0][1] == 0.3


def test_tvlqr_dimensions_and_numpy_discrete_jacobian(dynamic_vehicle, straight_geometry):
    model = SymbolicBicycle(dynamic_vehicle, RACING_TIRE_PHYSICS)
    design = TVLQR(model, straight_geometry)
    times, gains = design.compute(packet())
    assert times.shape == (40,) and gains.shape == (40, 4)
    assert np.isfinite(gains).all() and gains[0, 0] > 0
    x, u = np.array([2.0, 0.01, 0.01, 0.02, 1.0, 0.01]), np.array([0.02, 0.1])
    a, b = map(np.asarray, design.jacobian(x, u, 0))
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)

    def step(z, v):
        return plant.step(plant.step(z, v, 0.005), v, 0.005)

    epsilon = 1e-6
    numeric_a = np.column_stack(
        [(step(x + epsilon * e, u) - step(x - epsilon * e, u)) / (2 * epsilon) for e in np.eye(6)]
    )
    numeric_b = np.column_stack(
        [(step(x, u + epsilon * e) - step(x, u - epsilon * e)) / (2 * epsilon) for e in np.eye(2)]
    )
    np.testing.assert_allclose(a, numeric_a, atol=1e-7)
    np.testing.assert_allclose(b, numeric_b, atol=1e-7)


def test_prediction_uses_feedback_without_mutating_tracker(dynamic_vehicle, straight_geometry):
    model = SymbolicBicycle(dynamic_vehicle, RACING_TIRE_PHYSICS)
    predictor = ActuationPredictor(model, straight_geometry)
    b = TrajectoryBuffer()
    b.insert(replace(packet(), controls=np.zeros((4, 2))), 0)
    t = tracker(dynamic_vehicle)
    initial = np.array([2.0, 0, 0, 0, 0, 0.04])
    predicted, command = predictor.predict(initial, 0, 0.05, b, t)
    assert predicted[4] > 0.09 and command[0] < 0
    np.testing.assert_array_equal(t.previous, np.zeros(2))
    with pytest.raises(ValueError):
        predictor.predict(initial, 0, 0.5, b, t)


def test_margin_is_explicit_and_default_preserved(dynamic_vehicle):
    base = MPCProblem(dynamic_vehicle, MPCConfig(horizon=1))
    margin = MPCProblem(dynamic_vehicle, MPCConfig(horizon=1, tracker_margin=0.08))
    assert base.config.tracker_margin == 0
    assert margin.equality_count == base.equality_count
    # Boundary expressions shift; no dimension or bound-array changes.
    np.testing.assert_array_equal(base.lbg, margin.lbg)
    np.testing.assert_array_equal(base.ubg, margin.ubg)
    with pytest.raises(ValueError):
        MPCConfig(tracker_margin=-0.01)


@pytest.mark.parametrize("offset", [0.0, -1e-14, 1e-14])
def test_zoh_node_roundoff_selects_new_interval(offset):
    p = packet()
    np.testing.assert_allclose(p.sample(0.3 + offset)[1], [0.03, 0.3], atol=1e-14)
    np.testing.assert_allclose(p.sample(0.3 + offset)[0], p.states[3], atol=1e-12)


def test_trim_discards_expired_gain_prefix():
    p = packet().trim(0.15)
    assert p.gain_times[0] == 0.15
    assert np.all(p.gain_times >= 0.15)
    np.testing.assert_array_equal(p.sample(0.15)[2], packet().sample(0.15)[2])


def test_prediction_refuses_invalid_stage_domain(dynamic_vehicle, straight_geometry):
    p = ActuationPredictor(SymbolicBicycle(dynamic_vehicle, RACING_TIRE_PHYSICS), straight_geometry)
    b = TrajectoryBuffer()
    b.insert(packet(), 0)
    with pytest.raises(ValueError):
        p.predict([6.1, 0, 0, 0, 0, 0], 0, 0.02, b, tracker(dynamic_vehicle))


@pytest.mark.parametrize("kwargs", [{"dt": 0}, {"steering_rate": -1}, {"speed_kp": float("nan")}])
def test_tracker_rejects_invalid_config(kwargs):
    with pytest.raises(ValueError):
        TrackerConfig(**kwargs)


def test_gain_failure_discards_successful_nominal_packet(
    dynamic_vehicle, straight_geometry, monkeypatch
):
    from apex.control.mpc.controller import make_mpc
    from apex.control.trajectory.planner import TrajectoryPlanner

    controller = make_mpc(dynamic_vehicle, straight_geometry, config=MPCConfig(horizon=4))
    planner = TrajectoryPlanner(controller, straight_geometry)

    def fail_gain(_packet):
        raise np.linalg.LinAlgError("Injected Riccati failure")

    monkeypatch.setattr(planner.gain_builder, "compute", fail_gain)
    result, event = planner.prepare(
        0,
        np.array([2.0, 0, 0, 0, 0, 0]),
        0,
        0,
        TrajectoryBuffer(),
        tracker(dynamic_vehicle),
        startup=True,
    )
    assert result is None
    assert not event["success"]
    assert event["preparation"] == "prediction_or_gain_validation_failed"
