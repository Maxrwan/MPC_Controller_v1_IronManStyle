"""Small cost editor, native replay and descriptive Control Analysis presentation."""

import plotly.graph_objects as go
import streamlit as st

from tools.apex_workbench import jobs, storage
from tools.apex_workbench import nmpc_analysis as analysis
from tools.apex_workbench import nmpc_scratch as scratch

PLOT_CONFIG = {"displayModeBar": False, "displaylogo": False}
ERRORS = (OSError, ValueError, RuntimeError, KeyError, TypeError, IndexError, AttributeError)
HELP = {
    "lateral": "Scale the existing e_y and e_psi stage penalties.",
    "dynamic": "Joint scale for existing vy and yaw-rate stage penalties.",
    "speed": "Scale the existing longitudinal-speed stage penalty.",
    "control": "Scale deviation from the native command reference.",
    "rate": "Scale native command-increment penalties, not derivative penalties.",
    "terminal": "Scale the existing terminal objective; no new terminal law.",
    "alpha_vy": "Native vy stage factor and terminal DARE weighting.",
    "alpha_r": "Native yaw-rate stage factor and terminal DARE weighting.",
}


def records():
    if not scratch.RUNS.exists():
        return []
    return [
        p
        for p in sorted(scratch.RUNS.iterdir(), reverse=True)
        if p.is_dir() and not p.is_symlink() and not p.name.startswith(".")
    ]


def label(directory):
    try:
        value = scratch.validate(storage.read_json(directory / "request.json")["effective"])
        return (
            value["configuration_id"]
            + " · lateral="
            + str(value["costs"]["lateral"])
            + " · "
            + value["disturbance"]
            + " · "
            + directory.name
        )
    except ERRORS:
        return directory.name + " · unverified metadata"


def run_panel():
    st.warning(scratch.BANNER)
    st.caption("Architecture A · synthetic GP gamma2 · 2.0 s · native NMPC/IPOPT + TVLQR")
    baseline = scratch.defaults()
    if st.button("Reset costs to accepted baseline"):
        for name, value in baseline["costs"].items():
            st.session_state["scratch_cost_" + name] = value
    columns = st.columns(2)
    values = scratch.defaults()
    for index, name in enumerate(scratch.FIELDS):
        with columns[index % 2]:
            values["costs"][name] = st.number_input(
                name,
                value=float(baseline["costs"][name]),
                min_value=0.0,
                key="scratch_cost_" + name,
                format="%.6f",
                help=HELP[name],
            )
    values["disturbance"] = st.selectbox(
        "Native disturbance", ["none", scratch.PROFILE["disturbance"]["id"]]
    )
    if values["disturbance"] != "none":
        st.caption(
            (
                "One native state perturbation: +0.08 m lateral / −0.04 rad "
                "heading at configured 0.5 s. Actual trigger time is retained."
            )
        )
    st.caption(
        (
            "Stage multipliers must be positive; terminal/alpha multipliers "
            "may be zero under native CostScales semantics. Changes remain "
            "unqualified."
        )
    )
    st.table(
        [
            {
                "field": name,
                "accepted": baseline["costs"][name],
                "selected": value,
                "changed": value != baseline["costs"][name],
            }
            for name, value in values["costs"].items()
        ]
    )
    try:
        values = scratch.validate(values)
    except ValueError as error:
        st.error(str(error))
        return
    with st.expander("Configuration sources and fixed scientific assumptions"):
        st.json(scratch.PROFILE)
        st.caption(
            (
                "Broader settings are fixed by the referenced scientific revision. New "
                "assumptions/domain require scientific review; the accepted "
                "Performance baseline is never overwritten."
            )
        )
    with st.expander("Save an explicit versioned experimental draft"):
        values["configuration_id"] = st.text_input("Configuration ID", value="baseline")
        values["version"] = int(
            st.number_input("Configuration version", min_value=1, value=1, step=1)
        )
        if st.button("Save configuration draft"):
            try:
                path = scratch.saved_configuration(values)
                st.success("Saved unreviewed draft: " + str(path))
            except ERRORS as error:
                st.error(str(error))
        st.caption(
            (
                "Future deployment must explicitly select a versioned, reviewed "
                "configuration. The last editor values are not deployment "
                "approval."
            )
        )
    if st.button("Inspect effective frozen configuration (no solve)"):
        try:
            result = scratch.probe(values)
            st.json(result["resolved"], expanded=False)
            st.caption(
                (
                    "Native dataclasses resolved in frozen source isolation; no "
                    "optimizer solve or plant execution."
                )
            )
        except ERRORS as error:
            st.error(str(error))
    try:
        scratch.access(values)
        ready = True
    except ERRORS as error:
        ready = False
        st.info("Scratch execution gate: " + str(error))
    st.caption(
        (
            "Before Primary acceptance, only the three reviewed WORK attempts "
            "are available, once each. After acceptance, explicit interactive "
            "runs use the approved profile and same limits."
        )
    )
    if st.button("Run Scratch experiment", disabled=not ready, type="primary"):
        try:
            directory = jobs.start_run(scratch.ADAPTER, values)
            st.session_state["pending_directory"] = str(directory)
            st.session_state["next_view"] = "Inspect"
            st.rerun()
        except ERRORS as error:
            st.error(str(error))


