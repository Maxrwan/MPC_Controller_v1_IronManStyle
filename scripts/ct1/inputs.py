"""Standard-library immutable identity/causal readers; no APEX/numerical imports."""

from __future__ import annotations

import bisect
import hashlib
import json
import math
import subprocess
from pathlib import Path
from types import MappingProxyType

from .contracts import (
    ASSIGNMENT_REVISION,
    MANIFEST_SHA256,
    STATE_NAMES,
    ArchivedPacket,
    AuthorityInterval,
    CandidateBinding,
    CausalHistory,
    CurvaturePolicy,
    FileBinding,
    InputSpec,
    OperatingTuple,
    Outcome,
    OutcomeStatus,
    PendingRequest,
    Reason,
    TupleRole,
    VerifiedInputs,
)


def _read(path):
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError("Duplicate JSON key: " + k)
            d[k] = v
        return d

    return json.loads(
        Path(path).read_text(),
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
    )


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _plain(value):
    from collections.abc import Mapping

    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _canonical(value):
    return (
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _resolve(root, name):
    p = (Path(root) / name).resolve()
    if not p.is_relative_to(Path(root).resolve()):
        raise ValueError("Source path escapes verified root")
    return p


def verify_inputs(spec: InputSpec) -> Outcome[VerifiedInputs]:
    try:
        root = spec.repo_root.resolve()
        if _git(root, "rev-parse", "HEAD") != spec.expected_revision:
            raise ValueError("Implementation revision mismatch")
        if _git(root, "status", "--porcelain"):
            raise ValueError("Unreviewed dirty worktree")
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "merge-base",
                "--is-ancestor",
                ASSIGNMENT_REVISION,
                spec.expected_revision,
            ],
            check=True,
        )
        if _git(root, "remote", "get-url", "origin") not in (
            "https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle.git",
            "git@github.com:Maxrwan/MPC_Controller_v1_IronManStyle.git",
        ):
            raise ValueError("Wrong repository remote")
        if spec.assignment_root.resolve() != root / "docs/ct1/ct1l":
            raise ValueError("Assignment root mismatch")
        # Every approved documentation file is immutable, even on descendants.
        for name in _git(
            root, "ls-tree", "-r", "--name-only", ASSIGNMENT_REVISION, "docs/ct1"
        ).splitlines():
            original = subprocess.check_output(
                ["git", "-C", str(root), "show", ASSIGNMENT_REVISION + ":" + name]
            )
            if _resolve(root, name).read_bytes() != original:
                raise ValueError("Approved document changed: " + name)
        manifest = "configs/performance/apex_performance_synthetic_v1.json"
        if _sha(root / manifest) != MANIFEST_SHA256:
            raise ValueError("Performance manifest mismatch")
        provenance = _read(root / "docs/ct1/preservation_and_provenance.json")
        bindings = []
        for item in provenance["source_files"]:
            p = _resolve(root, item["path"])
            if _sha(p) != item["sha256"]:
                raise ValueError("Source hash mismatch: " + item["path"])
            bindings.append(FileBinding(item["path"], item["sha256"]))
        allow = _read(spec.assignment_root / "future_source_allowlist.json")
        for item in allow["additional_read_only_bindings"]:
            if _sha(_resolve(root, item["path"])) != item["sha256"]:
                raise ValueError("Additional accepted binding changed: " + item["path"])
            if not any(b.path == item["path"] for b in bindings):
                bindings.append(FileBinding(item["path"], item["sha256"]))
        for item in provenance["evidence_files"]:
            if _sha(_resolve(spec.archive_root, item["path"])) != item["sha256"]:
                raise ValueError("Archive hash mismatch: " + item["path"])
            bindings.append(FileBinding(item["path"], item["sha256"]))
        panel_path = "docs/ct1/operating_point_selection.json"
        panel = _read(root / panel_path)
        contract = _read(spec.assignment_root / "point_qualification_contract.json")[
            "immutable_panel"
        ]
        if _sha(root / panel_path) != contract["sha256"]:
            raise ValueError("Panel hash mismatch")
        if [p["id"] for p in panel["points"]] != contract["candidate_order"] or len(
            panel["points"]
        ) != 12:
            raise ValueError("Candidate membership/order changed")
        candidates = []
        for p, b in zip(panel["points"], contract["bindings"], strict=True):
            h = hashlib.sha256(_canonical(p)).hexdigest()
            if h != b["candidate_object_canonical_sha256"]:
                raise ValueError("Candidate object mismatch")
            candidates.append(
                CandidateBinding(
                    p["id"],
                    _freeze(p),
                    h,
                    contract["sha256"],
                    p["raw_state_row"],
                    p["raw_control_row"],
                    p["packet_id"],
                    p["packet_gain_index"],
                )
            )
        metrics = _freeze(_read(root / "docs/ct1/metrics_and_interpretation.json"))
        return Outcome.available(VerifiedInputs(spec, tuple(bindings), tuple(candidates), metrics))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        return Outcome(OutcomeStatus.INVALID, (Reason("SOURCE_IDENTITY_FAILURE", str(exc)),))


