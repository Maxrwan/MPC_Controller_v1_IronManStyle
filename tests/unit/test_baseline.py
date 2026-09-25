"""Independent signs, balances, DARE stability and saturation checks."""

from dataclasses import replace

import numpy as np
import pytest

from apex.control.baseline import BaselineController, ConstantSpeed, cornering_reference
from apex.control.baseline.lqr import (
    DesignScales,
    ScheduledLQR,
    continuous_matrices,
    discrete_matrices,
)
from apex.control.baseline.speed import SpeedPI


@pytest.mark.parametrize("v", [1.0, 2.0, 3.0])
def test_matrices_and_stability(dynamic_vehicle, v):
    a, b = continuous_matrices(dynamic_vehicle, v)
    ad, bd = discrete_matrices(dynamic_vehicle, v)
    assert a.shape == ad.shape == (4, 4)
    assert b.shape == bd.shape == (4, 1)
    assert np.all(np.isfinite(a)) and np.all(np.isfinite(b))
    assert (
        np.linalg.matrix_rank(np.hstack([np.linalg.matrix_power(a, j) @ b for j in range(4)])) == 4
    )
    gain, _, _ = ScheduledLQR(dynamic_vehicle).gain(v)
    assert np.all(np.isfinite(gain))
    assert max(abs(np.linalg.eigvals(ad - bd @ gain[None, :]))) < 1
    assert a[0, 1] == v
    assert a[2, 2] == pytest.approx(-45 / v)
    assert b[2, 0] == 22.5 and b[3, 0] == 270.0


def test_bryson_weights_and_speed_dependence(dynamic_vehicle):
    q, r = DesignScales().weights()
    np.testing.assert_allclose(q, np.diag([100, 100, 4, 1]))
    np.testing.assert_allclose(r, [[25]])
    assert not np.allclose(
        continuous_matrices(dynamic_vehicle, 1)[0], continuous_matrices(dynamic_vehicle, 3)[0]
    )


@pytest.mark.parametrize("v", [1.0, 1.5, 2.0, 2.5, 3.0])
def test_interpolation(dynamic_vehicle, v):
    lqr = ScheduledLQR(dynamic_vehicle)
    k, actual, clamped = lqr.gain(v)
    expected = np.array([np.interp(v, lqr.nodes, lqr.gains[:, j]) for j in range(4)])
    np.testing.assert_array_equal(k, expected)
    if v in (1.5, 2.5):
        i = int(v) - 1
        np.testing.assert_allclose(k, 0.5 * (lqr.gains[i] + lqr.gains[i + 1]))
    assert actual == v and not clamped


def test_interpolated_stability(dynamic_vehicle):
    lqr = ScheduledLQR(dynamic_vehicle)
    for v in np.linspace(1, 3, 101):
        a, b = discrete_matrices(dynamic_vehicle, v)
        k, _, _ = lqr.gain(v)
        assert max(abs(np.linalg.eigvals(a - b @ k[None, :]))) < 1


@pytest.mark.parametrize("index", [3, 5])
@pytest.mark.parametrize("sign", [-1, 1])
def test_feedback_sign(dynamic_vehicle, straight_geometry, index, sign):
    c = BaselineController(dynamic_vehicle, straight_geometry)
    x = np.array([2.0, 0, 0, 0, 0, 0])
    x[index] = sign * 0.01
    command = c.compute_control(x, {})
    assert command[0] * sign < 0


@pytest.mark.parametrize("v", [1.0, 2.0, 3.0])
@pytest.mark.parametrize("curvature", [-0.2, 0, 0.2])
def test_cornering_force_and_moment_balance(dynamic_vehicle, v, curvature):
    p = dynamic_vehicle
    ref = cornering_reference(p, v, curvature)
    fyf = p.front_cornering_stiffness * (ref.delta_dynamic - (ref.vy + p.lf * ref.yaw_rate) / v)
    fyr = p.rear_cornering_stiffness * (-(ref.vy - p.lr * ref.yaw_rate) / v)
    assert fyf + fyr == pytest.approx(p.mass * v * ref.yaw_rate, abs=1e-13)
    assert p.lf * fyf - p.lr * fyr == pytest.approx(0, abs=1e-13)
    assert ref.yaw_rate == v * curvature
    assert np.isfinite(ref.vy)
    assert ref.delta_dynamic == pytest.approx(0.3 * curvature)
    assert ref.delta_kinematic == pytest.approx(np.arctan(0.3 * curvature))
    if curvature == 0:
        assert ref.vy == ref.yaw_rate == ref.delta_dynamic == ref.delta_kinematic == 0
    else:
        assert ref.delta_dynamic * curvature > 0
        # vy need NOT share curvature sign: this fixture changes sign at high speed.
        assert ref.vy == pytest.approx(v * curvature * (0.15 - 2 * v * v * 0.15 / (0.3 * 45)))


def test_asymmetric_reference(dynamic_vehicle):
    p = replace(dynamic_vehicle, lf=0.12, lr=0.18, front_cornering_stiffness=30.0)
    ref = cornering_reference(p, 2.0, 0.2)
    assert ref.delta_dynamic == pytest.approx(
        0.3 * 0.2 + 2 * 4 * 0.2 / 0.3 * (0.18 / 30 - 0.12 / 45)
    )


