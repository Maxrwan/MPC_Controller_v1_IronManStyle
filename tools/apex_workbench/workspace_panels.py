"""Compact Streamlit panels over verified records; no execution or scientific equations."""

import time

import plotly.graph_objects as go
import streamlit as st

from tools.apex_workbench import engineering_views as views
from tools.apex_workbench import jobs, plots
from tools.apex_workbench import recorded_view as recorded
from tools.apex_workbench.experiment_catalog import CASES, EXPERIMENTS

viewer_now = time.monotonic


def description(adapter, case=None):
    item = EXPERIMENTS[adapter]
    st.caption(f"{item['mode']} · {item['purpose']}")
    if case in CASES:
        st.caption(CASES[case])
    with st.expander("Experiment purpose, inputs and scientific limits"):
        st.json(item, expanded=True)


def _series(snapshots, channel, ylabel, *, reference=None, source="states.csv"):
    """Build native traces from this operation's verified snapshots, without rereading files."""
    figure = go.Figure()
    for snapshot in snapshots:
        frame = snapshot.data.frames[source]
        if channel in frame:
            figure.add_trace(
                go.Scatter(
                    x=frame.time,
                    y=frame[channel],
                    name=f"{snapshot.run.run_id} · {channel}",
                )
            )
        controls = snapshot.data.frames.get("controls.csv", {})
        if reference and reference in controls:
            figure.add_trace(
                go.Scatter(
                    x=controls.time,
                    y=controls[reference],
                    name=f"{snapshot.run.run_id} · {reference}",
                    line=dict(dash="dash"),
                )
            )
    return plots.style(figure, ylabel)


def _trajectory(snapshot):
    geometry = snapshot.data.frames["geometry.csv"]
    xy = snapshot.data.frames["trajectory_xy.csv"]
    figure = go.Figure()
    for x, y, name, color in (
        ("x", "y", "Centerline", "#8495ad"),
        ("left_x", "left_y", "Left boundary", "#455c76"),
        ("right_x", "right_y", "Right boundary", "#455c76"),
    ):
        figure.add_trace(
            go.Scatter(x=geometry[x], y=geometry[y], name=name, line=dict(color=color, dash="dot"))
        )
    figure.add_trace(
        go.Scatter(x=xy.x, y=xy.y, name="Plant trajectory", line=dict(color="#3ee0b2", width=3))
    )
    return plots.style(figure, "Y [m]", xy=True)


def channels(snapshots, key, selected_time, decisions=()):
    data = [s.data for s in snapshots]
    common = set(data[0].frames)
    for item in data[1:]:
        common &= set(item.frames)
    sources = [name for name in ("states.csv", "controls.csv", "diagnostics.csv") if name in common]
    if not sources:
        st.info("Scientific telemetry unavailable for this selection.")
        return True
    source_key, channel_key = key + "_source", key + "_channels"
    if st.session_state.get(source_key) not in sources:
        st.session_state[source_key] = sources[0]
    source = st.selectbox("Telemetry source", sources, key=source_key)
    available = [c for c in data[0].frames[source].columns if c != "time"]
    available = [c for c in available if all(c in item.frames[source] for item in data)]
    # Initialize through session state OR widget defaults, never both (V0.3-B N1).
    if channel_key not in st.session_state:
        st.session_state[channel_key] = [
            c for c in ("r", "vy", "delta", "alpha_f", "alpha_r") if c in available
        ][:3]
    else:
        st.session_state[channel_key] = [c for c in st.session_state[channel_key] if c in available]
    chosen = st.multiselect("Channels", available, key=channel_key)
    st.caption("Native raw time; no resampling, interpolation or inferred hold. Cursor is a guide.")
    columns = st.columns(2)
    for index, channel in enumerate(chosen):
        units = [views.unit(item, channel) for item in data]
        if len(set(units)) != 1:
            st.warning(f"{channel}: unit contracts differ; overlay withheld.")
            continue
        reference = views.REFERENCES.get(channel) if source == "states.csv" else None
        if reference and not all(reference in item.frames.get("controls.csv", {}) for item in data):
            st.caption(f"{channel}: reference channel unavailable in one or more records.")
            reference = None
        try:
            figure = _series(
                snapshots,
                channel,
                f"{channel} [{units[0]}]",
                reference=reference,
                source=source,
            )
            # Only this producer explicitly declares held input intervals. No data is resampled.
            if channel in {"delta", "a_cmd"}:
                for trace, snapshot in zip(figure.data, snapshots):
                    if (
                        snapshot.data.request["adapter"] == "dynamic_lab"
                        and snapshot.data.contract.get("row_semantics")
                        == "state at tick k; input held over next interval; terminal informational"
                    ):
                        trace.update(line_shape="hv")
            figure.update_layout(height=240)
            if selected_time is not None:
                figure.add_vline(x=selected_time, line_dash="dot")
            if not current(snapshots, decisions):
                return False
            with columns[index % 2]:
                st.plotly_chart(figure, width="stretch")
        except (OSError, ValueError):
            return False
    return True


