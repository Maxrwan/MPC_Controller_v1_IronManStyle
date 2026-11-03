"""Scripted packet/software fixtures, not NMPC or physical Safety evidence."""

from types import SimpleNamespace

import numpy as np
import pytest

from apex.control.trajectory.packet import TrajectoryBuffer, TrajectoryPacket
from apex.control.trajectory.prediction import RollingDelay, UrgentReplan
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.preintegration.profile import Components
from apex.preintegration.records import Feedback, Prepared
from apex.preintegration.session import ControlSession


def fb(time, sample=0, **kw):
    return Feedback(sample, time, kw.pop("state", (2, 0, 0, 0, 2 * time, 0)), **kw)


def packet(plan_id=0, time=0, estimate=0, state=None):
    state = np.array((2, 0, 0, 0, 2 * time, 0) if state is None else state, dtype=float)
    times = time + estimate + np.arange(5) * 0.1
    states = np.tile(state, (5, 1))
    states[:, 4] = state[4] + 2 * (times - time)
    return TrajectoryPacket(
        plan_id,
        time,
        time,
        time + estimate,
        time,
        times,
        states,
        np.zeros((4, 2)),
        state,
        states[0],
        "SCRIPTED_ONLY",
        0.01,
        0.017,
        times[:-1],
        np.zeros((4, 4)),
    )


class ScriptedPlanner:
    fail = False

    def prepare(self, plan_id, state, time, estimate, buffer, tracker, startup=False):
        return (None if self.fail else packet(plan_id, time, estimate, state)), {
            "success": not self.fail,
            "status": "SCRIPTED_ONLY",
            "plan_id": plan_id,
            "release_time": time,
            "estimated_delay": estimate,
            "predicted_state": (np.array(state) + [0, 0, 0, 0, 2 * estimate, 0]).tolist(),
            "planner_total_time": 0.017,
            "planner_cpu_time": 0.017,
            "solve_time": 0.01,
        }


def factory():
    tracker = TrajectoryTracker(None, [-0.4, -3], [0.4, 2])
    track = SimpleNamespace(length=1000000, sample=lambda s: None)
    return Components(
        SimpleNamespace(solution=None),
        ScriptedPlanner(),
        tracker,
        TrajectoryBuffer(),
        RollingDelay(),
        UrgentReplan(),
        track,
        lambda x, u: None,
        None,
        {"fixture": "SCRIPTED_ONLY"},
    )


def ready():
    session = ControlSession(factory)
    prepared, _ = session.prepare(fb(0), 0, 0, plan_id=0, applied=[0, 0], startup=True)
    assert isinstance(prepared, Prepared)
    assert session.complete(prepared, fb(0), 0).status == "ACCEPTED"
    return session


def test_owned_feedback_and_no_output_startup():
    state = np.array([2, 0, 0, 0, 0, 0.0])
    feedback = Feedback(0, 0, state)
    state[0] = 99
    assert feedback.state[0] == 2
    session = ControlSession(factory)
    result = session.propose(feedback, 0, [0, 0])
    assert result.command is None and result.status == "INHIBITED"
    with pytest.raises(Exception):
        result.status = "VALID_NOMINAL"


def test_session_isolation_reset_and_close():
    a, b = ready(), ready()
    assert a.components.tracker is not b.components.tracker
    assert a.buffer is not b.buffer and a.components.estimator is not b.components.estimator
    assert a.components.urgent is not b.components.urgent
    first = a.propose(fb(0.01, 1), 0.01, [0, 0])
    assert first.command == b.propose(fb(0.01, 1), 0.01, [0, 0]).command
    old_session = a.session_id
    a.reset()
    assert a.session_id != old_session and a.buffer.active is None
    assert not a.components.estimator.samples and a.components.controller.solution is None
    assert a.check_application(first, fb(0.02, 2), 0.02, [0, 0], 0).command is None
    assert a.close().status == a.close().status == "CLOSED"
    assert a.propose(fb(0.03, 3), 0.03, [0, 0]).command is None


def test_old_completion_cannot_reopen_reset():
    session = ControlSession(factory)
    prepared, _ = session.prepare(fb(0), 0, 0, plan_id=0, applied=[0, 0], startup=True)
    session.reset()
    assert session.complete(prepared, fb(0), 0).command is None
    assert session.buffer.active is None and session.inhibited


