"""Task006.2 staged experiments; unchanged plant and synchronous IPOPT architecture."""

import argparse
import json
from dataclasses import asdict

from parameter_study.common import (
    OUT,
    choice,
    database,
    design,
    run,
    save_choice,
    select_stage,
)
from parameter_study.fidelity import measure

from apex.control.mpc.cost import CostScales


def stage_a():
    for track in ("circle", "oval"):
        for mode in ("zero", "measured"):
            run("A", f"reference_{track}_{mode}", track=track, mode=mode, laps=2, duration=80.0)


def stage_b():
    for n in (8, 10, 12, 15, 20, 25):
        run("B", f"horizon_{n}", n=n)
    viable = [r for r in select_stage("B") if r["quality_pass"]]
    if not viable:
        raise RuntimeError("No quality-qualified horizon; inspect results before continuing")
    save_choice("horizon_compute", min(viable, key=lambda r: r["summary"]["solve_time"]["p95"]))
    save_choice("horizon_tracking", min(viable, key=lambda r: r["summary"]["full_run"]["rms_e_y"]))


def stage_c():
    horizons = sorted(
        {
            choice("horizon_compute")["configuration"]["n"],
            choice("horizon_tracking")["configuration"]["n"],
        }
    )
    for substeps in (1, 2, 3, 5):
        fidelity = measure(0.05, substeps)
        for n in horizons:
            r = run("C", f"integration_n{n}_s{substeps}", n=n, substeps=substeps)
            r["prediction_accuracy"] = fidelity
            if not fidelity["accuracy_pass"]:
                r["rejection_reasons"].append("prediction_accuracy_gate")
                r["status"] = "rejected"
                r["quality_pass"] = False
            (OUT / "runs" / r["id"] / "experiment.json").write_text(json.dumps(r, indent=2) + "\n")
    viable = [r for r in select_stage("C") if r["quality_pass"]]
    save_choice("integration", min(viable, key=lambda r: r["summary"]["solve_time"]["p95"]))
    database()


def stage_d():
    substeps = choice("integration")["configuration"]["substeps"]
    for hz in (10, 15, 20, 25):
        fidelity = measure(1 / hz, substeps)
        settings = [(substeps, fidelity)]
        used = substeps
        while not fidelity["accuracy_pass"] and used < 10:
            used += 1
            fidelity = measure(1 / hz, used)
        if used != substeps:
            settings.append((used, fidelity))
        # Preserve the literal fixed-substep comparison, even when inaccurate;
        # an additional refined variant may restore accuracy at the slower rate.
        for used, accuracy in settings:
            for mode in ("zero", "measured"):
                r = run(
                    "D",
                    f"frequency_{hz}_s{used}_{mode}",
                    hz=float(hz),
                    n=hz,
                    substeps=used,
                    mode=mode,
                )
                r["prediction_accuracy"] = accuracy
                if not accuracy["accuracy_pass"]:
                    if "prediction_accuracy_gate" not in r["rejection_reasons"]:
                        r["rejection_reasons"].append("prediction_accuracy_gate")
                    r["status"] = "rejected"
                    r["quality_pass"] = False
                (OUT / "runs" / r["id"] / "experiment.json").write_text(
                    json.dumps(r, indent=2) + "\n"
                )
    # Stage B selected 0.4-second coverage; test that same coverage across rates
    # after the required one-second comparison, without a Cartesian search.
    coverage = choice("horizon_compute")["configuration"]["n"] / 20
    for hz in (10, 15, 20, 25):
        used = substeps
        accuracy = measure(1 / hz, used)
        while not accuracy["accuracy_pass"] and used < 10:
            used += 1
            accuracy = measure(1 / hz, used)
        n = round(coverage * hz)
        for mode in ("zero", "measured"):
            r = run(
                "D", f"short_frequency_{hz}_{mode}", hz=float(hz), n=n, substeps=used, mode=mode
            )
            r["prediction_accuracy"] = accuracy
            if not accuracy["accuracy_pass"]:
                if "prediction_accuracy_gate" not in r["rejection_reasons"]:
                    r["rejection_reasons"].append("prediction_accuracy_gate")
                r["status"], r["quality_pass"] = "rejected", False
            (OUT / "runs" / r["id"] / "experiment.json").write_text(json.dumps(r, indent=2) + "\n")
    viable = [
        r for r in select_stage("D") if r["quality_pass"] and r["configuration"]["mode"] == "zero"
    ]
    # Select structural screening anchor by margin, subject to quality and accuracy.
    save_choice("frequency", min(viable, key=lambda r: r["compute_ratio_p95"]))
    database()


