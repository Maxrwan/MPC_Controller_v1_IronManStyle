"""Scripted chronology and mock application endpoint; not genuine NMPC evidence."""

import numpy as np
from test_async_chronology import StraightPlanner
from test_preintegration_session import factory, fb, ready

from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.preintegration.local import LocalAdapters
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner


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
        plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
        comp.validator = plant.diagnostics
        session = ControlSession(lambda: comp)
        local = LocalAdapters(session)
        runner = AsyncRunner(
            plant,
            local.planner if adapted else comp.planner,
            local.tracker if adapted else comp.tracker,
            straight_geometry,
            AsyncConfig(
                duration=0.24, latency_mode="injected", injected_delay=0.06, codriver_delay=0.025
            ),
            estimator=comp.estimator,
        )
        result = runner.run([2, 0, 0, 0, 0, 0])
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
