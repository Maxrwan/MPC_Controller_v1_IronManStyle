"""Read actual retained CSVs. Missing columns are never synthesized."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def read_frame(directory: Path, name: str):
    path = directory / "experiment" / name
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


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
    return style(figure, "Y [m]", xy=True)


def series(runs, columns, ylabel, *, reference=None):
    figure = go.Figure()
    for label, directory in runs:
        states = read_frame(directory, "states.csv")
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
