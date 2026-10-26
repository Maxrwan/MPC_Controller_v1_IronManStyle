"""Local dimensional/scaled controllability and conservative PBH numerical audits."""

from __future__ import annotations

from typing import Literal

from .contracts import (
    LATERAL,
    ControllabilityAudit,
    Linearization,
    MapId,
    NormalizedPair,
    Outcome,
    PBHAudit,
    PBHCriteria,
    RankCriteria,
    Scales,
    SubsystemPair,
)


def extract_subsystem(
    pair: Linearization, subsystem: Literal["full", "lateral", "speed"]
) -> SubsystemPair:
    import numpy as np

    if subsystem == "full":
        ix = list(range(6))
        ju = [0, 1]
    elif subsystem == "lateral":
        ix = list(LATERAL)
        ju = [0]
    elif subsystem == "speed":
        ix = [0]
        ju = [1]
    else:
        raise ValueError("Unknown subsystem")
    omitted = [j for j in range(6) if j not in ix]
    other_u = [j for j in range(2) if j not in ju]
    blocks = (pair.A[np.ix_(ix, omitted)], pair.B[np.ix_(ix, other_u)])
    return SubsystemPair(
        pair.key,
        subsystem,
        pair.A[np.ix_(ix, ix)],
        pair.B[np.ix_(ix, ju)],
        tuple(pair.state_names[j] for j in ix),
        tuple(pair.input_names[j] for j in ju),
        blocks,
    )


def _default_scales(pair):
    import numpy as np

    if pair.parent_key.candidate_id == "TOY":
        return Scales(
            np.ones(pair.A.shape[0]),
            np.ones(pair.B.shape[1]),
            1.0,
            pair.state_names,
            pair.input_names,
        )
    if pair.subsystem == "full":
        dx = [0.5, 0.5, 1, 0.1, 0.75, 0.1]
        du = [0.2, 1]
    elif pair.subsystem == "lateral":
        dx = [0.1, 0.1, 0.5, 1]
        du = [0.2]
    else:
        dx = [0.5]
        du = [1]
    return Scales(np.array(dx), np.array(du), 1.0, pair.state_names, pair.input_names)


def normalize_pair(pair: SubsystemPair, scales: Scales, *, tau_s: float = 1.0) -> NormalizedPair:
    import numpy as np

    dx, du = np.asarray(scales.Dx_diagonal_SI), np.asarray(scales.Du_diagonal_SI)
    if (
        dx.shape != (pair.A.shape[0],)
        or du.shape != (pair.B.shape[1],)
        or pair.A.shape != (len(dx), len(dx))
        or pair.B.shape[0] != len(dx)
    ):
        raise ValueError("Normalization dimensions mismatch")
    if (
        not np.isfinite(dx).all()
        or not np.isfinite(du).all()
        or np.any(dx <= 0)
        or np.any(du <= 0)
        or not np.isfinite(tau_s)
        or tau_s <= 0
    ):
        raise ValueError("Invalid positive scales")
    continuous = pair.parent_key.map_id in (MapId.C_FIXED, MapId.C_PHYSICAL)
    factor = tau_s if continuous else 1.0
    return NormalizedPair(
        pair,
        factor * pair.A * dx[None, :] / dx[:, None],
        factor * pair.B * du[None, :] / dx[:, None],
        Scales(dx, du, tau_s, pair.state_names, pair.input_names),
    )


def _C(a, b):
    import numpy as np

    blocks = []
    block = b.copy()
    for _ in range(a.shape[0]):
        blocks.append(block)
        block = a @ block
    return np.hstack(blocks)


def _spectrum(matrix, tolerance):
    import numpy as np

    s = np.linalg.svd(matrix, compute_uv=False)
    threshold = max(1e-12, tolerance * float(s[0]) if len(s) else 0.0)
    rank = int(np.count_nonzero(s > threshold))
    full = rank == matrix.shape[0]
    return {
        "singular_values": [float(x) for x in s],
        "relative_tolerance": tolerance,
        "absolute_floor": 1e-12,
        "threshold": threshold,
        "rank": rank,
        "condition_number": float(s[0] / s[-1]) if full and len(s) and s[-1] > 0 else None,
        "condition_kind": "FINITE" if full else "INFINITE_RANK_DEFICIENT",
    }


