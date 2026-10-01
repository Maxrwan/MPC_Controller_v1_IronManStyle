"""Measured comparison tables and target-independent workload/portability exports."""

import json

import pandas as pd
from threading_study.config import ROOT
from threading_study.report import table


def generate(root, frame):
    columns = [
        "case",
        "completed",
        "rms_e_y",
        "tracking_e_y_rms",
        "tracking_e_y_max",
        "steering_total_variation",
        "steering_rate_limit_seconds",
        "recovery_seconds",
        "planner_misses",
        "codriver_misses",
        "qp_local_fallbacks",
        "fallback_events",
        "boundary_violations",
        "compute_ratio_p95",
    ]
    sections = [
        "# Task 006.4 measured comparison",
        "RMS values use SI units. Full-loop summaries include measured codriver latency. "
        "Replay uses identical offered packets, with unchanged acceptance gates. "
        "Raw timing tails and local replacement events are retained.",
        "## Experiment outcomes",
        table(frame[columns]),
    ]
    timing = []
    envelope = []
    for path in sorted(root.glob("*/summary.json")):
        r = json.loads(path.read_text())
        for component, values in r["codriver_timing"].items():
            timing.append(
                dict(
                    case=path.parent.name,
                    component=component,
                    **{k: values[k] * 1000 for k in ["mean", "p50", "p95", "p99", "max", "std"]},
                )
            )
        for key, values in r["tracker_envelope"].items():
            envelope.append(dict(case=path.parent.name, error=key, **values))
    pd.DataFrame(timing).to_csv(root / "timing.csv", index=False)
    pd.DataFrame(envelope).to_csv(root / "tracker_envelopes.csv", index=False)
    qp_columns = [
        name
        for name in [
            "case",
            "qp_update_time_mean",
            "qp_update_time_p95",
            "qp_solver_time_mean",
            "qp_solver_time_p95",
            "qp_solver_update_time_mean",
            "qp_model_assembly_time_mean",
            "qp_iterations_mean",
            "qp_iterations_p95",
            "qp_non_deadline_fallbacks",
        ]
        if name in frame
    ]
    sections += [
        "## QP work (seconds except iteration/count fields)",
        table(frame[frame.controller == "mpc"][qp_columns]),
        "OSQP update time includes numerical matrix-update/refactorization work; "
        "an isolated factorization timer is not exposed by this Python interface.",
    ]
    sections += [
        "## Full-update timing, milliseconds",
        table(pd.DataFrame(timing).query("component == 'total_time'")),
        "## Four-state trajectory error distributions",
        table(pd.DataFrame(envelope)),
        "## Actuator activity",
        table(
            frame[
                [
                    "case",
                    "steering_total_variation",
                    "acceleration_total_variation",
                    "steering_rate_rms",
                    "steering_rate_max",
                    "steering_rate_limit_seconds",
                    "steering_correction_rms",
                    "steering_correction_max",
                    "applied_steering_correction_rms",
                    "applied_steering_correction_max",
                ]
            ]
        ),
        "Correction columns are requested pre-clipping corrections; applied columns use "
        "actual steering minus nominal feedforward.",
        "## CPU demand and process memory",
        table(
            frame[
                [
                    "case",
                    "planner_core_demand",
                    "codriver_core_demand",
                    "total_core_demand",
                    "effective_cores",
                    "final_rss_mib",
                    "peak_rss_mib",
                    "construction_rss_delta_mib",
                ]
            ]
        ),
        "CPU-core-seconds per second excludes plant integration/logging/transport. Replay does not "
        "execute the planner and its planner CPU demand is zero. In full replanning, forecasting "
        "the MPC codriver executes cloned QPs; that cost belongs to the planner pipeline. "
        "Process RSS includes imports, planner and logs, not an isolated QP workspace.",
        "## Constraint and deadline behavior",
        table(
            frame[
                [
                    "case",
                    "solver_failures",
                    "planner_failures",
                    "qp_local_fallbacks",
                    "codriver_computational_exceedances",
                    "max_front_utilization",
                    "max_rear_utilization",
                ]
            ]
        ),
    ]
    benchmark_path = root / "timing_benchmark/timing.json"
    measured = {}
    if benchmark_path.exists():
        measured = json.loads(benchmark_path.read_text())["results"]
        (root / "timing.json").write_text(json.dumps(measured, indent=2) + "\n")
        bench_rows = []
        for name, result in measured.items():
            bench_rows.append(
                dict(
                    controller=name,
                    **{
                        k: result["total_time"][k] * 1000
                        for k in ["mean", "p50", "p95", "p99", "max", "std"]
                    },
                    iterations_mean=result["iterations"]["mean"],
                    iterations_p95=result["iterations"]["p95"],
                    core_demand_100hz=result["core_demand_100hz"],
                    deadline_exceedances=result["deadline_exceedances"],
                )
            )
        sections += [
            "## Fixed-input repeated timing benchmark",
            table(pd.DataFrame(bench_rows)),
            "Three rotated controller-order replicates use identical sampled states, packets and "
            "previous controls. Warm/cold modes share matrix-update structure; cold mode "
            "zeros primal and dual starts; this is not a cold process per tick.",
        ]
    selection_path = root / "selected_configuration.json"
    selection = (
        json.loads(selection_path.read_text())
        if selection_path.exists()
        else {"horizon": 5, "selection_pending": True}
    )
    n = selection["horizon"]
    dimensions = dict(
        nx=4,
        nu=1,
        horizon=n,
        dt=0.01,
        decision_variables=n,
        equalities=0,
        two_sided_constraint_rows=2 * n,
        scalar_inequalities=4 * n,
        hessian_shape=[n, n],
        hessian_full_structural_nonzeros=n * n,
        hessian_upper_stored_nonzeros=n * (n + 1) // 2,
        constraint_shape=[2 * n, n],
        constraint_nonzeros=3 * n - 1,
        kkt_shape=[3 * n, 3 * n],
    )
    (root / "qp_dimensions.json").write_text(json.dumps(dimensions, indent=2) + "\n")
    workload = dict(
        **dimensions,
        update_rate_hz=100,
        major_operations=[
            "Approved six-state RK4 Jacobians; four-state lateral extraction.",
            "Finite-horizon state elimination and dense condensed cost assembly.",
            "4x4 DARE terminal cost; sparse quasi-definite QP factorization and ADMM iterations.",
            "Shared physical command validation and optional TVLQR replacement.",
        ],
        condensed_recursion_dense_multiply_count=4 * n**3 + 52 * n**2 + 16 * n,
        condensed_recursion_dense_add_count=4 * n**3 + 40 * n**2 + 20 * n,
        operation_count_caveat="Algebraic dense count for the N-step response/cost loop only; "
        "excludes rate penalty, model Jacobians, DARE, QP factorization/iterations and validation.",
        core_matrix_float64_payload_bytes=8 * (n * n + (3 * n - 1) + 5 * n),
        memory_caveat="Dense H, CSC A values, q/l/u only; "
        "excludes indices, model, solver factorization and objects.",
        timing=measured,
        solver="OSQP 1.1.3, built-in direct backend",
        fixed_structure_reuse=True,
        numeric_hessian_updates_require_refactorization=True,
    )
    (root / "workload.json").write_text(json.dumps(workload, indent=2) + "\n")
    portability = {
        name: dict(
            m1_p95_seconds=data["total_time"]["p95"],
            rho_required_10ms=data["total_time"]["p95"] / 0.01,
            rho_required_5ms=data["total_time"]["p95"] / 0.005,
            interpretation="Target single-core throughput / M1 throughput; not Pi utilization",
        )
        for name, data in measured.items()
    }
    (root / "portability.json").write_text(
        json.dumps(
            dict(
                model="T_target ~= T_M1 / rho",
                requirements=portability,
                pi4_measured=False,
                pi5_measured=False,
                unknowns=[
                    "Target BLAS/OSQP build and CPU frequency/thermal governor",
                    "OS jitter, scheduling, sensor/transport overhead and concurrent planner load",
                    "Memory allocation and Python versus compiled implementation",
                ],
            ),
            indent=2,
        )
        + "\n"
    )
    sections += [
        "## Hardware-independent QP dimensions",
        table(pd.DataFrame([dimensions])),
        "## Pi portability",
        table(pd.DataFrame([dict(controller=k, **v) for k, v in portability.items()])),
        "These are throughput requirements, not measured Pi performance. On both Pi 4 and Pi 5, "
        "benchmark the complete callback and concurrent planner under the intended OS, "
        "thermal policy and native-library build. Small matrices make single-core latency and "
        "Python/validation overhead material; tiny matrix storage does not imply tiny process RSS. "
        "Direct target measurement is necessary before deployment.",
        "OSQP numerical updates and warm starts follow its "
        "[official Python interface](https://osqp.org/docs/interfaces/python.html).",
    ]
    (ROOT / "docs/LINEAR_MPC_CODRIVER_RESULTS.md").write_text("\n\n".join(sections) + "\n")
