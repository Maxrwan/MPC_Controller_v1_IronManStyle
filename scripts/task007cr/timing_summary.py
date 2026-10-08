"""One-delay intervention verification and downstream differences on common physical samples."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from task007cr.compare import STATE, difference


def summarize(root=Path("results/task007cr")):
    chosen = json.loads((root / "timing_selection.json").read_text())
    baseline = root / "r2_e_00"
    config = json.loads((baseline / "summary.json").read_text())["diagnostic_timing"]
    states = pd.read_csv(baseline / "states.csv", float_precision="round_trip")
    base_nlp = json.loads((baseline / "nlp_snapshots.json").read_text())
    base_events = json.loads((baseline / "events.json").read_text())
    rows = []
    for path in sorted(root.glob("r7_*/summary.json")):
        summary = json.loads(path.read_text())
        schedule = summary["diagnostic_timing"]
        changed = np.flatnonzero(np.array(config["planner"]) != np.array(schedule["planner"]))
        assert changed.tolist() == [chosen["index"]]
        assert config["codriver"] == schedule["codriver"]
        other = pd.read_csv(path.parent / "states.csv", float_precision="round_trip")
        times, ia, ib = np.intersect1d(
            np.round(states.time, 12), np.round(other.time, 12), return_indices=True
        )
        a, b = states[STATE].to_numpy()[ia], other[STATE].to_numpy()[ib]
        ready_a = chosen["release_time"] + config["planner"][chosen["index"]]
        ready_b = chosen["release_time"] + schedule["planner"][chosen["index"]]
        before = times < min(ready_a, ready_b)
        effect = difference(a, b, 1e-9, times, a[:, 4])
        nlp = json.loads((path.parent / "nlp_snapshots.json").read_text())
        selected_a = next(r for r in base_nlp if r["plan_id"] == chosen["plan_id"])
        selected_b = next(r for r in nlp if r["plan_id"] == chosen["plan_id"])
        events = json.loads((path.parent / "events.json").read_text())
        handoffs = {}
        for name, entries in [("baseline", base_events), ("perturbed", events)]:
            handoffs[name] = [
                h["time"]
                for h in entries["handoffs"]
                if h["plan_id"] == chosen["plan_id"] and h["accepted"]
            ]
        optimizer_difference = difference(
            [r["parameters"] for r in base_nlp],
            [r["parameters"] for r in nlp],
            1e-10,
            [r["release_time"] for r in base_nlp],
        )
        rows.append(
            dict(
                case=path.parent.name,
                perturbation_ms=(
                    schedule["planner"][chosen["index"]] - config["planner"][chosen["index"]]
                )
                * 1000,
                verified_only_one_planner_delay_changed=True,
                verified_codriver_delays_unchanged=True,
                earliest_changed_ready_time=min(ready_a, ready_b),
                pre_intervention_state_max_abs=float(np.max(abs(a[before] - b[before]))),
                common_physical_state=effect,
                selected_update_solution_identical=selected_a["solution"] == selected_b["solution"],
                selected_update_parameters_identical=selected_a["parameters"]
                == selected_b["parameters"],
                selected_update_handoff_times=handoffs,
                optimizer_parameter_difference=optimizer_difference,
                state_channel_max=dict(zip(STATE, np.max(abs(a - b), axis=0).tolist())),
                state_channel_rms=dict(zip(STATE, np.sqrt(np.mean((a - b) ** 2, axis=0)).tolist())),
                complete_lap=bool(summary["lap_times"]),
                stop_reason=summary["stop_reason"],
                end_time=summary["end_time"],
                common_sample_end_time=float(times[-1]),
                note=(
                    "No interpolation. First state split is limited by common sample resolution. "
                    "Availability changes can also partition the frozen RK4 integrator differently."
                ),
            )
        )
    (root / "timing_sensitivity.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    summarize()
