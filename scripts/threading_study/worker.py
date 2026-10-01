"""One isolated process, one optimizer, deterministic repeated representative solves."""

import hashlib
import json
import os
import platform
import resource
from pathlib import Path
from time import perf_counter, process_time

from threading_study.config import OUT, ROOT, configure_accelerate


def stats(values):
    import numpy as np

    a = np.asarray(values, dtype=float)
    return {
        "mean": float(a.mean()),
        "p50": float(np.percentile(a, 50)),
        "p95": float(np.percentile(a, 95)),
        "p99": float(np.percentile(a, 99)),
        "max": float(a.max()),
        "std": float(a.std()),
        "cv": float(a.std() / a.mean()) if a.mean() else 0.0,
    }


class MeasuredBackend:
    """Bench-only proxy: aggregate process CPU clock brackets the native call."""

    def __init__(self, backend):
        self.backend = backend
        self.last = {}

    def __call__(self, **kwargs):
        wall, cpu = perf_counter(), process_time()
        answer = self.backend(**kwargs)
        self.last = {
            "backend_cpu_time": process_time() - cpu,
            "backend_measured_wall": perf_counter() - wall,
        }
        return answer

    def stats(self):
        return self.backend.stats()


def frozen(workload):
    selected = json.loads((OUT / "frozen_candidates.json").read_text())
    return selected[workload]


def make_controller(workload, diagnostic_options=None):
    from run_lqr_baseline import make_track

    from apex.config import load_vehicle_parameters
    from apex.control.mpc.controller import make_mpc
    from apex.control.mpc.cost import CostScales
    from apex.control.mpc.problem import MPCConfig
    from apex.models.tire.config import RACING_TIRE_PHYSICS

    record = frozen(workload)
    c = record["configuration"]
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    config = MPCConfig(
        horizon=c["n"],
        dt=1 / c["hz"],
        substeps=c["substeps"],
        costs=CostScales(**c["costs"]),
        tire_physics=RACING_TIRE_PHYSICS,
    )
    return make_mpc(
        p,
        make_track("oval"),
        config=config,
        solver_options={**c["solver"], **(diagnostic_options or {})},
        warm_start=c["warm_start"],
    )


