"""Composition, persisted physical events and separate computational accounting."""

import hashlib
import json
import os
import platform
import resource
from dataclasses import asdict
from datetime import datetime, timezone
from time import perf_counter

import numpy as np
import pandas as pd
import psutil
from run_lqr_baseline import make_track
from threading_study.config import ROOT
from threading_study.worker import stats

from apex.config import load_vehicle_parameters
from apex.control.baseline import cornering_reference
from apex.control.mpc.controller import make_mpc
from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig
from apex.control.trajectory.planner import TrajectoryPlanner
from apex.control.trajectory.tracker import TrackerConfig, TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner


def run(args, native):
    code_paths = list((ROOT / "src/apex/control/trajectory").glob("*.py")) + [
        ROOT / "src/apex/simulation/asynchronous.py",
        ROOT / "src/apex/control/mpc/problem.py",
        ROOT / "scripts/async_study/run.py",
        ROOT / "scripts/run_async_planner_tracker.py",
    ]
    provenance = dict(
        started_utc=datetime.now(timezone.utc).isoformat(),
        host=platform.platform(),
        python=platform.python_version(),
        load_at_start=os.getloadavg(),
        source_sha256={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths
        },
    )
    record = json.loads(
        (ROOT / "results/mpc_parameter_study/selected_candidates.json").read_text()
    )["C"]
    frozen = record["configuration"]
    config = MPCConfig(
        horizon=frozen["n"],
        dt=1 / frozen["hz"],
        substeps=frozen["substeps"],
        costs=CostScales(**frozen["costs"]),
        tire_physics=RACING_TIRE_PHYSICS,
        tracker_margin=0 if args.architecture == "sync" else 0.08,
    )
    folder = args.output / args.name
    folder.mkdir(parents=True, exist_ok=True)
    if args.architecture == "sync":
        from run_mpc_baseline import run_case

        run_case(
            args.name,
            mode=args.mode,
            latency=args.delay,
            duration=args.duration,
            laps=args.laps,
            output=args.output,
            plots=False,
            mpc_config=config,
            solver_options=frozen["solver"],
            warm_start=frozen["warm_start"],
        )
        r = json.loads((folder / "summary.json").read_text())
        r.update(
            architecture="sync",
            native_control=native,
            requested_delay=args.delay,
            provenance=provenance,
        )
        (folder / "summary.json").write_text(json.dumps(r, indent=2) + "\n")
        return
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = make_track("oval")
    before_rss = psutil.Process().memory_info().rss
    construction = perf_counter()
    controller = make_mpc(
        p, track, config=config, solver_options=frozen["solver"], warm_start=frozen["warm_start"]
    )
    problem = controller.problem
    lower = problem.lbx[problem.nx : problem.nx + 2]
    upper = problem.ubx[problem.nx : problem.nx + 2]
    tracker = TrajectoryTracker(
        p, lower, upper, TrackerConfig(feedback=args.architecture != "open_loop")
    )
    planner = TrajectoryPlanner(controller, track)
    construction_time = perf_counter() - construction
    after_rss = psutil.Process().memory_info().rss
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    simulation = AsyncConfig(
        duration=args.duration,
        laps=args.laps,
        latency_mode=args.mode,
        injected_delay=args.delay,
        spike_plan_id=40 if args.spike else -1,
        failed_plan_ids=(40,) if args.failure else (),
        disturbance_time=5.0 if args.disturbance else None,
        codriver_delay=None if args.mode == "measured" else 0.0,
    )
    ref = cornering_reference(p, 2, track.sample(0).curvature)
    initial = np.array([2.0, ref.vy, ref.yaw_rate, 0.0, 0.0, 0.0])
    result = AsyncRunner(plant, planner, tracker, track, simulation).run(initial)
    for key in [
        "states",
        "controls",
        "plans",
        "triggers",
        "fallbacks",
        "handoffs",
        "releases",
        "misses",
        "reserves",
        "codriver_misses",
    ]:
        pd.DataFrame(result.get(key, [])).to_csv(folder / (key + ".csv"), index=False)
    (folder / "trajectory_packets.json").write_text(json.dumps(result["packets"]) + "\n")
    (folder / "events.json").write_text(
        json.dumps(
            {
                k: result[k]
                for k in ["plans", "triggers", "fallbacks", "handoffs", "releases", "misses"]
            },
            default=lambda value: value.item() if isinstance(value, np.generic) else value,
        )
        + "\n"
    )
    summary = summarize(result)
    summary.update(
        architecture=args.architecture,
        config=asdict(simulation),
        candidate=record,
        planner_config=asdict(config),
        native_control=native,
        provenance=provenance,
        construction_seconds=construction_time,
        rss_before_bytes=before_rss,
        rss_after_construction_bytes=after_rss,
        rss_final_bytes=psutil.Process().memory_info().rss,
        rss_lifetime_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        startup_assumption="Gated synthetic rolling launch at 2 m/s; no dynamic model at rest",
    )
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def summarize(result):
    states, controls = pd.DataFrame(result["states"]), pd.DataFrame(result["controls"])
    summary = {
        k: result.get(k)
        for k in ["failure", "stop_reason", "lap_times", "end_time", "pending_at_end"]
    }
    if states.empty or controls.empty:
        return summary
    end = result["end_time"]
    weights = np.diff(np.r_[states.time.to_numpy(), end])
    weights = weights / weights.sum()
    summary["full_run"] = {
        "rms_e_y": float(np.sqrt(np.sum(weights * states.e_y**2))),
        "rms_e_psi": float(np.sqrt(np.sum(weights * states.e_psi**2))),
        "rms_speed_error": float(np.sqrt(np.sum(weights * (states.vx - 2) ** 2))),
    }
    active = controls[controls["mode"] == "trajectory"]
    summary["tracker_envelope"] = {}
    for key in ["e_y", "e_psi", "vy", "r"]:
        values = active["error_" + key].to_numpy()
        summary["tracker_envelope"][key] = dict(
            rms=float(np.sqrt(np.mean(values**2))),
            p95=float(np.percentile(abs(values), 95)),
            max=float(np.max(abs(values))),
        )
    plans = [r for r in result["plans"] if not r["startup"]]
    completed = [r for r in plans if r.get("completed")]
    summary.update(
        planner_launched=len(plans),
        planner_completed=len(completed),
        planner_misses=len(result["misses"]),
        codriver_misses=len(result.get("codriver_misses", [])),
        codriver_computational_exceedances=int(controls.computational_deadline_exceeded.sum()),
        planner_effective_hz=len(completed) / end,
        codriver_effective_hz=len(controls) / end,
        solver_failures=sum(r.get("solver_attempted", False) and not r["success"] for r in plans),
        planner_failures=sum(not r["success"] for r in plans),
        forecast_or_gain_failures=sum(
            r["preparation"] == "prediction_or_gain_validation_failed" for r in plans
        ),
        fallback_events=len(result["fallbacks"]),
        urgent_triggers=sum(r["kind"] == "urgent_replan" for r in result["triggers"]),
        boundary_violations=int(states.boundary_violation.sum()),
        max_front_utilization=float(states.front_utilization.max()),
        max_rear_utilization=float(states.rear_utilization.max()),
        steering_total_variation=float(abs(np.diff(controls.delta)).sum()),
        acceleration_total_variation=float(abs(np.diff(controls.a_cmd)).sum()),
        max_steering_rate=float(
            np.max(abs(np.diff(controls.delta)) / np.diff(controls.application_time))
        ),
    )
    reserve = np.array([r["reserve"] for r in result["reserves"]])
    intervals = weights * end
    descent = np.minimum(intervals, reserve)
    mean = float(np.sum(reserve * descent - descent**2 / 2) / end)
    moment2 = float(np.sum(reserve**2 * descent - reserve * descent**2 + descent**3 / 3) / end)

    def quantile(q):
        lo, hi = 0.0, float(reserve.max())
        for _ in range(40):
            mid = (lo + hi) / 2
            below = np.clip(intervals - (reserve - mid), 0, intervals).sum() / end
            if below >= q:
                hi = mid
            else:
                lo = mid
        return hi

    std = float(np.sqrt(max(0.0, moment2 - mean**2)))
    summary["reserve"] = {
        "mean": mean,
        "min": float(np.maximum(0, reserve - intervals).min()),
        "p50": quantile(0.50),
        "p95": quantile(0.95),
        "p99": quantile(0.99),
        "max": float(reserve.max()),
        "std": std,
        "cv": std / mean if mean else 0.0,
        "time_below_warning": float(np.clip(intervals - (reserve - 0.20), 0, intervals).sum()),
        "time_below_critical": float(np.clip(intervals - (reserve - 0.05), 0, intervals).sum()),
        "statistic_basis": "physical-time piecewise-linear reserve between logged events",
    }
    summary["codriver_timing"] = {
        k: stats(controls[k])
        for k in [
            "interpolation_time",
            "feedback_time",
            "command_validation_time",
            "kernel_time",
            "total_time",
            "cpu_time",
        ]
    }
    if plans:
        summary["planner_timing"] = {
            k: stats([r.get(k, 0) for r in plans])
            for k in [
                "solve_time",
                "preview_time",
                "prediction_time",
                "gain_time",
                "planner_total_time",
                "planner_cpu_time",
            ]
        }
        summary["planner_core_demand"] = sum(r["planner_cpu_time"] for r in plans) / end
    summary["codriver_core_demand"] = controls.cpu_time.sum() / end
    summary["total_core_demand"] = (
        summary.get("planner_core_demand", 0) + summary["codriver_core_demand"]
    )
    summary["startup"] = result["plans"][0]
    return summary
