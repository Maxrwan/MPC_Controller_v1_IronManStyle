"""Manual accepted-equation derivatives. This cross-check is never the scientific plant."""

from __future__ import annotations

from .contracts import (
    CurvaturePolicy,
    EvaluationKey,
    F64Vector,
    ForcePartials,
    FrozenParameters,
    GeometryJet,
    Linearization,
    MapId,
    Method,
    OperatingTuple,
    Outcome,
)


def force_load_partials(
    x: F64Vector, u: F64Vector, parameters: FrozenParameters
) -> Outcome[ForcePartials]:
    try:
        import numpy as np

        p = parameters
        v, w, r = map(float, x[:3])
        delta, a = map(float, u)
        if (
            not np.isfinite(x).all()
            or not np.isfinite(u).all()
            or v < 0.5 - 1e-10
            or v > 6 + 1e-10
            or abs(delta) > 0.4
            or not -3 <= a <= 2
        ):
            raise ValueError("Accepted input/speed domain")
        m, lf, lr, h, mu = p.mass, p.lf, p.lr, p.cg_height, p.tire_road_friction_coefficient
        length = lf + lr
        g = 9.81
        z0 = np.array([m * g * lr / length, m * g * lf / length])
        dz = np.array([-m * h / length, m * h / length])
        z = z0 + dz * a
        if not np.all(z > 1e-9):
            raise ValueError("Axle unloading")
        xx = m * a * z / z.sum()
        if np.any(np.abs(xx) > (1 - 1e-6) * mu * z):
            raise ValueError("Hard longitudinal reserve")
        dx = m * z / z.sum() + m * a * dz / z.sum()
        q = np.array([w + lf * r, w - lr * r])
        alpha = np.array([delta - np.arctan2(q[0], v), -np.arctan2(q[1], v)])
        da_x = np.zeros((2, 6))
        da_u = np.zeros((2, 2))
        da_u[0, 0] = 1
        da_x[:, 0] = q / (v * v + q * q)
        da_x[:, 1] = -v / (v * v + q * q)
        da_x[:, 2] = np.array([-lf * v, lr * v]) / (v * v + q * q)
        stiffness = np.array([p.front_cornering_stiffness, p.rear_cornering_stiffness])
        ce = stiffness * z / z0
        dce = stiffness * dz / z0
        rad = (mu * z) ** 2 - xx**2
        if not np.all(rad > 0):
            raise ValueError("Nonpositive tire capacity")
        cap = np.sqrt(rad)
        dcap = (mu * mu * z * dz - xx * dx) / cap
        slip = ce * alpha / cap
        th = np.tanh(slip)
        slope = 1 - th * th
        fy = cap * th
        fx = slope[:, None] * ce[:, None] * da_x
        fu = slope[:, None] * ce[:, None] * da_u
        fu[:, 1] = slope * alpha * dce + (th - slip * slope) * dcap
        loads = np.zeros((2, 2))
        loads[:, 1] = dz
        return Outcome.available(
            ForcePartials(tuple(fy), tuple(z), tuple(alpha), fx, fu, loads, tuple(rad))
        )
    except (ValueError, ArithmeticError, AttributeError) as exc:
        return Outcome.unavailable("ANALYTIC_DOMAIN", str(exc))


def continuous_pair(
    point: OperatingTuple,
    parameters: FrozenParameters,
    geometry: GeometryJet | None,
    *,
    policy: CurvaturePolicy,
) -> Outcome[Linearization]:
    try:
        import numpy as np

        if geometry is None:
            raise ValueError("Explicit matching curvature jet required")
        k = geometry.kappa_1pm
        ks = 0.0 if policy == CurvaturePolicy.FROZEN_EXOGENOUS else geometry.kappa_s_1pm2
        if ks is None:
            raise ValueError("Unresolved physical curvature derivative")
        x = np.asarray(point.x, dtype=float)
        v, w, r, theta, s, y = x
        p = parameters
        forces = force_load_partials(x, point.u, p).unwrap()
        df, dg = forces.force_state_partials, forces.force_input_partials
        D = 1 - k * y
        if D <= 0.001:
            raise ValueError("Invalid Frenet denominator")
        n = v * np.cos(theta) - w * np.sin(theta)
        b = v * np.sin(theta) + w * np.cos(theta)
        progress = n / D
        dp = np.array(
            [np.cos(theta) / D, -np.sin(theta) / D, 0.0, -b / D, n * y * ks / D**2, n * k / D**2]
        )
        A = np.zeros((6, 6))
        B = np.zeros((6, 2))
        A[0, 1] = r
        A[0, 2] = w
        B[0, 1] = 1
        A[1, :] = (df[0] + df[1]) / p.mass
        A[1, 0] -= r
        A[1, 2] -= v
        A[2, :] = (p.lf * df[0] - p.lr * df[1]) / p.yaw_inertia
        B[1, :] = (dg[0] + dg[1]) / p.mass
        B[2, :] = (p.lf * dg[0] - p.lr * dg[1]) / p.yaw_inertia
        A[3, :] = -k * dp
        A[3, 2] += 1
        A[3, 4] -= ks * progress
        A[4, :] = dp
        A[5, :] = [np.sin(theta), np.cos(theta), 0, n, 0, 0]
        mid = MapId.C_FIXED if policy == CurvaturePolicy.FROZEN_EXOGENOUS else MapId.C_PHYSICAL
        key = EvaluationKey(
            point.candidate_id,
            point.tuple_id,
            mid,
            policy,
            p.source_binding_set_sha256,
            point.gain_index,
            geometry.branch,
            (point.time_s, point.time_s),
        )
        return Outcome.available(Linearization(key, A, B, method=Method.ANALYTIC))
    except (ValueError, ArithmeticError, AttributeError) as exc:
        return Outcome.unavailable("ANALYTIC_PAIR_UNAVAILABLE", str(exc))
