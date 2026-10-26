"""O04/O05: hand-rational force/load and body derivative expectations."""

import numpy as np


def test_exact_zero_slip_partials(parameters, point, jet):
    from ct1.analytic import continuous_pair, force_load_partials

    q = force_load_partials(point.x, point.u, parameters).unwrap()
    np.testing.assert_allclose(q.load_input_partials[:, 1], [-4 / 15, 4 / 15], atol=1e-7, rtol=1e-4)
    np.testing.assert_allclose(q.force_input_partials[:, 0], [45, 0], atol=1e-7, rtol=1e-4)
    np.testing.assert_allclose(
        q.force_state_partials[:, 1], [-45 / 2, -45 / 2], atol=1e-7, rtol=1e-4
    )
    np.testing.assert_allclose(
        q.force_state_partials[:, 2], [-27 / 8, 27 / 8], atol=1e-7, rtol=1e-4
    )
    p = continuous_pair(point, parameters, jet, policy=point.kappa_policy).unwrap()
    np.testing.assert_allclose(p.B[:3], [[0, 1], [45 / 2, 0], [270, 0]], atol=1e-7, rtol=1e-4)
    np.testing.assert_allclose(p.A[1:3, 1:3], [[-45 / 2, -2], [0, -81 / 2]], atol=1e-7, rtol=1e-4)


def test_nonzero_slip_acceleration_derivative(parameters, point):
    from ct1.analytic import force_load_partials

    q = force_load_partials(point.x, (0.02, 0.0), parameters).unwrap()
    expected = (-4 / 15) * np.tanh(45 * 0.02 / (981 / 100))
    assert abs(q.force_input_partials[0, 1] - expected) <= 1e-7 + 1e-4 * abs(expected)


def test_invalid_capacity_not_regularized(parameters, point):
    from dataclasses import replace

    from ct1.analytic import force_load_partials

    low = replace(parameters, values={**parameters.values, "tire_road_friction_coefficient": 0.01})
    assert force_load_partials(point.x, (0.0, 1.0), low).value is None


def test_mixed_steering_acceleration_slope(parameters, point):
    from ct1.analytic import force_load_partials

    h = 1e-5
    left = force_load_partials(point.x, (0.0, -h), parameters).unwrap().force_input_partials[0, 0]
    right = force_load_partials(point.x, (0.0, h), parameters).unwrap().force_input_partials[0, 0]
    expected = -400 / 327  # C_f*(-m*h/L)/Z_front_static, independent rational definition.
    assert abs((right - left) / (2 * h) - expected) <= 1e-7 + 1e-4 * abs(expected)
