"""Independent VALUE transcription. No analytical/tangent/CasADi implementation imported."""

from __future__ import annotations

from typing import Callable

from .contracts import F64Vector, FrozenParameters, MapValue


def crosscheck_f(
    x: F64Vector, u: F64Vector, parameters: FrozenParameters, *, curvature: float
) -> F64Vector:
    import numpy as np

    x = np.array(x, dtype=float, copy=True)
    u = np.array(u, dtype=float, copy=True)
    p = parameters
    vx, vy, r, epsi, progress, ey = x
    steer, acc = u
    if (
        not np.isfinite(x).all()
        or not np.isfinite(u).all()
        or progress < 0
        or vx < 0.5 - 1e-10
        or vx > 6 + 1e-10
        or abs(steer) > 0.4
        or not -3 <= acc <= 2
    ):
        raise ValueError("Independent source-domain rejection")
    wheelbase = p.lf + p.lr
    front0 = p.mass * 9.81 * p.lr / wheelbase
    rear0 = p.mass * 9.81 * p.lf / wheelbase
    transfer = p.mass * acc * p.cg_height / wheelbase
    front, rear = front0 - transfer, rear0 + transfer
    if min(front, rear) <= 1e-9:
        raise ValueError("Invalid loads")
    ff = p.mass * acc * front / (front + rear)
    fr = p.mass * acc * rear / (front + rear)
    mu = p.tire_road_friction_coefficient
    if abs(ff) > (1 - 1e-6) * mu * front or abs(fr) > (1 - 1e-6) * mu * rear:
        raise ValueError("Longitudinal tire domain")
    sf = steer - np.arctan2(vy + p.lf * r, vx)
    sr = -np.arctan2(vy - p.lr * r, vx)
    cf = np.sqrt((mu * front) ** 2 - ff**2)
    cr = np.sqrt((mu * rear) ** 2 - fr**2)
    yf = cf * np.tanh((p.front_cornering_stiffness * front / front0) * sf / cf)
    yr = cr * np.tanh((p.rear_cornering_stiffness * rear / rear0) * sr / cr)
    den = 1 - curvature * ey
    if den <= 0.001:
        raise ValueError("Independent Frenet rejection")
    ds = (vx * np.cos(epsi) - vy * np.sin(epsi)) / den
    return np.array(
        [
            acc + r * vy,
            (yf + yr) / p.mass - r * vx,
            (p.lf * yf - p.lr * yr) / p.yaw_inertia,
            r - curvature * ds,
            ds,
            vx * np.sin(epsi) + vy * np.cos(epsi),
        ]
    )


def crosscheck_rk4(
    x: F64Vector,
    u: F64Vector,
    parameters: FrozenParameters,
    *,
    dt_s: float,
    substeps: int,
    curvature: float | None,
    geometry_value: Callable[[float], float] | None,
) -> MapValue:
    import numpy as np

    if dt_s <= 0 or not isinstance(substeps, int) or substeps < 1:
        raise ValueError("Invalid integration contract")
    if (curvature is None) == (geometry_value is None):
        raise ValueError("Choose one explicit curvature policy")
    z = np.array(x, dtype=float, copy=True)
    stages = []
    h = dt_s / substeps

    def value(q):
        k = curvature if geometry_value is None else float(geometry_value(float(q[4])))
        return crosscheck_f(q, u, parameters, curvature=k)

    for _ in range(substeps):
        a = value(z)
        xb = z + h * a / 2
        b = value(xb)
        xc = z + h * b / 2
        c = value(xc)
        xd = z + h * c
        d = value(xd)
        stages.extend((z.copy(), xb.copy(), xc.copy(), xd.copy()))
        z = z + h * (a + 2 * b + 2 * c + d) / 6
        value(z)
        stages.append(z.copy())
    return MapValue(z, tuple(stages))