def series(rows, x, fields, ylabel):
    plot = go.Figure()
    for field, label in fields:
        valid = [r for r in rows if analysis.numeric(r.get(x)) and analysis.numeric(r.get(field))]
        plot.add_trace(
            go.Scatter(
                x=[r[x] for r in valid],
                y=[r[field] for r in valid],
                mode="lines+markers",
                name=label,
            )
        )
    plot.update_layout(xaxis_title="Native simulated time [s]", yaxis_title=ylabel)
    return plot


def commands(raw, channel, packet=None):
    plot = go.Figure()
    for clock, field, label in [
        ("time", "requested_" + channel, "Requested at computation time"),
        ("application_time", channel, "Actually applied at application_time"),
    ]:
        rows = [
            r
            for r in raw["controls"]
            if analysis.numeric(r.get(clock)) and analysis.numeric(r.get(field))
        ]
        plot.add_trace(
            go.Scatter(
                x=[r[clock] for r in rows],
                y=[r[field] for r in rows],
                mode="lines+markers",
                name=label,
            )
        )
    if packet:
        native = packet["packet"]
        column = 0 if channel == "delta" else 1
        plot.add_trace(
            go.Scatter(
                x=native["timestamps"][:-1],
                y=[r[column] for r in native["controls"]],
                mode="lines+markers",
                name="Selected packet nominal optimum; not application",
            )
        )
    plot.update_layout(
        xaxis_title="Separate native simulated clocks [s]",
        yaxis_title="Steering [rad]" if channel == "delta" else "a_cmd = Fx/m [m/s²]",
    )
    return plot


def trajectory(display, index, packet):
    figure = go.Figure()
    geometry, states = display["geometry"], display["states"]
    for x, y, label in [
        ("x", "y", "Track centerline"),
        ("left_x", "left_y", "Left boundary"),
        ("right_x", "right_y", "Right boundary"),
    ]:
        figure.add_trace(
            go.Scatter(
                x=[r[x] for r in geometry], y=[r[y] for r in geometry], mode="lines", name=label
            )
        )
    figure.add_trace(
        go.Scatter(
            x=[r["x"] for r in states],
            y=[r["y"] for r in states],
            mode="lines",
            name="Native simulated trajectory",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[states[index]["x"]],
            y=[states[index]["y"]],
            mode="markers",
            marker={"size": 12},
            name="Selected native position",
        )
    )
    if packet:
        for name, label in [
            ("prediction_xy", "Native NMPC predicted states"),
            ("reference_xy", "Native optimization reference nodes"),
        ]:
            if packet.get(name):
                figure.add_trace(
                    go.Scatter(
                        x=[r[0] for r in packet[name]],
                        y=[r[1] for r in packet[name]],
                        mode="lines+markers",
                        name=label,
                    )
                )
    figure.update_layout(
        xaxis_title="Global x [m]", yaxis_title="Global y [m]", yaxis={"scaleanchor": "x"}
    )
    return figure


