"""Parameterized direct multiple shooting, with domain guards at RK4 stages."""

from dataclasses import dataclass
from time import perf_counter

import casadi as ca
import numpy as np

from apex.control.mpc.cost import (
    SLACK_LINEAR,
    SLACK_QUADRATIC,
    CostScales,
    stage_cost,
    terminal_cost,
)
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.models.constants import STANDARD_GRAVITY
from apex.models.tire.config import TirePhysics
from apex.models.tire.grip import LONGITUDINAL_MARGIN
from apex.state import StateIndex as S


@dataclass(frozen=True)
class MPCConfig:
    tire_physics: TirePhysics = TirePhysics()
    costs: CostScales = CostScales()
    horizon: int = 20
    dt: float = 0.05
    substeps: int = 5
    steering_rate: float = 1.0
    minimum_speed: float = 0.5
    denominator_margin: float = 0.01
    minimum_axle_load: float = 1e-6
    tracker_margin: float = 0.0

    def __post_init__(self):
        if not np.isfinite(self.tracker_margin) or self.tracker_margin < 0:
            raise ValueError("Tracker margin must be finite nonnegative")
        if not isinstance(self.horizon, int) or self.horizon < 1:
            raise ValueError("Positive integer horizon required")
        if not isinstance(self.substeps, int) or self.substeps < 1:
            raise ValueError("Positive integer substeps required")
        if not all(
            np.isfinite(v) and v > 0
            for v in (
                self.dt,
                self.steering_rate,
                self.minimum_speed,
                self.denominator_margin,
                self.minimum_axle_load,
            )
        ):
            raise ValueError("MPC configuration values must be finite positive")


