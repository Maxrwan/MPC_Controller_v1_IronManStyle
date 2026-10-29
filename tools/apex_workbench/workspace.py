"""Primary engineering presentation over the unchanged accepted Workbench engine."""

import shutil
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.apex_workbench import engineering_views as views  # noqa: E402
from tools.apex_workbench import jobs, plots, run_catalog  # noqa: E402
from tools.apex_workbench.configuration import (  # noqa: E402
    ADAPTERS,
    BOUNDS,
    DEFAULTS,
    ROOT,
    validate,
)

st.set_page_config(page_title="APEX Engineering Workspace", page_icon="🏎", layout="wide")
st.title("APEX Engineering Workspace")
st.caption("Synthetic models · accepted finite numerical scope · no physical validation")
if "next_view" in st.session_state:
    st.session_state["workspace_view"] = st.session_state.pop("next_view")
catalog = run_catalog.discover()
by_key = {run.key: run for run in catalog.runs}
pending = st.session_state.pop("pending_directory", None)
if pending:
    match = next((run for run in catalog.runs if str(run.directory) == pending), None)
    if match:
        st.session_state["inspect_run"] = match.key
with st.sidebar:
    page = st.radio("Workspace", ["Home", "Run", "Inspect", "Compare"], key="workspace_view")
    st.button("Refresh catalog")
    selected_qualification = st.selectbox(
        "Qualification record",
        [None, *catalog.qualifications],
        format_func=lambda p: "None selected" if p is None else p.parent.name,
        key="selected_qualification",
    )
    st.caption(
        "Discovery is metadata only. Qualification is checked when applied to a verified run."
    )
for problem in catalog.issues:
    st.warning(problem)


def selector(label, key):
    if not by_key:
        st.info("No records discovered in the approved roots.")
        return None
    if st.session_state.get(key) not in by_key:
        st.session_state.pop(key, None)
    chosen = st.selectbox(label, list(by_key), format_func=lambda k: by_key[k].label, key=key)
    return by_key[chosen]


def show_channels(runs, data, key, *, decision=None):
    common = set(data[0].frames)
    for item in data[1:]:
        common &= set(item.frames)
    sources = [name for name in ("states.csv", "controls.csv", "diagnostics.csv") if name in common]
    if not sources:
        st.info("Scientific telemetry unavailable for this selection.")
        return True
    if st.session_state.get(key + "_source") not in sources:
        st.session_state.pop(key + "_source", None)
    source = st.selectbox("Telemetry source", sources, key=key + "_source")
    channels = [c for c in data[0].frames[source].columns if c != "time"]
    channels = [c for c in channels if all(c in item.frames[source] for item in data)]
    defaults = [c for c in ("r", "vy", "delta", "alpha_f", "alpha_r") if c in channels][:3]
    if key + "_channels" in st.session_state:
        st.session_state[key + "_channels"] = [
            c for c in st.session_state[key + "_channels"] if c in channels
        ]
    chosen = st.multiselect("Channels", channels, default=defaults, key=key + "_channels")
    st.caption(
        "Raw retained timestamps; no interpolation, time alignment or new metric calculation."
    )
    for channel in chosen:
        units = [views.unit(item, channel) for item in data]
        if len(set(units)) != 1:
            st.warning(f"{channel}: different/unknown unit contracts; overlay withheld.")
            continue
        reference = views.REFERENCES.get(channel) if source == "states.csv" else None
        if reference and not all(reference in item.frames.get("controls.csv", {}) for item in data):
            st.caption(f"{channel}: reference channel unavailable in one or more records.")
            reference = None
        try:
            figure = plots.series(
                [(run.run_id, run.directory) for run in runs],
                [channel],
                f"{channel} [{units[0]}]",
                reference=reference,
                source=source,
            )
            if decision is not None and not views.comparison_current(decision):
                return False
            st.plotly_chart(figure, width="stretch")
        except (OSError, ValueError) as error:
            st.error("Telemetry unavailable/changed: " + str(error))
            return False
    return True


