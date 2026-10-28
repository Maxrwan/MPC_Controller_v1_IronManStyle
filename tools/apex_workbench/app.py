"""APEX Workbench V0.1 — local experiment, predict, inspect and retain loop."""

import io
import sys
import zipfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.apex_workbench import comparison, jobs, plots, storage  # noqa: E402
from tools.apex_workbench.configuration import ADAPTERS, DEFAULTS, RUNS, validate  # noqa: E402

st.set_page_config(page_title="APEX Workbench", page_icon="🏎", layout="wide")
st.markdown(
    """<style>
.stApp {background:#0c1421;color:#e8eef6}
[data-testid="stSidebar"] {background:#111e30}
h1 {letter-spacing:-.045em} h2,h3 {letter-spacing:-.025em}
[data-testid="stMetric"] {border:1px solid #294058;border-radius:10px;padding:12px}
</style>""",
    unsafe_allow_html=True,
)
st.caption("APEX / ENGINEERING LABORATORY                                      LOCAL · V0.2 WORK")
st.title("Predict. Run. Understand.")
st.write("Explore the actual APEX bicycle model and LQR/PI baseline. Every run keeps its evidence.")
st.caption(
    "SYNTHETIC parameters · perfect state · unsaturated linear tires · no physical safety claim"
)

with st.sidebar:
    st.header("APEX Workbench")
    page = st.radio("Workspace", ["Experiment", "Compare runs", "Capabilities"])
    if page == "Experiment":
        adapter = st.selectbox("Experiment", list(ADAPTERS), format_func=ADAPTERS.get)
        st.caption(
            {
                "dynamic_demo": "Existing Task004 demo",
                "lqr_baseline": "Existing Task005 run_case",
                "dynamic_lab": "Prescribed open-loop canonical vehicle dynamics",
            }[adapter]
        )
        with st.form("configuration"):
            values = {}
            if adapter == "dynamic_lab":
                from tools.apex_workbench.lab_configuration import CASES, request_for, resolve

                values = request_for(st.selectbox("Synthetic laboratory case", CASES))
                preview = resolve(values)
                st.caption("0.500 s · 5 ms plant/input ticks · steering step at 0.100 s · a_cmd=0")
                st.json(
                    {
                        "vehicle_parameters_SI": preview["effective_parameters"],
                        "initial_state_SI": preview["initial_state"],
                        "schedule": preview["schedule"],
                    },
                    expanded=False,
                )
                st.caption(
                    "Finite synthetic cases. Numerical qualification has not been performed."
                )
            else:
                values["duration"] = st.number_input(
                    "Duration [s]",
                    value=DEFAULTS[adapter]["duration"],
                    step=0.01,
                    help="UI resource safeguard: 0.01–20 s. LQR: multiple of 0.005 s.",
                )
            if adapter == "dynamic_demo":
                values["dt"] = st.number_input(
                    "Integration timestep [s]",
                    value=0.005,
                    step=0.001,
                    format="%.4f",
                    help="UI numerical/resource safeguard: 0.001–0.01 s; no accuracy guarantee.",
                )
                st.caption("Fixed 2 m/s initial vx; original steering/acceleration schedule.")
            elif adapter == "lqr_baseline":
                values["track"] = st.selectbox("Synthetic track", ["circle", "oval"])
                values["speed"] = st.number_input(
                    "Initial / reference speed [m/s]",
                    value=2.0,
                    step=0.1,
                    help="Task005 design/reference domain: 1–3 m/s.",
                )
                values["ey"] = st.number_input(
                    "Initial lateral error [m]",
                    value=0.0,
                    step=0.01,
                    help="UI safeguard: ±0.1 m, based on existing disturbance examples.",
                )
                values["epsi"] = st.number_input(
                    "Initial heading error [rad]",
                    value=0.0,
                    step=0.01,
                    help="UI safeguard: ±0.05 rad, based on existing disturbance examples.",
                )
                st.caption("Fixed plant 200 Hz / controller 100 Hz. Duration-only stop.")
            prediction = st.text_area(
                "My prediction", max_chars=8000, placeholder="What do I expect to happen, and why?"
            )
            submitted = st.form_submit_button("Run experiment", type="primary")
        if submitted:
            try:
                validate(adapter, values)
                directory = jobs.start_run(adapter, values, prediction)
                st.session_state["selected_run"] = directory.name
                st.success("Run launched; evidence directory reserved.")
            except (ValueError, RuntimeError, OSError) as error:
                st.error(str(error))
    st.divider()
    st.caption(
        "Original adapters keep their fixed vehicle and controller. The laboratory offers five "
        "finite synthetic cases; tire selection and latency modes stay fixed."
    )

