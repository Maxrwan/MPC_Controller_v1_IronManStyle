from dataclasses import FrozenInstanceError, replace
from math import asin, atan, cos, pi, tan

import numpy as np
import pytest

from apex.models.errors import FrenetGeometryError, ModelValidationError
from apex.models.vehicle.kinematic import (
    DEFAULT_TIMESTEP,
    FRENET_DENOMINATOR_MIN,
    SPEED_TOLERANCE,
    KinematicBicycle,
)
from apex.models.vehicle.parameters import VehicleParameters
from apex.state import StateIndex as I
from apex.state import state_vector


def test_geometry_only_validation(synthetic_vehicle, straight_geometry):
    synthetic_vehicle.validate_for_kinematic()
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    assert model.step(state_vector([1, 0, 0, 0, 0, 0]), [0, 0])[I.S_ABS] == DEFAULT_TIMESTEP
    with pytest.raises(ValueError, match="Undefined vehicle parameters"):
        synthetic_vehicle.validate_for_simulation()


@pytest.mark.parametrize("missing", ["wheelbase", "lf", "lr"])
def test_missing_geometry(synthetic_vehicle, straight_geometry, missing):
    with pytest.raises(ValueError, match="Undefined kinematic geometry"):
        KinematicBicycle(replace(synthetic_vehicle, **{missing: None}), straight_geometry)


def test_inconsistent_geometry():
    with pytest.raises(ValueError, match="wheelbase"):
        VehicleParameters(name="synthetic", wheelbase=0.5, lf=0.15, lr=0.15)


