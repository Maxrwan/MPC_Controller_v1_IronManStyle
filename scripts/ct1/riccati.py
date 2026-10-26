"""Original packet gains remain primary; numerical reproduction never replaces them."""

from __future__ import annotations

from .contracts import (
    LATERAL,
    ArchivedPacket,
    F64Matrix,
    GainComparison,
    GainCriteria,
    Linearization,
    Outcome,
    OutcomeStatus,
    Reason,
    RiccatiAudit,
    RiccatiCriteria,
)


def compare_original_gains(
    original: F64Matrix, recomputed: F64Matrix, criteria: GainCriteria
) -> GainComparison:
    import numpy as np

    atol = criteria.get("gain_reproduction_abs_tol", criteria.get("gain_abs_tol", 1e-9))
    rtol = criteria.get("gain_reproduction_rel_tol", criteria.get("gain_rel_tol", 1e-7))
    if atol != 1e-9 or rtol != 1e-7:
        raise ValueError("Changed gain reproduction criteria")
    old, new = np.asarray(original), np.asarray(recomputed)
    if old.shape != new.shape or not np.isfinite(old).all() or not np.isfinite(new).all():
        raise ValueError("Gain shape/finite failure")
    error = np.abs(old - new)
    passed = error <= atol + rtol * np.abs(old)
    return {
        "original_gains": old.copy(),
        "recomputed_gains": new.copy(),
        "absolute_errors": error,
        "relative_errors": np.divide(error, np.abs(old)) if np.all(old != 0) else None,
        "criteria": criteria,
        "entrywise_pass": passed,
        "comparison": "PASS" if passed.all() else "FAIL",
        "original_replaced": False,
    }


def _residual(name, terms, threshold):
    import numpy as np

    raw = float(np.linalg.norm(sum(terms), "fro"))
    den = max(1.0, sum(float(np.linalg.norm(t, "fro")) for t in terms))
    v = raw / den
    return {
        "name": name,
        "norm_kind": "Frobenius",
        "raw_residual": raw,
        "denominator": den,
        "normalized_residual": v,
        "threshold": threshold,
        "comparison": "PASS" if v <= threshold else "FAIL",
    }


def _terminal_solution(a, b, q, r):
    from scipy.linalg import solve_discrete_are

    return solve_discrete_are(a, b, q, r)


def _backward_step(a, b, q, r, pnext):
    import numpy as np

    h = r + b.T @ pnext @ b
    if not np.isfinite(h).all() or np.linalg.eigvalsh((h + h.T) / 2).min() <= 0:
        raise ValueError("Nonpositive Riccati H; no regularization")
    gain = np.linalg.solve(h, b.T @ pnext @ a)
    return gain, q + a.T @ pnext @ a - a.T @ pnext @ b @ gain, h


