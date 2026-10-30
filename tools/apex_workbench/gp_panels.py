"""Presentation/export of the single reviewed historical GP profile, without execution."""

import hashlib
import html
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from tools.apex_workbench import gp_archive as archive

GROUPS = {
    "Vehicle and reference": ("vx", "vy", "r"),
    "Tracking": ("e_y", "e_psi", "error_vx", "error_vy", "error_r"),
    "Applied/requested controls": ("delta", "a_cmd"),
    "Recorded diagnostics": (
        "front_utilization",
        "rear_utilization",
        "packet_age",
        "reserve",
        "clearance",
    ),
    "Planner and solver events": (),
}


def figures(snapshot, group, channel, sector=None):
    """Only recorded coordinates/samples; sector visits use unconnected markers."""
    states = archive.sector_frame(snapshot, "states", sector)
    planning = archive.sector_frame(snapshot, "planning", sector)
    track = go.Figure()
    if sector:
        context = snapshot.frames["planning"]
        track.add_trace(
            go.Scattergl(
                x=context["x_ref_m"],
                y=context["y_ref_m"],
                mode="lines",
                name="Whole original GP Planning context (unfiltered)",
                line={"color": "lightgrey"},
                connectgaps=False,
            )
        )
    for frame, x, y, label in (
        (planning, "x_ref_m", "y_ref_m", "Original offline Planning reference"),
        (states, "x_world", "y_world", "Stored producer-reconstructed vehicle XY"),
    ):
        track.add_trace(
            go.Scattergl(
                x=frame[x],
                y=frame[y],
                mode="markers" if sector else "lines",
                name=label,
                marker={"size": 3},
                connectgaps=False,
            )
        )
    track.update_layout(
        title="Original GP geometry · selected native samples",
        xaxis_title="World X [m]",
        yaxis_title="World Y [m]",
    )
    track.update_yaxes(scaleanchor="x", scaleratio=1)
    result = [track]
    if group == "Planner and solver events":
        return result
    signal = go.Figure()
    if group == "Applied/requested controls":
        frame = snapshot.frames["controls"]
        for clock, column, label in (
            ("application_time", channel, "Applied at native application_time"),
            ("time", "requested_" + channel, "Requested at native computation time"),
        ):
            signal.add_trace(
                go.Scattergl(
                    x=frame[clock],
                    y=frame[column],
                    mode="markers",
                    name=label,
                    marker={"size": 3},
                    connectgaps=False,
                )
            )
        title = "Full-run controls · independent computation/application clocks"
    else:
        for column in (channel, "reference_" + channel):
            if column in states:
                signal.add_trace(
                    go.Scattergl(
                        x=states["time"],
                        y=states[column],
                        mode="markers" if sector else "lines",
                        name=column,
                        marker={"size": 3},
                        connectgaps=False,
                    )
                )
        title = "Native state-row history · stored reference sampling is producer-reconstructed"
    signal.update_layout(
        title=title,
        xaxis_title="Simulated physical time [s]",
        yaxis_title=f"{channel} [{archive.unit(channel)}]",
    )
    result.append(signal)
    return result


