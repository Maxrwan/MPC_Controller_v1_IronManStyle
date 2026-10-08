"""Matched native-progress comparisons for retained histories, including censored outcomes."""

import argparse
import json
from pathlib import Path

ROOT = Path("results/task007c_resume")
HISTORIES = ["fixed", "smooth", "median", "pathological_e", "pathological_f"]


def main(gamma):
    from threading_study.config import configure_accelerate

    configure_accelerate(1)
    from task007c_resume.common_coverage import compare
    from task007c_resume.grid_report import table

    variants = [(1, 4, 0), (1, 6, 0), (1, 8, 0)]
    if gamma == 2:
        variants += [(0.5, 4, 0), (1, 4, 4)]
    elif gamma == 2.2:
        variants = [(1, 4, 0), (1, 6, 0)]
    selected, missing = [], []
    metadata = {}

    def code(v):
        return f"{v:g}".replace(".", "p")

    for history in HISTORIES:
        for vy, horizon, weight in variants:
            # N4 g2.2 is the retained fixed/smooth stress comparison only.
            if gamma == 2.2 and horizon == 4 and history not in ["fixed", "smooth"]:
                continue
            name = f"g{code(gamma)}_w{code(weight)}_vy{code(vy)}_r1_n{horizon}_{history}_l1"
            folder = ROOT / name
            if not (folder / "analysis.json").exists():
                missing.append(name)
                continue
            selected.append(folder)
            metadata[name] = dict(history=history, horizon=horizon, alpha_vy=vy, weight=weight)
    if not selected:
        raise ValueError("No analyzed histories")
    stem = "g" + code(gamma)
    global_prefix = compare(selected, ROOT / f"{stem}_all_histories_common_progress.json")
    per_history = {}
    for history in HISTORIES:
        folders = [p for p in selected if metadata[p.name]["history"] == history]
        if folders:
            per_history[history] = compare(folders, ROOT / f"{stem}_{history}_common_progress.json")
    fields = [
        ("case", "Case"),
        ("completed_laps", "Lap-end crossings"),
        ("whole_boundary", "Whole-record boundary samples"),
        ("prefix_boundary", "Common-prefix boundary samples"),
        ("native_end", "Native end m"),
        ("heading_tv", "epsi TV rad"),
        ("steering_tv", "Nominal steering TV rad"),
        ("rate_limit_s", "Rate-limit s"),
        ("clearance", "Prefix clearance min m"),
        ("tracking_ey", "Prefix ey RMS m"),
    ]

    def rows(report):
        result = []
        for c in report["cases"]:
            summary = json.loads((ROOT / c["case"] / "summary.json").read_text())
            laps = c["lap_prefixes"]
            result.append(
                dict(
                    case=c["case"],
                    completed_laps=c["complete_laps"],
                    whole_boundary=summary["boundary_violations"],
                    prefix_boundary=c["boundary_samples"],
                    native_end=c["sampled_end_m"],
                    heading_tv=sum(x["planned_heading_total_variation"] for x in laps),
                    steering_tv=sum(x["planned_steering_total_variation"] for x in laps),
                    rate_limit_s=sum(x["actual_rate_limit_s"] for x in laps),
                    clearance=c["clearance_min"],
                    tracking_ey=c["tracking_ey_rms"],
                )
            )
        return result

    lines = [
        f"# Task007C gamma{gamma:g} retained timing histories",
        "",
        f"{len(selected)} analyzed records; {len(missing)} pending. "
        + ("INTERIM." if missing else "Requested history matrix analyzed."),
        "",
        "The first counted lap begins at s_abs=1m and is a rolling segment. "
        "Finite histories are never padded or cycled. A trace-exhausted record without a lap "
        "is censored, not a lap-completion pass. Whole-record boundary failures remain visible "
        "even if the matched prefix ends before them. Native endpoints differ by sampling; "
        "the final retained endpoint contributes zero forward interval.",
        "",
        "## Common progress across every listed record",
        "",
        f"Shared requested interval: {global_prefix['cases'][0]['shared_start_m']:.6f}–"
        f"{global_prefix['cases'][0]['shared_end_m']:.6f}m. "
        "The table uses lap-prefix metrics with lap seams reset. It is deliberately separate "
        "from full-lap outcomes and from per-history comparisons below.",
        "",
        table(rows(global_prefix), fields),
        "",
    ]
    for history, report in per_history.items():
        lines += [
            f"## Matched {history} prefix",
            "",
            f"Shared requested end: {report['cases'][0]['shared_end_m']:.6f}m. "
            "This may be longer than the all-history intersection.",
            "",
            table(rows(report), fields),
            "",
        ]
    if missing:
        lines += ["## Pending analyzed records", "", *["- " + name for name in missing], ""]
    lines += [
        "Matched baseline/candidate pairs share the same original availability sequence. "
        "These histories are a deliberately selected diagnostic set, not independent random "
        "samples. Their ranges describe sensitivity, not population confidence. Fresh "
        "measured repetitions and isolated compute cost remain separate acceptance layers.",
        "",
    ]
    output = Path(f"docs/TASK007C_{stem.upper()}_HISTORY_RESULTS.md")
    output.write_text("\n".join(lines))
    print(output, len(selected), "records,", len(missing), "pending", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--gamma", type=float, choices=[2, 2.1, 2.2], required=True)
    main(p.parse_args().gamma)
