"""Decode raw snapshots, distinguishing physical release from forecast application."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def decode(folder):
    model = json.loads((folder / "nlp_model.json").read_text())
    records = json.loads((folder / "nlp_snapshots.json").read_text())
    physical = pd.read_csv(folder / "states.csv", float_precision="round_trip")
    n = model["config"]["horizon"]
    rows = []
    for record in records:
        parameters = np.asarray(record["parameters"])
        preview = parameters[8:-16].reshape(11, n + 1, order="F")
        matches = physical[np.isclose(physical.time, record["release_time"], atol=1e-10, rtol=0)]
        applied = matches[["delta", "a_cmd"]].iloc[0].tolist() if len(matches) else None
        rows.append(
            dict(
                plan_id=record["plan_id"],
                release_time=record["release_time"],
                release_state=record["release_state"],
                release_applied_control=applied,
                release_control_note="Startup is gated; row reflects prepositioned launch control"
                if record["plan_id"] == 0
                else "Release-time physical row; None if replay stopped before this row was logged",
                optimizer_initial_state=parameters[:6].tolist(),
                optimizer_previous_forecast_command=parameters[6:8].tolist(),
                centerline_curvature=preview[0].tolist(),
                racing_curvature=preview[9].tolist(),
                track_left_width=preview[1].tolist(),
                track_right_width=preview[2].tolist(),
                reference_vx=preview[3].tolist(),
                reference_vy=preview[4].tolist(),
                reference_r=preview[5].tolist(),
                reference_ey=preview[7].tolist(),
                reference_epsi=preview[8].tolist(),
                terminal_P=parameters[-16:].reshape(4, 4, order="F").tolist(),
            )
        )
    (folder / "nlp_snapshot_index.json").write_text(json.dumps(rows) + "\n")
    return rows


if __name__ == "__main__":
    for path in Path("results/task007cr").glob("r*/nlp_model.json"):
        decode(path.parent)
