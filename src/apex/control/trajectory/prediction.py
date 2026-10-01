"""Replaceable delay estimate and independent closed-loop actuation-state prediction."""

from collections import deque

import casadi as ca
import numpy as np

from apex.state import StateIndex as S
from apex.state import state_vector


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

    def predict(self, state, time, duration, buffer, tracker):
        if not np.isfinite([time, duration]).all() or min(time, duration) < 0:
            raise ValueError("Invalid forecast time")
        x, t, end = state_vector(state), time, time + duration
        if buffer.active is None or end > buffer.active.horizon_end_time + 1e-10:
            raise ValueError("Prediction exceeds active trajectory")
        local = tracker.clone()
        next_tick = (int(np.floor((time + 1e-9) / local.config.dt)) + 1) * local.config.dt
        while t < end - 1e-12:
            if t >= next_tick - 1e-10:
                if buffer.reserve(t) <= 1e-10:
                    raise ValueError("Prediction exceeds active trajectory")
                if hasattr(local, "forecast_command"):
                    local.forecast_command(x, buffer, t)
                else:
                    local.command(x, *buffer.sample(t))
                next_tick += local.config.dt
            h = min(0.005, end - t, next_tick - t)
            curvature = self.track.sample(x[S.S_ABS] % self.track.length).curvature
            predicted, domains = self.step(x, local.previous, curvature, h)
            x, domains = np.asarray(predicted).ravel(), np.asarray(domains)
            if (
                not np.isfinite(x).all()
                or not np.isfinite(domains).all()
                or np.min(domains[0]) < 0.5
                or np.max(domains[0]) > self.maximum_speed
                or np.min(domains[1]) < 0.01
            ):
                raise ValueError("Invalid predicted handoff state")
            t += h
        return x, local.previous.copy()


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
