"""Canonical scalar angle convention: (-pi, pi]."""

from math import isfinite, pi


def wrap_angle(angle: float) -> float:
    """Wrap a finite angle in radians; both odd-pi endpoints map to +pi."""
    if not isfinite(angle):
        raise ValueError("angle must be finite")
    wrapped = (angle + pi) % (2 * pi) - pi
    return pi if wrapped == -pi else wrapped
