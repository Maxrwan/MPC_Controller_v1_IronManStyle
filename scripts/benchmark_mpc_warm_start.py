"""Paired cold/shifted-primal solves of the identical, fixed circle NLP."""

import json
from pathlib import Path

import numpy as np

from apex.config import load_vehicle_parameters
from apex.control.baseline import cornering_reference
from apex.control.mpc.cost import TerminalSchedule
from apex.control.mpc.preview import make_preview
from apex.control.mpc.problem import MPCProblem
from apex.control.mpc.warm_start import shift_solution
from apex.optimization.base import NLPRequest
from apex.optimization.solvers.ipopt import IpoptSolver
from apex.track import ClosedTrack
from apex.track.synthetic import circle_waypoints


def main():
    root = Path(__file__).resolve().parents[1]
    p = load_vehicle_parameters(root / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = ClosedTrack.from_waypoints(
        circle_waypoints(5, count=64), left_width=0.6, right_width=0.9
    )
    problem = MPCProblem(p)
    solver = IpoptSolver(problem)
    ref = cornering_reference(p, 2, track.sample(0).curvature)
    state = np.array([2.0, ref.vy, ref.yaw_rate, -0.04, 0, 0.08])
    previous = np.zeros(2)
    preview = make_preview(track, p, lambda s: 2, 0)
    parameters = problem.parameter_vector(state, previous, preview, TerminalSchedule(p).matrix(2))
    cold_guess = problem.pack(*problem.cold_start(state, previous, preview))
    records = []
    for pair in range(6):
        cold = solver.solve(NLPRequest(cold_guess, parameters))
        assert cold.success
        cold_stats = dict(cold.statistics)
        warm_guess = problem.pack(*shift_solution(*problem.unpack(cold.solution), state))
        warm = solver.solve(NLPRequest(warm_guess, parameters))
        assert warm.success
        assert abs(warm.statistics["objective"] - cold_stats["objective"]) < 1e-5
        records.append(
            {
                "pair": pair,
                "cold_time": cold_stats["solve_time"],
                "warm_time": warm.statistics["solve_time"],
                "cold_iterations": cold_stats["iterations"],
                "warm_iterations": warm.statistics["iterations"],
                "objective_difference": abs(warm.statistics["objective"] - cold_stats["objective"]),
            }
        )
    summary = {
        "method": (
            "Six interleaved pairs, same NLP parameters/state; "
            "compiled once; shifted primal warm guess"
        ),
        "records": records,
    }
    for key in ("cold_time", "warm_time", "cold_iterations", "warm_iterations"):
        summary[key + "_mean"] = float(np.mean([r[key] for r in records]))
    path = root / "results/mpc_baseline/warm_start_benchmark.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
