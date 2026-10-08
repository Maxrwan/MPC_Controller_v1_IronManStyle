"""Fresh single-thread workers; generation is never called by simulation."""

import json
import subprocess
import sys

from threading_study.config import ROOT, configure_accelerate, environment


def dispatch(args):
    folder = args.output / args.case
    if args.worker:
        native = configure_accelerate(1)
        run(args, folder, native)
        return
    if (folder / "summary.json").exists():
        raise ValueError("Preserve existing results; use fresh output")
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "worker.log").open("w") as log:
        status = subprocess.run(
            [sys.executable, str(ROOT / "scripts/run_task007cr.py"), *sys.argv[1:], "--worker"],
            env=environment(1),
            cwd=ROOT,
            stdout=log,
            stderr=log,
        )
    if status.returncode:
        raise RuntimeError(str(folder / "worker.log"))
    print(json.loads((folder / "summary.json").read_text())["stop_reason"], flush=True)


def run(args, folder, native):
    import hashlib
    import random
    import resource
    import shutil
    from dataclasses import asdict

    import numpy as np
    import pandas as pd
    import psutil
    from async_study.run import summarize
    from task007b.references import PACKAGES, package_name

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

    random.seed(0)
    np.random.seed(0)
    args.fixture = args.fixture or PACKAGES / package_name(args.gamma)
    shutil.copytree(args.fixture, folder / "fixture", dirs_exist_ok=True)
    track, source, identity = load_track(args.fixture / "track_source.json")
    reference = PlanningReference(args.fixture, track, identity, feasibility_policy="advisory")
    if reference.manifest.get("aggression_factor") != args.gamma:
        raise ValueError("Requested gamma does not match the serialized fixture")
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    record = json.loads(
        (ROOT / "results/mpc_parameter_study/selected_candidates.json").read_text()
    )["C"]
    c = record["configuration"]
    config = MPCConfig(
        horizon=c["n"],
        dt=1 / c["hz"],
        substeps=c["substeps"],
        costs=CostScales(**c["costs"]),
        tire_physics=RACING_TIRE_PHYSICS,
        tracker_margin=0.08,
        racing_reference=True,
        progress_weight=args.progress_weight,
    )
    controller = make_mpc(
        p,
        track,
        config=config,
        speed_reference=reference,
        racing_reference=reference,
        solver_options=c["solver"],
        warm_start=c["warm_start"],
    )
    from task007cr.snapshot import RecordingSolver

    from apex.simulation.diagnostic_timing import DiagnosticTiming

    capture = RecordingSolver(controller.solver, controller)
    if args.capture:
        controller.solver = capture
    problem = controller.problem
    tracker = TrajectoryTracker(
        p, problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
    )

    class RecordingPlanner(TrajectoryPlanner):
        def __init__(self, *values):
            super().__init__(*values)
            self.predictions = []

        def prepare(self, *values, **kwargs):
            capture.context = dict(
                plan_id=values[0],
                release_time=values[2],
                release_state=np.asarray(values[1]).tolist(),
            )
            packet, diagnostics = super().prepare(*values, **kwargs)
            if diagnostics.get("solver_attempted"):
                self.predictions.append(
                    dict(
                        plan_id=values[0],
                        release_time=values[2],
                        prediction=self.controller.last_prediction,
                        diagnostics=self.controller.diagnostics(),
                    )
                )
            return packet, diagnostics

    planner = RecordingPlanner(controller, track)
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    simulation = AsyncConfig(
        duration=args.duration,
        laps=args.laps,
        latency_mode=args.mode,
        injected_delay=args.injected_delay,
        codriver_delay=None if args.mode == "measured" else 0.0,
    )
    ref = reference.sample(1.0)
    initial = np.array(
        [
            ref["v_ref_mps"],
            0,
            ref["v_ref_mps"] * ref["kappa_ref_1pm"],
            ref["e_psi_ref_rad"],
            1.0,
            ref["e_y_ref_m"],
        ]
    )
    timing = None
    if args.timing == "fixed":
        timing = DiagnosticTiming("fixed", (args.plan_delay,), (args.driver_delay,))
    elif args.timing == "replay":
        trace = json.loads(args.trace.read_text())
        timing = DiagnosticTiming("replay", tuple(trace["planner"]), tuple(trace["codriver"]))
        if args.perturb_index is not None:
            timing = timing.perturb(args.perturb_index, args.perturb_ms / 1000)
    result = AsyncRunner(plant, planner, tracker, track, simulation, timing=timing).run(initial)
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
            default=lambda x: x.item() if isinstance(x, np.generic) else x,
        )
        + "\n"
    )
    (folder / "predictions.json").write_text(json.dumps(planner.predictions) + "\n")
    import os
    import platform

    from threadpoolctl import threadpool_info

    metadata = dict(
        python=sys.version,
        platform=platform.platform(),
        machine=platform.machine(),
        processor=platform.processor(),
        native_control=native,
        threadpools=threadpool_info(),
        process_threads=psutil.Process().num_threads(),
        thread_environment={
            k: os.environ.get(k)
            for k in [
                "VECLIB_MAXIMUM_THREADS",
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "PYTHONHASHSEED",
            ]
        },
        seed=0,
        rng_used_by_active_path=False,
        gamma=args.gamma,
        progress_weight=args.progress_weight,
        fixture=str(args.fixture),
        timing=args.timing,
    )
    if args.capture:
        capture.save(folder, metadata)
    (folder / "backend.json").write_text(json.dumps(metadata, indent=2) + "\n")
    summary = summarize(result)
    # The inherited centerline/constant-2m/s summary is not a racing-reference metric.
    summary.pop("full_run", None)
    summary.update(
        architecture="tvlqr",
        diagnostic_timing=None if timing is None else asdict(timing),
        capture_enabled=args.capture,
        capture_total_seconds=sum(r["capture_seconds"] for r in capture.records),
        seed=0,
        gamma=args.gamma,
        progress_weight=args.progress_weight,
        config=asdict(simulation),
        planner_config=asdict(config),
        candidate=record,
        native_control=native,
        track_length=track.length,
        track_source=source,
        reference_manifest=reference.manifest,
        reference_validation=reference.validation,
        fixture_sha256={
            x.name: hashlib.sha256(x.read_bytes()).hexdigest()
            for x in args.fixture.glob("*")
            if x.is_file()
        },
        source_sha256={
            str(x.relative_to(ROOT)): hashlib.sha256(x.read_bytes()).hexdigest()
            for x in (ROOT / "src").rglob("*.py")
        },
        rss_final_bytes=psutil.Process().memory_info().rss,
        rss_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        startup_assumption="Gated rolling launch at s=1m on loaded reference; "
        "first lap transient, next two comparable",
    )
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
