from math import pi

import numpy as np
import pytest

from apex.coordinates.angles import wrap_angle
from apex.coordinates.frenet import GlobalPose, frenet_to_global, project_point, project_pose
from apex.track import ClosedTrack
from apex.track.progress import unwrap_progress, wrap_progress
from apex.track.synthetic import circle_waypoints


def progress_error(a, b, length):
    return abs((a - b + length / 2) % length - length / 2)


def test_analytical_left_and_right(circle):
    left, right = frenet_to_global(circle, 0, 0.3), frenet_to_global(circle, 0, -0.4)
    assert [left.x, left.y, left.psi] == pytest.approx([4.7, 0, pi / 2], abs=1e-12)
    assert [right.x, right.y] == pytest.approx([5.4, 0], abs=1e-12)
    projection = project_point(circle, 4.7, 0)
    assert progress_error(projection.track_s, 0, circle.length) < 1e-10
    assert projection.e_y == pytest.approx(0.3, abs=1e-12)
    assert projection.e_psi is None
    assert projection.s_abs is None
    assert project_point(circle, 5.4, 0).e_y == pytest.approx(-0.4, abs=1e-12)


def test_heading_error_sign(circle):
    for error in [-0.4, 0.4, pi, -pi]:
        pose = frenet_to_global(circle, 0.8 * circle.length, 0.1, error)
        result = project_pose(circle, pose)
        assert abs(wrap_angle(result.e_psi - error)) < 1e-10
    assert GlobalPose(0, 0, -pi).psi == pi


@pytest.mark.parametrize("track_name", ["circle", "oval"])
def test_frenet_round_trip(request, track_name):
    track = request.getfixturevalue(track_name)
    for s in np.linspace(0, 3 * track.length, 61):
        for e_y in [-0.2, 0.0, 0.2]:
            pose = frenet_to_global(track, s, e_y, 0.3)
            result = project_pose(track, pose, previous_s_abs=s)
            assert progress_error(result.track_s, s, track.length) < 1e-8
            assert result.s_abs == pytest.approx(s, abs=1e-8)
            assert result.e_y == pytest.approx(e_y, abs=1e-9)
            assert abs(wrap_angle(result.e_psi - 0.3)) < 1e-9
            reconstructed = frenet_to_global(track, result.track_s, result.e_y, result.e_psi)
            assert np.hypot(reconstructed.x - pose.x, reconstructed.y - pose.y) < 1e-8
            assert abs(wrap_angle(reconstructed.psi - pose.psi)) < 1e-9


def test_independent_cartesian_round_trip(circle, oval):
    # Independently chosen Cartesian points, not outputs of frenet_to_global.
    for track, points in [
        (circle, [(5.2, 0.5), (-3.7, 3.8), (0.2, -4.8)]),
        (oval, [(7.1, 0.2), (-0.3, 2.9), (-6.9, -0.6)]),
    ]:
        for x, y in points:
            original = GlobalPose(x, y, -2.8)
            result = project_pose(track, original)
            pose = frenet_to_global(track, result.track_s, result.e_y, result.e_psi)
            assert np.hypot(pose.x - x, pose.y - y) < 1e-8
            assert abs(wrap_angle(pose.psi - original.psi)) < 1e-10


def test_seam_and_multiple_laps(circle):
    length = circle.length
    previous = length - 0.01
    for lap in range(1, 6):
        for expected in [
            lap * length - 0.001,
            lap * length,
            lap * length + 0.001,
            lap * length + length / 3,
            lap * length + 2 * length / 3,
        ]:
            result = project_pose(
                circle, frenet_to_global(circle, expected, 0.1), previous_s_abs=previous
            )
            assert result.s_abs == pytest.approx(expected, abs=1e-8)
            assert result.s_abs >= previous - 1e-8
            previous = result.s_abs
    assert unwrap_progress(
        wrap_progress(1000000 * length + 0.1, length), 1000000 * length, length
    ) == pytest.approx(1000000 * length + 0.1)


def test_clockwise_projection():
    track = ClosedTrack.from_waypoints(
        circle_waypoints(5, clockwise=True), left_width=0.5, right_width=0.5
    )
    point = frenet_to_global(track, 0, 0.3)
    assert point.x == pytest.approx(5.3)
    assert project_pose(track, point).e_y == pytest.approx(0.3)


def test_projection_nearest_distance_against_dense_oval(oval):
    samples = np.array(
        [(p.x, p.y) for p in (oval.sample(s) for s in np.linspace(0, oval.length, 1001))]
    )
    for x, y in [(8, 1), (-5, 4), (0.2, 0.1)]:
        projected = oval.sample(oval.project_point(x, y))
        distance = np.hypot(projected.x - x, projected.y - y)
        assert distance <= np.min(np.linalg.norm(samples - [x, y], axis=1)) + 1e-9


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_invalid_coordinates(circle, value):
    with pytest.raises(ValueError):
        GlobalPose(value, 0, 0)
    with pytest.raises(ValueError):
        project_point(circle, 0, value)
    with pytest.raises(ValueError):
        frenet_to_global(circle, 0, value)
    with pytest.raises(ValueError):
        frenet_to_global(circle, 0, 0, value)


def test_nonuniform_waypoints():
    angles = np.linspace(0, 1, 32, endpoint=False) ** 1.4 * 2 * np.pi
    points = np.column_stack([4 * np.cos(angles), 2 * np.sin(angles)])
    track = ClosedTrack.from_waypoints(points, left_width=0.2, right_width=0.3)
    for s in np.linspace(0, track.length, 25, endpoint=False):
        result = project_pose(track, frenet_to_global(track, s, 0.05, -0.2))
        assert progress_error(result.track_s, s, track.length) < 1e-8
        assert result.e_y == pytest.approx(0.05, abs=1e-9)
