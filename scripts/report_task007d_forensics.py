"""D5 retained-record forensics only. Never launch a solver, forecast or plant."""

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

from threading_study.config import configure_accelerate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/task007d/d4"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        list(Path("results").rglob("MEASURED_ACTIVE"))
        or Path("results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Active measurement/campaign guard")
    if shutil.disk_usage(".").free < 1024**3:
        raise RuntimeError("Existing 1 GiB disk safety floor")
    configure_accelerate(1)
    from task007d.forensics import (
        accepted_packets,
        active_at,
        audit_nominals,
        comparisons,
        describe,
        low_latency_tables,
    )
    from task007d.metrics import chronology, physical_metrics

    from apex.planning_reference.track import load_track
    from apex.state import STATE_NAMES

    d4 = json.loads(Path("docs/task007d/d4/summary.json").read_text())
    source_hashes = json.loads(Path("docs/task007d/d4/source_hashes.json").read_text())
    frozen = dict(d4["runs"]["D4-R4_A"]["fixture_sha256"])
    frozen.update(
        {p: digest for p, digest in source_hashes["D4-R4_A"].items() if p.startswith("src/")}
    )
    if any(sha(Path(p)) != digest for p, digest in frozen.items()):
        raise ValueError("Fixture or core source differs from the retained D4 baseline")
    fixture = Path(d4["runs"]["D4-R4_A"]["fixture"])
    track, _, _ = load_track(fixture / "track_source.json")
    sectors = json.loads((fixture / "planning_manifest.json").read_text())["sectors"]
    raw, scores, contexts, provenance, audits = {}, {}, {}, {}, {}
    for regime in ("R1", "R2", "R3", "R4"):
        for host in ("A", "B"):
            key = regime + "_" + host
            folder = args.input / key
            provenance[key] = {
                name: sha(folder / name)
                for name in ("raw.json", "scores.json", "release_contexts.json", "summary.json")
            }
            if provenance[key] != d4["runs"]["D4-" + key]["evidence_sha256"]:
                raise ValueError("Retained evidence differs from D4 committed hashes: " + key)
            raw[key] = json.loads((folder / "raw.json").read_text())
            scores[key] = json.loads((folder / "scores.json").read_text())
            contexts[key] = json.loads((folder / "release_contexts.json").read_text())
            issues = chronology(raw[key])
            if issues:
                raise ValueError(issues)
            timeline = accepted_packets(raw[key])
            audits[key] = audit_nominals(raw[key], timeline)
            plans = {p["plan_id"]: p for p in raw[key]["plans"]}
            for row, context in zip(scores[key], contexts[key], strict=True):
                p = plans[row["plan_id"]]
                if (
                    row["forecasts"][host]["state"] != p["predicted_state"]
                    or row["forecasts"][host]["control"] != p["predicted_previous_control"]
                    or context["state"] != p["source_state"]
                    or context["packet"]["plan_id"]
                    != active_at(timeline, row["release_time"]).plan_id
                ):
                    raise ValueError("Saved forecast/release inputs differ from runtime")
            audits[key]["retained_active_forecast_input_matches"] = len(scores[key])

    timelines = {h: accepted_packets(raw["R4_" + h]) for h in ("A", "B")}
    derived = {
        h: [describe(r, timelines[h], track, sectors) for r in raw["R4_" + h]["states"]]
        for h in ("A", "B")
    }
    coverage, same_time, same_progress = comparisons(
        derived["A"], derived["B"], timelines, track, sectors
    )
    minima, chain, applications = {}, {}, []
    for h in ("A", "B"):
        r = raw["R4_" + h]
        minimum = min(derived[h], key=lambda row: row["clearance"])
        expected = d4["runs"]["D4-R4_" + h]["physical"]["minimum_center_clearance"]
        if minimum["clearance"] != expected:
            raise ValueError("D4 minimum did not reproduce exactly")
        t = minimum["time"]
        plans = {p["plan_id"]: p for p in r["plans"]}
        recent_states = [
            {k: row[k] for k in ("time", "s_abs", "e_y", "e_psi", "r", "vy", "delta", "plan_id")}
            for row in derived[h]
            if t - 0.1000000001 <= row["time"] <= t
        ]
        previous_time, previous_delta = r["states"][0]["time"], r["states"][0]["delta"]
        for c in r["controls"]:
            elapsed = c["application_time"] - previous_time
            # Application-interval average, not a continuous actuator derivative.
            rate = (c["delta"] - previous_delta) / elapsed if elapsed > 0 else None
            applications.append(
                dict(
                    host=h,
                    sample_time=c["time"],
                    application_time=c["application_time"],
                    plan_id=c["plan_id"],
                    requested_delta=c["requested_delta"],
                    applied_delta=c["delta"],
                    a_cmd=c["a_cmd"],
                    elapsed_since_application=elapsed,
                    delta_change=c["delta"] - previous_delta,
                    application_average_rate=rate,
                    application_clamp_change=c["delta"] - c["requested_delta"],
                )
            )
            previous_time, previous_delta = c["application_time"], c["delta"]
        minima[h] = dict(
            event=minimum,
            margin_clearance=minimum["clearance"] - 0.08,
            active_plan_max_slack=plans[minimum["plan_id"]]["max_slack"],
            recent_heading_and_state=recent_states,
            recent_handoffs=[v for v in r["handoffs"] if t - 0.21 <= v["time"] <= t],
            recent_applications=[
                v for v in applications if v["host"] == h and t - 0.10 <= v["application_time"] <= t
            ],
            full_interval_metrics=physical_metrics(r, track),
        )
        p = plans[1]
        packet = next(v for v in r["packets"] if v["plan_id"] == 1)
        command = next(v for v in r["controls"] if v["plan_id"] == 1)
        chain[h] = dict(
            release_context=contexts["R4_" + h][0],
            plan={
                k: p[k]
                for k in (
                    "release_time",
                    "estimated_delay",
                    "predicted_completion_time",
                    "predicted_state",
                    "predicted_previous_control",
                    "completion_time",
                    "success",
                    "status",
                    "objective",
                    "iterations",
                    "max_slack",
                )
            },
            first_two_packet_times=packet["timestamps"][:2],
            first_two_packet_states=packet["states"][:2],
            first_packet_control=packet["controls"][0],
            first_handoff=r["handoffs"][0],
            first_command=command,
            state_at_first_difference=next(v for v in r["states"] if abs(v["time"] - 0.18) < 1e-10),
        )
        # The complete packet/config is already retained; keep only release-known fields here.
        context = chain[h]["release_context"]
        chain[h]["release_context"] = {
            k: context[k] for k in ("plan_id", "state", "estimated_delay", "prefix")
        }
        chain[h]["release_context"]["active_packet_id"] = context["packet"]["plan_id"]

    # First steering difference is much later than the first acceleration difference.
    control_changes = {}
    for channel in ("delta", "a_cmd"):
        b_by_time = {round(c["time"], 10): c for c in raw["R4_B"]["controls"]}
        for a in raw["R4_A"]["controls"]:
            b = b_by_time[round(a["time"], 10)]
            if abs(a[channel] - b[channel]) > 1e-12:
                control_changes[channel] = {"A": a, "B": b}
                break
    details, phases = [], []
    for regime in ("R1", "R2", "R3"):
        for h in ("A", "B"):
            d, p = low_latency_tables(scores[regime + "_" + h], regime, h)
            details.extend(d)
            phases.extend(p)
    # Discrete threshold crossings describe this retained trajectory, not a new safety gate.
    onset = {}
    for threshold in (1e-12, 0.001, 0.01, 0.05, 0.10):
        onset[str(threshold)] = next(
            (r for r in same_time if r["clearance_B_minus_A"] < -threshold), None
        )
    handoff_positions = [
        row
        for row in same_time
        if any(abs(row["A_time"] - h["time"]) < 1e-10 for h in raw["R4_A"]["handoffs"])
    ]
    summary = dict(
        method="Retained packet sampling and labelled linear spatial interpolation only",
        coverage=coverage,
        minimum_events=minima,
        audits=audits,
        clearance_loss_threshold_first_observation=onset,
        largest_same_time_loss=min(same_time, key=lambda r: r["clearance_B_minus_A"]),
        largest_same_progress_loss=min(same_progress, key=lambda r: r["clearance_B_minus_A"]),
        first_divergence=chain,
        first_control_channel_differences=control_changes,
        d4_first_divergence=d4["pairs"]["D4-R4"],
        unrecorded_nlp_internals="NLP guesses, parameters and iteration trajectory unavailable",
        state_order=list(STATE_NAMES),
    )
    args.output.mkdir(parents=True, exist_ok=False)
    write(args.output / "summary.json", summary)
    write(
        args.output / "provenance.json",
        dict(
            evidence_sha256=provenance,
            analysis_source_sha256={
                p: sha(Path(p))
                for p in ("scripts/task007d/forensics.py", "scripts/report_task007d_forensics.py")
            },
            fixture_sha256={
                str(fixture / p): sha(fixture / p)
                for p in ("track_source.json", "planning_manifest.json")
            },
        ),
    )
    for name, rows in [
        ("same_time", same_time),
        ("same_progress", same_progress),
        ("handoff_positions", handoff_positions),
        ("applications", applications),
        ("recorded_states", [{"host": h, **r} for h in ("A", "B") for r in derived[h]]),
        ("low_latency_releases", details),
        ("low_latency_phases", phases),
    ]:
        with (args.output / (name + ".csv")).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(
        json.dumps(
            dict(
                coverage=coverage, minima={h: minima[h]["event"] for h in ("A", "B")}, audits=audits
            )
        )
    )


if __name__ == "__main__":
    main()
