"""One fresh numerical process per window; all source mathematics remain delegated."""

import csv
import importlib.metadata
import json
import os
import platform
import sys
import time
import tomllib
import traceback
from pathlib import Path

from common import ROOT, THREAD_ENV, clean, verify_sources, write


def run(output, scenario, self_check=False):
    started, cpu = time.perf_counter(), time.process_time()
    for key, value in THREAD_ENV.items():
        if os.environ.get(key) != value:
            raise ValueError("Fresh single-thread bootstrap required: " + key)
    verify_sources()
    if sys.version_info[:3] != (3, 12, 14):
        raise ValueError("Expected locked Python 3.12.14")
    locked = tomllib.loads((ROOT / "vendor/uv.lock").read_text())
    for package in locked["package"]:
        if package["name"] in {
            "numpy",
            "scipy",
            "casadi",
            "pandas",
            "pyyaml",
            "psutil",
            "threadpoolctl",
            "python-dateutil",
            "six",
        }:
            if importlib.metadata.version(package["name"]) != package["version"]:
                raise ValueError("Locked dependency mismatch: " + package["name"])
    sys.path.insert(0, str(ROOT / "vendor/src"))
    import numpy as np
    from runtime import compose
    from threadpoolctl import threadpool_info, threadpool_limits

    from apex.control.trajectory.tracker import TrajectoryTracker
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

    plans, updates, steps = [], [], []
    journal = (output / "progress.jsonl").open("x", buffering=1)

    def event(value):
        journal.write(json.dumps(clean(value), allow_nan=False) + "\n")

    class Tracker(TrajectoryTracker):
        def update(self, state, buffer, when):
            begin = time.perf_counter()
            try:
                result = super().update(state, buffer, when)
            except Exception as error:
                elapsed = time.perf_counter() - begin
                updates.append(
                    {
                        "time": when,
                        "plan_id": buffer.active_plan_id,
                        "update_wall_s": elapsed,
                        "success": False,
                        "exception": repr(error),
                    }
                )
                raise
            elapsed = time.perf_counter() - begin
            updates.append(
                {
                    "time": when,
                    "plan_id": buffer.active_plan_id,
                    "update_wall_s": elapsed,
                    "kernel_time": result[1]["total_time"],
                    "success": True,
                }
            )
            return result

    class Plant(DynamicBicycle):
        simulated_time = 0.0

        def step(self, state, control, dt=None):
            begin = time.perf_counter()
            result = super().step(state, control, dt)
            elapsed = time.perf_counter() - begin
            self.simulated_time += dt
            steps.append({"end_time": self.simulated_time, "step_wall_s": elapsed})
            return result

    result = None
    failure = None
    snapshot = None
    pools_before, pools_after = [], []
    native_imports = {}
    # Enforce supported loaded BLAS controls, in addition to pre-import environment.
    with threadpool_limits(limits=1):
        construction = time.perf_counter()
        controller, delegate, tracker, track, snapshot = compose(Tracker)
        construction = time.perf_counter() - construction
        pools_before = threadpool_info()
        write(output / "resolved_configuration.json", snapshot)
        solver = controller.solver

        class Solver:
            latest = None

            def solve(self, request):
                self.latest = None
                answer = solver.solve(request)
                self.latest = {
                    **answer.statistics,
                    "success": bool(answer.success),
                    "status": answer.status,
                }
                return answer

        observed_solver = Solver()
        controller.solver = observed_solver

        class Planner:
            def prepare(self, plan_id, state, when, estimate, buffer, active_tracker, **kwargs):
                observed_solver.latest = None
                event(
                    {
                        "event": "prepare_begin",
                        "plan_id": plan_id,
                        "release_time": when,
                        "source_state": state,
                        "startup": kwargs.get("startup", False),
                        "monotonic_s": time.perf_counter(),
                    }
                )
                begin = time.perf_counter()
                try:
                    packet, diagnostic = delegate.prepare(
                        plan_id, state, when, estimate, buffer, active_tracker, **kwargs
                    )
                except Exception as error:
                    elapsed = time.perf_counter() - begin
                    row = {
                        "plan_id": plan_id,
                        "release_time": when,
                        "startup": kwargs.get("startup", False),
                        "source_s_abs_m": float(state[4]),
                        "source_s_track_m": float(state[4] % track.length),
                        "prepare_wall_s": elapsed,
                        "exception": repr(error),
                        "solver": observed_solver.latest,
                        "success": False,
                        "solver_success": (observed_solver.latest or {}).get("success"),
                    }
                    plans.append(row)
                    event({"event": "prepare_end", **row})
                    raise
                elapsed = time.perf_counter() - begin
                row = {
                    **diagnostic,
                    "startup": kwargs.get("startup", False),
                    "source_s_abs_m": float(state[4]),
                    "source_s_track_m": float(state[4] % track.length),
                    "prepare_wall_s": elapsed,
                    "packet_prepared": packet is not None,
                    "solver": observed_solver.latest,
                    "solver_success": (observed_solver.latest or {}).get("success"),
                    "controller_success": controller.diagnostics().get("success")
                    if observed_solver.latest is not None
                    else None,
                }
                plans.append(row)
                event({"event": "prepare_end", **row})
                return packet, diagnostic

        plant = Plant(controller.parameters, track, tire_physics=RACING_TIRE_PHYSICS)
        initial = np.asarray(scenario["initial_state"], dtype=float)
        plant.diagnostics(initial, scenario["initial_validation_control"])
        config = AsyncConfig(
            duration=2.0,
            laps=2,
            latency_mode="measured",
            codriver_delay=None,
            injected_delay=0.0,
            spike_plan_id=-1,
            failed_plan_ids=(),
            committed_prefix_prediction=False,
            fixed_handoff_offset=None,
        )
        write(output / "scenario.json", {**scenario, "simulation": config.__dict__})
        loop_start, loop_cpu = time.perf_counter(), time.process_time()
        try:
            runner = AsyncRunner(plant, Planner(), tracker, track, config)
            if self_check:
                packet, diagnostic = runner.planner.prepare(
                    0, initial, 0.0, 0.0, runner.buffer, tracker, startup=True
                )
                if packet is None:
                    raise RuntimeError("Real controller startup failed: " + str(diagnostic))
                accepted, reason = runner.buffer.insert(packet, 0.0)
                if not accepted:
                    raise RuntimeError("Startup packet rejected: " + reason)
                tracker.previous = packet.controls[0].copy()
                expected, _ = tracker.clone().update(initial, runner.buffer, 0.0)
                command, _ = tracker.update(initial, runner.buffer, 0.0)
                if not np.array_equal(expected, command):
                    raise RuntimeError("Tracker observation changed the command")
                plant.diagnostics(initial, command)
                result = {
                    "stop_reason": "self_check_complete",
                    "failure": None,
                    "end_time": 0.0,
                    "controls": [],
                    "plans": plans,
                    "states": [],
                }
            else:
                result = runner.run(initial)
        except Exception:
            failure = traceback.format_exc()
        loop_wall, loop_process_cpu = (
            time.perf_counter() - loop_start,
            time.process_time() - loop_cpu,
        )
        pools_after = threadpool_info()
        # Resolve identities after execution; do not hash modules inside timed calls.
        import hashlib

        for name, module in tuple(sys.modules.items()):
            path = getattr(module, "__file__", None)
            if name.startswith("apex") and path:
                native_imports[name] = {
                    "path": str(path),
                    "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                }
    journal.close()
    write(output / "raw_simulation.json", result)
    write(output / "plans.json", plans)
    write(output / "tracker.json", updates)
    write(output / "plant_steps.json", steps)
    fields = [
        "plan_id",
        "release_time",
        "source_s_abs_m",
        "source_s_track_m",
        "startup",
        "warm_start",
        "solver_attempted",
        "solve_time",
        "iterations",
        "success",
        "solver_success",
        "controller_success",
        "primal_infeasibility",
        "max_slack",
        "slack_sum",
        "status",
        "preparation",
        "packet_prepared",
        "planner_total_time",
        "prepare_wall_s",
        "planner_cpu_time",
    ]
    with (output / "plans.csv").open("x", newline="") as file:
        writer = csv.DictWriter(file, fields, extrasaction="ignore")
        writer.writeheader()
        for row in plans:
            writer.writerow(
                {
                    **row,
                    **{
                        key: value
                        for key, value in (row.get("solver") or {}).items()
                        if key in ("solve_time", "iterations", "primal_infeasibility")
                    },
                }
            )
    with (output / "tracker.csv").open("x", newline="") as file:
        writer = csv.DictWriter(
            file, ["time", "plan_id", "update_wall_s", "kernel_time", "success", "exception"]
        )
        writer.writeheader()
        writer.writerows(updates)
    controller_failure = any(
        not row.get("success") or not row.get("packet_prepared") for row in plans
    )
    incomplete = result is None or (
        not self_check
        and (result.get("stop_reason") != "duration" or result.get("end_time", 0) < 2.0 - 1e-9)
    )
    fallback = bool(result and result.get("fallbacks"))
    thread_mismatch = any(pool.get("num_threads") != 1 for pool in pools_before + pools_after)
    summary = {
        "status": "FAILED_OR_INCOMPLETE"
        if failure or controller_failure or incomplete or fallback or thread_mismatch
        else "COMPLETE",
        "exception": failure,
        "self_check": self_check,
        "stop_reason": None if result is None else result.get("stop_reason"),
        "simulation_failure": None if result is None else result.get("failure"),
        "end_simulated_time_s": plant.simulated_time,
        "startup_or_recurring_failures": controller_failure,
        "fallback_observed": fallback,
        "construction_wall_s": construction,
        "loop_wall_s": loop_wall,
        "loop_process_cpu_s": loop_process_cpu,
        "worker_wall_before_final_report_s": time.perf_counter() - started,
        "worker_process_cpu_s": time.process_time() - cpu,
        "plant_step_wall_s": sum(row["step_wall_s"] for row in steps),
        "python": sys.version,
        "machine": platform.machine(),
        "platform": platform.platform(),
        "os_release": platform.freedesktop_os_release() if sys.platform == "linux" else {},
        "packages": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "scipy", "casadi", "pandas", "PyYAML", "psutil", "threadpoolctl"]
        },
        "thread_environment": {key: os.environ.get(key) for key in THREAD_ENV},
        "pools_before": pools_before,
        "pools_after": pools_after,
        "thread_pool_mismatch": thread_mismatch,
        "native_libraries": sorted(
            {
                line.split()[-1]
                for line in Path("/proc/self/maps").read_text().splitlines()
                if ".so" in line and any(name in line for name in ("casadi", "numpy", "scipy"))
            }
        ),
        "apex_imports": native_imports,
        "timing_scope": "Measured controller calls; plant/setup/in-memory simulation "
        "recording and file logging excluded from solve/update timers. "
        "Planner includes lightweight solver-statistics capture.",
    }
    write(output / "worker_summary.json", summary)
    return 0 if summary["status"] == "COMPLETE" else 2
