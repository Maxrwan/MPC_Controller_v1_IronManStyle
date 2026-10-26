"""Classical RK4 value/tangent composition, retaining every physical stage."""

from __future__ import annotations

from .contracts import (
    CurvaturePolicy,
    EvaluationKey,
    F64Vector,
    Linearization,
    MapId,
    Method,
    OperatingTuple,
    Outcome,
    PairFunction,
    StageGuard,
    StepJet,
    ValueFunction,
)


def rk4_tangent(
    x: F64Vector, u: F64Vector, *, h_s: float, f: ValueFunction, df: PairFunction
) -> Outcome[StepJet]:
    try:
        import numpy as np

        if h_s <= 0:
            raise ValueError("Positive RK4 step required")
        x, u = np.array(x, dtype=float, copy=True), np.array(u, dtype=float, copy=True)
        nx, nu = len(x), len(u)
        identity = np.eye(nx)
        zero = np.zeros((nx, nu))
        h = h_s

        def stage(z, X, U):
            a, b = df(z, u)
            return np.asarray(f(z, u)), a @ X, a @ U + b

        k1, x1, u1 = stage(x, identity, zero)
        z2 = x + h * k1 / 2
        k2, x2, u2 = stage(z2, identity + h * x1 / 2, h * u1 / 2)
        z3 = x + h * k2 / 2
        k3, x3, u3 = stage(z3, identity + h * x2 / 2, h * u2 / 2)
        z4 = x + h * k3
        k4, x4, u4 = stage(z4, identity + h * x3, h * u3)
        value = x + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        A = identity + h * (x1 + 2 * x2 + 2 * x3 + x4) / 6
        B = h * (u1 + 2 * u2 + 2 * u3 + u4) / 6
        if not all(np.isfinite(z).all() for z in (value, A, B)):
            raise ValueError("Nonfinite tangent")
        return Outcome.available(StepJet(value, A, B, (x, z2, z3, z4, value)))
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("RK4_TANGENT_FAILURE", str(exc))


def compose_rk4(
    point: OperatingTuple,
    *,
    dt_s: float,
    substeps: int,
    f: ValueFunction,
    df: PairFunction,
    stage_guard: StageGuard,
) -> Outcome[Linearization]:
    try:
        import numpy as np

        if dt_s <= 0 or not isinstance(substeps, int) or substeps < 1:
            raise ValueError("Invalid substeps")
        z = np.array(point.x, dtype=float)
        X = np.eye(len(z))
        U = np.zeros((len(z), len(point.u)))
        for _ in range(substeps):
            step = rk4_tangent(z, point.u, h_s=dt_s / substeps, f=f, df=df).unwrap()
            for state in step.stages:
                stage_guard(state, point.u).unwrap()
            U = step.Jx @ U + step.Ju
            X = step.Jx @ X
            z = step.value
        physical = point.kappa_policy == CurvaturePolicy.GEOMETRY_PROGRESS
        mid = (
            (MapId.D_PLANT_10 if dt_s == 0.01 else MapId.D_PLANT_100)
            if physical
            else (MapId.D_TRACKER if dt_s == 0.01 else MapId.D_NMPC)
        )
        if (
            (dt_s, substeps) not in ((0.01, 2), (0.1, 4), (0.1, 20))
            or (physical and (dt_s, substeps) == (0.1, 4))
            or (not physical and (dt_s, substeps) == (0.1, 20))
        ):
            raise ValueError("Unsupported six-map schedule")
        key = EvaluationKey(
            point.candidate_id,
            point.tuple_id,
            mid,
            point.kappa_policy,
            "",
            point.gain_index,
            physical_interval=(point.time_s, point.time_s + dt_s),
        )
        return Outcome.available(Linearization(key, X, U, method=Method.RK4_TANGENT))
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("RK4_COMPOSITION_UNAVAILABLE", str(exc))
