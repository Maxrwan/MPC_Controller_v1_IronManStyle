"""Ideal local feedback and explicitly scoped finite products; no hybrid/event model."""

from __future__ import annotations

from .contracts import (
    LATERAL,
    ApplicabilityAudit,
    BudgetToken,
    ClosedLoopAudit,
    ClosedLoopSample,
    DefectAudit,
    F64Matrix,
    F64Vector,
    Linearization,
    MapId,
    MapSemantics,
    NominalSample,
    Outcome,
    OutcomeStatus,
    ProductAudit,
    ProductIntervals,
    Reason,
    Scales,
    ValueFunction,
)


def feedback_matrix(original_gain: F64Vector, *, speed_kp_per_s: float = 1.0) -> F64Matrix:
    import numpy as np

    k = np.asarray(original_gain)
    if k.shape != (4,) or not np.isfinite(k).all() or speed_kp_per_s != 1.0:
        raise ValueError("Original four-state gain and kp=1 required")
    G = np.zeros((2, 6))
    G[0, list(LATERAL)] = k
    G[1, 0] = speed_kp_per_s
    return G


def closed_loop_pair(
    pair: Linearization, original_gain: F64Vector, applicability: ApplicabilityAudit
) -> Outcome[ClosedLoopAudit]:
    try:
        import numpy as np

        if pair.key.map_id not in (MapId.D_TRACKER, MapId.D_PLANT_10):
            raise ValueError("Actual feedback comparison requires a reviewed 10ms map")
        n = pair.A.shape[0]
        if n == 6:
            G = feedback_matrix(original_gain)
            dx = np.array([0.5, 0.5, 1, 0.1, 0.75, 0.1])
            sub = "full"
        elif n == 4:
            G = np.asarray(original_gain).reshape(1, 4)
            dx = np.array([0.1, 0.1, 0.5, 1])
            sub = "lateral"
        elif n == 1:
            G = np.ones((1, 1))
            dx = np.array([0.5])
            sub = "speed"
        else:
            raise ValueError("Unsupported state dimensions")
        acl = pair.A - pair.B @ G
        scaled = acl * dx[None, :] / dx[:, None]
        values, vectors = np.linalg.eig(scaled)
        rho = float(np.max(np.abs(values)))
        residuals = []
        for i, z in enumerate(values):
            raw = float(np.linalg.norm(scaled @ vectors[:, i] - z * vectors[:, i]))
            den = float(max(1.0, np.linalg.norm(scaled)) * np.linalg.norm(vectors[:, i]))
            residuals.append(
                {
                    "name": "eigenvector_" + str(i),
                    "norm_kind": "2",
                    "raw_residual": raw,
                    "denominator": den,
                    "normalized_residual": raw / den,
                    "threshold": None,
                    "comparison": "REPORT_ONLY",
                }
            )
        return Outcome.available(
            {
                "subsystem": sub,
                "Acl_dimensional": acl,
                "Acl_scaled": scaled,
                "original_feedback": G.copy(),
                "eigenvalues": [{"re": float(v.real), "im": float(v.imag)} for v in values],
                "eigenvalue_residuals": residuals,
                "spectral_radius": rho,
                "frozen_classification": "SCHUR_LOCAL_IDEAL"
                if rho < 1 - 1e-8
                else "UNSTABLE_LOCAL_IDEAL"
                if rho > 1 + 1e-8
                else "INDETERMINATE",
                "singular_values": [float(v) for v in np.linalg.svd(scaled, compute_uv=False)],
                "ideal_feedback_applicable": applicability.ideal_unsaturated_immediate_feedback_applicable,
                "applicability_flags": list(applicability.flags),
                "progress_interpretation": "Unregulated frozen-curvature offset; physical progress coupling retained in full A."
                if n == 6
                else "Conditional projected subsystem, omitted couplings remain in full pair.",
                "hybrid_event_map": "UNAVAILABLE_NOT_IMPLEMENTED",
            }
        )
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("CLOSED_LOOP_UNAVAILABLE", str(exc))


