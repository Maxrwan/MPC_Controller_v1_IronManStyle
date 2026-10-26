"""UNEXECUTED G2 support. No test or worker is authorized by this file's existence.

Use explicit reviewed roots/revisions and allowance after Primary G2 approval. Dense
spies are test-only, equal across controlled builds, and never observer-cost evidence.
This module contains no automatic 44-worker campaign or historical warm reconstruction.
"""

import copy
import hashlib
import importlib.util
import json
import math
import os
import pickle
import struct
import subprocess
import sys
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FROZEN = "48adbdf64d492592d15e23c917aca71fa58aa8a5"
CONTRACT_PATH = ROOT / "docs/task007f/profile1/g1_parity_field_allowlist.json"
SYNTHETIC = {
    "S0": dict(duration=0.8, injected_delay=0.15, codriver_delay=0.0),
    "S1": dict(duration=0.8, injected_delay=0.025, codriver_delay=0.025),
    "S2": dict(
        duration=0.8, injected_delay=0.025, codriver_delay=0.005, spike_plan_id=3, spike_delay=0.15
    ),
    "S3": dict(duration=0.8, injected_delay=0.45, codriver_delay=0.0),
    "S4": dict(duration=0.24, injected_delay=0.06, codriver_delay=0.025),
}
OBSERVER_ORDERS = (
    ("B0", "B1", "B2"),
    ("B1", "B2", "B0"),
    ("B2", "B0", "B1"),
    ("B2", "B1", "B0"),
    ("B1", "B0", "B2"),
    ("B0", "B2", "B1"),
)


def _git(root, *args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(root), *args])


def _approved():
    """An explicit future protocol invocation; elapsed time never grants authorization."""
    revision = os.environ.get("APEX_PROFILE1_G2_REVIEWED_REVISION")
    allowance = os.environ.get("APEX_PROFILE1_G2_CLOCK_ALLOWANCE")
    baseline = os.environ.get("APEX_PROFILE1_B0_ROOT")
    if not revision or not allowance or not baseline:
        pytest.skip(
            "Separate G2 authorization, reviewed revision/allowance and pristine B0 root required"
        )
    assert _git(ROOT, "rev-parse", "HEAD").decode().strip() == revision
    assert not _git(ROOT, "status", "--porcelain")
    return revision, Path(allowance), Path(baseline)


def _matches(selector, path):
    """A star matches an ARRAY INDEX only, never an arbitrary object key."""
    parts = selector.lstrip("/").split("/")
    return len(parts) == len(path) and all(
        (part == "*" and type(value) is int) or (part != "*" and part == value)
        for part, value in zip(parts, path)
    )


