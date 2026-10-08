"""Descriptive paired sector evidence; no fitted threshold, score, or adaptive policy."""

import json
from pathlib import Path


def main():
    from threading_study.config import configure_accelerate

    configure_accelerate(1)
    import numpy as np
    import pandas as pd
    from task007b.metrics import distribution
    from task007c.metrics import traversal_metrics

    ROOT = Path("results/task007c_resume")
    rows = []
    for p in sorted(ROOT.glob("g*/analysis.json")):
        c = json.loads((p.parent / "cell.json").read_text())
        if (
            c["gamma"] not in [1.9, 2, 2.1]
            or c["horizon"] != 4
            or c["alpha_vy"] != 1
            or c["alpha_r"] != 1
            or c["repeat"] is not None
            or c["history"] not in ["fixed", "smooth"]
            or c["laps"] != 1
        ):
            continue
        t = pd.read_csv(p.parent / "telemetry.csv")
        for (lap, sector), g in t.groupby(["lap", "sector"], sort=False):
            if len(g) < 3 or g.s_abs.iloc[-1] <= g.s_abs.iloc[0]:
                continue
            m = traversal_metrics(g)
            row = dict(
                case=p.parent.name,
                gamma=c["gamma"],
                history=c["history"],
                weight=c["progress_weight"],
                lap=int(lap),
                sector=sector,
                progress_start=g.s_abs.iloc[0],
                progress_end=g.s_abs.iloc[-1],
                duration_s=m["duration_s"],
                heading_tv=m["planned_heading_total_variation"],
                steering_tv=m["planned_steering_total_variation"],
                rate_limit_s=m["actual_rate_limit_s"],
                rate_limit_fraction=m["actual_rate_limit_fraction"],
                planned_reversals=m["planned_steering_reversals_db_0.0001"],
                actual_reversals=m["actual_steering_reversals_db_0.0001"],
                clearance_min=g.clearance.min(),
                slack_max=g.predicted_slack.max(),
                denominator_min=g.denominator.min(),
            )
            for field in [
                "front_utilization",
                "rear_utilization",
                "steering_utilization",
                "steering_rate_utilization",
                "actual_beta",
                "forecast_residual_e_y",
            ]:
                mask = np.isfinite(g[field]) & (g.interval > 0)
                stats = distribution(g.loc[mask, field], g.loc[mask, "interval"])
                for metric in ["p95_abs", "max_abs", "rms"]:
                    row[field + "_" + metric] = stats[metric]
            rows.append(row)
    t = pd.DataFrame(rows)
    base = t[t.weight == 0].set_index(["gamma", "history", "lap", "sector"])
    metrics = [
        "heading_tv",
        "steering_tv",
        "rate_limit_s",
        "duration_s",
        "clearance_min",
        "planned_reversals",
        "actual_reversals",
    ]
    for metric in metrics:
        t["baseline_" + metric] = [
            base.loc[(r.gamma, r.history, r.lap, r.sector), metric] for r in t.itertuples()
        ]
        t["delta_" + metric] = t[metric] - t["baseline_" + metric]
    t.to_csv(ROOT / "c4_paired_sector_feasibility.csv", index=False)
    (ROOT / "c4_paired_sector_feasibility_method.json").write_text(
        json.dumps(
            dict(
                rows=len(t),
                cases=int(t.case.nunique()),
                method="Native samples by lap and contiguous named sector, paired with same "
                "gamma/history/lap/sector lambda0. Spatial endpoints differ by sampling. "
                "RMS uses physical-interval weights; p95 is a sample quantile.",
                caveats=[
                    "Signals after changing lambda are responses, not independent predictors.",
                    "Held handoff forecast residual includes chronology and changed feedback; "
                    "it is not a one-step physical model residual.",
                    "No correlation, threshold, scalar score or adaptive switch is fitted.",
                    "Short seam fragments remain bounded separately from full sector traversals.",
                ],
            ),
            indent=2,
        )
        + "\n"
    )
    print("Exported", len(t), "sector traversals from", t.case.nunique(), "C4 cells")


if __name__ == "__main__":
    main()
