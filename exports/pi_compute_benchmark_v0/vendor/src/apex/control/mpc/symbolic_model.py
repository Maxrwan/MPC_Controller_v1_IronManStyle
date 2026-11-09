"""Independent CasADi transcription of Task 004; never the physical plant."""

import casadi as ca

from apex.models.constants import STANDARD_GRAVITY
from apex.models.tire.config import TirePhysics
from apex.models.vehicle.parameters import VehicleParameters
from apex.state import ControlIndex as U
from apex.state import StateIndex as S


class SymbolicBicycle:
    def __init__(self, parameters: VehicleParameters, tire_physics=TirePhysics()):
        parameters.validate_for_dynamic()
        self.parameters = p = parameters
        self.tire_physics = tire_physics
        x, u, curvature = ca.SX.sym("x", 6), ca.SX.sym("u", 2), ca.SX.sym("kappa")
        vx, vy, r = x[S.VX], x[S.VY], x[S.YAW_RATE]
        delta, acceleration = u[U.DELTA], u[U.A_CMD]
        length = p.lf + p.lr
        fzf0 = p.mass * STANDARD_GRAVITY * p.lr / length
        fzr0 = p.mass * STANDARD_GRAVITY * p.lf / length
        transfer = p.mass * acceleration * p.cg_height / length
        fzf, fzr = fzf0 - transfer, fzr0 + transfer
        alpha_f = delta - ca.atan2(vy + p.lf * r, vx)
        alpha_r = -ca.atan2(vy - p.lr * r, vx)
        fyf = p.front_cornering_stiffness * fzf / fzf0 * alpha_f
        fyr = p.rear_cornering_stiffness * fzr / fzr0 * alpha_r
        mu = p.tire_road_friction_coefficient
        fx = p.mass * acceleration
        fxf, fxr = fx * fzf / (fzf + fzr), fx * fzr / (fzf + fzr)
        self.longitudinal_domain = None
        if tire_physics.model == "smooth_combined_grip":
            if mu is None or mu <= 0:
                raise ValueError("Grip prediction requires configured mu > 0")
            capf = ca.sqrt((mu * fzf) ** 2 - fxf**2)
            capr = ca.sqrt((mu * fzr) ** 2 - fxr**2)
            fyf = capf * ca.tanh(fyf / capf)
            fyr = capr * ca.tanh(fyr / capr)
            q = ca.vertcat(fxf / (mu * fzf), fxr / (mu * fzr))
            self.longitudinal_domain = ca.Function("longitudinal_domain", [u], [q])
        if mu is not None and tire_physics.longitudinal_allocation is not None:
            utilization = ca.vertcat(
                ca.sqrt(fxf**2 + fyf**2) / (mu * fzf), ca.sqrt(fxr**2 + fyr**2) / (mu * fzr)
            )
            self.tire_diagnostics = ca.Function(
                "tire_diagnostics", [x, u], [ca.vertcat(fxf, fxr, fyf, fyr), utilization]
            )
        denominator = 1 - curvature * x[S.E_Y]
        progress_rate = (vx * ca.cos(x[S.E_PSI]) - vy * ca.sin(x[S.E_PSI])) / denominator
        dx = ca.vertcat(
            acceleration + r * vy,
            (fyf + fyr) / p.mass - r * vx,
            (p.lf * fyf - p.lr * fyr) / p.yaw_inertia,
            r - curvature * progress_rate,
            progress_rate,
            vx * ca.sin(x[S.E_PSI]) + vy * ca.cos(x[S.E_PSI]),
        )
        self.derivative = ca.Function("bicycle_derivative", [x, u, curvature], [dx])
        self.loads = ca.Function("axle_loads", [u], [ca.vertcat(fzf, fzr)])
        self.domain = ca.Function("state_domain", [x, curvature], [ca.vertcat(vx, denominator)])

    def rk4(self, dt: float = 0.05, substeps: int = 5):
        """Return a map and all four evaluation states per internal RK4 step.

        Curvature is an exogenous constant within each shooting interval. Heading
        stays locally unwrapped inside the NLP to preserve smooth derivatives.
        """
        if dt <= 0 or substeps < 1 or not isinstance(substeps, int):
            raise ValueError("Positive dt and integer substeps required")
        x, u, k = ca.SX.sym("x", 6), ca.SX.sym("u", 2), ca.SX.sym("k")
        z, stages, h = x, [], dt / substeps
        for _ in range(substeps):
            a = self.derivative(z, u, k)
            b_state = z + h * a / 2
            b = self.derivative(b_state, u, k)
            c_state = z + h * b / 2
            c = self.derivative(c_state, u, k)
            d_state = z + h * c
            d = self.derivative(d_state, u, k)
            stages.extend([z, b_state, c_state, d_state])
            z = z + h * (a + 2 * b + 2 * c + d) / 6
        return ca.Function("rk4_prediction", [x, u, k], [z, ca.horzcat(*stages)])
