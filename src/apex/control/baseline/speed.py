"""Longitudinal PI with conditional-integration anti-windup."""

from dataclasses import dataclass
from math import isfinite

import numpy as np


@dataclass(frozen=True)
class SpeedDiagnostics:
    speed_error: float
    integral: float
    acceleration_unsaturated: float
    acceleration: float
    acceleration_saturated: bool
    integration_blocked: bool


class SpeedPI:
    def __init__(
        self, maximum_acceleration: float, maximum_braking: float, kp: float = 1.0, ki: float = 0.5
    ):
        values = (maximum_acceleration, maximum_braking, kp, ki)
        if not all(isfinite(x) and x > 0 for x in values):
            raise ValueError("PI gains and acceleration/braking magnitudes must be positive finite")
        self.maximum_acceleration = maximum_acceleration
        self.maximum_braking = maximum_braking
        self.kp, self.ki = kp, ki
        self.reset()

    def reset(self):
        self.integral = 0.0

    def update(self, speed: float, reference: float, dt: float) -> SpeedDiagnostics:
        if not all(isfinite(x) for x in (speed, reference, dt)) or dt <= 0:
            raise ValueError("PI inputs must be finite and dt positive")
        error = reference - speed
        candidate = self.integral + error * dt
        proposed = self.kp * error + self.ki * candidate
        blocked = (proposed > self.maximum_acceleration and error > 0) or (
            proposed < -self.maximum_braking and error < 0
        )
        if not blocked:
            self.integral = candidate
        unsaturated = self.kp * error + self.ki * self.integral
        command = float(np.clip(unsaturated, -self.maximum_braking, self.maximum_acceleration))
        return SpeedDiagnostics(
            error, self.integral, unsaturated, command, command != unsaturated, blocked
        )