def _candidate(inputs, candidate_id):
    return next(c for c in inputs.candidates if c.candidate_id == candidate_id)


def _run(inputs):
    return inputs.spec.archive_root / "results/task007d/vis/vis1r_c699057/controlled_A"


def _interval(d):
    return AuthorityInterval(
        d["start"], d["end"], d["expiry"], d.get("superseded_at"), d["plan_id"], d["origin"]
    )


def load_original_packet(inputs: VerifiedInputs, packet_id: int) -> Outcome[ArchivedPacket]:
    try:
        run = _run(inputs)
        path = run / "scientific/packets.json"
        packets = _read(path)
        i, p = next((i, p) for i, p in enumerate(packets) if p["plan_id"] == packet_id)
        authorities = _read(run / "scientific/manifest.json")["accepted_authority_intervals"]
        intervals = tuple(_interval(a) for a in authorities if a["plan_id"] == packet_id)
        binding = FileBinding(str(path.relative_to(inputs.spec.archive_root)), _sha(path), f"/{i}")
        return Outcome.available(
            ArchivedPacket(
                _freeze(p),
                tuple(p["timestamps"]),
                _freeze(p["states"]),
                _freeze(p["controls"]),
                tuple(p["gain_times"]),
                _freeze(p["gains"]),
                tuple(p["curvatures"]),
                binding,
                intervals,
            )
        )
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        return Outcome.unavailable("PACKET_UNAVAILABLE", str(exc))


def _sample(packet, time):
    ts = packet.timestamps_s
    if time < ts[0] - 1e-10 or time > ts[-1] + 1e-10:
        raise ValueError("No packet extrapolation")
    i = max(0, min(bisect.bisect_right(ts, time + 1e-10) - 1, len(packet.controls) - 1))
    a = min(1.0, max(0.0, (time - ts[i]) / (ts[i + 1] - ts[i])))
    # Match packet heading unwrapping before interpolation without numerical package imports.
    headings = []
    for row in packet.states:
        t = float(row[3])
        if headings:
            delta = t - headings[-1]
            wrapped = (delta + math.pi) % (2 * math.pi) - math.pi
            if wrapped == -math.pi and delta > 0:
                wrapped = math.pi
            t = headings[-1] + wrapped
        headings.append(t)
    x = tuple(
        (1 - a) * packet.states[i][j] + a * packet.states[i + 1][j]
        if j != 3
        else (1 - a) * headings[i] + a * headings[i + 1]
        for j in range(6)
    )
    gi = max(
        0,
        min(
            bisect.bisect_right(packet.gain_times_s, time + 1e-10) - 1,
            len(packet.original_gains) - 1,
        ),
    )
    return x, tuple(packet.controls[i]), tuple(packet.original_gains[gi]), gi


