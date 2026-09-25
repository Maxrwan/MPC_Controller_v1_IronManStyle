"""Numerical integration independent of vehicle, track and controller equations."""

from collections.abc import Callable
from math import isfinite

from apex.models.errors import ModelValidationError
from apex.state import Vector


def rk4_step(derivative: Callable[[Vector], Vector], state: Vector, dt: float) -> Vector:
    """Classical fixed-step RK4; callers supply held inputs through the callable."""
    if not isfinite(dt) or dt <= 0:
        raise ModelValidationError("dt must be finite and positive [s]")
    k1 = derivative(state)
    k2 = derivative(state + dt * k1 / 2)
    k3 = derivative(state + dt * k2 / 2)
    k4 = derivative(state + dt * k3)
    return state + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
