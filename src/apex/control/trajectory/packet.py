"""Immutable nominal trajectories with physical-time interpolation; no extrapolation."""

from dataclasses import dataclass, field, replace

import numpy as np

from apex.state import StateIndex as S


@dataclass(frozen=True)
class TrajectoryPacket:
    plan_id: int
    planner_release_time: float
    planner_sample_time: float
    intended_handoff_time: float
    actual_completion_time: float
    timestamps: np.ndarray
    states: np.ndarray
    controls: np.ndarray
    source_sampled_state: np.ndarray
    predicted_handoff_state: np.ndarray
    solver_status: str
    solve_duration: float
    total_computation_duration: float
    gain_times: np.ndarray = field(default_factory=lambda: np.empty(0))
    gains: np.ndarray = field(default_factory=lambda: np.empty((0, 4)))
    curvatures: np.ndarray = field(default_factory=lambda: np.empty(0))
    valid: bool = True
    validation_reason: str = "solver_and_model_valid"

    def __post_init__(self):
        for name in (
            "timestamps",
            "states",
            "controls",
            "source_sampled_state",
            "predicted_handoff_state",
            "gain_times",
            "gains",
            "curvatures",
        ):
            value = np.array(getattr(self, name), dtype=float, copy=True)
            if not np.isfinite(value).all():
                raise ValueError(f"Nonfinite {name}")
            if name == "states" and value.ndim == 2 and value.shape[1] == 6:
                value[:, S.E_PSI] = np.unwrap(value[:, S.E_PSI])
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        if self.timestamps.ndim != 1:
            raise ValueError("Timestamps must be one-dimensional")
        n = len(self.timestamps)
        if (
            n < 2
            or self.timestamps.ndim != 1
            or np.any(np.diff(self.timestamps) <= 0)
            or self.states.shape != (n, 6)
            or self.controls.shape != (n - 1, 2)
            or self.source_sampled_state.shape != (6,)
            or self.predicted_handoff_state.shape != (6,)
        ):
            raise ValueError("Invalid trajectory dimensions/timestamps")
        if np.any(np.diff(self.states[:, S.S_ABS]) < -1e-9):
            raise ValueError("Progress must remain continuous and nondecreasing")
        if self.gains.shape != (len(self.gain_times), 4) or (
            len(self.gain_times) and np.any(np.diff(self.gain_times) <= 0)
        ):
            raise ValueError("Invalid feedback gain schedule")
        if self.curvatures.shape not in ((0,), (n,)):
            raise ValueError("Curvatures must match nominal state nodes")
        metadata = [
            self.planner_release_time,
            self.planner_sample_time,
            self.intended_handoff_time,
            self.actual_completion_time,
            self.solve_duration,
            self.total_computation_duration,
        ]
        if not np.isfinite(metadata).all() or min(metadata) < 0:
            raise ValueError("Invalid packet timing metadata")
        if self.actual_completion_time < self.planner_release_time:
            raise ValueError("Completion precedes release")

    @property
    def horizon_end_time(self):
        return float(self.timestamps[-1])

    @property
    def remaining_reserve_at_completion(self):
        return self.horizon_end_time - self.actual_completion_time

    def sample(self, time):
        if (
            not np.isfinite(time)
            or time < self.timestamps[0] - 1e-10
            or time > self.timestamps[-1] + 1e-10
        ):
            raise ValueError("Trajectory unavailable at requested physical time")
        time = float(np.clip(time, self.timestamps[0], self.timestamps[-1]))
        i = min(
            np.searchsorted(self.timestamps, time + 1e-10, side="right") - 1, len(self.controls) - 1
        )
        a = (time - self.timestamps[i]) / (self.timestamps[i + 1] - self.timestamps[i])
        a = float(np.clip(a, 0, 1))
        x = (1 - a) * self.states[i] + a * self.states[i + 1]
        k = np.zeros(4)
        if len(self.gain_times):
            j = max(
                0,
                min(
                    np.searchsorted(self.gain_times, time + 1e-10, side="right") - 1,
                    len(self.gains) - 1,
                ),
            )
            k = self.gains[j].copy()
        return x, self.controls[i].copy(), k

    def curvature(self, time):
        if not len(self.curvatures):
            raise ValueError("No nominal curvature preview")
        if time < self.timestamps[0] - 1e-10 or time > self.horizon_end_time + 1e-10:
            raise ValueError("Curvature outside trajectory")
        i = max(
            0,
            min(
                np.searchsorted(self.timestamps, time + 1e-10, side="right") - 1,
                len(self.curvatures) - 1,
            ),
        )
        return float(self.curvatures[i])

    def trim(self, time):
        if time <= self.timestamps[0]:
            return self
        if time >= self.horizon_end_time:
            raise ValueError("Cannot accept exhausted plan")
        times = np.r_[time, self.timestamps[self.timestamps > time + 1e-12]]
        states = np.array([self.sample(t)[0] for t in times])
        controls = np.array([self.sample(t)[1] for t in times[:-1]])
        curvatures = (
            np.array([self.curvature(t) for t in times])
            if len(self.curvatures)
            else self.curvatures
        )
        gain_times, gains = self.gain_times, self.gains
        if len(gain_times):
            keep = gain_times > time + 1e-10
            gains = np.vstack([self.sample(time)[2], gains[keep]])
            gain_times = np.r_[time, gain_times[keep]]
        return replace(
            self,
            timestamps=times,
            states=states,
            controls=controls,
            curvatures=curvatures,
            gain_times=gain_times,
            gains=gains,
        )

    def as_dict(self):
        return {
            **{k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in vars(self).items()},
            "horizon_end_time": self.horizon_end_time,
            "remaining_reserve_at_completion": self.remaining_reserve_at_completion,
        }


class TrajectoryBuffer:
    def __init__(self, minimum_handoff_reserve=0.05):
        self.active = None
        self.minimum_handoff_reserve = minimum_handoff_reserve

    @property
    def active_plan_id(self):
        return None if self.active is None else self.active.plan_id

    def reserve(self, time):
        return 0.0 if self.active is None else max(0.0, self.active.horizon_end_time - time)

    def category(self, time):
        reserve = self.reserve(time)
        return (
            "exhausted"
            if reserve <= 1e-10
            else "critical"
            if reserve < 0.05
            else "warning"
            if reserve < 0.20
            else "healthy"
        )

    def insert(self, packet, time):
        if not packet.valid:
            return False, packet.validation_reason
        if self.active is not None and packet.plan_id <= self.active.plan_id:
            return False, "stale_plan"
        if time < packet.actual_completion_time - 1e-10 or time < packet.timestamps[0] - 1e-10:
            return False, "not_available_yet"
        if packet.horizon_end_time - time < self.minimum_handoff_reserve:
            return False, "insufficient_reserve"
        self.active = packet.trim(time)
        return True, "accepted"

    def sample(self, time):
        if self.active is None or self.category(time) == "exhausted":
            raise ValueError("No unexpired active trajectory")
        return self.active.sample(time)