def provenance(snapshot, sector, group, channel):
    manifest = snapshot.manifest
    return {
        "kind": "derived_read_only_inspection_not_new_execution",
        "profile": archive.PROFILE,
        "original_path": str(snapshot.directory),
        "original_run_id": manifest["run_id"],
        "manifest_sha256": archive.MANIFEST_SHA256,
        "historical_provenance": manifest["provenance"],
        "original_termination": manifest["termination"],
        "original_coverage": manifest["coverage"],
        "historical_export_review_status": manifest["review_status"],
        "field_provenance": manifest["field_provenance"],
        "clock": manifest["clock"],
        "ordering": manifest["ordering"],
        "request_coverage": manifest["request_coverage"],
        "view": {
            "sector": sector,
            "group": group,
            "channel": channel,
            "states_export_rows": archive.sector_frame(snapshot, "states", sector)[
                "export_row"
            ].tolist(),
            "other_streams": "full-run; no native sector progress",
        },
        "original_inventory": snapshot.inventory,
        "presentation_source_sha256": {
            str(p.relative_to(archive.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(archive.__file__), Path(__file__))
        },
        "limits": "Synthetic historical P acceptance only; no V0.2 qualification, physical "
        "validation, hard real-time, guaranteed recovery or standstill braking. "
        "No new interpolation, events, metrics or execution. G/C70 unsupported.",
    }


def report(snapshot, plots, metadata):
    """Serialize the currently verified view, then recheck its source before publication."""
    fragments = [
        "<!doctype html><html><head><meta charset='utf-8'><title>APEX P inspection</title>"
        "</head><body><h1>Historical P archive inspection</h1>",
        "<p>Derived read-only view; original execution identity retained. "
        "Synthetic evidence; no new qualification or physical validation.</p>",
    ]
    for index, figure in enumerate(plots):
        fragments.append(figure.to_html(full_html=False, include_plotlyjs=index == 0))
    fragments.extend(
        (
            "<h2>Exact source and view provenance</h2><pre>",
            html.escape(json.dumps(metadata, indent=2)),
            "</pre></body></html>",
        )
    )
    content = "".join(fragments).encode()
    snapshot.current()
    return content


def _inspect(run):
    st.caption("Read-only historical P archive · no worker, controller or Safety command path")
    st.caption("V0.2 qualification selection does not apply to this producer/profile.")
    group = st.selectbox("GP signal group", list(GROUPS))
    channel = st.selectbox("GP signal", GROUPS[group]) if GROUPS[group] else None
    tables = ["states", "planning", "controls"]
    if group == "Planner and solver events":
        tables.extend(("events", "cycles"))
    snapshot = archive.read(run.directory, tables)
    sector = st.selectbox(
        "GP sector",
        [None, *archive.sector_names(snapshot)],
        format_func=lambda x: "Full run" if x is None else x,
    )
    built = figures(snapshot, group, channel, sector)
    metadata = provenance(snapshot, sector, group, channel)
    # Construct everything before emitting any scientific plots or accepted labels.
    snapshot.current()
    st.success("Verified retained P/VIS-1R bytes · historical bounded synthetic acceptance")
    st.write("Architecture A · TVLQR · N8/0.1 s · gamma2 · progress0")
    st.caption(
        "Evaluation conditions: planner delay 35/55/45/25 ms; codriver delay 5 ms. "
        "Historical worker/export source " + archive.REVISION
    )
    st.caption("Original export review flag: " + snapshot.manifest["review_status"])
    st.caption(
        "Completed to two crossings: initial partial plus one complete lap; "
        "native endpoint 62.235 s of an intended maximum 80 s."
    )
    st.info(
        "Synthetic/unmeasured vehicle. Stored XY/reference sampling are producer "
        "reconstructions. This case contains no fallback/failure episode; failure-case "
        "inspection remains incomplete. G and incomplete C70 archives are unsupported."
    )
    if sector:
        st.caption(
            "Sector selects native state/Planning progress samples only; separate visits "
            "use markers. Controls, cycles and events remain full-run. No crossing "
            "interpolation, independent sector track or new score."
        )
    st.caption(
        "Dynamic a_cmd = Fx/m [m/s²], not body dvx/dt. Controls use their own recorded "
        "computation/application clocks. No inferred hold or resampling."
    )
    for figure in built:
        st.plotly_chart(figure, width="stretch")
    if group == "Planner and solver events":
        events = snapshot.frames["events"]
        kind = st.selectbox("Recorded event kind", list(events["event_kind"].drop_duplicates()))
        selected = events.loc[events["event_kind"] == kind]
        first = st.number_input(
            "First matching event row (zero-based)",
            min_value=0,
            max_value=max(0, len(selected) - 1),
            value=0,
            step=1,
        )
        st.caption(
            "Full-run original export order; at most100 matching rows per page. "
            "Same-time cross-stream ties remain unspecified. Solver status is the "
            "preparation_ready payload.status; cycle status is packet availability."
        )
        st.dataframe(selected.iloc[first : first + 100], hide_index=True)
        metadata["view"]["event_page"] = {
            "kind": kind,
            "first_matching_row": first,
            "original_export_rows": selected.iloc[first : first + 100]["export_row"].tolist(),
            "recorded_payloads": selected.iloc[first : first + 100]["payload"].tolist(),
        }
        with st.expander("Original full-run planner/tracker cycle rows"):
            st.dataframe(snapshot.frames["cycles"], hide_index=True)
    if st.toggle("Exact native samples, units and provenance"):
        st.json(
            {
                "view": metadata["view"],
                "state_units": snapshot.manifest["state_units"],
                "control_units": snapshot.manifest["control_units"],
                "provenance": snapshot.manifest["provenance"],
                "field_provenance": snapshot.manifest["field_provenance"],
                "missingness": snapshot.manifest["null_policy"],
                "coverage": snapshot.manifest["coverage"],
                "ordering": snapshot.manifest["ordering"],
            },
            expanded=False,
        )
        st.dataframe(archive.sector_frame(snapshot, "states", sector), hide_index=True)
        st.caption(
            "Controls below are full-run; their time and application_time both have SI seconds."
        )
        st.dataframe(snapshot.frames["controls"], hide_index=True)
    if st.button("Prepare source-linked HTML inspection"):
        content = report(snapshot, built, metadata)
        st.download_button(
            "Download verified view HTML",
            content,
            file_name="APEX_P_controlled_A_inspection.html",
            mime="text/html",
            on_click="ignore",
        )
    # Catch replacement during late serialization too; clear the scoped presentation on error.
    snapshot.current()


def inspect(run):
    presentation = st.empty()
    try:
        with presentation.container():
            _inspect(run)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        presentation.empty()
        presentation.error("GP evidence quarantined/unavailable: " + str(error))
