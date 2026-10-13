"""Frozen D3 construction reused for A-only C pilots; read-only observation of physics."""

import hashlib
import json
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, process_time

import numpy as np
import psutil
from task007d.metrics import chronology, physical_metrics, stop_reasons
from task007d.worker import write
from threadpoolctl import threadpool_info

from apex.config import load_vehicle_parameters
from apex.control.mpc.controller import make_mpc
from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig
from apex.control.trajectory.packet import TrajectoryBuffer
from apex.control.trajectory.planner import TrajectoryPlanner
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner
from apex.simulation.diagnostic_timing import DiagnosticTiming


def run(args, protocol, native):
    spec = protocol["cases"][args.case]
    gamma = spec["gamma"]
    fixture = (
        Path("configs/planning")
        / ("task007b" if gamma == 2.0 else "task007c_resume")
        / f"gamma_{gamma:.3f}".replace(".", "p")
    )
    track, _, identity = load_track(fixture / "track_source.json")
    reference = PlanningReference(fixture, track, identity, feasibility_policy="advisory")
    assert reference.manifest["aggression_factor"] == gamma
    vehicle_path = Path("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    p = load_vehicle_parameters(vehicle_path)
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
    threads = []

    class Planner(TrajectoryPlanner):
        def prepare(self, *args, **kwargs):
            threads.append(psutil.Process().num_threads())
            value = super().prepare(*args, **kwargs)
            threads.append(psutil.Process().num_threads())
            return value

    segments = []

    class Plant(DynamicBicycle):
        physical_time = 0.0

        def step(self, state, control, dt):
            next_state = super().step(state, control, dt)
            segments.append(
                dict(
                    start=self.physical_time,
                    end=self.physical_time + dt,
                    dt=dt,
                    state_before=np.asarray(state).tolist(),
                    state_after=next_state.tolist(),
                    control=np.asarray(control).tolist(),
                )
            )
            self.physical_time += dt
            return next_state

    planner = Planner(controller, track)
    problem = controller.problem
    tracker = TrajectoryTracker(
        p, problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
    )
    timing = DiagnosticTiming(
        "replay", tuple(spec["planner"]), tuple([protocol["codriver_delay"]] * 256)
    )
    simulation = AsyncConfig(
        duration=protocol["duration"],
        latency_mode="injected",
        codriver_delay=protocol["codriver_delay"],
        fixed_handoff_offset=spec["offset"],
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
    plant = Plant(p, track, tire_physics=RACING_TIRE_PHYSICS)
    wall, cpu = perf_counter(), process_time()
    result = AsyncRunner(
        plant, planner, tracker, track, simulation, timing=timing, release_observer=releases.append
    ).run(initial)
    wall, cpu = perf_counter() - wall, process_time() - cpu
    write(args.output / "raw.json", result)
    write(args.output / "segments.json", segments)
    write(args.output / "release_contexts.json", [asdict(r) for r in releases])
    matches = []
    for r in releases:
        buffer = TrajectoryBuffer()
        buffer.active = r.packet
        local = TrajectoryTracker(r.parameters, r.lower, r.upper, r.tracker_config)
        local.previous = np.array(r.prefix.applied_control)
        try:
            x, u = planner.predictor.predict(
                r.state, r.prefix.release_time, r.estimated_delay, buffer, local
            )
            event = next(e for e in result["plans"] if e["plan_id"] == r.plan_id)
            matches.append(
                x.tolist() == event["predicted_state"]
                and u.tolist() == event["predicted_previous_control"]
            )
        except ValueError:
            matches.append(False)
    physical = physical_metrics(result, track)
    issues = chronology(result)
    if spec["offset"] is not None:
        for cycle in result["fixed_handoffs"]:
            if (
                cycle["t_accept"] is not None
                and abs(cycle["t_accept"] - cycle["valid_from"]) > 1e-10
            ):
                issues.append(dict(kind="fixed_acceptance_timestamp", plan_id=cycle["plan_id"]))
            if cycle["status"] == "missed" and any(
                h["accepted"] and h["plan_id"] == cycle["plan_id"] for h in result["handoffs"]
            ):
                issues.append(dict(kind="late_packet_authority", plan_id=cycle["plan_id"]))
    gates = stop_reasons(result, physical, issues)
    if not all(matches):
        gates.append("release_context_A_forecast_mismatch")
    files = (
        sorted(Path("src").rglob("*.py"))
        + sorted(Path("scripts/task007dc").glob("*.py"))
        + [Path("scripts/run_task007dc.py"), Path("docs/task007d/c/amended/protocol.json")]
    )
    summary = dict(
        case=args.case,
        spec=spec,
        configuration=asdict(config),
        simulation=asdict(simulation),
        timing=asdict(timing),
        initial_state=initial,
        fixture=str(fixture),
        fixture_sha256={
            str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in fixture.glob("*")
            if f.is_file()
        },
        vehicle_sha256=hashlib.sha256(vehicle_path.read_bytes()).hexdigest(),
        source_sha256={str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
        git_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        native=native,
        threadpools=threadpool_info(),
        observed_process_thread_counts=sorted(set(threads)),
        wall_seconds=wall,
        cpu_seconds=cpu,
        platform=platform.platform(),
        active_A_forecast_exact_matches=sum(matches),
        release_count=len(releases),
        physical=physical,
        chronology_issues=issues,
        stop_gate=gates,
    )
    write(args.output / "summary.json", summary)
    print(json.dumps(dict(case=args.case, stop_gate=gates)))
    return bool(gates)
