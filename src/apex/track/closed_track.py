"""Closed centerline and independent constant left/right track widths."""

from math import isfinite

from numpy.typing import ArrayLike

from apex.track.base import TrackSample
from apex.track.centerline import PeriodicCenterline
from apex.track.progress import wrap_progress


class ClosedTrack:
    def __init__(
        self, centerline: PeriodicCenterline, *, left_width: float, right_width: float
    ) -> None:
        for value in (left_width, right_width):
            if not isfinite(value) or value <= 0:
                raise ValueError("track half-widths must be finite and positive")
        self._centerline = centerline
        self._left = float(left_width)
        self._right = float(right_width)

    @classmethod
    def from_waypoints(
        cls, waypoints: ArrayLike, *, left_width: float, right_width: float
    ) -> "ClosedTrack":
        return cls(PeriodicCenterline(waypoints), left_width=left_width, right_width=right_width)

    @property
    def centerline(self) -> PeriodicCenterline:
        return self._centerline

    @property
    def length(self) -> float:
        return self.centerline.length

    def left_width(self, s: float) -> float:
        wrap_progress(s, self.length)
        return self._left

    def right_width(self, s: float) -> float:
        wrap_progress(s, self.length)
        return self._right

    def sample(self, s: float) -> TrackSample:
        track_s = wrap_progress(s, self.length)
        x, y, heading, curvature = self.centerline.geometry(track_s)
        return TrackSample(
            track_s, x, y, heading, curvature, self.left_width(track_s), self.right_width(track_s)
        )

    def project_point(self, x: float, y: float) -> float:
        return self.centerline.project_point(x, y)
