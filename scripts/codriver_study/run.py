"""Fresh-worker paired experiments using the frozen asynchronous architecture."""

import hashlib
import json
import platform
import resource
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import psutil
from async_study.run import summarize
from codriver_study.replay import PacketReplay
from run_lqr_baseline import make_track
from threading_study.config import ROOT

from apex.config import load_vehicle_parameters
from apex.control.baseline import cornering_reference
from apex.control.local_mpc.model import LocalModel
from apex.control.local_mpc.tracker import LinearMPCTracker, LocalMPCConfig
from apex.control.mpc.controller import make_mpc
from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.control.trajectory.planner import TrajectoryPlanner
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner


def run(args, native):
    folder = args.output / args.name
    frozen_path = ROOT / "results/mpc_parameter_study/selected_candidates.json"
    candidate = json.loads(frozen_path.read_text())["C"]["configuration"]
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = make_track("oval")
    before = psutil.Process().memory_info().rss
    construction = perf_counter()
    controller = make_mpc(
        p,
        track,
        config=MPCConfig(
            horizon=candidate["n"],
            dt=1 / candidate["hz"],
            substeps=candidate["substeps"],
            costs=CostScales(**candidate["costs"]),
            tire_physics=RACING_TIRE_PHYSICS,
            tracker_margin=0.08,
        ),
        solver_options=candidate["solver"],
        warm_start=candidate["warm_start"],
    )
    problem = controller.problem
    lo, hi = problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
    local = LocalMPCConfig(
        horizon=args.horizon,
        rate_weight=args.weight,
        varying=args.model == "ltv",
        warm_start=not args.cold,
    )
    tracker = (
        TrajectoryTracker(p, lo, hi)
        if args.controller == "tvlqr"
        else LinearMPCTracker(p, lo, hi, LocalModel(SymbolicBicycle(p, RACING_TIRE_PHYSICS)), local)
    )
    source = ROOT / "results/asynchronous_planner_tracker/async_measured"
    planner = (
        PacketReplay(source) if args.phase == "replay" else TrajectoryPlanner(controller, track)
    )
    construction_time = perf_counter() - construction
    after = psutil.Process().memory_info().rss
    if args.scenario == "qp_failure" and args.controller == "mpc":
        tracker.failure_times.add(6.0)
    perturbation = args.scenario in ["disturbance", "stress"]
    config = AsyncConfig(
        duration=args.duration,
        laps=2,
        latency_mode="measured" if args.phase == "replay" else args.mode,
        injected_delay=args.delay,
        codriver_delay=0.0 if args.zero_codriver else None,
        spike_plan_id=40 if args.scenario == "spike" else -1,
        disturbance_time=(7.7 if args.scenario == "stress" else 5.0) if perturbation else None,
        disturbance_ey=0.06 if args.scenario == "stress" else 0.08,
        disturbance_heading=0.06 if args.scenario == "stress" else -0.04,
        urgent=args.phase != "replay",
    )
    reference = cornering_reference(p, 2, track.sample(0).curvature)
    result = AsyncRunner(
        DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS), planner, tracker, track, config
    ).run([2, reference.vy, reference.yaw_rate, 0, 0, 0])
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

    def scalar(value):
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(f"Unsupported JSON value: {type(value)}")

    (folder / "events.json").write_text(
        json.dumps(
            {
                k: result[k]
                for k in ["plans", "triggers", "fallbacks", "handoffs", "releases", "misses"]
            },
            default=scalar,
        )
        + "\n"
    )
    (folder / "trajectory_packets.json").write_text(json.dumps(result["packets"]) + "\n")
    records = getattr(tracker, "records", [])
    pd.DataFrame(records).to_csv(folder / "qp_events.csv", index=False)
    report = summarize(result)
    report.update(
        architecture=args.controller,
        phase=args.phase,
        scenario=args.scenario,
        config=asdict(config),
        local_config=asdict(local),
        native_control=native,
        construction_seconds=construction_time,
        rss_before_bytes=before,
        rss_after_construction_bytes=after,
        rss_final_bytes=psutil.Process().memory_info().rss,
        rss_lifetime_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        host=platform.platform(),
        qp_local_fallbacks=sum(r["local_fallback"] for r in records),
        frozen_candidate_sha256=hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
        replay_source=str(source) if args.phase == "replay" else None,
        replay_source_sha256=hashlib.sha256(
            (source / "trajectory_packets.json").read_bytes()
        ).hexdigest()
        if args.phase == "replay"
        else None,
    )
    if args.controller == "mpc":
        report["qp_dimensions"] = {str(n): s.dimensions() for n, s in tracker.workspaces.items()}
    report["source_sha256"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in list((ROOT / "src/apex/control/local_mpc").glob("*.py"))
        + [
            ROOT / "src/apex/control/trajectory/prediction.py",
            ROOT / "src/apex/simulation/asynchronous.py",
            Path(__file__),
        ]
    }
    (folder / "summary.json").write_text(json.dumps(report, indent=2, default=scalar) + "\n")
