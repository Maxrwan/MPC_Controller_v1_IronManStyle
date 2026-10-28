"""Read actual retained CSVs. Missing columns are never synthesized."""

import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from tools.apex_workbench import storage
from tools.apex_workbench.storage import IntegrityError


def read_frame(directory: Path, name: str):
    request = storage.read_request(directory, verified=True)
    status = storage.read_status(directory)
    storage.check_required_artifacts(directory, request, status)
    relative = "experiment/" + name
    contents = storage.artifact_bytes(
        directory, relative, optional=relative not in storage.required_artifacts(request, status)
    )
    if contents is None:
        return pd.DataFrame()
    if request["adapter"] == "dynamic_lab":
        from tools.apex_workbench.lab_evidence import read_record

        read_record(directory)
    try:
        data = pd.read_csv(
            io.BytesIO(contents),
            **({"float_precision": "round_trip"} if request["adapter"] == "dynamic_lab" else {}),
        )
        required = {
            "states.csv": ["time", "vx", "vy", "r", "e_psi", "s_abs", "e_y", "delta", "a_cmd"],
            "controls.csv": ["time", "delta", "a_cmd"],
            "geometry.csv": ["s", "x", "y", "left_x", "left_y", "right_x", "right_y"],
            "trajectory_xy.csv": ["time", "x", "y"],
            "diagnostics.csv": [
                "time",
                "alpha_f",
                "alpha_r",
                "fyf",
                "fyr",
                "fzf",
                "fzr",
                "cf_eff",
                "cr_eff",
                "front_lateral_utilization",
                "rear_lateral_utilization",
                "frenet_denominator",
            ],
        }[name]
        if data.empty or not set(required) <= set(data.columns):
            raise IntegrityError("Incomplete telemetry columns/rows: " + name)
        if data[required].isna().any().any():
            raise IntegrityError("Incomplete telemetry values: " + name)
        return data
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError) as error:
        raise IntegrityError("Unreadable telemetry: " + name) from error


def style(figure, ylabel, *, xy=False):
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=12, t=24, b=12),
        xaxis_title="X [m]" if xy else "Time [s]",
        yaxis_title=ylabel,
        legend=dict(orientation="h", y=1.12),
        height=440 if xy else 290,
    )
    if xy:
        figure.update_yaxes(scaleanchor="x", scaleratio=1)
    return figure


def trajectory(directory):
    geometry = read_frame(directory, "geometry.csv")
    xy = read_frame(directory, "trajectory_xy.csv")
    figure = go.Figure()
    if not geometry.empty:
        for x, y, name, color in (
            ("x", "y", "Centerline", "#8495ad"),
            ("left_x", "left_y", "Left boundary", "#455c76"),
            ("right_x", "right_y", "Right boundary", "#455c76"),
        ):
            figure.add_trace(
                go.Scatter(
                    x=geometry[x], y=geometry[y], name=name, line=dict(color=color, dash="dot")
                )
            )
    if not xy.empty:
        figure.add_trace(
            go.Scatter(x=xy.x, y=xy.y, name="Plant trajectory", line=dict(color="#3ee0b2", width=3))
        )
    if geometry.empty or xy.empty:
        missing = "Track geometry" if geometry.empty else "Plant trajectory"
        figure.add_annotation(
            text=missing + " unavailable in this record",
            x=0.5,
            y=1.0,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
    return style(figure, "Y [m]", xy=True)


def series(runs, columns, ylabel, *, reference=None, source="states.csv"):
    figure = go.Figure()
    for label, directory in runs:
        states = read_frame(directory, source)
        for column in columns:
            if column in states:
                figure.add_trace(
                    go.Scatter(x=states.time, y=states[column], name=f"{label} · {column}")
                )
        if reference:
            controls = read_frame(directory, "controls.csv")
            if reference in controls:
                figure.add_trace(
                    go.Scatter(
                        x=controls.time,
                        y=controls[reference],
                        name=f"{label} · {reference}",
                        line=dict(dash="dash"),
                    )
                )
    return style(figure, ylabel)
