"""Augment cached physical/node telemetry with independent oscillation diagnostics."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from task007b.metrics import distribution
from task007c.metrics import prediction_diagnostics, traversal_metrics


def export_case(folder):
    folder = Path(folder)
    summary = json.loads((folder / "summary.json").read_text())
    telemetry = pd.read_csv(folder / "telemetry.csv")
    predictions = json.loads((folder / "predictions.json").read_text())
    events = json.loads((folder / "events.json").read_text())
    accepted = {p["plan_id"] for p in events["handoffs"] if p["accepted"]}
    accepted.add(0)  # Gated startup packet.
    prepared = {p["plan_id"] for p in events["plans"] if p.get("preparation") == "prepared"}
    rows = []
    dt = summary["planner_config"]["dt"]
    for item in predictions:
        p = item["prediction"]
        if not p or "states" not in p:
            continue
        states, controls = np.asarray(p["states"]).T, np.asarray(p["controls"]).T
        rows.append(
            dict(
                plan_id=item["plan_id"],
                release_time=item["release_time"],
                packet_prepared=item["plan_id"] in prepared,
                handoff_accepted=item["plan_id"] in accepted,
                s_abs=float(states[0, 4]),
                **prediction_diagnostics(states, controls, dt),
            )
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(folder / "prediction_oscillation.csv", index=False)
    lookup = frame.set_index("plan_id")
    mapped = {
        "prediction_" + column: telemetry.plan_id.map(lookup[column])
        for column in frame.columns.difference(["plan_id", "release_time", "s_abs"])
    }
    telemetry = pd.concat([telemetry, pd.DataFrame(mapped, index=telemetry.index)], axis=1).copy()
    # Rolling variation is within each lap; it never includes a seam jump.
    for column in [
        "reference_e_psi",
        "reference_e_y",
        "reference_vy",
        "reference_r",
        "nominal_delta",
    ]:
        telemetry["rolling_TV_1s_" + column] = np.nan
        for _, group in telemetry.groupby("lap", sort=False):
            values = group[column].to_numpy()
            if column == "reference_e_psi":
                values = np.unwrap(values)
            series = pd.Series(
                np.r_[0, abs(np.diff(values))], index=pd.to_timedelta(group.time, unit="s")
            )
            telemetry.loc[group.index, "rolling_TV_1s_" + column] = (
                series.rolling("1s").sum().to_numpy()
            )
    telemetry.to_csv(folder / "diagnostic_telemetry.csv", index=False)
    traversals = []
    for (lap, sector), group in telemetry.groupby(["lap", "sector"], sort=False):
        if len(group) >= 3 and group.s_abs.iloc[-1] > group.s_abs.iloc[0]:
            traversals.append(dict(lap=int(lap), sector=sector, **traversal_metrics(group)))
    pd.DataFrame(traversals).to_csv(folder / "sector_oscillation.csv", index=False)
    lap_rows = []
    for lap, group in telemetry.groupby("lap", sort=False):
        if len(group) >= 3 and group.s_abs.iloc[-1] > group.s_abs.iloc[0]:
            lap_rows.append(dict(lap=int(lap), **traversal_metrics(group)))
    pd.DataFrame(lap_rows).to_csv(folder / "lap_oscillation.csv", index=False)
    costs = summary["planner_config"]["costs"]
    report = dict(
        case=folder.name,
        gamma=summary["gamma"],
        progress_weight=summary["progress_weight"],
        alpha_vy=costs.get("alpha_vy", 1),
        alpha_r=costs.get("alpha_r", 1),
        horizon=summary["planner_config"]["horizon"],
        dt=dt,
        predictions={
            c: distribution(frame[c])
            for c in frame.columns
            if c not in ["plan_id", "release_time", "s_abs"]
        },
        laps=lap_rows,
        sectors=traversals,
        note="Within-prediction steering excludes unavailable prior-control to u0 increment; "
        "active-plan steering jumps are not physical rate-limit violations.",
    )
    (folder / "oscillation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Oscillation export", folder.name, flush=True)
    return report


def export(output, cases=None):
    for path in sorted(Path(output).glob("*/analysis.json")):
        if not cases or path.parent.name in cases:
            export_case(path.parent)
