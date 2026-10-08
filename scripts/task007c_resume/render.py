"""Fresh SINGLE offline rendering entry point; never run alongside measured repetitions."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("results/task007c_resume")


def render(args):
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not compete with active measured repetitions")

    from threading_study.config import configure_accelerate

    configure_accelerate(1)
    from task007c_resume.dashboard import dashboard
    from task007c_resume.formulation_plots import plot as formulation_plot
    from task007c_resume.physics_plots import phase_portraits, plots
    from task007c_resume.transition_plot import plot as transition_plot

    folders = [ROOT / name for name in args.cases]
    for folder in folders:
        validation = folder / "physics_validation.json"
        if not validation.exists() or json.loads(validation.read_text()).get("schema_version") != 2:
            raise ValueError(f"Complete physics export first: {folder}")
        plots(folder)
        dashboard(folder)
        for sector in args.sectors:
            dashboard(folder, sector)
        print("Rendered", folder.name, flush=True)
    if args.phase_output:
        if not folders:
            raise ValueError("Phase portraits require cases")
        phase_portraits(folders, ROOT / args.phase_output)
    for phase in args.comparisons:
        transition_plot() if phase == "c1" else formulation_plot(phase)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="*", default=[])
    parser.add_argument(
        "--sectors",
        nargs="*",
        default=[],
        choices=["hairpin", "technical_section", "fast_sweeper", "return_complex"],
    )
    parser.add_argument("--phase-output")
    parser.add_argument("--comparisons", nargs="*", default=[], choices=["c1", "c2", "c3", "c4"])
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        render(args)
    else:
        from threading_study.config import environment

        env = environment(1)
        env.update(
            MPLCONFIGDIR="/private/tmp/apex-matplotlib", XDG_CACHE_HOME="/private/tmp/apex-cache"
        )
        subprocess.run([sys.executable, __file__, *sys.argv[1:], "--worker"], env=env, check=True)
