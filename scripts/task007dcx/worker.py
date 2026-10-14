"""Frozen C construction, measured preparation availability, unchanged physical scheduler."""

import hashlib
import importlib.metadata
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

FIXTURE = Path("configs/planning/task007b/gamma_2p000")
VEHICLE = Path("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")


def hashes(files):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}


def geometry():
    track, _, identity = load_track(FIXTURE / "track_source.json")
    ref = PlanningReference(FIXTURE, track, identity, feasibility_policy="advisory")
    return track, ref, load_vehicle_parameters(VEHICLE)


def frozen_config():
    # Identical constructor arguments to the accepted task007dc.worker, no retuning.
    return MPCConfig(
        horizon=8,
        dt=0.1,
        substeps=4,
        costs=CostScales(lateral=2),
        tire_physics=RACING_TIRE_PHYSICS,
        tracker_margin=0.08,
        racing_reference=True,
        progress_weight=0,
    )


def availability(protocol, case):
    spec = protocol["cases"][case]
    sim = AsyncConfig(
        duration=protocol["duration"],
        latency_mode="measured" if spec["study"] == 2 else "injected",
        codriver_delay=protocol["codriver_delay"],
        fixed_handoff_offset=spec["offset"],
    )
    timing = (
        None
        if spec["study"] == 2
        else DiagnosticTiming(
            "replay", tuple(spec["planner"]), tuple([protocol["codriver_delay"]] * 256)
        )
    )
    return sim, timing


class RecordedPlant(DynamicBicycle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.segments = []
        self.physical_time = 0.0

    def step(self, state, control, dt):
        value = super().step(state, control, dt)
        self.segments.append(
            dict(
                start=self.physical_time,
                end=self.physical_time + dt,
                dt=dt,
                state_before=np.asarray(state).tolist(),
                state_after=value.tolist(),
                control=np.asarray(control).tolist(),
            )
        )
        self.physical_time += dt
        return value


def run(args, protocol, native):
    spec = protocol["cases"][args.case]
    track, reference, p = geometry()
    assert reference.manifest["aggression_factor"] == protocol["gamma"] == 2.0
    config = frozen_config()
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
        def prepare(self, *a, **kw):
            threads.append(psutil.Process().num_threads())
            value = super().prepare(*a, **kw)
            threads.append(psutil.Process().num_threads())
            return value

    planner = Planner(controller, track)
    problem = controller.problem
    tracker = TrajectoryTracker(
        p, problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
    )
    sim, timing = availability(protocol, args.case)
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
    plant = RecordedPlant(p, track, tire_physics=RACING_TIRE_PHYSICS)
    wall, cpu = perf_counter(), process_time()
    raw = AsyncRunner(
        plant, planner, tracker, track, sim, timing=timing, release_observer=releases.append
    ).run(initial)
    wall, cpu = perf_counter() - wall, process_time() - cpu
    # Measurement is over. Export and audit offline; no competing worker is launched here.
    write(args.output / "raw.json", raw)
    write(args.output / "segments.json", plant.segments)
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
            event = next(e for e in raw["plans"] if e["plan_id"] == r.plan_id)
            matches.append(
                x.tolist() == event["predicted_state"]
                and u.tolist() == event["predicted_previous_control"]
            )
        except ValueError:
            matches.append(False)
    physical = physical_metrics(raw, track)
    issues = chronology(raw)
    for cycle in raw.get("fixed_handoffs", []):
        if cycle["t_accept"] is not None and abs(cycle["t_accept"] - cycle["valid_from"]) > 1e-10:
            issues.append(dict(kind="fixed_acceptance_timestamp", plan_id=cycle["plan_id"]))
        if cycle["status"] == "missed" and any(
            h["accepted"] and h["plan_id"] == cycle["plan_id"] for h in raw["handoffs"]
        ):
            issues.append(dict(kind="late_packet_authority", plan_id=cycle["plan_id"]))
    gates = stop_reasons(raw, physical, issues)
    if physical.get("minimum_reserve", 0) <= 0:
        gates.append("reserve_exhaustion")
    if not all(matches):
        gates.append("release_context_A_forecast_mismatch")
    if sorted(set(threads)) != [1]:
        gates.append("native_thread_policy")
    files = (
        sorted(Path("src").rglob("*.py"))
        + sorted(Path("scripts/task007dcx").glob("*.py"))
        + sorted(Path("scripts/task007dc").glob("*.py"))
        + sorted(Path("scripts/task007d").glob("*.py"))
        + [
            Path("scripts/run_task007dcx.py"),
            Path("scripts/threading_study/config.py"),
            Path("docs/task007d/cx/protocol.json"),
            Path("pyproject.toml"),
            Path("uv.lock"),
        ]
    )
    summary = dict(
        case=args.case,
        spec=spec,
        configuration=asdict(config),
        simulation=asdict(sim),
        timing=None if timing is None else asdict(timing),
        initial_state=initial,
        fixture=str(FIXTURE),
        fixture_sha256=hashes(FIXTURE.glob("*")),
        vehicle_sha256=hashes([VEHICLE])[str(VEHICLE)],
        source_sha256=hashes(files),
        git_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        dirty_status=subprocess.check_output(["git", "status", "--short"], text=True),
        native=native,
        threadpools=threadpool_info(),
        observed_process_thread_counts=sorted(set(threads)),
        wall_seconds=wall,
        cpu_seconds=cpu,
        platform=platform.platform(),
        packages={
            n: importlib.metadata.version(n)
            for n in ["numpy", "scipy", "casadi", "psutil", "threadpoolctl"]
        },
        active_A_forecast_exact_matches=sum(matches),
        release_count=len(releases),
        physical=physical,
        chronology_issues=issues,
        stop_gate=gates,
    )
    write(args.output / "summary.json", summary)
    print(json.dumps(dict(case=args.case, stop_gate=gates, cpu_wall_ratio=cpu / wall)))
    return bool(gates)
