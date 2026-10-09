"""Small causal-prefix fixtures using the existing synthetic bicycle and TVLQR law."""

from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest

from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.control.trajectory.packet import TrajectoryBuffer, TrajectoryPacket
from apex.control.trajectory.prediction import ActuationPredictor, CommittedControlPrefix
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner
from apex.simulation.diagnostic_timing import DiagnosticTiming


@pytest.fixture
def rig(dynamic_vehicle, straight_geometry):
    times = np.arange(5) * 0.1
    states = np.zeros((5, 6))
    states[:, 0], states[:, 4] = 2, 2 * times
    packet = TrajectoryPacket(
        1,
        0,
        0,
        0,
        0,
        times,
        states,
        np.tile([0.1, 0.4], (4, 1)),
        states[0],
        states[0],
        "fixture",
        0,
        0,
        times[:-1],
        np.tile([1.0, 2.0, 0.1, 0.1], (4, 1)),
    )
    buffer = TrajectoryBuffer()
    assert buffer.insert(packet, 0)[0]
    tracker = TrajectoryTracker(dynamic_vehicle, [-0.4, -2], [0.4, 2])
    predictor = ActuationPredictor(
        SymbolicBicycle(dynamic_vehicle, RACING_TIRE_PHYSICS), straight_geometry
    )
    return predictor, buffer, tracker


# Captured from the pre-D1 predictor, synthetic fixture above, on the current backend.
# Exact equality is intentional: these guard unchanged arithmetic, not wall-clock time.
@pytest.mark.parametrize(
    "release,duration,expected_state,expected_control",
    [
        (0, 0, [2.1, 0.02, 0.04, 0.01, 1, 0.03], [0.015, 0.2]),
        (
            0.1,
            0.017,
            [
                2.1041052448564472,
                0.018278833687999367,
                0.08776889373253903,
                0.0110353046133599,
                1.0357261620585194,
                0.03069239816802456,
            ],
            [0.025, 0.2979902703744851],
        ),
        (
            0.003,
            0.044,
            [
                2.1123891568752593,
                0.01743818314296077,
                0.15988546101042492,
                0.01491488495243093,
                1.0926444234051063,
                0.031945067368932135,
            ],
            [0.022967186656247973, 0.289658734941162],
        ),
        (
            0.1,
            0.02,
            [
                2.1050042850779054,
                0.018204368467568278,
                0.09727095549627177,
                0.011313142677778717,
                1.0420388206928017,
                0.0308176672278721,
            ],
            [0.025, 0.2979902703744851],
        ),
    ],
)
def test_legacy_exact_golden(rig, release, duration, expected_state, expected_control):
    predictor, buffer, tracker = rig
    tracker.previous = np.array([0.015, 0.2])
    x = [2.1, 0.02, 0.04, 0.01, 1, 0.03]
    omitted = predictor.predict(x, release, duration, buffer, tracker)
    explicit = predictor.predict(x, release, duration, buffer, tracker, committed_prefix=None)
    for answer in (omitted, explicit):
        np.testing.assert_array_equal(answer[0], expected_state)
        np.testing.assert_array_equal(answer[1], expected_control)


@pytest.mark.parametrize("target", [0.019, 0.025 - 1e-6, 0.025, 0.027])
def test_pending_application_time_and_held_physics(rig, target):
    predictor, buffer, tracker = rig
    prefix = CommittedControlPrefix(0, (0, 0), 0, (0, 0.5), 0.025)
    x, u = predictor.predict(
        [2, 0, 0, 0, 0, 0], 0, target, buffer, tracker, committed_prefix=prefix
    )
    elapsed = max(0, target - 0.025)
    # Exact straight-line constant-acceleration solution of the approved bicycle.
    # 1e-12 absolute permits only float summation roundoff in a <30 ms fixture.
    np.testing.assert_allclose(
        x,
        [2 + 0.5 * elapsed, 0, 0, 0, 2 * target + 0.25 * elapsed**2, 0],
        rtol=0,
        atol=1e-12,
    )
    np.testing.assert_array_equal(u, [0, 0.5 if target >= 0.025 else 0])


