"""Numeric geometry preview: no SciPy spline inside the symbolic NLP."""

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

import numpy as np

from apex.control.baseline.references import cornering_reference, validate_reference_speed
from apex.models.vehicle.parameters import VehicleParameters
from apex.track.base import Track
from apex.track.progress import wrap_progress

# Rows: curvature, left/right width, speed, vy_ref, r_ref, delta_ff.
PREVIEW_DIM = 7


@dataclass(frozen=True)
class Preview:
    progress: np.ndarray
    values: np.ndarray


def make_preview(
    track: Track,
    parameters: VehicleParameters,
    speed_reference: Callable,
    progress: float,
    horizon: int = 20,
    dt: float = 0.05,
    timing: dict | None = None,
) -> Preview:
    samples, positions = [], []
    s = float(progress)
    geometry_seconds = reference_seconds = 0.0
    for _ in range(horizon + 1):
        start = perf_counter()
        g = track.sample(wrap_progress(s, track.length))
        geometry_seconds += perf_counter() - start
        start = perf_counter()
        speed = validate_reference_speed(speed_reference(g.track_s))
        ref = cornering_reference(parameters, speed, g.curvature)
        reference_seconds += perf_counter() - start
        positions.append(s)
        samples.append(
            [
                g.curvature,
                g.left_width,
                g.right_width,
                speed,
                ref.vy,
                ref.yaw_rate,
                ref.delta_dynamic,
            ]
        )
        s += dt * speed  # nominal centerline progress; independent of decision variables
    if timing is not None:
        timing.update(
            preview_geometry_time=geometry_seconds, reference_generation_time=reference_seconds
        )
    return Preview(np.array(positions), np.array(samples).T)
