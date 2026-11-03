"""Compact experimental NMPC presentation; no scientific imports or numerical execution here."""

import json
import os
import uuid

import plotly.graph_objects as go
import streamlit as st

from tools.apex_workbench import jobs, storage
from tools.apex_workbench import nmpc_weight_lab as lab

PLOT_CONFIG = {"displayModeBar": False, "modeBarButtonsToRemove": ["toImage"], "displaylogo": False}
UNITS = {"vx": "m/s", "vy": "m/s", "r": "rad/s", "e_y": "m", "e_psi": "rad", "s_abs": "m"}


def preview_path(preset):
    lab.validate({"preset": preset})
    return lab.safe(lab.OUTPUT / "previews" / lab.SUCCESSOR / (preset + ".json"))


def _preview_directory(path):
    """Open each directory without following links, including during namespace replacement."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    create_from = len(lab.safe(lab.OUTPUT).parts) - 1
    descriptor = os.open(path.anchor, flags)
    try:
        for index, name in enumerate(path.parts[1:], start=1):
            if index >= create_from:
                try:
                    os.mkdir(name, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(name, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def publish_preview(preset, report):
    path = preview_path(preset)
    data = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode("utf-8")
    descriptor = _preview_directory(path.parent)
    temporary = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        name = ".pending-" + uuid.uuid4().hex + ".tmp"
        stream = os.open(name, flags, 0o600, dir_fd=descriptor)
        temporary = name
        with os.fdopen(stream, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        # The same pinned directory owns both names even if its pathname is swapped.
        os.replace(temporary, path.name, src_dir_fd=descriptor, dst_dir_fd=descriptor)
        os.fsync(descriptor)
        visible, pinned = preview_path(preset).parent.stat(), os.fstat(descriptor)
        if (visible.st_dev, visible.st_ino) != (pinned.st_dev, pinned.st_ino):
            raise ValueError("Preview namespace changed during publication")
    finally:
        try:
            if temporary is not None:
                try:
                    os.unlink(temporary, dir_fd=descriptor)
                except FileNotFoundError:
                    pass
        finally:
            os.close(descriptor)


def run_panel():
    st.warning(lab.BANNER)
    preset = st.selectbox("M0 preset", list(lab.PRESETS))
    st.caption("One fixed controlled GP gamma2 / A / N8 / 0.1 s / RK4×4 / 2.0 s scenario.")
    st.write(
        "Stage tracking coefficients: "
        + str([4, 4, 1, 100 * lab.PRESETS[preset], 100 * lab.PRESETS[preset]])
    )
    try:
        preview = preview_path(preset)
        if preview.exists():
            report = storage.read_json(preview)
            with st.expander(
                "Complete source-isolated effective configuration and import identities"
            ):
                st.text(json.dumps(report, indent=2))
            st.caption(
                "Mutable, non-authoritative configuration preview; execution independently repeats "
                "identity/configuration checks against sealed gate evidence."
            )
        else:
            st.info(
                "No prepared configuration preview; execution is gated until software checks pass."
            )
    except (OSError, ValueError, RuntimeError) as error:
        st.error("Configuration preview unavailable: " + str(error))
    if st.button("Validate frozen configuration (no solve)"):
        try:
            report = lab.probe(preset)
            publish_preview(preset, report)
            st.rerun()
        except (OSError, ValueError, RuntimeError) as error:
            st.error(str(error))
    try:
        # Readiness hint; admission and the fresh worker check actual dependencies.
        lab.verify_gate(check_environment=False)
        ready = lab.available(preset)
        if not ready:
            st.info(
                "This preset's single M0 attempt is consumed. Inspect its outcome; "
                "further execution requires Primary authorization."
            )
    except (OSError, ValueError, RuntimeError) as error:
        ready = False
        st.info("Numerical gate closed: " + str(error))
    if st.button("Run one authorized M0 attempt", disabled=not ready):
        try:
            directory = jobs.start_run(lab.ADAPTER, {"preset": preset}, runs=lab.RUNS)
            st.session_state["pending_directory"] = str(directory)
            st.session_state["next_view"] = "Inspect"
            st.rerun()
        except (OSError, ValueError, RuntimeError) as error:
            st.error(str(error))


def signal(raw, channel):
    rows = raw.get("states", [])
    plot = go.Figure(
        go.Scattergl(
            x=[r["time"] for r in rows], y=[r[channel] for r in rows], mode="markers", name=channel
        )
    )
    plot.update_layout(
        title="EXPERIMENTAL / UNQUALIFIED · native " + channel,
        xaxis_title="Native simulated state time [s]",
        yaxis_title=channel + " [" + UNITS[channel] + "]",
    )
    return plot


def commands(raw, channel="delta"):
    plot = go.Figure()
    for clock, field, name in (
        ("time", "requested_" + channel, "Requested at computation time"),
        ("application_time", channel, "Applied at native application_time"),
    ):
        rows = [r for r in raw.get("controls", []) if r.get(clock) is not None and field in r]
        plot.add_trace(
            go.Scattergl(
                x=[r[clock] for r in rows], y=[r[field] for r in rows], mode="markers", name=name
            )
        )
    plot.update_layout(
        title="EXPERIMENTAL / UNQUALIFIED · requests versus applications",
        xaxis_title="Independent native clocks [s]",
        yaxis_title="Steering delta [rad]" if channel == "delta" else "a_cmd = Fx/m [m/s²]",
    )
    return plot


def _inspect(selected):
    st.warning(lab.BANNER)
    directory, anchor = lab.owned_run(selected)
    status = jobs.status_for(directory)
    if lab.owned_run(selected) != (directory, anchor):
        raise ValueError("M0 ownership changed during lifecycle inspection")
    st.write(
        "Execution: "
        + status.get("state", "unknown")
        + " / evidence: "
        + status.get("evidence_state", "unknown")
    )
    if status.get("state") in jobs.ACTIVE:
        st.button("Refresh M0 owned run")
        if st.button("Cancel M0 owned run"):
            if lab.owned_run(selected) != (directory, anchor):
                raise ValueError("M0 ownership changed before cancellation")
            jobs.cancel_run(directory)
            st.rerun()
        st.caption(
            "In-progress evidence is not committed; "
            "any native journals are retained without reconstruction."
        )
        return
    view = lab.read_run(directory)
    raw = view["raw"]
    summary = storage.artifact_json(directory, "experiment/summary.json", optional=True)
    if summary is not None:
        st.table([{k: json.dumps(v) for k, v in summary.items()}], hide_index=True)
    with st.expander("Effective configuration, frozen provenance and original outcome"):
        st.text(json.dumps({"request": view["request"], "status": view["status"]}, indent=2))
    if raw is None:
        st.info(
            "Original runner result unavailable; failed/cancelled native journals remain retained."
        )
    else:
        channel = st.selectbox("M0 native state", list(UNITS), index=list(UNITS).index("e_y"))
        command = st.selectbox("M0 native command", ["delta", "a_cmd"])
        built = [signal(raw, channel), commands(raw, command)]
        lab.current(view)
        for plot in built:
            st.plotly_chart(plot, width="stretch", config=PLOT_CONFIG)
        st.caption(
            "No interpolation or held-command inference. e_y/e_psi are native Frenet states, "
            "not an invented racing-reference residual. Optimization/preparation success "
            "does not prove packet or command application."
        )
        st.table(
            [{k: json.dumps(v) for k, v in lab.descriptive_metrics(raw).items()}], hide_index=True
        )
        plans = raw.get("plans", [])
        st.subheader("Native optimizer / planner events")
        st.caption(
            "Components are frozen-controller post-solve expression evaluations after validation, "
            "not native IPOPT instrumentation. Unavailable is not zero. "
            "solve_time/planner_total_time are host durations; release_time/physical_delay "
            "belong to the simulated clock/imposed availability; startup is prelaunch."
        )
        st.caption(
            "Different weights change objective meaning: totals are not a common performance score."
        )
        st.table(
            [
                {
                    "plan_id": str(p["plan_id"]),
                    "release_time": str(p.get("release_time", "absent")),
                    "status": str(p.get("status", "absent")),
                    "success": str(p.get("success", "absent")),
                    "iterations": str(p.get("iterations", "unavailable")),
                    "feasibility": str(p.get("primal_infeasibility", "unavailable")),
                    "max_slack": str(p.get("max_slack", "unavailable")),
                    "solve_time_s": str(p.get("solve_time", "unavailable")),
                    "planner_total_time_s": str(p.get("planner_total_time", "unavailable")),
                    "physical_delay_s": str(p.get("physical_delay", "unavailable")),
                    "objective_components": json.dumps(
                        p.get("objective_components", "unavailable")
                    ),
                }
                for p in plans
            ],
            hide_index=True,
        )
        with st.expander("Original native states, controls, plans, packets and stop reasons"):
            st.text("BEGIN NATIVE RESULT\n" + json.dumps(raw, indent=2) + "\nEND NATIVE RESULT")
    for name in (
        "optimizations.jsonl",
        "preparations.jsonl",
        "plant_segments.jsonl",
        "command_requests.jsonl",
    ):
        with st.expander("Retained native callback journal: " + name):
            content = storage.artifact_bytes(directory, "experiment/" + name, optional=True)
            st.text(content.decode() if content is not None else "unavailable")
    st.caption(
        "Callbacks retain successful-event association and native plant segments, "
        "including partial coverage; they are not fabricated native runner results."
        " Native controls carry request values alongside application rows; the separate TVLQR "
        "journal retains every observed live proposal before runner validation/application."
    )
    lab.current(view)


def inspect(selected):
    scope = st.empty()
    try:
        with scope.container():
            _inspect(selected)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        scope.empty()
        scope.error("M0 evidence quarantined/unavailable: " + str(error))


def comparison(a, b):
    if a["request"]["run_id"] == b["request"]["run_id"]:
        raise ValueError("An alias is not a second experiment")
    presets = {a["request"]["effective"]["preset"], b["request"]["effective"]["preset"]}
    if presets != {"nominal", "exploratory"}:
        raise ValueError("Select the one nominal and one exploratory M0 attempt")
    configs = []
    for view in (a, b):
        config = json.loads(json.dumps(view["request"]["nmpc_capture"]["resolved"]))
        config.pop("preset")
        config.pop("stage_coefficients")
        config["configuration"]["costs"].pop("lateral")
        configs.append(config)
    if configs[0] != configs[1]:
        raise ValueError("Non-treatment configuration differs")
    return (
        "Experimental / unqualified nominal–exploratory pair; "
        "native independent coverage, no objective-total ranking"
    )


def compare_panel():
    st.warning(lab.BANNER)
    dirs = (
        [p for p in sorted(lab.RUNS.iterdir()) if p.is_dir() and not p.name.startswith(".")]
        if lab.RUNS.exists()
        else []
    )
    selected = st.multiselect(
        "M0 retained attempts", dirs, max_selections=2, format_func=lambda p: p.name
    )
    if len(selected) != 2:
        st.info(
            "Select the two retained attempts; partial/failed outcomes remain visible in Inspect."
        )
        return
    scope = st.empty()
    try:
        a, b = [lab.read_run(p) for p in selected]
        label = comparison(a, b)
        plot = go.Figure()
        for view in (a, b):
            raw = view["raw"] or {}
            rows = raw.get("states", [])
            plot.add_trace(
                go.Scattergl(
                    x=[r["time"] for r in rows],
                    y=[r["e_y"] for r in rows],
                    mode="markers",
                    name=view["request"]["effective"]["preset"],
                )
            )
        plot.update_layout(
            title="EXPERIMENTAL / UNQUALIFIED · native Frenet e_y",
            xaxis_title="Native simulated time [s]",
            yaxis_title="e_y [m]",
        )
        for view in (a, b):
            lab.current(view)
        with scope.container():
            st.caption(label)
            st.plotly_chart(plot, width="stretch", config=PLOT_CONFIG)
            st.table(
                [
                    {
                        "preset": v["request"]["effective"]["preset"],
                        "outcome": v["status"]["state"],
                        **{
                            k: json.dumps(value)
                            for k, value in lab.descriptive_metrics(v["raw"]).items()
                        },
                    }
                    for v in (a, b)
                ],
                hide_index=True,
            )
            st.caption(
                "RMS uses each run's own native sample coverage. Partial/different coverage "
                "is not a performance ranking. Differently weighted objective totals "
                "are deliberately not compared."
            )
        for view in (a, b):
            lab.current(view)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        scope.empty()
        scope.error("M0 comparison quarantined: " + str(error))
