from dataclasses import FrozenInstanceError, replace
from math import atan2, pi, tan

import numpy as np
import pytest

from apex.models.errors import (
    FrenetGeometryError,
    LowSpeedValidityError,
    ModelValidationError,
    VehicleModelValidityError,
)
from apex.models.tire.base import AxleTireResult
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.models.vehicle.kinematic import DEFAULT_TIMESTEP
from apex.models.vehicle.load_transfer import AxleLoads
from apex.state import StateIndex as I
from apex.state import state_vector


@pytest.mark.parametrize(
    "missing",
    [
        "mass",
        "yaw_inertia",
        "wheelbase",
        "lf",
        "lr",
        "cg_height",
        "front_cornering_stiffness",
        "rear_cornering_stiffness",
    ],
)
def test_model_specific_readiness(dynamic_vehicle, straight_geometry, missing):
    with pytest.raises(ValueError, match="Undefined dynamic"):
        DynamicBicycle(replace(dynamic_vehicle, **{missing: None}), straight_geometry)


def test_only_dynamic_parameters_required(dynamic_vehicle, straight_geometry):
    p = replace(dynamic_vehicle, tire_road_friction_coefficient=None)
    model = DynamicBicycle(p, straight_geometry)
    assert model.default_dt == 0.005
    assert DEFAULT_TIMESTEP == 0.01  # Kinematic default unchanged.
    assert model.diagnostics(state_vector([2, 0, 0, 0, 1, 0]), [0, 0]).mu is None
    assert (
        model.diagnostics(state_vector([2, 0, 0, 0, 1, 0]), [0, 0]).front_lateral_utilization
        is None
    )
    with pytest.raises(ValueError, match="Undefined vehicle"):
        p.validate_for_simulation()


