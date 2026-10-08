"""Reuse the accepted full-trend view solely for visual anchor reproduction."""

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from matplotlib.figure import Figure
from task007b.plots import comparison, dashboard

from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track


def render(output=Path("results/task007c")):
    # Reuse the accepted drawing code while labeling these as the new anchor review.
    original = Figure.suptitle

    def title(figure, text, *args, **kwargs):
        return original(
            figure,
            text.replace("Task007B", "Task007C anchor reproduction review"),
            *args,
            **kwargs,
        )

    with patch.object(Figure, "suptitle", title):
        return render_anchors(output)


def render_anchors(output):
    paths = []
    cases = ["anchor_" + c for c in "abcdef"] + ["anchor_e_repeat", "anchor_f_repeat"]
    for case in cases:
        folder = output / case
        fixture = folder / "fixture"
        track, _, identity = load_track(fixture / "track_source.json")
        reference = PlanningReference(fixture, track, identity, feasibility_policy="advisory")
        path = Path(
            dashboard(
                folder,
                pd.read_csv(folder / "telemetry.csv"),
                pd.read_csv(folder / "planning_apex_nodes.csv"),
                reference,
                track,
            )
        )
        destination = output / f"task007c_anchor_review_{case}.png"
        path.replace(destination)
        paths.append(str(destination))
    comparison(output, cases, reference)
    (output / "task007b_aggression_comparison_dashboard.png").replace(
        output / "task007c_anchor_comparison.png"
    )
    (output / "anchor_review_images.json").write_text(json.dumps(paths, indent=2) + "\n")


if __name__ == "__main__":
    render()
