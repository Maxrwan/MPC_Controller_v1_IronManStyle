"""Fresh frozen Candidate C measured-latency confirmation at one native ceiling."""

import json
from pathlib import Path

from threading_study.config import OUT, configure_accelerate


def closed_loop(threads, replicate, folder):
    native = configure_accelerate(threads)
    from run_mpc_baseline import run_case

    from apex.control.mpc.cost import CostScales
    from apex.control.mpc.problem import MPCConfig
    from apex.models.tire.config import RACING_TIRE_PHYSICS

    folder = Path(folder)
    frozen = json.loads((OUT / "frozen_candidates.json").read_text())["C"]
    c = frozen["configuration"]
    config = MPCConfig(
        horizon=c["n"],
        dt=1 / c["hz"],
        substeps=c["substeps"],
        costs=CostScales(**c["costs"]),
        tire_physics=RACING_TIRE_PHYSICS,
    )
    run_case(
        folder.name,
        track_name="oval",
        mode="measured",
        laps=2,
        duration=80.0,
        output=folder.parent,
        plots=False,
        mpc_config=config,
        solver_options=c["solver"],
        warm_start=c["warm_start"],
    )
    summary = json.loads((folder / "summary.json").read_text())
    summary.update(
        threading_control=native,
        threading_replicate=replicate,
        frozen_source=frozen["configuration_hash"],
    )
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    quality = (
        summary["failure"] is None
        and len(summary["lap_times"]) == 2
        and summary["solver_failures"] == 0
        and summary["fallbacks"] == 0
        and summary["boundary_violations"] == 0
        and summary["max_slack"] <= 1e-4
        and summary["maximum_primal_residual"] <= 1e-6
        and summary["full_run"]["rms_e_y"] <= 0.025
        and summary["full_run"]["rms_e_psi"] <= 0.06
        and summary["full_run"]["rms_speed_error"] <= 0.08
        and max(summary["max_front_combined_utilization"], summary["max_rear_combined_utilization"])
        <= 1 + 1e-12
    )
    (folder / "quality.json").write_text(json.dumps({"quality_pass": quality}) + "\n")
    # Retain failed physical runs; do not erase or silently retry them.