@pytest.mark.parametrize("speed,expected", [(1, 1), (3, -1)])
def test_pi_direction(speed, expected):
    d = SpeedPI(2, 3).update(speed, 2, 0.01)
    assert d.acceleration * expected > 0


@pytest.mark.parametrize("speed,reference,limit", [(0, 10, 2), (10, 0, -3)])
def test_pi_antiwindup_and_limits(speed, reference, limit):
    c = SpeedPI(2, 3)
    for _ in range(1000):
        d = c.update(speed, reference, 0.01)
    assert d.acceleration == limit and d.acceleration_saturated and d.integration_blocked
    assert c.integral == 0
    c.update(1, 2, 0.1)
    assert c.integral > 0
    c.reset()
    assert c.integral == 0


def test_pi_can_unwind():
    c = SpeedPI(2, 3)
    c.integral = 10
    d = c.update(2.1, 2, 0.01)
    assert not d.integration_blocked and c.integral < 10


def test_command_saturation_and_reset(dynamic_vehicle, circle):
    c = BaselineController(dynamic_vehicle, circle)
    u = c.compute_control(np.array([2.0, 0, 0, 0, 0, 20]), {})
    assert u[0] == -0.4 and c.diagnostics()["steering_saturated"]
    assert c.diagnostics()["delta_unsaturated"] < -0.4
    c.reset()
    assert c.previous_delta == c.speed.integral == 0
    assert not c.diagnostics()


def test_configured_rate_limit(dynamic_vehicle, circle):
    c = BaselineController(replace(dynamic_vehicle, maximum_steering_rate=1.0), circle)
    for _ in range(5):
        c.compute_control(np.array([2.0, 0, 0, 0, 0, 0.1]), {})
        assert abs(c.diagnostics()["steering_rate"]) <= 1 + 1e-12
    assert c.diagnostics()["steering_rate_limited"]


@pytest.mark.parametrize("v,node", [(0.8, 1), (3.2, 3)])
def test_schedule_clamps_only_variable(dynamic_vehicle, circle, v, node):
    x = np.array([v, 0, 0, 0, 0, 0])
    before = x.copy()
    c = BaselineController(dynamic_vehicle, circle)
    c.compute_control(x, {})
    np.testing.assert_array_equal(x, before)
    assert c.diagnostics()["scheduling_speed"] == node
    assert c.diagnostics()["scheduling_clamped"]
    assert c.diagnostics()["r_ref"] == pytest.approx(v * circle.sample(0).curvature)


def test_progress_reference_and_lap_seam(dynamic_vehicle, circle):
    def profile(s):
        return 2 + 0.5 * np.sin(2 * np.pi * s / circle.length)

    commands = []
    for s in (0.0, circle.length, 2 * circle.length):
        c = BaselineController(dynamic_vehicle, circle, profile)
        commands.append(c.compute_control(np.array([2.0, 0.024, 0.4, 0, s, 0.02]), {}))
        assert c.diagnostics()["reference_speed"] == 2
    np.testing.assert_allclose(commands, np.tile(commands[0], (3, 1)), atol=1e-12)
    c = BaselineController(dynamic_vehicle, circle, profile)
    c.compute_control(np.array([2.0, 0, 0, 0, circle.length / 4, 0]), {})
    assert c.diagnostics()["reference_speed"] == pytest.approx(2.5)
    # Near seam: equivalent inputs must not generate a geometric jump.
    near = []
    for s in (circle.length - 1e-7, circle.length + 1e-7):
        c.reset()
        near.append(c.compute_control(np.array([2.0, 0.024, 0.4, 0, s, 0.02]), {}))
    np.testing.assert_allclose(*near, atol=1e-7)


@pytest.mark.parametrize("v", [0, np.nan, np.inf, -1])
def test_invalid_design_speed(dynamic_vehicle, v):
    with pytest.raises(ValueError):
        continuous_matrices(dynamic_vehicle, v)


@pytest.mark.parametrize("v", [0.5, 3.5, np.nan])
def test_invalid_speed_reference(v):
    with pytest.raises(ValueError):
        ConstantSpeed(v)


def test_controller_context_rate_mismatch(dynamic_vehicle, circle):
    with pytest.raises(ValueError, match="dt"):
        BaselineController(dynamic_vehicle, circle).compute_control(
            np.array([2.0, 0, 0, 0, 0, 0]), {"dt": 0.02}
        )


def test_missing_command_limit_rejected(dynamic_vehicle, circle):
    with pytest.raises(ValueError, match="maximum_steering_angle"):
        BaselineController(replace(dynamic_vehicle, maximum_steering_angle=None), circle)


@pytest.mark.parametrize("dt", [0, -1, np.nan])
def test_invalid_discretization_period(dynamic_vehicle, dt):
    with pytest.raises(ValueError):
        discrete_matrices(dynamic_vehicle, 2, dt)


def test_invalid_design_scale():
    with pytest.raises(ValueError):
        DesignScales(e_y=0).weights()