RUNS.mkdir(parents=True, exist_ok=True)
retained, incomplete = storage.list_runs(RUNS)
for problem in incomplete:
    st.warning("Incomplete record preserved and excluded from selection: " + problem)
by_id = {p.name: p for p in retained}

if page == "Capabilities":
    st.subheader("Supported inputs and scientific boundaries")
    st.markdown((Path(__file__).parent / "CAPABILITY_MATRIX.md").read_text())
    st.stop()

if page == "Compare runs":
    st.subheader("Compare retained experiments")
    selected = st.multiselect("Choose two runs", list(by_id), max_selections=2)
    if len(selected) == 2:
        decision = comparison.eligibility(*(by_id[key] for key in selected))
        label = decision["classification"].upper()
        if label == "CONTROLLED":
            st.success("Controlled comparison: " + decision["reason"])
        elif label == "CONTROLLED_CANDIDATE":
            st.info("Controlled candidate: " + decision["reason"])
            st.caption("Numerical qualification unavailable · no physical validation")
            st.json(
                {
                    key: decision[key]
                    for key in (
                        "declared_treatment",
                        "numerical_qualification",
                        "excitation",
                        "sampled_model_windows",
                    )
                },
                expanded=False,
            )
        elif label == "ILLUSTRATIVE":
            st.warning("Illustrative comparison only: " + decision["reason"])
        else:
            st.error("Invalid comparison — telemetry quarantined: " + decision["reason"])
        st.json(
            {"varied_inputs": decision["varied_inputs"], "differences": decision["differences"]}
        )
        if label != "INVALID":
            st.caption("Raw elapsed simulation time; no interpolation or acceptance claim.")
            pairs = [(key, by_id[key]) for key in selected]
            try:
                channels = [
                    (["vx"], "vx [m/s]"),
                    (["e_y"], "e_y [m]"),
                    (["delta"], "Steering [rad]"),
                ]
                if "numerical_qualification" in decision:
                    channels[1:1] = [
                        (["r"], "Yaw rate [rad/s]"),
                        (["vy"], "Lateral velocity [m/s]"),
                    ]
                for columns, unit in channels:
                    st.plotly_chart(plots.series(pairs, columns, unit), width="stretch")
                if label == "CONTROLLED_CANDIDATE":
                    for columns, unit in [
                        (["alpha_f", "alpha_r"], "Slip [rad]"),
                        (["fyf", "fyr"], "Lateral axle forces [N]"),
                    ]:
                        st.plotly_chart(
                            plots.series(pairs, columns, unit, source="diagnostics.csv"),
                            width="stretch",
                        )
            except storage.IntegrityError as error:
                st.error("Telemetry quarantined: " + str(error))
    st.stop()

if not retained:
    st.info("Choose an experiment, write a prediction, then run it from the sidebar.")
    st.subheader("A real experiment, with its limits visible")
    st.write(
        "The dynamic demo explores open-loop response; LQR/PI tracks a synthetic centerline. "
        "Plots appear only after the original experiment produces real output files."
    )
    st.stop()

selected = st.selectbox("Retained run", list(by_id), key="selected_run")
directory = by_id[selected]


@st.fragment(run_every=1)
def progress():
    status = jobs.status_for(directory)
    state = status["state"]
    st.metric("Execution", state.upper())
    st.caption(
        "Scientific outcome: "
        + status.get("scientific_outcome", state)
        + " · Evidence: "
        + status.get("evidence_state", "legacy — hashes checked on use")
    )
    if status.get("error"):
        st.error(status["error"])
    if state in jobs.ACTIVE:
        st.caption("Fresh worker running. Closing this page does not cancel the bounded run.")
        if st.button("Cancel run"):
            jobs.cancel_run(directory)
            st.info("Cancellation requested; partial files will be retained.")
    elif st.session_state.get("last_terminal") != selected:
        st.session_state["last_terminal"] = selected
        st.rerun()