def test_straight_motion_and_constant_lateral_error(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    x = state_vector([2, 99, -99, 0, 3, 0.2])
    original = x.copy()
    u = np.array([0.0, 0.0])
    result = model.step(x, u, 0.1)
    np.testing.assert_allclose(result, [2, 0, 0, 0, 3.2, 0.2], atol=1e-14)
    np.testing.assert_array_equal(x, original)
    np.testing.assert_array_equal(u, [0, 0])


def test_straight_chart_heading(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    result = model.step(state_vector([2, 0, 0, 0.2, 3, 0.1]), [0, 0], 0.1)
    assert result[I.S_ABS] == pytest.approx(3 + 0.2 * np.cos(0.2), abs=1e-14)
    assert result[I.E_Y] == pytest.approx(0.1 + 0.2 * np.sin(0.2), abs=1e-14)
    assert result[I.E_PSI] == pytest.approx(0.2)


@pytest.mark.parametrize("acceleration", [0.5, -0.5])
def test_constant_acceleration(synthetic_vehicle, straight_geometry, acceleration):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    x = state_vector([2, 0, 0, 0, 3, 0])
    for _ in range(100):
        x = model.step(x, [0, acceleration])
    assert x[I.VX] == pytest.approx(2 + acceleration, abs=1e-12)
    assert x[I.S_ABS] == pytest.approx(3 + 2 + 0.5 * acceleration, abs=1e-12)


@pytest.mark.parametrize("dt", [0.05, 0.5, 1.0])
def test_braking_event(synthetic_vehicle, straight_geometry, dt):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    x = state_vector([1, 0, 0, 0, 3, 0.1])
    for _ in range(round(1 / dt)):
        x = model.step(x, [0, -2], dt)
    np.testing.assert_allclose(x, [0, 0, 0, 0, 3.25, 0.1], atol=1e-13)
    np.testing.assert_allclose(model.step(x, [0.2, -2], 1), x, atol=1e-13)


def test_braking_turn_stops_at_event(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    x = state_vector([1, 0, 0, 0, 3, 0])
    at_stop = model.step(x, [0.1, -2], 0.5)
    after_stop = model.step(x, [0.1, -2], 2)
    np.testing.assert_allclose(after_stop, at_stop, atol=1e-14)
    assert after_stop[I.VX] == after_stop[I.VY] == after_stop[I.YAW_RATE] == 0


def test_restart_from_rest(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    x = model.step(state_vector([0] * 6), [0, 1], 0.1)
    assert x[I.VX] == pytest.approx(0.1)
    assert x[I.S_ABS] == pytest.approx(0.005)


@pytest.mark.parametrize("delta", [-0.2, 0, 0.2])
def test_algebraic_signs_and_consistency(synthetic_vehicle, straight_geometry, delta):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    x = state_vector([1, 50, -50, 0, 10, 0])
    beta = atan(0.5 * tan(delta))
    for _ in range(25):
        x = model.step(x, [delta, 0.5])
        assert x[I.VY] == pytest.approx(x[I.VX] * tan(beta), abs=1e-14)
        assert x[I.YAW_RATE] == pytest.approx(x[I.VX] / 0.15 * tan(beta), abs=1e-14)
        assert np.sign(x[I.VY]) == np.sign(delta)
        assert np.sign(x[I.YAW_RATE]) == np.sign(delta)
    d = model.diagnostics(x, [delta, 0.5])
    assert d.beta == beta
    with pytest.raises(FrozenInstanceError):
        d.beta = 0


def test_instantaneous_steering_reconstructs_channels(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    x = state_vector([1, 0, 0, 0, 10, 0])
    positive = model.consistent_state(x, [0.2, 0])
    negative = model.consistent_state(positive, [-0.2, 0])
    assert negative[I.VY] == -positive[I.VY]
    assert negative[I.YAW_RATE] == -positive[I.YAW_RATE]
    assert negative[I.S_ABS] == positive[I.S_ABS]


def test_analytic_circle_steady_motion_and_seams(synthetic_vehicle, analytic_circle):
    model = KinematicBicycle(synthetic_vehicle, analytic_circle)
    beta = asin(0.15 / analytic_circle.radius)
    delta = atan(2 * tan(beta))
    length = analytic_circle.length
    x = state_vector([2, 0, 0, -beta, length - 0.1, 0])
    start = x[I.S_ABS]
    for _ in range(200):
        previous = x[I.S_ABS]
        x = model.step(x, [delta, 0], 0.1)
        assert x[I.S_ABS] > previous
        assert abs(x[I.E_Y]) < 1e-11
        assert abs(x[I.E_PSI] + beta) < 1e-11
    assert x[I.S_ABS] > 2 * length
    assert x[I.S_ABS] == pytest.approx(start + 40 / cos(beta), abs=1e-10)
    # CG path curvature is r/total_speed, NOT r/vx.
    assert x[I.YAW_RATE] / np.hypot(x[I.VX], x[I.VY]) == pytest.approx(1 / 5)


@pytest.mark.parametrize("denominator", [0, 1e-8, FRENET_DENOMINATOR_MIN / 2, -0.1])
def test_frenet_singularity(synthetic_vehicle, analytic_circle, denominator):
    model = KinematicBicycle(synthetic_vehicle, analytic_circle)
    x = state_vector([1, 0, 0, 0, 1, (1 - denominator) * 5])
    with pytest.raises(FrenetGeometryError, match=r"1-kappa\*e_y"):
        model.step(x, [0, 0])


def test_singularity_at_rk_stage(synthetic_vehicle, analytic_circle):
    model = KinematicBicycle(synthetic_vehicle, analytic_circle)
    # Positive lateral velocity reaches the invalid coordinate branch during the step.
    x = state_vector([1, 0, 0, pi / 2, 1, 4.99])
    with pytest.raises(FrenetGeometryError):
        model.step(x, [0, 0], 0.1)


@pytest.mark.parametrize(
    "control,match",
    [
        ([0.21, 0], "steering"),
        ([-0.21, 0], "steering"),
        ([0, 1.01], "acceleration"),
        ([0, -2.01], "braking"),
    ],
)
def test_configured_input_limits(synthetic_vehicle, straight_geometry, control, match):
    p = replace(
        synthetic_vehicle,
        maximum_steering_angle=0.2,
        maximum_acceleration=1,
        maximum_braking_deceleration=2,
    )
    with pytest.raises(ModelValidationError, match=match):
        KinematicBicycle(p, straight_geometry).step(state_vector([1, 0, 0, 0, 10, 0]), control)


def test_limits_at_boundary_and_undefined(synthetic_vehicle, straight_geometry):
    x = state_vector([1, 0, 0, 0, 10, 0])
    limited = replace(
        synthetic_vehicle,
        maximum_steering_angle=0.2,
        maximum_acceleration=1,
        maximum_braking_deceleration=2,
        maximum_steering_rate=0.001,
    )
    model = KinematicBicycle(limited, straight_geometry)
    model.step(x, [0.2, 1])
    model.step(x, [-0.2, -2])  # No steering-rate actuator state in this model.
    free = KinematicBicycle(synthetic_vehicle, straight_geometry)
    free.step(x, [0.4, 10], 0.001)
    assert free.step(x, [0, -100], 0.02)[I.VX] == 0


def test_speed_limit(synthetic_vehicle, straight_geometry):
    p = replace(synthetic_vehicle, maximum_speed=2)
    model = KinematicBicycle(p, straight_geometry)
    with pytest.raises(ModelValidationError, match="maximum_speed"):
        model.step(state_vector([2.1, 0, 0, 0, 10, 0]), [0, 0])
    with pytest.raises(ModelValidationError, match="maximum_speed"):
        model.step(state_vector([1.9, 0, 0, 0, 10, 0]), [0, 2], 0.1)
    result = model.step(state_vector([1.9, 0, 0, 0, 10, 0]), [0, 1], 0.1)
    assert result[I.VX] == 2
    result = model.step(state_vector([2 + SPEED_TOLERANCE / 2, 0, 0, 0, 10, 0]), [0, 0])
    assert result[I.VX] == 2


def test_negative_speed_tolerance(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    with pytest.raises(ModelValidationError, match="forward-only"):
        model.step(state_vector([-1e-6, 0, 0, 0, 10, 0]), [0, 0])
    result = model.step(state_vector([-SPEED_TOLERANCE / 2, 0, 0, 0, 10, 0]), [0, -1])
    assert result[I.VX] == 0
    assert result[I.S_ABS] == 10


@pytest.mark.parametrize("dt", [0, -0.1, float("nan"), float("inf")])
def test_invalid_timestep(synthetic_vehicle, straight_geometry, dt):
    with pytest.raises(ModelValidationError, match="dt"):
        KinematicBicycle(synthetic_vehicle, straight_geometry, default_dt=dt)
    with pytest.raises(ModelValidationError, match="dt"):
        KinematicBicycle(synthetic_vehicle, straight_geometry).step(
            state_vector([0] * 6), [0, 0], dt
        )


def test_default_timestep_and_angle_wrap(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry, default_dt=0.02)
    result = model.step(state_vector([1, 0, 0, 2 * pi, 10, 0]), [0, 0])
    assert result[I.S_ABS] == pytest.approx(10.02)
    assert result[I.E_PSI] == 0


@pytest.mark.parametrize("control", [[0], [0, float("nan")], [pi / 2, 0], [pi, 0]])
def test_invalid_control(synthetic_vehicle, straight_geometry, control):
    with pytest.raises(ValueError):
        KinematicBicycle(synthetic_vehicle, straight_geometry).step(state_vector([0] * 6), control)


def test_negative_progress_not_hidden(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    with pytest.raises(ModelValidationError, match="s_abs"):
        model.step(state_vector([1, 0, 0, pi, 0, 0]), [0, 0])
