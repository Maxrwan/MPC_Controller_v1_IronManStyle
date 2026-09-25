from dataclasses import replace

import pytest

from apex.models.constants import STANDARD_GRAVITY
from apex.models.errors import VehicleModelValidityError
from apex.models.tire.linear import LinearAxleTire
from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer


@pytest.mark.parametrize("alpha", [-0.1, 0, 0.1])
def test_axle_linear_law(alpha):
    result = LinearAxleTire().evaluate(alpha, 40, 12, 10)
    assert result.effective_stiffness == 48
    assert result.lateral_force == pytest.approx(48 * alpha)


def test_no_saturation_in_force_component():
    assert LinearAxleTire().evaluate(0.5, 100, 10, 10).lateral_force == 50


@pytest.mark.parametrize(
    "values",
    [
        (float("nan"), 40, 10, 10),
        (0.1, 0, 10, 10),
        (0.1, 40, 0, 10),
        (0.1, 40, -1, 10),
        (0.1, 40, 10, 0),
        (0.1, float("inf"), 10, 10),
    ],
)
def test_invalid_tire_inputs(values):
    with pytest.raises(VehicleModelValidityError):
        LinearAxleTire().evaluate(*values)


def test_static_loads_asymmetric_geometry(dynamic_vehicle):
    p = replace(dynamic_vehicle, lf=0.12, lr=0.18)
    result = QuasiStaticLongitudinalLoadTransfer().evaluate(p, 0)
    assert result.front == pytest.approx(2 * STANDARD_GRAVITY * 0.18 / 0.3)
    assert result.rear == pytest.approx(2 * STANDARD_GRAVITY * 0.12 / 0.3)
    assert result.front == result.front_static
    assert result.rear == result.rear_static


@pytest.mark.parametrize("a_cmd", [-5, -2, 0, 2, 5])
def test_load_conservation_and_direction(dynamic_vehicle, a_cmd):
    result = QuasiStaticLongitudinalLoadTransfer().evaluate(dynamic_vehicle, a_cmd)
    assert result.front + result.rear == pytest.approx(2 * STANDARD_GRAVITY, abs=1e-13)
    assert result.front - result.front_static == pytest.approx(-2 * a_cmd * 0.04 / 0.30)
    assert result.rear - result.rear_static == pytest.approx(2 * a_cmd * 0.04 / 0.30)
    if a_cmd > 0:
        assert result.front < result.front_static and result.rear > result.rear_static
    elif a_cmd < 0:
        assert result.front > result.front_static and result.rear < result.rear_static


@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("scale", [1, 1.1])
def test_unloading_rejected(dynamic_vehicle, sign, scale):
    critical = STANDARD_GRAVITY * 0.15 / 0.04
    with pytest.raises(VehicleModelValidityError, match="unloading"):
        QuasiStaticLongitudinalLoadTransfer().evaluate(dynamic_vehicle, sign * critical * scale)


def test_zero_height_and_configurable_gravity(dynamic_vehicle):
    p = replace(dynamic_vehicle, cg_height=0)
    result = QuasiStaticLongitudinalLoadTransfer(gravity=10).evaluate(p, 100)
    assert result.front == result.rear == 10


@pytest.mark.parametrize("gravity", [0, -1, float("inf"), float("nan")])
def test_invalid_gravity(gravity):
    with pytest.raises(ValueError):
        QuasiStaticLongitudinalLoadTransfer(gravity)
