"""Fresh numerical worker. Call existing entry points; never reproduce their equations."""

import json
import os
import resource
import sys
import traceback
from pathlib import Path

from tools.apex_workbench.configuration import ROOT, validate


def execute(adapter: str, effective: dict, output: Path) -> dict:
    """Also usable for focused parity checks against the original entry point."""
    effective = validate(adapter, effective)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite experiment output: {output}")
    if adapter == "dynamic_demo":
        import run_dynamic_bicycle_demo as original

        previous = sys.argv
        sys.argv = [
            str(ROOT / "scripts/run_dynamic_bicycle_demo.py"),
            "--duration",
            str(effective["duration"]),
            "--dt",
            str(effective["dt"]),
            "--output-dir",
            str(output),
            "--no-plot",
        ]
        try:
            original.main()
        finally:
            sys.argv = previous
        return json.loads((output / "summary.json").read_text())

    from run_lqr_baseline import run_case

    return run_case(
        output.name,
        effective["track"],
        effective["speed"],
        output.parent,
        duration=effective["duration"],
        laps=None,
        ey=effective["ey"],
        epsi=effective["epsi"],
        profile=False,
        plots=False,
    )


def export_geometry(adapter, effective, output):
    """Derived display coordinates through the canonical Frenet conversion API."""
    import csv

    import numpy as np

    from apex.coordinates.frenet import frenet_to_global

    if adapter == "dynamic_demo":
        from run_dynamic_bicycle_demo import synthetic_track

        track = synthetic_track()
    else:
        from run_lqr_baseline import make_track

        track = make_track(effective["track"])
    with (output / "states.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    with (output / "trajectory_xy.csv").open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time", "x", "y"])
        for row in rows:
            pose = frenet_to_global(
                track, float(row["s_abs"]), float(row["e_y"]), float(row["e_psi"])
            )
            writer.writerow([row["time"], pose.x, pose.y])
    with (output / "geometry.csv").open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["s", "x", "y", "left_x", "left_y", "right_x", "right_y"])
        for progress in np.linspace(0, track.length, 401):
            sample = track.sample(float(progress % track.length))
            left = frenet_to_global(track, progress, sample.left_width, 0)
            right = frenet_to_global(track, progress, -sample.right_width, 0)
            writer.writerow([progress, sample.x, sample.y, left.x, left.y, right.x, right.y])


def main(directory: Path) -> int:
    # Apply kernel limits and native controls BEFORE any numerical imports.
    resource.setrlimit(resource.RLIMIT_CPU, (30, 31))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]
    environment = {"python": sys.version, "platform": sys.platform}
    if sys.platform == "darwin":
        from threading_study.config import configure_accelerate

        environment["native_control"] = configure_accelerate(1)
    from threadpoolctl import threadpool_info, threadpool_limits

    with threadpool_limits(limits=1):
        request = json.loads((directory / "request.json").read_text())
        try:
            summary = execute(request["adapter"], request["effective"], directory / "experiment")
            (directory / "worker_result.json").write_text(json.dumps(summary, indent=2) + "\n")
            export_geometry(request["adapter"], request["effective"], directory / "experiment")
            if summary.get("failure"):
                raise RuntimeError(summary["failure"])
            return 0
        except Exception:
            traceback.print_exc()
            return 2
        finally:
            # Libraries loaded by the entry point may appear only after execution.
            environment["threadpools"] = threadpool_info()
            environment["thread_environment"] = {
                name: os.environ.get(name)
                for name in (
                    "VECLIB_MAXIMUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "OMP_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "BLIS_NUM_THREADS",
                )
            }
            (directory / "numerical_environment.json").write_text(
                json.dumps(environment, indent=2) + "\n"
            )


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
