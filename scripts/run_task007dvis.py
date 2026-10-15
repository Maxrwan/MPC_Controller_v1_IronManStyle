"""One authorized VIS-1 case, guarded and ordered; no controller or fixture CLI overrides."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from task007dvis.protocol import CASES, FLOOR, HEADROOM, case_named, source_hashes
from threading_study.config import ROOT, configure_accelerate, environment


def check_prerequisites(root, case):
    record = json.loads((root / "prerequisites.json").read_text())
    if not record["passed"] or record["source_sha256"] != source_hashes():
        raise RuntimeError("Missing, failed or stale focused prerequisite gate")
    for earlier in CASES[: CASES.index(case)]:
        summary_path = root / earlier.name / "summary.json"
        if not summary_path.exists():
            raise RuntimeError("Previous case missing: " + earlier.name)
        summary = json.loads(summary_path.read_text())
        if summary["stop_gate"] or summary["source_sha256"] != record["source_sha256"]:
            raise RuntimeError("Previous case failed or source changed: " + earlier.name)
        if earlier.phase == "parity" and not summary["parity"]["passed"]:
            raise RuntimeError("Parity gate failed: " + earlier.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[c.name for c in CASES], required=True)
    parser.add_argument("--root", type=Path, default=Path("results/task007d/vis/vis1"))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()
    case = case_named(args.case)
    if not root.is_relative_to(ROOT / "results/task007d/vis"):
        parser.error("VIS evidence must be in results/task007d/vis")
    folder = root / case.name
    if args.worker:
        native = configure_accelerate(1)
        from task007dvis.worker import run

        return 2 if run(case, folder, native) else 0
    if (
        list((ROOT / "results").rglob("MEASURED_ACTIVE"))
        or (ROOT / "results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Active measurement guard")
    if shutil.disk_usage(ROOT).free < FLOOR + HEADROOM:
        raise RuntimeError("Need 1 GiB free floor plus 1.5 GiB planned headroom")
    check_prerequisites(root, case)
    contract = json.loads((root / "export_validation.json").read_text())
    if not contract["passed"] or contract["source_sha256"] != source_hashes():
        raise RuntimeError("Missing, failed or stale export validation gate")
    folder.mkdir(exist_ok=False)
    guard = root / "MEASURED_ACTIVE"
    with guard.open("x") as f:
        json.dump(dict(pid=os.getpid(), case=case.name, output=str(folder)), f)
    try:
        with (folder / "worker.log").open("x") as log:
            result = subprocess.run(
                [sys.executable, __file__, *sys.argv[1:], "--worker"],
                cwd=ROOT,
                env=environment(1),
                stdout=log,
                stderr=log,
            )
        (folder / "exit.json").write_text(
            json.dumps(dict(case=asdict(case), exit_code=result.returncode)) + "\n"
        )
        print(json.dumps(dict(case=case.name, exit_code=result.returncode, folder=str(folder))))
        return result.returncode
    finally:
        guard.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