def audit_packet_gains(
    packet: ArchivedPacket,
    original_grid_pairs: tuple[Linearization, ...],
    criteria: RiccatiCriteria,
) -> Outcome[RiccatiAudit]:
    try:
        import numpy as np

        if not original_grid_pairs:
            raise ValueError("No original gain support")
        if (
            criteria["DARE_and_recursion_relative_residual_max"] != 1e-8
            or criteria["symmetry_relative_residual_max"] != 1e-10
            or criteria["positive_eigenvalue_floor_scaled"] != 1e-12
        ):
            raise ValueError("Changed Riccati criteria")
        indices = [p.key.gain_index for p in original_grid_pairs]
        if indices != list(range(indices[0], len(packet.gain_times_s))) or len(indices) > 80:
            raise ValueError("Complete original suffix through terminal required")
        matrices = [
            (p.A[np.ix_(LATERAL, LATERAL)], p.B[list(LATERAL), :1]) for p in original_grid_pairs
        ]
        Q = np.diag(1 / np.array([0.1, 0.1, 0.5, 1.0]) ** 2)
        R = np.array([[1 / 0.2**2]])
        a, b = matrices[-1]
        P = _terminal_solution(a, b, Q, R)
        terminal = P.copy()
        D = np.diag([0.1, 0.1, 0.5, 1.0])
        Ui = np.array([[0.2]])
        H = R + b.T @ P @ b
        term = a.T @ P @ b @ np.linalg.solve(H, b.T @ P @ a)
        residuals = [
            _residual("terminal_DARE", tuple(D @ v @ D for v in (P, -Q, -a.T @ P @ a, term)), 1e-8)
        ]
        terminal_scaled = D @ terminal @ D
        terminal_skew = float(
            np.linalg.norm(D @ (terminal - terminal.T) @ D)
            / max(1.0, np.linalg.norm(terminal_scaled))
        )
        terminal_eig = float(np.linalg.eigvalsh((terminal_scaled + terminal_scaled.T) / 2).min())
        terminal_condition = float(np.linalg.cond(terminal_scaled))
        residuals.append(
            _residual("terminal_symmetry", (D @ terminal @ D, -D @ terminal.T @ D), 1e-10)
        )
        gains = []
        pmins = []
        hmins = []
        conditions = []
        skews = []
        valid = terminal_eig > 1e-12 and terminal_condition <= 1e10 and terminal_skew <= 1e-10
        for index, (a, b) in reversed(list(zip(indices, matrices))):
            H = R + b.T @ P @ b
            scaled_h = Ui @ H @ Ui
            hmin = float(np.linalg.eigvalsh((scaled_h + scaled_h.T) / 2).min())
            hmins.append(hmin)
            if hmin <= 1e-12:
                raise ValueError("Nonpositive/ill-resolved Riccati H")
            gain, nextP, H = _backward_step(a, b, Q, R, P)
            skew = float(
                np.linalg.norm(D @ (nextP - nextP.T) @ D) / max(1.0, np.linalg.norm(D @ nextP @ D))
            )
            skews.append(skew)
            Pnew = (nextP + nextP.T) / 2
            residuals.append(
                _residual(
                    "recursion_" + str(index),
                    tuple(D @ v @ D for v in (Pnew, -Q, -a.T @ P @ a, a.T @ P @ b @ gain)),
                    1e-8,
                )
            )
            residuals.append(
                {
                    "name": "symmetry_" + str(index),
                    "norm_kind": "Frobenius",
                    "raw_residual": float(np.linalg.norm(D @ (nextP - nextP.T) @ D)),
                    "denominator": max(1.0, float(np.linalg.norm(D @ nextP @ D))),
                    "normalized_residual": skew,
                    "threshold": 1e-10,
                    "comparison": "PASS" if skew <= 1e-10 else "FAIL",
                }
            )
            scaledP = D @ Pnew @ D
            eig = np.linalg.eigvalsh(scaledP)
            pmins.append(float(eig.min()))
            condition = float(np.linalg.cond(scaledP))
            conditions.append(condition if np.isfinite(condition) else None)
            valid = valid and eig.min() > 1e-12 and skew <= 1e-10 and condition <= 1e10
            gains.append(gain.ravel())
            P = Pnew
        computed = np.array(gains[::-1])
        original = np.asarray(packet.original_gains)[indices]
        comparison = compare_original_gains(original, computed, criteria)
        valid = bool(
            valid
            and comparison["comparison"] == "PASS"
            and all(r["comparison"] == "PASS" for r in residuals)
        )
        data = {
            "packet_id": packet.raw_fields["plan_id"],
            "original_gain_indices": indices,
            "original_gains": original.copy(),
            "recomputed_gains": computed,
            "terminal_P": terminal,
            "terminal_Q": Q,
            "terminal_R": R,
            "residuals": residuals,
            "P_min_eigenvalues": pmins[::-1],
            "H_min_eigenvalues": hmins[::-1],
            "condition_numbers": conditions[::-1],
            "pre_symmetrization_skews": skews[::-1],
            "gain_abs_errors": comparison["absolute_errors"],
            "gain_reproduction": comparison["comparison"],
            "original_gains_replaced": False,
        }
        return Outcome(
            OutcomeStatus.AVAILABLE if valid else OutcomeStatus.FAILED_COMPARISON,
            ()
            if valid
            else (
                Reason(
                    "RICCATI_OR_GAIN_CHECK_FAILED",
                    "Original gains preserved; affected conclusions withheld",
                ),
            ),
            data,
        )
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("RICCATI_UNAVAILABLE", str(exc))