progress()
status = jobs.status_for(directory)
try:
    request = storage.read_request(directory, verified=status["state"] not in jobs.ACTIVE)
    if status["state"] not in jobs.ACTIVE:
        storage.check_required_artifacts(directory, request, status)
except (storage.IntegrityError, OSError, ValueError) as error:
    st.error("Retained record quarantined; files preserved: " + str(error))
    st.code(str(directory), language=None)
    st.json(status, expanded=False)
    st.stop()
st.caption(f"Viewing {ADAPTERS[request['adapter']]} · effective configuration below")
st.json(request["effective"], expanded=False)
expected = storage.required_artifacts(request, status)
if request["adapter"] == "dynamic_lab" and status["state"] not in jobs.ACTIVE:
    from tools.apex_workbench.lab_evidence import read_record

    try:
        if "experiment/summary.json" in storage.artifact_manifest(directory):
            lab = read_record(directory)
            st.caption(
                "Configuration: admissible · Numerics: "
                + lab["summary"]["numerical_qualification"]
                + " · Evidence: "
                + status.get("evidence_state", "unknown")
            )
            st.json(
                {
                    "sampled_model_window": lab["summary"]["sampled_model_window"],
                    "excitation": lab["summary"]["excitation"],
                    "comparison": "requires a permitted baseline/treatment pair",
                    "limitations": lab["summary"]["limitations"],
                },
                expanded=False,
            )
            with st.expander("Resolved laboratory metadata and provisional criteria"):
                st.json(lab["resolved"])
    except storage.IntegrityError as error:
        st.error("Retained laboratory evidence quarantined: " + str(error))
        st.stop()
trajectory_tab, states_tab, evidence_tab, notes_tab = st.tabs(
    ["Trajectory", "States & controls", "Evidence & logs", "Learning notes"]
)
with trajectory_tab:
    if status["state"] in jobs.ACTIVE:
        st.info("Waiting for the experiment to finish. Status updates automatically.")
    else:
        try:
            figure = plots.trajectory(directory)
            if figure.data:
                st.plotly_chart(figure, width="stretch")
            else:
                st.info("Trajectory unavailable: this run produced no coordinate export.")
        except storage.IntegrityError as error:
            st.error("Telemetry quarantined: " + str(error))
        st.caption(
            "XY is derived from retained Frenet states using apex.coordinates.frenet. "
            "Track boundaries describe a CG corridor; no swept-body safety guarantee."
        )
    if status["state"] not in jobs.ACTIVE:
        try:
            summary = storage.artifact_json(
                directory, "worker_result.json", optional="worker_result.json" not in expected
            )
            if summary is not None:
                st.json(summary, expanded=False)
            else:
                st.info("Summary unavailable: not produced by this execution.")
        except storage.IntegrityError as error:
            st.error("Summary quarantined: " + str(error))
    st.caption(
        "COMPLETED means the entry point exited successfully. "
        "Scientific acceptance remains separate."
    )
