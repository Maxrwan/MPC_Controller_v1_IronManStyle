"""Task007C resumed formulation study: fresh single-native-thread diagnostic worker."""

import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", required=True)
    p.add_argument("--gamma", type=float, default=2.5)
    p.add_argument("--progress-weight", type=float, default=1)
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("results/task007c_resume"))
    p.add_argument("--mode", choices=["zero", "injected", "measured"], default="measured")
    p.add_argument("--timing", choices=["normal", "fixed", "replay"], default="normal")
    p.add_argument("--trace", type=Path)
    p.add_argument("--plan-delay", type=float, default=0.035)
    p.add_argument("--driver-delay", type=float, default=0.001)
    p.add_argument("--perturb-index", type=int)
    p.add_argument("--perturb-ms", type=float, default=0)
    p.add_argument("--laps", type=int, default=1)
    p.add_argument("--duration", type=float, default=100)
    p.add_argument("--injected-delay", type=float, default=0.06)
    p.add_argument("--capture", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--horizon", type=int, choices=[4, 6, 8], default=4)
    p.add_argument("--alpha-vy", type=float, default=1.0)
    p.add_argument("--alpha-r", type=float, default=1.0)
    p.add_argument("--worker", action="store_true")
    args = p.parse_args()
    if args.timing == "replay" and args.trace is None:
        p.error("replay requires --trace")
    from task007c_resume.run import dispatch

    dispatch(args)


if __name__ == "__main__":
    main()
