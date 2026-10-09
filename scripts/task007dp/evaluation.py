"""Retained-history scoring and per-channel statistics, outside forecast inputs."""

import hashlib
import json
from pathlib import Path

import numpy as np
from task007d.diagnostics import residual

from apex.planning_reference.track import load_track
from apex.state import STATE_NAMES
from task007dp.candidates import METHODS, TIME_TOL, Candidate, read_release

CHANNELS = (*STATE_NAMES, "delta", "a_cmd")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def dataset():
    """D4 primary plus retained gamma2 D3 reference. Reject changed original evidence."""
    compact = json.loads(Path("docs/task007d/d4/summary.json").read_text())
    sources = json.loads(Path("docs/task007d/d4/source_hashes.json").read_text())
    first = compact["runs"]["D4-R1_A"]
    frozen = {
        **first["fixture_sha256"],
        **{p: v for p, v in sources["D4-R1_A"].items() if p.startswith("src/")},
    }
    if any(sha(p) != v for p, v in frozen.items()):
        raise ValueError("Frozen fixture/source changed")
    track, _, _ = load_track(Path(first["fixture"]) / "track_source.json")
    cases = {}
    for name, summary in compact["runs"].items():
        folder = Path(summary["retained_directory"])
        for file, expected in summary["evidence_sha256"].items():
            if sha(folder / file) != expected:
                raise ValueError("Historical evidence changed: " + str(folder / file))
        contexts = json.loads((folder / "release_contexts.json").read_text())
        cases[name] = dict(
            releases=[read_release(r) for r in contexts],
            raw=json.loads((folder / "raw.json").read_text()),
            scores=json.loads((folder / "scores.json").read_text()),
            provenance=summary["evidence_sha256"],
        )
    return track, cases


def authority_events(raw, release, target):
    """Acceptance at target does not contaminate the preceding state/control convention."""
    start = release.prefix.release_time
    return [
        dict(kind="handoff", **h)
        for h in raw["handoffs"]
        if h["accepted"] and start + TIME_TOL < h["time"] < target - TIME_TOL
    ] + [
        {**row, "event_channel": channel}
        for channel in ("fallbacks", "triggers")
        for row in raw[channel]
        if start + TIME_TOL < row["time"] < target - TIME_TOL
        and (channel == "fallbacks" or row.get("kind") == "approved_state_perturbation")
    ]


def preceding_truth(raw, release, target):
    """After due prior work, before handoff/new feedback at target, as in D1.

    A zero-latency command computed AT target appears in the final same-time state row,
    but is too late for this preceding-input convention. A known due-now release request
    is included even for a zero-duration query. No forecast function receives this history.
    """
    if (
        not raw["states"]
        or not raw["states"][0]["time"] <= target <= raw["states"][-1]["time"] + TIME_TOL
    ):
        return None
    applied = np.asarray(release.prefix.applied_control)
    for c in raw["controls"]:
        known_at_release = c["time"] <= release.prefix.release_time + TIME_TOL
        if (
            c["application_time"] >= release.prefix.release_time - TIME_TOL
            and c["application_time"] <= target + TIME_TOL
            and (known_at_release or c["time"] < target - TIME_TOL)
        ):
            applied = np.array([c["delta"], c["a_cmd"]])
    return applied


