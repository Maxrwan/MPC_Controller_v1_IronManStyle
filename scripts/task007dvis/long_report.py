"""Offline VIS-1L stop report, including retained traces with failed export finalization.

Never launches a worker or repairs an export. Existing runtime/report code is unchanged.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from task007dcx.analysis import cycle_rows

from apex.state import STATE_NAMES
from task007dvis.analysis import physical_difference, window_metrics
from task007dvis.export import csv_rows, flatten, hashes, write
from task007dvis.protocol import CASES
from task007dvis.validation import validate

PAIRS = (("controlled_A", "controlled_C70"), ("measured_A_1", "measured_C70_1"))
TOL = 1e-10  # Existing event comparison tolerance; no physical tolerance is relaxed.


def read(path):
    return json.loads(path.read_text())


def load_trace(folder):
    """Require native CSV identity against raw states and the recorded final RK4 endpoint."""
    raw, segments = (read(folder / name) for name in ("raw.json", "segments.json"))
    frame = pd.read_csv(folder / "scientific/states.csv", float_precision="round_trip")
    keys = [*STATE_NAMES, "delta", "a_cmd"]
    assert np.isfinite(frame[["time", *keys]].to_numpy()).all()
    assert (frame.time.diff().dropna() >= 0).all()
    assert (frame.sample_provenance == "native").all()
    assert len(frame) in (len(raw["states"]), len(raw["states"]) + 1)
    assert np.array_equal(
        frame.iloc[: len(raw["states"])][["time", *keys]].to_numpy(),
        [[s[k] for k in ["time", *keys]] for s in raw["states"]],
    )
    assert frame.time.iloc[-1] == segments[-1]["end"] == raw["end_time"]
    assert frame.iloc[-1][list(STATE_NAMES)].tolist() == segments[-1]["state_after"]
    assert abs(sum(s["dt"] for s in segments) - raw["end_time"]) < TOL
    for a, b in zip(segments, segments[1:]):
        assert abs(a["end"] - b["start"]) < TOL
        assert a["state_after"] == b["state_before"]
    # No regeneration of a missing manifest, summary, runtime observation or event stream.
    return frame, raw, segments


def common_windows(a, b, kind):
    """Bound both windows by shared observed coverage; retain actual native sample edges."""
    field = "time" if kind == "common_time" else "s_abs"
    lo = max(a[field].iloc[0], b[field].iloc[0])
    hi = min(a[field].iloc[-1], b[field].iloc[-1])
    if hi <= lo:
        raise ValueError("No common observed coverage")
    out = []
    for f in (a, b):
        subset = f[(f[field] >= lo) & (f[field] <= hi)]
        if len(subset) < 2:
            raise ValueError("Insufficient native samples in shared interval")
        out.append(
            dict(
                kind=kind,
                index=0,
                start=float(subset.time.iloc[0]),
                end=float(subset.time.iloc[-1]),
                start_s=float(subset.s_abs.iloc[0]),
                end_s=float(subset.s_abs.iloc[-1]),
                complete=False,
                status="common_observed_native_coverage",
                selection_field=field,
                shared_lower=float(lo),
                shared_upper=float(hi),
            )
        )
    return out


def miss_records(raw, rows):
    """Resolved deadline != observed completion; recovery requires an accepted handoff."""
    accepted = [h for h in raw["handoffs"] if h["accepted"]]
    packets = {p["plan_id"]: p for p in raw["packets"]}
    initial = dict(time=rows[0]["time"], plan_id=rows[0]["plan_id"])
    out = []
    for c in raw.get("fixed_handoffs", []):
        if c["status"] != "missed":
            continue
        t = c["miss_time"]
        assert c["t_accept"] is None
        assert not any(h["plan_id"] == c["plan_id"] for h in accepted)
        prior = [h for h in [initial, *accepted] if h["time"] <= t + TOL][-1]
        recovery = next((h for h in accepted if h["time"] > t + TOL), None)
        end = raw["end_time"] if recovery is None else recovery["time"]
        # Include the native terminal endpoint if the last raw reserve event precedes it.
        selected = [r for r in rows if t - TOL <= r["time"] <= end + TOL]
        assert selected
        out.append(
            dict(
                **c,
                old_plan_id=prior["plan_id"],
                old_authority_start=prior["time"],
                old_expiry=packets[prior["plan_id"]]["timestamps"][-1],
                recovery_time=None if recovery is None else recovery["time"],
                recovery_plan_id=None if recovery is None else recovery["plan_id"],
                recovery_censored=recovery is None,
                observed_until=end,
                minimum_native_reserve=min(r["reserve"] for r in selected),
                observed_without_replacement=end - t,
                completion_observed=c["t_ready"] is not None,
            )
        )
    return out


def build(source, output):
    output.mkdir(parents=True, exist_ok=False)
    data, report, windows, cycles, misses = {}, {}, [], [], []
    provenance = dict(scientific_source=read(source / "vis1l_preflight.json"), inputs={})
    for case in CASES:
        if case.phase == "parity":
            continue
        folder = source / case.name
        if not (folder / "raw.json").exists():
            report[case.name] = dict(status="NOT_EXECUTED_CAMPAIGN_STOP", complete_lap_seconds=None)
            continue
        frame, raw, segments = load_trace(folder)
        rows = frame.astype(object).where(pd.notna(frame), None).to_dict("records")
        analysis = read(folder / "analysis.json")
        summary = read(folder / "summary.json") if (folder / "summary.json").exists() else None
        exit_code = read(folder / "exit.json")["exit_code"]
        validation = validate(folder / "scientific") if summary else None
        cycle = cycle_rows(raw)
        assert len(cycle) == len(raw["plans"]) - 1
        report[case.name] = dict(
            status="COMPLETE_PIPELINE"
            if exit_code == 0 and not analysis["stop_gate"]
            else "SCIENTIFIC_STOP_AND_EXPORT_FAILURE",
            worker_exit=exit_code,
            stop_gate=analysis["stop_gate"],
            stop_reason=raw["stop_reason"],
            physical=analysis["physical"],
            coverage=analysis["coverage"],
            timing=analysis["timing"],
            native_run_metrics=analysis["windows"][0],
            complete_lap_seconds=next(
                (
                    w["duration"]
                    for w in analysis["windows"]
                    if w["kind"] == "lap" and w["complete"]
                ),
                None,
            ),
            runtime_thread_observations=None
            if summary is None
            else summary["observed_process_thread_counts"],
            runtime_forecast_matches=None
            if summary is None
            else summary["active_A_forecast_exact_matches"],
            runtime_summary_missing_reason=None
            if summary
            else "export_failed_before_summary_write",
            export_validation=validation,
            chronology_issues=analysis["chronology_issues"],
            physical_completion_censored=sum(c["t_ready"] is None for c in cycle),
            host_preparations=len(cycle),
            rk4_segments=len(segments),
            terminal_endpoint=rows[-1],
            native_csv_identity_verified=True,
        )
        windows.extend(dict(case=case.name, **flatten(w)) for w in analysis["windows"])
        cycles.extend(dict(case=case.name, **c) for c in cycle)
        misses.extend(dict(case=case.name, **c) for c in miss_records(raw, rows))
        provenance["inputs"][case.name] = hashes(p for p in folder.rglob("*") if p.is_file())
        data[case.name] = (frame, raw, rows)
    comparisons, common = {}, []
    for a, b in PAIRS:
        if a not in data or b not in data:
            continue
        pair = a + "_vs_" + b
        comparisons[pair] = physical_difference(data[a][2], data[b][2])
        for kind in ("common_time", "common_progress"):
            for name, w in zip((a, b), common_windows(data[a][0], data[b][0], kind)):
                metric = window_metrics(data[name][2], data[name][1], w)
                metric["timing_method"] = "native_edges_inside_shared_observed_bounds"
                common.append(dict(case=name, pair=pair, **flatten(metric)))
    write(output / "summary.json", report)
    write(output / "comparison.json", comparisons)
    write(output / "provenance.json", provenance)
    csv_rows(output / "lap_sector_metrics.csv", windows, ("case", "kind", "index", "complete"))
    csv_rows(output / "common_coverage_metrics.csv", common, ("case", "pair", "kind"))
    csv_rows(output / "cycles.csv", cycles, ("case", "plan_id", "t_release", "t_ready"))
    csv_rows(output / "misses.csv", misses, ("case", "plan_id", "miss_time", "recovery_time"))
    from task007dvis.long_figures import render

    render(data, report, windows, cycles, output)
    write(output / "artifact_hashes.json", hashes(p for p in output.iterdir() if p.is_file()))
    return {k: v["status"] for k, v in report.items()}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
