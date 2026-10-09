"""Post-hoc sensitivity of the existing reversal metric, never an acceptance gate."""

import csv
import json
from pathlib import Path

from threading_study.config import configure_accelerate

ROOT = Path("results/task007c_resume")
DEADBANDS = [0.0001, 0.001, 0.01, 0.05, 0.1, 0.25]


def main():
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not analyze during measured repetitions")
    configure_accelerate(1)
    import pandas as pd
    from task007c.metrics import steering_activity

    rows = []
    for horizon in [4, 6, 8]:
        for folder in sorted(ROOT.glob(f"g2_w0_vy1_r1_n{horizon}_measured_l1_rep*")):
            telemetry = pd.read_csv(folder / "telemetry.csv")
            summary = json.loads((folder / "summary.json").read_text())
            row = dict(case=folder.name, horizon=horizon, completed=bool(summary["lap_times"]))
            for deadband in DEADBANDS:
                row[str(deadband)] = steering_activity(
                    telemetry.delta, telemetry.time, deadband=deadband
                )["rate_sign_reversals"]
            rows.append(row)
    with (ROOT / "measured_reversal_deadband_sensitivity.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    method = dict(
        method="Post-hoc descriptive sensitivity of existing steering_activity metric, using "
        "the same native telemetry grid and physical delta as the original measure. Filter "
        "rate magnitudes below each listed rad/s deadband before counting sign changes. "
        "These deadbands are not acceptance thresholds. Incomplete N6 retains its outcome "
        "and cannot be compared as a full-run count.",
        deadbands_rad_s=DEADBANDS,
    )
    (ROOT / "measured_reversal_deadband_method.json").write_text(
        json.dumps(method, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
