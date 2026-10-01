"""Condensed convex QP and replaceable persistent OSQP workspace."""

from time import perf_counter
from typing import Protocol

import numpy as np
from scipy import sparse


def difference_matrix(n):
    return np.eye(n) - np.eye(n, k=-1)


def condense(matrices, error, nominal, previous, q, r, terminal, lower, upper, rate, weight=0):
    n = len(matrices)
    response, drift = np.zeros((4, n)), np.array(error, copy=True)
    hessian, gradient = r * np.eye(n), np.zeros(n)
    for i, (a, b, c) in enumerate(matrices):
        response = a @ response
        response[:, i] += b[:, 0]
        drift = a @ drift + c
        cost = terminal if i == n - 1 else q
        hessian += response.T @ cost @ response
        gradient += response.T @ cost @ drift
    d = difference_matrix(n)
    correction_prior = previous - nominal[0]
    offset = np.zeros(n)
    offset[0] = -correction_prior
    hessian += weight * d.T @ d
    gradient += weight * d.T @ offset
    nominal_increments = d @ nominal
    nominal_increments[0] -= previous
    lo = np.r_[lower - nominal, -rate - nominal_increments]
    hi = np.r_[upper - nominal, rate - nominal_increments]
    return 2 * (hessian + hessian.T) / 2, 2 * gradient, lo, hi


class QPSolver(Protocol):
    def solve(self, hessian, gradient, lower, upper, warm=None): ...


class OSQPWorkspace:
    """Fixed sparsity, numerical updates, bounded iterations; no nonlinear solver."""

    def __init__(self, n, tolerance=1e-6, maximum_iterations=400):
        import osqp

        self.n = n
        self.solver = osqp.OSQP()
        self.structure = sparse.csc_matrix(np.triu(np.ones((n, n))))
        self.rows = self.structure.indices
        self.columns = np.repeat(np.arange(n), np.diff(self.structure.indptr))
        self.constraints = sparse.csc_matrix(np.vstack([np.eye(n), difference_matrix(n)]))
        start = perf_counter()
        self.solver.setup(
            P=self.structure,
            q=np.zeros(n),
            A=self.constraints,
            l=np.full(2 * n, -1.0),
            u=np.full(2 * n, 1.0),
            verbose=False,
            eps_abs=tolerance,
            eps_rel=tolerance,
            max_iter=maximum_iterations,
            polishing=False,
            warm_starting=True,
            adaptive_rho=True,
            adaptive_rho_interval=25,
            check_termination=10,
        )
        self.setup_time = perf_counter() - start
        self.calls = 0

    def solve(self, hessian, gradient, lower, upper, warm=None):
        start = perf_counter()
        self.solver.update(Px=hessian[self.rows, self.columns], q=gradient, l=lower, u=upper)
        self.solver.warm_start(x=np.zeros(self.n) if warm is None else warm, y=np.zeros(2 * self.n))
        updated = perf_counter()
        result = self.solver.solve(raise_error=False)
        self.calls += 1
        info = result.info
        return result.x, dict(
            status=info.status,
            iterations=info.iter,
            primal_residual=info.prim_res,
            dual_residual=info.dual_res,
            update_time=updated - start,
            solve_wall_time=perf_counter() - updated,
            solver_time=info.solve_time,
            solver_update_time=info.update_time,
            solver_run_time=info.run_time,
            success=info.status_val == 1,
        )

    def dimensions(self):
        n = self.n
        return dict(
            nx=4,
            nu=1,
            horizon=n,
            decisions=n,
            equalities=0,
            two_sided_rows=2 * n,
            scalar_inequalities=4 * n,
            hessian_shape=[n, n],
            hessian_full_structural_nonzeros=n * n,
            hessian_upper_stored_nonzeros=n * (n + 1) // 2,
            constraint_shape=[2 * n, n],
            constraint_nonzeros=3 * n - 1,
        )