def controllability_audit(
    pair: SubsystemPair, criteria: RankCriteria
) -> Outcome[ControllabilityAudit]:
    try:
        import numpy as np

        if (
            tuple(criteria["relative_tolerances"]) != (1e-12, 1e-10, 1e-8, 1e-6)
            or criteria["absolute_floor"] != 1e-12
        ):
            raise ValueError("Changed rank criteria")
        scales = _default_scales(pair)
        cases = []
        nominal = normalize_pair(pair, scales)
        variants = [
            (
                "raw_SI_unit_dependent",
                Scales(np.ones(len(scales.Dx_diagonal_SI)), np.ones(len(scales.Du_diagonal_SI))),
                1.0,
            ),
            ("nominal", scales, 1.0),
        ]
        for target, n in [("x", len(scales.Dx_diagonal_SI)), ("u", len(scales.Du_diagonal_SI))]:
            for j in range(n):
                for factor in (0.1, 10.0):
                    dx, du = scales.Dx_diagonal_SI.copy(), scales.Du_diagonal_SI.copy()
                    (dx if target == "x" else du)[j] *= factor
                    variants.append((f"{target}{j}x{factor}", Scales(dx, du), 1.0))
        if pair.parent_key.map_id in (MapId.C_FIXED, MapId.C_PHYSICAL):
            variants.extend((("tau0.1", scales, 0.1), ("tau10", scales, 10.0)))
        for name, sc, tau in variants:
            norm = normalize_pair(pair, sc, tau_s=tau)
            C = _C(norm.A_scaled, norm.B_scaled)
            for tol in criteria["relative_tolerances"]:
                cases.append(
                    {
                        "case_id": name,
                        "Dx": list(sc.Dx_diagonal_SI),
                        "Du": list(sc.Du_diagonal_SI),
                        "tau_s": tau,
                        "spectrum": _spectrum(C, tol),
                    }
                )
        return Outcome.available(
            {
                "dimensional_pair": pair,
                "normalized_pair": nominal,
                "C_dimensional": _C(pair.A, pair.B),
                "C_scaled": _C(nominal.A_scaled, nominal.B_scaled),
                "scale_cases": cases,
                "reasons": [],
            }
        )
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("CONTROLLABILITY_NUMERICAL_FAILURE", str(exc))


def stabilizability_audit(pair: SubsystemPair, criteria: PBHCriteria) -> Outcome[PBHAudit]:
    try:
        import numpy as np
        from scipy.linalg import schur

        norm = normalize_pair(pair, _default_scales(pair))
        a, b = norm.A_scaled, norm.B_scaled
        if criteria["include_boundary_band"] != 1e-8:
            raise ValueError("Changed PBH boundary band")
        continuous = pair.parent_key.map_id in (MapId.C_FIXED, MapId.C_PHYSICAL)
        vals, vec = np.linalg.eig(a)
        tri, unitary = schur(a, output="complex")
        schur_res = float(np.linalg.norm(a @ unitary - unitary @ tri) / max(1.0, np.linalg.norm(a)))
        modes = []
        failed = False
        ambiguous = False
        for j, lam in enumerate(vals):
            boundary = abs(lam.real) if continuous else abs(abs(lam) - 1)
            required = lam.real >= 0 if continuous else abs(lam) >= 1
            band = boundary <= 1e-8
            matrix = np.hstack((lam * np.eye(len(a)) - a, b))
            spectra = [_spectrum(matrix, t) for t in (1e-12, 1e-10, 1e-8, 1e-6)]
            ranks = {s["rank"] for s in spectra}
            full = min(ranks) == len(a)
            residual = float(
                np.linalg.norm(a @ vec[:, j] - lam * vec[:, j])
                / (max(1.0, np.linalg.norm(a)) * np.linalg.norm(vec[:, j]))
            )
            repeated = any(i != j and abs(lam - v) <= 1e-8 for i, v in enumerate(vals))
            unresolved = band or len(ranks) > 1 or repeated
            if unresolved:
                classification = "INDETERMINATE"
                ambiguous = True
            elif full:
                classification = "CONTROLLABLE_MODE"
            elif required:
                classification = "UNCONTROLLABLE_UNSTABLE_OR_MARGINAL"
                failed = True
            else:
                classification = "UNCONTROLLABLE_STABLE"
            modes.append(
                {
                    "eigenvalue": {"re": float(lam.real), "im": float(lam.imag)},
                    "eigenvalue_residual": {
                        "name": "eigenvector",
                        "norm_kind": "2",
                        "raw_residual": float(np.linalg.norm(a @ vec[:, j] - lam * vec[:, j])),
                        "denominator": float(
                            max(1.0, np.linalg.norm(a)) * np.linalg.norm(vec[:, j])
                        ),
                        "normalized_residual": residual,
                        "threshold": None,
                        "comparison": "REPORT_ONLY",
                    },
                    "required_for_stabilizability": bool(required),
                    "boundary_ambiguous": bool(band),
                    "PBH_matrix_real": matrix.real,
                    "PBH_matrix_imag": matrix.imag,
                    "spectra": spectra,
                    "classification": classification,
                }
            )
        # Rank-revealing orthogonal reachable-subspace check; never use eigenvector inversion.
        C = _C(a, b)
        U, s, _ = np.linalg.svd(C, full_matrices=True)
        rank = int(np.count_nonzero(s > max(1e-12, 1e-10 * (s[0] if len(s) else 0))))
        unreachable = U[:, rank:]
        reduced = unreachable.conj().T @ a @ unreachable
        crosscheck = {
            "rank": rank,
            "unreachable_schur_eigenvalues": [],
            "schur_residual": schur_res,
            "rank_tolerance": 1e-10,
        }
        if len(reduced):
            rt, _ = schur(reduced, output="complex")
            crosscheck["unreachable_schur_eigenvalues"] = [
                {"re": float(z.real), "im": float(z.imag)} for z in np.diag(rt)
            ]
        return Outcome.available(
            {
                "normalized_pair": norm,
                "modes": modes,
                "stabilizability": "FAILED_PBH"
                if failed
                else "INDETERMINATE"
                if ambiguous
                else "SUPPORTED_LOCAL_NUMERICAL",
                "reasons": [],
                "rank_revealing_crosscheck": crosscheck,
            }
        )
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("PBH_NUMERICAL_FAILURE", str(exc))