if page == "Home":
    st.subheader("Engineering home")
    st.write("Supported execution modes")
    for name, label in ADAPTERS.items():
        st.write(f"• {label} ({name})")
    st.caption("LQR/PI uses the scheduled baseline, not trajectory-dependent TVLQR.")
    st.info(
        "Unavailable here: NMPC/TVLQR/async execution, multi-run comparison beyond two, "
        "telemetry import/replay, physical telemetry and Safety commands."
    )
    try:
        jobs.preflight()
        st.caption(
            "Disk/measurement preflight passes; execution ownership is checked again at admission."
        )
    except (OSError, RuntimeError) as error:
        st.warning(str(error))
    st.caption(
        f"Free local disk: {shutil.disk_usage(ROOT).free:,} bytes. Owned root: {catalog.owned_root}"
    )
    adapter_filter = st.selectbox("Adapter filter", ["All", *ADAPTERS])
    state_filter = st.selectbox(
        "Outcome filter", ["All", *sorted({r.outcome for r in catalog.runs})]
    )
    rows = [
        run
        for run in catalog.runs
        if (adapter_filter == "All" or run.adapter == adapter_filter)
        and (state_filter == "All" or run.outcome == state_filter)
    ]
    st.caption(
        "Discovery metadata below is unverified; inspect a record before interpreting it. "
        "Aliases are grouped, not counted as new executions."
    )
    st.dataframe(
        [
            dict(
                run_id=r.run_id,
                adapter=r.adapter,
                case=r.case,
                profile=r.profile,
                state=r.state,
                outcome=r.outcome,
                evidence=r.evidence,
                sources=", ".join(r.origins),
                aliases=len(r.aliases),
                discovery_issues="; ".join(r.issues),
            )
            for r in rows
        ],
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Legacy compatibility application remains at tools/apex_workbench/app.py; "
        "direct launch instructions are in the Workbench README."
    )

elif page == "Run":
    st.subheader("Run an accepted experiment")
    adapter = st.selectbox("Execution mode", list(ADAPTERS), format_func=ADAPTERS.get)
    with st.form("engineering_run"):
        if adapter == "dynamic_lab":
            from tools.apex_workbench.lab_configuration import CASES, request_for, resolve

            values = request_for(st.selectbox("Synthetic case", CASES))
            st.json(resolve(values), expanded=False)
            st.caption(
                "Nominal grid only. A completed run does not confer qualification; "
                "select and validate qualification evidence separately."
            )
        else:
            values = dict(DEFAULTS[adapter])
            for name in values:
                if name == "track":
                    values[name] = st.selectbox("Track", ["circle", "oval"])
                else:
                    labels = {
                        "duration": "Duration [s]",
                        "dt": "Integration timestep [s]",
                        "speed": "Initial/reference speed [m/s]",
                        "ey": "Initial e_y [m]",
                        "epsi": "Initial e_psi [rad]",
                    }
                    low, high = BOUNDS[name]
                    values[name] = st.number_input(
                        labels[name],
                        min_value=low,
                        max_value=high,
                        value=float(values[name]),
                        format="%.4f",
                        key=adapter + "_" + name,
                    )
            st.caption(
                "Accepted entrypoint, fixed vehicle/controller/tire/timing assumptions; "
                "ranges are existing software safeguards."
            )
            st.json(values, expanded=False)
        note = st.text_area("Engineering run note (optional)", max_chars=8000)
        submitted = st.form_submit_button("Start run", type="primary")
    if submitted:
        try:
            validate(adapter, values)
            directory = jobs.start_run(adapter, values, note, runs=catalog.owned_root)
            st.session_state["pending_directory"] = str(directory.resolve())
            st.session_state["next_view"] = "Inspect"
            st.rerun()
        except (OSError, ValueError, RuntimeError) as error:
            st.error(str(error))

