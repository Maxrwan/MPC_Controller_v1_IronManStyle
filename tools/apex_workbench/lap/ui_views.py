"""Presentation workflow over existing configuration, execution and evidence APIs."""

import copy

import plotly.graph_objects as go
import streamlit as st

from tools.apex_workbench import jobs, storage
from tools.apex_workbench import nmpc_analysis as short_analysis
from tools.apex_workbench import nmpc_scratch as transient
from tools.apex_workbench.nmpc_scratch_panels import ERRORS, HELP

from . import analysis, config, evidence, execution, panels, ui_data, ui_replay
from . import ui_theme as theme

PAGES = ["Configure", "Run", "Replay", "Analyze", "Compare"]


def number(value, digits=3):
    return f"{value:.{digits}f}" if short_analysis.numeric(value) else "Unavailable"


def navigate(page):
    st.session_state["ui_next"] = page
    st.rerun()


def configured():
    return st.session_state.get("ui_configuration", config.defaults())


def configure():
    theme.heading(
        "01 / CONFIGURE",
        "Shape the experiment",
        (
            "Explore eight native cost multipliers. The controller, vehicle "
            "and numerical profile stay explicit and fixed."
        ),
    )
    previous = configured()
    old_costs = previous.get("scratch", previous)
    modes = ["Extended", "Transient · 2 s", "Full lap"]
    old_mode = (
        "Transient · 2 s"
        if "scratch" not in previous
        else ("Full lap" if previous["mode"] == "full_lap" else "Extended")
    )
    mode = st.selectbox("Experiment type", modes, index=modes.index(old_mode))
    value = (
        config.defaults("full_lap" if mode == "Full lap" else "extended")
        if mode != "Transient · 2 s"
        else transient.defaults()
    )
    costs = value["scratch"] if "scratch" in value else value
    costs.update(
        copy.deepcopy(
            {k: old_costs[k] for k in ("costs", "disturbance", "configuration_id", "version")}
        )
    )
    if mode == "Extended":
        value["maximum_simulation_s"] = st.selectbox(
            "Recording duration [simulated s]",
            config.PROFILE["extended_seconds"],
            index=config.PROFILE["extended_seconds"].index(previous.get("maximum_simulation_s", 10))
            if previous.get("mode") == "extended"
            else 1,
        )
    elif mode == "Full lap":
        st.info(
            (
                "One complete finish-line circuit after the partial launch "
                "crossing; 80 s ceiling. Execution remains blocked by the retained"
                " resource preflight."
            )
        )
    if st.button("Reset cost multipliers"):
        for name, default in transient.defaults()["costs"].items():
            st.session_state["ui_cost_" + name] = default
    columns = st.columns(2, gap="large")
    for i, (name, default) in enumerate(costs["costs"].items()):
        with columns[i % 2]:
            costs["costs"][name] = st.number_input(
                name.replace("_", " ").title(),
                min_value=0.0,
                value=float(default),
                format="%.4f",
                key="ui_cost_" + name,
                help=HELP[name],
            )
    costs["disturbance"] = st.selectbox(
        "Fixed experimental disturbance",
        ["none", transient.PROFILE["disturbance"]["id"]],
        index=0 if costs["disturbance"] == "none" else 1,
    )
    if costs["disturbance"] != "none":
        st.caption(
            (
                "Native state kick: +0.08 m lateral / −0.04 rad heading at "
                "configured 0.5 s; actual application time is retained."
            )
        )
    with st.expander("Versioned draft & fixed scientific configuration"):
        costs["configuration_id"] = st.text_input("Configuration ID", costs["configuration_id"])
        costs["version"] = int(
            st.number_input("Configuration version", min_value=1, value=costs["version"], step=1)
        )
        st.caption(
            "Synthetic GP gamma2 · N=8 NMPC / TVLQR · frozen source "
            + transient.frozen.SOURCE[:12]
            + (
                ". Broader parameter changes require source-controlled "
                "configuration and scientific review. Drafts never overwrite the "
                "accepted Performance baseline."
            )
        )
        st.json(value, expanded=False)
        if st.button("Save configuration draft"):
            try:
                if "scratch" not in value:
                    path = transient.saved_configuration(value)
                else:
                    checked = config.validate(value)
                    folder = config.safe(config.OUTPUT / "configurations")
                    folder.mkdir(parents=True, exist_ok=True)
                    path = folder / (
                        f"{costs['configuration_id']}_{value['mode']}_"
                        f"{value['maximum_simulation_s']}s_v{costs['version']}.json"
                    )
                    storage.write_json(path, checked, exclusive=True)
                st.success("Saved unreviewed draft: " + str(path))
            except ERRORS as error:
                st.error("Draft was not saved: " + str(error))
    try:
        checked = config.validate(value) if "scratch" in value else transient.validate(value)
        st.session_state["ui_configuration"] = copy.deepcopy(checked)
        st.session_state.pop("ui_configuration_error", None)
        if st.button("Review run setup", type="primary"):
            navigate("Run")
    except ERRORS as error:
        st.session_state["ui_configuration_error"] = str(error)
        st.error("Invalid configuration: " + str(error))