def compare_controlled(left, right, *, tracker_dt=0.01):
    """Strict test envelope comparison. Return retained duration/host-flag differences."""
    import numpy as np

    contract = json.loads(CONTRACT_PATH.read_text())
    selectors = contract["clock_duration_leaf_paths_only"]
    assert len(selectors) == 98
    assert len(contract["individually_enumerated_IPOPT_timing_keys"]) == 14
    assert all("**" not in path for path in selectors)
    for envelope in (left, right):
        for row in envelope.get("raw", {}).get("controls", ()):
            assert type(row["computational_deadline_exceeded"]) is bool
            assert row["computational_deadline_exceeded"] == (row["total_time"] > tracker_dt)
    observations = []
    predicate = "/raw/controls/*/computational_deadline_exceeded"

    def visit(a, b, path=()):
        assert type(a) is type(b), (path, type(a), type(b))
        if isinstance(a, dict):
            assert list(a) == list(b), (path, "key set or order")
            for key in a:
                visit(a[key], b[key], (*path, key))
        elif isinstance(a, (tuple, list)):
            assert len(a) == len(b), (path, "length")
            for index, (av, bv) in enumerate(zip(a, b)):
                visit(av, bv, (*path, index))
        elif any(_matches(selector, path) for selector in selectors):
            if a is None or b is None:
                assert a is b, (path, "null branch")
            else:
                assert type(a) in (int, float) and math.isfinite(a) and a >= 0
                assert type(b) in (int, float) and math.isfinite(b) and b >= 0
            observations.append((path, a, b))
        elif _matches(predicate, path):
            if a != b:
                observations.append((path, a, b))
        elif isinstance(a, np.ndarray):
            assert a.dtype == b.dtype and a.shape == b.shape, path
            assert not a.dtype.hasobject, path
            assert a.tobytes(order="C") == b.tobytes(order="C"), path
        elif isinstance(a, float):
            assert struct.pack("!d", a) == struct.pack("!d", b), (path, a, b)
        else:
            assert a == b, (path, a, b)

    visit(left, right)
    return observations


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _recorder(revision, allowance_path):
    api = _load(ROOT / "scripts/task007f/profile1/recorder.py", "profile1_g2_api")
    allowance = api.ClockAllowance(**json.loads(allowance_path.read_text()))
    assert isinstance(allowance.provenance, str) and allowance.provenance
    assert len(allowance.provenance.encode("utf-8")) <= 2048
    assert all(type(v) is int and v >= 0 for v in (allowance.wall_ns, allowance.cpu_ns))
    identity = api.WorkerIdentity(
        "g2",
        os.getpid(),
        api.REFERENCE_REVISION,
        revision,
        hashlib.sha256(_git(ROOT, "diff", "--binary", api.REFERENCE_REVISION, "HEAD")).hexdigest(),
        api.MANIFEST_SHA256,
    )
    return (
        api,
        api.create_recorder(mode="profile1-v1", identity=identity, limits=api.RecorderLimits()),
        allowance,
    )


class BoundedRows(list):
    """Test-only slots; overflow stops the attempt rather than dropping a trace."""

    def __init__(self, limit):
        super().__init__()
        self.limit = limit

    def append(self, value):
        if len(self) >= self.limit:
            raise ValueError("Test-only snapshot slot capacity")
        super().append(value)


def _snap(value):
    return copy.deepcopy(asdict(value) if is_dataclass(value) else value)


def _dense_spies(planner, plant, calls, rk4):
    """Instance-local observation of ACTUAL calls only; no extra evaluate/step/solve."""
    controller = planner.controller
    original_prepare, original_solve = planner.prepare, controller.solver.solve
    current = [None]

    def solve(request):
        current[0]["solver_request"] = dict(
            initial=_snap(request.initial),
            parameters=_snap(request.parameters),
            bounds={
                name: _snap(getattr(controller.problem, name))
                for name in ("lbx", "ubx", "lbg", "ubg")
            },
        )
        result = original_solve(request)
        current[0]["solver_result"] = _snap(result)
        return result

    def prepare(*args, **kwargs):
        row = dict(pre_control_solution=_snap(controller.solution))
        current[0] = row
        calls.append(row)
        try:
            packet, event = original_prepare(*args, **kwargs)
            row["packet_fields"] = (
                None
                if packet is None
                else {field.name: _snap(getattr(packet, field.name)) for field in fields(packet)}
            )
            row["return_event"] = _snap(event)
            return packet, event
        finally:
            row["post_control_solution"] = _snap(controller.solution)
            row["solver_last_statistics"] = _snap(controller.solver.last_statistics)
            row["controller_last_prediction"] = _snap(controller.last_prediction)
            row["controller_last_diagnostics"] = _snap(controller.last_diagnostics)

    planner.prepare, controller.solver.solve = prepare, solve
    _plant_spies(plant, rk4)
    original_predict_step = planner.predictor.step

    def predict_step(*args):
        row = dict(kind="predictor", inputs=_snap(args))
        rk4.append(row)
        answer = original_predict_step(
            *args
        )  # Actual endpoint + stage domains, no extra evaluation.
        row["endpoint_and_stage_domains"] = tuple(_snap(value.full()) for value in answer)
        return answer

    planner.predictor.step = predict_step


