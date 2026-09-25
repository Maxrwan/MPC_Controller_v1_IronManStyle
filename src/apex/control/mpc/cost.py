"""Explicit development cost and ordered lateral terminal mapping."""

from dataclasses import dataclass

import casadi as ca
import numpy as np
from scipy.linalg import solve_discrete_are

from apex.control.baseline.lqr import DesignScales, discrete_matrices
from apex.state import StateIndex as S

STATE_WEIGHTS = np.array([4.0, 4.0, 1.0, 100.0, 100.0])
INPUT_WEIGHTS = np.array([25.0, 1.0])
# Increment penalties: modest relative to input costs; these are NOT derivative costs.
RATE_WEIGHTS = np.array([1.0, 0.1])
SLACK_LINEAR = 1e4
SLACK_QUADRATIC = 1e5


@dataclass(frozen=True)
class CostScales:
    lateral: float = 1.0
    dynamic: float = 1.0
    speed: float = 1.0
    control: float = 1.0
    rate: float = 1.0
    terminal: float = 1.0

    def __post_init__(self):
        values = (self.lateral, self.dynamic, self.speed, self.control, self.rate)
        if not all(np.isfinite(v) and v > 0 for v in values):
            raise ValueError("Stage cost multipliers must be finite positive")
        if not np.isfinite(self.terminal) or self.terminal < 0:
            raise ValueError("Terminal multiplier must be finite nonnegative")


def tracking_error(x, preview):
    return ca.vertcat(
        x[S.VX] - preview[3], x[S.VY] - preview[4], x[S.YAW_RATE] - preview[5], x[S.E_PSI], x[S.E_Y]
    )


def stage_cost(x, u, previous, preview, scales=CostScales()):
    e = tracking_error(x, preview)
    du_ref = u - ca.vertcat(preview[6], 0)
    change = u - previous
    return (
        ca.dot(
            STATE_WEIGHTS
            * np.array(
                [scales.speed, scales.dynamic, scales.dynamic, scales.lateral, scales.lateral]
            )
            * e,
            e,
        )
        + scales.control * ca.dot(INPUT_WEIGHTS * du_ref, du_ref)
        + scales.rate * ca.dot(RATE_WEIGHTS * change, change)
    )


def terminal_cost(x, preview, p):
    # Task 005 order differs from MPC order. No s_abs cost.
    lateral = ca.vertcat(x[S.E_Y], x[S.E_PSI], x[S.VY] - preview[4], x[S.YAW_RATE] - preview[5])
    return ca.mtimes([lateral.T, p, lateral]) + 4 * (x[S.VX] - preview[3]) ** 2


class TerminalSchedule:
    """Reuse the Task 005 100 Hz DARE construction, unchanged, as provisional P."""

    def __init__(self, parameters):
        q, r = DesignScales().weights()
        self.nodes = np.array([1.0, 2.0, 3.0])
        self.matrices = np.array(
            [solve_discrete_are(*discrete_matrices(parameters, v, 0.01), q, r) for v in self.nodes]
        )

    def matrix(self, speed):
        speed = np.clip(speed, 1, 3)
        return np.array(
            [
                np.interp(speed, self.nodes, self.matrices[:, i, j])
                for i in range(4)
                for j in range(4)
            ]
        ).reshape(4, 4)