def test_failed_replacement_preserves_old_authority():
    session = ready()
    old = session.buffer.active
    session.components.planner.fail = True
    prepared, _ = session.prepare(fb(0.1, 1), 0.1, 0, plan_id=1, applied=[0, 0])
    assert session.complete(prepared, fb(0.1, 1), 0.1).status == "REJECTED"
    assert session.buffer.active is old
    assert session.propose(fb(0.11, 2), 0.11, [0, 0]).status == "VALID_NOMINAL"


def test_future_packet_waits_and_stale_replacement_rejects():
    session = ready()
    prepared, _ = session.prepare(fb(0.1, 1), 0.1, 0.1, plan_id=1, applied=[0, 0])
    assert session.complete(prepared, fb(0.11, 2), 0.11).status == "NOT_READY"
    assert session.buffer.active_plan_id == 0
    assert session.offer_waiting(fb(0.19, 3), 0.19).status == "NOT_READY"
    assert session.offer_waiting(fb(0.2, 4), 0.2).status == "ACCEPTED"
    prepared, _ = session.prepare(fb(0.21, 5), 0.21, 0, plan_id=0, applied=[0, 0])
    assert session.complete(prepared, fb(0.21, 5), 0.21).status == "REJECTED"
    assert session.buffer.active_plan_id == 1 and not session.inhibited


def test_busy_is_explicit_and_exceptions_retain_original_type():
    session = ready()
    session.prepare(fb(0.1, 1), 0.1, 0, plan_id=1, applied=[0, 0])
    result, _ = session.prepare(fb(0.11, 2), 0.11, 0, plan_id=2, applied=[0, 0])
    assert result.reasons == ("PREPARATION_BUSY",)
    other = ready()

    def fail(*args):
        raise RuntimeError("literal injected error")

    other.components.validator = fail
    assert other.propose(fb(0.01, 1), 0.01, [0, 0]).command is None
    assert "RuntimeError" in repr(other.events[-1])
    assert "literal injected error" in repr(other.events[-1])


def test_native_gain_failure_discards_scripted_success_without_optimizer(monkeypatch):
    from apex.control.trajectory.planner import TrajectoryPlanner

    planned = packet()
    controller = SimpleNamespace(
        config=SimpleNamespace(dt=0.1),
        compute_control=lambda x, context: None,
        diagnostics=lambda: {
            "success": True,
            "status": "SCRIPTED",
            "solve_time": 0.01,
            "total_compute_time": 0.017,
        },
        solution=(planned.states.T, planned.controls.T, np.zeros((2, 5))),
        last_prediction={"preview": np.zeros((11, 5))},
    )
    planner = object.__new__(TrajectoryPlanner)
    planner.controller = controller

    def fail_gain(value):
        raise np.linalg.LinAlgError("scripted gain failure")

    planner.gain_builder = SimpleNamespace(compute=fail_gain)
    result, event = planner.prepare(
        0, np.array(fb(0).state), 0, 0, TrajectoryBuffer(), factory().tracker, startup=True
    )
    assert result is None and event["success"] is False
    assert event["preparation"] == "prediction_or_gain_validation_failed"


def test_factory_failure_during_reset_cannot_reuse_old_authority():
    session = ready()
    old_buffer = session.buffer

    def broken():
        raise RuntimeError("injected reset construction failure")

    session.factory = broken
    with pytest.raises(RuntimeError, match="reset construction failure"):
        session.reset()
    assert session.inhibited and old_buffer.active is None
    assert session.propose(fb(0.01, 1), 0.01, [0, 0]).command is None


def test_live_sessions_and_resets_reject_shared_mutable_components():
    comp = factory()
    session = ControlSession(lambda: comp)
    with pytest.raises(ValueError, match="ALREADY_OWNED"):
        ControlSession(lambda: comp)
    with pytest.raises(ValueError, match="FRESH_COMPONENT"):
        session.reset()
    assert session.inhibited
    other = ready()
    fresh = ready()
    with pytest.raises(ValueError, match="Cannot replace live"):
        other.bind_buffer(fresh.buffer)