def run():
    value = configured()
    v2 = "scratch" in value
    selected = value["scratch"] if v2 else value
    duration = value["maximum_simulation_s"] if v2 else 2
    theme.heading(
        "02 / RUN",
        "Review & execute",
        (
            "A run starts only when you press the execution button. Resource "
            "limits, source identity and worker ownership remain enforced."
        ),
    )
    if st.session_state.get("ui_configuration_error"):
        st.error("Configuration requires correction: " + st.session_state["ui_configuration_error"])
        if st.button("Back to configuration"):
            navigate("Configure")
        return
    theme.cards(
        [
            ("Configuration", selected["configuration_id"], "Version " + str(selected["version"])),
            ("Recording ceiling", f"{duration} s", "Simulated time"),
            ("Controller", "N = 8", "Frozen NMPC + TVLQR"),
            (
                "Disturbance",
                "None" if selected["disturbance"] == "none" else "State kick",
                "Fixed approved selector",
            ),
        ]
    )
    with st.expander("Selected cost multipliers & execution profile"):
        st.json(value, expanded=False)
    ready = False
    try:
        (config.access if v2 else transient.access)(value)
        ready = True
        st.success("Source-bound execution policy available.")
    except ERRORS as error:
        st.warning(
            (
                "Execution unavailable for this selection. The execution policy "
                "must match its reviewed source and authorization."
            )
        )
        with st.expander("Execution gate details"):
            st.code(str(error), language=None)
    if v2:
        budget = ui_data.full_lap_gate()
        st.caption(
            f"Retained full-lap gate: {budget['projection']['cpu_s']:.2f} s projected CPU "
            f"exceeds the unchanged {budget['limits']['cpu_s']} s ceiling. "
            "This UI delivery does not authorize another pilot or full lap."
        )
    if st.button("Run experiment", type="primary", disabled=not ready):
        try:
            directory = execution.start(value) if v2 else jobs.start_run(transient.ADAPTER, value)
            st.session_state["ui_selected"] = str(directory)
            navigate("Replay")
        except ERRORS as error:
            st.error("Execution did not start: " + str(error))
    if st.button("Back to configuration"):
        navigate("Configure")


def select_record(key="ui_record"):
    choices = ui_data.recordings()
    if not choices:
        st.info("No retained experiment recordings. Configure an authorized experiment to begin.")
        return None
    preferred = st.session_state.get("ui_selected")
    index = next((i for i, r in enumerate(choices) if str(r["directory"]) == preferred), 0)
    chosen = st.selectbox(
        "Retained recording", choices, index=index, format_func=ui_data.label, key=key
    )
    st.session_state["ui_selected"] = str(chosen["directory"])
    return chosen


def active(record):
    try:
        state = storage.read_status(record["directory"])
    except ERRORS as error:
        st.error("Evidence quarantined: " + str(error))
        return True
    if state["state"] not in execution.ACTIVE:
        return False
    st.info(
        (
            "Execution in progress. Native journals are retained; a complete "
            "trajectory is not yet available."
        )
    )
    if st.button("Refresh execution status"):
        if record["family"] == "V2":
            lease = panels.jobs_lock()
            if lease:
                try:
                    execution.reconcile()
                finally:
                    lease.close()
        else:
            jobs.status_for(record["directory"])
        st.rerun()
    if st.button("Cancel owned experiment"):
        if record["family"] == "V2":
            (config.safe(record["directory"]) / "cancel.request").touch(exist_ok=True)
        else:
            jobs.cancel_run(record["directory"])
        st.rerun()
    return True