def current(snapshots, decisions=()):
    return all(s.current() for s in snapshots) and all(
        views.comparison_current(d) for d in decisions
    )


def cursor(snapshots, key, identity):
    names = [s.run.case or s.run.adapter for s in snapshots]
    clock_key = key + "_clock"
    if st.session_state.get(clock_key, 0) >= len(snapshots):
        st.session_state[clock_key] = 0
    clock_column, speed_column = st.columns([4, 1])
    with clock_column:
        if len(snapshots) > 1:
            clock = st.selectbox(
                "Cursor timebase",
                list(range(len(snapshots))),
                format_func=lambda i: names[i] + " · " + snapshots[i].run.run_id,
                key=clock_key,
            )
        else:
            clock = 0
            st.caption(
                "Cursor follows native state samples; other sources require exact timestamps."
            )
    with speed_column:
        count = st.selectbox("Samples per viewer tick", [1, 5, 10], key=key + "_speed")
    timestamps = recorded.times(snapshots[clock])
    token = (identity, clock)
    state_key = key + "_playback"
    if st.session_state.get(key + "_identity") != token:
        st.session_state[key + "_identity"] = token
        st.session_state[state_key] = {"index": 0, "playing": False, "last_tick": viewer_now()}
        st.session_state[key + "_time"] = timestamps[0]
        st.session_state[key + "_requested_time"] = timestamps[0]
        st.session_state.pop(key + "_seek_error", None)
    state = recorded.tick(
        st.session_state[state_key], len(timestamps), viewer_now(), samples_per_tick=count
    )
    st.session_state[state_key] = state
    st.session_state[key + "_time"] = timestamps[state["index"]]

    def seek_slider():
        value = st.session_state[key + "_time"]
        st.session_state[state_key].update(index=timestamps.index(value), playing=False)
        st.session_state.pop(key + "_seek_error", None)

    def seek_exact():
        cursor_state = st.session_state[state_key]
        cursor_state["playing"] = False
        requested = st.session_state[key + "_requested_time"]
        if requested in timestamps:
            cursor_state["index"] = timestamps.index(requested)
            st.session_state.pop(key + "_seek_error", None)
        else:
            st.session_state[key + "_seek_error"] = (
                "No exact native state timestamp; no interpolation or snapping applied."
            )

    def move(count):
        cursor_state = st.session_state[state_key]
        cursor_state.update(
            index=recorded.step(cursor_state["index"], len(timestamps), count), playing=False
        )

    def play(playing):
        st.session_state[state_key].update(playing=playing, last_tick=viewer_now())

    timeline, entry, seek = st.columns([4, 2, 1])
    with timeline:
        st.select_slider("Selected time [s]", timestamps, key=key + "_time", on_change=seek_slider)
    with entry:
        st.number_input("Exact time entry [s]", key=key + "_requested_time", format="%.9f")
    with seek:
        st.button("Seek exact time", key=key + "_seek", on_click=seek_exact)
    if key + "_seek_error" in st.session_state:
        st.error(st.session_state[key + "_seek_error"])
    buttons = st.columns(4)
    with buttons[0]:
        st.button(
            "Previous sample",
            key=key + "_previous",
            disabled=state["index"] == 0,
            on_click=move,
            args=(-1,),
        )
    with buttons[1]:
        st.button(
            "Next sample",
            key=key + "_next",
            disabled=state["index"] == len(timestamps) - 1,
            on_click=move,
            args=(1,),
        )
    with buttons[2]:
        st.button(
            "Play recorded samples",
            key=key + "_play",
            disabled=state["index"] == len(timestamps) - 1 or state["playing"],
            on_click=play,
            args=(True,),
        )
    with buttons[3]:
        st.button(
            "Pause",
            key=key + "_pause",
            disabled=not state["playing"],
            on_click=play,
            args=(False,),
        )
    st.caption(
        "Recorded synthetic software replay · viewer tick 1 s (render dependent), "
        "not plant time, live telemetry or a real-time guarantee. No dynamics/control is executed."
    )
    st.caption("Event timeline unavailable in this Workbench profile; no events reconstructed.")
    selected = timestamps[state["index"]]
    st.caption(
        f"Native state sample {state['index']} · t={selected!r} s · "
        + ("Playing" if state["playing"] else "Paused")
    )
    return selected


