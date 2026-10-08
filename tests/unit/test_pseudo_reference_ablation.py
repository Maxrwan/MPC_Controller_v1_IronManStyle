"""Specified C2 weighting and compatible DARE; no changes to TVLQR or vehicle states."""

import casadi as ca
import numpy as np
import pytest
from scipy.linalg import solve_discrete_are

from apex.control.baseline.lqr import DesignScales, discrete_matrices
from apex.control.mpc.cost import CostScales, TerminalSchedule, stage_components

PAIRS = [(1, 1), (0.5, 1), (0.25, 1), (0, 1), (1, 0.5), (1, 0.25), (1, 0), (0.25, 0.25), (0, 0)]


@pytest.mark.parametrize("vy,r", PAIRS)
def test_stage_tracking_and_dare_match_spec(dynamic_vehicle, vy, r):
    # Error order vx,vy,r,epsi,ey; retain all nonlinear channels when their cost is zero.
    x = ca.DM([1, 2, 3, 4, 5, 6])
    preview = ca.DM.zeros(11)
    cost = stage_components(
        x, ca.DM.zeros(2), ca.DM.zeros(2), preview, CostScales(lateral=2, alpha_vy=vy, alpha_r=r)
    )[0]
    assert float(cost) == pytest.approx(4 + 4 * vy * 4 + r * 9 + 200 * 16 + 200 * 36)
    schedule = TerminalSchedule(dynamic_vehicle, alpha_vy=vy, alpha_r=r)
    q, rr = DesignScales().weights()
    q[2, 2] *= vy
    q[3, 3] *= r
    for speed, p in zip(schedule.nodes, schedule.matrices):
        a, b = discrete_matrices(dynamic_vehicle, speed, 0.01)
        k = np.linalg.solve(rr + b.T @ p @ b, b.T @ p @ a)
        residual = a.T @ p @ a - p - a.T @ p @ b @ k + q
        assert np.linalg.norm(residual, ord=np.inf) / max(1, np.linalg.norm(p, ord=np.inf)) < 1e-10
        np.testing.assert_allclose(p, p.T, atol=1e-10)
        assert np.linalg.eigvalsh(p).min() >= -1e-9
        assert max(abs(np.linalg.eigvals(a - b @ k))) < 1


def test_default_schedule_is_exact_prior_dare(dynamic_vehicle):
    q, r = DesignScales().weights()
    schedule = TerminalSchedule(dynamic_vehicle)
    old = np.array(
        [solve_discrete_are(*discrete_matrices(dynamic_vehicle, v, 0.01), q, r) for v in [1, 2, 3]]
    )
    np.testing.assert_array_equal(schedule.matrices, old)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_bad_multipliers_rejected(value):
    with pytest.raises(ValueError):
        CostScales(alpha_vy=value)
    with pytest.raises(ValueError):
        CostScales(alpha_r=value)