def run_worker(workload, threads, replicate, samples, warmup, folder):
    native = configure_accelerate(threads)
    import casadi as ca
    import numpy as np
    import pandas as pd
    import psutil
    from threadpoolctl import threadpool_info

    from apex.state import STATE_NAMES

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    record = frozen(workload)
    source = ROOT / "results/mpc_parameter_study/runs" / record["experiment_id"]
    frame = pd.read_csv(source / "solver_events.csv", float_precision="round_trip")
    indices = np.linspace(0, len(frame) - 1, samples, dtype=int)
    snapshots = frame.iloc[indices]
    process = psutil.Process()
    controller = make_controller(workload)
    proxy = MeasuredBackend(controller.solver.backend)
    controller.solver.backend = proxy
    problem = controller.problem
    jacobian = proxy.backend.get_function("nlp_jac_g").sparsity_out(1)
    hessian = proxy.backend.get_function("nlp_hess_l").sparsity_out(0)
    rr, cc = hessian.get_triplet()
    diagonal = sum(i == j for i, j in zip(rr, cc))
    dimensions = {
        "variables": len(problem.lbx),
        "equalities": problem.equality_count,
        "inequalities": problem.inequality_count,
        "jacobian_shape": list(jacobian.shape),
        "jacobian_nnz": jacobian.nnz(),
        "hessian_shape": list(hessian.shape),
        "hessian_upper_nnz": hessian.nnz(),
        "hessian_full_nnz": 2 * hessian.nnz() - diagonal,
        "rk4_rhs_sites_per_full_horizon": 4
        * controller.config.substeps
        * controller.config.horizon,
    }

    def step(row):
        state = np.array([row[f"x_sample_{k}"] for k in STATE_NAMES])
        context = {
            "dt": controller.config.dt,
            "previous_control": np.array([row.previous_delta, row.previous_a_cmd]),
        }
        start, cpu = perf_counter(), process_time()
        action = controller.compute_control(state, context)
        cpu_elapsed, wall_elapsed = process_time() - cpu, perf_counter() - start
        d = controller.diagnostics()
        prediction = controller.last_prediction
        return action, d, prediction, cpu_elapsed, wall_elapsed

    for i in range(warmup):
        _, diagnostic, _, _, _ = step(snapshots.iloc[i % samples])
        if not diagnostic["success"]:
            raise RuntimeError("Warm-up solve failed")
    pools = threadpool_info()
    rows, solutions = [], []
    start = perf_counter()
    for i, (_, snapshot) in enumerate(snapshots.iterrows()):
        action, diagnostic, prediction, cpu, wall = step(snapshot)
        native_stats = prediction["solver_statistics"]["ipopt_statistics"]
        row = {
            "sample": i,
            "source_row": int(indices[i]),
            **diagnostic,
            **proxy.last,
            "controller_cpu_time": cpu,
            "controller_measured_wall": wall,
            "rss_bytes": process.memory_info().rss,
            "threads_between_solves": process.num_threads(),
        }
        row.update(
            {
                k: v
                for k, v in native_stats.items()
                if k.startswith(("t_wall_nlp_", "t_proc_nlp_", "n_call_nlp_"))
            }
        )
        rows.append(row)
        solutions.append(
            {
                "sample": i,
                "objective": diagnostic["objective"],
                "success": diagnostic["success"],
                "status": diagnostic["status"],
                "primal_infeasibility": diagnostic["primal_infeasibility"],
                "first_control": action.tolist(),
                **{k: prediction.get(k) for k in ["states", "controls", "slacks"]},
            }
        )
    end = perf_counter()
    pd.DataFrame(rows).to_csv(folder / "observations.csv", index=False)
    (folder / "solutions.json").write_text(json.dumps(solutions) + "\n")
    timed = [
        "solve_time",
        "backend_cpu_time",
        "backend_measured_wall",
        "controller_cpu_time",
        "controller_measured_wall",
        "preview_time",
        "parameter_update_time",
        "postprocessing_time",
        "total_compute_time",
        "warm_start_preparation_time",
        "iterations",
    ]
    report = {
        "workload": workload,
        "threads": threads,
        "replicate": replicate,
        "samples": samples,
        "warmup": warmup,
        "native_control": native,
        "threadpoolctl": pools,
        "dimensions": dimensions,
        "configuration": record,
        "input_file_sha256": hashlib.sha256(
            (source / "solver_events.csv").read_bytes()
        ).hexdigest(),
        "indices": indices.tolist(),
        "measurement_start": start,
        "measurement_end": end,
        "host_load": list(os.getloadavg()),
        "pid": os.getpid(),
        "all_success": all(r["success"] for r in rows),
        "max_primal_residual": max(r["primal_infeasibility"] or 0 for r in rows),
        "statistics": {key: stats([r[key] for r in rows]) for key in timed},
        "effective_backend_cores": sum(r["backend_cpu_time"] for r in rows)
        / sum(r["backend_measured_wall"] for r in rows),
        "effective_controller_cores": sum(r["controller_cpu_time"] for r in rows)
        / sum(r["controller_measured_wall"] for r in rows),
        "rss_peak_process_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "rss_between_solves": stats([r["rss_bytes"] for r in rows]),
        "threads_between_solves": stats([r["threads_between_solves"] for r in rows]),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "casadi": ca.__version__,
        },
        "environment": {
            k: os.environ.get(k)
            for k in [
                "VECLIB_MAXIMUM_THREADS",
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
            ]
        },
    }
    (folder / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["all_success"]:
        raise RuntimeError("Measured solver failure: retained logs")
