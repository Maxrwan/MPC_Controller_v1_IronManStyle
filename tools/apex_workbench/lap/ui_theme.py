"""One token source for Streamlit chrome, native replay and Plotly."""

import html
import re
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).with_name("ui_web")


def palette():
    return dict(re.findall(r"--apex-([a-z]+):\s*(#[0-9a-f]+)", (ASSETS / "tokens.css").read_text()))


def install():
    css = (ASSETS / "tokens.css").read_text() + (ASSETS / "host.css").read_text()
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)


def header():
    st.markdown(
        '<div class="apex-header"><div class="apex-brand">APEX'
        "<span>ENGINEERING WORKBENCH <b>V2</b></span></div>"
        '<div class="apex-header-meta"><span class="apex-badge">NMPC + TVLQR</span>'
        "<span>SYNTHETIC · UNQUALIFIED</span></div></div>",
        unsafe_allow_html=True,
    )


def heading(eyebrow, title, description=""):
    st.markdown(
        '<div class="apex-page-heading"><div class="apex-eyebrow">'
        + html.escape(eyebrow)
        + "</div><h1>"
        + html.escape(title)
        + "</h1><p>"
        + html.escape(description)
        + "</p></div>",
        unsafe_allow_html=True,
    )


def cards(items):
    st.markdown(
        '<div class="apex-cards">'
        + "".join(
            '<div class="apex-card"><small>'
            + html.escape(label)
            + "</small><strong>"
            + html.escape(str(value))
            + "</strong><span>"
            + html.escape(note)
            + "</span></div>"
            for label, value, note in items
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def chart(figure):
    colors = palette()
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor=colors["surface"],
        plot_bgcolor=colors["surface"],
        font={
            "family": "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
            "color": colors["muted"],
            "size": 12,
        },
        margin={"l": 20, "r": 18, "t": 32, "b": 30},
        height=300,
        legend={"orientation": "h", "y": 1.13, "x": 0},
        xaxis={"gridcolor": colors["line"], "zerolinecolor": colors["line"]},
        yaxis={"gridcolor": colors["line"], "zerolinecolor": colors["line"]},
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False, "displaylogo": False})
