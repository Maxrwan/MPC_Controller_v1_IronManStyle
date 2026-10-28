"""Fixed 17-execution protocol. Plan is read-only; execute requires separate human authorization."""

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from tools.apex_workbench import jobs, storage
from tools.apex_workbench.configuration import ROOT
from tools.apex_workbench.lab_configuration import CRITERIA, GRIDS, request_for
from tools.apex_workbench.lab_sources import REQUIRED
from tools.apex_workbench.qualification import SLOTS, bind_run, publish


def plan():
    rows = []
    for slot in SLOTS:
        case, grid = (
            ("VDL1_BASE", "nominal") if slot in {"repeat", "reference"} else slot.split("/")
        )
        h, steps, onset = GRIDS[grid]
        rows.append(
            {
                "slot": slot,
                "case_id": case,
                "grid_id": grid,
                "dt_s": h,
                "steps": steps,
                "onset_tick": onset,
                "role": "canonical_reference" if slot == "reference" else "adapter",
            }
        )
    return {
        "schema": "apex-vdl-campaign-plan/1",
        "protocol": CRITERIA["version"],
        "execution_count": 17,
        "plant_intervals": sum(r["steps"] for r in rows),
        "aggregate_simulation_s": 8.5,
        "duration_per_execution_s": 0.5,
        "slots": rows,
        "execution_authorized_by_plan": False,
    }


def checked_revision(revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("An exact reviewed source commit SHA is required")
    expected = {}
    for name in REQUIRED:
        data = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=ROOT)
        expected[name] = hashlib.sha256(data).hexdigest()
        if storage.sha256(ROOT / name) != expected[name]:
            raise ValueError("Current scientific source differs from reviewed revision: " + name)
    return expected


def _wait(directory):
    deadline = time.monotonic() + 70
    while time.monotonic() < deadline:
        status = jobs.status_for(directory)
        if status["state"] not in jobs.ACTIVE:
            # Finalization precedes release of the inherited lease.
            try:
                with jobs.execution_lock():
                    return status
            except RuntimeError:
                pass
        time.sleep(0.05)
    jobs.cancel_run(directory)
    raise RuntimeError("Worker did not finalize within the bounded coordination interval")


def execute(directory, revision, *, acknowledge=False):
    if acknowledge is not True:
        raise ValueError(
            "Separate scientific execution authorization must be explicitly acknowledged"
        )
    expected = checked_revision(revision)
    jobs.preflight()
    directory = Path(directory).resolve()
    if (
        not directory.is_relative_to((ROOT / "results").resolve())
        or directory == (ROOT / "results").resolve()
    ):
        raise ValueError("A fresh task-specific directory under results is required")
    directory.mkdir(parents=True, exist_ok=False)
    admission = {"reviewed_source_revision": revision, "source_sha256": expected, "plan": plan()}
    storage.write_json(directory / "admission.json", admission, exclusive=True)
    references, current = {}, None
    try:
        for row in plan()["slots"]:
            # Check the exact reviewed source again before every fresh worker admission.
            checked_revision(revision)
            current = jobs.start_run(
                "dynamic_lab",
                request_for(row["case_id"], grid_id=row["grid_id"]),
                "Separately authorized fixed numerical qualification protocol: " + row["slot"],
                runs=directory / "runs",
                qualification=True,
                reference=row["role"] == "canonical_reference",
            )
            status = _wait(current)
            if (
                status.get("scientific_outcome") != "completed"
                or status.get("evidence_state") != "valid"
            ):
                raise RuntimeError(
                    "Qualification execution failed; retained without retry: " + row["slot"]
                )
            references[row["slot"]], _ = bind_run(current)
            storage.write_json(directory / "progress.json", {"references": references})
            current = None
        checked_revision(revision)
        result = publish(references, directory / "qualification")
        storage.write_json(
            directory / "status.json",
            {
                "state": "evaluated",
                "numerical_decision": result["decision"],
                "physical_validity": "not_established",
            },
        )
        return {"directory": str(directory), "decision": result["decision"]}
    except BaseException as error:
        if current is not None:
            jobs.cancel_run(current)
        storage.write_json(
            directory / "status.json",
            {
                "state": "failed_or_interrupted",
                "numerical_decision": "not_qualified",
                "error": f"{type(error).__name__}: {error}",
                "retained_references": references,
            },
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="Print the fixed scope without launching any worker")
    run = commands.add_parser("execute", help="Only after separate execution authorization")
    run.add_argument("--output-dir", required=True)
    run.add_argument("--reviewed-revision", required=True)
    run.add_argument("--acknowledge-scientific-execution", action="store_true", required=True)
    args = parser.parse_args()
    result = (
        plan()
        if args.command == "plan"
        else execute(
            args.output_dir,
            args.reviewed_revision,
            acknowledge=args.acknowledge_scientific_execution,
        )
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
