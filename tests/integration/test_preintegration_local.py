"""Scripted chronology and mock application endpoint; not genuine NMPC evidence."""

import sys
from pathlib import Path

import numpy as np

from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.preintegration.local import LocalAdapters
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

# Existing unit fixtures are explicit local test inputs, independent of collection order.
UNIT = Path(__file__).resolve().parents[1] / "unit"
if str(UNIT) not in sys.path:
    sys.path.insert(0, str(UNIT))
from test_async_chronology import StraightPlanner  # noqa: E402
from test_preintegration_session import factory, fb, ready  # noqa: E402


def test_native_and_local_delegates_preserve_scripted_chronology(
    dynamic_vehicle, straight_geometry
):
    from apex.preintegration.session import ControlSession

    def run(adapted):
        comp = factory()
        comp.planner, comp.parameters, comp.track = (
            StraightPlanner(),
            dynamic_vehicle,
            straight_geometry,
        )
        comp.tracker.parameters = dynamic_vehicle
        plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
        comp.validator = plant.diagnostics
        session = ControlSession(lambda: comp)
        local = LocalAdapters(session)
        releases = []
        runner = AsyncRunner(
            plant,
            local.planner if adapted else comp.planner,
            local.tracker if adapted else comp.tracker,
            straight_geometry,
            AsyncConfig(
                duration=0.24, latency_mode="injected", injected_delay=0.06, codriver_delay=0.025
            ),
            estimator=comp.estimator,
            release_observer=releases.append,
        )
        result = runner.run([2, 0, 0, 0, 0, 0])
        assert releases and releases[0].parameters is dynamic_vehicle
        assert releases[0].prefix.release_time == 0.1
        return result, local, session

    native, _, _ = run(False)
    actual, local, session = run(True)
    assert actual["failure"] is None and actual["end_time"] == 0.24
    assert actual["states"] == native["states"]
    assert actual["handoffs"] == native["handoffs"]
    keys = ("time", "application_time", "plan_id", "delta", "a_cmd", "mode")
    assert [[r[k] for k in keys] for r in actual["controls"]] == [
        [r[k] for k in keys] for r in native["controls"]
    ]
    assert actual["codriver_misses"] == native["codriver_misses"]
    assert actual["states"][-1]["s_abs"] > 0.4
    assert local.boundary_times and any(e.operation == "propose" for e in session.events)
    assert local.tracker.clone() is not session.components.tracker


def test_mock_endpoint_receives_only_application_checked_command():
    session, endpoint = ready(), []
    proposal = session.propose(fb(0.01, 1), 0.01, [0, 0])
    checked = session.check_application(proposal, fb(0.02, 2), 0.02, [0, 0], 0)
    assert checked.stage == "application_checked"
    if checked.command is not None:
        endpoint.append(checked.command)
    np.testing.assert_array_equal(
        endpoint, [(0, 0)]
    )  # Valid scripted nominal, never a stop default.
    result = session.check_application(proposal, fb(0.03, 3), 0.03, [0, 0], 0)
    if result.command is not None:
        endpoint.append(result.command)
    assert len(endpoint) == 1 and result.status == "INHIBITED"


def test_genuine_guard_stops_on_scripted_preparation_failure_before_continuation():
    import pytest

    from apex.models.errors import ModelValidationError
    from apex.preintegration.session import ControlSession

    session = ControlSession(factory)
    session.components.planner.fail = True
    local = LocalAdapters(session, stop_on_preparation_failure=True)
    with pytest.raises(ModelValidationError, match="preparation/scientific gate"):
        local.planner.prepare(
            0, np.array(fb(0).state), 0, 0, session.buffer, local.tracker, startup=True
        )
    assert session.buffer.active is None
    assert session.events[-1].status == "REJECTED"


def test_frozen_release_capture_accepts_typed_delegate_and_bound_runtime_state(dynamic_vehicle):
    """Pure callback regression with a literal packet: zero solves and zero plant steps."""
    from test_preintegration_session import packet

    from apex.control.trajectory.packet import TrajectoryBuffer
    from apex.control.trajectory.prediction import CommittedControlPrefix, UrgentReplan
    from apex.control.trajectory.tracker import TrajectoryTracker
    from apex.preintegration.session import ControlSession
    from apex.simulation.prediction_capture import PredictionRelease

    comp = factory()
    comp.tracker.parameters = dynamic_vehicle
    session = ControlSession(lambda: comp)
    buffer, urgent = TrajectoryBuffer(), UrgentReplan()
    session.bind_buffer(buffer)
    session.bind_urgent(urgent)
    assert buffer.insert(packet(), 0)[0]
    local = LocalAdapters(session)
    prefix = CommittedControlPrefix(0.1, (0, 0), 0.09, (0, 0), 0.125)
    release = PredictionRelease.capture(1, fb(0.1).state, 0.06, prefix, buffer, local.tracker)
    assert isinstance(local.tracker, TrajectoryTracker)
    assert release.parameters is dynamic_vehicle and release.prefix == prefix
    assert release.packet.plan_id == 0 and release.state == fb(0.1).state
    assert session.components.urgent is urgent and session.buffer is buffer
    assert local.tracker.clone() is not comp.tracker
