"""Reproducible numerical error report: pytest -s tests/regression/test_geometry_accuracy.py."""

import json
from math import pi

import numpy as np

from apex.coordinates.angles import wrap_angle
from apex.coordinates.frenet import frenet_to_global, project_pose


def test_geometry_accuracy_report(circle, oval):
    metrics = {
        "circle_circumference_error_m": abs(circle.length - 10 * pi),
        "circle_chord_perimeter_error_m": abs(circle.centerline.chord_length - 10 * pi),
        "circle_max_curvature_error_per_m": max(
            abs(circle.sample(s).curvature - 0.2) for s in np.linspace(0, circle.length, 501)
        ),
    }
    for name, track in [("circle", circle), ("oval", oval)]:
        errors = np.zeros(4)
        for s in np.linspace(0, 2 * track.length, 101):
            pose = frenet_to_global(track, s, 0.2 * np.cos(s), 0.3)
            projection = project_pose(track, pose, previous_s_abs=s)
            rebuilt = frenet_to_global(track, projection.track_s, projection.e_y, projection.e_psi)
            errors = np.maximum(
                errors,
                [
                    abs(projection.s_abs - s),
                    abs(projection.e_y - 0.2 * np.cos(s)),
                    abs(wrap_angle(projection.e_psi - 0.3)),
                    np.hypot(rebuilt.x - pose.x, rebuilt.y - pose.y),
                ],
            )
        for key, value in zip(
            ["progress_error_m", "lateral_error_m", "heading_error_rad", "cartesian_error_m"],
            errors,
            strict=True,
        ):
            metrics[f"{name}_max_round_trip_{key}"] = float(value)
        first, last = track.sample(0), track.sample(track.length)
        metrics[f"{name}_exact_seam_position_error_m"] = float(
            np.hypot(first.x - last.x, first.y - last.y)
        )
        before, after = track.sample(track.length - 1e-6), track.sample(1e-6)
        metrics[f"{name}_seam_span_at_plus_minus_1um_m"] = float(
            np.hypot(before.x - after.x, before.y - after.y)
        )
        metrics[f"{name}_seam_heading_span_rad"] = abs(wrap_angle(before.heading - after.heading))
        metrics[f"{name}_seam_curvature_span_per_m"] = abs(before.curvature - after.curvature)
        assert max(errors) < 1e-8
        assert metrics[f"{name}_exact_seam_position_error_m"] < 1e-12
        assert metrics[f"{name}_seam_span_at_plus_minus_1um_m"] < 2.001e-6
    assert metrics["circle_circumference_error_m"] < 5e-6
    assert metrics["circle_max_curvature_error_per_m"] < 2e-4
    print("\nGeometry accuracy metrics:\n" + json.dumps(metrics, indent=2, sort_keys=True))
