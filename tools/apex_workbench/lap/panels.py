"""Small Streamlit/Plotly extension; reuse accepted V1 replay and short-response analysis."""

import math

import plotly.graph_objects as go
import streamlit as st

from tools.apex_workbench import nmpc_scratch_panels as short
from tools.apex_workbench import storage

from . import analysis, config, evidence, execution, replay


def records():
    return (
        sorted(
            (p for p in config.RUNS.iterdir() if p.is_dir() and not p.name.startswith(".")),
            reverse=True,
        )
        if config.RUNS.exists()
        else []
    )


def run_panel(mode):
    value = config.defaults("full_lap" if mode == "Full Lap" else "extended")
    if mode == "Extended":
        value["maximum_simulation_s"] = st.selectbox(
            "Maximum simulated duration [s]", config.PROFILE["extended_seconds"], index=1
        )
    else:
        st.caption(
            "Native second finish-line crossing; first crossing from s_abs=1m is partial. "
            "Maximum80simulated seconds."
        )
    if st.button("Reset V2 costs to accepted baseline"):
        for name, number in value["scratch"]["costs"].items():
            st.session_state["lap_cost_" + name] = number
    columns = st.columns(2)
    for i, (name, number) in enumerate(value["scratch"]["costs"].items()):
        with columns[i % 2]:
            value["scratch"]["costs"][name] = st.number_input(
                name, value=number, min_value=0.0, key="lap_cost_" + name, help=short.HELP[name]
            )
    value["scratch"]["disturbance"] = st.selectbox(
        "V2 fixed native disturbance", ["none", config.v1.PROFILE["disturbance"]["id"]]
    )
    with st.expander("Versioned configuration and fixed assumptions"):
        value["scratch"]["configuration_id"] = st.text_input("V2 configuration ID", "baseline")
        value["scratch"]["version"] = int(
            st.number_input("V2 configuration version", value=1, min_value=1, step=1)
        )
        st.json(value, expanded=False)
        st.json(config.PROFILE, expanded=False)
        if st.button("Save V2 experimental configuration"):
            try:
                checked = config.validate(value)
                folder = config.safe(config.OUTPUT / "configurations")
                folder.mkdir(parents=True, exist_ok=True)
                name = (
                    f"{checked['scratch']['configuration_id']}_{checked['mode']}_"
                    f"{checked['maximum_simulation_s']}s_v{checked['scratch']['version']}.json"
                )
                storage.write_json(folder / name, checked, exclusive=True)
                st.success("Saved unreviewed versioned draft: " + name)
            except (OSError, ValueError, KeyError, TypeError) as error:
                st.error("Configuration draft was not saved: " + str(error))
    ready = False
    try:
        config.access(value)
        ready = True
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        st.caption("V2 execution gate: " + str(error))
    if st.button("Run V2 experiment", disabled=not ready, type="primary"):
        directory = execution.start(value)
        st.session_state["lap_selected"] = str(directory)
        st.session_state["next_view"] = "Inspect"
        st.rerun()


def reduced(rows, maximum=2000):
    if len(rows) <= maximum:
        return rows
    step = math.ceil((len(rows) - 1) / (maximum - 1))
    return rows[::step] + ([rows[-1]] if rows[-1] is not rows[::step][-1] else [])


def plot(rows, x, fields, ylabel):
    figure = go.Figure()
    for field, label in fields:
        selected = reduced(
            [
                r
                for r in rows
                if analysis.short.numeric(r.get(x)) and analysis.short.numeric(r.get(field))
            ]
        )
        figure.add_trace(
            go.Scatter(
                x=[r[x] for r in selected], y=[r[field] for r in selected], mode="lines", name=label
            )
        )
    figure.update_layout(
        xaxis_title="Unwrapped native track progress [m]"
        if x == "s_abs"
        else "Native simulated time [s]",
        yaxis_title=ylabel,
    )
    st.plotly_chart(figure, width="stretch", config=short.PLOT_CONFIG)


def replay_window(view, start, duration=10):
    raw, display = view["raw"], view["presentation"]
    indices = [i for i, row in enumerate(raw["states"]) if start <= row["time"] <= start + duration]
    if len(indices) < 2:
        raise ValueError("Replay window has fewer than two native samples")
    observed = [
        {"plan_id": p["plan_id"], "packet": p, "prediction_xy": xy}
        for p, xy in zip(raw["packets"], view["prediction_xy"], strict=True)
    ]
    return {
        **view,
        "raw": {**raw, "states": [raw["states"][i] for i in indices]},
        "presentation": {**display, "states": [display["states"][i] for i in indices]},
        "packets": observed,
    }