def _plant_spies(plant, rk4):
    original_step, original_derivative = plant.step, plant.derivative
    active_plant = [None]

    def derivative(state, control):
        answer = original_derivative(state, control)
        if active_plant[0] is not None:
            active_plant[0]["stages"].append(
                dict(state=_snap(state), control=_snap(control), derivative=_snap(answer))
            )
        return answer

    def step(state, control, dt=None):
        row = dict(kind="physical", state=_snap(state), control=_snap(control), dt=dt, stages=[])
        rk4.append(row)
        active_plant[0] = row
        try:
            result = original_step(state, control, dt)
            row["endpoint"] = _snap(result)
            row["valid"] = True
            return result
        except BaseException as error:
            row["exception_type"] = type(error).__qualname__
            raise
        finally:
            active_plant[0] = None

    plant.step, plant.derivative = step, derivative


def _synthetic(root, name):
    from apex.control.trajectory.tracker import TrajectoryTracker
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle

    fixtures = _load(root / "tests/conftest.py", "profile1_existing_fixtures")
    original = _load(root / "tests/unit/test_async_chronology.py", "profile1_existing_chronology")
    # Use the existing fixture bodies and StraightPlanner. No fabricated NMPC/dynamics.
    parameters = fixtures.dynamic_vehicle.__wrapped__()
    track = fixtures.straight_geometry.__wrapped__()
    return (
        track,
        original.StraightPlanner(),
        TrajectoryTracker(parameters, [-0.4, -2], [0.4, 2]),
        DynamicBicycle(parameters, track, tire_physics=RACING_TIRE_PHYSICS),
    )


def _case(root, name, recorder, *, dense):
    from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

    launcher = _load(ROOT / "scripts/task007f/profile1/run_phase_a.py", "profile1_g2_launcher")
    calls, rk4, construction = BoundedRows(64), BoundedRows(8192), {}
    if name in SYNTHETIC:
        track, planner, tracker, plant = _synthetic(root, name)
        initial = [2.0, 0, 0, 0, 0, 0]
        config = AsyncConfig(laps=2, latency_mode="injected", **SYNTHETIC[name])
        if dense:
            _plant_spies(plant, rk4)
    else:
        if recorder is None:
            track, reference, planner, tracker, plant = launcher._construct(None)
        else:
            call = recorder.begin_call(
                kind="construction", plan_id=None, release_sim_s=None, estimate_sim_s=None
            )
            with launcher._span(recorder, "construction_full", None):
                track, reference, planner, tracker, plant = launcher._construct(recorder)
            recorder.finish_call(
                call,
                outcome=dict(
                    kind="not_applicable",
                    existing_status=None,
                    solver_attempted=None,
                    exception_type=None,
                ),
            )
        construction = dict(
            problem_construction_seconds=planner.controller.problem.construction_seconds,
            solver_construction_seconds=planner.controller.solver.construction_seconds,
        )
        initial = json.loads(
            (root / "docs/task007d/vis/vis1l/evidence/controlled_A/summary.json").read_text()
        )["initial_state"]
        config = AsyncConfig(
            duration=0.24,
            laps=2,
            latency_mode="zero" if name == "C0" else "injected" if name == "C1" else "measured",
            injected_delay=0.06 if name == "C1" else 0.0,
            codriver_delay=0.025 if name == "C1" else 0.005 if name == "M0" else 0.0,
        )
        if dense:
            _dense_spies(planner, plant, calls, rk4)
    kwargs = {} if recorder is None else dict(recorder=recorder)
    raw = AsyncRunner(plant, planner, tracker, track, config, **kwargs).run(initial)
    return dict(construction=construction, calls=list(calls), raw=raw, rk4_trace=list(rk4))


