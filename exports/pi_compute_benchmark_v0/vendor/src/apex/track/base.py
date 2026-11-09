"""Closed-track geometry interface, independent of vehicle and race state."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TrackSample:
    """Wrapped progress and centerline geometry in SI units."""

    track_s: float
    x: float
    y: float
    heading: float
    curvature: float
    left_width: float
    right_width: float


class Track(Protocol):
    @property
    def length(self) -> float:
        """Positive centerline circumference [m]."""
        ...

    def sample(self, s: float) -> TrackSample:
        """Query geometry at arbitrary finite progress, wrapping internally."""
        ...

    def left_width(self, s: float) -> float:
        """Left half-width [m]; may vary with progress in future implementations."""
        ...

    def right_width(self, s: float) -> float:
        """Right half-width [m]."""
        ...

    def project_point(self, x: float, y: float) -> float:
        """Return nearest wrapped centerline progress [m]."""
        ...
