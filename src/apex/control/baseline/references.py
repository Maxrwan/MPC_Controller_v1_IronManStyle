"""Nominal static-load, small-slip steady cornering references (SI)."""

from dataclasses import dataclass
from math import atan, isfinite

from apex.models.vehicle.parameters import VehicleParameters


@dataclass(frozen=True)
class CorneringReference:
    vy: float
    yaw_rate: float
    delta_dynamic: float
    delta_kinematic: float


def cornering_reference(p: VehicleParameters, speed: float, curvature: float) -> CorneringReference:
    """Solve steady linear force/moment balance; no nonlinear plant solve."""
    p.validate_for_dynamic()
    if not isfinite(speed) or speed <= 0 or not isfinite(curvature):
        raise ValueError("Reference speed must be positive and curvature finite")
    m, lf, lr = p.mass, p.lf, p.lr
    cf, cr = p.front_cornering_stiffness, p.rear_cornering_stiffness
    length = lf + lr
    yaw_rate = speed * curvature
    rear_force = m * speed**2 * curvature * lf / length
    front_force = m * speed**2 * curvature * lr / length
    vy = lr * yaw_rate - speed * rear_force / cr
    delta = vy / speed + lf * curvature + front_force / cf
    return CorneringReference(vy, yaw_rate, delta, atan(length * curvature))


@dataclass(frozen=True)
class ConstantSpeed:
    value: float = 2.0

    def __post_init__(self):
        validate_reference_speed(self.value)

    def __call__(self, track_s: float) -> float:
        return self.value


def validate_reference_speed(value: float) -> float:
    if not isfinite(value) or not 1.0 <= value <= 3.0:
        raise ValueError("Baseline reference speed must be within synthetic domain [1, 3] m/s")
    return float(value)
