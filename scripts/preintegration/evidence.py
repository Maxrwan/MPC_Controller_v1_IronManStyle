"""New W1 JSON projection and descriptive summaries; never repairs old VIS evidence."""

import hashlib
import json
import math
import os
from dataclasses import fields, is_dataclass
from pathlib import Path


def project(value):
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: project(getattr(value, f.name)) for f in fields(value)}
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("Nonfinite scientific value; retain separate fault representation")
        return value
    if isinstance(value, dict):
        if any(type(k) is not str for k in value):
            raise ValueError("JSON object keys must be strings")
        return {k: project(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [project(v) for v in value]
    if type(value).__module__.startswith("numpy"):
        return project(value.tolist())
    raise TypeError("Unsupported result type " + type(value).__name__)


def write(path, value):
    data = json.dumps(project(value), indent=2, allow_nan=False, sort_keys=True) + "\n"
    path = Path(path)
    pending = path.with_name(path.name + ".pending")
    with pending.open("w") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)


class Journal:
    def __init__(self, path):
        self.path = Path(path)

    def __call__(self, event):
        with self.path.open("a") as stream:
            stream.write(json.dumps(project(event), allow_nan=False, sort_keys=True) + "\n")
            stream.flush()


def inventory(root):
    root = Path(root)
    return {
        str(p.relative_to(root)): {
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != "index.json"
    }


def distribution(values):
    raw_values = list(values)
    values = [v for v in raw_values if v is not None]
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Invalid timing observation")
    ordered = sorted(values)
    if not ordered:
        return {
            "count": 0,
            "samples_s": raw_values,
            "missing_count": len(raw_values) - len(values),
            "min": None,
            "median": None,
            "p95": None,
            "max": None,
            "status": "NOT_OBSERVED",
        }
    n = len(values)
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    return {
        "count": n,
        "samples_s": raw_values,
        "missing_count": len(raw_values) - len(values),
        "min": ordered[0],
        "median": median,
        "p95": ordered[math.ceil(0.95 * n) - 1],
        "max": ordered[-1],
        "quantile": "nearest-rank ceil(0.95*n)",
        "status": "OBSERVED",
    }


def assess(raw, boundary, *, scientific=None):
    plans = raw.get("plans", [])
    recurring = [p for p in plans if not p.get("startup") and p.get("completed")]
    full = distribution(p["planner_total_time"] for p in recurring)
    solve = distribution(p.get("solve_time") for p in recurring)
    tracker = distribution(
        b.get("native_seconds") for b in boundary if b.get("operation") == "propose"
    )
    runner = distribution(c.get("total_time") for c in raw.get("controls", []))
    valid = (
        raw.get("failure") is None
        and raw.get("stop_reason") == "duration"
        and not raw.get("fallbacks")
        and scientific is not None
        and scientific.get("valid_prerequisite") is True
    )
    classification = "INSUFFICIENT_EVIDENCE"
    if valid and full["count"] >= 10:
        concern = bool(
            raw.get("misses")
            or raw.get("codriver_misses")
            or full["p95"] > 0.1
            or (tracker["p95"] or 0) > 0.01
        )
        classification = (
            "FEASIBILITY_CONCERN_OBSERVED" if concern else "PRELIMINARY_FEASIBILITY_OBSERVED"
        )
    return {
        "classification": classification,
        "native_preparation": full,
        "native_solve": solve,
        "native_tracker": tracker,
        "runner_control_envelope": runner,
        "timing_populations": {
            "native_tracker": (
                "all successful proposals; native update total_time captured before runner mutation"
            ),
            "runner_control_envelope": "applied control rows only; enclosing runner total_time",
            "boundary_envelopes": "delegate wall_seconds including validation and journal work",
            "units": "seconds",
        },
        "startup": [p for p in plans if p.get("startup")],
        "unfinished_preparations": [
            p for p in plans if not p.get("startup") and not p.get("completed")
        ],
        "boundary_envelopes": boundary,
        "planner_busy": raw.get("misses", []),
        "codriver_busy": raw.get("codriver_misses", []),
        "simulated_coverage_s": raw.get("end_time"),
        "comparisons": {
            "preparation_release_opportunity_s": 0.1,
            "tracker_period_s": 0.01,
            "fixed_handoff_deadline": None,
        },
        "limits": [
            "small sample",
            "no observer correction",
            "Mac only, no onboard claim",
            "legacy application observations are not endpoint enforcement",
        ],
    }


def reconcile(exit_code, worker, guard_reason=None):
    return (
        exit_code == 0
        and worker is not None
        and worker.get("complete") is True
        and guard_reason is None
    )


def audit_completion(raw, segments, events, track, sim, tracker, releases):
    """Audit recorded native execution, without substituting a new simulator or policy.

    Exact track widths and native packet validity apply. Time/state comparisons only use
    the existing runner's floating-point chronology tolerance; boundary limits are exact.
    Offending records remain in the original artifacts and are addressed by JSON paths.
    """
    import numpy as np

    from apex.control.trajectory.packet import TrajectoryPacket
    from apex.state import STATE_NAMES

    errors = []

    def require(ok, path, reason):
        if not ok:
            errors.append({"path": path, "reason": reason})

    def same(a, b):
        return np.shape(a) == np.shape(b) and bool(
            np.allclose(a, b, atol=1e-9, rtol=0, equal_nan=False)
        )

    def finite(value):
        return bool(np.isfinite(value).all())

    def state(x, path):
        require(np.shape(x) == (6,) and finite(x), path, "INVALID_STATE")
        if np.shape(x) == (6,) and finite(x):
            geometry = track.sample(x[4] % track.length)
            require(-geometry.right_width <= x[5] <= geometry.left_width, path, "TRACK_BOUNDARY")

    def command(u, path):
        require(
            np.shape(u) == (2,)
            and finite(u)
            and bool(np.all(np.asarray(u) >= tracker.lower))
            and bool(np.all(np.asarray(u) <= tracker.upper)),
            path,
            "INVALID_COMMAND",
        )

    try:
        require(raw["failure"] is None, "/failure", "NATIVE_FAILURE")
        require(raw["stop_reason"] == "duration", "/stop_reason", "INCOMPLETE_EXECUTION")
        require(same(raw["end_time"], sim.duration), "/end_time", "INCOMPLETE_COVERAGE")
        require(not raw["fallbacks"], "/fallbacks", "FALLBACK")
        plans, packets = {}, {}
        for i, p in enumerate(raw["plans"]):
            path = f"/plans/{i}"
            pid = p["plan_id"]
            require(type(pid) is int and pid not in plans, path, "PLAN_IDENTITY")
            require(p["success"] is True and p["max_slack"] <= 1e-6, path, "PREPARATION_FAILED")
            require(p["prediction_architecture"] == "A", path, "PREDICTION_ARCHITECTURE")
            require(
                finite([p["release_time"], p["completion_time"], p["max_slack"]])
                and 0 <= p["release_time"] <= p["completion_time"],
                path,
                "PLAN_CHRONOLOGY",
            )
            require(p["startup"] is (i == 0) and pid == i, path, "PLAN_SEQUENCE")
            if i == 0:
                require(p["release_time"] == p["completion_time"] == 0, path, "STARTUP_TIME")
            else:
                require(
                    same(p["completion_time"], p["release_time"] + p["physical_delay"]),
                    path,
                    "COMPLETION_DELAY",
                )
                require(
                    p["completed"] is (p["completion_time"] < sim.duration - 1e-10),
                    path,
                    "COMPLETION_VISIBILITY",
                )
            plans[pid] = p
        require(bool(plans), "/plans", "NO_STARTUP")
        for i, p in enumerate(raw["packets"]):
            path = f"/packets/{i}"
            packet = TrajectoryPacket(
                **{k: p[k] for k in TrajectoryPacket.__dataclass_fields__ if k in p}
            )
            pid = packet.plan_id
            require(pid not in packets and pid in plans and packet.valid, path, "PACKET_IDENTITY")
            plan = plans[pid]
            require(
                same(packet.planner_release_time, plan["release_time"])
                and same(packet.planner_sample_time, plan["release_time"])
                and same(packet.actual_completion_time, plan["completion_time"])
                and same(packet.intended_handoff_time, plan["predicted_completion_time"])
                and same(packet.source_sampled_state, plan["source_state"])
                and same(packet.predicted_handoff_state, plan["predicted_state"]),
                path,
                "PACKET_SOURCE_BINDING",
            )
            packets[pid] = packet
        require(set(packets) == set(plans), "/packets", "MISSING_PACKET")
        accepted = {0: 0.0}
        last_handoff = 0.0
        for i, handoff in enumerate(raw["handoffs"]):
            pid, now = handoff["plan_id"], handoff["time"]
            require(
                handoff["accepted"] is True and pid in packets and pid not in accepted,
                f"/handoffs/{i}",
                "REJECTED_OR_INVALID_HANDOFF",
            )
            require(now >= last_handoff and now < sim.duration, f"/handoffs/{i}", "HANDOFF_ORDER")
            packet = packets[pid]
            require(
                now >= max(packet.actual_completion_time, packet.timestamps[0]) - 1e-10
                and packet.horizon_end_time - now >= 0.05,
                f"/handoffs/{i}",
                "HANDOFF_AUTHORITY",
            )
            accepted[pid], last_handoff = now, now

        def authority(pid, now, path):
            packet = packets[pid]
            require(
                pid in accepted
                and now
                >= max(
                    accepted.get(pid, math.inf), packet.actual_completion_time, packet.timestamps[0]
                )
                - 1e-10
                and now < packet.horizon_end_time - 1e-10,
                path,
                "SOURCE_AUTHORITY",
            )

        def active_source(pid, now, path):
            # A same-instant handoff can follow a proposal. Earlier replacements are visible.
            earlier = [p for p, accepted_at in accepted.items() if accepted_at < now - 1e-10]
            require(not earlier or pid >= max(earlier), path, "STALE_ACTIVE_SOURCE")

        proposals, preparations, completions = [], [], []
        last_time, session = 0.0, events[0].session
        for i, e in enumerate(events):
            path = f"/events/{i}"
            require(e.sequence == i and e.session == session, path, "EVENT_IDENTITY")
            require(e.status not in ("INHIBITED", "REJECTED"), path, "CONTROLLER_FAULT")
            if e.time is not None:
                require(
                    finite(e.time) and last_time - 1e-10 <= e.time <= sim.duration,
                    path,
                    "EVENT_ORDER",
                )
                last_time = e.time
            detail = dict(e.details)
            if e.operation == "prepare":
                preparations.append(detail["plan_id"])
                require(
                    same(e.time, plans[detail["plan_id"]]["release_time"]), path, "EVENT_RELEASE"
                )
            if e.operation == "completion":
                completions.append(detail["plan_id"])
                require(
                    same(e.time, plans[detail["plan_id"]]["completion_time"]),
                    path,
                    "EVENT_COMPLETION",
                )
            if e.operation == "propose":
                output = dict(detail["output"])
                require(
                    output["proposal_id"] == len(proposals) + 1
                    and output["status"] == "VALID_NOMINAL",
                    path,
                    "PROPOSAL_IDENTITY",
                )
                require(same(output["time"], e.time), path, "PROPOSAL_TIME")
                authority(output["plan_id"], e.time, path)
                active_source(output["plan_id"], e.time, path)
                command(output["command"], path)
                proposals.append(output)
        require(preparations == list(plans), "/events", "MISSING_PREPARATION_EVENT")
        require(
            completions == [pid for pid, p in plans.items() if p["startup"] or p["completed"]],
            "/events",
            "MISSING_COMPLETION_EVENT",
        )
        require(bool(proposals) and bool(raw["controls"]), "/controls", "NO_NOMINAL_CONTROL")
        require(len(raw["states"]) == len(segments) > 0, "/segments", "STATE_SEGMENT_COVERAGE")
        previous_end = 0.0
        for i, segment in enumerate(segments):
            path = f"/segments/{i}"
            require(
                finite([segment["start"], segment["end"], segment["dt"]])
                and same(segment["start"], previous_end)
                and segment["end"] > segment["start"]
                and same(segment["end"] - segment["start"], segment["dt"]),
                path,
                "SEGMENT_CHRONOLOGY",
            )
            state(segment["state_before"], path + "/state_before")
            state(segment["state_after"], path + "/state_after")
            command(segment["control"], path + "/control")
            row = raw["states"][i]
            require(
                row["boundary_violation"] is False, f"/states/{i}", "RECORDED_BOUNDARY_VIOLATION"
            )
            state([row[k] for k in STATE_NAMES], f"/states/{i}")
            require(
                same(row["time"], segment["start"])
                and same([row[k] for k in STATE_NAMES], segment["state_before"])
                and same([row["delta"], row["a_cmd"]], segment["control"])
                and row["mode"] == "trajectory",
                path,
                "NATIVE_STATE_SEGMENT_BINDING",
            )
            authority(row["plan_id"], segment["start"], path)
            require(
                row["plan_id"]
                == max(pid for pid, at in accepted.items() if at <= segment["start"] + 1e-10),
                path,
                "STATE_ACTIVE_SOURCE",
            )
            if i:
                require(
                    same(segments[i - 1]["state_after"], segment["state_before"]),
                    path,
                    "STATE_DISCONTINUITY",
                )
            previous_end = segment["end"]
        require(same(previous_end, sim.duration), "/segments", "MISSING_TERMINAL_STATE")
        initial = raw["plans"][0]["prepositioned_control"]
        applied, last_application, source = initial, 0.0, 0
        consumed, control_index = set(), 0
        for i, c in enumerate(raw["controls"]):
            path = f"/controls/{i}"
            require(c["mode"] == "trajectory", path, "NON_NOMINAL_CONTROL")
            require(
                finite([c["time"], c["application_time"], c["physical_latency"]])
                and 0 <= c["time"] <= c["application_time"] < sim.duration
                and c["application_time"] >= last_application
                and same(c["application_time"] - c["time"], c["physical_latency"]),
                path,
                "APPLICATION_CHRONOLOGY",
            )
            matches = [
                p for p in proposals if same(p["time"], c["time"]) and p["plan_id"] == c["plan_id"]
            ]
            require(len(matches) == 1, path, "APPLICATION_SOURCE_PROPOSAL")
            if len(matches) == 1:
                proposal = matches[0]
                require(proposal["proposal_id"] not in consumed, path, "DUPLICATE_APPLICATION")
                consumed.add(proposal["proposal_id"])
                require(
                    same(proposal["command"], [c["requested_delta"], c["requested_a_cmd"]]),
                    path,
                    "REQUEST_BINDING",
                )
            authority(c["plan_id"], c["time"], path)
            authority(c["plan_id"], c["application_time"], path)
            rate = tracker.config.steering_rate * max(0.0, c["application_time"] - last_application)
            expected = [
                float(np.clip(c["requested_delta"], applied[0] - rate, applied[0] + rate)),
                c["requested_a_cmd"],
            ]
            require(same(expected, [c["delta"], c["a_cmd"]]), path, "RECORDED_APPLICATION_CLAMP")
            command(expected, path)
            applied, last_application = expected, c["application_time"]
        applied, source = initial, 0
        for i, segment in enumerate(segments):
            while (
                control_index < len(raw["controls"])
                and raw["controls"][control_index]["application_time"] <= segment["start"] + 1e-10
            ):
                c = raw["controls"][control_index]
                applied, source = [c["delta"], c["a_cmd"]], c["plan_id"]
                control_index += 1
            require(same(applied, segment["control"]), f"/segments/{i}", "APPLICATION_HOLD_ORDER")
            authority(source, segment["start"], f"/segments/{i}")
            require(
                segment["end"] <= packets[source].horizon_end_time + 1e-10,
                f"/segments/{i}",
                "HELD_SOURCE_EXPIRED",
            )
        require(len(releases) == len(plans) - 1, "/releases", "RELEASE_OBSERVER_COVERAGE")
        require(
            [r["plan_id"] for r in raw["releases"]] == list(plans)[1:],
            "/releases",
            "RELEASE_PLAN_BINDING",
        )
        require(
            all(same(r["time"], plans[r["plan_id"]]["release_time"]) for r in raw["releases"]),
            "/releases",
            "NATIVE_RELEASE_TIME",
        )
        for release, plan in zip(releases, list(plans.values())[1:]):
            require(
                release.plan_id == plan["plan_id"]
                and same(release.prefix.release_time, plan["release_time"])
                and same(release.state, plan["source_state"]),
                "/releases",
                "CAPTURE_SOURCE_BINDING",
            )
            prefix = release.prefix
            prior = [
                c
                for c in raw["controls"]
                if c["application_time"] <= prefix.release_time + 1e-10
                and c["time"] < prefix.release_time - 1e-10
            ]
            last = prior[-1] if prior else None
            require(
                same(
                    prefix.applied_control,
                    initial if last is None else [last["delta"], last["a_cmd"]],
                )
                and same(
                    prefix.last_application_time, 0 if last is None else last["application_time"]
                ),
                "/releases",
                "RELEASE_APPLICATION_ORDER",
            )
            require(release.packet is not None, "/releases", "MISSING_RELEASE_AUTHORITY")
            if release.packet is not None:
                authority(release.packet.plan_id, prefix.release_time, "/releases")
                active_source(release.packet.plan_id, prefix.release_time, "/releases")
            at_release = [s for s in segments if same(s["start"], plan["release_time"])]
            require(
                len(at_release) == 1 and same(at_release[0]["state_before"], plan["source_state"]),
                "/releases",
                "SAMPLED_PLANT_STATE",
            )
        if sim.latency_mode == "zero":
            require(
                all(c["physical_latency"] == 0 for c in raw["controls"])
                and all(p.get("physical_delay", 0) == 0 for p in plans.values()),
                "/",
                "ZERO_DELAY_PROTOCOL",
            )
        if sim.latency_mode == "injected":
            require(
                bool(raw["codriver_misses"])
                and all(same(c["physical_latency"], 0.025) for c in raw["controls"])
                and all(same(p["physical_delay"], 0.06) for p in list(plans.values())[1:]),
                "/",
                "INJECTED_DELAY_PROTOCOL",
            )
    except (KeyError, IndexError, TypeError, ValueError, AttributeError) as error:
        errors.append(
            {"path": "/", "reason": "INCOMPLETE_OR_INVALID_EVIDENCE", "detail": str(error)}
        )
    return {
        "valid_prerequisite": not errors,
        "errors": errors,
        "execution_completed": raw.get("stop_reason") == "duration" and raw.get("failure") is None,
        "physical_safety": "NOT_OBSERVED_NOT_VALIDATED",
    }
