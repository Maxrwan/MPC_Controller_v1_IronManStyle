import pytest

from apex.track import ClosedTrack
from apex.track.synthetic import circle_waypoints


@pytest.fixture(scope="session")
def circle():
    """Synthetic 5 m circle, explicitly chosen test-only widths."""
    return ClosedTrack.from_waypoints(
        circle_waypoints(5.0, count=64), left_width=0.6, right_width=0.9
    )


@pytest.fixture(scope="session")
def oval():
    points = circle_waypoints(1.0, count=72)
    points *= [7.0, 3.0]
    return ClosedTrack.from_waypoints(points, left_width=0.3, right_width=0.5)


@pytest.fixture
def synthetic_vehicle():
    """NOT identified and NOT representative of APEX: arbitrary geometry only."""
    from apex.models.vehicle.parameters import VehicleParameters

    return VehicleParameters(name="synthetic_test_vehicle", wheelbase=0.30, lf=0.15, lr=0.15)


@pytest.fixture
def straight_geometry():
    """Analytical local straight chart to isolate propagation; not a real closed circuit."""
    from apex.track.base import TrackSample

    class StraightGeometry:
        length = 1000000.0

        def sample(self, s):
            assert 0 <= s < self.length
            return TrackSample(s, s, 0, 0, 0, 10, 10)

    return StraightGeometry()


@pytest.fixture
def analytic_circle():
    """Exact synthetic circle to separate model errors from cubic interpolation errors."""
    from math import cos, pi, sin

    from apex.coordinates.angles import wrap_angle
    from apex.track.base import TrackSample

    class AnalyticCircle:
        radius = 5.0
        length = 2 * pi * radius

        def sample(self, s):
            assert 0 <= s < self.length
            theta = s / self.radius
            return TrackSample(
                s,
                self.radius * cos(theta),
                self.radius * sin(theta),
                wrap_angle(theta + pi / 2),
                1 / self.radius,
                0.6,
                0.9,
            )

    return AnalyticCircle()


@pytest.fixture
def dynamic_vehicle():
    """SYNTHETIC validation only; not experimentally identified APEX parameters."""
    from pathlib import Path

    from apex.config import load_vehicle_parameters

    return load_vehicle_parameters(
        Path(__file__).resolve().parents[1] / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml"
    )
