"""Preserve both mandatory amended C0 fixtures, separately from the original conflict."""

import argparse
import shutil
import sys
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        list((ROOT / "results").rglob("MEASURED_ACTIVE"))
        or (ROOT / "results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Active measurement")
    if shutil.disk_usage(ROOT).free < 1024**3:
        raise RuntimeError("Need 1 GiB free")
    configure_accelerate(1)
    sys.path[:0] = [str(ROOT / "tests/unit"), str(ROOT / "tests")]
    from conftest import dynamic_vehicle, straight_geometry
    from task007d.worker import write
    from test_fixed_handoff_scheduler import simulate

    from apex.simulation.diagnostic_timing import DiagnosticTiming

    args.output.mkdir(parents=True, exist_ok=False)
    p, t = dynamic_vehicle.__wrapped__(), straight_geometry.__wrapped__()
    summary = {}
    for name, timing in [
        ("original155", None),
        ("recovery35", DiagnosticTiming("replay", (0.155, *([0.035] * 10)), tuple([0.0] * 100))),
    ]:
        raw = simulate(p, t, delay=0.155, disturbance_time=0.15, timing=timing)
        write(args.output / (name + ".json"), raw)
        summary[name] = {
            k: raw[k]
            for k in [
                "fixed_handoffs",
                "urgent_demands",
                "releases",
                "misses",
                "fallbacks",
                "failure",
                "end_time",
            ]
        }
    write(args.output / "summary.json", summary)


if __name__ == "__main__":
    main()
