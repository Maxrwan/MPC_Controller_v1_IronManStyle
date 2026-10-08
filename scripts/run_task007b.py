"""Task 007B sequential measured progress/aggression experiments."""

import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["generate", "validate", "run", "analyze", "plots"])
    p.add_argument("--gamma", type=float, default=1)
    p.add_argument("--gammas", type=float, nargs="+", default=[1, 1.25, 1.5, 1.75])
    p.add_argument("--progress-weight", type=float, default=0)
    p.add_argument("--case", default="b0")
    p.add_argument("--fixture", type=Path, default=None)
    p.add_argument("--cases", nargs="*", default=[])
    p.add_argument("--output", type=Path, default=Path("results/task007b"))
    p.add_argument("--mode", choices=["zero", "injected", "measured"], default="measured")
    p.add_argument("--laps", type=int, default=1)
    p.add_argument("--injected-delay", type=float, default=0.06)
    p.add_argument("--duration", type=float, default=100)
    p.add_argument("--worker", action="store_true")
    args = p.parse_args()
    if args.action == "generate":
        from task007b.references import generate

        generate(args.gammas)
    elif args.action == "validate":
        import json

        from task007b.references import PACKAGES, package_name

        from apex.planning_reference.reference import PlanningReference
        from apex.planning_reference.track import load_track

        fixture = PACKAGES / package_name(args.gamma)
        track, _, identity = load_track(fixture / "track_source.json")
        ref = PlanningReference(fixture, track, identity, feasibility_policy="advisory")
        print(json.dumps(ref.validation, indent=2))
    elif args.action == "plots":
        from task007b.render import render

        render(args.output, args.cases)
    elif args.action == "run":
        from task007b.run import dispatch

        dispatch(args)
    else:
        from task007b.analysis import analyze

        analyze(args.output, args.cases)


if __name__ == "__main__":
    main()
