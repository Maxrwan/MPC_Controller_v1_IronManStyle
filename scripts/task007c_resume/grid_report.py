"""Offline controlled-grid tables; missing cells stay explicit and never count as passes."""

import argparse
import csv
from pathlib import Path

ROOT = Path("results/task007c_resume")


def table(rows, fields):
    lines = [
        "| " + " | ".join(label for _, label in fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        values = []
        for key, _ in fields:
            value = row.get(key, "")
            try:
                value = f"{float(value):.5g}"
            except (TypeError, ValueError):
                pass
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build(phase):
    rows = list(csv.DictReader((ROOT / "comparison.csv").open()))
    gammas = [1.8, 2, 2.1] if phase == "c3" else [1.9, 2, 2.1]
    axis = "horizon" if phase == "c3" else "progress_weight"
    values = [4, 6, 8] if phase == "c3" else [0, 0.5, 1, 2, 4]
    retained = []
    for row in rows:
        if (
            row["history"] not in ["fixed", "smooth"]
            or row["repeat"]
            or int(row["laps"]) != 1
            or float(row["gamma"]) not in gammas
            or float(row["alpha_vy"]) != 1
            or float(row["alpha_r"]) != 1
        ):
            continue
        if phase == "c3" and float(row["progress_weight"]) != 0:
            continue
        if phase == "c4" and int(row["horizon"]) != 4:
            continue
        if float(row[axis]) in values:
            retained.append(row)
    retained.sort(key=lambda row: (float(row["gamma"]), row["history"], float(row[axis])))
    expected = {(g, h, v) for g in gammas for h in ["fixed", "smooth"] for v in values}
    index = {(float(r["gamma"]), r["history"], float(r[axis])): r for r in retained}
    missing = sorted(expected - index.keys())
    out = [
        f"# Task007C {phase.upper()} controlled grid",
        "",
        f"Analyzed cells: {len(retained)}/{len(expected)}. "
        + (
            "Grid analysis complete."
            if not missing
            else "INTERIM; analysis or simulation remains pending."
        ),
        "",
        "Single-lap screens retain the existing rolling start at s_abs=1m; their first "
        "lap-end time is a rolling segment, not a complete geometric lap. Comparisons "
        "share this start. Sustained confirmations report later complete laps separately.",
        "",
        "Candidate C weights remain fixed. "
        + (
            "Only N changes; dt=0.1s, lambda0."
            if phase == "c3"
            else "Only static lambda changes; N4, dt=0.1s."
        ),
        "",
        "All comparisons use matched physical availability histories. Offline analysis can overlap "
        "these imposed-timing runs; their measured preparation wall times are not isolated compute "
        "benchmarks. Fresh measured repetitions remain a separate acceptance requirement.",
        "",
    ]
    if missing:
        out += [
            "Missing analyzed cells: "
            + "; ".join(f"gamma{g:g}/{h}/{axis}={v:g}" for g, h, v in missing),
            "",
        ]
    fields = [
        ("gamma", "Gamma"),
        ("history", "History"),
        (axis, "N" if phase == "c3" else "Lambda"),
        ("boundary_count", "Boundary samples"),
        ("solver_failures", "Solver failures"),
        ("slack", "Slack max m"),
        ("clearance", "Clearance min m"),
        ("heading_tv", "Heading TV rad"),
        ("steering_tv", "Steering TV rad"),
        ("rate_limit_s", "Rate limit s"),
        ("beta_p95", "Beta p95 rad"),
        ("tracking_ey_rms", "Tracking ey RMS m"),
        ("lap_s", "Lap s"),
    ]
    out += [
        table(retained, fields),
        "",
        "## Deltas from matched baseline",
        "",
        "Positive deltas mean a larger metric. These are separate diagnostics, not a combined "
        "score or an acceptance rule. A small lap-time gain never compensates "
        "for a safety failure.",
        "",
    ]
    differences = []
    base = 4 if phase == "c3" else 0
    metrics = [
        "heading_tv",
        "steering_tv",
        "rate_limit_s",
        "beta_p95",
        "clearance",
        "tracking_ey_rms",
        "lap_s",
    ]
    for row in retained:
        key = (float(row["gamma"]), row["history"], base)
        if float(row[axis]) == base or key not in index:
            continue
        d = {key: row[key] for key in ["gamma", "history", axis]}
        for metric in metrics:
            if row[metric] and index[key][metric]:
                d[metric] = float(row[metric]) - float(index[key][metric])
        differences.append(d)
    out += [
        table(differences, fields[:3] + [(m, "Delta " + dict(fields)[m]) for m in metrics]),
        "",
        "## Timing-history spread",
        "",
        "Absolute fixed-versus-smooth differences below describe these two retained histories "
        "only. They do not estimate a population distribution.",
        "",
    ]
    spreads = []
    for gamma in gammas:
        for value in values:
            pair = [index.get((gamma, history, value)) for history in ["fixed", "smooth"]]
            if any(r is None for r in pair):
                continue
            d = {"gamma": gamma, axis: value}
            for metric in metrics:
                if all(row[metric] for row in pair):
                    d[metric] = abs(float(pair[0][metric]) - float(pair[1][metric]))
            spreads.append(d)
    out += [
        table(
            spreads,
            [fields[0], fields[2]] + [(m, "Abs spread " + dict(fields)[m]) for m in metrics],
        ),
        "",
    ]
    if phase == "c3":
        out += [
            "## Comparable prediction prefix",
            "",
            "Accepted packets only. State predictions use their first0.4s in all cases. "
            "Steering TV spans the four corresponding held input nodes (three differences). "
            "Full-horizon variation is exported separately with duration normalization.",
            "",
            table(
                retained,
                fields[:3]
                + [
                    (
                        "accepted_prediction_mean_common_0p4_heading_total_variation",
                        "First0.4s heading TV",
                    ),
                    (
                        "accepted_prediction_mean_common_0p4_steering_total_variation",
                        "First0.4s steering TV",
                    ),
                    (
                        "accepted_prediction_mean_common_0p4_steering_rate_sign_reversals",
                        "First0.4s reversals",
                    ),
                    ("iterations_per_call_mean", "Iterations mean"),
                    ("planner_misses", "Planner misses"),
                    ("codriver_misses", "Codriver misses"),
                ],
            ),
            "",
        ]
    out += [
        "No production selection is made by this generated report. Retain physical failures, "
        "finite-trace censoring and the later representative/measured outcomes "
        "in the final review.",
        "",
    ]
    path = Path(f"docs/TASK007C_{phase.upper()}_GRID_RESULTS.md")
    path.write_text("\n".join(out))
    print(path, f"{len(retained)}/{len(expected)} analyzed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["c3", "c4"])
    build(parser.parse_args().phase)
