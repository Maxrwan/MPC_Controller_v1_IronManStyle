"""Delegates around the existing AsyncRunner; no new event scheduler or endpoint."""

from time import perf_counter

from apex.control.trajectory.tracker import TrajectoryTracker

from .records import Feedback, Prepared


class LocalAdapters:
    def __init__(self, session, *, stop_on_preparation_failure=False):
        self.session = session
        self.stop_on_preparation_failure = stop_on_preparation_failure
        self.sample_id, self.sample = -1, None
        self.prepared, self.event = None, None
        self.boundary_times = []
        self.tracker = TrackerDelegate(self)
        self.planner = PlannerDelegate(self)

    def feedback(self, state, now):
        candidate = tuple(map(float, state))
        if self.sample is None or self.sample.time != now or self.sample.state != candidate:
            self.sample_id += 1
            self.sample = Feedback(self.sample_id, float(now), candidate, self.session.clock)
        return self.sample

    def completion(self):
        if self.prepared is not None and (self.event.get("startup") or self.event.get("completed")):
            self.session.observe_completion(
                self.prepared, self.event["completion_time"], observe_delay=False
            )
            self.prepared = None


class PlannerDelegate:
    def __init__(self, owner):
        self.owner = owner

    def prepare(self, plan_id, state, time, estimate, buffer, tracker, *, startup=False):
        owner, start = self.owner, perf_counter()
        owner.completion()
        if owner.session.buffer is not buffer:
            owner.session.bind_buffer(buffer)
        result, event = owner.session.prepare(
            owner.feedback(state, time),
            time,
            estimate,
            plan_id=plan_id,
            applied=tracker.previous,
            startup=startup,
        )
        if not isinstance(result, Prepared):
            from apex.models.errors import ModelValidationError

            raise ModelValidationError("Local preparation inhibited: " + str(result.reasons))
        owner.prepared, owner.event = result, event
        owner.boundary_times.append(
            {
                "operation": "prepare",
                "plan_id": plan_id,
                "wall_seconds": perf_counter() - start,
                "native_seconds": event["planner_total_time"],
            }
        )
        if owner.stop_on_preparation_failure and (
            result.packet is None
            or event.get("success") is not True
            or event.get("max_slack") is None
            or event["max_slack"] > 1e-6
        ):
            from apex.models.errors import ModelValidationError

            raise ModelValidationError("Genuine attempt stopped at preparation/scientific gate")
        return result.packet, event


class TrackerDelegate(TrajectoryTracker):
    def __init__(self, owner):
        # The frozen release observer accepts TVLQR trackers via isinstance. All state and
        # calculations stay in the already constructed native tracker; do not initialize a copy.
        if not isinstance(owner.session.components.tracker, TrajectoryTracker):
            raise TypeError("Local adapter requires the accepted TVLQR tracker")
        self.owner = owner

    @property
    def native(self):
        return self.owner.session.components.tracker

    @property
    def previous(self):
        return self.native.previous

    @previous.setter
    def previous(self, value):
        self.native.previous = value

    def __getattr__(self, name):
        return getattr(self.native, name)

    def clone(self):
        return (
            self.native.clone()
        )  # Predictor receives detached native tracker, no session callbacks.

    def update(self, state, buffer, time):
        owner, start = self.owner, perf_counter()
        owner.completion()
        if buffer is not owner.session.buffer:
            raise ValueError("Authority buffer mismatch")
        result = owner.session.propose(owner.feedback(state, time), time, self.previous)
        if result.command is None:
            from apex.models.errors import ModelValidationError

            raise ModelValidationError("Local output inhibited: " + str(result.reasons))
        owner.boundary_times.append(
            {
                "operation": "propose",
                "time": time,
                "wall_seconds": perf_counter() - start,
                "native_seconds": owner.session.last_tracker_diagnostics["total_time"],
            }
        )
        import numpy as np

        return np.array(result.command), owner.session.last_tracker_diagnostics