def test_application_steering_limit_and_resume_without_catchup(rig, monkeypatch):
    predictor, buffer, tracker = rig
    prefix = CommittedControlPrefix(0, (0, 0), 0, (-0.1, 0.5), 0.019)
    calls = []
    command = TrajectoryTracker.command

    def observe(self, *args):
        calls.append(args[0].copy())
        return command(self, *args)

    monkeypatch.setattr(TrajectoryTracker, "command", observe)
    x = [2, 0, 0, 0, 0, 0]
    _, at_application = predictor.predict(x, 0, 0.019, buffer, tracker, committed_prefix=prefix)
    assert not calls  # The 10 ms tick was busy; no forecast command was generated.
    assert at_application[0] == pytest.approx(-0.019, abs=1e-15)
    _, resumed = predictor.predict(x, 0, 0.021, buffer, tracker, committed_prefix=prefix)
    assert len(calls) == 1  # Only the 20 ms tick, not the missed 10 ms tick.
    # TVLQR requests increasing steering; only 1 ms since the pending application.
    assert resumed[0] == pytest.approx(-0.018, abs=1e-15)


@pytest.mark.parametrize("target,expected_calls", [(0.02, 0), (0.021, 1)])
def test_pending_tick_target_order(rig, monkeypatch, target, expected_calls):
    predictor, buffer, tracker = rig
    calls = []
    command = TrajectoryTracker.command

    def observe(self, *args):
        calls.append(args[0].copy())
        return command(self, *args)

    monkeypatch.setattr(TrajectoryTracker, "command", observe)
    prefix = CommittedControlPrefix(0, (0, 0), 0, (-0.1, 0.5), 0.02)
    _, u = predictor.predict(
        [2, 0, 0, 0, 0, 0], 0, target, buffer, tracker, committed_prefix=prefix
    )
    assert len(calls) == expected_calls
    # Application precedes a coincident tick. Its second application has zero elapsed
    # time, so new feedback may change acceleration, but cannot change steering yet.
    assert u[0] == pytest.approx(-0.02, abs=1e-15)
    assert u[1] == pytest.approx(0.5 if target == 0.02 else 0.4, abs=1e-15)


def test_due_at_release_zero_target(rig):
    predictor, buffer, tracker = rig
    initial = [2, 0, 0, 0, 0.2, 0]
    prefix = CommittedControlPrefix(0.1, (0, 0), 0.09, (0.1, 0.5), 0.1)
    x, u = predictor.predict(initial, 0.1, 0, buffer, tracker, committed_prefix=prefix)
    np.testing.assert_array_equal(x, initial)
    np.testing.assert_allclose(u, [0.01, 0.5], atol=1e-15, rtol=0)


@pytest.mark.parametrize("target", [0.02, 0.025, 0.03, 0.04])
def test_agrees_with_existing_runner_before_handoff(
    rig, dynamic_vehicle, straight_geometry, target
):
    predictor, buffer, tracker = rig
    packet = buffer.active
    initial = np.array([2, 0, 0, 0, 0, 0.03])
    applied = packet.controls[0].copy()
    release_tracker = tracker.clone()
    release_tracker.previous = applied.copy()
    known_request = release_tracker.update(initial, buffer, 0)[0]
    prefix = CommittedControlPrefix(0, applied, 0, known_request, 0.025)

    class StartupOnly:
        def prepare(self, plan_id, state, time, estimate, buffer, tracker, *, startup=False):
            assert startup  # No later planner or future new-packet authority in this fixture.
            return replace(packet, plan_id=plan_id), {"success": True}

    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    result = AsyncRunner(
        plant,
        StartupOnly(),
        tracker,
        straight_geometry,
        AsyncConfig(duration=0.05, urgent=False),
        timing=DiagnosticTiming("replay", (0,), (0.025, 0, 0, 0, 0)),
    ).run(initial)
    assert result["failure"] is None
    predicted, u = predictor.predict(
        initial, 0, target, buffer, release_tracker, committed_prefix=prefix
    )
    row = next(s for s in result["states"] if abs(s["time"] - target) < 1e-12)
    actual = [row[k] for k in ["vx", "vy", "r", "e_psi", "s_abs", "e_y"]]
    # Independent NumPy/CasADi arithmetic and plant heading wrapping differ by roundoff.
    np.testing.assert_allclose(predicted, actual, rtol=0, atol=1e-12)
    prior = [
        c
        for c in result["controls"]
        if c["application_time"] <= target + 1e-12 and c["time"] < target - 1e-12
    ]
    expected = [prior[-1]["delta"], prior[-1]["a_cmd"]] if prior else applied
    np.testing.assert_allclose(u, expected, rtol=0, atol=1e-12)


