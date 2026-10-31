"""Literal historical C0 inspection using the existing Streamlit/Plotly/export surface."""

import html
import json

import plotly.graph_objects as go
import streamlit as st

from tools.apex_workbench import c0_archive as archive

LIMITS = (
    "G1 OPEN. Capture source, configuration, environment and producer schema are unknown. "
    "No authenticated controller execution, optimizer convergence, causal sequence, successful "
    "recovery, physical measurement, Safety or numerical qualification follows. World XY, "
    "terminal state and missing events are unavailable. No cross-profile comparison."
)
ORDERING = (
    "Literal chronology is a visual index of separate collections in their original array order. "
    "Cross-stream ties/order remain unknown. Null, absent, zero and empty are distinct; "
    "no interpolation, held-input inference or elapsed-response metrics."
)


def figure(data, collection, channel):
    """Recorded markers only; authoritative hover tokens and pointers are never rounded."""
    rows = data[collection]
    if collection not in ("states", "controls", "reserves") or not rows:
        raise archive.ArchiveError("Unsupported descriptive plot collection")
    if channel not in rows[0] or not isinstance(rows[0][channel], archive.Number):
        raise archive.ArchiveError("Unsupported descriptive numeric field")
    result = go.Figure(
        go.Scattergl(
            x=[float(row["time"].token) for row in rows],
            y=[float(row[channel].token) for row in rows],
            mode="markers",
            name=channel,
            customdata=[
                [
                    f"/{collection}/{i}/time",
                    row["time"].token,
                    f"/{collection}/{i}/{channel}",
                    row[channel].token,
                    archive.SHA256,
                ]
                for i, row in enumerate(rows)
            ],
            hovertemplate=(
                "%{customdata[0]} = %{customdata[1]}<br>"
                "%{customdata[2]} = %{customdata[3]}<br>"
                "original SHA-256: %{customdata[4]}<extra></extra>"
            ),
        )
    )
    result.update_layout(
        title="DESCRIPTIVE ONLY · SOURCE UNVERIFIED · " + collection,
        xaxis_title="time [unit/frame not declared in artifact]",
        yaxis_title=channel + " [unit/frame not declared in artifact]",
    )
    return result


def provenance():
    return {
        "classification": archive.PROFILE,
        "presentation_status": "descriptive_record_valid_source_unverified",
        "G1": "OPEN",
        "original_path": archive.RELATIVE,
        "bytes": archive.SIZE,
        "sha256": archive.SHA256,
        "contemporary_inspection_contract": archive.IDENTIFIER,
        "contemporary_contract_revision": "5bf6cce22816bc8fd5a7d7bf84cefef87c69e358",
        "contemporary_contract_review": "79c450f28a2715e3a5284c8815b49e0b07bd9123",
        "contemporary_authority_sha256": archive.ANCHORS,
        "historical_capture_source_configuration_environment": "unknown",
        "historical_producer_schema": "not embedded; unknown",
        "execution_identity": "unavailable; this inspection is not a new execution",
        "units_frames": "not declared; optional reference interpretation is unverified for capture",
        "ordering": ORDERING,
        "limitations": LIMITS,
    }


def report(snapshot, collection, channel):
    """Self-contained read-only HTML from operation-local bytes, checked around serialization."""
    snapshot.current()
    data = snapshot.data()
    plot = figure(data, collection, channel)
    meta = {**provenance(), "selected_collection": collection, "selected_channel": channel}
    content = (
        "<!doctype html><html><head><meta charset='utf-8'><title>APEX C0 descriptive inspection"
        "</title></head><body><h1>Historical C0 literal record</h1><p>"
        + html.escape(archive.BANNER)
        + "</p><p>"
        + html.escape(LIMITS)
        + "</p><p>"
        + html.escape(ORDERING)
        + "</p>"
        + plot.to_html(full_html=False, include_plotlyjs=True)
        + "<h2>Contemporary inspection identity and limits</h2><pre>"
        + html.escape(json.dumps(meta, indent=2, ensure_ascii=False))
        + "</pre><h2>Literal chronology: pointers and tokens</h2><pre>"
        + html.escape(json.dumps(archive.chronology(data), indent=2, ensure_ascii=False))
        + "</pre><h2>Present-null and absent fields</h2><pre>"
        + html.escape(json.dumps(archive.missingness(data), indent=2, ensure_ascii=False))
        + "</pre><h2>Original JSON bytes decoded as UTF-8 (not reserialized)</h2><pre>"
        + html.escape(snapshot.raw.decode("utf-8"))
        + "</pre></body></html>"
    ).encode("utf-8")
    snapshot.current()
    return content


