"""Opt-in scalar preparation observations. G1 code; behavioral verification is pending G2.

No numerical imports, global hooks, background work or authority decisions belong here.
Clock endpoints exclude their own final publication tail. Limits are caps, not an RSS proof.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import get_ident
from types import MappingProxyType

API_VERSION = "profile1-v1"
REFERENCE_REVISION = "eaa0a3398515a21f30a850de59a0b44c775fad4d"
MANIFEST_SHA256 = "5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf"
PREPARATION_PARENTS = {
    "prepare_full": None,
    "prediction": "prepare_full",
    "controller": "prepare_full",
    "reference": "controller",
    "reference_geometry": "reference",
    "reference_values": "reference",
    "warm": "controller",
    "terminal_lookup": "warm",
    "guess": "warm",
    "parameter_pack": "controller",
    "solver_adapter": "controller",
    "ipopt_call": "solver_adapter",
    "adapter_validation": "solver_adapter",
    "controller_validation": "controller",
    "packet_initial": "prepare_full",
    "gains": "prepare_full",
    "gain_jacobians": "gains",
    "gain_terminal_dare": "gains",
    "gain_backward": "gains",
    "packet_gain_attach": "prepare_full",
    "packet_final": "prepare_full",
    "return_assembly": "prepare_full",
}
CONSTRUCTION_PARENTS = {
    "construction_full": None,
    "fixture_load": "construction_full",
    "nlp_graph": "construction_full",
    "solver_construction": "construction_full",
    "controller_construction": "construction_full",
    "terminal_construction": "controller_construction",
    "planner_construction": "construction_full",
    "gain_builder_construction": "planner_construction",
}
CLOCK_PROBE_PARENTS = {"clock_empty": None, "clock_parent": None, "clock_child": "clock_parent"}
CallToken = int
SpanToken = int
PrepOutcome = Mapping[str, object]
ReconciliationReport = dict[str, object]
ExportReport = dict[str, object]


@dataclass(frozen=True)
class WorkerIdentity:
    worker_id: str
    pid: int
    reference_revision: str
    implementation_revision: str
    implementation_diff_sha256: str
    manifest_sha256: str


@dataclass(frozen=True)
class RecorderLimits:
    max_calls: int = 64
    max_span_records: int = 8192
    max_stack_depth: int = 8
    max_fault_records: int = 64
    max_identity_utf8_bytes: int = 128
    max_exception_type_utf8_bytes: int = 256
    max_serialized_bytes: int = 16777216
    max_status_utf8_bytes: int = 2048


@dataclass(frozen=True)
class ClockAllowance:
    wall_ns: int | None = None
    cpu_ns: int | None = None
    provenance: str | None = None


@dataclass(frozen=True)
class FrozenSidecar:
    payload: Mapping[str, object]


class ClockReader:
    def wall_ns(self) -> int:
        return time.perf_counter_ns()

    def cpu_ns(self) -> int:
        return time.process_time_ns()


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _plain(value):
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_plain(v) for v in value]
    return value


def _hex(value, length):
    return (
        isinstance(value, str)
        and len(value) == length
        and all(c in "0123456789abcdef" for c in value)
    )


def create_recorder(
    *, mode: str, identity: WorkerIdentity, limits: RecorderLimits, clock: ClockReader | None = None
) -> Recorder | None:
    if mode == "off":
        return None
    if mode != API_VERSION:
        raise ValueError("Unsupported efficiency instrumentation mode")
    return Recorder(identity, limits, clock)


class Recorder:
    """Single-writer bounded slots; ordinary observation errors never escape into numerics."""

    api_version = API_VERSION

    def __init__(self, identity, limits, clock=None):
        if not isinstance(identity, WorkerIdentity) or not isinstance(limits, RecorderLimits):
            raise ValueError("Reviewed worker identity and limits required")
        defaults = RecorderLimits()
        for name, value in asdict(limits).items():
            if type(value) is not int or not 1 <= value <= getattr(defaults, name):
                raise ValueError("Recorder capacity exceeds reviewed limit")
        if (
            not isinstance(identity.worker_id, str)
            or not identity.worker_id
            or len(identity.worker_id.encode("utf-8")) > limits.max_identity_utf8_bytes
            or type(identity.pid) is not int
            or identity.pid <= 0
            or identity.reference_revision != REFERENCE_REVISION
            or not _hex(identity.implementation_revision, 40)
            or not _hex(identity.implementation_diff_sha256, 64)
            or identity.manifest_sha256 != MANIFEST_SHA256
        ):
            raise ValueError("Invalid or unbound worker identity")
        self.identity, self.limits = identity, limits
        self._clock = ClockReader() if clock is None else clock
        if not callable(getattr(self._clock, "wall_ns", None)) or not callable(
            getattr(self._clock, "cpu_ns", None)
        ):
            raise ValueError("ClockReader interface required")
        self._writer = get_ident()
        self._calls = [None] * limits.max_calls
        self._spans = [None] * limits.max_span_records
        self._faults = [None] * limits.max_fault_records
        self._first_fault = {"code": None, "call_seq": None, "span_token": None}
        self._fault_count = self._call_count = self._span_count = self._sequence = 0
        self._stack, self._occurrences = [], {}
        self._seen_plan_ids = set()
        self._active = None
        self._last_wall = self._last_cpu = None
        self._clock_order_valid = True
        self._sealed = None
        self._reconciliation = None

    def _fault(self, code, span=None):
        # First-fault storage was allocated before numerical work. Persistence is best effort.
        try:
            self._fault_count += 1
            if self._first_fault["code"] is None:
                self._first_fault.update(code=code, call_seq=self._active, span_token=span)
            if self._fault_count <= len(self._faults):
                self._faults[self._fault_count - 1] = {
                    "code": code,
                    "call_seq": self._active,
                    "span_token": span,
                }
        except Exception:
            self._fault_count = max(1, self._fault_count)

    def _guard(self, *, allow_fault=False):
        if get_ident() != self._writer:
            self._fault("foreign_writer")
            return False
        if self._sealed is not None:
            self._fault("recording_after_seal")
            return False
        return allow_fault or not self._fault_count

    def _pair(self):
        values = []
        for name, reader in (("wall", self._clock.wall_ns), ("cpu", self._clock.cpu_ns)):
            try:
                value = reader()
                if type(value) is not int or not 0 <= value < 2**63:
                    value = None
                    self._clock_order_valid = False
                    self._fault("invalid_" + name + "_clock")
                previous = getattr(self, "_last_" + name)
                if value is not None:
                    if previous is not None and value < previous:
                        self._clock_order_valid = False
                        self._fault("decreasing_" + name + "_clock")
                    setattr(self, "_last_" + name, value)
            except Exception:
                value = None
                self._clock_order_valid = False
                self._fault(name + "_clock_read_failed")
            values.append(value)
        return values

    @property
    def active_call(self) -> CallToken | None:
        return self._active

    def begin_call(
        self,
        *,
        kind: str,
        plan_id: int | None,
        release_sim_s: float | None,
        estimate_sim_s: float | None,
    ) -> CallToken | None:
        try:
            if not self._guard():
                return None
            if self._active is not None or self._call_count >= self.limits.max_calls:
                self._fault("call_overlap_or_capacity")
                return None
            faults_before = self._fault_count
            wall, cpu = self._pair()  # Before dispatch metadata/slot work, always wall then CPU.
            auxiliary = kind in ("construction", "clock_probe")
            if kind not in ("construction", "startup", "recurring", "clock_probe"):
                self._fault("unknown_call_kind")
                return None
            if auxiliary:
                valid = plan_id is None and release_sim_s is None and estimate_sim_s is None
            else:
                valid = (
                    type(plan_id) is int
                    and (plan_id == 0 if kind == "startup" else plan_id >= 1)
                    and all(
                        type(v) in (int, float) and math.isfinite(v) and v >= 0
                        for v in (release_sim_s, estimate_sim_s)
                    )
                )
            if not valid:
                self._fault("invalid_call_identity")
                return None
            if not auxiliary:
                if plan_id in self._seen_plan_ids:
                    self._fault("duplicate_preparation_identity")
                    return None
                self._seen_plan_ids.add(plan_id)
            self._call_count += 1
            token = self._call_count
            self._active = token
            self._calls[token - 1] = {
                "worker_id": self.identity.worker_id,
                "call_seq": token,
                "call_kind": kind,
                "plan_id": plan_id,
                "release_sim_s": release_sim_s,
                "estimate_sim_s": estimate_sim_s,
                "wall_start_ns": wall,
                "cpu_start_ns": cpu,
                "wall_end_ns": None,
                "cpu_end_ns": None,
                "outcome": None,
                "coverage": "partial",
                "missing_reason": "call_not_finished",
                "fault_count_at_begin": faults_before,
                "fault_count_at_end": None,
            }
            return token
        except Exception:
            self._fault("call_record_failed")
            return None

    def _catalog(self, call):
        kind = self._calls[call - 1]["call_kind"]
        if kind == "construction":
            return CONSTRUCTION_PARENTS
        if kind == "clock_probe":
            return CLOCK_PROBE_PARENTS
        return PREPARATION_PARENTS

    def span_begin(
        self, call: CallToken, span_id: str, *, expected_parent: str | None
    ) -> SpanToken | None:
        try:
            if not self._guard():
                return None
            if type(call) is not int or call != self._active:
                self._fault("missing_active_call")
                return None
            catalog = self._catalog(call)
            parent = self._stack[-1] if self._stack else None
            actual = self._spans[parent]["span_id"] if parent is not None else None
            if (
                span_id not in catalog
                or catalog[span_id] != expected_parent
                or actual != expected_parent
            ):
                self._fault("span_parent_mismatch")
                return None
            if (
                self._span_count >= self.limits.max_span_records
                or len(self._stack) >= self.limits.max_stack_depth
            ):
                self._fault("span_or_depth_capacity")
                return None
            token = self._span_count
            key = (call, span_id, parent)
            occurrence = self._occurrences.get(key, 0) + 1
            if (
                occurrence > 1
                and self._calls[call - 1]["call_kind"] != "clock_probe"
                and span_id not in ("reference_geometry", "reference_values")
            ):
                self._fault("unexpected_span_occurrence")
                return None
            self._occurrences[key] = occurrence
            self._span_count += 1
            self._sequence += 1
            record = {
                "worker_id": self.identity.worker_id,
                "call_seq": call,
                "call_kind": self._calls[call - 1]["call_kind"],
                "plan_id": self._calls[call - 1]["plan_id"],
                "span_token": token,
                "parent_span_token": parent,
                "span_id": span_id,
                "occurrence": occurrence,
                "begin_sequence": self._sequence,
                "end_sequence": None,
                "wall_start_ns": None,
                "cpu_start_ns": None,
                "wall_end_ns": None,
                "cpu_end_ns": None,
                "exit": None,
                "exception_type": None,
                "coverage": "partial",
                "missing_reason": "span_not_closed",
            }
            self._spans[token] = record
            self._stack.append(token)
            record["wall_start_ns"], record["cpu_start_ns"] = self._pair()
            return token
        except Exception:
            self._fault("span_begin_failed")
            return None

    def span_end(
        self, token: SpanToken | None, *, exit: str, exception_type: str | None = None
    ) -> str:
        try:
            if token is None:
                if not self._fault_count:
                    self._fault("missing_span_token")
                return "faulted"
            if not self._guard(allow_fault=True):
                return "faulted"
            if type(token) is not int or not 0 <= token < self._span_count:
                self._fault("invalid_span_token")
                return "faulted"
            if not self._stack or self._stack[-1] != token:
                self._fault("out_of_order_span_end", token)
                return "faulted"
            record = self._spans[token]
            record["wall_end_ns"], record["cpu_end_ns"] = self._pair()
            self._stack.pop()
            self._sequence += 1
            record["end_sequence"] = self._sequence
            if exit not in ("complete", "exception", "aborted"):
                self._fault("invalid_span_exit", token)
                exit = "aborted"
            if exception_type is not None and (
                not isinstance(exception_type, str)
                or len(exception_type.encode("utf-8")) > self.limits.max_exception_type_utf8_bytes
            ):
                self._fault("exception_type_capacity", token)
                exception_type = None
            record["exit"], record["exception_type"] = exit, exception_type
            endpoints = [
                record[k] for k in ("wall_start_ns", "cpu_start_ns", "wall_end_ns", "cpu_end_ns")
            ]
            record["coverage"] = (
                "complete" if exit == "complete" and None not in endpoints else "partial"
            )
            record["missing_reason"] = (
                None if record["coverage"] == "complete" else "exception_abort_or_clock_gap"
            )
        except Exception:
            self._fault("span_end_failed", token)
        return "faulted" if self._fault_count else "ok"

    def finish_call(self, call: CallToken | None, *, outcome: PrepOutcome) -> str:
        try:
            if not self._guard(allow_fault=True) or type(call) is not int or call != self._active:
                self._fault("finish_without_active_call")
                return "faulted"
            record = self._calls[call - 1]
            allowed = {"kind", "existing_status", "solver_attempted", "exception_type"}
            if set(outcome) != allowed or outcome["kind"] not in (
                "returned_packet",
                "returned_none",
                "raised",
                "not_applicable",
            ):
                self._fault("invalid_outcome_shape")
            else:
                safe = {"kind": outcome["kind"]}
                for key, maximum in (
                    ("existing_status", self.limits.max_status_utf8_bytes),
                    ("exception_type", self.limits.max_exception_type_utf8_bytes),
                ):
                    value = outcome[key]
                    if value is not None and (
                        not isinstance(value, str) or len(value.encode("utf-8")) > maximum
                    ):
                        self._fault("outcome_string_capacity")
                        value = None
                    safe[key] = value
                attempted = outcome["solver_attempted"]
                if attempted is not None and type(attempted) is not bool:
                    self._fault("invalid_solver_attempted")
                    attempted = None
                safe["solver_attempted"] = attempted
                record["outcome"] = safe
            if self._stack:
                self._fault("unclosed_spans_at_call_end")
                # Preserve incomplete slots without synthesizing endpoints or successful closure.
                for token in self._stack:
                    self._spans[token]["missing_reason"] = "unclosed_at_call_end"
                self._stack.clear()
            root_name = (
                "construction_full" if record["call_kind"] == "construction" else "prepare_full"
            )
            if record["call_kind"] != "clock_probe" and not any(
                row is not None and row["call_seq"] == call and row["span_id"] == root_name
                for row in self._spans[: self._span_count]
            ):
                self._fault("missing_call_root")
            # Last dispatch endpoint: appends/outcome bookkeeping precede it; publication follows
            # it.
            record["wall_end_ns"], record["cpu_end_ns"] = self._pair()
            record["coverage"] = (
                "complete"
                if all(
                    record[k] is not None
                    for k in ("wall_start_ns", "cpu_start_ns", "wall_end_ns", "cpu_end_ns")
                )
                else "partial"
            )
            record["missing_reason"] = None if record["coverage"] == "complete" else "clock_gap"
            record["fault_count_at_end"] = self._fault_count
            self._active = None
        except Exception:
            self._fault("finish_call_failed")
        return "faulted" if self._fault_count else "ok"

    def stop_requested(self) -> bool:
        return bool(self._fault_count)

    def reconcile(
        self, *, clock_allowance_ns: ClockAllowance | None = None
    ) -> ReconciliationReport:
        if self._sealed is not None:
            raise ValueError("Reconcile before seal")
        allowance = None
        if clock_allowance_ns is not None:
            if (
                not isinstance(clock_allowance_ns, ClockAllowance)
                or not isinstance(clock_allowance_ns.provenance, str)
                or not clock_allowance_ns.provenance
                or len(clock_allowance_ns.provenance.encode("utf-8"))
                > self.limits.max_status_utf8_bytes
                or any(
                    type(v) is not int or v < 0
                    for v in (clock_allowance_ns.wall_ns, clock_allowance_ns.cpu_ns)
                )
            ):
                self._fault("invalid_clock_allowance")
            else:
                allowance = asdict(clock_allowance_ns)
        spans = [s for s in self._spans[: self._span_count] if s is not None]
        if len(spans) != self._span_count:
            self._fault("missing_reserved_span")
        children = {}
        for row in spans:
            children.setdefault(row["parent_span_token"], []).append(row)
        reports = []
        for call in (c for c in self._calls[: self._call_count] if c is not None):
            rows = [s for s in spans if s["call_seq"] == call["call_seq"]]
            end_faults = call["fault_count_at_end"]
            faulted = (self._fault_count if end_faults is None else end_faults) > call[
                "fault_count_at_begin"
            ]
            phases = []
            for row in rows:
                phase = {
                    "span_token": row["span_token"],
                    "span_id": row["span_id"],
                    "coverage": row["coverage"],
                }
                for clock in ("wall", "cpu"):
                    start, end = row[clock + "_start_ns"], row[clock + "_end_ns"]
                    inclusive = None if start is None or end is None else end - start
                    direct = children.get(row["span_token"], [])
                    complete = all(
                        c["coverage"] == "complete"
                        and c[clock + "_start_ns"] is not None
                        and c[clock + "_end_ns"] is not None
                        for c in direct
                    )
                    exclusive = (
                        inclusive
                        - sum(c[clock + "_end_ns"] - c[clock + "_start_ns"] for c in direct)
                        if inclusive is not None and complete and row["coverage"] == "complete"
                        else None
                    )
                    phase[clock + "_inclusive_ns"] = inclusive
                    phase[clock + "_exclusive_ns"] = exclusive
                    if exclusive is not None and exclusive < 0:
                        if allowance is None or exclusive < -allowance[clock + "_ns"]:
                            self._fault("unreconciled_negative_residual", row["span_token"])
                phases.append(phase)
            seen = {s["span_id"] for s in rows}
            catalog = (
                CONSTRUCTION_PARENTS
                if call["call_kind"] == "construction"
                else CLOCK_PROBE_PARENTS
                if call["call_kind"] == "clock_probe"
                else PREPARATION_PARENTS
            )
            reports.append(
                {
                    "call_seq": call["call_seq"],
                    "phases": phases,
                    "missing_phases": [
                        {
                            "span_id": name,
                            "coverage": "unavailable" if faulted else "not_reached",
                            "reason": "observer_fault" if faulted else "branch_not_executed",
                        }
                        for name in catalog
                        if name not in seen
                    ],
                }
            )
        self._reconciliation = {
            "structural_valid": not bool(self._fault_count),
            "clock_order_valid": self._clock_order_valid,
            "allowance_status": "approved" if allowance else "unresolved",
            "clock_allowance": allowance,
            "call_reports": reports,
            "first_fault": dict(self._first_fault),
        }
        return self._reconciliation

    def seal(
        self, *, legacy_result: Mapping[str, object] | None, termination: str
    ) -> FrozenSidecar:
        if self._sealed is not None:
            raise ValueError("Recorder already sealed")
        if self._reconciliation is None:
            raise ValueError("Reconciliation required before seal")
        if self._active is not None or self._stack:
            self._fault("worker_terminated_with_open_call")
        if (
            not isinstance(termination, str)
            or len(termination.encode("utf-8")) > self.limits.max_status_utf8_bytes
        ):
            self._fault("termination_status_capacity")
            termination = None
        raw = {} if legacy_result is None else legacy_result
        call_ids = {c["plan_id"] for c in self._calls[: self._call_count] if c is not None}
        plans = {}
        for plan in raw.get("plans", ()):
            plan_id = plan.get("plan_id")
            if plan_id in call_ids:
                if plan_id in plans:
                    self._fault("duplicate_legacy_plan_identity")
                plans[plan_id] = plan  # Borrow only; never copy numerical fields.
        handoffs = raw.get("handoffs", ())
        controls = raw.get("controls", ())
        outcomes, join_count = [], 0
        spans = [s for s in self._spans[: self._span_count] if s is not None]
        for call in (c for c in self._calls[: self._call_count] if c is not None):
            plan = plans.get(call["plan_id"], {})
            completed = plan.get("completed") is True or (
                call["call_kind"] == "startup"
                and plan.get("startup") is True
                and plan.get("success") is True
            )
            accepts, applications = [], []
            join_overflow = False
            for source, destination, field in (
                (handoffs, accepts, "time"),
                (controls, applications, "application_time"),
            ):
                for item in source:
                    if (
                        item.get("plan_id") != call["plan_id"]
                        or field not in item
                        or (field == "time" and item.get("accepted") is not True)
                    ):
                        continue
                    if join_count >= self.limits.max_span_records:
                        self._fault("outcome_join_capacity")
                        join_overflow = True
                        break
                    destination.append(item[field])
                    join_count += 1
            root = next(
                (
                    s
                    for s in spans
                    if s["call_seq"] == call["call_seq"] and s["span_id"] == "prepare_full"
                ),
                None,
            )
            row = {
                "call_seq": call["call_seq"],
                "plan_id": call["plan_id"],
                "scheduled_legacy_completion_sim_s": plan.get("completion_time"),
                "observed_completion_sim_s": plan.get("completion_time") if completed else None,
                "accepted_times_sim_s": accepts,
                "application_times_sim_s": applications,
                "outcome_join_incomplete": join_overflow,
                "physical_completion_censored": call["call_kind"] == "recurring" and not completed,
                "missing_completion_reason": None
                if completed
                else "not_observed_or_no_physical_population",
                "host_call_partial": call["wall_end_ns"] is None or call["cpu_end_ns"] is None,
                "application_permission_status": "not_implemented_or_unobserved",
            }
            for clock in ("wall", "cpu"):
                start, end = call[clock + "_start_ns"], call[clock + "_end_ns"]
                row["dispatch_envelope_" + clock + "_ns"] = (
                    None if start is None or end is None else end - start
                )
                a = None if root is None else root[clock + "_start_ns"]
                b = None if root is None else root[clock + "_end_ns"]
                row["full_prepare_" + clock + "_ns"] = None if a is None or b is None else b - a
                observed = [
                    s[clock + "_end_ns"]
                    for s in spans
                    if s["call_seq"] == call["call_seq"] and s[clock + "_end_ns"] is not None
                ]
                row[clock + "_observed_lower_bound_ns"] = (
                    max(observed) - a
                    if a is not None and observed and self._clock_order_valid
                    else None
                )
            legacy_wall = plan.get("planner_total_time")
            legacy_cpu = plan.get("planner_cpu_time")
            row["legacy_preparation_wall_s"], row["legacy_preparation_cpu_s"] = (
                legacy_wall,
                legacy_cpu,
            )
            for clock, old in (("wall", legacy_wall), ("cpu", legacy_cpu)):
                duration = row["full_prepare_" + clock + "_ns"]
                row["legacy_boundary_" + clock + "_delta_ns"] = (
                    duration - round(old * 1e9)
                    if duration is not None and old is not None
                    else None
                )
            release = call["release_sim_s"]
            for boundary in ("full_prepare", "dispatch_envelope"):
                duration = row[boundary + "_wall_ns"]
                value = (
                    release + duration / 1e9
                    if release is not None and duration is not None
                    else None
                )
                row["hypothetical_measured_" + boundary + "_completion_sim_s"] = value
                row["hypothetical_" + boundary + "_readiness_difference_s"] = (
                    value - plan["completion_time"]
                    if value is not None and "completion_time" in plan
                    else None
                )
            outcomes.append(row)
        # Sealing may discover an interruption or join overflow after reconciliation.
        self._reconciliation = dict(
            self._reconciliation,
            structural_valid=not bool(self._fault_count),
            first_fault=dict(self._first_fault),
        )
        payload = {
            "schema": "apex-profile1-sidecar/1.0.0",
            "schema_version": "1.0.0",
            "worker_identity": asdict(self.identity),
            "limits": asdict(self.limits),
            "calls": self._calls[: self._call_count],
            "spans": self._spans[: self._span_count],
            "first_fault": dict(self._first_fault),
            "fault_count": self._fault_count,
            "faults": [f for f in self._faults if f is not None],
            "diagnostic_overflow_count": max(0, self._fault_count - self.limits.max_fault_records),
            "observer_validity": "invalid"
            if self._fault_count
            else (
                "incomplete"
                if self._reconciliation["allowance_status"] == "unresolved"
                else "valid"
            ),
            "reconciliation": self._reconciliation,
            "termination": termination,
            "physical_outcomes": outcomes,
            "raw_not_returned": legacy_result is None,
            "open_span_tokens": [
                s["span_token"]
                for s in self._spans[: self._span_count]
                if s is not None and s["end_sequence"] is None
            ],
            "clock_publication_tail": (
                "unmeasured after final endpoint; no end-to-end software/physical latency claim"
            ),
            "dispatch_exclusions": (
                "estimator/release prologue before capture and final endpoint publication/return"
            ),
            "observer_cost": (
                "Independent B0/B1/B2 pairing required; residual is not pure observer overhead"
            ),
        }
        self._sealed = FrozenSidecar(_freeze(payload))
        return self._sealed


def write_sidecar(sidecar: FrozenSidecar, *, output_dir: Path) -> ExportReport:
    """Publish in an exclusively owned worker directory, without replacement, after measurement."""
    partial = output_dir / "preparation_sidecar.json.partial"
    target = output_dir / "preparation_sidecar.json"
    report = {
        "complete": False,
        "path": None,
        "partial_path": None,
        "sha256": None,
        "failure": None,
    }
    try:
        if (
            output_dir.is_symlink()
            or not output_dir.is_dir()
            or target.exists()
            or partial.exists()
        ):
            raise FileExistsError("Exclusive fresh sidecar destination required")
        value = _plain(sidecar.payload)
        limit = value["limits"]["max_serialized_bytes"]
        digest, count = hashlib.sha256(), 0
        with partial.open("xb") as stream:
            report["partial_path"] = str(partial)
            for chunk in json.JSONEncoder(
                allow_nan=False, sort_keys=True, separators=(",", ":")
            ).iterencode(value):
                data = chunk.encode("utf-8")
                if count + len(data) > limit:
                    raise ValueError("Serialized sidecar capacity exceeded")
                stream.write(data)
                digest.update(data)
                count += len(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Hard-link publication is atomic and refuses any existing target; no overwrite race.
        os.link(partial, target)
        report.update(complete=True, path=str(target), sha256=digest.hexdigest())
        partial.unlink()
        report["partial_path"] = None
    except Exception as error:
        report["complete"], report["sha256"] = False, None
        report["failure"] = type(error).__module__ + "." + type(error).__qualname__
    return report