with states_tab:
    if status["state"] in jobs.ACTIVE:
        st.info("Telemetry is displayed after execution to avoid reading partially written CSVs.")
    else:
        try:
            data = plots.read_frame(directory, "states.csv")
        except storage.IntegrityError as error:
            st.error("Telemetry quarantined: " + str(error))
            data = None
        if data is None:
            pass
        elif data.empty:
            st.info("State telemetry unavailable for this run.")
        else:
            pairs = [("Actual", directory)]
            for columns, unit, reference in [
                (["vx"], "Longitudinal speed [m/s]", "reference_speed"),
                (["vy"], "Lateral velocity [m/s]", "vy_ref"),
                (["r"], "Yaw rate [rad/s]", "r_ref"),
                (["e_y"], "Lateral error [m]", None),
                (["e_psi"], "Heading error [rad]", None),
                (["delta"], "Steering [rad]", None),
                (["a_cmd"], "Commanded Fx/m [m/s²]", None),
            ]:
                try:
                    st.plotly_chart(
                        plots.series(pairs, columns, unit, reference=reference), width="stretch"
                    )
                except storage.IntegrityError as error:
                    st.error("Telemetry quarantined: " + str(error))
            if "boundary_violation" in data:
                st.write("Sampled CG boundary violations:", int(data.boundary_violation.sum()))
            else:
                st.caption("Boundary violation metric unavailable in the original dynamic demo.")
            if request["adapter"] == "dynamic_lab":
                for columns, unit in [
                    (["alpha_f", "alpha_r"], "Axle slip angles [rad]"),
                    (["fyf", "fyr"], "Lateral axle forces [N]"),
                    (["fzf", "fzr"], "Normal axle loads [N]"),
                    (["cf", "cr", "cf_eff", "cr_eff"], "Axle stiffness [N/rad]"),
                    (
                        ["front_lateral_utilization", "rear_lateral_utilization"],
                        "Lateral utilization [diagnostic ratio]",
                    ),
                    (["frenet_denominator"], "Frenet denominator [dimensionless]"),
                ]:
                    try:
                        st.plotly_chart(
                            plots.series(pairs, columns, unit, source="diagnostics.csv"),
                            width="stretch",
                        )
                    except storage.IntegrityError as error:
                        st.error("Telemetry quarantined: " + str(error))
                st.caption(
                    "Canonical diagnostics recomputed at retained samples. Provisional "
                    "sampled filters do not establish physical validity; "
                    "terminal input is informational."
                )
    st.info(
        "Solver status/time, injected/measured latency and deadline metrics: unavailable in these "
        "adapters. LQR is not an optimizer; host execution time is shown only in evidence."
    )
with evidence_tab:
    st.code(str(directory), language=None)
    st.json(request, expanded=False)
    st.json(status, expanded=False)
    for name in ["numerical_environment.json", "artifacts.json"]:
        with st.expander(name):
            try:
                if status["state"] in jobs.ACTIVE:
                    st.caption("Evidence finalization pending")
                else:
                    data = (
                        storage.artifact_manifest(directory)
                        if name == "artifacts.json"
                        else storage.artifact_json(directory, name, optional=name not in expected)
                    )
                    if data is None:
                        st.info("Evidence unavailable: not produced by this execution.")
                    else:
                        st.json(data)
            except (storage.IntegrityError, OSError, ValueError) as error:
                st.error("Evidence unavailable/unverified: " + str(error))
    for name in ["stdout.log", "stderr.log", "supervisor.log"]:
        with st.expander(name):
            path = directory / name
            try:
                if status["state"] in jobs.ACTIVE or name == "supervisor.log":
                    st.caption("Live/unverified diagnostic log; excluded from scientific claims.")
                    contents = path.read_bytes() if path.exists() else None
                else:
                    contents = storage.artifact_bytes(directory, name, optional=True)
                st.code(
                    contents.decode(errors="replace")[-100_000:]
                    if contents is not None
                    else "No log produced yet",
                    language=None,
                )
            except (storage.IntegrityError, OSError) as error:
                st.error("Log unavailable/unverified: " + str(error))
            st.caption("Last 100,000 characters displayed; full log retained on disk.")
    if status["state"] not in jobs.ACTIVE:
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
            for path in directory.rglob("*"):
                if path.is_file():
                    zipped.write(path, path.relative_to(directory))
        st.download_button(
            "Download retained files (.zip, may include unverified evidence)",
            archive.getvalue(),
            selected + ".zip",
            "application/zip",
        )
with notes_tab:
    st.write("**My prediction**")
    st.write(request["prediction"] or "No prediction recorded.")
    latest, note_problems = storage.latest_note(directory)
    for problem in note_problems:
        st.warning(problem)
    with st.form("notes_" + selected):
        observation = st.text_area(
            "My observation", value=latest.get("observation", ""), max_chars=8000
        )
        explanation = st.text_area(
            "My explanation", value=latest.get("explanation", ""), max_chars=8000
        )
        if st.form_submit_button("Save learning notes"):
            jobs.save_notes(directory, observation, explanation)
            st.success("Saved a new note version. Earlier notes and prediction retained.")
    st.caption("Explain the result in your own words. No generated answer is supplied.")
