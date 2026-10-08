"""Retrospective snapshot selection from complete retained records; no invented history."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def select(output=Path("results/task007cr")):
    outcomes = pd.read_csv(output / "outcomes.csv")
    divergence = json.loads((output / "first_divergence.json").read_text())
    selected = []
    for label in ["e", "f"]:
        folder = output / f"r2_{label}_00"
        records = json.loads((folder / "nlp_snapshots.json").read_text())
        measured = outcomes[(outcomes.family == "r4") & (outcomes.configuration == label)]
        metric = (
            "fast_sweeper_heading_TV_rad" if label == "e" else "technical_section_heading_TV_rad"
        )
        smooth = measured.sort_values(metric).iloc[0]["case"]

        def heading_tv(r):
            x = np.array(r["solution"][:30]).reshape(6, 5, order="F")
            return np.abs(np.diff(x[3])).sum()

        window = (40, 67) if label == "e" else (112, 124)
        strong = max(
            [r for r in records if window[0] <= r["parameters"][4] <= window[1]], key=heading_tv
        )
        slack = max(records, key=lambda r: max(r["solution"][-10:]))
        chosen = [
            ("before", records[1]),
            ("strong_sector_prediction", strong),
            ("max_slack", slack),
        ]
        if label == "e":
            chosen.append(
                (
                    "first_input_divergence",
                    next(
                        r
                        for r in records
                        if r["plan_id"] == divergence["state_perturbation_source_plan_id"]
                    ),
                )
            )
        # Select E's sweeper and F's late technical section separately.
        # Selection is descriptive; local TV alone is not a pathology classifier.
        for name, r in chosen:
            selected.append(
                dict(
                    name=f"{label}_{name}",
                    folder=str(folder),
                    plan_id=r["plan_id"],
                    progress=r["parameters"][4],
                    release_time=r["release_time"],
                    selection_metric_heading_TV_rad=float(heading_tv(r)),
                    selection_metric_slack_m=float(max(r["solution"][-10:])),
                    state_perturbations=divergence["state_perturbations"],
                    perturbation_basis=(
                        "Absolute early E replay/measured optimizer-state difference at first "
                        "input divergence, reused unchanged across snapshots"
                    ),
                    smooth_folder=str(output / smooth),
                    smooth_selection_metric=metric,
                )
            )
        other = json.loads((output / smooth / "nlp_snapshots.json").read_text())
        match = min(other, key=lambda r: abs(r["parameters"][4] - strong["parameters"][4]))
        selected.append(
            dict(
                name=f"{label}_matched_smooth",
                folder=str(output / smooth),
                plan_id=match["plan_id"],
                progress=match["parameters"][4],
                release_time=match["release_time"],
                match_distance_m=abs(match["parameters"][4] - strong["parameters"][4]),
                state_perturbations=divergence["state_perturbations"],
                smooth_folder=str(output / smooth),
                smooth_selection_metric=metric,
            )
        )
    (output / "snapshot_selection.json").write_text(json.dumps(selected, indent=2) + "\n")
    return selected


if __name__ == "__main__":
    select()
