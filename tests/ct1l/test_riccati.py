"""O12/O13 exact scalar radical DARE and rational finite recursion, independent oracle."""

import math

import numpy as np
import pytest


def test_scalar_terminal_and_finite_step():
    from ct1.riccati import _backward_step, _terminal_solution

    a = b = q = r = np.array([[1.0]])
    p = _terminal_solution(a, b, q, r)
    assert abs(p[0, 0] - (1 + math.sqrt(5)) / 2) <= 1e-8
    k, new, h = _backward_step(a, b, q, r, np.array([[1.0]]))
    assert k[0, 0] == 0.5 and new[0, 0] == 1.5 and h[0, 0] == 2


def test_gain_corruption_preserved(inputs):
    from ct1.riccati import compare_original_gains

    expected = np.array([[(math.sqrt(5) - 1) / 2]])
    before = expected.copy()
    result = compare_original_gains(expected, expected + 0.01, inputs.metrics["Riccati"])
    assert result["comparison"] == "FAIL" and not result["original_replaced"]
    assert np.array_equal(expected, before)


def test_nonpositive_h_not_regularized():
    from ct1.riccati import _backward_step

    with pytest.raises(ValueError):
        _backward_step(
            np.ones((1, 1)), np.ones((1, 1)), np.ones((1, 1)), np.zeros((1, 1)), np.zeros((1, 1))
        )
