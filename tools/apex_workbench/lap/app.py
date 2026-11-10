"""APEX engineering workflow; execution and scientific readers remain independent."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.apex_workbench.lap import ui_data, ui_theme, ui_views

st.set_page_config(
    page_title="APEX · Engineering Workbench",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="collapsed",
)
ui_theme.install()
ui_theme.header()
if "ui_next" in st.session_state:
    st.session_state["ui_page"] = st.session_state.pop("ui_next")
page = st.radio(
    "Engineering workflow",
    ui_views.PAGES,
    index=2 if ui_data.recordings() else 0,
    horizontal=True,
    label_visibility="collapsed",
    key="ui_page",
)
{
    "Configure": ui_views.configure,
    "Run": ui_views.run,
    "Replay": ui_views.replay,
    "Analyze": ui_views.analyze,
    "Compare": ui_views.compare,
}[page]()