def selected_samples(snapshots, selected_time):
    rows, detail = [], []
    for snapshot in snapshots:
        samples = {
            source: recorded.sample(snapshot, source, selected_time)
            for source in recorded.TIME_SOURCES
        }
        state, control = samples["states.csv"], samples["controls.csv"]
        diagnostic, xy = samples["diagnostics.csv"], samples["trajectory_xy.csv"]
        rows.append(
            {
                "run": snapshot.run.case or snapshot.run.run_id,
                "state_sample": state["sample_index"],
                "state_time_s": state["timestamp_s"],
                "r [rad/s]": state["values"].get("r"),
                "vy [m/s]": state["values"].get("vy"),
                "control_time_s": control["timestamp_s"],
                "delta [rad]": control["values"].get("delta"),
                "a_cmd [m/s^2]": control["values"].get("a_cmd"),
                "control_meaning": control["meaning"],
                "diagnostic_meaning": diagnostic["meaning"],
                "x [m]": xy["values"].get("x"),
                "y [m]": xy["values"].get("y"),
                "run_id": snapshot.run.run_id,
            }
        )
        for source, value in samples.items():
            detail.append({"run_id": snapshot.run.run_id, **value})
            if not value["available"]:
                st.caption(
                    f"{snapshot.run.case or snapshot.run.run_id} · {source}: {value['meaning']}"
                )
            elif source == "diagnostics.csv" and (
                "terminal" in value["meaning"] or "partial" in value["meaning"]
            ):
                st.caption(f"{snapshot.run.case or snapshot.run.run_id}: {value['meaning']}")
    st.dataframe(rows, hide_index=True, width="stretch")
    with st.expander("Exact source/sample identities and all selected native values"):
        st.json(detail)


def trajectory(snapshot, selected_time):
    if not all(name in snapshot.data.frames for name in ("geometry.csv", "trajectory_xy.csv")):
        st.info("Stored track/XY unavailable; no position reconstructed.")
        return
    figure = _trajectory(snapshot)
    point = (
        recorded.sample(snapshot, "trajectory_xy.csv", selected_time)
        if selected_time is not None
        else {"available": False}
    )
    if point["available"]:
        figure.add_trace(
            go.Scatter(
                x=[point["values"]["x"]],
                y=[point["values"]["y"]],
                name=f"Native XY at {point['timestamp_s']!r} s",
                mode="markers",
            )
        )
    figure.update_layout(height=400)
    st.plotly_chart(figure, width="stretch")