def transition_products(
    sequence: tuple[ClosedLoopSample, ...],
    intervals: ProductIntervals,
    scales: Scales,
    budget: BudgetToken,
) -> Outcome[ProductAudit]:
    try:
        import numpy as np

        if not sequence:
            raise ValueError("No covered original factors")
        dx = np.asarray(scales.Dx_diagonal_SI, dtype=float)
        results = []
        if len(dx) != len(sequence[0].Acl):
            raise ValueError("Product normalization shape")
        for range_index, interval in enumerate(intervals.ranges):
            start, end = interval.start_index_inclusive, interval.end_index_exclusive
            if start < 0 or end > len(sequence) or end < start:
                raise ValueError("Requested factors outside supplied support")
            phi = np.eye(len(dx))
            maximum = 1.0
            peak = interval.start_time_s
            completed = start
            missing = []
            logs = []
            for k in range(start, end):
                try:
                    budget.poll()
                except TimeoutError:
                    missing = [
                        {
                            "start_index_inclusive": k,
                            "end_index_exclusive": end,
                            "start_time_s": sequence[k].time_s,
                            "end_time_s": interval.end_time_s,
                        }
                    ]
                    break
                s = sequence[k]
                if s.authority_scope != intervals.authority_scope:
                    raise ValueError("Analytical populations mixed")
                if k > start and abs(sequence[k - 1].next_time_s - s.time_s) > 1e-10:
                    raise ValueError("Discontinuous product chronology")
                if abs(s.next_time_s - s.time_s - 0.01) > 1e-10:
                    raise ValueError("Off-grid interval has no reviewed map")
                phi = s.Acl @ phi
                if not np.isfinite(phi).all():
                    raise ValueError("Product overflow/nonfinite; no favorable replacement")
                normalized = phi * dx[None, :] / dx[:, None]
                norm = float(np.linalg.norm(normalized, 2))
                if norm > maximum:
                    maximum = norm
                    peak = s.next_time_s
                completed = k + 1
            complete = completed == end
            endpoint = (
                float(np.linalg.norm(phi * dx[None, :] / dx[:, None], 2)) if complete else None
            )
            results.append(
                {
                    "requested_range": {
                        "start_index_inclusive": start,
                        "end_index_exclusive": end,
                        "start_time_s": interval.start_time_s,
                        "end_time_s": interval.end_time_s,
                    },
                    "completed_range": {
                        "start_index_inclusive": start,
                        "end_index_exclusive": completed,
                        "start_time_s": interval.start_time_s,
                        "end_time_s": sequence[completed - 1].next_time_s
                        if completed > start
                        else interval.start_time_s,
                    },
                    "missing_ranges": missing,
                    "source_matrix_ids": [s.key.tuple_id for s in sequence[start:completed]],
                    "original_gain_indices": [
                        s.original_gain_index for s in sequence[start:completed]
                    ],
                    "Phi_endpoint": phi.copy() if complete else None,
                    "endpoint_norm": endpoint,
                    "max_transient_norm": maximum,
                    "peak_time_s": peak,
                    "norm_scope": "COMPLETE_REQUESTED_INTERVAL"
                    if complete
                    else "COMPLETED_PREFIX_ONLY",
                    "rescaling_log": logs,
                    "time_varying_stability_guarantee": False,
                    "raw_SI_endpoint_norm": float(np.linalg.norm(phi, 2)) if complete else None,
                }
            )
            if not complete:
                remaining = [
                    {
                        "start_index_inclusive": z.start_index_inclusive,
                        "end_index_exclusive": z.end_index_exclusive,
                        "start_time_s": z.start_time_s,
                        "end_time_s": z.end_time_s,
                    }
                    for z in intervals.ranges[range_index + 1 :]
                ]
                return Outcome(
                    OutcomeStatus.RESOURCE_CENSORED,
                    (
                        Reason(
                            "PRODUCT_CENSORED",
                            "Completed prefixes retained; no requested endpoint backfill",
                        ),
                    ),
                    {
                        "products": results,
                        "authority_scope": intervals.authority_scope,
                        "unstarted_ranges": remaining,
                    },
                )
        return Outcome.available(
            {
                "products": results,
                "authority_scope": intervals.authority_scope,
                "unstarted_ranges": [],
            }
        )
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("PRODUCT_UNAVAILABLE", str(exc))


def nominal_defects(
    sequence: tuple[NominalSample, ...], transition: ValueFunction, semantics: MapSemantics
) -> Outcome[DefectAudit]:
    try:
        from math import pi

        import numpy as np

        dx = np.array([0.5, 0.5, 1, 0.1, 0.75, 0.1])
        records = []
        for sample in sequence:
            if not sample.same_packet_through_endpoint:
                raise ValueError("Packet replacement is a discontinuity, not smooth defect")
            if (
                semantics.dt_s is None
                or abs(sample.next_time_s - sample.time_s - semantics.dt_s) > 1e-10
            ):
                raise ValueError("Mismatched map/reference interval")
            if (
                sample.key.map_id != semantics.map_id
                or sample.key.curvature_policy != semantics.curvature_policy
            ):
                raise ValueError("Mismatched nominal defect semantics")
            value = np.array(transition(sample.x, sample.u), dtype=float, copy=True)
            anchor = float(sample.next_x[3])
            delta = (float(value[3]) - anchor + pi) % (2 * pi) - pi
            if not np.isfinite(value).all() or abs(delta) == pi:
                raise ValueError("Nonfinite or ambiguous nominal defect chart")
            value[3] = anchor + delta
            d = value - np.asarray(sample.next_x)
            records.append(
                {
                    "nominal_x_start": list(sample.x),
                    "nominal_x_next": list(sample.next_x),
                    "nominal_u": list(sample.u),
                    "F_nominal": list(value),
                    "d_dimensional": list(d),
                    "d_scaled": list(d / dx),
                    "forced_response_scaled": None,
                    "matching_map_semantics": True,
                    "discontinuity_flags": [],
                    "interpretation": "Affine reference/map defect, separate from homogeneous feedback. Forced convolution requires matching Phi records.",
                }
            )
        return Outcome.available({"defects": records})
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("NOMINAL_DEFECT_UNAVAILABLE", str(exc))