def horizon_node(packet, index):
    """Select a retained node; the final state has no invented terminal command."""
    native = packet["packet"]
    states, controls, times = (native[k] for k in ("states", "controls", "timestamps"))
    if len(states) != len(times) or len(controls) != len(states) - 1:
        raise ValueError("Recorded state/control horizon dimensions differ")
    if type(index) is not int or not 0 <= index < len(states):
        raise ValueError("Recorded horizon node is out of range")
    return times[index], states[index], controls[index] if index < len(controls) else None


def packet_details(view, packet, key, sample_time):
    """Bench-inspired inspection using this run's actual N=8 records and clocks."""
    st.subheader("Retained prediction horizon")
    node = st.select_slider(
        "Prediction node", options=list(range(len(packet["packet"]["states"]))), key=key + "_node"
    )
    time, state, command = horizon_node(packet, node)
    st.table(
        [
            {"solver-predicted state": name, "value": value, "SI unit": unit}
            for name, unit, value in zip(
                ("vx", "vy", "r", "e_psi", "s_abs", "e_y"),
                ("m/s", "m/s", "rad/s", "rad", "m", "m"),
                state,
                strict=True,
            )
        ]
    )
    st.write(
        {
            "prediction_node": node,
            "native_prediction_time_s": time,
            "nominal_delta_rad": command[0] if command is not None else None,
            "nominal_a_cmd_mps2": command[1] if command is not None else None,
            "terminal_state_without_command": command is None,
        }
    )
    plan_id = packet["plan_id"]
    plan = next((p for p in view["raw"]["plans"] if p.get("plan_id") == plan_id), {})
    scheduled = next((p for p in view["raw"]["packets"] if p.get("plan_id") == plan_id), {})
    completion = scheduled.get("actual_completion_time")
    st.json(
        {
            "selected_plant_sample_time_s": sample_time,
            "selected_packet_plan_id": plan_id,
            "recorded_completion_time_s": completion,
            "recorded_completion_reached_at_sample": sample_time >= completion
            if analysis.numeric(completion)
            else None,
            "recorded_packet_valid": scheduled.get("valid"),
            "recorded_validation_reason": scheduled.get("validation_reason"),
            "recorded_handoffs": [
                p for p in view["raw"]["handoffs"] if p.get("plan_id") == plan_id
            ],
            "solver_status": plan.get("status"),
            "iterations": plan.get("iterations"),
            "primal_infeasibility": plan.get("primal_infeasibility"),
            "maximum_soft_margin_slack_m": plan.get("max_slack"),
            "host_solve_duration_s": plan.get("solve_time"),
            "host_preparation_duration_s": plan.get("planner_total_time"),
            "native_prediction_error_at_completion": plan.get("prediction_error"),
            "prediction_target_time_s": plan.get("predicted_completion_time"),
            "actual_comparison_time_s": plan.get("completion_time"),
        },
        expanded=False,
    )
    parts = {
        k: v
        for k, v in plan.get("objective_components", {}).items()
        if k != "total" and analysis.numeric(v)
    }
    if parts:
        plot = go.Figure(go.Bar(x=list(parts), y=list(parts.values())))
        plot.update_layout(yaxis_title="Recorded weighted objective contribution")
        st.plotly_chart(plot, width="stretch", config=PLOT_CONFIG)
    else:
        st.info("Objective components were not retained for this event.")
    st.caption(
        "SIMULATED: recorded plant samples and applied commands. SOLVER: predicted states, "
        "nominal commands, objective and residuals. DERIVED: global geometry, tracking metrics "
        "and local linear indicators. A selected prediction is historical inspection, not proof "
        "of availability or application at the selected plant sample. Completion, validity and "
        "handoff are distinct. Native completion prediction_error compares actual completion "
        "state with the original predicted state; target and completion times can differ. "
        "No interpolated prediction-error curve or active-set flags are invented. Component "
        "values explain this weighted problem; they do not rank differently weighted runs."
    )