def _worker(root, revision, mode, fixture, allowance_path, output, snapshot_fd, *, dense=True):
    """Fresh sequential process entry, invoked only by an explicitly approved future test."""
    sys.path[:0] = [str(root / "scripts"), str(root / "src")]
    from threading_study.config import configure_accelerate

    native = configure_accelerate(1)
    launcher = _load(ROOT / "scripts/task007f/profile1/run_phase_a.py", "profile1_fresh_launcher")
    launcher._fresh(root, revision)
    recorder = None
    if mode == "profile1-v1":
        api, recorder, allowance = _recorder(revision, allowance_path)
    envelope = _case(root, fixture, recorder, dense=dense)
    # Dense optimizer snapshots stay in RAM/IPC; never write a warm-history capture.
    launcher._write_new(output / "raw.json", envelope["raw"])
    message = pickle.dumps(envelope, protocol=5)
    if len(message) > 16777216:
        raise ValueError("Test-only IPC snapshot cap; preserve raw result and stop")
    with os.fdopen(snapshot_fd, "wb") as stream:
        stream.write(message)
    if recorder is not None:
        recorder.reconcile(clock_allowance_ns=allowance)
        sidecar = recorder.seal(
            legacy_result=envelope["raw"], termination=envelope["raw"]["stop_reason"]
        )
        assert api.write_sidecar(sidecar, output_dir=output)["complete"]
    import psutil
    from threadpoolctl import threadpool_info

    provenance = dict(
        revision=revision,
        mode=mode,
        native=native,
        threadpools=threadpool_info(),
        threads=psutil.Process().num_threads(),
        manifest=launcher.MANIFEST_SHA256,
        source_hashes={
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "src").rglob("*.py"))
        },
        numerical_versions={
            name: sys.modules[name].__version__ for name in ("numpy", "scipy", "casadi")
        },
    )
    (output / "provenance.json").write_text(json.dumps(provenance, sort_keys=True))


def run_build(tmp_path, build, fixture, *, dense=True):
    """One worker only; do not call concurrently. No retry or campaign loop."""
    reviewed, allowance, baseline = _approved()
    root = baseline if build == "B0" else ROOT
    revision = FROZEN if build == "B0" else reviewed
    assert _git(root, "rev-parse", "HEAD").decode().strip() == revision
    import psutil
    from threading_study.config import environment

    if (
        any(ROOT.glob("results/**/MEASURED_ACTIVE"))
        or (ROOT / "results/task007d/D3_ACTIVE").exists()
    ):
        pytest.fail("Existing owner guard")
    workloads = (
        "run_phase_a",
        "pytest",
        "run_mpc_threading_study",
        "task007dvis",
        "task007dcx",
        "task007d.worker",
        "run_async_planner_tracker",
    )
    assert not any(
        any(label in " ".join(p.info.get("cmdline") or ()) for label in workloads)
        for p in psutil.process_iter(["pid", "cmdline"])
        if p.info["pid"] not in (os.getpid(), os.getppid())
    ), "Concurrent workload"
    assert os.statvfs(tmp_path).f_bavail * os.statvfs(tmp_path).f_frsize >= 2 * 2**30
    output = tmp_path / (fixture + "-" + build)
    output.mkdir(exist_ok=False)
    mode = "profile1-v1" if build == "B2" else "off"
    read_fd, write_fd = os.pipe()
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--g2-worker",
        str(root),
        revision,
        mode,
        fixture,
        str(allowance),
        str(output),
        "dense" if dense else "minimal",
        str(write_fd),
    ]
    # IPC is a private inherited pipe. No pickle is read from persistent/untrusted files.
    import time

    samples, message = [], bytearray()
    process = None
    guard = ROOT / "results/task007f/profile1/MEASURED_ACTIVE"
    guard.parent.mkdir(parents=True, exist_ok=True)
    with guard.open("x") as stream:
        json.dump(dict(owner_pid=os.getpid()), stream)
    try:
        with (output / "worker.log").open("xb") as log:
            process = subprocess.Popen(
                command, cwd=root, env=environment(1), stdout=log, stderr=log, pass_fds=(write_fd,)
            )
            os.close(write_fd)
            write_fd = None
            os.set_blocking(read_fd, False)
            monitor, start = psutil.Process(process.pid), time.monotonic()
            eof = False
            while process.poll() is None or not eof:
                try:
                    while True:
                        data = os.read(read_fd, 65536)
                        if not data:
                            eof = True
                            break
                        message.extend(data)
                        assert len(message) <= 16777216, "Test-only IPC snapshot cap"
                except BlockingIOError:
                    pass
                try:
                    rss, cpu = monitor.memory_info().rss, monitor.cpu_times()
                    samples.append(
                        dict(
                            elapsed_s=time.monotonic() - start,
                            rss_bytes=rss,
                            threads=monitor.num_threads(),
                            cpu_user_s=cpu.user,
                            cpu_system_s=cpu.system,
                        )
                    )
                    space = os.statvfs(output)
                    output_bytes = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
                    assert (
                        rss <= 2**30
                        and output_bytes <= 2**30
                        and space.f_bavail * space.f_frsize >= 2**30
                    ), "G2 resource ceiling"
                except psutil.NoSuchProcess:
                    pass
                assert time.monotonic() - start <= 30, "G2 worker timeout; no retry"
                if process.poll() is None:
                    time.sleep(0.1)
            assert process.wait(timeout=2) == 0, str(output / "worker.log")
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)
        if guard.is_file() and json.loads(guard.read_text()).get("owner_pid") == os.getpid():
            guard.unlink()
        (output / "parent_resource_samples.json").write_text(json.dumps(samples))
    envelope = pickle.loads(message)
    provenance = json.loads((output / "provenance.json").read_text())
    assert provenance["revision"] == revision and provenance["mode"] == mode
    for path, digest in provenance["source_hashes"].items():
        assert digest == hashlib.sha256(_git(root, "show", revision + ":" + path)).hexdigest()
    sidecar = (
        json.loads((output / "preparation_sidecar.json").read_text()) if build == "B2" else None
    )
    if sidecar is not None:
        assert sidecar["observer_validity"] == "valid", sidecar["first_fault"]
        assert sidecar["worker_identity"]["implementation_revision"] == reviewed
        assert not sidecar["open_span_tokens"]
        if fixture in ("C0", "C1"):
            expected = {
                row["id"]: row["parent"]
                for row in json.loads(
                    (ROOT / "docs/task007f/profile1/g1_recorder_api.json").read_text()
                )["span_tree"]
            }
            for call in sidecar["calls"]:
                if call["call_kind"] not in ("startup", "recurring"):
                    continue
                spans = [row for row in sidecar["spans"] if row["call_seq"] == call["call_seq"]]
                assert {row["span_id"] for row in spans} == set(expected)
                by_token = {row["span_token"]: row for row in spans}
                for row in spans:
                    parent = row["parent_span_token"]
                    assert (None if parent is None else by_token[parent]["span_id"]) == expected[
                        row["span_id"]
                    ]
                    assert row["coverage"] == "complete"
    return envelope, provenance, sidecar


