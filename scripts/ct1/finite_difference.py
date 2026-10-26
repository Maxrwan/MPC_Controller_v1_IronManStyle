"""Predeclared independent real finite differences; never shrink a failed stencil."""

from __future__ import annotations

from typing import Callable

from .contracts import (
    MAPS,
    ComparisonAudit,
    DerivativeCriteria,
    EvaluationKey,
    FDPair,
    FDSteps,
    GeometryCriteria,
    GeometryJet,
    Linearization,
    MapId,
    Method,
    OperatingTuple,
    Outcome,
    Scales,
    StencilGuard,
    ValueFunction,
)


def central_pair(
    point: OperatingTuple,
    function: ValueFunction,
    map_id: MapId,
    scales: Scales,
    steps: FDSteps,
    guard: StencilGuard,
) -> Outcome[FDPair]:
    try:
        import numpy as np

        if tuple(steps.multipliers) != (2e-5, 1e-5, 5e-6):
            raise ValueError("Unreviewed FD steps")
        mid = MapId(map_id)
        stencil = guard(point, mid, steps).unwrap()
        if not stencil.central_available:
            return Outcome.unavailable(
                "CENTRAL_STENCIL_UNAVAILABLE", "No unrestricted central domain"
            )
        x, u = np.array(point.x, dtype=float), np.array(point.u, dtype=float)
        pairs = []
        for mult in steps.multipliers:
            columns = []
            for j, scale in enumerate(tuple(steps.state_scales_SI) + tuple(steps.input_scales_SI)):
                h = mult * scale
                if h <= 0:
                    raise ValueError("Nonpositive diagnostic scale")
                xp, xm, up, um = x.copy(), x.copy(), u.copy(), u.copy()
                if j < len(x):
                    xp[j] += h
                    xm[j] -= h
                else:
                    up[j - len(x)] += h
                    um[j - len(x)] -= h
                yp, ym = np.asarray(function(xp, up)), np.asarray(function(xm, um))
                if yp.shape != x.shape or ym.shape != x.shape:
                    raise ValueError("FD value shape")
                columns.append((yp - ym) / (2 * h))
            J = np.column_stack(columns)
            if not np.isfinite(J).all():
                raise ValueError("Nonfinite independent FD")
            key = EvaluationKey(
                point.candidate_id,
                point.tuple_id,
                mid,
                point.kappa_policy,
                "",
                point.gain_index,
                stencil.branch,
                (point.time_s, point.time_s + (MAPS[mid][0] or 0)),
            )
            pairs.append(
                Linearization(key, J[:, : len(x)], J[:, len(x) :], method=Method.INDEPENDENT_FD)
            )
        return Outcome.available(FDPair(tuple(pairs), steps, stencil))
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("FD_UNAVAILABLE", str(exc))


def compare_pairs(
    reference: Linearization, independent: FDPair, criteria: DerivativeCriteria
) -> ComparisonAudit:
    import numpy as np

    required = (
        "candidate_id",
        "tuple_id",
        "map_id",
        "curvature_policy",
        "physical_interval",
        "gain_index",
        "source_binding_set_sha256",
    )
    if any(
        any(getattr(reference.key, n) != getattr(p.key, n) for n in required)
        for p in independent.pairs_per_step
    ):
        return {
            "comparison": "INCOMPARABLE_METHOD_SEMANTICS",
            "reasons": ["Different tuple/map/curvature/interval"],
            "entry_errors_per_step": [],
        }
    if criteria["entry_absolute_tolerance"] != 1e-7 or criteria["entry_relative_tolerance"] != 1e-4:
        raise ValueError("Changed derivative criteria")
    dx = np.asarray(independent.steps.state_scales_SI)
    du = np.asarray(independent.steps.input_scales_SI)
    cols = np.r_[dx, du]

    def normalized(p):
        return np.hstack((p.A, p.B)) * cols[None, :] / dx[:, None]

    J = normalized(reference)
    estimates = [normalized(p) for p in independent.pairs_per_step]
    errors = []
    ok = True
    relative = []
    for D in estimates:
        error = np.abs(J - D)
        den = np.maximum(np.abs(J), np.abs(D))
        errors.append(error)
        ok = ok and bool(np.all(error <= 1e-7 + 1e-4 * den))
        relative.append(np.divide(error, den, out=np.zeros_like(error), where=den != 0))
    a, b = estimates[-2:]
    agree = bool(np.all(np.abs(a - b) <= 1e-7 + 1e-4 * np.maximum(np.abs(a), np.abs(b))))
    return {
        "comparison": "PASS" if ok and agree else "FAIL",
        "entry_errors_per_step": errors,
        "max_abs_error": max(float(e.max()) for e in errors),
        "max_relative_error": max(float(e.max()) for e in relative),
        "two_smallest_step_agreement": agree,
        "column_steps": list(independent.steps.multipliers),
        "invalid_columns": [],
    }


def crosscheck_curvature_derivative(
    jet: GeometryJet, geometry_value: Callable[[float], float], criteria: GeometryCriteria
) -> Outcome[ComparisonAudit]:
    try:
        if jet.kappa_s_1pm2 is None or jet.branch.side != "SMOOTH":
            raise ValueError("No two-sided smooth curvature jet")
        if (
            tuple(criteria["s_steps_m"]) != (2e-5, 1e-5, 5e-6)
            or criteria["absolute_tolerance_1pm2"] != 1e-5
            or criteria["relative_tolerance"] != 1e-3
        ):
            raise ValueError("Changed geometry criteria")
        estimates = [
            (geometry_value(jet.s_abs_m + h) - geometry_value(jet.s_abs_m - h)) / (2 * h)
            for h in criteria["s_steps_m"]
        ]
        errors = [abs(jet.kappa_s_1pm2 - v) for v in estimates]
        ok = all(
            e <= 1e-5 + 1e-3 * max(abs(jet.kappa_s_1pm2), abs(v)) for e, v in zip(errors, estimates)
        )
        ok = ok and abs(estimates[-1] - estimates[-2]) <= 1e-5 + 1e-3 * max(
            abs(estimates[-1]), abs(estimates[-2])
        )
        return Outcome.available(
            {
                "comparison": "PASS" if ok else "FAIL",
                "estimates": estimates,
                "absolute_errors": errors,
            }
        )
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("CURVATURE_FD_UNAVAILABLE", str(exc))
