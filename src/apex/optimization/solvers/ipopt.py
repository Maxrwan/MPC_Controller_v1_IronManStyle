"""CasADi/IPOPT adapter; wall-clock timer encloses the actual optimization call."""

from time import perf_counter

import casadi as ca
import numpy as np

from apex.optimization.base import NLPRequest, SolverResult

DEFAULT_OPTIONS = {
    "print_time": False,
    "error_on_fail": False,
    "ipopt.print_level": 0,
    "ipopt.sb": "yes",
    "ipopt.max_iter": 100,
    "ipopt.tol": 1e-7,
    "ipopt.acceptable_tol": 1e-6,
    "ipopt.constr_viol_tol": 1e-7,
    "ipopt.bound_relax_factor": 0.0,
    "ipopt.honor_original_bounds": "yes",
}


class IpoptSolver:
    def __init__(self, problem, options=None):
        self.problem = problem
        self.options = {**DEFAULT_OPTIONS, **(options or {})}
        construction_start = perf_counter()
        self.backend = ca.nlpsol("apex_nmpc", "ipopt", problem.nlp, self.options)
        self.construction_seconds = perf_counter() - construction_start
        self.last_statistics = {}

    def solve(self, problem: NLPRequest) -> SolverResult:
        start = perf_counter()
        try:
            answer = self.backend(
                x0=problem.initial,
                p=problem.parameters,
                lbx=self.problem.lbx,
                ubx=self.problem.ubx,
                lbg=self.problem.lbg,
                ubg=self.problem.ubg,
            )
            elapsed = perf_counter() - start
            stats = self.backend.stats()
            g = np.asarray(answer["g"]).ravel()
            x = np.asarray(answer["x"]).ravel()
            infeasibility = max(
                float(np.max(np.maximum(self.problem.lbg - g, 0))),
                float(np.max(np.maximum(g - self.problem.ubg, 0))),
                float(np.max(np.maximum(self.problem.lbx - x, 0))),
                float(np.max(np.maximum(x - self.problem.ubx, 0))),
            )
            success = bool(
                stats["success"]
                and np.isfinite(x).all()
                and np.isfinite(g).all()
                and infeasibility <= 1e-6
            )
            self.last_statistics = {
                "solve_time": elapsed,
                "success": success,
                "status": stats["return_status"],
                "iterations": int(stats["iter_count"]),
                "objective": float(answer["f"]),
                "primal_infeasibility": infeasibility,
                "ipopt_statistics": stats,
            }
            return SolverResult(
                success, stats["return_status"], x if success else None, self.last_statistics
            )
        except RuntimeError as error:
            self.last_statistics = {
                "solve_time": perf_counter() - start,
                "success": False,
                "status": str(error),
                "iterations": 0,
                "objective": None,
                "primal_infeasibility": None,
                "ipopt_statistics": {},
            }
            return SolverResult(False, str(error), statistics=self.last_statistics)