def guarded(records, render):
    scope = st.empty()
    try:
        views = [ui_data.read(r) for r in records]
        if any(not v.get("raw") or not v.get("presentation") for v in views):
            st.warning(
                (
                    "Incomplete execution. Partial evidence remains retained; replay "
                    "and complete-run metrics are unavailable."
                )
            )
            return
        with scope.container():
            render(views)
        for view in views:
            ui_data.current(view)

        @st.fragment(run_every=1.0)
        def verify():
            try:
                for view in views:
                    ui_data.current(view)
            except ERRORS:
                st.rerun()

        verify()
    except ERRORS as error:
        scope.empty()
        st.error("Evidence quarantined: " + str(error))


def replay():
    theme.heading(
        "03 / REPLAY",
        "See the controller at work",
        (
            "Inspect genuine retained trajectories, applied commands and "
            "physically available packets on one replay clock."
        ),
    )
    chosen = select_record()
    if chosen is None or active(chosen):
        return

    def present(views):
        view = views[0]
        windows = ui_data.windows(view)
        selected = windows[0]
        if len(windows) > 1:
            selected = st.selectbox(
                "Native recording window",
                windows,
                format_func=lambda w: (
                    f"{view['raw']['states'][w[0]]['time']:.3f}–"
                    f"{view['raw']['states'][w[1] - 1]['time']:.3f} s · "
                    f"{w[1] - w[0]} native states"
                ),
            )
        ui_replay.replay(ui_data.window(view, selected))
        with st.expander("Recording outcome, provenance & scientific boundaries"):
            st.write(
                "Execution: "
                + str(view["status"].get("scientific_outcome"))
                + " · Evidence: "
                + str(view["status"].get("evidence_state"))
            )
            st.caption(
                (
                    "Retained offline Planning reference and canonical track. Native "
                    "telemetry and command events are never interpolated. Predictions "
                    "are solver outputs, not guaranteed future motion. Synthetic and "
                    "unqualified; no physical or real-time claim."
                )
            )
            st.json(view["request"], expanded=False)

    guarded([chosen], present)


def metrics(view):
    return analysis.metrics(view) if view["ui_family"] == "V2" else short_analysis.metrics(view)


def plot(rows, fields, ylabel, *, x="time"):
    fig = go.Figure()
    palette = theme.palette()
    colors = [palette["copper"], palette["mint"], palette["lime"], palette["muted"]]
    for i, (field, label) in enumerate(fields):
        xs, ys = ui_data.trace(rows, x, field)
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                connectgaps=False,
                name=label,
                mode="lines",
                line={"color": colors[i % len(colors)], "width": 1.8},
            )
        )
    fig.update_layout(
        xaxis_title="Simulated time [s]" if x == "time" else "Native release time [simulated s]",
        yaxis_title=ylabel,
    )
    theme.chart(fig)


