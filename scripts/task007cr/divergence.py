"""First observed divergence, with release-versus-availability semantics explicit."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from task007cr.compare import pair


def analyze(output=Path("results/task007cr")):
    outcomes = pd.read_csv(output / "outcomes.csv")
    measured = outcomes[(outcomes.family == "r4") & (outcomes.configuration == "e")]
    smooth = measured.sort_values("fast_sweeper_heading_TV_rad").iloc[0]["case"]
    first = output / "r2_e_00"
    second = output / smooth
    metrics = pair(first, second)
    labels = {
        "physical_latency": "codriver physical delay differs at release",
        "application_time": "codriver command-availability timestamp differs",
        "state": "plant state at common physical sample timestamps",
        "accepted_handoff_time": "accepted trajectory handoff time",
        "active_reference_e_y": "active sampled APEX lateral reference",
        "source_state": "planner release state",
        "physical_delay": "planner physical delay differs at release",
        "predicted_state": "predicted optimizer application state",
        "previous_solution": "previous optimized solution / warm-start history",
        "initial": "decision-vector initial guess",
        "parameters": "exact numeric optimizer input",
        "first_apex_control": "first optimized control",
        "solution": "full optimized decision vector",
        "controls": "codriver requested/applied command by launch ordinal",
    }
    timeline = [
        dict(channel=k, description=v, **metrics[k]) for k, v in labels.items() if k in metrics
    ]
    driver_a = pd.read_csv(first / "controls.csv", float_precision="round_trip")
    driver_b = pd.read_csv(second / "controls.csv", float_precision="round_trip")
    index = metrics["application_time"]["first_row"]
    earliest_availability = (
        None
        if index is None
        else min(driver_a.application_time.iloc[index], driver_b.application_time.iloc[index])
    )
    initial_a = json.loads((first / "summary.json").read_text())["startup"]["prepositioned_control"]
    initial_b = json.loads((second / "summary.json").read_text())["startup"][
        "prepositioned_control"
    ]
    previous_a, previous_b = np.array(initial_a), np.array(initial_b)
    first_nontrivial_availability = None
    for a, b in zip(driver_a.itertuples(), driver_b.itertuples()):
        proposed_a = np.array([a.requested_delta, a.requested_a_cmd])
        proposed_b = np.array([b.requested_delta, b.requested_a_cmd])
        changed = (
            max(np.max(abs(proposed_a - previous_a)), np.max(abs(proposed_b - previous_b))) > 1e-12
        )
        if abs(a.application_time - b.application_time) > 1e-10 and changed:
            first_nontrivial_availability = min(a.application_time, b.application_time)
            break
        previous_a = np.array([a.delta, a.a_cmd])
        previous_b = np.array([b.delta, b.a_cmd])
    # Perturbation magnitudes come from the actual two optimizer inputs at their first split.
    snapshots_a = json.loads((first / "nlp_snapshots.json").read_text())
    snapshots_b = json.loads((second / "nlp_snapshots.json").read_text())
    index = metrics["parameters"]["first_row"]
    magnitudes = {}
    for field, i in [("vx", 0), ("vy", 1), ("r", 2), ("epsi", 3), ("ey", 5)]:
        magnitudes[field] = abs(
            snapshots_a[index]["parameters"][i] - snapshots_b[index]["parameters"][i]
        )
    report = dict(
        a=first.name,
        b=second.name,
        selection=(
            "Original-history E replay versus measured E with minimum sweeper heading TV; "
            "all measured runs retained separately"
        ),
        metrics=metrics,
        timeline=timeline,
        first_different_command_available_at=earliest_availability,
        first_nontrivial_command_availability_split=first_nontrivial_availability,
        state_perturbation_source_plan_id=snapshots_a[index]["plan_id"],
        state_perturbations=magnitudes,
        note=(
            "Solver/request channels use planner launch ordinal. State comparisons use common "
            "exact timestamps, no interpolation; first observed state split is resolution-limited. "
            "Timing metadata difference at release precedes its physical availability effect."
        ),
    )
    (output / "first_divergence.json").write_text(json.dumps(report, indent=2) + "\n")
    pd.DataFrame(timeline).to_csv(output / "first_divergence_timeline.csv", index=False)
    return report


def figure(output=Path("results/task007cr")):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads((output / "first_divergence.json").read_text())
    a = pd.read_csv(output / report["a"] / "states.csv")
    b = pd.read_csv(output / report["b"] / "states.csv")
    times, ia, ib = np.intersect1d(np.round(a.time, 12), np.round(b.time, 12), return_indices=True)
    fig, axes = plt.subplots(2, 2, figsize=(22, 13), layout="constrained")
    rows = [r for r in report["timeline"] if r["first_time"] is not None]
    axes[0, 0].barh([r["description"] for r in rows], [r["first_time"] for r in rows])
    axes[0, 0].set_xlabel("First observed difference: release/sample time [s]")
    for field in ["vx", "vy", "r", "e_psi", "e_y"]:
        delta = np.abs(a[field].to_numpy()[ia] - b[field].to_numpy()[ib])
        early = times <= 0.4
        axes[0, 1].plot(times[early], delta[early], label=field)
        axes[1, 0].plot(times, delta, label=field)
    axes[0, 1].set(
        xlim=(0, 0.4),
        xlabel="Physical time [s]",
        ylabel="Absolute state difference (SI per channel)",
    )
    axes[0, 1].set_yscale("symlog", linthresh=1e-10)
    axes[0, 1].set_ylim(bottom=0)
    axes[1, 0].set(xlabel="Physical time [s]", ylabel="Absolute state difference (SI per channel)")
    for case in [report["a"], report["b"]]:
        controls = pd.read_csv(output / case / "controls.csv")
        controls = controls[controls.time <= 0.4]
        axes[1, 1].plot(controls.time, controls.physical_latency * 1000, label=case)
    axes[1, 1].set(
        xlim=(0, 0.4), xlabel="Codriver release [s]", ylabel="Physical availability delay [ms]"
    )
    for ax in axes.ravel():
        ax.grid(alpha=0.2)
    for ax in [axes[0, 1], axes[1, 0], axes[1, 1]]:
        ax.legend(fontsize=8)
    fig.suptitle(
        "First divergence — exact common state samples, no interpolation\n"
        "Launch versus availability distinguished"
    )
    fig.savefig(output / "task007cr_first_divergence_timeline.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    analyze()
    figure()
