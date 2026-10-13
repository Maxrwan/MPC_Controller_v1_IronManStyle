"""Offline replay of the first differing C1 RK4 partition using the unchanged plant."""

import argparse
import json
from pathlib import Path

import numpy as np

from apex.config import load_vehicle_parameters
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.planning_reference.track import load_track


def check(source):
    runs = [
        json.loads((source / n / "segments.json").read_text()) for n in ["C1_steady", "C1_jitter"]
    ]
    parts = [
        [r for r in run if r["start"] >= 0.12 - 1e-10 and r["end"] <= 0.125 + 1e-10] for run in runs
    ]
    assert [len(p) for p in parts] == [1, 2]
    p = load_vehicle_parameters("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track, _, _ = load_track("configs/planning/task007b/gamma_2p000/track_source.json")
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    replay = []
    for path in parts:
        x = np.array(path[0]["state_before"])
        for r in path:
            x = plant.step(x, np.array(r["control"]), r["dt"])
        replay.append(x)
    return dict(
        interval=[0.12, 0.125],
        segments=parts,
        identical_start=parts[0][0]["state_before"] == parts[1][0]["state_before"],
        identical_held_commands=all(
            r["control"] == parts[0][0]["control"] for path in parts for r in path
        ),
        replay_matches_recorded=[
            np.array_equal(x, path[-1]["state_after"]) for x, path in zip(replay, parts)
        ],
        replay_difference=(replay[0] - replay[1]).tolist(),
        note=(
            "Existing plant with recorded actual dt: 5 ms versus 3+2 ms; "
            "no correction or integration change."
        ),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    with args.output.open("x") as f:
        json.dump(check(args.source), f, indent=2)
        f.write("\n")