def replay(directory):
    key = "scratch_replay_" + directory.name
    running = st.session_state.get(key + "_playing", False)

    @st.fragment(run_every=0.4 if running else None)
    def render():
        scope = st.empty()
        try:
            view = scratch.read_run(directory)
            display, raw = view["presentation"], view["raw"]
            if not raw or not display or not display["states"]:
                scope.info("Native trajectory unavailable; partial journals remain retained.")
                return
            rows = display["states"]
            sample_key = key + "_sample"
            if sample_key not in st.session_state:
                st.session_state[sample_key] = 0
            index = min(st.session_state[sample_key] + int(running), len(rows) - 1)
            st.session_state[sample_key] = index
            with scope.container():
                buttons = st.columns(3)
                if buttons[0].button("Previous sample", key=key + "_previous"):
                    index = max(0, index - 1)
                    st.session_state[sample_key] = index
                if buttons[1].button(
                    "Pause" if running else "Play recorded samples", key=key + "_play"
                ):
                    st.session_state[key + "_playing"] = not running
                    st.rerun()
                if buttons[2].button("Next sample", key=key + "_next"):
                    index = min(len(rows) - 1, index + 1)
                    st.session_state[sample_key] = index
                index = st.select_slider(
                    "Native simulated sample",
                    options=list(range(len(rows))),
                    format_func=lambda i: f"{rows[i]['time']:.6f} s",
                    key=key + "_sample",
                )
                packets = {p["plan_id"]: p for p in view["packets"] if p.get("packet") is not None}
                active = raw["states"][index].get("plan_id")
                chosen = (
                    st.selectbox(
                        "Recorded solver/packet event",
                        list(packets),
                        index=list(packets).index(active) if active in packets else 0,
                        key=key + "_packet",
                    )
                    if packets
                    else None
                )
                packet = packets.get(chosen)
                plot = trajectory(display, index, packet)
                error_plot = series(
                    rows,
                    "time",
                    [
                        ("racing_error_y_m", "Racing-reference error"),
                        ("reference_e_y_m", "Reference lateral offset"),
                    ],
                    "Lateral distance [m]",
                )
                scratch.current(view)
                st.plotly_chart(plot, width="stretch", config=PLOT_CONFIG)
                st.plotly_chart(error_plot, width="stretch", config=PLOT_CONFIG)
                st.plotly_chart(commands(raw, "delta", packet), width="stretch", config=PLOT_CONFIG)
                st.plotly_chart(commands(raw, "a_cmd", packet), width="stretch", config=PLOT_CONFIG)
                st.caption(
                    (
                        "Native samples only. Geometry/reference conversions use canonical "
                        "APIs. Prediction nodes belong to the selected preparation, not to "
                        "an assumed applied trajectory. Viewer playback does not advance "
                        "the simulator."
                    )
                )
                if packet:
                    st.caption(packet["capture_phase"])
                    st.write(
                        {
                            "selected_packet_plan_id": chosen,
                            "plant_active_plan_id": active,
                            "release_time_s": packet["release_time"],
                            "prediction_timestamps_s": packet["packet"]["timestamps"],
                        }
                    )
                    packet_details(view, packet, key, rows[index]["time"])
                scratch.current(view)
                if running:
                    if index == len(rows) - 1:
                        st.session_state[key + "_playing"] = False
                        st.rerun()
        except ERRORS as error:
            st.session_state[key + "_playing"] = False
            scope.empty()
            scope.error("Scratch evidence quarantined: " + str(error))

    render()


def inspect(selected):
    st.warning(scratch.BANNER)
    try:
        directory = scratch.owned(selected)
        status = jobs.status_for(directory)
        st.write(
            {
                "execution": status.get("scientific_outcome"),
                "evidence": status.get("evidence_state"),
            }
        )
        if status.get("state") in jobs.ACTIVE:
            st.button("Refresh Scratch run")
            if st.button("Cancel Scratch run"):
                scratch.owned(selected)
                jobs.cancel_run(directory)
                st.rerun()
            st.caption(
                (
                    "Partial native journals are retained; unfinished evidence is not "
                    "a completed trajectory."
                )
            )
            return
        view = scratch.read_run(directory)
        with st.expander("Original effective configuration and provenance"):
            st.json(view["request"], expanded=False)
        if st.button("Open Control Analysis"):
            st.session_state["scratch_analysis_directory"] = str(directory)
            st.session_state["next_view"] = "Analyze"
            st.rerun()
        replay(directory)
    except ERRORS as error:
        st.error("Scratch record quarantined: " + str(error))


