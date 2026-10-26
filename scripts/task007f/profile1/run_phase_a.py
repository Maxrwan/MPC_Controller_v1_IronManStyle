"""One explicitly selected G2 worker. G1 authors this code; G2 execution is unauthorized.

Module import is stdlib-only. No automatic campaign, Phase B, warm-history capture or solver tuning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = "configs/performance/apex_performance_synthetic_v1.json"
MANIFEST_SHA256 = "5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf"
REFERENCE = "eaa0a3398515a21f30a850de59a0b44c775fad4d"


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--efficiency-instrumentation", choices=("off", "profile1-v1"), default="off"
    )
    parser.add_argument("--fixture", choices=("C0", "C1", "M0", "clock_probe"), default="C0")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--reviewed-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clock-allowance", type=Path)
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    return parser


def _git(root, *args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(root), *args])


def _write_new(path, value):
    # Numerical raw output is preserved independently of optional sidecar export.
    partial = path.with_name(path.name + ".partial")
    if path.exists():
        raise FileExistsError("Refusing to replace an existing artifact")
    with partial.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, allow_nan=False, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


@contextmanager
def _span(recorder, name, parent):
    """Called only inside an explicit ON arm; no context allocation on OFF paths."""
    token = recorder.span_begin(recorder.active_call, name, expected_parent=parent)
    try:
        yield
    except BaseException as error:
        recorder.span_end(
            token,
            exit="exception",
            exception_type=type(error).__module__ + "." + type(error).__qualname__,
        )
        raise
    else:
        recorder.span_end(token, exit="complete")


def _fresh(root, revision):
    if any(
        name == prefix or name.startswith(prefix + ".")
        for name in sys.modules
        for prefix in ("numpy", "scipy", "casadi", "apex.control", "apex.simulation")
    ):
        raise ValueError("A fresh child before numerical imports is required")
    if _git(root, "rev-parse", "HEAD").decode().strip() != revision:
        raise ValueError("Source differs from exact reviewed revision")
    if _git(root, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("Reviewed source checkout must be clean")
    if hashlib.sha256((root / MANIFEST).read_bytes()).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Accepted manifest changed")


def _construct(recorder):
    # Imported only in a fresh SINGLE child, after mode/revision/guard checks.
    from task007dcx.worker import frozen_config, geometry

    from apex.control.mpc.controller import make_mpc
    from apex.control.trajectory.planner import TrajectoryPlanner
    from apex.control.trajectory.tracker import TrajectoryTracker
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle

    if recorder is None:
        track, reference, parameters = geometry()
        config = frozen_config()
        controller = make_mpc(
            parameters,
            track,
            config=config,
            speed_reference=reference,
            racing_reference=reference,
            solver_options={"ipopt.warm_start_init_point": "yes"},
            warm_start=True,
        )
        planner = TrajectoryPlanner(controller, track)
    else:
        with _span(recorder, "fixture_load", "construction_full"):
            track, reference, parameters = geometry()
            config = frozen_config()
        controller = make_mpc(
            parameters,
            track,
            config=config,
            speed_reference=reference,
            racing_reference=reference,
            solver_options={"ipopt.warm_start_init_point": "yes"},
            warm_start=True,
            recorder=recorder,
        )
        with _span(recorder, "planner_construction", "construction_full"):
            planner = TrajectoryPlanner(controller, track, recorder=recorder)
    problem = controller.problem
    tracker = TrajectoryTracker(
        parameters,
        problem.lbx[problem.nx : problem.nx + 2],
        problem.ubx[problem.nx : problem.nx + 2],
    )
    plant = DynamicBicycle(parameters, track, tire_physics=RACING_TIRE_PHYSICS)
    return track, reference, planner, tracker, plant


def _worker(args):
    _fresh(args.source_root, args.reviewed_revision)
    guard = args.output / "MEASURED_ACTIVE"
    if (
        args.output.is_symlink()
        or not guard.is_file()
        or json.loads(guard.read_text()).get("owner_pid") != os.getppid()
    ):
        raise ValueError("Worker requires its live parent's exclusively owned output guard")
    if args.fixture == "clock_probe":
        return _clock_worker(args)  # Stdlib-only child; no native/backend initialization.
    from threading_study.config import configure_accelerate

    native = configure_accelerate(1)  # Native supported API, before NumPy/SciPy/CasADi imports.
    recorder = None
    allowance = None
    if args.efficiency_instrumentation == "profile1-v1":
        from task007f.profile1.recorder import (
            ClockAllowance,
            RecorderLimits,
            WorkerIdentity,
            create_recorder,
            write_sidecar,
        )

        if args.clock_allowance is None:
            raise ValueError("Numerical ON worker requires a separately reviewed clock allowance")
        allowance = ClockAllowance(**json.loads(args.clock_allowance.read_text()))
        if (
            not isinstance(allowance.provenance, str)
            or not allowance.provenance
            or len(allowance.provenance.encode("utf-8")) > 2048
            or any(type(v) is not int or v < 0 for v in (allowance.wall_ns, allowance.cpu_ns))
        ):
            raise ValueError("Reviewed wall/CPU allowance and provenance required")
        _write_new(
            args.output / "clock_allowance_input.json",
            {
                "sha256": hashlib.sha256(args.clock_allowance.read_bytes()).hexdigest(),
                "values": vars(allowance),
            },
        )
        identity = WorkerIdentity(
            args.output.name,
            os.getpid(),
            REFERENCE,
            args.reviewed_revision,
            hashlib.sha256(
                _git(args.source_root, "diff", "--binary", REFERENCE, "HEAD")
            ).hexdigest(),
            MANIFEST_SHA256,
        )
        recorder = create_recorder(
            mode=args.efficiency_instrumentation, identity=identity, limits=RecorderLimits()
        )
    raw, runner, original_exception, output_error = None, None, None, None
    try:
        if recorder is None:
            track, reference, planner, tracker, plant = _construct(None)
        else:
            call = recorder.begin_call(
                kind="construction", plan_id=None, release_sim_s=None, estimate_sim_s=None
            )
            try:
                with _span(recorder, "construction_full", None):
                    track, reference, planner, tracker, plant = _construct(recorder)
            except BaseException as error:
                recorder.finish_call(
                    call,
                    outcome={
                        "kind": "raised",
                        "existing_status": None,
                        "solver_attempted": None,
                        "exception_type": type(error).__module__ + "." + type(error).__qualname__,
                    },
                )
                raise
            else:
                recorder.finish_call(
                    call,
                    outcome={
                        "kind": "not_applicable",
                        "existing_status": None,
                        "solver_attempted": None,
                        "exception_type": None,
                    },
                )
        import psutil
        from threadpoolctl import threadpool_info

        from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

        observed_threads = psutil.Process().num_threads()
        case = args.fixture
        config = AsyncConfig(
            duration=0.24,
            laps=2,
            latency_mode="zero" if case == "C0" else "injected" if case == "C1" else "measured",
            injected_delay=0.06 if case == "C1" else 0.0,
            codriver_delay=0.025 if case == "C1" else 0.005 if case == "M0" else 0.0,
        )
        initial = json.loads(
            (
                args.source_root / "docs/task007d/vis/vis1l/evidence/controlled_A/summary.json"
            ).read_text()
        )["initial_state"]
        if recorder is None:
            runner = AsyncRunner(plant, planner, tracker, track, config)
        else:
            runner = AsyncRunner(plant, planner, tracker, track, config, recorder=recorder)
        raw = runner.run(initial)
        _write_new(args.output / "raw.json", raw)
        # Preserve a returned tuple even if observer-invalid startup prevented
        # publication/authority.
        prepared = getattr(runner, "_instrumentation_last_preparation", None)
        if prepared is not None and raw.get("stop_reason") == "instrumentation_stop":
            packet, event = prepared
            _write_new(
                args.output / "original_preparation.json",
                {
                    "packet": None if packet is None else packet.as_dict(),
                    "event": event,
                },
            )
        _write_new(
            args.output / "provenance.json",
            {
                "source_revision": args.reviewed_revision,
                "source_root": str(args.source_root),
                "fixture": case,
                "mode": args.efficiency_instrumentation,
                "native": native,
                "process_threads_before_run": observed_threads,
                "process_threads_after_run": psutil.Process().num_threads(),
                "threadpools": threadpool_info(),
                "rss_sample_bytes": psutil.Process().memory_info().rss,
                "rss_limitation": (
                    "Worker RSS sample, not an internally measured peak; parent samples separately"
                ),
                "timing_consumer": "unchanged legacy planner_total_time",
                "construction_exclusions": (
                    "imports/native setup/recorder creation; retained in parent "
                    "worker resource observations"
                ),
            },
        )
    except BaseException as error:
        if raw is None:
            original_exception = error
        else:
            output_error = error
    finally:
        if recorder is not None:
            try:
                recorder.reconcile(clock_allowance_ns=allowance)
                sealed = recorder.seal(
                    legacy_result=raw,
                    termination=(
                        "raised"
                        if original_exception is not None
                        else str(raw.get("stop_reason"))
                        if raw
                        else "no_raw_return"
                    ),
                )
                export = write_sidecar(sealed, output_dir=args.output)
                _write_new(args.output / "sidecar_export.json", export)
            except Exception as export_error:
                try:
                    _write_new(
                        args.output / "sidecar_export_failure.json",
                        {"exception_type": type(export_error).__name__},
                    )
                except Exception:
                    pass  # Best effort only; never replace the original numerical exception.
                if original_exception is None:
                    return 3
    if original_exception is not None:
        raise original_exception.with_traceback(original_exception.__traceback__)
    if output_error is not None:
        return 3
    if recorder is not None and (recorder.stop_requested() or not export["complete"]):
        return 3
    if recorder is not None and sealed.payload["observer_validity"] != "valid":
        return 3
    return (
        4
        if raw is None or raw.get("failure") or raw.get("stop_reason") == "instrumentation_stop"
        else 0
    )


def _clock_worker(args):
    if args.efficiency_instrumentation != "profile1-v1":
        raise ValueError("Clock-only probe requires explicit profile1-v1")
    from task007f.profile1.recorder import (
        RecorderLimits,
        WorkerIdentity,
        create_recorder,
        write_sidecar,
    )

    identity = WorkerIdentity(
        args.output.name,
        os.getpid(),
        REFERENCE,
        args.reviewed_revision,
        hashlib.sha256(_git(args.source_root, "diff", "--binary", REFERENCE, "HEAD")).hexdigest(),
        MANIFEST_SHA256,
    )
    recorder = create_recorder(mode="profile1-v1", identity=identity, limits=RecorderLimits())
    _write_new(
        args.output / "clock_metadata.json",
        {name: vars(time.get_clock_info(name)) for name in ("perf_counter", "process_time")},
    )
    call = recorder.begin_call(
        kind="clock_probe", plan_id=None, release_sim_s=None, estimate_sim_s=None
    )
    for _ in range(1000):
        token = recorder.span_begin(call, "clock_empty", expected_parent=None)
        recorder.span_end(token, exit="complete")
        if recorder.stop_requested():
            break
    if not recorder.stop_requested():
        for _ in range(1000):
            parent = recorder.span_begin(call, "clock_parent", expected_parent=None)
            child = recorder.span_begin(call, "clock_child", expected_parent="clock_parent")
            recorder.span_end(child, exit="complete")
            recorder.span_end(parent, exit="complete")
            if recorder.stop_requested():
                break
    recorder.finish_call(
        call,
        outcome=dict(
            kind="not_applicable", existing_status=None, solver_attempted=None, exception_type=None
        ),
    )
    recorder.reconcile()  # This raw probe cannot approve its own empirical allowance.
    sidecar = recorder.seal(legacy_result=None, termination="clock_probe_only")
    export = write_sidecar(sidecar, output_dir=args.output)
    _write_new(args.output / "sidecar_export.json", export)
    spans, calls = sidecar.payload["spans"], sidecar.payload["calls"]
    _write_new(
        args.output / "clock_probe_counts.json",
        {
            "spans_begun": len(spans),
            "spans_closed": sum(s["end_sequence"] is not None for s in spans),
            "sampled_wall_endpoints": sum(
                s[k] is not None for s in (*spans, *calls) for k in ("wall_start_ns", "wall_end_ns")
            ),
            "sampled_cpu_endpoints": sum(
                s[k] is not None for s in (*spans, *calls) for k in ("cpu_start_ns", "cpu_end_ns")
            ),
            "policy": (
                "Retain every raw slot; no automatic tolerance, correction or "
                "numerical continuation"
            ),
        },
    )
    return 3 if recorder.stop_requested() or not export["complete"] else 0


def _parent(args, argv):
    import psutil
    from threading_study.config import environment

    if (
        any(ROOT.glob("results/**/MEASURED_ACTIVE"))
        or (ROOT / "results/task007d/D3_ACTIVE").exists()
    ):
        raise ValueError("Existing measurement guard requires owner review")
    workloads = (
        "run_phase_a",
        "pytest",
        "run_mpc_threading_study",
        "task007dvis",
        "task007dcx",
        "task007d.worker",
        "run_async_planner_tracker",
    )
    if any(
        any(label in " ".join(p.info.get("cmdline") or ()) for label in workloads)
        for p in psutil.process_iter(["pid", "cmdline"])
        if p.info["pid"] not in (os.getpid(), os.getppid())
    ):
        raise ValueError("Another Phase A worker is active")
    if not args.output.parent.is_dir() or args.output.is_symlink():
        raise ValueError("Existing parent and a fresh output path required")
    free = os.statvfs(args.output.parent)
    if free.f_bavail * free.f_frsize < 2 * 2**30:
        raise ValueError("1 GiB remaining floor plus 1 GiB output headroom required")
    args.output.mkdir(exist_ok=False)
    guard = args.output / "MEASURED_ACTIVE"
    _write_new(guard, {"owner_pid": os.getpid(), "fixture": args.fixture})
    env = environment(1)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(args.source_root / "scripts"), str(args.source_root / "src"), str(ROOT / "scripts"))
    )
    command = [sys.executable, str(Path(__file__).resolve()), *argv, "--_worker"]
    observations, failure, process = [], None, None
    start = time.monotonic()
    try:
        with (args.output / "worker.log").open("xb") as log:
            process = subprocess.Popen(
                command, cwd=args.source_root, env=env, stdout=log, stderr=subprocess.STDOUT
            )
            monitor = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    rss = monitor.memory_info().rss
                    cpu = monitor.cpu_times()
                    observations.append(
                        {
                            "elapsed_s": time.monotonic() - start,
                            "rss_bytes": rss,
                            "threads": monitor.num_threads(),
                            "cpu_user_s": cpu.user,
                            "cpu_system_s": cpu.system,
                        }
                    )
                    space = os.statvfs(args.output)
                    output_bytes = sum(
                        p.stat().st_size for p in args.output.rglob("*") if p.is_file()
                    )
                    if (
                        rss > 2**30
                        or time.monotonic() - start > 30
                        or output_bytes > 2**30
                        or space.f_bavail * space.f_frsize < 2**30
                    ):
                        failure = "resource_or_worker_timeout"
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        break
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.1)
            result = process.wait()
        _write_new(
            args.output / "parent_exit.json",
            {
                "exit_code": result,
                "failure": failure,
                "monitor": observations,
                "monitor_policy": (
                    "Sequential child; parent 10 Hz RSS/thread observations are "
                    "outside preparation kernels"
                ),
                "measurement_limits": (
                    "No target-hardware timing, full software latency, hidden rerun "
                    "or Phase B evidence claim"
                ),
            },
        )
        return 3 if failure else result
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        # Remove only this process's own guard after its child has finished; unknown guards are
        # untouched.
        if guard.is_file() and json.loads(guard.read_text()).get("owner_pid") == os.getpid():
            guard.unlink()


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(values)  # Unsupported mode rejects before all numerical imports.
    args.source_root, args.output = args.source_root.resolve(), args.output.absolute()
    # A script invocation needs the existing startup-only configuration module on its path.
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(args.source_root / "scripts"))
    if args._worker:
        return _worker(args)  # Original escaping numerical exception keeps its traceback.
    try:
        return _parent(args, values)
    except (ValueError, OSError) as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