@pytest.mark.parametrize("fixture", ["C0", "C1", *SYNTHETIC])
def test_B0_B1_B2_controlled_parity(tmp_path, fixture):
    outputs = [run_build(tmp_path, build, fixture) for build in ("B0", "B1", "B2")]
    for envelope, provenance, _ in outputs:
        assert envelope["raw"]["failure"] is None
        if fixture != "S3":
            assert not envelope["raw"]["fallbacks"]
        else:
            assert len(envelope["raw"]["fallbacks"]) == 1  # Declared negative exhaustion oracle.
        if fixture in ("C0", "C1"):
            import numpy as np

            for call in envelope["calls"]:
                prediction = call["controller_last_prediction"]
                assert prediction is not None
                assert np.max(prediction["slacks"]) <= 1e-6
        assert provenance["manifest"] == outputs[0][1]["manifest"]
        assert provenance["numerical_versions"] == outputs[0][1]["numerical_versions"]
    assert outputs[1][1]["source_hashes"] == outputs[2][1]["source_hashes"]
    differences = [compare_controlled(outputs[0][0], other[0]) for other in outputs[1:]]
    (tmp_path / "duration_and_host_flag_differences.json").write_text(json.dumps(differences))
    if fixture in ("C1", "S4"):
        assert any(
            row["physical_completion_censored"] for row in outputs[2][2]["physical_outcomes"]
        )