def analysis_panel():
    st.warning(scratch.BANNER)
    directories = records()
    if not directories:
        st.info("No retained Scratch runs. Configure an experiment on Run.")
        return
    preferred = st.session_state.get("scratch_analysis_directory")
    selected = st.selectbox(
        "Scratch analysis run",
        directories,
        index=next((i for i, p in enumerate(directories) if str(p) == preferred), 0),
        format_func=label,
    )
    scope = st.empty()
    try:
        view = scratch.read_run(selected)
        if not view["raw"] or not view["presentation"]:
            st.info(
                (
                    "Analysis unavailable without genuine native results and derived "
                    "reference channels."
                )
            )
            return
        band = st.number_input(
            "Analysis-only lateral error band [m]", value=0.01, min_value=0.000001, format="%.6f"
        )
        tail = st.number_input("Minimum observed settling tail [s]", value=0.25, min_value=0.000001)
        result = analysis.metrics(view, band_m=band, minimum_tail_s=tail)
        raw, display = view["raw"], view["presentation"]
        plots = [
            series(
                display["states"],
                "time",
                [("racing_error_y_m", "Racing-reference lateral error")],
                "Error [m]",
            ),
            series(
                display["states"],
                "time",
                [("racing_error_heading_rad", "Racing-reference heading error")],
                "Error [rad]",
            ),
            commands(raw, "delta"),
            commands(raw, "a_cmd"),
            series(
                raw["plans"],
                "release_time",
                [
                    ("solve_time", "Host solve duration"),
                    ("planner_total_time", "Host preparation duration"),
                ],
                "Host duration [s]",
            ),
            series(
                raw["states"],
                "time",
                [
                    ("front_utilization", "Front combined utilization"),
                    ("rear_utilization", "Rear combined utilization"),
                ],
                "Utilization [1]",
            ),
            series(
                raw["plans"],
                "release_time",
                [("iterations", "Native iterations")],
                "Iterations [1]",
            ),
            series(
                raw["plans"],
                "release_time",
                [("max_slack", "Native maximum slack")],
                "Native soft-constraint slack [m]",
            ),
        ]
        limits = display["limits"]
        if "delta_rad" in limits:
            for value in (-limits["delta_rad"], limits["delta_rad"]):
                plots[2].add_hline(y=value, line_dash="dot")
            for value in (limits["a_cmd_lower_mps2"], limits["a_cmd_upper_mps2"]):
                plots[3].add_hline(y=value, line_dash="dot")
        for disturbance in display["applied_disturbances"]:
            for plot in plots:
                plot.add_vline(x=disturbance["application_time_s"], line_dash="dot")
        scratch.current(view)
        with scope.container():
            st.subheader("Transient response and effort")
            st.caption(
                (
                    "Racing-reference error subtracts the original Planning lateral "
                    "offset/heading at actual progress. Raw e_y is a centerline "
                    "coordinate. Native TVLQR packet errors are a third, separate "
                    "reference."
                )
            )
            st.json(result, expanded=False)
            for plot in plots:
                st.plotly_chart(plot, width="stretch", config=PLOT_CONFIG)
            st.subheader("Disturbance and constraints")
            st.json(
                {
                    "actual_applications": display["applied_disturbances"],
                    "configured_limits": display["limits"],
                    "native_handoffs": raw["handoffs"],
                    "native_packets": raw["packets"],
                },
                expanded=False,
            )
            st.caption(
                (
                    "Settling uses a user-selected descriptive band and observed tail, "
                    "not scientific acceptance thresholds. No step-response overshoot "
                    "is assigned here. Steering magnitude alone does not establish "
                    "tire saturation. Optimized, requested and applied commands have "
                    "separate records/clocks; slack and utilization retain native "
                    "meanings."
                )
            )
            st.subheader("Local linear indicators")
            packets = [p for p in view["packets"] if p.get("packet") is not None]
            if packets:
                packet = st.selectbox(
                    "Local nominal packet", packets, format_func=lambda p: str(p["plan_id"])
                )
                indicators = analysis.linear_indicators(packet["linearization"])
                st.plotly_chart(
                    series(
                        indicators["rows"],
                        "time",
                        [
                            ("spectral_radius", "Spectral radius"),
                            (
                                "finite_horizon_amplification_2norm",
                                "Nominal-packet error amplification",
                            ),
                        ],
                        "Local indicator [1]",
                    ),
                    width="stretch",
                    config=PLOT_CONFIG,
                )
                st.plotly_chart(
                    series(
                        indicators["rows"],
                        "time",
                        [("gain_change_2norm", "Change in native gain")],
                        "Gain change in mixed SI coordinates",
                    ),
                    width="stretch",
                    config=PLOT_CONFIG,
                )
                st.caption(indicators["definition"] + ". " + indicators["limitations"])
                st.caption(
                    (
                        "Actual frozen 10 ms TVLQR Jacobian/gain pairs; order "
                        "[e_y,e_psi,vy,r], feedback −K. Observed behavior and local "
                        "indicators establish no formal nonlinear/hybrid stability "
                        "guarantee."
                    )
                )
                st.json(indicators, expanded=False)
            else:
                st.info(
                    (
                        "Native Jacobian/gain associations unavailable; no local stability "
                        "values synthesized."
                    )
                )
            with st.expander("Original optimizer predictions, slack and request records"):
                st.json(raw["plans"], expanded=False)
        scratch.current(view)
    except ERRORS as error:
        scope.empty()
        scope.error("Analysis unavailable / evidence quarantined: " + str(error))


