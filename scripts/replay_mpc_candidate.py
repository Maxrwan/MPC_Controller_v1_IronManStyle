"""Replay a frozen selected controller without repeating the parameter search."""

import argparse
import json

from parameter_study.common import OUT, design, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=list("ABCD"), default="C")
    parser.add_argument("--mode", choices=["zero", "measured", "injected"], default="zero")
    parser.add_argument("--latency", type=float, default=0.0)
    parser.add_argument("--track", choices=["circle", "oval"], default="oval")
    args = parser.parse_args()
    selected = json.loads((OUT / "selected_candidates.json").read_text())[args.candidate]
    run(
        "replay",
        f"replay_{args.candidate}_{args.track}_{args.mode}",
        **design(selected),
        track=args.track,
        mode=args.mode,
        latency=args.latency,
        laps=2,
        duration=80.0,
    )


if __name__ == "__main__":
    main()