def load_candidate_tuples(
    inputs: VerifiedInputs, candidate_id: str
) -> Outcome[tuple[OperatingTuple, OperatingTuple]]:
    try:
        c = _candidate(inputs, candidate_id)
        p = c.original_candidate_json
        raw = _read(_run(inputs) / "raw.json")
        state = raw["states"][c.raw_state_row]
        control = raw["controls"][c.raw_control_row]
        if (
            tuple(state[k] for k in STATE_NAMES) != tuple(p["state"])
            or state["time"] != p["timestamp_s"]
            or control["time"] != state["time"]
        ):
            raise ValueError("Archived state/control association changed")
        packet = load_original_packet(inputs, c.packet_id).unwrap()
        x, u, g, gi = _sample(packet, state["time"])
        if tuple(g) != tuple(p["original_gain"]) or gi != c.gain_index:
            raise ValueError("Original gain association changed")
        actual = OperatingTuple(
            candidate_id + ":actual",
            candidate_id,
            TupleRole.ACTUAL_HELD,
            tuple(p["state"]),
            tuple(p["held_applied_control"]),
            state["time"],
            c.packet_id,
            gi,
            CurvaturePolicy.GEOMETRY_PROGRESS,
        )
        nominal = OperatingTuple(
            candidate_id + ":nominal",
            candidate_id,
            TupleRole.PACKET_NOMINAL,
            x,
            u,
            state["time"],
            c.packet_id,
            gi,
            CurvaturePolicy.FROZEN_EXOGENOUS,
        )
        return Outcome.available((actual, nominal))
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        return Outcome(OutcomeStatus.INVALID, (Reason("CAUSAL_BINDING_INVALID", str(exc)),))


def load_authority_and_command_history(
    inputs: VerifiedInputs, candidate_id: str
) -> Outcome[CausalHistory]:
    try:
        c = _candidate(inputs, candidate_id)
        p = c.original_candidate_json
        t = p["timestamp_s"]
        raw = _read(_run(inputs) / "raw.json")
        packet = load_original_packet(inputs, c.packet_id).unwrap()
        a = next(
            a for a in packet.authority_intervals if a.start_s <= t < a.end_s and t < a.expiry_s
        )
        apps = [
            r
            for r in raw["controls"]
            if r.get("application_time") is not None and r["application_time"] <= t + 1e-10
        ]
        last = max(apps, key=lambda r: r["application_time"])
        if (last["delta"], last["a_cmd"]) != tuple(p["held_applied_control"]):
            raise ValueError("Held physical command mismatch")
        if (
            last["plan_id"] != p["applied_source_plan_id"]
            or last["application_time"] != p["last_application_s"]
            or last["delta"] != p["previous_applied_steering_rad"]
        ):
            raise ValueError("Applied packet/time/steering lineage contradicts candidate binding")
        requests = tuple(_freeze(r) for r in raw["controls"] if r["time"] <= t + 1e-10)
        pending = [
            r
            for r in raw["controls"]
            if r["time"] <= t + 1e-10
            and (r.get("application_time") is None or r["application_time"] > t + 1e-10)
        ]
        q = None
        if pending:
            r = max(pending, key=lambda r: r["time"])
            q = PendingRequest(
                (r["requested_delta"], r["requested_a_cmd"]),
                r["time"],
                r.get("application_time"),
                r["plan_id"],
                r.get("application_time"),
                "observed later application; unapplied tail incomplete",
            )
        return Outcome.available(
            CausalHistory(
                tuple(p["state"]),
                t,
                tuple(p["held_applied_control"]),
                p["applied_source_plan_id"],
                last["application_time"],
                last["delta"],
                q,
                False,
                a,
                requests,
                (
                    Reason(
                        "PENDING_TAIL_INCOMPLETE",
                        "Historical export does not contain exhaustive unapplied tail",
                    ),
                ),
            )
        )
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        return Outcome.unavailable("CAUSAL_HISTORY_UNAVAILABLE", str(exc))