elif page == "Inspect":
    st.subheader("Inspect a retained run")
    run = selector("Run", "inspect_run")
    if run:
        st.code(str(run.directory), language=None)
        st.caption(
            "Sources: "
            + ", ".join(run.origins)
            + "; metadata discovery does not establish validity."
        )
        if len(run.aliases) > 1:
            st.warning(
                "Captured execution has path aliases; it is shown once, not as new executions."
            )
            st.json([str(path) for path in run.aliases], expanded=False)
        for issue in run.issues:
            st.caption(issue)
        data = views.inspect(run)
        st.json(
            {"execution_status": data.status, "scientific_evidence_valid": data.valid},
            expanded=False,
        )
        if data.status.get("state") in views.ACTIVE and run.owned:
            if st.button("Refresh owned execution status"):
                jobs.status_for(run.directory)
                st.rerun()
            if st.button("Cancel owned run"):
                jobs.cancel_run(run.directory)
                st.rerun()
        if data.error:
            if data.status.get("state") in views.ACTIVE:
                st.warning(data.error)
            else:
                st.error("Evidence quarantined: " + data.error)
        if not run.owned:
            st.caption(
                "Archive is read-only: no reconciliation, cancellation or annotation writes."
            )
        if data.request:
            with st.expander("Configuration and source provenance", expanded=True):
                st.json(data.request)
        if data.valid:
            st.caption(
                "Required artifacts and all manifest-listed bytes verified. "
                "Scientific outcome, coverage and qualification remain separate."
            )
            st.subheader("Existing summary metrics and numerical environment")
            if data.summary:
                st.json(data.summary, expanded=False)
            else:
                st.info("Summary unavailable.")
            if data.environment:
                st.json(data.environment, expanded=False)
            else:
                st.info("Numerical environment unavailable.")
            if selected_qualification is not None and data.request["adapter"] == "dynamic_lab":
                try:
                    st.json(views.qualification(run, selected_qualification), expanded=False)
                    st.caption(
                        "Selected qualification validated against this run; no physical validation."
                    )
                except (OSError, ValueError) as error:
                    st.error("Qualification unavailable/inapplicable: " + str(error))
            else:
                st.caption(
                    "No qualification applied. "
                    "Export-time summary is preserved as originally recorded."
                )
            st.subheader("Trajectory and available telemetry")
            if all(name in data.frames for name in ("geometry.csv", "trajectory_xy.csv")):
                try:
                    st.plotly_chart(plots.trajectory(run.directory), width="stretch")
                except (OSError, ValueError) as error:
                    st.error("Trajectory unavailable/changed: " + str(error))
            else:
                st.info("Track/trajectory export unavailable.")
            st.json(
                {name: list(frame.columns) for name, frame in data.frames.items()}, expanded=False
            )
            show_channels([run], [data], "inspect")
            for name, frame in data.frames.items():
                with st.expander(name + " — actual rows and native coverage"):
                    st.caption(f"{len(frame)} retained rows; original units/column contract below.")
                    st.dataframe(frame, width="stretch", hide_index=True)
            st.json(data.contract, expanded=False)
            with st.expander("Verified retained artifact index and export"):
                st.json(data.manifest)
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
                "Diagnostic text, last 100,000 bytes per file. "
                "Unverified when evidence is invalid/active; not scientific interpretation."
            )
            for name, text in views.raw_records(run).items():
                st.write(name)
                st.code(text, language=None)
        with st.expander("Engineering notes (optional)"):
            latest, problems = views.notes(run)
            for problem in problems:
                st.warning(problem)
            if run.owned:
                with st.form("notes_" + run.key):
                    observation = st.text_area(
                        "Observation", value=latest.get("observation", ""), max_chars=8000
                    )
                    explanation = st.text_area(
                        "Interpretation", value=latest.get("explanation", ""), max_chars=8000
                    )
                    if st.form_submit_button("Append engineering note"):
                        jobs.save_notes(run.directory, observation, explanation)
                        st.success("New note version saved; earlier notes retained.")
            else:
                st.json(latest)

else:
    st.subheader("Compare two retained runs")
    selected = st.multiselect(
        "Runs", list(by_key), max_selections=2, format_func=lambda key: by_key[key].label
    )
    if len(selected) == 2:
        runs = [by_key[key] for key in selected]
        decision = views.compare(*runs, qualification_record=selected_qualification)
        data = []
        if decision["classification"] != "invalid":
            data = [views.inspect(run) for run in runs]
            if any(not item.valid for item in data) or not views.comparison_current(decision):
                decision = views.invalid_comparison(
                    "Evidence changed after comparison; refresh or inspect the raw records."
                )
        result = st.empty()
        stable = True
        with result.container():
            label = decision["classification"]
            st.subheader(label.replace("_", " ").title())
            st.json(decision, expanded=False)
            if label == "invalid":
                st.error(decision["reason"])
                st.info(
                    "Scientific overlays withheld. Inspect each record's raw logs to investigate."
                )
            else:
                st.write(decision["reason"])
                if label == "qualified_synthetic_comparison":
                    st.caption(
                        "Accepted finite numerical criteria · sampled model window · "
                        "no physical validation"
                    )
                st.write(
                    "Actual configuration, outcome, existing summary values/units and raw coverage"
                )
                for run, item in zip(runs, data):
                    st.json(
                        {
                            "run": run.run_id,
                            "configuration": item.request["effective"],
                            "status": item.status,
                            "existing_summary": item.summary,
                            "telemetry_contract": item.contract,
                        },
                        expanded=False,
                    )
                stable = show_channels(runs, data, "compare", decision=decision)
        if label != "invalid" and (not stable or not views.comparison_current(decision)):
            result.empty()
            st.error("Evidence changed during display; classification and overlays withheld.")
