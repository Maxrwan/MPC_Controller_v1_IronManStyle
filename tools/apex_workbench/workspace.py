"""Primary engineering presentation over the unchanged accepted Workbench engine."""

import shutil
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.apex_workbench import (  # noqa: E402  # noqa: E402
    c0_panels,
    gp_archive,
    gp_panels,
    jobs,
    run_catalog,
)
from tools.apex_workbench import engineering_views as views  # noqa: E402
from tools.apex_workbench import recorded_view as recorded  # noqa: E402
from tools.apex_workbench import workspace_panels as panels
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
if st.session_state.pop("prepare_oval", False):
    st.session_state["execution_mode"] = "lqr_baseline"
    for name, value in {**DEFAULTS["lqr_baseline"], "track": "oval"}.items():
        st.session_state["lqr_baseline_" + name] = value
catalog = run_catalog.discover(include_racing=True)
by_key = {run.key: run for run in catalog.runs}
pending = st.session_state.pop("pending_directory", None)
if pending:
    match = next((run for run in catalog.runs if str(run.directory) == pending), None)
    if match:
        st.session_state["inspect_run"] = match.key
        st.session_state["inspect_archive"] = "Workbench / P retained runs"
with st.sidebar:
    page = st.radio("Workspace", ["Home", "Run", "Inspect", "Compare"], key="workspace_view")
    st.button("Refresh catalog")
    if st.session_state.get("selected_qualification") not in (None, *catalog.qualifications):
        st.session_state["selected_qualification"] = None
    selected_qualification = st.selectbox(
        "Qualification record",
        [None, *catalog.qualifications],
        format_func=lambda p: "None selected" if p is None else p.parent.name,
        key="selected_qualification",
    )
    st.caption(
        "Discovery is metadata only. Qualification is checked when applied to a verified run."
    )
if st.session_state.get("previous_workspace_view") != page:
    for name in ("inspect_playback", "compare_playback"):
        if name in st.session_state:
            st.session_state[name]["playing"] = False
    st.session_state["previous_workspace_view"] = page
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