def _inspect():
    snapshot = archive.read()
    data = snapshot.data()
    collection = st.selectbox("C0 recorded signal collection", ["states", "controls", "reserves"])
    channels = [
        key for key, value in data[collection][0].items() if isinstance(value, archive.Number)
    ]
    channel = st.selectbox("C0 recorded field", channels)
    plot = figure(data, collection, channel)
    snapshot.current()
    st.warning(archive.BANNER)
    st.caption("descriptive_record_valid_source_unverified · G1 OPEN · read-only archive")
    st.info(LIMITS)
    st.caption("Selected V0.2 qualification does not apply; no worker or controller path.")
    st.json(provenance(), expanded=False)
    st.caption(
        "Markers show only recorded numbers; exact tokens/pointers/hash are in hover and tables."
    )
    st.plotly_chart(plot, width="stretch")
    st.caption(ORDERING)
    with st.expander(
        "Literal chronology: readiness, misses, late discards, urgent demand and fallback"
    ):
        st.dataframe(archive.chronology(data), hide_index=True, width="stretch")
    with st.expander("Present-null and absent fields"):
        st.dataframe(archive.missingness(data), hide_index=True, width="stretch")
    with st.expander("Original rows, pointers and numerical tokens"):
        collections = [key for key, value in data.items() if isinstance(value, list)]
        selected = st.selectbox("C0 raw collection", collections)
        if data[selected]:
            index = st.number_input("C0 original array index", 0, len(data[selected]) - 1, 0, 1)
            st.dataframe(archive.fields(data, selected, index), hide_index=True, width="stretch")
        else:
            st.write("No rows recorded in this collection; no real-system absence is established.")
    with st.expander("Reference-only explanations — unverified for the original capture"):
        st.write(
            "Later reference source describes a test StraightPlanner and fixture-imposed timing. "
            "The recorded test_success string is not an authenticated IPOPT/NMPC result. "
            "Reference time/application_time/physical_latency interpretations, SI units and "
            "[vx,vy,r,e_psi,s_abs,e_y] ordering are unverified for capture. "
            "Reference a_cmd = Fx/m differs from dvx/dt. Reference fallback self-substitution "
            "can zero error fields; recorded zeros do not demonstrate perfect tracking. "
            "valid_domain=true and failure=null remain recorded fields only."
        )
        st.caption(
            "Reference-only revision: 44e0471680bb22ea1ee790173d1f2481a905f386; "
            "not capture identity."
        )
    with st.expander("Original JSON — literal bytes"):
        st.code(snapshot.raw.decode("utf-8"), language="json")
    if st.button("Prepare C0 descriptive HTML inspection"):
        content = report(snapshot, collection, channel)
        st.download_button(
            "Download descriptive-only C0 HTML",
            content,
            file_name="APEX_C0_original155_descriptive_only.html",
            mime="text/html",
            on_click="ignore",
        )
    snapshot.current()


def inspect():
    # Same scoped publication/quarantine pattern as the existing GP inspector.
    presentation = st.empty()
    try:
        with presentation.container():
            _inspect()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        presentation.empty()
        presentation.error(
            "C0 descriptive_record_quarantined — evidence unavailable: " + str(error)
        )