def measured_readiness_report(outputs):
    """Descriptive population; caller must apply physical gates, never trace-equality waiver."""
    reports = []
    for build, (envelope, provenance, sidecar) in outputs.items():
        raw = envelope["raw"]
        assert raw["failure"] is None and not raw["fallbacks"]
        assert all(h["time"] <= raw["end_time"] for h in raw["handoffs"])
        reports.append(
            dict(
                build=build,
                source=provenance["revision"],
                misses=raw["misses"],
                codriver_misses=raw["codriver_misses"],
                handoffs=raw["handoffs"],
                controls=raw["controls"],
                plans=raw["plans"],
                physical_outcomes=None if sidecar is None else sidecar["physical_outcomes"],
                claim=(
                    "Descriptive legacy readiness; no p99, observer threshold or "
                    "end-to-end latency claim"
                ),
            )
        )
    return reports


def observer_block_report(blocks):
    """Post-run scalar report for six separately approved C1 blocks; launches nothing.

    Call run_build(..., dense=False) in the reviewed order with distinct block paths.
    Never pass controlled dense-spy data here or infer a negligible-overhead threshold.
    """
    assert len(blocks) == len(OBSERVER_ORDERS)
    report = []
    for index, (block, order) in enumerate(zip(blocks, OBSERVER_ORDERS)):
        assert tuple(block) == order
        costs = {}
        for build, (envelope, provenance, sidecar) in block.items():
            assert not envelope["calls"] and not envelope["rk4_trace"], (
                "Dense capture is not an observer sample"
            )
            assert envelope["raw"]["failure"] is None and not envelope["raw"]["fallbacks"]
            plans = envelope["raw"]["plans"]
            costs[build] = {
                population: {
                    clock: sum(p[field] for p in plans if bool(p["startup"]) == startup)
                    for clock, field in (
                        ("wall_s", "planner_total_time"),
                        ("cpu_s", "planner_cpu_time"),
                    )
                }
                for population, startup in (("startup", True), ("recurring", False))
            }
        deltas = {
            pair: {
                population: {
                    clock: costs[b][population][clock] - costs[a][population][clock]
                    for clock in ("wall_s", "cpu_s")
                }
                for population in ("startup", "recurring")
            }
            for pair, a, b in (("B1_minus_B0", "B0", "B1"), ("B2_minus_B1", "B1", "B2"))
        }
        report.append(
            dict(
                block=index,
                order=order,
                raw_costs=costs,
                signed_deltas=deltas,
                claim=(
                    "Legacy-boundary descriptive costs, all signs retained; no p99 or "
                    "subtractive correction"
                ),
            )
        )
    return report


def test_measured_observer_readiness_is_separate(tmp_path):
    outputs = {build: run_build(tmp_path, build, "M0", dense=False) for build in ("B0", "B1", "B2")}
    (tmp_path / "measured_readiness.json").write_text(
        json.dumps(measured_readiness_report(outputs))
    )


def test_strict_allowlist_rejects_unlisted_stats_and_authority_changes():
    _approved()
    base = dict(
        construction={},
        calls=[dict(solver_result=dict(statistics=dict(ipopt_statistics=dict(iter_count=3))))],
        raw=dict(controls=[], handoffs=[dict(time=0.1, accepted=True)]),
        rk4_trace=[],
    )
    for change in ("iterations", "authority", "new_key"):
        altered = copy.deepcopy(base)
        if change == "iterations":
            altered["calls"][0]["solver_result"]["statistics"]["ipopt_statistics"]["iter_count"] = 4
        elif change == "authority":
            altered["raw"]["handoffs"][0]["accepted"] = False
        else:
            altered["calls"][0]["solver_result"]["statistics"]["new_time"] = 0.1
        with pytest.raises(AssertionError):
            compare_controlled(base, altered)
    assert not _matches(
        "/calls/*/return_event/solve_time", ("calls", "arbitrary", "return_event", "solve_time")
    )


