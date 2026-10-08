"""Sequential fresh measured repetitions; start only after all numerical jobs finish."""

import argparse
import json
import os
from datetime import datetime, timezone

from task007c_resume.campaign import ROOT, launch, requires_review


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", type=float, required=True)
    parser.add_argument("--horizons", type=int, nargs="+", choices=[4, 6, 8], required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1 or len(set(args.horizons)) != len(args.horizons):
        parser.error("Use positive repeats and distinct horizons")
    order = []
    for repeat in range(args.repeats):
        shift = repeat % len(args.horizons)
        rotated = args.horizons[shift:] + args.horizons[:shift]
        order += [dict(repeat=repeat, horizon=n) for n in rotated]
    plan = dict(
        gamma=args.gamma,
        horizons=args.horizons,
        repeats=args.repeats,
        alpha_vy=1,
        alpha_r=1,
        progress_weight=0,
        laps=1,
        sequence=order,
        method="Fresh SINGLE workers, one at a time. Rotate starting "
        "configuration by repetition to reduce fixed ordering bias. Five repetitions "
        "support descriptive distributions, not population confidence guarantees.",
    )
    tag = f"g{args.gamma:g}".replace(".", "p") + "_" + "_".join(f"n{n}" for n in args.horizons)
    path = ROOT / ("measured_plan_" + tag + ".json")
    if path.exists():
        assert json.loads(path.read_text()) == plan
    else:
        path.write_text(json.dumps(plan, indent=2) + "\n")
    journal = ROOT / ("measured_events_" + tag + ".jsonl")

    def event(kind, **details):
        with journal.open("a") as handle:
            handle.write(
                json.dumps(
                    dict(
                        event=kind,
                        utc=datetime.now(timezone.utc).isoformat(),
                        pid=os.getpid(),
                        **details,
                    )
                )
                + "\n"
            )

    lock = ROOT / "MEASURED_ACTIVE"
    with lock.open("x") as handle:
        json.dump(
            dict(
                pid=os.getpid(),
                plan=str(path),
                started_utc=datetime.now(timezone.utc).isoformat(),
                note="Do not start analysis, rendering, tests, benchmarks or other numerical "
                "jobs. This guard does not stop preexisting processes.",
            ),
            handle,
            indent=2,
        )
    os.environ["APEX_MEASURED_OWNER_PID"] = str(os.getpid())
    try:
        for cell in order:
            event("dispatch_or_reuse", **cell)
            folder, summary = launch(
                gamma=args.gamma, history="measured", horizon=cell["horizon"], repeat=cell["repeat"]
            )
            event(
                "result",
                case=folder.name,
                stop_reason=summary["stop_reason"],
                boundary_samples=summary["boundary_violations"],
                **cell,
            )
            if requires_review(folder, summary):
                (ROOT / "review_required.json").write_text(
                    json.dumps(
                        dict(
                            case=folder.name,
                            reason="Review measured outcome before continuing repetitions",
                        ),
                        indent=2,
                    )
                    + "\n"
                )
                raise RuntimeError(f"Review retained measured failure: {folder}")
    finally:
        event("harness_exit")
        os.environ.pop("APEX_MEASURED_OWNER_PID", None)
        lock.unlink()
    print("Measured plan complete", path, flush=True)


if __name__ == "__main__":
    main()