def evaluate(track, cases):
    output, audit = [], {}
    for name, case in cases.items():
        engines = {m: Candidate(m, case["releases"][0].parameters, track) for m in METHODS}
        engines["P1b"].precompute(case["releases"])
        audit[name] = dict(
            reference_exact_matches=0,
            targets_on_nodes=0,
            interior_targets=0,
            optional_60ms_uncontaminated=0,
            optional_80ms_uncontaminated=0,
        )
        for release, old_score in zip(case["releases"], case["scores"], strict=True):
            target = release.prefix.release_time + release.estimated_delay
            if target != old_score["target_time"]:
                raise ValueError("Historical target mismatch")
            contamination = authority_events(case["raw"], release, target)
            node = bool(np.any(abs(release.packet.timestamps - target) <= TIME_TOL))
            audit[name]["targets_on_nodes" if node else "interior_targets"] += 1
            for duration in (0.060, 0.080):
                alternate = release.prefix.release_time + duration
                covered = alternate <= min(
                    release.packet.horizon_end_time, case["raw"]["states"][-1]["time"]
                )
                audit[name][f"optional_{int(duration * 1000)}ms_uncontaminated"] += int(
                    covered and not authority_events(case["raw"], release, alternate)
                )
            truth = old_score["truth"]["state"]
            truth_u = preceding_truth(case["raw"], release, target)
            predictions = {}
            for method, engine in engines.items():
                failure = None
                try:
                    x, u = engine(release)
                    predicted = np.r_[x, u].tolist()
                    clearance = engine.validate(x, u, release)
                except (ValueError, np.linalg.LinAlgError) as error:
                    failure, predicted, clearance = str(error), None, None
                if method in ("A", "P2"):
                    original = old_score["forecasts"]["A" if method == "A" else "B"]
                    if (
                        failure is not None
                        or predicted[:6] != original["state"]
                        or predicted[6:] != original["control"]
                    ):
                        raise RuntimeError(
                            "Existing reference behavior changed: " + name + "/" + method
                        )
                    audit[name]["reference_exact_matches"] += 1
                errors = None
                if (
                    predicted is not None
                    and truth is not None
                    and truth_u is not None
                    and not contamination
                ):
                    errors = np.r_[
                        residual(predicted[:6], truth), np.asarray(predicted[6:]) - truth_u
                    ].tolist()
                predictions[method] = dict(
                    predicted=predicted,
                    error=errors,
                    failure=failure,
                    predicted_center_clearance=clearance,
                )
            output.append(
                dict(
                    case=name,
                    plan_id=release.plan_id,
                    release_time=release.prefix.release_time,
                    target_time=target,
                    estimated_delay=release.estimated_delay,
                    target_on_node=node,
                    pending_application_time=release.prefix.pending_application_time,
                    truth_kind=old_score["truth"]["kind"],
                    truth=truth,
                    truth_control=None if truth_u is None else truth_u.tolist(),
                    contamination=contamination,
                    predictions=predictions,
                )
            )
    return output, audit


def statistics(rows):
    """No pooled A/B-host performance claims. P95 only for at least 20 contexts."""
    output = []
    for case in sorted({r["case"] for r in rows}):
        group = sorted([r for r in rows if r["case"] == case], key=lambda r: r["release_time"])
        phases = dict(all=group, first=group[:1], later=group[1:], after_second=group[2:])
        for phase, selected in phases.items():
            for method in METHODS:
                valid = [r for r in selected if r["predictions"][method]["error"] is not None]
                for i, state in enumerate(CHANNELS):
                    values = np.array([r["predictions"][method]["error"][i] for r in valid])
                    row = dict(
                        case=case,
                        phase=phase,
                        method=method,
                        channel=state,
                        total=len(selected),
                        comparable=len(valid),
                        excluded=len(selected) - len(valid),
                        failures=sum(
                            r["predictions"][method]["failure"] is not None for r in selected
                        ),
                        contaminated=sum(bool(r["contamination"]) for r in selected),
                        mean_signed=float(np.mean(values)) if len(values) else None,
                        rms=float(np.sqrt(np.mean(values**2))) if len(values) else None,
                        max_abs=float(np.max(abs(values))) if len(values) else None,
                        p95_abs=float(np.percentile(abs(values), 95))
                        if len(values) >= 20
                        else None,
                    )
                    for ref in ("A", "P2"):
                        differences = [
                            abs(r["predictions"][method]["error"][i])
                            - abs(r["predictions"][ref]["error"][i])
                            for r in valid
                            if r["predictions"][ref]["error"] is not None
                        ]
                        row.update(
                            {
                                f"{kind}_vs_{ref}": sum(predicate(v) for v in differences)
                                for kind, predicate in [
                                    ("better", lambda v: v < -1e-12),
                                    ("worse", lambda v: v > 1e-12),
                                    ("tie", lambda v: abs(v) <= 1e-12),
                                ]
                            }
                        )
                    output.append(row)
    return output
