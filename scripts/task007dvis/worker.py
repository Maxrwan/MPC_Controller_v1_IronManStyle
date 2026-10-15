"""Frozen CX construction with VIS-only duration, lap gates and offline exports."""

import importlib.metadata
import json
import platform
import resource
import subprocess
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, process_time

import numpy as np
import psutil
from task007dcx.worker import FIXTURE, VEHICLE, RecordedPlant, frozen_config, geometry
from threadpoolctl import threadpool_info

from apex.control.mpc.controller import make_mpc
from apex.control.trajectory.packet import TrajectoryBuffer
from apex.control.trajectory.planner import TrajectoryPlanner
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.simulation.asynchronous import AsyncRunner
from task007dvis.analysis import analyze
from task007dvis.export import export, hashes, write
from task007dvis.parity import applicability, compare
from task007dvis.protocol import availability, source_hashes
from task007dvis.validation import validate


def run(case, folder, native):
    track, reference, p = geometry()
    config = frozen_config()
    sim, timing = availability(case)
    baseline = json.loads(Path("docs/task007d/c/amended/tables_v2/provenance.json").read_text())[
        "C1_steady"
    ]
    assert asdict(config) == baseline["configuration"]
    assert reference.manifest["aggression_factor"] == 2.0
    compatible = None
    if case.phase == "parity":
        compatible = applicability(case, asdict(config), asdict(sim), FIXTURE, VEHICLE)
        write(folder / "applicability.json", compatible)
        if not compatible["passed"]:
            raise ValueError("Historical C3 applicability gate failed")
    source = source_hashes()
    write(
        folder / "input_configuration.json",
        dict(
            case=asdict(case),
            configuration=asdict(config),
            simulation=asdict(sim),
            timing=None if timing is None else asdict(timing),
            source_sha256=source,
        ),
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
    ref = reference.sample(1.0)
    initial = [
        ref["v_ref_mps"],
        0.0,
        ref["v_ref_mps"] * ref["kappa_ref_1pm"],
        ref["e_psi_ref_rad"],
        1.0,
        ref["e_y_ref_m"],
    ]
    plant = RecordedPlant(p, track, tire_physics=RACING_TIRE_PHYSICS)
    releases = []
    wall, cpu = perf_counter(), process_time()
    raw = AsyncRunner(
        plant, planner, tracker, track, sim, timing=timing, release_observer=releases.append
    ).run(initial)
    wall, cpu = perf_counter() - wall, process_time() - cpu
    # Measurements finished. Preserve raw output BEFORE offline analysis or parity assertions.
    write(folder / "raw.json", raw)
    write(folder / "segments.json", plant.segments)
    write(folder / "release_contexts.json", [asdict(r) for r in releases])
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
    summary = dict(
        case=case.name,
        spec=asdict(case),
        configuration=asdict(config),
        simulation=asdict(sim),
        tracker_configuration=asdict(tracker.config),
        initial_state=initial,
        fixture=str(FIXTURE),
        fixture_sha256=hashes(FIXTURE.glob("*")),
        vehicle_sha256=hashes([VEHICLE])[str(VEHICLE)],
        source_sha256=source,
        git_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        dirty_status=subprocess.check_output(["git", "status", "--short"], text=True),
        native=native,
        threadpools=threadpool_info(),
        observed_process_thread_counts=sorted(set(threads)),
        wall_seconds=wall,
        cpu_seconds=cpu,
        platform=platform.platform(),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        packages={
            n: importlib.metadata.version(n)
            for n in ["numpy", "scipy", "casadi", "psutil", "threadpoolctl"]
        },
        release_count=len(releases),
        active_A_forecast_exact_matches=sum(matches),
        seed=None,
    )
    if case.phase == "parity":
        summary["parity"] = compare(case, raw, plant.segments)
        write(folder / "parity.json", summary["parity"])
    try:
        report, rows, cycles = analyze(
            raw, plant.segments, plant, reference, case, matches, threads
        )
        if case.phase == "parity" and not summary["parity"]["passed"]:
            report["stop_gate"].append("historical_C3_parity_failed")
        summary.update(physical=report["physical"], stop_gate=report["stop_gate"])
        write(folder / "analysis.json", report)
        export(folder, raw, plant.segments, rows, cycles, report, summary, FIXTURE)
        summary["export_validation"] = validate(folder / "scientific")
    except (ValueError, KeyError, IndexError, AssertionError) as error:
        summary.update(
            stop_gate=["offline_analysis_or_coverage_failure"], analysis_failure=repr(error)
        )
    summary["source_unchanged_during_worker"] = source == source_hashes()
    if not summary["source_unchanged_during_worker"]:
        summary["stop_gate"].append("source_changed_during_worker")
    write(folder / "summary.json", summary)
    print(json.dumps(dict(case=case.name, stop_gate=summary["stop_gate"], wall_seconds=wall)))
    return bool(summary["stop_gate"])