def analysis(runs, key, qualification_record=None, *, mounted_epoch=None):
    """All replay-dependent panels share one fragment and a validated evidence epoch."""
    running = st.session_state.get(key + "_playback", {}).get("playing", False)
    if mounted_epoch is None:
        try:
            mounted_epoch = views.comparison_epoch(runs, qualification_record)
        except (OSError, ValueError, RuntimeError):
            mounted_epoch = ()

    @st.fragment(run_every=1.0 if running else None)
    def frame():
        if st.session_state.get(key + "_playback", {}).get("playing", False) != running:
            st.rerun()  # Install/remove the timer before any costly scientific reads.
        result = st.empty()
        try:
            if mounted_epoch is None or mounted_epoch != views.comparison_epoch(
                runs, qualification_record
            ):
                raise ValueError("Mounted evidence changed; refresh the catalog before replay")
            pairs = []
            if len(runs) > 1:
                snapshots, pairs = recorded.matrix(runs, qualification_record)
            else:
                snapshots = [recorded.load(runs[0])]
            decisions = [p["decision"] for p in pairs]
            if any(d["classification"] == "invalid" for d in decisions):
                raise ValueError(
                    "Invalid pair: "
                    + "; ".join(d["reason"] for d in decisions if d["classification"] == "invalid")
                )
            q_epoch = (
                views.comparison_epoch((), qualification_record) if qualification_record else ()
            )
            identity = (tuple((s.run.key, s.epoch) for s in snapshots), q_epoch)
            with result.container():
                for snapshot in snapshots:
                    st.caption(
                        "Snapshot source · "
                        + snapshot.run.run_id
                        + " · "
                        + snapshot.data.request.get("provenance", {}).get("git_revision", "unknown")
                    )
                    if snapshot.data.status.get("scientific_outcome") != "completed":
                        st.warning(
                            "Unsuccessful/partial execution: retained samples only; "
                            + str(
                                snapshot.data.summary.get("failure")
                                or snapshot.data.status.get("error")
                                or "inspect original logs"
                            )
                        )
                    window = snapshot.data.summary.get("sampled_model_window", {})
                    if window.get("status") in {"outside_window", "unknown"}:
                        st.warning("Recorded sampled model window: " + str(window))
                if len(pairs) == 1:
                    st.subheader(decisions[0]["classification"].replace("_", " ").title())
                    st.caption(decisions[0]["reason"])
                elif pairs:
                    st.subheader("Pairwise eligibility — no group qualification")
                if pairs:
                    st.dataframe(
                        [
                            {
                                "left": runs[p["left"]].case or runs[p["left"]].run_id,
                                "left_run_id": runs[p["left"]].run_id,
                                "right": runs[p["right"]].case or runs[p["right"]].run_id,
                                "right_run_id": runs[p["right"]].run_id,
                                "classification": p["decision"]["classification"],
                                "reason": p["decision"]["reason"],
                            }
                            for p in pairs
                        ],
                        hide_index=True,
                        width="stretch",
                    )
                    with st.expander("Pairwise differences, source and qualification evidence"):
                        st.json(pairs)
                elif qualification_record and snapshots[0].data.request["adapter"] == "dynamic_lab":
                    try:
                        qualification = views.qualification(runs[0], qualification_record)
                        st.caption(
                            "Selected qualification: "
                            + qualification["numerical_qualification"]
                            + " · no physical validation"
                        )
                        with st.expander("Selected qualification evidence"):
                            st.json(qualification)
                    except (OSError, ValueError) as error:
                        st.error("Qualification unavailable/inapplicable: " + str(error))
                else:
                    st.caption("No qualification applied; original export-time status is retained.")
                selected_time = None
                if all(recorded.supports_replay(s) for s in snapshots):
                    selected_time = cursor(snapshots, key, identity)
                    selected_samples(snapshots, selected_time)
                else:
                    st.warning("Replay profile unsupported; verified native plots/raw data only.")
                    if key + "_playback" in st.session_state:
                        st.session_state[key + "_playback"]["playing"] = False
                if running and not st.session_state[key + "_playback"]["playing"]:
                    st.rerun()  # Cancel the frontend timer after pause/seek/end.
                left, right = st.columns([1, 2])
                with left:
                    trajectory(snapshots[0], selected_time)
                    if len(snapshots) > 1:
                        st.caption(
                            "XY follows the first selected run; all source XY samples above."
                        )
                with right:
                    stable = channels(snapshots, key, selected_time, decisions)
                if (
                    not stable
                    or not current(snapshots, decisions)
                    or (q_epoch and not views.comparison_current({"presentation_epoch": q_epoch}))
                ):
                    raise ValueError("Evidence/qualification changed during display")
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError) as error:
            result.empty()
            if key + "_playback" in st.session_state:
                st.session_state[key + "_playback"]["playing"] = False
            st.error("Scientific view withheld: " + str(error))
            st.info(
                "Inspect the original raw records; no interpolation, repair "
                "or qualification promotion."
            )
            if running:
                st.rerun()

    frame()


def details(run, data):
    diagnostics, evidence, notes = st.tabs(
        ["Diagnostics & raw data", "Evidence & provenance", "Notes"]
    )
    with diagnostics:
        if data.summary:
            st.json(data.summary, expanded=False)
        with st.expander("Native raw rows, columns and units"):
            for name, frame in data.frames.items():
                st.write(name)
                st.dataframe(frame, width="stretch", hide_index=True)
            st.json(data.contract, expanded=False)
    with evidence:
        with st.expander("Configuration and source provenance"):
            st.code(str(run.directory), language=None)
            st.json(data.request, expanded=False)
            st.json(data.environment, expanded=False)
        with st.expander("Verified artifact index and export"):
            st.json(data.manifest, expanded=False)
            if data.valid:
                try:
                    st.download_button(
                        "Download manifest-verified run files",
                        views.bundle(run),
                        run.run_id + ".zip",
                        "application/zip",
                    )
                except (OSError, ValueError) as error:
                    st.error("Export unavailable/changed: " + str(error))
        with st.expander("Raw records and failure logs", expanded=not data.valid):
            st.caption(
                "Diagnostic text: last 100,000 bytes/file; unverified for invalid/active evidence."
            )
            for name, text in views.raw_records(run).items():
                st.write(name)
                st.code(text, language=None)
    with notes:
        latest, problems = views.notes(run)
        for problem in problems:
            st.warning(problem)
        if run.owned:
            with st.form("notes_" + run.key):
                observation = st.text_area(
                    "Observation",
                    value=latest.get("observation", ""),
                    max_chars=8000,
                    key="observation_" + run.key,
                )
                explanation = st.text_area(
                    "Interpretation",
                    value=latest.get("explanation", ""),
                    max_chars=8000,
                    key="explanation_" + run.key,
                )
                if st.form_submit_button("Append engineering note"):
                    jobs.save_notes(run.directory, observation, explanation)
                    st.success("New version saved; earlier notes and original prediction retained.")
        else:
            st.caption("Archive notes are read-only.")
            st.json(latest, expanded=False)
