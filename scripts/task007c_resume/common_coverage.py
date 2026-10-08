"""Compare retained histories on a disclosed shared progress prefix, without inventing tails."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from task007c.metrics import traversal_metrics


def compare(folders, output):
    frames = {str(p): pd.read_csv(Path(p) / "telemetry.csv") for p in folders}
    start = max(t.s_abs.iloc[0] for t in frames.values())
    end = min(t.s_abs.iloc[-1] for t in frames.values())
    if end <= start:
        raise ValueError("No shared progress coverage")
    rows = []
    for name, frame in frames.items():
        t = frame[(frame.s_abs >= start) & (frame.s_abs <= end)].copy()
        # The last retained sample is an endpoint, not permission to include
        # its following interval outside the disclosed native progress range.
        t.loc[t.index[-1], "interval"] = 0.0
        s = pd.read_csv(Path(name) / "states.csv")
        s = s[(s.s_abs >= start) & (s.s_abs <= end)]
        summary = json.loads((Path(name) / "summary.json").read_text())
        row = dict(
            case=Path(name).name,
            shared_start_m=float(start),
            shared_end_m=float(end),
            sampled_start_m=float(t.s_abs.iloc[0]),
            sampled_end_m=float(t.s_abs.iloc[-1]),
            duration_s=float(t.time.iloc[-1] - t.time.iloc[0]),
            complete_laps=len(summary["lap_times"]),
            stop_reason=summary["stop_reason"],
            boundary_samples=int(s.boundary_violation.sum()),
            beta_p95=float(np.quantile(abs(t.actual_beta), 0.95)),
            beta_max=float(abs(t.actual_beta).max()),
            front_util_max=float(t.front_utilization.max()),
            rear_util_max=float(t.rear_utilization.max()),
            clearance_min=float(t.clearance.min()),
            slack_max=float(t.predicted_slack.max()),
            tracking_ey_rms=float(np.sqrt(np.mean(t.error_e_y**2))),
        )
        # Preserve traversal boundaries and provide individual metrics, not a score.
        traversals = []
        for (lap, sector), group in t.groupby(["lap", "sector"], sort=False):
            if len(group) >= 3 and group.s_abs.iloc[-1] > group.s_abs.iloc[0]:
                traversals.append(dict(lap=int(lap), sector=sector, **traversal_metrics(group)))
        row["traversals"] = traversals
        row["lap_prefixes"] = [
            dict(lap=int(lap), **traversal_metrics(group))
            for lap, group in t.groupby("lap", sort=False)
            if len(group) >= 3 and group.s_abs.iloc[-1] > group.s_abs.iloc[0]
        ]
        rows.append(row)
    payload = dict(
        method=(
            "Intersection of observed progress ranges. Native samples retained; no tail padding "
            "or interpolation. Sector and lap differences reset at traversal boundaries. "
            "Partial sectors remain explicitly bounded by their exported distances. "
            "Last native endpoint contributes zero forward interval; lap-prefix and "
            "individual sector metrics are both retained."
        ),
        cases=rows,
    )
    Path(output).write_text(json.dumps(payload, indent=2) + "\n")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    compare(args.folders, args.output)