def compare_panel():
    st.warning(scratch.BANNER)
    selected = st.multiselect("Scratch experiments", records(), max_selections=2, format_func=label)
    if len(selected) != 2:
        st.info(
            (
                "Select baseline/treatment or two Scratch runs. Historical M5-A "
                "remains available in its original view."
            )
        )
        return
    scope = st.empty()
    try:
        views = [scratch.read_run(p) for p in selected]
        decision = analysis.comparison(*views)
        results = [analysis.metrics(v) for v in views]
        plot = go.Figure()
        for view in views:
            rows = view["presentation"]["states"]
            plot.add_trace(
                go.Scatter(
                    x=[r["time"] for r in rows],
                    y=[r["racing_error_y_m"] for r in rows],
                    mode="lines+markers",
                    name=view["directory"].name,
                )
            )
        plot.update_layout(
            xaxis_title="Native simulated time [s]",
            yaxis_title="Racing-reference lateral error [m]",
        )
        for view in views:
            scratch.current(view)
        with scope.container():
            st.info(decision["classification"])
            st.json(decision, expanded=False)
            st.table(
                [
                    {
                        "run": v["directory"].name,
                        "lateral_RMS_m": m["racing_lateral_error_m"]["rms"],
                        "peak_lateral_error_m": m["racing_lateral_error_m"]["peak_abs"],
                        "steering_total_variation_rad": m["steering_rad"]["total_variation"],
                        "a_cmd_total_variation_mps2": m["longitudinal_a_cmd_mps2"][
                            "total_variation"
                        ],
                        "mean_host_solve_s": m["solver_host_seconds"]["mean"],
                        "max_slack": m["max_native_slack"],
                    }
                    for v, m in zip(views, results)
                ]
            )
            st.plotly_chart(plot, width="stretch", config=PLOT_CONFIG)
            st.caption(
                (
                    "Common physical errors/effort are reported over each native "
                    "window. Differently weighted objective totals are not ranked. "
                    "These observations do not establish statistical superiority or "
                    "physical validity."
                )
            )
            if decision["recovery_metrics_comparable"]:
                st.json([m["disturbance_recovery"] for m in results], expanded=False)
        for view in views:
            scratch.current(view)
    except ERRORS as error:
        scope.empty()
        scope.error("Comparison unavailable / evidence quarantined: " + str(error))
