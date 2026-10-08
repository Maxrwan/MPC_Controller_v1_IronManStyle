"""Ordered offline validation, cross replay, then uncontended measured repetitions."""

import json
import subprocess
import sys
from pathlib import Path

OUT = Path("results/task007cr")


def main():
    steps = [
        ("pre_measured_analysis", [sys.executable, "scripts/task007cr/analyze_all.py"]),
        (
            "focused_regression",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/unit/test_diagnostic_timing.py",
                "tests/unit/test_nlp_snapshot.py",
                "tests/unit/test_async_chronology.py",
            ],
        ),
        ("backend_audit", [sys.executable, "scripts/task007cr/backend_audit.py"]),
        ("cross_replay", [sys.executable, "scripts/task007cr/campaign.py", "cross"]),
        ("measured_repeats", [sys.executable, "scripts/task007cr/campaign.py", "measured"]),
    ]
    for name, command in steps:
        (OUT / "campaign_stage.json").write_text(
            json.dumps(dict(stage=name, status="running")) + "\n"
        )
        print("Starting", name, flush=True)
        with (OUT / (name + ".log")).open("w") as log:
            status = subprocess.run(command, stdout=log, stderr=log)
        if status.returncode:
            (OUT / "campaign_stage.json").write_text(
                json.dumps(dict(stage=name, status="failed", returncode=status.returncode)) + "\n"
            )
            raise RuntimeError(str(OUT / (name + ".log")))
        print("Finished", name, flush=True)
    (OUT / "campaign_stage.json").write_text(
        json.dumps(dict(stage="campaign", status="complete")) + "\n"
    )


if __name__ == "__main__":
    main()