def test_zero_slip_and_straight_acceleration(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    x = state_vector([2, 0, 0, 0, 1, 0])
    d = model.diagnostics(x, [0, 0.5])
    assert d.alpha_f == d.alpha_r == d.fyf == d.fyr == 0
    np.testing.assert_allclose(model.derivative(x, [0, 0.5]), [0.5, 0, 0, 0, 2, 0], atol=1e-14)
    result = model.step(x, [0, 0.5], 0.1)
    np.testing.assert_allclose(result, [2.05, 0, 0, 0, 1.2025, 0], atol=1e-13)


@pytest.mark.parametrize("delta", [-0.03, 0.03])
def test_steering_sign(dynamic_vehicle, straight_geometry, delta):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    x = state_vector([2, 0, 0, 0, 1, 0])
    d = model.diagnostics(x, [delta, 0])
    derivative = model.derivative(x, [delta, 0])
    assert np.sign(d.alpha_f) == np.sign(d.fyf) == np.sign(derivative[I.YAW_RATE]) == np.sign(delta)
    assert d.alpha_r == d.fyr == 0


@pytest.mark.parametrize("vy,r", [(0.1, 0), (-0.1, 0), (0, 0.2), (0, -0.2)])
def test_rear_slip_convention(dynamic_vehicle, straight_geometry, vy, r):
    d = DynamicBicycle(dynamic_vehicle, straight_geometry).diagnostics(
        state_vector([2, vy, r, 0, 1, 0]), [0, 0]
    )
    assert d.alpha_r == pytest.approx(-atan2(vy - 0.15 * r, 2))
    assert np.sign(d.fyr) == -np.sign(vy - 0.15 * r)


def test_exact_atan2_not_small_angle(dynamic_vehicle, straight_geometry):
    d = DynamicBicycle(dynamic_vehicle, straight_geometry).diagnostics(
        state_vector([2, 0.4, 0.2, 0, 1, 0]), [0.2, 0]
    )
    assert d.alpha_f == pytest.approx(0.2 - atan2(0.43, 2), abs=1e-15)
    assert abs(d.alpha_f - (0.2 - 0.43 / 2)) > 1e-3


def test_hand_computable_force_moment(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    x = state_vector([2, 2 * tan(0.1), 0, 0, 1, 0])
    d = model.diagnostics(x, [0.15, 0])
    dx = model.derivative(x, [0.15, 0])
    assert d.alpha_f == pytest.approx(0.05, abs=1e-15)
    assert d.alpha_r == pytest.approx(-0.1, abs=1e-15)
    assert d.fyf == pytest.approx(2.25, abs=1e-13)
    assert d.fyr == pytest.approx(-4.5, abs=1e-13)
    assert dx[I.VY] == pytest.approx(-1.125, abs=1e-13)
    assert dx[I.YAW_RATE] == pytest.approx(40.5, abs=1e-12)


def test_input_semantics_and_load_acceleration(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    x = state_vector([2, 0.1, 0.2, 0, 1, 0])
    u = [0.03, 1.2]
    d = model.diagnostics(x, u)
    dx = model.derivative(x, u)
    assert d.fx_total == pytest.approx(2.4)
    assert dx[I.VX] == pytest.approx(1.22)
    assert dx[I.VX] - 0.2 * 0.1 == pytest.approx(d.a_cmd)
    assert d.fzf == pytest.approx(9.81 - 2 * 1.2 * 0.04 / 0.3)


@pytest.mark.parametrize("acceleration", [-1, 1])
def test_load_scaled_stiffness(dynamic_vehicle, straight_geometry, acceleration):
    d = DynamicBicycle(dynamic_vehicle, straight_geometry).diagnostics(
        state_vector([2, 0.03, 0.2, 0, 1, 0]), [0.03, acceleration]
    )
    assert d.cf_eff == pytest.approx(45 * d.fzf / d.fzf_static)
    assert d.cr_eff == pytest.approx(45 * d.fzr / d.fzr_static)
    assert np.sign(d.cf_eff - d.cf) == -np.sign(acceleration)
    assert np.sign(d.cr_eff - d.cr) == np.sign(acceleration)


def test_mu_diagnostic_only(dynamic_vehicle, straight_geometry):
    x = state_vector([2, 0, 0, 0, 1, 0])
    u = [0.3, 0]
    a = DynamicBicycle(dynamic_vehicle, straight_geometry).diagnostics(x, u)
    b = DynamicBicycle(
        replace(dynamic_vehicle, tire_road_friction_coefficient=0.1), straight_geometry
    ).diagnostics(x, u)
    assert a.fyf == b.fyf == 13.5
    assert a.front_lateral_utilization > 1
    assert b.front_lateral_utilization == pytest.approx(10 * a.front_lateral_utilization)


def test_replaceable_tire_and_load_components(dynamic_vehicle, straight_geometry):
    class ZeroTire:
        def evaluate(self, slip_angle, nominal_stiffness, normal_load, static_load):
            return AxleTireResult(0, 0)

    class StaticLoad:
        def evaluate(self, parameters, a_cmd):
            return AxleLoads(8, 12, 8, 12)

    model = DynamicBicycle(
        dynamic_vehicle, straight_geometry, tire_model=ZeroTire(), load_model=StaticLoad()
    )
    d = model.diagnostics(state_vector([2, 0, 0, 0, 1, 0]), [0.2, 1])
    assert d.fzf == 8 and d.fzr == 12 and d.fyf == d.fyr == 0
    assert model.derivative(state_vector([2, 0, 0, 0, 1, 0]), [0.2, 1])[I.YAW_RATE] == 0


@pytest.mark.parametrize("vx", [-1, 0, 0.49])
def test_low_speed_rejected(dynamic_vehicle, straight_geometry, vx):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    with pytest.raises(LowSpeedValidityError, match="minimum"):
        model.step(state_vector([vx, 0, 0, 0, 1, 0]), [0, 0])


def test_minimum_speed_configurable_and_not_clipped(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry, v_dynamic_min=0.2)
    vx = 0.2 - 1e-11
    x = model.step(state_vector([vx, 0, 0, 0, 1, 0]), [0, 0])
    assert x[I.VX] == vx
    with pytest.raises(LowSpeedValidityError):
        model.derivative(state_vector([0.19, 0, 0, 0, 1, 0]), [0, 0])


def test_braking_stage_rejects_without_switch_or_mutation(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    x = state_vector([0.51, 0, 0, 0, 1, 0])
    original = x.copy()
    with pytest.raises(LowSpeedValidityError):
        model.step(x, [0, -1], 0.02)
    np.testing.assert_array_equal(x, original)


@pytest.mark.parametrize("denominator", [0, -0.1, 1e-5])
def test_frenet_invalid(dynamic_vehicle, analytic_circle, denominator):
    model = DynamicBicycle(dynamic_vehicle, analytic_circle)
    with pytest.raises(FrenetGeometryError):
        model.derivative(state_vector([2, 0, 0, 0, 1, 5 * (1 - denominator)]), [0, 0])


@pytest.mark.parametrize("acceleration", [-40, 40])
def test_unloading_reaches_model_exception(dynamic_vehicle, straight_geometry, acceleration):
    p = replace(dynamic_vehicle, maximum_acceleration=None, maximum_braking_deceleration=None)
    with pytest.raises(VehicleModelValidityError, match="unloading"):
        DynamicBicycle(p, straight_geometry).derivative(
            state_vector([2, 0, 0, 0, 1, 0]), [0, acceleration]
        )


@pytest.mark.parametrize(
    "control,match",
    [
        ([0.41, 0], "steering"),
        ([-0.41, 0], "steering"),
        ([0, 2.1], "acceleration"),
        ([0, -3.1], "braking"),
    ],
)
def test_configured_control_limits(dynamic_vehicle, straight_geometry, control, match):
    with pytest.raises(ModelValidationError, match=match):
        DynamicBicycle(dynamic_vehicle, straight_geometry).step(
            state_vector([2, 0, 0, 0, 1, 0]), control
        )


def test_speed_limits_and_undefined_limits(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    with pytest.raises(ModelValidationError, match="speed"):
        model.step(state_vector([6.01, 0, 0, 0, 1, 0]), [0, 0])
    with pytest.raises(ModelValidationError, match="speed"):
        model.step(state_vector([5.99, 0, 0, 0, 1, 0]), [0, 2], 0.02)
    p = replace(
        dynamic_vehicle,
        maximum_speed=None,
        maximum_steering_angle=None,
        maximum_acceleration=None,
        maximum_braking_deceleration=None,
    )
    result = DynamicBicycle(p, straight_geometry).derivative(
        state_vector([7, 0, 0, 0, 1, 0]), [0.5, 5]
    )
    assert np.all(np.isfinite(result))


@pytest.mark.parametrize("dt", [0, -1, float("nan"), float("inf")])
def test_invalid_dt(dynamic_vehicle, straight_geometry, dt):
    with pytest.raises(ModelValidationError):
        DynamicBicycle(dynamic_vehicle, straight_geometry, default_dt=dt)
    with pytest.raises(ModelValidationError):
        DynamicBicycle(dynamic_vehicle, straight_geometry).step(
            state_vector([2, 0, 0, 0, 1, 0]), [0, 0], dt
        )


def test_deterministic_pure_derivative_and_dynamic_channels(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    x = state_vector([2, 0.02, 0.1, 0, 1, 0])
    u = np.array([0.03, 0.2])
    x0 = x.copy()
    u0 = u.copy()
    np.testing.assert_array_equal(model.derivative(x, u), model.derivative(x, u))
    result = model.step(x, u, 1e-6)
    assert abs(result[I.VY] - x[I.VY]) < 1e-5
    assert abs(result[I.YAW_RATE] - x[I.YAW_RATE]) < 1e-5
    assert result[I.VY] != pytest.approx(result[I.VX] * 0.5 * np.tan(0.03), abs=1e-3)
    np.testing.assert_array_equal(x, x0)
    np.testing.assert_array_equal(u, u0)
    with pytest.raises(FrozenInstanceError):
        model.diagnostics(x, u).mu = 0


def test_angles_only_wrapped_after_step(dynamic_vehicle, straight_geometry):
    result = DynamicBicycle(dynamic_vehicle, straight_geometry).step(
        state_vector([2, 0, 0, 2 * pi, 1, 0]), [0, 0]
    )
    assert result[I.E_PSI] == 0
    assert result[I.S_ABS] > 1


@pytest.mark.parametrize("minimum", [0, -1, float("nan"), float("inf")])
def test_invalid_minimum(dynamic_vehicle, straight_geometry, minimum):
    with pytest.raises(ModelValidationError):
        DynamicBicycle(dynamic_vehicle, straight_geometry, v_dynamic_min=minimum)


def test_instantaneous_mechanical_power_balance(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    x = state_vector([2, 0.1, 0.2, 0, 1, 0])
    u = [0.03, 0.4]
    d, dx = model.diagnostics(x, u), model.derivative(x, u)
    kinetic_rate = (
        2 * (x[I.VX] * dx[I.VX] + x[I.VY] * dx[I.VY]) + 0.025 * x[I.YAW_RATE] * dx[I.YAW_RATE]
    )
    force_power = (
        x[I.VX] * d.fx_total
        + x[I.VY] * (d.fyf + d.fyr)
        + x[I.YAW_RATE] * (0.15 * d.fyf - 0.15 * d.fyr)
    )
    assert kinetic_rate == pytest.approx(force_power, abs=1e-13)


def test_components_recomputed_at_stages_and_final(dynamic_vehicle, straight_geometry):
    from apex.models.tire.linear import LinearAxleTire
    from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer

    class RecordingTire(LinearAxleTire):
        def __init__(self):
            self.slips = []

        def evaluate(self, slip_angle, nominal_stiffness, normal_load, static_load):
            self.slips.append(slip_angle)
            return super().evaluate(slip_angle, nominal_stiffness, normal_load, static_load)

    class RecordingLoad:
        def __init__(self):
            self.accelerations = []

        def evaluate(self, parameters, a_cmd):
            self.accelerations.append(a_cmd)
            return QuasiStaticLongitudinalLoadTransfer().evaluate(parameters, a_cmd)

    class RecordingTrack:
        length = straight_geometry.length

        def __init__(self):
            self.queries = []

        def sample(self, s):
            self.queries.append(s)
            return straight_geometry.sample(s)

    tire, loads, track = RecordingTire(), RecordingLoad(), RecordingTrack()
    model = DynamicBicycle(dynamic_vehicle, track, tire_model=tire, load_model=loads)
    model.step(state_vector([2, 0, 0, 0, 1, 0]), [0.03, 0.2])
    assert len(tire.slips) == 10  # Two axles, four RK stages plus final validity check.
    assert len(set(tire.slips)) > 4
    assert loads.accelerations == [0.2] * 5
    assert len(track.queries) == 5
    assert len(set(track.queries)) > 2