def _forced_step(previous, acl, defect, dx):
    """Exact affine convolution recursion e[k+1]=Acl[k]e[k]+d[k], returned scaled."""
    import numpy as np

    scale = np.asarray(dx)
    return (np.asarray(acl) @ np.asarray(previous) + np.asarray(defect)) / scale


# CT-L2B fixed metadata-only panel; supersedes exhaustive interval enumeration.
_PRODUCT_WINDOW_STEPS = (1, 5, 10, 20, 40)
_PRODUCT_PANEL_MAX_FACTORS = 80
_PRODUCT_PANEL_MAX_INTERVALS = 16
_PRODUCT_NORMALIZATION_IDS = (
    "nominal_scaled",
    "raw_SI_unit_dependent",
    "selected_coordinate_x0.1",
    "selected_coordinate_x10",
)
_PRODUCT_SENSITIVITY_COORDINATE = {"full": "e_y", "lateral": "e_y", "speed": "vx"}


def _product_selection(sequence, candidate_id, authority_scope):
    """Select from metadata, never matrices/growth; full scan is retained first.

    Full [0,N), then lengths 1/5/10/20/40 in this order. For each available
    length L, select starts 0, (N-L)//2, N-L, in that order. Deduplicate by
    first occurrence. Lengths exceeding N are omitted, never shortened.
    Each selected product scans all its prefixes and reports the actual maximum.
    This is not exhaustive enumeration of arbitrary start/end intervals.
    """
    from .contracts import IndexInterval

    if not candidate_id or authority_scope not in ("DESIGN_CONDITIONAL", "OBSERVED_AUTHORITY"):
        raise ValueError("Explicit candidate and one reviewed authority population required")
    n = len(sequence)
    if n > _PRODUCT_PANEL_MAX_FACTORS:
        raise ValueError("Product panel exceeds the reviewed 80-slot population bound")
    for i, sample in enumerate(sequence):
        if sample.authority_scope != authority_scope:
            raise ValueError("No cross-population substitution")
        if abs(sample.next_time_s - sample.time_s - 0.01) > 1e-10:
            raise ValueError("No approximate off-grid factor in bounded selection")
        if i and (
            sample.original_gain_index != sequence[i - 1].original_gain_index + 1
            or abs(sequence[i - 1].next_time_s - sample.time_s) > 1e-10
        ):
            raise ValueError("Selection requires one original contiguous gain-grid population")
    pairs = []

    def add(start, end):
        if (start, end) not in pairs:
            pairs.append((start, end))

    if n:
        add(0, n)
        for length in _PRODUCT_WINDOW_STEPS:
            if length <= n:
                for start in (0, (n - length) // 2, n - length):
                    add(start, start + length)
    if len(pairs) > _PRODUCT_PANEL_MAX_INTERVALS:
        raise ValueError("Bounded panel implementation exceeds its declared interval cap")
    intervals = tuple(
        IndexInterval(start, end, sequence[start].time_s, sequence[end - 1].next_time_s)
        for start, end in pairs
    )
    exhaustive = n * (n + 1) // 2
    return {
        "rule_id": "ct1l-l2b-full-first-three-anchors-v1",
        "candidate_id": candidate_id,
        "authority_scope": authority_scope,
        "factor_count": n,
        "intervals": intervals,
        "selected_interval_count": len(intervals),
        "exhaustive_nonempty_interval_count": exhaustive,
        "omitted_interval_count": exhaustive - len(intervals),
        "unavailable_window_lengths_steps": [
            length for length in _PRODUCT_WINDOW_STEPS if length > n
        ],
        "full_interval_prefixes_scanned_if_complete": n,
        "exhaustive_stability_verification": False,
    }


def _product_normalizations(subsystem_pair, nominal_scales):
    """Four fixed populations; existing Dx and definitions are unchanged.

    The two sensitivity cases probe e_y for full/lateral and vx for scalar speed.
    Other coordinate sensitivities are explicitly omitted by CT-L2B, not retuned.
    """
    import numpy as np

    from .contracts import Scales

    coordinate = _PRODUCT_SENSITIVITY_COORDINATE[subsystem_pair.subsystem]
    index = subsystem_pair.state_names.index(coordinate)
    base = nominal_scales.Dx_diagonal_SI
    low, high = base.copy(), base.copy()
    low[index] *= 0.1
    high[index] *= 10.0
    values = (base, np.ones(len(base)), low, high)
    return tuple(
        (name, Scales(dx, nominal_scales.Du_diagonal_SI))
        for name, dx in zip(_PRODUCT_NORMALIZATION_IDS, values, strict=True)
    )
