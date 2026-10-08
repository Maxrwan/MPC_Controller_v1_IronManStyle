"""Serialized fresh-SINGLE formulation cases with immutable per-cell manifests."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("results/task007c_resume")


def requires_review(folder, summary):
    issue = (
        summary["boundary_violations"]
        or summary["solver_failures"]
        or summary["planner_failures"]
        or summary["forecast_or_gain_failures"]
        or summary["fallback_events"]
        or (summary["failure"] and summary["stop_reason"] != "diagnostic_trace_exhausted")
    )
    if not issue:
        return False
    path = ROOT / "reviewed_failures.json"
    records = json.loads(path.read_text()) if path.exists() else {}
    review = records.get(folder.name)
    digest = hashlib.sha256((folder / "summary.json").read_bytes()).hexdigest()
    if review and review["summary_sha256"] == digest:
        print("Retained reviewed rejection", folder.name, review["decision"], flush=True)
        return False
    return True


def launch(
    gamma, history="fixed", weight=0, vy=1, r=1, horizon=4, laps=1, repeat=None, duration=120
):
    def code(v):
        return f"{v:g}".replace(".", "p")

    name = f"g{code(gamma)}_w{code(weight)}_vy{code(vy)}_r{code(r)}_n{horizon}_{history}_l{laps}"
    if repeat is not None:
        name += f"_rep{repeat:02d}"
    folder = ROOT / name
    spec = dict(
        gamma=gamma,
        history=history,
        progress_weight=weight,
        alpha_vy=vy,
        alpha_r=r,
        horizon=horizon,
        laps=laps,
        repeat=repeat,
        duration=duration,
    )
    if (folder / "summary.json").exists():
        assert json.loads((folder / "cell.json").read_text()) == spec
        print("Retained", name, flush=True)
    else:
        folder.mkdir(exist_ok=True)
        (folder / "cell.json").write_text(json.dumps(spec, indent=2) + "\n")
        fixture = "configs/planning/task007c_resume/gamma_" + f"{gamma:.3f}".replace(".", "p")
        command = [
            sys.executable,
            "scripts/run_task007c_resume.py",
            "--case",
            name,
            "--fixture",
            fixture,
            "--gamma",
            str(gamma),
            "--progress-weight",
            str(weight),
            "--alpha-vy",
            str(vy),
            "--alpha-r",
            str(r),
            "--horizon",
            str(horizon),
            "--laps",
            str(laps),
            "--duration",
            str(duration),
        ]
        if history == "measured":
            command += ["--timing", "normal"]
        elif history == "fixed":
            command += ["--timing", "fixed"]
        else:
            histories = json.loads((ROOT / "histories.json").read_text())
            command += ["--timing", "replay", "--trace", histories[history]["path"]]
        subprocess.run(command, check=True)
    summary = json.loads((folder / "summary.json").read_text())
    print(
        name,
        {
            k: summary[k]
            for k in [
                "stop_reason",
                "failure",
                "lap_times",
                "boundary_violations",
                "solver_failures",
                "planner_misses",
                "codriver_misses",
            ]
        },
        flush=True,
    )
    return folder, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase", choices=["c1", "c1-progress", "c2", "c2-followup", "c3", "c4"]
    )
    parser.add_argument("--histories", nargs="+", default=["fixed", "smooth"])
    args = parser.parse_args()
    if args.phase == "c1":
        for history in args.histories:
            for gamma in [1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2]:
                folder, s = launch(gamma, history)
                if requires_review(folder, s):
                    (ROOT / "review_required.json").write_text(
                        json.dumps(
                            dict(
                                case=folder.name,
                                reason="Review failed case before extending region",
                            ),
                            indent=2,
                        )
                        + "\n"
                    )
                    raise RuntimeError(f"Review retained failure: {folder}")
    elif args.phase == "c2":
        pairs = [
            (1, 1),
            (0.5, 1),
            (0.25, 1),
            (0, 1),
            (1, 0.5),
            (1, 0.25),
            (1, 0),
            (0.25, 0.25),
            (0, 0),
        ]
        for history in args.histories:
            for gamma in [1.8, 2.0]:
                for vy, r in pairs:
                    folder, s = launch(gamma, history, vy=vy, r=r)
                    if requires_review(folder, s):
                        (ROOT / "review_required.json").write_text(
                            json.dumps(
                                dict(
                                    case=folder.name,
                                    reason="Review failed ablation before extension",
                                ),
                                indent=2,
                            )
                            + "\n"
                        )
                        raise RuntimeError(f"Review retained failure: {folder}")
    elif args.phase == "c2-followup":
        # Only half-vy retained a smoothness improvement at gamma2 in both C1 histories.
        # Test one higher-demand point and one progress-enabled point, keeping N4.
        for history in args.histories:
            for gamma, weight in [(2.1, 0), (2.0, 2)]:
                folder, s = launch(gamma, history, weight=weight, vy=0.5, r=1)
                if requires_review(folder, s):
                    (ROOT / "review_required.json").write_text(
                        json.dumps(dict(case=folder.name, reason="Review C2 follow-up"), indent=2)
                        + "\n"
                    )
                    raise RuntimeError(f"Review retained failure: {folder}")
    else:
        # Original approved near-transition grid. Keep baseline costs and isolate
        # horizon from progress pressure rather than testing combinations here.
        for history in args.histories:
            gammas = [1.9, 2.0, 2.1] if args.phase == "c4" else [1.8, 2.0, 2.1]
            for gamma in gammas:
                values = (
                    [4, 6, 8]
                    if args.phase == "c3"
                    else ([2] if args.phase == "c1-progress" else [0, 0.5, 1, 2, 4])
                )
                for value in values:
                    kwargs = {"horizon": value} if args.phase == "c3" else {"weight": value}
                    folder, s = launch(gamma, history, **kwargs)
                    if requires_review(folder, s):
                        (ROOT / "review_required.json").write_text(
                            json.dumps(
                                dict(case=folder.name, reason=f"Review {args.phase} failure"),
                                indent=2,
                            ) + "\n"
                        )
                        raise RuntimeError(f"Review retained failure: {folder}")
    print("Phase complete", args.phase, flush=True)


if __name__ == "__main__":
    main()