def analyze():
    theme.heading(
        "04 / ANALYZE",
        "Turn observations into insight",
        (
            "Sample-based measurements from the full retained recording. "
            "Display traces use at most 2,000 genuine points; metrics use "
            "every native sample."
        ),
    )
    chosen = select_record("ui_analysis_record")
    if chosen is None or active(chosen):
        return

    def present(views):
        view = views[0]
        m = metrics(view)
        theme.cards(
            [
                (
                    "Racing error · RMS",
                    number(m["racing_lateral_error_m"]["rms"]),
                    "m · retained native samples",
                ),
                (
                    "Peak racing error",
                    number(m["racing_lateral_error_m"]["peak_abs"]),
                    "m · absolute",
                ),
                (
                    "Solver duration · mean",
                    number(m["solver_host_seconds"]["mean"]),
                    "Host seconds · not simulated time",
                ),
                (
                    "Boundary observations",
                    m["recorded_boundary_violation_rows"],
                    "Recorded violation rows · not safety proof",
                ),
            ]
        )
        group = st.selectbox(
            "Analysis view",
            ["Tracking", "Actuation & grip", "Solver & events", "Prediction inspection"],
        )
        rows = [
            {**s, **d}
            for s, d in zip(view["raw"]["states"], view["presentation"]["states"], strict=True)
        ]
        if group == "Tracking":
            plot(rows, [("vx", "Longitudinal speed")], "Speed [m/s]")
            plot(
                rows, [("racing_error_y_m", "Planning lateral error")], "Racing-reference error [m]"
            )
            if view["ui_family"] == "V2":
                lap = m["lap"]
                st.caption(
                    f"Recording outcome: {lap['completed_laps']} complete laps · "
                    f"lap time {number(lap['lap_time_s'])} s. Initial partial crossing excluded."
                )
                with st.expander("Lap & sector measurements"):
                    st.json(
                        analysis.sectors(view, evidence.rows(view, "segments", "journal")),
                        expanded=False,
                    )
        elif group == "Actuation & grip":
            plot(rows, [("delta", "Native held applied δ")], "Steering [rad]")
            plot(
                rows,
                [
                    ("a_cmd", "Held applied Fx/m"),
                    ("body_ax_mps2", "Derived body ax"),
                    ("body_ay_mps2", "Derived body ay"),
                ],
                "Acceleration [m/s²]",
            )
            plot(
                rows,
                [("front_utilization", "Front"), ("rear_utilization", "Rear")],
                "Combined-grip utilization [1]",
            )
        elif group == "Solver & events":
            plans = view["raw"]["plans"]
            plot(
                plans,
                [
                    ("solve_time", "Solver host duration"),
                    ("planner_total_time", "Preparation host duration"),
                ],
                "Host duration [s]",
                x="release_time",
            )
            plot(plans, [("iterations", "IPOPT iterations")], "Iterations [1]", x="release_time")
            st.json(
                {
                    k: view["raw"].get(k)
                    for k in ("failure", "stop_reason", "misses", "fallbacks", "codriver_misses")
                },
                expanded=False,
            )
        else:
            if view["ui_family"] == "V2" and view["raw"]["packets"]:
                selected = st.selectbox(
                    "Recorded prediction packet", [p["plan_id"] for p in view["raw"]["packets"]]
                )
                st.json(analysis.predictions(view, selected), expanded=False)
            else:
                st.info(
                    (
                        "Use Replay’s prediction explorer for native horizon nodes and "
                        "solver diagnostics."
                    )
                )
        with st.expander("Metric definitions & full measurement record"):
            st.json(m, expanded=False)
            st.caption(
                (
                    "No value-function stability or physical validity conclusion. "
                    "Differently weighted raw objective totals are not performance "
                    "ranks."
                )
            )

    guarded([chosen], present)


def compare():
    theme.heading(
        "05 / COMPARE",
        "Compare the evidence",
        (
            "Two recordings, explicit experimental conditions and native "
            "tracking measurements. No automatic best-controller score."
        ),
    )
    family = st.selectbox("Recording family", ["V2", "Transient"])
    choices = ui_data.recordings(family)
    if len(choices) < 2:
        st.info(
            (
                "Two retained recordings are required. Only one V2 pilot is "
                "retained; no new run is started by this screen."
            )
        )
        return
    selected = st.multiselect(
        "Recordings · select two", choices, format_func=ui_data.label, max_selections=2
    )
    if len(selected) != 2:
        st.caption("Select two completed recordings from the same family.")
        return

    def present(views):
        decision = (
            analysis.comparison(*views) if family == "V2" else short_analysis.comparison(*views)
        )
        st.info(decision["classification"])
        ms = [metrics(v) for v in views]
        theme.cards(
            [
                (
                    f"Run {i + 1} · RMS error",
                    number(m["racing_lateral_error_m"]["rms"]),
                    "m · full native record",
                )
                for i, m in enumerate(ms)
            ]
            + [
                (
                    f"Run {i + 1} · peak error",
                    number(m["racing_lateral_error_m"]["peak_abs"]),
                    "m · absolute",
                )
                for i, m in enumerate(ms)
            ]
        )
        figure = go.Figure()
        colors = theme.palette()
        for i, view in enumerate(views):
            rows = panels.reduced(view["presentation"]["states"])
            figure.add_trace(
                go.Scatter(
                    x=[r["time"] for r in rows],
                    y=[r["racing_error_y_m"] for r in rows],
                    name=f"Run {i + 1}",
                    line={"color": colors["copper" if i == 0 else "mint"]},
                )
            )
        figure.update_layout(
            xaxis_title="Native simulated time [s]",
            yaxis_title="Racing-reference lateral error [m]",
        )
        theme.chart(figure)
        st.caption(
            "Run 1: " + ui_data.label(selected[0]) + " · Run 2: " + ui_data.label(selected[1])
        )
        with st.expander("Experimental differences, eligibility & full metrics"):
            st.json(decision, expanded=False)
            st.json(ms, expanded=False)

    guarded(selected, present)
