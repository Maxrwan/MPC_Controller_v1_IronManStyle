"""Replaceable delay estimate and independent closed-loop actuation-state prediction."""

from collections import deque
from dataclasses import dataclass

import casadi as ca
import numpy as np

from apex.control.trajectory.packet import TrajectoryBuffer
from apex.state import StateIndex as S
from apex.state import control_vector, state_vector


@dataclass(frozen=True)
class CommittedControlPrefix:
    """Release-known actuator state; commands are owned immutable SI tuples.

    Capture after the release-time codriver tick has been processed. A pending
    command may be due at release (new zero-latency work), but never in the past.
    Future feedback remains a prediction, not part of this commitment.
    """

    release_time: float
    applied_control: tuple[float, float]
    last_application_time: float
    pending_control: tuple[float, float] | None = None
    pending_application_time: float | None = None

    def __post_init__(self):
        for name in ("release_time", "last_application_time"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value < 0:
                raise ValueError("Finite nonnegative actuator timestamps required")
            object.__setattr__(self, name, value)
        if self.last_application_time > self.release_time:
            raise ValueError("Last application cannot be after release")
        if (self.pending_control is None) != (self.pending_application_time is None):
            raise ValueError("Pending command and application time must be supplied together")
        for name in ("applied_control", "pending_control"):
            value = getattr(self, name)
            if name == "applied_control" or value is not None:
                object.__setattr__(self, name, tuple(map(float, control_vector(value))))
        if self.pending_application_time is not None:
            due = float(self.pending_application_time)
            if not np.isfinite(due) or due < self.release_time:
                raise ValueError("Pending application cannot precede release")
            object.__setattr__(self, "pending_application_time", due)


class RollingDelay:
    def __init__(self, initial=0.017, window=10, maximum=0.30):
        if not np.isfinite(initial) or not 0 <= initial <= maximum or window < 1:
            raise ValueError("Invalid delay estimator")
        self.initial, self.maximum = initial, maximum
        self.samples = deque(maxlen=window)

    def estimate(self):
        return float(
            np.clip(np.median(self.samples) if self.samples else self.initial, 0, self.maximum)
        )

    def observe(self, duration):
        if not np.isfinite(duration) or duration < 0:
            raise ValueError("Nonnegative finite computation duration required")
        self.samples.append(float(duration))


class ActuationPredictor:
    def __init__(self, model, track):
        self.track = track
        x, u, k, h = ca.SX.sym("x", 6), ca.SX.sym("u", 2), ca.SX.sym("k"), ca.SX.sym("h")
        f = model.derivative
        a = f(x, u, k)
        b = f(x + h * a / 2, u, k)
        c = f(x + h * b / 2, u, k)
        d = f(x + h * c, u, k)
        end = x + h * (a + 2 * b + 2 * c + d) / 6
        stages = [x, x + h * a / 2, x + h * b / 2, x + h * c, end]
        domains = ca.horzcat(*[model.domain(v, k) for v in stages])
        self.step = ca.Function("handoff_prediction", [x, u, k, h], [end, domains])
        self.maximum_speed = model.parameters.maximum_speed

    def predict(self, state, time, duration, buffer, tracker, *, committed_prefix=None):
        """Forecast to time + duration; omitting the snapshot preserves legacy behavior.

        With a snapshot, replay its pending application before coincident feedback
        ticks, and before returning at the target. Do not generate feedback at the
        target: handoff precedes that tick in AsyncRunner. See the D1 contract.
        """
        if not np.isfinite([time, duration]).all() or min(time, duration) < 0:
            raise ValueError("Invalid forecast time")
        x, t, end = state_vector(state), time, time + duration
        if buffer.active is None or end > buffer.active.horizon_end_time + 1e-10:
            raise ValueError("Prediction exceeds active trajectory")
        local = tracker.clone()
        next_tick = (int(np.floor((time + 1e-9) / local.config.dt)) + 1) * local.config.dt
        pending, due, last_application = None, None, None
        if committed_prefix is not None:
            if committed_prefix.release_time != time:
                raise ValueError("Snapshot release must match forecast release")
            # Pin the release-active immutable packet, never a future buffer takeover.
            released = TrajectoryBuffer()
            released.active = buffer.active
            buffer = released
            if not buffer.active.valid or buffer.active.actual_completion_time > time + 1e-10:
                raise ValueError("Release trajectory unavailable")
            buffer.sample(time)  # Reject future-dated or already exhausted packets.
            local.previous = control_vector(committed_prefix.applied_control)
            last_application = committed_prefix.last_application_time
            due = committed_prefix.pending_application_time
            if committed_prefix.pending_control is not None:
                pending = control_vector(committed_prefix.pending_control)
            for command in (local.previous, pending):
                if command is not None and (
                    np.any(command < local.lower) or np.any(command > local.upper)
                ):
                    raise ValueError("Committed command outside actuator bounds")
            self._propagate(x, local.previous, 0.0)  # Validate even zero-duration forecasts.
            tick_index = int(np.floor(time / local.config.dt)) + 1
            while tick_index * local.config.dt <= time + 1e-10:
                tick_index += 1
            next_tick = tick_index * local.config.dt
        while True:
            if pending is not None and due <= t + 1e-10 and due <= end:
                local.previous = self._apply(
                    pending, local.previous, t - last_application, local.config.steering_rate
                )
                last_application, pending = t, None
                self._propagate(x, local.previous, 0.0)
            if not t < end - 1e-12:
                break
            if t >= next_tick - 1e-10:
                if pending is None:
                    if buffer.reserve(t) <= 1e-10:
                        raise ValueError("Prediction exceeds active trajectory")
                    previous = local.previous.copy() if committed_prefix is not None else None
                    if hasattr(local, "forecast_command"):
                        local.forecast_command(x, buffer, t)
                    else:
                        local.command(x, *buffer.sample(t))
                    if committed_prefix is not None:
                        local.previous = self._apply(
                            local.previous,
                            previous,
                            t - last_application,
                            local.config.steering_rate,
                        )
                        last_application = t
                if committed_prefix is None:
                    next_tick += local.config.dt
                else:
                    tick_index += 1  # Busy ticks are skipped, never replayed as catch-up work.
                    next_tick = tick_index * local.config.dt
            h = min(0.005, end - t, next_tick - t)
            if pending is not None:
                h = min(h, due - t)
            x = self._propagate(x, local.previous, h)
            t += h
        return x, local.previous.copy()

    @staticmethod
    def _apply(requested, previous, elapsed, steering_rate):
        """Same elapsed-application steering clamp as AsyncRunner; no extra dynamics."""
        applied = requested.copy()
        applied[0] = np.clip(
            applied[0],
            previous[0] - steering_rate * max(0.0, elapsed),
            previous[0] + steering_rate * max(0.0, elapsed),
        )
        return applied

    def _propagate(self, x, command, h):
        # Shared unchanged RK4 map, curvature sampling and stage-domain checks.
        curvature = self.track.sample(x[S.S_ABS] % self.track.length).curvature
        predicted, domains = self.step(x, command, curvature, h)
        x, domains = np.asarray(predicted).ravel(), np.asarray(domains)
        if (
            not np.isfinite(x).all()
            or not np.isfinite(domains).all()
            or np.min(domains[0]) < 0.5
            or np.max(domains[0]) > self.maximum_speed
            or np.min(domains[1]) < 0.01
        ):
            raise ValueError("Invalid predicted handoff state")
        return x


class UrgentReplan:
    def __init__(self, enabled=True):
        self.enabled, self.consecutive, self.pending = enabled, 0, False

    def observe(self, error):
        excessive = abs(error[S.E_Y]) > 0.05 or abs(error[S.E_PSI]) > 0.10
        self.consecutive = self.consecutive + 1 if excessive else 0
        trigger = self.enabled and self.consecutive == 2
        if trigger:
            self.pending = True
        return trigger

    def consume(self):
        value, self.pending = self.pending, False
        return value
