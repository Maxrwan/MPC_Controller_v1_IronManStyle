"""Task006.4: isolated sequential workers for low-level controller comparisons."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate, environment

OUT = ROOT / "results/linear_mpc_codriver"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=["run", "horizons", "comparisons", "analyze", "audit", "benchmark", "parity"],
    )
    parser.add_argument("--name", default="mpc_measured")
    parser.add_argument("--controller", choices=["tvlqr", "mpc"], default="mpc")
    parser.add_argument("--phase", choices=["replay", "closed"], default="closed")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--weight", type=float, default=0)
    parser.add_argument("--model", choices=["lti", "ltv"], default="ltv")
    parser.add_argument("--cold", action="store_true")
    parser.add_argument(
        "--scenario",
        choices=["nominal", "disturbance", "stress", "spike", "qp_failure"],
        default="nominal",
    )
    parser.add_argument("--mode", choices=["zero", "injected", "measured"], default="measured")
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--duration", type=float, default=80)
    parser.add_argument("--zero-codriver", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if args.action in ["analyze", "audit"]:
        from codriver_study.analysis import analyze, audit

        (analyze if args.action == "analyze" else audit)(args.output)
        return
    if args.action in ["horizons", "comparisons"]:
        cases = []
        if args.action == "horizons":
            cases = [["--name", "replay_tvlqr", "--controller", "tvlqr", "--phase", "replay"]]
            cases += [
                ["--name", f"replay_N{n}", "--phase", "replay", "--horizon", str(n)]
                for n in [3, 5, 8, 10, 15]
            ]
        else:
            for controller in ["tvlqr", "mpc"]:
                common = [
                    "--controller",
                    controller,
                    "--horizon",
                    str(args.horizon),
                    "--weight",
                    str(args.weight),
                    "--model",
                    args.model,
                ]
                for scenario in ["nominal", "disturbance", "stress", "qp_failure"]:
                    cases.append(
                        ["--name", f"{controller}_{scenario}", *common, "--scenario", scenario]
                    )
                for delay in [0.06, 0.1, 0.15]:
                    cases.append(
                        [
                            "--name",
                            f"{controller}_{round(delay * 1000)}ms",
                            *common,
                            "--mode",
                            "injected",
                            "--delay",
                            str(delay),
                            "--zero-codriver",
                        ]
                    )
                cases.append(
                    [
                        "--name",
                        f"{controller}_spike",
                        *common,
                        "--scenario",
                        "spike",
                        "--mode",
                        "injected",
                        "--delay",
                        ".025",
                        "--zero-codriver",
                    ]
                )
        for case in cases:
            subprocess.run(
                [sys.executable, __file__, "run", *case, "--output", str(args.output)],
                check=True,
                cwd=ROOT,
            )
        return
    if args.worker:
        native = configure_accelerate(1)
        if args.action == "run":
            from codriver_study.run import run

            run(args, native)
        else:
            from codriver_study.benchmark import run

            run(args, native)
        return
    folder = args.output / args.name
    if any((folder / name).exists() for name in ["summary.json", "timing.json", "parity.json"]):
        raise ValueError("Existing result retained; select a fresh name/output")
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "worker.log").open("w") as log:
        completed = subprocess.run(
            [sys.executable, __file__, *sys.argv[1:], "--worker"],
            cwd=ROOT,
            env=environment(1),
            stdout=log,
            stderr=log,
        )
    if completed.returncode:
        raise RuntimeError(f"Worker failed: {folder / 'worker.log'}")
    path = folder / "summary.json"
    print(
        args.name,
        json.loads(path.read_text()).get("stop_reason", "complete")
        if path.exists()
        else "complete",
        flush=True,
    )


if __name__ == "__main__":
    main()
