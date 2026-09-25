"""Explicitly synthetic geometric fixtures; no real circuit dimensions are assumed."""

from math import isfinite

import numpy as np
from numpy.typing import NDArray


def circle_waypoints(
    radius: float, *, count: int = 64, clockwise: bool = False
) -> NDArray[np.float64]:
    """Return endpoint-exclusive points starting at (radius, 0), in metres."""
    if not isfinite(radius) or radius <= 0:
        raise ValueError("radius must be finite and positive")
    if isinstance(count, bool) or not isinstance(count, int) or count < 4:
        raise ValueError("count must be an integer >= 4")
    angles = np.linspace(0, (-2 if clockwise else 2) * np.pi, count, endpoint=False)
    return radius * np.column_stack([np.cos(angles), np.sin(angles)])