if page == "Home":
    st.subheader("Engineering home")
    if st.button("Inspect retained C0 descriptive-only archive"):
        st.session_state["next_view"] = "Inspect"
        st.session_state["inspect_archive"] = "C0 descriptive-only record"
        st.rerun()
    if st.button("Inspect retained Performance P GP archive"):
        st.session_state["inspect_run"] = "gp-" + gp_archive.MANIFEST_SHA256
        st.session_state["inspect_archive"] = "Workbench / P retained runs"
        st.session_state["next_view"] = "Inspect"
        st.rerun()
    if st.button("Prepare 2 m/s oval LQR/PI"):
        st.session_state["prepare_oval"] = True
        st.session_state["next_view"] = "Run"
        st.rerun()
    st.caption(
        "Oval shortcut prepares the existing 12 s / 2 m/s / zero-error interface; Start run "
        "remains explicit. Historical results/lqr_baseline/oval_2mps is preserved, but lacks "
        "the source-bound Workbench integrity contract and is not promoted to verified evidence."
    )
    st.write("Supported execution modes")
    for name, label in ADAPTERS.items():
        st.write(f"• {label} ({name})")
    st.caption(
        "LQR/PI uses the scheduled baseline, not trajectory-dependent TVLQR. "
        "Replay reads retained software samples; comparison supports two to four runs."
    )
    with st.expander("Experiment descriptions"):
        for adapter in ADAPTERS:
            st.write(ADAPTERS[adapter])
            panels.description(adapter)
    st.info(
        "Unavailable here: NMPC/TVLQR/async execution, arbitrary telemetry import, "
        "physical telemetry, Safety commands and proposed racing-scenario execution."
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
    adapter_filter = st.selectbox("Adapter filter", ["All", *ADAPTERS, gp_archive.ADAPTER])
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
    adapter = st.selectbox(
        "Execution mode", list(ADAPTERS), format_func=ADAPTERS.get, key="execution_mode"
    )
    if adapter == "dynamic_lab":
        from tools.apex_workbench.lab_configuration import CASES, request_for, resolve

        # Outside the submission form so descriptions/snapshots follow case selection immediately.
        case = st.selectbox("Synthetic case", CASES)
        panels.description(adapter, case)
    else:
        panels.description(adapter)
    with st.form("engineering_run"):
        if adapter == "dynamic_lab":
            values = request_for(case)
            with st.expander("Exact accepted parameter/state/input snapshot"):
                st.json(resolve(values), expanded=False)
            st.caption(
                "Nominal grid only. A completed run does not confer qualification; "
                "select and validate qualification evidence separately."
            )
        else:
            values = dict(DEFAULTS[adapter])
            form_columns = st.columns(2)
            for input_index, name in enumerate(values):
                with form_columns[input_index % 2]:
                    if name == "track":
                        values[name] = st.selectbox(
                            "Track", ["circle", "oval"], key=adapter + "_track"
                        )
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
    archive_kind = st.radio(
        "Inspection source",
        ["Workbench / P retained runs", "C0 descriptive-only record"],
        key="inspect_archive",
    )
    if archive_kind == "C0 descriptive-only record":
        c0_panels.inspect()
        st.stop()
    run = selector("Run", "inspect_run")
    if run and run.adapter == gp_archive.ADAPTER:
        gp_panels.inspect(run)
        st.stop()
    if run:
        try:
            mounted = views.comparison_epoch((run,), selected_qualification)
        except (OSError, ValueError, RuntimeError):
            mounted = ()
        data = views.inspect(run)
        status_columns = st.columns(3)
        for column, label, value in zip(
            status_columns,
            ("Execution", "Evidence", "Profile"),
            (
                data.status.get("scientific_outcome", data.status.get("state", "unknown")),
                data.status.get("evidence_state", "unknown"),
                run.profile,
            ),
        ):
            column.metric(label, str(value))
        st.caption(f"Run {run.run_id} · {', '.join(run.origins)}")
        if run.adapter in ADAPTERS:
            panels.description(run.adapter, run.case)
        for issue in run.issues:
            st.warning(issue)
        if len(run.aliases) > 1:
            st.caption("Path aliases grouped as one execution; original source retained.")
            with st.expander("Source aliases"):
                st.json([str(path) for path in run.aliases])
        if data.status.get("state") in views.ACTIVE and run.owned:
            refresh, cancel = st.columns(2)
            with refresh:
                if st.button("Refresh owned execution status"):
                    jobs.status_for(run.directory)
                    st.rerun()
            with cancel:
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
        if data.valid:
            st.caption(
                "Verified artifacts · execution, coverage and qualification remain separate."
            )
            panels.analysis([run], "inspect", selected_qualification, mounted_epoch=mounted)
        panels.details(run, data)

else:
    st.subheader("Compare retained runs")
    compare_keys = [key for key in by_key if by_key[key].adapter != gp_archive.ADAPTER]
    if "compare_runs" in st.session_state:
        st.session_state["compare_runs"] = [
            key for key in st.session_state["compare_runs"] if key in compare_keys
        ][: recorded.MAX_RUNS]
    selected = st.multiselect(
        "Runs",
        compare_keys,
        max_selections=recorded.MAX_RUNS,
        format_func=lambda key: by_key[key].label,
        key="compare_runs",
    )
    st.caption(
        "Two to four original executions · pairwise eligibility, no group qualification. "
        "Native timestamps only; no resampling or causal ranking of illustrative pairs."
    )
    st.caption(
        "Historical GP profile P has no accepted cross-profile comparison contract; "
        "inspect separately."
    )
    if len(selected) >= 2:
        runs = [by_key[key] for key in selected]
        panels.analysis(runs, "compare", selected_qualification)
        if st.toggle(
            "Selected configurations, provenance and original summaries", key="compare_details"
        ):
            for run in runs:
                data = views.inspect(run)
                st.json(
                    {
                        "run_id": run.run_id,
                        "original_path": str(run.directory),
                        "request": data.request,
                        "outcome": data.status,
                        "summary": data.summary,
                        "units": data.contract,
                    },
                    expanded=False,
                )
