"""Short deterministic chronology checks for horizon candidates; no wall-time assertions."""

import bisect
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("results/task007c_resume")


def read_rows(folder, name):
    with (folder / name).open() as handle:
        return list(csv.DictReader(handle))


def verify(folder, mode):
    s = json.loads((folder / "summary.json").read_text())
    events = json.loads((folder / "events.json").read_text())
    plans = [p for p in events["plans"] if not p["startup"] and p.get("completed")]
    controls = read_rows(folder, "controls.csv")
    states = read_rows(folder, "states.csv")
    times = [float(row["time"]) for row in states]
    progress = [float(row["s_abs"]) for row in states]

    def at(time):
        j = bisect.bisect_right(times, time) - 1
        if j == len(times) - 1:
            return progress[j]
        ratio = (time - times[j]) / (times[j + 1] - times[j])
        return progress[j] + ratio * (progress[j + 1] - progress[j])

    staleness = [
        at(float(c["application_time"])) - at(float(c["time"]))
        for c in controls
        if times[0] <= float(c["time"]) <= float(c["application_time"]) <= times[-1]
    ]
    moving = [abs(p["actual_state"][4] - p["source_state"][4]) for p in plans]
    driver_during_plan = sum(
        any(p["release_time"] < float(c["time"]) < p["completion_time"] for c in controls)
        for p in plans
    )
    report = dict(
        case=folder.name,
        mode=mode,
        observed_duration_s=s["end_time"],
        completed_plans=len(plans),
        solver_failures=s["solver_failures"],
        planner_misses=s["planner_misses"],
        codriver_misses=s["codriver_misses"],
        max_plant_progress_during_solve_m=max(moving),
        max_application_progress_staleness_m=max(staleness),
        completed_plans_with_codriver_execution_inside=driver_during_plan,
        injected_planner_delay_s=0.15 if mode == "injected_both" else 0,
        injected_codriver_delay_s=0.025 if mode == "injected_both" else 0,
        note="Physical event chronology only; preparation wall times are not benchmarked.",
    )
    assert s["failure"] is None and s["boundary_violations"] == 0, report
    for key in [
        "solver_failures",
        "planner_failures",
        "forecast_or_gain_failures",
        "fallback_events",
    ]:
        assert s[key] == 0, (key, report)
    assert plans and staleness, report
    if mode == "zero":
        assert s["planner_misses"] == s["codriver_misses"] == 0, report
        assert max(abs(v) for v in moving) == max(abs(v) for v in staleness) == 0, report
    else:
        assert s["planner_misses"] > 0 and s["codriver_misses"] > 0, report
        assert max(moving) > 0 and max(staleness) > 0 and driver_during_plan > 0, report
    return report


def main():
    reports = []
    for horizon in [6, 8]:
        for mode in ["zero", "injected_both"]:
            name = f"latency_n{horizon}_{mode}"
            folder = ROOT / name
            spec = dict(
                horizon=horizon,
                gamma=2,
                progress_weight=0,
                alpha_vy=1,
                alpha_r=1,
                duration=0.8,
                mode=mode,
                planner_delay=0.15 if mode == "injected_both" else 0,
                codriver_delay=0.025 if mode == "injected_both" else 0,
            )
            folder.mkdir(exist_ok=True)
            manifest = folder / "latency_cell.json"
            if manifest.exists():
                assert json.loads(manifest.read_text()) == spec
            else:
                manifest.write_text(json.dumps(spec, indent=2) + "\n")
            if not (folder / "summary.json").exists():
                args = [
                    sys.executable,
                    "scripts/run_task007c_resume.py",
                    "--case",
                    name,
                    "--fixture",
                    "configs/planning/task007c_resume/gamma_2p000",
                    "--gamma",
                    "2",
                    "--progress-weight",
                    "0",
                    "--horizon",
                    str(horizon),
                    "--duration",
                    ".8",
                    "--mode",
                    "zero" if mode == "zero" else "injected",
                ]
                if mode == "injected_both":
                    args += [
                        "--injected-delay",
                        ".15",
                        "--timing",
                        "fixed",
                        "--plan-delay",
                        ".15",
                        "--driver-delay",
                        ".025",
                    ]
                subprocess.run(args, check=True)
            report = verify(folder, mode)
            reports.append(report)
            print(json.dumps(report), flush=True)
    (ROOT / "candidate_latency_checks.json").write_text(json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    main()
