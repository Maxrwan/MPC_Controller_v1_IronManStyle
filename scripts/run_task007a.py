"""Task 007A offline fixture and serialized-reference integration experiments."""

import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["generate", "validate", "run", "analyze"])
    p.add_argument("--fixture", type=Path, default=Path("configs/planning/synthetic_grand_prix_v1"))
    p.add_argument("--output", type=Path, default=Path("results/task007a"))
    p.add_argument("--mode", choices=["zero", "injected", "measured"], default="measured")
    p.add_argument("--duration", type=float, default=400)
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--worker", action="store_true")
    args = p.parse_args()
    if args.action == "generate":
        from task007a.generate import generate

        generate(args.fixture)
    elif args.action == "validate":
        from apex.planning_reference.reference import PlanningReference
        from apex.planning_reference.track import load_track

        track, _, identity = load_track(args.fixture / "track_source.json")
        ref = PlanningReference(args.fixture, track, identity)
        import json

        (args.fixture / "planning_validation.json").write_text(
            json.dumps(ref.validation, indent=2) + "\n"
        )
        print(ref.validation)
    elif args.action == "run":
        from task007a.run import dispatch

        dispatch(args)
    else:
        from task007a.analysis import analyze

        analyze(args.output, args.fixture)


if __name__ == "__main__":
    main()