def presentation(view):
    metrics = analysis.metrics(view)
    st.metric("Completed full laps", metrics["lap"]["completed_laps"])
    st.metric(
        "Measured lap time [s]",
        metrics["lap"]["lap_time_s"] if metrics["lap"]["lap_time_s"] is not None else "Incomplete",
    )
    st.caption(
        "First launch crossing is excluded. No physical, robustness or real-time qualification."
    )
    st.json(metrics, expanded=False)
    native = view["raw"]["states"]
    rows = [{**s, **d} for s, d in zip(native, view["presentation"]["states"], strict=True)]
    for fields, ylabel in [
        ([("vx", "Longitudinal vx")], "Speed [m/s]"),
        ([("racing_error_y_m", "Planning racing-line error")], "Lateral error [m]"),
        (
            [
                ("racing_error_heading_rad", "Planning heading error"),
                ("e_psi", "Centerline heading"),
            ],
            "Heading [rad]",
        ),
        ([("r", "Yaw rate")], "Yaw rate [rad/s]"),
        ([("delta", "Held applied steering")], "Steering [rad]"),
        (
            [
                ("a_cmd", "Held applied Fx/m"),
                ("body_ax_mps2", "Derived body longitudinal"),
                ("body_ay_mps2", "Derived body lateral"),
            ],
            "Acceleration [m/s²]",
        ),
        (
            [("front_utilization", "Front combined"), ("rear_utilization", "Rear combined")],
            "Combined-grip utilization [1]",
        ),
    ]:
        plot(rows, "s_abs", fields, ylabel)
    st.caption(
        "At most2000genuine points per display trace; scientific metrics use "
        "the complete retained native streams."
    )
    segments = evidence.rows(view, "segments", "journal")
    st.subheader("Common spatial sectors")
    st.json(analysis.sectors(view, segments), expanded=False)
    plans = view["raw"]["plans"]
    st.subheader("Native solver and packet chronology")
    progress_plans = [
        {**p, "s_abs": p["source_state"][4]} for p in plans if p.get("source_state") is not None
    ]
    plot(
        progress_plans,
        "s_abs",
        [
            ("planner_total_time", "Preparation host duration"),
            ("solve_time", "Solver host duration"),
        ],
        "Host duration [s]",
    )
    plot(progress_plans, "s_abs", [("iterations", "IPOPT iterations")], "Iterations [1]")
    plot(progress_plans, "s_abs", [("max_slack", "Native soft-margin slack")], "Slack [m]")
    with st.expander("Feasibility, failures, handoffs, missed releases and fallbacks"):
        st.json(
            {
                key: view["raw"].get(key)
                for key in (
                    "failure",
                    "stop_reason",
                    "handoffs",
                    "misses",
                    "fallbacks",
                    "codriver_misses",
                )
            },
            expanded=False,
        )
    if view["raw"]["packets"]:
        chosen = st.selectbox(
            "Genuine NMPC prediction", [p["plan_id"] for p in view["raw"]["packets"]]
        )
        st.json(analysis.predictions(view, chosen), expanded=False)
    if native:
        start = st.selectbox(
            "Replay window start [native s]",
            sorted(
                set([0.0] + [float(t) for t in range(10, math.floor(native[-1]["time"]) + 1, 10)])
            ),
        )
        replay.replay(replay_window(view, start))


def inspect(directory):
    directory = config.safe(directory)
    state = storage.read_status(directory)
    st.caption(
        f"Execution: {state.get('scientific_outcome')} · Evidence: {state.get('evidence_state')}"
    )
    if state["state"] in execution.ACTIVE:
        if st.button("Refresh V2 status"):
            lease = jobs_lock()
            if lease is not None:
                try:
                    execution.reconcile()
                finally:
                    lease.close()
            st.rerun()
        if st.button("Cancel V2 experiment"):
            (directory / "cancel.request").touch(exist_ok=True)
            st.rerun()
        st.info("Execution in progress; native journals retained. No complete trajectory claimed.")
        return
    scope = st.empty()
    try:
        view = evidence.read_run(directory, recover_failed=True)
        if "raw" not in view:
            st.warning(
                "Incomplete execution; partial native journals retained. " + str(state.get("error"))
            )
            return
        # Positions of genuine packet nodes were recorded through the canonical converter.
        view["prediction_xy"] = evidence.rows(view, "prediction_xy", "derived")
        with scope.container():
            if view.get("recovery"):
                st.warning(view["recovery"]["classification"])
            presentation(view)
            with st.expander("Source and effective configuration"):
                st.json(view["request"], expanded=False)
        evidence.current(view)

        @st.fragment(run_every=1.0)
        def verify_epoch():
            try:
                evidence.current(view)
            except (OSError, ValueError):
                st.rerun()

        verify_epoch()
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        TypeError,
        IndexError,
        AttributeError,
    ) as error:
        scope.empty()
        st.error("V2 evidence quarantined: " + str(error))


def jobs_lock():
    from tools.apex_workbench import jobs

    try:
        return jobs.execution_lock()
    except RuntimeError:
        return None


def compare():
    chosen = st.multiselect(
        "V2 experiments", records(), max_selections=2, format_func=lambda p: p.name
    )
    if len(chosen) != 2:
        st.info("Select baseline and changed weights with equivalent experimental conditions.")
        return
    scope = st.empty()
    try:
        views = [evidence.read_run(p) for p in chosen]
        decision = analysis.comparison(*views)
        with scope.container():
            st.info(decision["classification"])
            st.json(decision)
            st.json(
                [
                    {
                        "run": v["directory"].name,
                        "metrics": analysis.metrics(v),
                        "sectors": analysis.sectors(v, evidence.rows(v, "segments", "journal")),
                    }
                    for v in views
                ],
                expanded=False,
            )
        for view in views:
            evidence.current(view)

        @st.fragment(run_every=1.0)
        def verify_epoch():
            for view in views:
                try:
                    evidence.current(view)
                except (OSError, ValueError):
                    st.rerun()

        verify_epoch()
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        TypeError,
        IndexError,
        AttributeError,
    ) as error:
        scope.empty()
        st.error("V2 comparison quarantined: " + str(error))
