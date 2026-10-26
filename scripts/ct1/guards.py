"""L3-only supervision. Importing guards uses only the standard library and CT1 contracts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .contracts import (
    ASSIGNMENT_REVISION,
    BackendIdentity,
    Budget,
    ExecutionGrant,
    GuardOwner,
    NativeSetup,
    Outcome,
    ResourcePreflight,
    SupervisorReport,
    VerifiedInputs,
)
from .inputs import _git, _plain, _read


def check_execution_grant(
    grant_path: Path, inputs: VerifiedInputs, budget: Budget
) -> Outcome[ExecutionGrant]:
    try:
        raw = _read(grant_path)
        if (
            raw.get("primary_authorized") is not True
            or raw.get("authorized_stage") != "L3"
            or not raw.get("approval_reference")
        ):
            raise ValueError("Explicit Primary L3 authorization absent")
        if (
            raw["assignment_sha"] != ASSIGNMENT_REVISION
            or raw["implementation_sha"] != inputs.spec.expected_revision
        ):
            raise ValueError("Grant SHA binding mismatch")
        expiry = datetime.fromisoformat(raw["expiry_utc"].replace("Z", "+00:00"))
        if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
            raise ValueError("Grant expired or lacks timezone")
        if (
            budget.max_candidates,
            budget.gain_samples_before_dedup,
            budget.wall_s,
            budget.rss_bytes,
            budget.output_bytes,
            budget.initial_free_bytes,
        ) != (12, 960, 300, 1073741824, 1073741824, 2147483648):
            raise ValueError("Unreviewed planning ceilings")
        if raw["host_seconds"] != 300:
            raise ValueError("Grant must reconcile exact300s allocation")
        allow = _read(inputs.spec.assignment_root / "future_source_allowlist.json")
        expected = {
            n
            for n in allow["allowed_create_paths"]
            if n.startswith("tests/ct1l/test_") and n.endswith(".py")
        }
        if set(raw["test_paths"]) != expected or len(raw["test_paths"]) != len(expected):
            raise ValueError("Exact reviewed prerequisites required, no silent test omission")
        out = Path(raw["output_root"]).resolve()
        parent = inputs.spec.repo_root.resolve() / "results/ct1/ct1l" / raw["implementation_sha"]
        if not out.is_relative_to(parent) or out == parent:
            raise ValueError("Dedicated output descendant required")
        if out.exists():
            # Only the exact supervised child may recheck a just-created allocation.
            marker = _read(out / "MEASURED_ACTIVE")
            if (
                not os.environ.get("CT1L_DEADLINE_MONOTONIC")
                or marker.get("owner_pid") != os.getppid()
                or marker.get("implementation_sha") != raw["implementation_sha"]
                or marker.get("stage") != "L3"
            ):
                raise ValueError("Fresh output required outside the owning supervised child")
        return Outcome.available(
            ExecutionGrant(
                raw["assignment_sha"],
                raw["implementation_sha"],
                "L3",
                tuple(raw["test_paths"]),
                raw["host_seconds"],
                raw["expiry_utc"],
                out,
            )
        )
    except (KeyError, ValueError, OSError) as exc:
        return Outcome.unavailable("L3_AUTHORIZATION_REQUIRED", str(exc))


def preflight_resources(
    inputs: VerifiedInputs, grant: ExecutionGrant, budget: Budget
) -> Outcome[ResourcePreflight]:
    try:
        # This body is never called for L1 static checks.
        ancestor = grant.output_root.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        free = shutil.disk_usage(ancestor).free
        if free < budget.initial_free_bytes:
            raise ValueError("Less than2GiB initially free")
        roots = {inputs.spec.repo_root, inputs.spec.archive_root}
        for line in _git(inputs.spec.repo_root, "worktree", "list", "--porcelain").splitlines():
            if line.startswith("worktree "):
                roots.add(Path(line[9:]))
        guards = []
        for root in roots:
            result = root / "results"
            if not result.exists():
                continue
            for p in result.rglob("*"):
                if p.name in ("MEASURED_ACTIVE", "D3_ACTIVE") and p.is_file():
                    guards.append(GuardOwner(p, None, None, p.stat().st_mtime_ns, "ACTIVE"))
        inventory = subprocess.check_output(["ps", "-axo", "pid=,ppid=,command="], text=True)
        own = {os.getpid(), os.getppid()}
        competing = []
        for line in inventory.splitlines():
            parts = line.strip().split(None, 2)
            if len(parts) < 3:
                continue
            pid = int(parts[0])
            command = parts[2]
            if (
                pid not in own
                and ("python" in command.lower())
                and any(
                    s in command
                    for s in (
                        "pytest",
                        "ct1.worker",
                        "run_phase_a",
                        "threading_study/worker",
                        "task007dvis/worker",
                    )
                )
            ):
                competing.append(line)
        if guards or competing:
            raise ValueError(
                "Owned measurement guard or competing scientific worker; do not remove it"
            )
        import psutil

        return Outcome.available(
            ResourcePreflight(
                free,
                int(psutil.virtual_memory().available),
                tuple(competing),
                tuple(guards),
                hashlib.sha256(inventory.encode()).hexdigest(),
                grant.output_root,
                grant.host_seconds,
            )
        )
    except (OSError, ValueError, ImportError, subprocess.SubprocessError) as exc:
        return Outcome.unavailable("RESOURCE_PREFLIGHT_FAILED", str(exc))


def configure_native_single(backend: BackendIdentity) -> Outcome[NativeSetup]:
    try:
        if sys.platform != "darwin" or backend.name != "Accelerate":
            raise ValueError("Backend controls require separate qualification")
        if os.environ.get("VECLIB_MAXIMUM_THREADS") != "1":
            raise ValueError("Fresh-parent native ceiling absent")
        if any(n.split(".")[0] in ("numpy", "scipy", "casadi") for n in sys.modules):
            raise ValueError("Numerical import preceded native setup")
        import ctypes

        lib = ctypes.CDLL("/System/Library/Frameworks/Accelerate.framework/Accelerate")
        lib.BLASSetThreading.argtypes = [ctypes.c_uint]
        lib.BLASSetThreading.restype = ctypes.c_int
        lib.BLASGetThreading.restype = ctypes.c_uint
        status = lib.BLASSetThreading(1)
        mode = lib.BLASGetThreading()
        if status != 0 or mode != 1:
            raise ValueError("Actual Accelerate SINGLE setup failed")
        return Outcome.available(
            NativeSetup(1, status, "SINGLE", backend, {"VECLIB_MAXIMUM_THREADS": "1"}, False)
        )
    except (OSError, ValueError, AttributeError) as exc:
        return Outcome.unavailable("NATIVE_SINGLE_UNQUALIFIED", str(exc))


def _resource_stop(now, deadline, rss, written, free, budget):
    """Pure predicate for independent resource-negative tests; RSS remains sampled."""
    return (
        now >= deadline - 5
        or rss >= budget.rss_bytes
        or written >= int(0.95 * budget.output_bytes)
        or free < 1073741824
    )


def supervise_worker(
    command: tuple[str, ...], output_root: Path, grant: ExecutionGrant, budget: Budget
) -> SupervisorReport:
    import psutil

    from .contracts import EvidenceWriter
    from .evidence import append_record, finalize_run

    if (
        grant.authorized_stage != "L3"
        or grant.host_seconds != budget.wall_s
        or Path(output_root).resolve() != grant.output_root
    ):
        raise PermissionError("Reviewed supervisor grant/output allocation mismatch")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    repo = Path(command[command.index("--repo-root") + 1]).resolve()
    begin = time.monotonic()
    deadline = begin + budget.wall_s
    peak = 0
    gap = 0.0
    previous = begin
    termination = "COMPLETE"
    process = None
    final_index = None
    missing = []
    samples = 0
    cpu = None
    env = os.environ.copy()
    env.update(
        VECLIB_MAXIMUM_THREADS="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONHASHSEED="0",
        CT1L_DEADLINE_MONOTONIC=str(deadline),
    )
    env.update(
        TMPDIR=str(root), MPLCONFIGDIR=str(root / "mpl-cache"), XDG_CACHE_HOME=str(root / "cache")
    )
    marker = root / "MEASURED_ACTIVE"
    marker.write_text(
        json.dumps(
            {
                "owner_pid": os.getpid(),
                "implementation_sha": grant.implementation_sha,
                "stage": "L3",
            }
        )
        + "\n"
    )
    writer = EvidenceWriter(root, repo / "docs/ct1/ct1l/scientific_evidence.schema.json", root.name)

    def record(kind, ident, data):
        manifest = root / "run_manifest.json"
        if not manifest.exists():
            return None
        template = _read(manifest)
        observation = {
            "schema": template["schema"],
            "record_type": kind,
            "record_id": root.name + ":supervisor:" + ident,
            "run_id": root.name,
            "status": "COMPUTED",
            "context": template["context"],
            "source_bindings": template["source_bindings"],
            "reasons": [],
            "data": _plain(data),
        }
        return append_record(writer, kind, observation).value

    try:
        with (
            (root / "worker.stdout.log").open("xb") as stdout,
            (root / "worker.stderr.log").open("xb") as stderr,
        ):
            try:
                process = subprocess.Popen(
                    command, cwd=repo, env=env, stdout=stdout, stderr=stderr, start_new_session=True
                )
                monitored = psutil.Process(process.pid)
                while process.poll() is None:
                    now = time.monotonic()
                    gap = max(gap, now - previous)
                    previous = now
                    threads = None
                    rss = None
                    try:
                        rss = monitored.memory_info().rss
                        threads = monitored.num_threads()
                        c = monitored.cpu_times()
                        cpu = c.user + c.system
                    except psutil.NoSuchProcess:
                        pass
                    if rss is not None:
                        peak = max(peak, rss)
                    written = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                    free = shutil.disk_usage(root).free
                    violation = _resource_stop(now, deadline, rss or 0, written, free, budget)
                    mode = "UNCONFIRMED"
                    if (root / "source_environment.json").exists():
                        mode = _read(root / "source_environment.json")["data"][
                            "backend_setup_receipt"
                        ]
                    record(
                        "resource",
                        "resource:" + str(samples),
                        {
                            "monotonic_elapsed_s": now - begin,
                            "worker_pid": process.pid,
                            "worker_rss_bytes": rss,
                            "output_bytes": written,
                            "disk_free_bytes": free,
                            "process_thread_count": threads,
                            "native_mode": mode,
                            "hard_memory_enforcement": "UNAVAILABLE_SAMPLED_ONLY",
                            "guard_owner": str(os.getpid()),
                            "action": "TERM" if violation else "OBSERVE",
                        },
                    )
                    samples += 1
                    if violation:
                        termination = "RESOURCE_CENSORED"
                        try:
                            os.killpg(process.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                        grace = min(1.0, max(0.0, deadline - time.monotonic()))
                        try:
                            process.wait(timeout=grace)
                        except subprocess.TimeoutExpired:
                            try:
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                            process.wait()
                        break
                    time.sleep(min(0.1, max(0.0, deadline - 5 - now)))
            finally:
                if process is not None and process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
        code = process.returncode if process else None
        if termination == "COMPLETE":
            if code != 0:
                termination = "NUMERICAL_FAILURE"
            for line in reversed((root / "worker.stdout.log").read_text().splitlines()):
                try:
                    report = json.loads(line)
                except ValueError:
                    continue
                if isinstance(report, dict) and report.get("termination") in (
                    "COMPLETE",
                    "RESOURCE_CENSORED",
                    "NUMERICAL_FAILURE",
                    "MISSING_COVERAGE",
                    "SOURCE_IDENTITY_FAILURE",
                ):
                    termination = report["termination"]
                    break
        if not (root / "coverage.json").exists():
            missing.append("coverage")
            termination = (
                "RESOURCE_CENSORED" if termination == "RESOURCE_CENSORED" else "MISSING_COVERAGE"
            )
        record(
            "event",
            "cpu-observation",
            {
                "event": "SUPERVISOR_CPU_THREAD_OBSERVATION",
                "clock_s": time.monotonic() - begin,
                "related_record_ids": [],
                "termination_reason": "sampled cumulative worker CPU seconds="
                + str(cpu)
                + "; samples="
                + str(samples)
                + "; exact active BLAS thread count unavailable",
                "retention_action": "RSS and CPU observations are sampled; no hard memory cap claim",
            },
        )
    except (OSError, ValueError, KeyError, psutil.Error) as exc:
        termination = "RESOURCE_CENSORED"
        missing.append("supervisor:" + str(exc))
        code = process.returncode if process else None
    finally:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        # Rename only our own marker. Other measurement guards are never removed.
        marker.write_text(
            json.dumps(
                {
                    "owner_pid": os.getpid(),
                    "state": "COMPLETED",
                    "termination": termination,
                    "peak_observed_worker_rss_bytes": peak,
                    "hard_memory_cap": False,
                    "monitoring_gap_max_s": gap,
                }
            )
            + "\n"
        )
        marker.rename(root / "MEASURED_COMPLETED")
        writer._final_measurements = {
            "wall_elapsed_s": time.monotonic() - begin,
            "peak_observed_worker_rss_bytes": peak,
        }
        writer._final_deadline = deadline
        indexed = finalize_run(writer, (), termination)
        if indexed.value is not None:
            final_index = record("index", "index", indexed.value)
        if final_index is None:
            missing.append(
                "index: manifest/context or finalization unavailable; partial files retained"
            )
    return SupervisorReport(
        code, termination, time.monotonic() - begin, peak, False, gap, final_index, tuple(missing)
    )