class MPCProblem:
    def __init__(self, parameters, config=MPCConfig()):
        construction_start = perf_counter()
        self.parameters, self.config = parameters, config
        for field in (
            "maximum_steering_angle",
            "maximum_acceleration",
            "maximum_braking_deceleration",
            "maximum_speed",
        ):
            if getattr(parameters, field) is None:
                raise ValueError(f"MPC requires configured {field}")
        self.model = SymbolicBicycle(parameters, config.tire_physics)
        self.transition = self.model.rk4(config.dt, config.substeps)
        n = config.horizon
        x = ca.MX.sym("X", 6, n + 1)
        u = ca.MX.sym("U", 2, n)
        slack = ca.MX.sym("slack", 2, n + 1)
        p = ca.MX.sym("parameters", 6 + 2 + 7 * (n + 1) + 16)
        sampled, previous = p[:6], p[6:8]
        preview = ca.reshape(p[8 : 8 + 7 * (n + 1)], 7, n + 1)
        terminal_p = ca.reshape(p[-16:], 4, 4)
        equalities = [x[:, 0] - sampled]
        inequalities, lower, upper = [], [], []

        def bounded(expression, lo, hi):
            expression = ca.vec(expression)
            count = expression.numel()
            inequalities.append(expression)
            lower.extend(np.broadcast_to(lo, (count,)).tolist())
            upper.extend(np.broadcast_to(hi, (count,)).tolist())

        def domain(state, kappa):
            bounded(
                self.model.domain(state, kappa),
                [config.minimum_speed, config.denominator_margin],
                [parameters.maximum_speed, np.inf],
            )

        objective = 0
        for k in range(n + 1):
            bound_left = x[S.E_Y, k] - preview[1, k] + config.tracker_margin - slack[0, k]
            bound_right = -x[S.E_Y, k] - preview[2, k] + config.tracker_margin - slack[1, k]
            bounded(ca.vertcat(bound_left, bound_right), -np.inf, 0)
            domain(x[:, k], preview[0, k])
            objective += SLACK_LINEAR * ca.sum1(slack[:, k]) + SLACK_QUADRATIC * ca.sumsqr(
                slack[:, k]
            )
            if k == n:
                objective += config.costs.terminal * terminal_cost(
                    x[:, k], preview[:, k], terminal_p
                )
                continue
            prior = previous if k == 0 else u[:, k - 1]
            objective += stage_cost(x[:, k], u[:, k], prior, preview[:, k], config.costs)
            bounded(
                u[0, k] - prior[0],
                -config.steering_rate * config.dt,
                config.steering_rate * config.dt,
            )
            bounded(self.model.loads(u[:, k]), config.minimum_axle_load, np.inf)
            if self.model.longitudinal_domain is not None:
                bounded(
                    self.model.longitudinal_domain(u[:, k]),
                    -(1 - LONGITUDINAL_MARGIN),
                    1 - LONGITUDINAL_MARGIN,
                )
            next_state, stages = self.transition(x[:, k], u[:, k], preview[0, k])
            equalities.append(x[:, k + 1] - next_state)
            for j in range(stages.shape[1]):
                domain(stages[:, j], preview[0, k])
        decision = ca.vertcat(ca.vec(x), ca.vec(u), ca.vec(slack))
        eq = ca.vertcat(*equalities)
        constraints = ca.vertcat(eq, *inequalities)
        self.nx = 6 * (n + 1)
        self.nu = 2 * n
        self.ne = 2 * (n + 1)
        self.equality_count = eq.numel()
        self.inequality_count = len(lower)
        self.lbg = np.r_[np.zeros(self.equality_count), lower]
        self.ubg = np.r_[np.zeros(self.equality_count), upper]
        xl = np.full((6, n + 1), -np.inf)
        xu = np.full((6, n + 1), np.inf)
        xl[S.VX, :], xu[S.VX, :] = config.minimum_speed, parameters.maximum_speed
        xl[S.S_ABS, :] = 0
        ul = np.tile(
            [[-parameters.maximum_steering_angle], [-parameters.maximum_braking_deceleration]],
            (1, n),
        )
        uu = np.tile(
            [[parameters.maximum_steering_angle], [parameters.maximum_acceleration]], (1, n)
        )
        if self.model.longitudinal_domain is not None:
            # Proportional allocation gives Fx/(mu Fz)=a/(mu g). Box bounds keep
            # every IPOPT trial inside sqrt's domain, not just converged solutions.
            limit = (
                parameters.tire_road_friction_coefficient
                * STANDARD_GRAVITY
                * (1 - LONGITUDINAL_MARGIN)
            )
            ul[1, :] = np.maximum(ul[1, :], -limit)
            uu[1, :] = np.minimum(uu[1, :], limit)
            if parameters.cg_height > 0:
                length = parameters.lf + parameters.lr
                reserve = config.minimum_axle_load * length / parameters.mass
                ul[1, :] = np.maximum(
                    ul[1, :], (reserve - STANDARD_GRAVITY * parameters.lf) / parameters.cg_height
                )
                uu[1, :] = np.minimum(
                    uu[1, :], (STANDARD_GRAVITY * parameters.lr - reserve) / parameters.cg_height
                )
            if np.any(ul > uu):
                raise ValueError("Empty actuator/grip/load domain")
        self.lbx = self.pack(xl, ul, np.zeros((2, n + 1)))
        self.ubx = self.pack(xu, uu, np.full((2, n + 1), np.inf))
        self.nlp = {"x": decision, "p": p, "f": objective, "g": constraints}
        self.evaluate = ca.Function("evaluate_nlp", [decision, p], [objective, constraints])
        self.construction_seconds = perf_counter() - construction_start

    def pack(self, states, controls, slacks):
        return np.r_[
            np.asarray(states).ravel(order="F"),
            np.asarray(controls).ravel(order="F"),
            np.asarray(slacks).ravel(order="F"),
        ]

    def unpack(self, decision):
        z = np.asarray(decision).ravel()
        n = self.config.horizon
        return (
            z[: self.nx].reshape(6, n + 1, order="F"),
            z[self.nx : self.nx + self.nu].reshape(2, n, order="F"),
            z[-self.ne :].reshape(2, n + 1, order="F"),
        )

    def parameter_vector(self, state, previous, preview, terminal_p):
        return np.r_[state, previous, preview.values.ravel(order="F"), terminal_p.ravel(order="F")]

    def cold_start(self, state, previous, preview):
        n = self.config.horizon
        x = np.tile(np.asarray(state)[:, None], (1, n + 1))
        u = np.zeros((2, n))
        last = np.asarray(previous).copy()
        for k in range(n):
            delta = np.clip(
                preview.values[6, k],
                last[0] - self.config.dt * self.config.steering_rate,
                last[0] + self.config.dt * self.config.steering_rate,
            )
            u[:, k] = [
                np.clip(
                    delta,
                    -self.parameters.maximum_steering_angle,
                    self.parameters.maximum_steering_angle,
                ),
                0,
            ]
            next_state, _ = self.transition(x[:, k], u[:, k], preview.values[0, k])
            candidate = np.asarray(next_state).ravel()
            # Initial guesses need not satisfy shooting, but must remain finite/in bounds.
            if np.isfinite(candidate).all() and candidate[S.VX] >= self.config.minimum_speed:
                x[:, k + 1] = candidate
            else:
                x[:, k + 1] = x[:, k]
            last = u[:, k]
        e = np.maximum(
            np.vstack(
                (
                    x[S.E_Y, :] - preview.values[1, :] + self.config.tracker_margin,
                    -x[S.E_Y, :] - preview.values[2, :] + self.config.tracker_margin,
                )
            ),
            0,
        )
        return x, u, e
