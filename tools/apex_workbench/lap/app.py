"""Same Streamlit/Plotly workspace conventions, with unchanged V1 panels for Transient."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.apex_workbench import nmpc_scratch_panels as short
from tools.apex_workbench import run_catalog
from tools.apex_workbench.lap import config, panels

st.set_page_config(page_title="APEX Workbench V2", page_icon="🏎", layout="wide")
st.title("APEX Workbench V2")
st.caption("Synthetic research mode · Not physically qualified")
if "next_view" in st.session_state:
    st.session_state["lap_page"] = st.session_state.pop("next_view")
pending = st.session_state.pop("pending_directory", None)
if pending:
    st.session_state["lap_selected"] = pending
page = st.sidebar.radio(
    "Workspace", ["Home", "Run", "Inspect", "Compare", "Analyze"], key="lap_page"
)
if page == "Home":
    st.write(
        "Transient: accepted2s NMPC Lab V1. Extended:5/10/20s. Full Lap: one complete "
        "finish-line circuit after the partial launch crossing, maximum80s."
    )
    if st.button("Configure an experiment"):
        st.session_state["next_view"] = "Run"
        st.rerun()
    st.caption(
        "Same frozen synthetic GP gamma2 / N8 NMPC / TVLQR / controlled availability. "
        "No new physics, controller profile or real-time claim."
    )
elif page == "Run":
    mode = st.selectbox("Experiment mode", ["Transient (accepted V1)", "Extended", "Full Lap"])
    if mode == "Transient (accepted V1)":
        short.run_panel()
    else:
        panels.run_panel(mode)
elif page == "Inspect":
    choices = panels.records() + short.records()
    if choices:
        preferred = st.session_state.get("lap_selected")
        selected = st.selectbox(
            "Run",
            choices,
            index=next((i for i, p in enumerate(choices) if str(p) == preferred), 0),
            format_func=lambda p: ("V2 · " if p.parent == config.RUNS else "V1 · ") + p.name,
        )
        if selected.parent == config.RUNS:
            panels.inspect(selected)
        else:
            original = next(
                r for r in run_catalog.discover(include_nmpc=True).runs if r.directory == selected
            )
            short.inspect(original)
    else:
        st.info("No recorded experiments.")
elif page == "Compare":
    if (
        st.selectbox("Comparison family", ["V2 racing experiments", "V1 short response"])
        == "V1 short response"
    ):
        short.compare_panel()
    else:
        panels.compare()
else:
    st.subheader("Accepted short-response Control Analysis")
    short.analysis_panel()
