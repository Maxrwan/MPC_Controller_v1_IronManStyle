"""Numeric geometry preview: no SciPy spline inside the symbolic NLP."""

from collections.abc import Callable
from dataclasses import dataclass
from sys import exc_info
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
    racing_reference=None,
    *,
    recorder=None,
) -> Preview:
    if recorder is None:
        samples, positions = [], []
        s = float(progress)
        geometry_seconds = reference_seconds = 0.0
        for _ in range(horizon + 1):
            start = perf_counter()
            g = track.sample(wrap_progress(s, track.length))
            geometry_seconds += perf_counter() - start
            start = perf_counter()
            if racing_reference is not None:
                ref = racing_reference.sample(s)
                speed = ref["v_ref_mps"]
                ey, epsi, kr = ref["e_y_ref_m"], ref["e_psi_ref_rad"], ref["kappa_ref_1pm"]
                # Explicit zero-sideslip geometric baseline, not steady dynamic force balance.
                positions.append(s)
                samples.append(
                    [
                        g.curvature,
                        g.left_width,
                        g.right_width,
                        speed,
                        0.0,
                        speed * kr,
                        np.arctan(parameters.wheelbase * kr),
                        ey,
                        epsi,
                        kr,
                        ref["a_ref_mps2"],
                    ]
                )
                reference_seconds += perf_counter() - start
                s += dt * speed * np.cos(epsi) / (1 - g.curvature * ey)
                continue
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
    else:
        samples, positions = [], []
        s = float(progress)
        geometry_seconds = reference_seconds = 0.0
        for _ in range(horizon + 1):
            _g1_reference_geometry = recorder.span_begin(
                recorder.active_call, "reference_geometry", expected_parent="reference"
            )
            _g1_done_reference_geometry = False
            try:
                start = perf_counter()
                g = track.sample(wrap_progress(s, track.length))
                geometry_seconds += perf_counter() - start
                _g1_done_reference_geometry = True
            finally:
                _g1_error_reference_geometry = (
                    None if _g1_done_reference_geometry else exc_info()[0]
                )
                recorder.span_end(
                    _g1_reference_geometry,
                    exit="complete" if _g1_done_reference_geometry else "exception",
                    exception_type=None
                    if _g1_error_reference_geometry is None
                    else (
                        _g1_error_reference_geometry.__module__
                        + "."
                        + _g1_error_reference_geometry.__qualname__
                    ),
                )
            _g1_reference_values = recorder.span_begin(
                recorder.active_call, "reference_values", expected_parent="reference"
            )
            _g1_reference_done = False
            try:
                start = perf_counter()
                if racing_reference is not None:
                    ref = racing_reference.sample(s)
                    speed = ref["v_ref_mps"]
                    ey, epsi, kr = ref["e_y_ref_m"], ref["e_psi_ref_rad"], ref["kappa_ref_1pm"]
                    # Explicit zero-sideslip geometric baseline, not steady dynamic force balance.
                    positions.append(s)
                    samples.append(
                        [
                            g.curvature,
                            g.left_width,
                            g.right_width,
                            speed,
                            0.0,
                            speed * kr,
                            np.arctan(parameters.wheelbase * kr),
                            ey,
                            epsi,
                            kr,
                            ref["a_ref_mps2"],
                        ]
                    )
                    reference_seconds += perf_counter() - start
                    _g1_reference_done = True
                    recorder.span_end(_g1_reference_values, exit="complete")
                    _g1_reference_values = None
                    s += dt * speed * np.cos(epsi) / (1 - g.curvature * ey)
                    continue
                speed = validate_reference_speed(speed_reference(g.track_s))
                ref = cornering_reference(parameters, speed, g.curvature)
                reference_seconds += perf_counter() - start
                _g1_reference_done = True
            finally:
                if _g1_reference_values is not None:
                    _g1_reference_error = None if _g1_reference_done else exc_info()[0]
                    recorder.span_end(
                        _g1_reference_values,
                        exit="complete" if _g1_reference_done else "exception",
                        exception_type=None
                        if _g1_reference_error is None
                        else (
                            _g1_reference_error.__module__ + "." + _g1_reference_error.__qualname__
                        ),
                    )
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