def test_host_flag_predicate_checked_and_differences_exposed():
    _approved()
    a = dict(raw=dict(controls=[dict(total_time=0.001, computational_deadline_exceeded=False)]))
    b = dict(raw=dict(controls=[dict(total_time=0.02, computational_deadline_exceeded=True)]))
    assert any(
        path[-1] == "computational_deadline_exceeded" for path, _, _ in compare_controlled(a, b)
    )
    b["raw"]["controls"][0]["computational_deadline_exceeded"] = False
    with pytest.raises(AssertionError):
        compare_controlled(a, b)


@pytest.mark.parametrize("case", ["U05", "U06", "U07", "U08", "U09"])
def test_U05_U09_original_negative_outcome_and_traceback(case):
    """Protocol-worker checks on existing real mathematics, with labelled injected faults."""
    reviewed, allowance_path, _ = _approved()
    import numpy as np
    from apex.control.trajectory.buffer import TrajectoryBuffer

    from apex.optimization.base import SolverResult

    launcher = _load(ROOT / "scripts/task007f/profile1/run_phase_a.py", "profile1_failure_launcher")
    observations = []

    class OriginalPredictionError(RuntimeError):
        pass

    original_exception = OriginalPredictionError("deliberate prediction failure")

    def fail_prediction(*args, **kwargs):
        raise original_exception

    def fail_backend(*args, **kwargs):
        raise RuntimeError("deliberate backend RuntimeError")

    def fail_gains(*args, **kwargs):
        raise ValueError("deliberate gain failure")

    for enabled in (False, True):
        api, recorder, allowance = _recorder(reviewed, allowance_path)
        if not enabled:
            recorder = None
            track, reference, planner, tracker, plant = launcher._construct(None)
        else:
            call = recorder.begin_call(
                kind="construction", plan_id=None, release_sim_s=None, estimate_sim_s=None
            )
            with launcher._span(recorder, "construction_full", None):
                track, reference, planner, tracker, plant = launcher._construct(recorder)
            recorder.finish_call(
                call,
                outcome=dict(
                    kind="not_applicable",
                    existing_status=None,
                    solver_attempted=None,
                    exception_type=None,
                ),
            )
        initial = json.loads(
            (ROOT / "docs/task007d/vis/vis1l/evidence/controlled_A/summary.json").read_text()
        )["initial_state"]
        if case == "U05":
            planner.predictor.predict = fail_prediction
        elif case == "U06":
            planner.controller.solver.backend = fail_backend
        elif case == "U07":
            planner.controller.solver.solve = lambda request: SolverResult(
                True,
                "deliberate_invalid_result",
                np.full(planner.controller.problem.nx, np.nan),
                {},
            )
        elif case == "U08":
            planner.gain_builder.compute = fail_gains
        else:
            # Original packet __post_init__ must reject the deliberately invalid schedule.
            planner.gain_builder.compute = lambda packet: (np.array([0.0]), np.zeros((1, 3)))
        call = root = None
        if enabled:
            call = recorder.begin_call(
                kind="recurring" if case == "U05" else "startup",
                plan_id=1 if case == "U05" else 0,
                release_sim_s=0.0,
                estimate_sim_s=0.0,
            )
            root = recorder.span_begin(call, "prepare_full", expected_parent=None)
        try:
            packet, event = planner.prepare(
                1 if case == "U05" else 0,
                initial,
                0.0,
                0.0,
                TrajectoryBuffer(),
                tracker,
                startup=case != "U05",
            )
        except OriginalPredictionError as error:
            assert case == "U05" and error is original_exception
            names, trace = [], error.__traceback__
            while trace is not None:
                names.append(trace.tb_frame.f_code.co_name)
                trace = trace.tb_next
            assert "fail_prediction" in names
            if enabled:
                recorder.span_end(root, exit="exception", exception_type=type(error).__qualname__)
                recorder.finish_call(
                    call,
                    outcome=dict(
                        kind="raised",
                        existing_status=None,
                        solver_attempted=False,
                        exception_type=type(error).__qualname__,
                    ),
                )
            observations.append(
                dict(calls=[], raw={}, rk4_trace=[], exception_type=type(error).__qualname__)
            )
        else:
            assert packet is None and not event["success"]
            if case in ("U06", "U07"):
                assert planner.controller.solution is None
            if case == "U06":
                assert event["status"] == "deliberate backend RuntimeError"
            if enabled:
                recorder.span_end(root, exit="complete")
                recorder.finish_call(
                    call,
                    outcome=dict(
                        kind="returned_none",
                        existing_status=event["status"],
                        solver_attempted=event["solver_attempted"],
                        exception_type=None,
                    ),
                )
            observations.append(
                dict(
                    calls=[
                        dict(
                            return_event=_snap(event),
                            post_control_solution=_snap(planner.controller.solution),
                        )
                    ],
                    raw={},
                    rk4_trace=[],
                )
            )
        if enabled:
            recorder.reconcile(clock_allowance_ns=allowance)
            sealed = recorder.seal(legacy_result=None, termination="negative_fixture")
            assert sealed.payload["observer_validity"] == "valid"
            assert any(row["exit"] == "exception" for row in sealed.payload["spans"]) or case in (
                "U06",
                "U07",
            )
    compare_controlled(*observations)


