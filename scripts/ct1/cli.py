"""CLI entry owns one monotonic allocation. Numerical execution still requires Primary L3."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

from .contracts import Budget, InputSpec, OutcomeStatus
from .guards import (
    _AggregateDeadline,
    _cli_result_exit_code,
    _DeadlineExpired,
    _preworker_evidence,
    check_execution_grant,
    preflight_resources,
    supervise_worker,
)
from .inputs import verify_inputs


def main(argv: Sequence[str] | None = None) -> int:
    cli_start = time.monotonic()  # First CLI timestamp, before parsing or any preflight.
    deadline = _AggregateDeadline(cli_start, cli_start + 300)
    budget = Budget()
    parser = argparse.ArgumentParser(description="CT1L implementation does not grant execution")
    parser.add_argument("action", choices=("preflight-static", "run"))
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--assignment-root", required=True, type=Path)
    parser.add_argument("--grant", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    source_verified = False
    grant_validated = False
    sha = None
    phase = "arguments"

    def fail(termination, reasons):
        record = _preworker_evidence(
            deadline,
            operation=args.action,
            phase=phase,
            termination=termination,
            reasons=reasons,
            source_verified=source_verified,
            grant_validated=grant_validated,
            implementation_sha=sha,
            output_root_requested=args.output,
        )
        print(json.dumps(record, allow_nan=False))
        return 2

    try:
        if args.action == "run" and (args.grant is None or args.output is None):
            return fail(
                "AUTHORIZATION_FAILURE",
                [
                    {
                        "code": "L3_AUTHORIZATION_REQUIRED",
                        "detail": "Explicit grant and fresh output are required",
                    }
                ],
            )
        root = args.repo_root.resolve()
        phase = "source_revision"
        sha = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            timeout=deadline.work_remaining_s(phase),
        ).strip()
        spec = InputSpec(root, args.archive_root.resolve(), args.assignment_root.resolve(), sha)
        phase = "source_verification"
        deadline.work_remaining_s(phase)
        result = verify_inputs(spec)
        if result.status != OutcomeStatus.AVAILABLE or result.value is None:
            return fail(
                "SOURCE_IDENTITY_FAILURE",
                [{"code": r.code, "detail": r.detail} for r in result.reasons],
            )
        source_verified = True
        deadline.work_remaining_s("source verification completed")
        if args.action == "preflight-static":
            print(
                json.dumps(
                    {
                        "status": "SOURCE_BINDINGS_VERIFIED",
                        "candidates": len(result.value.candidates),
                        "numerical_execution": False,
                    }
                )
            )
            return 0
        phase = "grant_validation"
        grant = check_execution_grant(args.grant, result.value, budget, deadline=deadline)
        if grant.status != OutcomeStatus.AVAILABLE or grant.value is None:
            return fail(
                "AUTHORIZATION_FAILURE",
                [{"code": r.code, "detail": r.detail} for r in grant.reasons],
            )
        grant_validated = True
        deadline.work_remaining_s("grant validation completed")
        if args.output.resolve() != grant.value.output_root:
            grant_validated = False
            return fail(
                "AUTHORIZATION_FAILURE",
                [
                    {
                        "code": "OUTPUT_GRANT_MISMATCH",
                        "detail": "CLI output differs from reviewed Primary grant",
                    }
                ],
            )
        phase = "resource_preflight"
        resources = preflight_resources(result.value, grant.value, budget, deadline=deadline)
        if resources.status != OutcomeStatus.AVAILABLE or resources.value is None:
            return fail(
                "RESOURCE_PREFLIGHT_FAILED",
                [{"code": r.code, "detail": r.detail} for r in resources.reasons],
            )
        deadline.work_remaining_s("resource preflight completed")
        env_path = os.pathsep.join((str(root / "scripts"), str(root / "src")))
        command = (
            sys.executable,
            "-B",
            "-m",
            "ct1.worker",
            "--repo-root",
            str(root),
            "--archive-root",
            str(spec.archive_root),
            "--grant",
            str(args.grant.resolve()),
        )
        phase = "supervisor"
        deadline.work_remaining_s(phase)
        previous = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = env_path
        try:
            report = supervise_worker(
                command,
                grant.value.output_root,
                grant.value,
                budget,
                deadline=deadline,
                inputs=result.value,
                grant_path=args.grant,
            )
        finally:
            if previous is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = previous
        if (
            report.worker_exit_code is None
            and "worker_exit_status_NOT_OBSERVED" not in report.missing_result_ids
        ):
            return fail(
                report.termination,
                [{"code": "WORKER_NOT_STARTED", "detail": r} for r in report.missing_result_ids],
            )
        observed = time.monotonic()
        print(
            json.dumps(
                {
                    "schema": "apex-ct1l-cli-result/1",
                    "termination": report.termination,
                    "exit_code": report.worker_exit_code,
                    "worker_started": True,
                    "primary_grant_validated": True,
                    "cli_start_monotonic_s": cli_start,
                    "deadline_monotonic_s": deadline.deadline_monotonic_s,
                    "observed_monotonic_s": observed,
                    "elapsed_wall_s": observed - cli_start,
                    "timing_scope": "CLI_MONOTONIC_SAMPLE_BEFORE_STDOUT_AND_RETURN",
                    "peak_observed_worker_RSS_bytes": None
                    if "worker_RSS_NOT_OBSERVED" in report.missing_result_ids
                    else report.peak_observed_worker_RSS_bytes,
                    "worker_rss_observation": "NOT_OBSERVED"
                    if "worker_RSS_NOT_OBSERVED" in report.missing_result_ids
                    else "SAMPLED",
                    "hard_RSS_enforcement": False,
                    "whole_command_envelope": "UNRESOLVED",
                },
                allow_nan=False,
            )
        )
        return _cli_result_exit_code(report)
    except (_DeadlineExpired, subprocess.TimeoutExpired) as exc:
        return fail(
            "RESOURCE_CENSORED", [{"code": "AGGREGATE_DEADLINE_EXHAUSTED", "detail": str(exc)}]
        )
    except PermissionError as exc:
        grant_validated = False
        return fail(
            "AUTHORIZATION_FAILURE", [{"code": "L3_AUTHORIZATION_REQUIRED", "detail": str(exc)}]
        )
    except ImportError as exc:
        return fail("ENVIRONMENT_FAILURE", [{"code": type(exc).__name__, "detail": str(exc)}])
    except (OSError, subprocess.SubprocessError) as exc:
        termination = (
            "SOURCE_IDENTITY_FAILURE" if phase.startswith("source") else "ENVIRONMENT_FAILURE"
        )
        return fail(termination, [{"code": type(exc).__name__, "detail": str(exc)}])


if __name__ == "__main__":
    raise SystemExit(main())