def test_immutable_owned_snapshot_and_no_caller_mutation(rig):
    predictor, buffer, tracker = rig
    applied, pending = np.array([0, 0.0]), np.array([0.1, 0.5])
    prefix = CommittedControlPrefix(0, applied, 0, pending, 0.025)
    applied[:] = pending[:] = 99
    assert prefix.applied_control == (0, 0) and prefix.pending_control == (0.1, 0.5)
    with pytest.raises(FrozenInstanceError):
        prefix.release_time = 1
    with pytest.raises(TypeError):
        prefix.pending_control[0] = 1
    state = np.array([2, 0, 0, 0, 0, 0.0])
    before_state, before_tracker = state.copy(), tracker.previous.copy()
    packet, before_packet = buffer.active, buffer.active.as_dict()
    a = predictor.predict(state, 0, 0.034, buffer, tracker, committed_prefix=prefix)
    b = predictor.predict(state, 0, 0.034, buffer, tracker, committed_prefix=prefix)
    for aa, bb in zip(a, b):
        np.testing.assert_array_equal(aa, bb)
    np.testing.assert_array_equal(state, before_state)
    np.testing.assert_array_equal(tracker.previous, before_tracker)
    assert buffer.active is packet and packet.as_dict() == before_packet
    assert prefix.pending_control == (0.1, 0.5)


def test_no_future_truth_or_timing_and_release_packet_is_pinned(rig, monkeypatch):
    from apex.optimization.solvers.ipopt import IpoptSolver

    predictor, buffer, tracker = rig
    prefix = CommittedControlPrefix(0, (0, 0), 0)
    initial = [2, 0, 0, 0, 0, 0]
    expected = predictor.predict(initial, 0, 0.034, buffer, tracker, committed_prefix=prefix)

    def forbidden(*args, **kwargs):
        raise AssertionError("Predictor requested future solver/plant/timing information")

    monkeypatch.setattr(DynamicBicycle, "step", forbidden)
    monkeypatch.setattr(IpoptSolver, "solve", forbidden)
    monkeypatch.setattr(DiagnosticTiming, "planner_delay", forbidden)
    monkeypatch.setattr(DiagnosticTiming, "codriver_delay", forbidden)
    command = TrajectoryTracker.command
    future = replace(buffer.active, plan_id=2, controls=np.full((4, 2), -0.1))

    def external_takeover(self, *args):
        buffer.active = future  # Simulated external replacement; predictor must pin the old packet.
        return command(self, *args)

    monkeypatch.setattr(TrajectoryTracker, "command", external_takeover)
    actual = predictor.predict(initial, 0, 0.034, buffer, tracker, committed_prefix=prefix)
    for aa, bb in zip(actual, expected):
        np.testing.assert_array_equal(aa, bb)


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "expired",
        "future",
        "invalid",
        "beyond_horizon",
        "invalid_state",
        "zero_invalid_state",
        "bounds",
        "release",
    ],
)
def test_invalid_or_unavailable_prefix_fails(rig, kind):
    predictor, buffer, tracker = rig
    state, release, duration = [2, 0, 0, 0, 0, 0], 0, 0.015
    if kind == "missing":
        buffer.active = None
    elif kind == "expired":
        release, duration = 0.4, 0
    elif kind == "future":
        buffer.active = replace(buffer.active, timestamps=buffer.active.timestamps + 0.1)
    elif kind == "invalid":
        buffer.active = replace(buffer.active, valid=False)
    elif kind == "beyond_horizon":
        duration = 0.401
    elif kind in ("invalid_state", "zero_invalid_state"):
        state[0] = 0.4
        duration = 0 if kind == "zero_invalid_state" else duration
    prefix = CommittedControlPrefix(release, (0.5 if kind == "bounds" else 0, 0), 0)
    if kind == "release":
        prefix = replace(prefix, release_time=0.001)
    with pytest.raises(ValueError):
        predictor.predict(state, release, duration, buffer, tracker, committed_prefix=prefix)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"release_time": -1},
        {"release_time": float("nan")},
        {"last_application_time": 0.1},
        {"applied_control": [0]},
        {"applied_control": [0, float("nan")]},
        {"applied_control": None},
        {"pending_control": [0, 0]},
        {"pending_application_time": 0.1},
        {"pending_control": [0, 0], "pending_application_time": -0.01},
        {"pending_control": [0, 0], "pending_application_time": float("inf")},
    ],
)
def test_snapshot_rejects_inconsistent_information(kwargs):
    values = dict(release_time=0, applied_control=(0, 0), last_application_time=0)
    with pytest.raises(ValueError):
        CommittedControlPrefix(**(values | kwargs))