def test_observer_fault_preserves_tuple_and_stops_before_authority():
    reviewed, allowance_path, _ = _approved()
    from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

    api, recorder, allowance = _recorder(reviewed, allowance_path)
    track, planner, tracker, plant = _synthetic(ROOT, "S4")
    original_prepare, returned = planner.prepare, []

    def prepare(*args, **kwargs):
        answer = original_prepare(*args, **kwargs)
        returned.append(answer)
        return answer

    planner.prepare = prepare

    class BrokenClock:
        def wall_ns(self):
            raise RuntimeError("observer failure, never a solver failure")

        def cpu_ns(self):
            return 1

    recorder._clock = BrokenClock()
    runner = AsyncRunner(
        plant, planner, tracker, track, AsyncConfig(duration=0.24), recorder=recorder
    )
    raw = runner.run([2.0, 0, 0, 0, 0, 0])
    assert raw["stop_reason"] == "instrumentation_stop"
    assert raw["states"] == [] and raw["controls"] == [] and raw["fallbacks"] == []
    assert runner._instrumentation_last_preparation is returned[0]
    assert raw["plans"][0] is returned[0][1]
    assert returned[0][0] is not None and returned[0][1]["success"]
    recorder.reconcile(clock_allowance_ns=allowance)
    assert (
        recorder.seal(legacy_result=raw, termination=raw["stop_reason"]).payload[
            "observer_validity"
        ]
        == "invalid"
    )


def test_default_off_launcher_rejects_mode_before_numerical_imports(tmp_path, monkeypatch):
    reviewed, _, _ = _approved()
    import builtins

    original_import = builtins.__import__

    def reject_numerical(name, *args, **kwargs):
        if name.split(".")[0] in ("numpy", "scipy", "casadi", "apex") or name.endswith("recorder"):
            raise AssertionError("Forbidden import: " + name)
        return original_import(name, *args, **kwargs)

    # Scoped test sentinel in the protocol worker; no extra fresh worker or production hook.
    with monkeypatch.context() as scope:
        scope.setattr(builtins, "__import__", reject_numerical)
        launcher = _load(ROOT / "scripts/task007f/profile1/run_phase_a.py", "profile1_off_parser")
        args = launcher._parser().parse_args(
            ["--reviewed-revision", reviewed, "--output", str(tmp_path / "unused")]
        )
        assert args.efficiency_instrumentation == "off"
        with pytest.raises(SystemExit) as error:
            launcher.main(["--efficiency-instrumentation", "unsupported"])
        assert error.value.code == 2


if __name__ == "__main__":
    # An explicit future test command only. No code is invoked during G1 authoring.
    assert sys.argv[1] == "--g2-worker"
    _worker(
        Path(sys.argv[2]),
        sys.argv[3],
        sys.argv[4],
        sys.argv[5],
        Path(sys.argv[6]),
        Path(sys.argv[7]),
        int(sys.argv[9]),
        dense=sys.argv[8] == "dense",
    )