def stage_e():
    anchor = design(choice("frequency"))
    for group, values in [
        ("lateral", (0.5, 1, 2)),
        ("dynamic", (0.5, 1, 2)),
        ("speed", (0.5, 1, 2)),
        ("control", (0.5, 1, 2)),
        ("rate", (0.25, 0.5, 1, 2)),
    ]:
        for value in values:
            costs = {**asdict(CostScales()), group: value}
            run("E", f"weight_{group}_{value}", **{**anchor, "costs": costs})
    viable = [r for r in select_stage("E") if r["quality_pass"]]
    # Only one evidence-led combination: best lateral-tracking setting plus best
    # speed-tracking setting, if they modify distinct groups.
    lateral = min(viable, key=lambda r: r["summary"]["full_run"]["rms_e_y"])
    speed = min(viable, key=lambda r: r["summary"]["full_run"]["rms_speed_error"])
    costs = {**lateral["configuration"]["costs"]}
    for k, v in speed["configuration"]["costs"].items():
        if v != 1 and costs[k] == 1:
            costs[k] = v
    run("E", "weight_combined", **{**anchor, "costs": costs})
    viable = [r for r in select_stage("E") if r["quality_pass"]]
    save_choice("weights", min(viable, key=lambda r: r["summary"]["full_run"]["rms_e_y"]))


def stage_f():
    anchor = design(choice("weights"))
    for value in (0, 1, 0.5, 2):
        run("F", f"terminal_{value}", **{**anchor, "costs": {**anchor["costs"], "terminal": value}})
    viable = [r for r in select_stage("F") if r["quality_pass"]]
    save_choice("terminal", min(viable, key=lambda r: r["summary"]["full_run"]["rms_e_y"]))


def stage_g():
    anchor = design(choice("terminal"))
    options = [
        ("current", {}),
        ("max40", {"ipopt.max_iter": 40}),
        ("tol1e6", {"ipopt.tol": 1e-6, "ipopt.acceptable_tol": 1e-6}),
        ("strict", {"ipopt.tol": 1e-8, "ipopt.acceptable_tol": 1e-7}),
        ("limited_memory", {"ipopt.hessian_approximation": "limited-memory"}),
        ("warm_flag", {"ipopt.warm_start_init_point": "yes"}),
    ]
    for name, solver in options:
        run("G", f"ipopt_{name}", **{**anchor, "solver": solver})
    viable = [r for r in select_stage("G") if r["quality_pass"]]
    save_choice("solver", min(viable, key=lambda r: r["summary"]["solve_time"]["p95"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=list("ABCDEFG") + ["all", "analyze", "validate", "warm", "report"],
        required=True,
    )
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    stages = dict(zip("ABCDEFG", [stage_a, stage_b, stage_c, stage_d, stage_e, stage_f, stage_g]))
    if args.stage == "all":
        for stage, fn in stages.items():
            print("STAGE", stage, flush=True)
            fn()
        from parameter_study.analysis import analyze, validate_selected, warm_benchmark

        analyze()
        validate_selected()
        warm_benchmark()
        analyze()
        from parameter_study.report import generate

        generate()
    elif args.stage == "report":
        from parameter_study.report import generate

        generate()
    elif args.stage == "analyze":
        from parameter_study.analysis import analyze

        analyze()
    elif args.stage == "validate":
        from parameter_study.analysis import validate_selected

        validate_selected()
    elif args.stage == "warm":
        from parameter_study.analysis import warm_benchmark

        warm_benchmark()
    else:
        stages[args.stage]()
    database()


if __name__ == "__main__":
    main()
