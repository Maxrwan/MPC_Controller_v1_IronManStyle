from dataclasses import FrozenInstanceError
from math import cos, pi, sin

import numpy as np
import pytest
from scipy.special import ellipe

from apex.coordinates.angles import wrap_angle
from apex.track import ClosedTrack
from apex.track.centerline import PeriodicCenterline
from apex.track.synthetic import circle_waypoints


def test_circle_geometry(circle):
    assert abs(circle.length - 2 * pi * 5) < 5e-6
    for s in np.linspace(0, circle.length, 101):
        sample = circle.sample(s)
        theta = 2 * pi * s / circle.length
        assert abs(np.hypot(sample.x, sample.y) - 5) < 2e-6
        assert np.hypot(sample.x - 5 * cos(theta), sample.y - 5 * sin(theta)) < 3e-6
        assert abs(wrap_angle(sample.heading - theta - pi / 2)) < 1e-5
        assert abs(sample.curvature - 0.2) < 2e-4
        assert sample.left_width == 0.6
        assert sample.right_width == 0.9


def test_clockwise_curvature_and_normal():
    track = ClosedTrack.from_waypoints(
        circle_waypoints(5, clockwise=True), left_width=0.5, right_width=0.7
    )
    sample = track.sample(0)
    assert sample.heading == pytest.approx(-pi / 2, abs=1e-12)
    assert sample.curvature == pytest.approx(-0.2, abs=2e-4)


def test_periodicity(circle, oval):
    for track in (circle, oval):
        for s in [-0.01, 0, 0.023 * track.length, 0.63 * track.length, track.length - 0.01]:
            first, later = track.sample(s), track.sample(s + 7 * track.length)
            assert np.hypot(first.x - later.x, first.y - later.y) < 1e-10
            assert abs(wrap_angle(first.heading - later.heading)) < 1e-10
            assert abs(first.curvature - later.curvature) < 1e-10


def test_seam_continuity(circle, oval):
    epsilon = 1e-6
    for track in (circle, oval):
        before, at, after = (track.sample(s) for s in [track.length - epsilon, 0, epsilon])
        assert np.hypot(before.x - after.x, before.y - after.y) <= 2.001 * epsilon
        assert abs(wrap_angle(before.heading - after.heading)) < 2e-6
        assert abs(before.curvature - after.curvature) < 2e-6
        assert (
            np.hypot(at.x - track.sample(track.length).x, at.y - track.sample(track.length).y) == 0
        )


def test_arc_length_not_chord_parameter(oval):
    centerline = oval.centerline
    expected_perimeter = 4 * 7 * ellipe(1 - (3 / 7) ** 2)
    assert abs(oval.length - expected_perimeter) < 3e-5
    assert oval.length > centerline.chord_length
    # Independent fixed-order Gauss-Legendre quadrature of the original spline.
    nodes, weights = np.polynomial.legendre.leggauss(16)
    integrated = 0.0
    for a, b in zip(centerline._q[:-1], centerline._q[1:], strict=True):
        q = (a + b) / 2 + (b - a) / 2 * nodes
        speed = np.linalg.norm(centerline._spline(q, 1), axis=1)
        integrated += (b - a) / 2 * np.dot(weights, speed)
    assert abs(oval.length - integrated) < 1e-10
    ds = 1e-4
    for s in np.linspace(0, oval.length, 31, endpoint=False):
        before, after = oval.sample(s - ds), oval.sample(s + ds)
        numerical_speed = np.hypot(after.x - before.x, after.y - before.y) / (2 * ds)
        assert numerical_speed == pytest.approx(1, abs=1e-7)


def test_repeated_endpoint_and_input_copy():
    points = circle_waypoints(2, count=16)
    a, b = PeriodicCenterline(points), PeriodicCenterline(np.vstack([points, points[0]]))
    assert a.length == b.length
    assert len(b.waypoints) == 16
    points[:] = 99
    copy = a.waypoints
    copy[:] = 88
    assert a.geometry(0)[0] == pytest.approx(2)


def test_sample_immutable(circle):
    with pytest.raises(FrozenInstanceError):
        circle.sample(0).x = 42


@pytest.mark.parametrize(
    "points",
    [
        [],
        [[0, 0], [1, 0], [0, 1]],
        [[0, 0], [1, 0], [2, 0], [3, 0]],
        [[0, 0]] * 4,
        [[0, 0], [1, 0], [1, 0], [0, 1]],
        [[0, 0], [1, 0], [1, 1], [float("nan"), 1]],
        [[0, 0], [1, 0], [1, 1], [float("inf"), 1]],
        [[1, 2, 3]] * 4,
    ],
)
def test_invalid_centerlines(points):
    with pytest.raises(ValueError):
        PeriodicCenterline(points)


def test_zero_tangent_rejected():
    # Synthetic cusp: this width makes the periodic spline derivative at q=0 vanish.
    # Found by solving dx/dq(0)=0; reflection symmetry also gives dy/dq(0)=0.
    width = 84.00649388081153
    with pytest.raises(ValueError, match="tangent"):
        PeriodicCenterline([[0, 0], [0.01, 1], [width, 2], [-width, 2], [-0.01, 1]])


@pytest.mark.parametrize("width", [0, -1, float("inf"), float("nan")])
def test_invalid_width(width, circle):
    with pytest.raises(ValueError):
        ClosedTrack(circle.centerline, left_width=width, right_width=1)
    with pytest.raises(ValueError):
        ClosedTrack(circle.centerline, left_width=1, right_width=width)


@pytest.mark.parametrize("s", [float("nan"), float("inf")])
def test_nonfinite_geometry_queries(circle, s):
    for operation in [circle.sample, circle.left_width, circle.right_width]:
        with pytest.raises(ValueError):
            operation(s)


def test_translated_circle():
    offset = np.array([1000.0, -2000.0])
    center = PeriodicCenterline(circle_waypoints(5) + offset)
    assert center.geometry(0)[:2] == pytest.approx([1005, -2000])
    assert center.length == pytest.approx(2 * pi * 5, abs=5e-6)
