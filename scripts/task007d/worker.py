"""One short fixed-delay pilot. Imported only after fresh SINGLE configuration."""

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, process_time

import numpy as np
import psutil
from task007d.diagnostics import accuracy, forecasts, score
from task007d.metrics import chronology, physical_metrics, stop_reasons
from threadpoolctl import threadpool_info

from apex.config import load_vehicle_parameters
from apex.control.mpc.controller import make_mpc
from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig
from apex.control.trajectory.planner import TrajectoryPlanner
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner
from apex.simulation.diagnostic_timing import DiagnosticTiming


def write(path, value):
    def convert(v):
        return v.tolist() if isinstance(v, np.ndarray) else v.item()

    with path.open("x") as stream:
        json.dump(value, stream, indent=2, default=convert, allow_nan=False)
        stream.write("\n")


def run(args, native):
    folder = args.output
    fixture_root = "task007b" if args.gamma == 2.0 else "task007c_resume"
    fixture = Path("configs/planning") / fixture_root / f"gamma_{args.gamma:.3f}".replace(".", "p")
    track, _, identity = load_track(fixture / "track_source.json")
    reference = PlanningReference(fixture, track, identity, feasibility_policy="advisory")
    if reference.manifest["aggression_factor"] != args.gamma:
        raise ValueError("Wrong frozen fixture")
    parameters_path = Path("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    p = load_vehicle_parameters(parameters_path)
    config = MPCConfig(
        horizon=8,
        dt=0.1,
        substeps=4,
        costs=CostScales(lateral=2),
        tire_physics=RACING_TIRE_PHYSICS,
        tracker_margin=0.08,
        racing_reference=True,
        progress_weight=0,
    )
    controller = make_mpc(
        p,
        track,
        config=config,
        speed_reference=reference,
        racing_reference=reference,
        solver_options={"ipopt.warm_start_init_point": "yes"},
        warm_start=True,
    )
    thread_samples = [psutil.Process().num_threads()]

    class RecordingPlanner(TrajectoryPlanner):
        def prepare(self, *values, **kwargs):
            thread_samples.append(psutil.Process().num_threads())
            answer = super().prepare(*values, **kwargs)
            thread_samples.append(psutil.Process().num_threads())
            return answer

    planner = RecordingPlanner(controller, track)
    problem = controller.problem
    tracker = TrajectoryTracker(
        p, problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
    )
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    timing = DiagnosticTiming("fixed", (args.planner_delay,), (args.codriver_delay,))
    simulation = AsyncConfig(
        duration=args.duration,
        latency_mode="injected",
        injected_delay=args.planner_delay,
        codriver_delay=args.codriver_delay,
        committed_prefix_prediction=args.architecture == "B",
    )
    ref = reference.sample(1.0)
    initial = [
        ref["v_ref_mps"],
        0.0,
        ref["v_ref_mps"] * ref["kappa_ref_1pm"],
        ref["e_psi_ref_rad"],
        1.0,
        ref["e_y_ref_m"],
    ]
    releases = []
    wall, cpu = perf_counter(), process_time()
    result = AsyncRunner(
        plant, planner, tracker, track, simulation, timing=timing, release_observer=releases.append
    ).run(initial)
    wall, cpu = perf_counter() - wall, process_time() - cpu
    # Persist physical execution before any offline forecast/scoring failure is possible.
    write(folder / "raw.json", result)
    write(folder / "release_contexts.json", [asdict(r) for r in releases])
    offline_plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    rows = []
    active_matches = []
    for r in releases:
        alternatives = forecasts(r, planner.predictor)
        event = next(e for e in result["plans"] if e["plan_id"] == r.plan_id)
        active = alternatives[args.architecture]
        active_matches.append(
            active["state"] == event["predicted_state"]
            and active["control"] == event["predicted_previous_control"]
        )
        rows.append(score(r, alternatives, result, offline_plant))
    write(folder / "scores.json", rows)
    metrics = physical_metrics(result, track)
    issues = chronology(result)
    gates = stop_reasons(result, metrics, issues)
    if not all(active_matches):
        gates.append("offline_active_forecast_mismatch")
    if any(
        r["truth"]["kind"] in ("reconstruction_failed", "reconstruction_discontinuity")
        for r in rows
    ):
        gates.append("target_reconstruction_failure")
    if any(r["forecasts"][a]["failure"] for r in rows for a in ("A", "B")):
        gates.append("shadow_forecast_failure")
    source_files = sorted(Path("src").rglob("*.py")) + sorted(Path("scripts/task007d").glob("*.py"))
    source_files += [Path("scripts/run_task007d_pilot.py")]
    summary = dict(
        architecture=args.architecture,
        gamma=args.gamma,
        requested_duration=args.duration,
        configuration=asdict(config),
        timing=asdict(timing),
        simulation=asdict(simulation),
        initial_state=initial,
        fixture=str(fixture),
        fixture_sha256={
            str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(fixture.glob("*"))
            if f.is_file()
        },
        vehicle_sha256=hashlib.sha256(parameters_path.read_bytes()).hexdigest(),
        source_sha256={str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in source_files},
        base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        native=native,
        threadpools=threadpool_info(),
        observed_process_thread_counts=sorted(set(thread_samples)),
        runtime_wall_seconds=wall,
        runtime_cpu_seconds=cpu,
        runtime_cpu_wall_ratio=cpu / wall,
        python=sys.version,
        platform=platform.platform(),
        matched=accuracy(rows),
        physical=metrics,
        chronology_issues=issues,
        active_forecast_exact_matches=sum(active_matches),
        stop_gate=gates,
        raw_sha256=hashlib.sha256((folder / "raw.json").read_bytes()).hexdigest(),
    )
    write(folder / "summary.json", summary)
    print(
        json.dumps(
            {k: summary[k] for k in ("architecture", "gamma", "matched", "physical", "stop_gate")}
        )
    )
    return bool(gates)
