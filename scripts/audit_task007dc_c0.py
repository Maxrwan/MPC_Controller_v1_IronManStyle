"""Export the C0 urgent-grid counterexample using existing isolated pytest fixtures.

No fixed scheduler, optimizer call, racing fixture or scientific campaign is implemented.
Run in a fresh process with VECLIB_MAXIMUM_THREADS=1; requires the dev test environment.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "results/task007d/c"):
        parser.error("C0 evidence must be in results/task007d/c")
    if output.exists():
        raise FileExistsError("Preserve existing C0 evidence")
    if (
        list((ROOT / "results").rglob("MEASURED_ACTIVE"))
        or (ROOT / "results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Do not run fixtures during an active campaign")
    if shutil.disk_usage(ROOT).free < 1024**3:
        raise RuntimeError("Need at least 1 GiB free")
    native = configure_accelerate(1)
    # Deliberately reuse the existing test chart/vehicle/planner; no second model or fixture.
    sys.path[:0] = [str(ROOT / "tests/unit"), str(ROOT / "tests")]
    from conftest import dynamic_vehicle, straight_geometry
    from test_fixed_handoff_contract import off_grid_case, urgent_release

    from apex.simulation.asynchronous import AsyncConfig

    parameters, track = dynamic_vehicle.__wrapped__(), straight_geometry.__wrapped__()
    output.mkdir(parents=True, exist_ok=False)
    result = off_grid_case(parameters, track)
    with (output / "raw.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    release = urgent_release(result)["release_time"]
    if result["failure"] is not None or abs(release - 0.255) > 1e-12:
        raise RuntimeError("Expected C0 counterexample not reproduced")
    sources = [
        "AGENTS.md",
        "src/apex/simulation/asynchronous.py",
        "src/apex/simulation/diagnostic_timing.py",
        "src/apex/control/trajectory/packet.py",
        "src/apex/control/trajectory/planner.py",
        "src/apex/control/trajectory/prediction.py",
        "src/apex/control/trajectory/tracker.py",
        "tests/conftest.py",
        "tests/unit/test_async_chronology.py",
        "tests/unit/test_fixed_handoff_contract.py",
        "configs/vehicles/synthetic_dynamic_test_vehicle.yaml",
        "scripts/audit_task007dc_c0.py",
    ]
    summary = dict(
        status="BLOCKED_C0_URGENT_GRID_CONFLICT",
        implementation="unchanged legacy variable-handoff scheduler",
        baseline_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
        .decode()
        .strip(),
        config=asdict(
            AsyncConfig(
                duration=0.8,
                laps=2,
                latency_mode="injected",
                injected_delay=0.155,
                disturbance_time=0.15,
            )
        ),
        parameters=asdict(parameters),
        native=native,
        seed=None,
        fixture="Existing StraightPlanner and analytical straight_geometry pytest fixtures",
        trigger=result["triggers"],
        releases=result["releases"],
        planner_busy_misses=result["misses"],
        failure=result["failure"],
        stop_reason=result["stop_reason"],
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        targets=[
            dict(
                offset=ticks * 0.01,
                release=release,
                exact_target=release + ticks * 0.01,
                distance_to_grid=abs(
                    release + ticks * 0.01 - round((release + ticks * 0.01) / 0.01) * 0.01
                ),
            )
            for ticks in range(1, 11)
        ],
    )
    with (output / "summary.json").open("x") as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=summary["status"], release=release, output=str(output))))


if __name__ == "__main__":
    main()
