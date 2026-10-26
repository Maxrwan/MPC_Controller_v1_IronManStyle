"""CLI is standard-library-only; run refuses absent/unreviewed L3 grants before imports."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .contracts import Budget, InputSpec
from .guards import check_execution_grant, preflight_resources, supervise_worker
from .inputs import verify_inputs


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CT1L research: implementation does not grant execution"
    )
    parser.add_argument("action", choices=("preflight-static", "run"))
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--assignment-root", required=True, type=Path)
    parser.add_argument("--grant", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    spec = InputSpec(root, args.archive_root.resolve(), args.assignment_root.resolve(), sha)
    result = verify_inputs(spec)
    if result.value is None:
        print(json.dumps({"status": result.status, "reasons": [r.detail for r in result.reasons]}))
        return 2
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
    if args.grant is None or args.output is None:
        print("L3_AUTHORIZATION_REQUIRED: no numerical execution authorized", file=sys.stderr)
        return 2
    grant = check_execution_grant(args.grant, result.value, Budget())
    if grant.value is None:
        print("; ".join(r.detail for r in grant.reasons), file=sys.stderr)
        return 2
    if args.output.resolve() != grant.value.output_root:
        parser.error("Output differs from reviewed grant")
    resources = preflight_resources(result.value, grant.value, Budget())
    if resources.value is None:
        print("; ".join(r.detail for r in resources.reasons), file=sys.stderr)
        return 2
    env_path = os.pathsep.join((str(root / "scripts"), str(root / "src")))
    # Explicit module roots are passed to the worker; no dependence on another checkout's cwd.
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
    previous = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = env_path
    try:
        report = supervise_worker(command, grant.value.output_root, grant.value, Budget())
    finally:
        if previous is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = previous
    print(
        json.dumps(
            {
                "termination": report.termination,
                "exit_code": report.worker_exit_code,
                "elapsed_wall_s": report.elapsed_wall_s,
                "peak_observed_worker_RSS_bytes": report.peak_observed_worker_RSS_bytes,
                "hard_RSS_enforcement": False,
            }
        )
    )
    return report.worker_exit_code if report.worker_exit_code is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
