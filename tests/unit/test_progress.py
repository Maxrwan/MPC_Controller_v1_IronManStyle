from math import nextafter, pi

import pytest

from apex.coordinates.angles import wrap_angle
from apex.track.progress import lap_index, unwrap_progress, wrap_progress


@pytest.mark.parametrize("lap", [0, 1, 2, 3, 17, 1000000])
def test_exact_lap_boundaries(lap):
    length = 2 * pi * 5
    progress = lap * length
    assert wrap_progress(progress, length) == 0
    assert lap_index(progress, length) == lap
    assert unwrap_progress(0, progress, length) == progress


def test_immediately_adjacent_floats():
    length = 2 * pi * 5
    for lap in [1, 2, 3, 17]:
        boundary = lap * length
        below, above = nextafter(boundary, 0), nextafter(boundary, float("inf"))
        assert lap_index(below, length) == lap - 1
        assert lap_index(above, length) == lap
        assert 0 < wrap_progress(below, length) < length
        assert 0 < wrap_progress(above, length) < length
    assert 0 <= wrap_progress(-1e-300, length) < length


def test_unwrap_continuity_ties_and_start():
    assert unwrap_progress(0.1, 9.9, 10) == pytest.approx(10.1)
    assert unwrap_progress(9.9, 10.1, 10) == pytest.approx(9.9)
    assert unwrap_progress(1, 0, 10) == 1
    assert unwrap_progress(0, 5, 10) == 10  # Forward tie.
    assert wrap_progress(-1, 10) == 9


@pytest.mark.parametrize("length", [0, -1, float("nan"), float("inf")])
def test_invalid_length(length):
    for operation in [wrap_progress, lap_index]:
        with pytest.raises(ValueError):
            operation(0, length)
    with pytest.raises(ValueError):
        unwrap_progress(0, 0, length)


@pytest.mark.parametrize("s", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_progress(s):
    with pytest.raises(ValueError):
        wrap_progress(s, 10)
    with pytest.raises(ValueError):
        lap_index(s, 10)


@pytest.mark.parametrize("s,previous", [(-1, 0), (10, 0), (0, -1), (0, float("nan"))])
def test_invalid_unwrap(s, previous):
    with pytest.raises(ValueError):
        unwrap_progress(s, previous, 10)


@pytest.mark.parametrize(
    "angle,expected",
    [(0, 0), (pi, pi), (-pi, pi), (3 * pi, pi), (-3 * pi, pi), (2 * pi + 0.2, 0.2)],
)
def test_angle_convention(angle, expected):
    assert wrap_angle(angle) == pytest.approx(expected)


@pytest.mark.parametrize("angle", [float("inf"), float("nan")])
def test_nonfinite_angle(angle):
    with pytest.raises(ValueError):
        wrap_angle(angle)
