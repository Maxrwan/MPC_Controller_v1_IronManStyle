"""Opt-in release records for offline prediction diagnostics; no future history."""

from dataclasses import dataclass, replace

from apex.control.trajectory.packet import TrajectoryBuffer, TrajectoryPacket
from apex.control.trajectory.prediction import CommittedControlPrefix
from apex.control.trajectory.tracker import TrackerConfig, TrajectoryTracker
from apex.models.vehicle.parameters import VehicleParameters
from apex.state import state_vector


@dataclass(frozen=True)
class PredictionRelease:
    plan_id: int
    state: tuple[float, ...]
    estimated_delay: float
    prefix: CommittedControlPrefix
    packet: TrajectoryPacket | None
    parameters: VehicleParameters
    tracker_config: TrackerConfig
    lower: tuple[float, float]
    upper: tuple[float, float]

    @classmethod
    def capture(cls, plan_id, state, estimate, prefix, buffer, tracker):
        # Restrict this diagnostic to the authorized TVLQR, not arbitrary controller clones.
        if not isinstance(tracker, TrajectoryTracker):
            raise TypeError("Prediction capture requires the TVLQR tracker")
        return cls(
            plan_id,
            tuple(state_vector(state)),
            float(estimate),
            prefix,
            None if buffer.active is None else replace(buffer.active),
            tracker.parameters,
            tracker.config,
            tuple(tracker.lower),
            tuple(tracker.upper),
        )

    def forecast_inputs(self):
        """Fresh private buffer/tracker for each alternative; no live controller reference."""
        buffer = TrajectoryBuffer()
        buffer.active = None if self.packet is None else replace(self.packet)
        tracker = TrajectoryTracker(self.parameters, self.lower, self.upper, self.tracker_config)
        tracker.previous[:] = self.prefix.applied_control
        return buffer, tracker
