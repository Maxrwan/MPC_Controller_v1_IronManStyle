"""Task006.1 regression/timing without changing Task006 costs or solver options."""

import argparse
import json
from pathlib import Path

import numpy as np
from run_mpc_baseline import aggregate, run_case

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/mpc_grip"


def timing_report():
    summaries = {p.parent.name: json.loads(p.read_text()) for p in OUT.glob("*/summary.json")}
    report = {
        "cases": summaries,
        "timing_interpretation": (
            "Single-host observational comparison. No solver optimization or cost tuning."
        ),
    }
    old_path = ROOT / "results/mpc_baseline/oval_zero/summary.json"
    if "oval_zero" in summaries and old_path.exists():
        old = json.loads(old_path.read_text())
        new = summaries["oval_zero"]
        report["saved_task006_oval"] = {
            key: old[key]
            for key in (
                "solve_time",
                "iterations",
                "full_run",
                "settled",
                "cold_start",
                "warm_start",
            )
        }
        report["oval_mean_solve_change_percent"] = (
            new["solve_time"]["mean"] / old["solve_time"]["mean"] - 1
        ) * 100
        report["oval_iteration_mean_change"] = new["iterations"]["mean"] - old["iterations"]["mean"]
    path = OUT / "oval_zero/predictions.jsonl"
    if path.exists():
        entries = [
            json.loads(line)["solver_statistics"]["ipopt_statistics"]
            for line in path.read_text().splitlines()
        ]
        keys = sorted(
            {key for d in entries for key in d if key.startswith(("t_wall_", "t_proc_", "n_call_"))}
        )
        report["ipopt_evaluation_statistics"] = {
            k: {
                "mean": float(np.mean([d[k] for d in entries if k in d])),
                "max": float(max(d[k] for d in entries if k in d)),
            }
            for k in keys
        }
    # Sparsity is inspected using the unchanged adapter's derivative functions.
    from apex.config import load_vehicle_parameters
    from apex.control.mpc.problem import MPCConfig, MPCProblem
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.optimization.solvers.ipopt import IpoptSolver

    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    problem = MPCProblem(p, MPCConfig(tire_physics=RACING_TIRE_PHYSICS))
    solver = IpoptSolver(problem)
    structure = {
        "variables": len(problem.lbx),
        "equalities": problem.equality_count,
        "inequalities": problem.inequality_count,
        "parameters": int(problem.nlp["p"].numel()),
        "nlp_build_seconds": problem.construction_seconds,
        "backend_build_seconds": solver.construction_seconds,
    }
    for name in ("nlp_jac_g", "nlp_hess_l"):
        function = solver.backend.get_function(name)
        structure[name] = {
            function.name_out(i): {
                "shape": list(function.size_out(i)),
                "nonzeros": function.nnz_out(i),
            }
            for i in range(function.n_out())
        }
    report["structure"] = structure
    report["horizon_estimates"] = (
        "Not measured: horizon sweep belongs to Task006.2; no linear extrapolation of solve time."
    )
    (OUT / "timing_baseline.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "structure": structure,
                "oval_mean_solve_change_percent": report.get("oval_mean_solve_change_percent"),
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=["all", "circle", "oval", "disturbance", "latency", "timing"],
        default="all",
    )
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.case in ("all", "circle"):
        run_case("circle_zero", track_name="circle", output=OUT)
    if args.case in ("all", "oval"):
        run_case("oval_zero", output=OUT)
    if args.case in ("all", "disturbance"):
        run_case(
            "combined", track_name="circle", ey=0.08, epsi=-0.04, duration=12, laps=None, output=OUT
        )
    if args.case in ("all", "latency"):
        run_case("oval_45ms", mode="injected", latency=0.045, output=OUT)
    aggregate(OUT)
    timing_report()


if __name__ == "__main__":
    main()
