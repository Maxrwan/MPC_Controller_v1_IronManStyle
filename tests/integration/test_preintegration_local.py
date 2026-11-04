"""Scripted chronology and mock application endpoint; not genuine NMPC evidence."""

import sys
from pathlib import Path

import numpy as np
import pytest

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


@pytest.mark.parametrize("mode", ["zero", "injected"])
def test_scientific_completion_audits_scripted_native_chronology(
    dynamic_vehicle, straight_geometry, mode
):
    """Analytical straight motion and literal successful packets; no optimizer calls."""
    from dataclasses import replace

    from preintegration.evidence import audit_completion

    from apex.preintegration.session import ControlSession

    class AuditPlanner(StraightPlanner):
        def prepare(self, plan_id, state, time, estimate, buffer, tracker, startup=False):
            packet, event = super().prepare(
                plan_id, state, time, estimate, buffer, tracker, startup
            )
            event.update(
                max_slack=0.0,
                predicted_completion_time=time + estimate,
                source_state=state.tolist(),
            )
            return packet, event

    segments = []

    class ObservedPlant(DynamicBicycle):
        physical_time = 0.0

        def step(self, x, u, dt):
            end = super().step(x, u, dt)
            segments.append(
                dict(
                    start=self.physical_time,
                    end=self.physical_time + dt,
                    dt=dt,
                    state_before=x.copy(),
                    state_after=end.copy(),
                    control=u.copy(),
                )
            )
            self.physical_time += dt
            return end

    comp = factory()
    comp.planner, comp.parameters, comp.track = AuditPlanner(), dynamic_vehicle, straight_geometry
    comp.tracker.parameters = dynamic_vehicle
    plant = ObservedPlant(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    comp.validator = plant.diagnostics
    session = ControlSession(lambda: comp)
    local, releases = LocalAdapters(session), []
    sim = AsyncConfig(
        duration=0.24,
        latency_mode=mode,
        injected_delay=0.06 if mode == "injected" else 0,
        codriver_delay=0.025 if mode == "injected" else 0,
    )
    runner = AsyncRunner(
        plant,
        local.planner,
        local.tracker,
        straight_geometry,
        sim,
        estimator=comp.estimator,
        release_observer=releases.append,
    )
    raw = runner.run([2, 0, 0, 0, 0, 0])
    local.completion()
    result = audit_completion(
        raw, segments, session.events, straight_geometry, sim, comp.tracker, releases
    )
    assert result["valid_prerequisite"], result
    assert result["execution_completed"]
    # An execution ending at the requested time is insufficient if its boundary record is invalid.
    raw["states"][0]["boundary_violation"] = True
    bad = audit_completion(
        raw, segments, session.events, straight_geometry, sim, comp.tracker, releases
    )
    assert bad["execution_completed"] and not bad["valid_prerequisite"]
    assert any(e["reason"] == "RECORDED_BOUNDARY_VIOLATION" for e in bad["errors"])
    raw["states"][0]["boundary_violation"] = False
    # Exact existing widths include equality; the terminal endpoint must also be checked.
    last = segments[-1]["state_after"].copy()
    segments[-1]["state_after"][5] = 10.0
    assert audit_completion(
        raw, segments, session.events, straight_geometry, sim, comp.tracker, releases
    )["valid_prerequisite"]
    segments[-1]["state_after"][5] = 10.0 + 1e-8
    assert not audit_completion(
        raw, segments, session.events, straight_geometry, sim, comp.tracker, releases
    )["valid_prerequisite"]
    segments[-1]["state_after"] = last
    # Negative expectations follow literal scheduler ordering, not the audit's own output.
    import copy

    for mutate in (
        lambda r: r["controls"][0].update(application_time=-0.01),
        lambda r: r["controls"][0].update(plan_id=999),
        lambda r: r["controls"][0].update(requested_a_cmd=0.5),
        lambda r: r["states"][0].update(s_abs=3.0),
        lambda r: r["packets"][0].update(actual_completion_time=0.2),
        lambda r: r["handoffs"][0].update(accepted=False),
        lambda r: r["plans"][0].update(max_slack=0.1),
        lambda r: r["controls"].reverse(),
    ):
        corrupted = copy.deepcopy(raw)
        mutate(corrupted)
        assert not audit_completion(
            corrupted, segments, session.events, straight_geometry, sim, comp.tracker, releases
        )["valid_prerequisite"]
    events = session.events.copy()
    events[3] = replace(events[3], time=0.23)
    assert not audit_completion(
        raw, segments, events, straight_geometry, sim, comp.tracker, releases
    )["valid_prerequisite"]
