"""Cartesian/Frenet geometry; race progress is returned separately from wrapped s."""

from dataclasses import dataclass
from math import cos, isfinite, sin

from apex.coordinates.angles import wrap_angle
from apex.track.base import Track
from apex.track.progress import unwrap_progress


@dataclass(frozen=True)
class GlobalPose:
    x: float
    y: float
    psi: float

    def __post_init__(self) -> None:
        if not all(isfinite(value) for value in (self.x, self.y, self.psi)):
            raise ValueError("global pose must be finite")
        object.__setattr__(self, "psi", wrap_angle(self.psi))


@dataclass(frozen=True)
class FrenetProjection:
    track_s: float
    e_y: float
    e_psi: float | None
    s_abs: float | None


def frenet_to_global(track: Track, s: float, e_y: float, e_psi: float = 0.0) -> GlobalPose:
    """Offset along the left normal; default heading follows the track tangent."""
    if not isfinite(e_y) or not isfinite(e_psi):
        raise ValueError("Frenet offsets must be finite")
    sample = track.sample(s)
    return GlobalPose(
        sample.x - e_y * sin(sample.heading),
        sample.y + e_y * cos(sample.heading),
        wrap_angle(sample.heading + e_psi),
    )


def project_point(
    track: Track, x: float, y: float, *, previous_s_abs: float | None = None
) -> FrenetProjection:
    """Project a point; unwrapped progress is unknown unless a hint is supplied."""
    s = track.project_point(x, y)
    sample = track.sample(s)
    e_y = -(x - sample.x) * sin(sample.heading) + (y - sample.y) * cos(sample.heading)
    s_abs = None if previous_s_abs is None else unwrap_progress(s, previous_s_abs, track.length)
    return FrenetProjection(s, e_y, None, s_abs)


def project_pose(
    track: Track, pose: GlobalPose, *, previous_s_abs: float | None = None
) -> FrenetProjection:
    """Project full pose with left-positive heading error and optional lap continuity."""
    point = project_point(track, pose.x, pose.y, previous_s_abs=previous_s_abs)
    heading = track.sample(point.track_s).heading
    return FrenetProjection(point.track_s, point.e_y, wrap_angle(pose.psi - heading), point.s_abs)
