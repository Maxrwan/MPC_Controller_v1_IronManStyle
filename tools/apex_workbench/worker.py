"""Fresh numerical worker. Call existing entry points; never reproduce their equations."""

import json
import os
import resource
import sys
import traceback
from pathlib import Path

from tools.apex_workbench.configuration import ROOT, validate


def execute(
    adapter: str,
    effective: dict,
    output: Path,
    *,
    lab_resolved=None,
    qualification=False,
    reference=False,
) -> dict:
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

    if adapter == "dynamic_lab":
        if reference:
            from tools.apex_workbench.qualification_reference import execute as execute_reference

            return execute_reference(
                effective, output, resolved=lab_resolved, qualification=qualification
            )
        from tools.apex_workbench.dynamic_lab import execute as execute_lab

        return execute_lab(effective, output, resolved=lab_resolved, qualification=qualification)

    if adapter != "lqr_baseline":
        raise ValueError("Unsupported execution adapter")
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


def export_geometry(adapter, effective, output, *, track=None, telemetry_extra=None):
    """Derived display coordinates through the canonical Frenet conversion API."""
    import csv

    import numpy as np

    from apex.coordinates.frenet import frenet_to_global

    if track is not None and adapter != "dynamic_lab":
        raise ValueError("Injected export track is scoped to the laboratory")
    if track is None and adapter == "dynamic_demo":
        from run_dynamic_bicycle_demo import synthetic_track

        track = synthetic_track()
    elif track is None and adapter == "lqr_baseline":
        from run_lqr_baseline import make_track

        track = make_track(effective["track"])
    elif track is None:
        raise ValueError("Laboratory export requires its actual injected track")
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

    from apex.state import CONTROL_NAMES, CONTROL_UNITS, STATE_NAMES, STATE_UNITS
    from tools.apex_workbench.storage import write_json

    control_path = output / "controls.csv"
    with control_path.open() if control_path.exists() else (output / "states.csv").open() as stream:
        control_columns = csv.DictReader(stream).fieldnames
    write_json(
        output / "telemetry_contract.json",
        {
            "schema": "apex-workbench-telemetry/1",
            "state_names": list(STATE_NAMES),
            "state_units": list(STATE_UNITS),
            "control_names": list(CONTROL_NAMES),
            "control_units": list(CONTROL_UNITS),
            "time_unit": "s",
            "xy_unit": "m",
            "state_columns": list(rows[0]),
            "control_columns": control_columns,
            **(telemetry_extra or {}),
        },
        exclusive=True,
    )


def main(directory: Path, lock_fd: int) -> int:
    # Apply kernel limits and native controls BEFORE any numerical imports.
    resource.setrlimit(resource.RLIMIT_CPU, (30, 31))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    from tools.apex_workbench.lifecycle import start_guard

    # This guard and the inherited lock remain effective until this process exits.
    start_guard(directory, lock_fd)
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]
    environment = {"python": sys.version, "platform": sys.platform}
    if sys.platform == "darwin":
        from threading_study.config import configure_accelerate

        environment["native_control"] = configure_accelerate(1)
    from threadpoolctl import threadpool_info, threadpool_limits

    with threadpool_limits(limits=1):
        request = json.loads((directory / "request.json").read_text())
        try:
            if request["adapter"] == "dynamic_lab":
                from tools.apex_workbench.lab_configuration import verify_captured_sources

                verify_captured_sources(request)
            summary = execute(
                request["adapter"],
                request["effective"],
                directory / "experiment",
                lab_resolved=request.get("lab_resolved"),
                qualification=request.get("execution_context", {}).get("purpose")
                in {"numerical_qualification", "software_test"},
                reference=request.get("execution_context", {}).get("role") == "canonical_reference",
            )
            if request["adapter"] == "dynamic_lab":
                verify_captured_sources(request)
            (directory / "worker_result.json").write_text(json.dumps(summary, indent=2) + "\n")
            if request["adapter"] != "dynamic_lab":
                export_geometry(request["adapter"], request["effective"], directory / "experiment")
            if summary.get("failure"):
                raise RuntimeError(summary["failure"])
            return 0
        except Exception:
            traceback.print_exc()
            return 2
        finally:
            if request["adapter"] == "dynamic_lab":
                import platform

                environment["platform_details"] = platform.platform()
                environment["machine"] = platform.machine()
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
    raise SystemExit(main(Path(sys.argv[1]).resolve(), int(sys.argv[2])))
