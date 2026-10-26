"""Immutable S1-A values. Research code; no physical safety claim.

All constructors reject mutable containers, unknown fields and implicit defaults.
Executable behavior has not been exercised under the code-creation assignment.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Generic, Literal, TypeVar, Union, get_args, get_origin, get_type_hints

WIRE_VERSION = "apex-s1-authority/0.2.0"
API_VERSION = "apex-s1a-python/0.1.0"
APPROVED_ACTIVATION_MATRIX_SHA256 = (
    "f731597911d54c1fd24d47daa29c9fe7dd64d94e59119159d0149f2a4823d61f"
)
Tick = int
SIValue = Decimal
State = Literal[
    "DISARMED",
    "NORMAL",
    "WARNING",
    "RECOVERY",
    "DECELERATING",
    "STOP_REQUESTED",
    "STOPPING",
    "STOPPED_LATCHED",
    "NO_VALID_POLICY",
]
FrozenJsonValue = Union[None, bool, int, Decimal, str, tuple["FrozenJsonValue", ...]]
FrozenJsonObject = tuple[tuple[str, FrozenJsonValue], ...]
T = TypeVar("T")
ENABLED = ("T01", "T02", "T03", "T06", "T09", "T11", "T13", "T14")
DISABLED = ("T04", "T05", "T07", "T08", "T10", "T12")
REASON_ORDER = (
    "STAGE_NOT_ENABLED",
    "SCHEMA_INVALID",
    "VERSION_UNSUPPORTED",
    "BATCH_INVALID",
    "CAUSALITY_INVALID",
    "IDENTITY_CONFLICT",
    "SESSION_MISMATCH",
    "REVOKED",
    "CANCELLED",
    "EPOCH_MISMATCH",
    "BARRIER_UNACKNOWLEDGED",
    "EXPIRED",
    "NOT_YET_VALID",
    "APPLICATION_DEADLINE_MISSED",
    "TIME_INVALID",
    "FAULT_LATCHED",
    "AUTHORIZATION_UNKNOWN",
    "TRANSITION_DISABLED",
    "RESET_NOT_ADMISSIBLE",
    "ESTIMATE_MISSING",
    "ESTIMATE_INVALID",
    "ESTIMATE_DEGRADED",
    "MAP_MISMATCH",
    "FRAME_MISMATCH",
    "CLOCK_UNKNOWN",
    "STALE_ESTIMATE",
    "UNCERTAINTY_UNKNOWN",
    "NO_NOMINAL_FRESHNESS_BOUND",
    "HEALTH_INVALID",
    "DOMAIN_UNKNOWN",
    "SEQUENCE_REORDERED",
    "PERSISTENCE_UNKNOWN",
    "NO_VALID_POLICY",
    "APPLICATION_UNKNOWN",
    "CANCEL_PENDING",
    "DUPLICATE_PRIOR_OUTCOME",
    "PROPOSAL_ONLY",
    "TOO_LATE",
    "OK",
)


def reasons(*codes: str) -> tuple[str, ...]:
    values = set(codes)
    if values - {"OK"}:
        values.discard("OK")
    return tuple(
        sorted(
            values,
            key=lambda s: (
                REASON_ORDER.index(s) if s in REASON_ORDER else len(REASON_ORDER),
                s.encode("utf-8"),
            ),
        )
    )


def _check(value, annotation, path):
    origin, args = get_origin(annotation), get_args(annotation)
    if annotation is T:
        if is_dataclass(value):
            if not value.__dataclass_params__.frozen:
                raise TypeError(path + ": frozen result required")
            for field in fields(value):
                _check(getattr(value, field.name), T, path + "." + field.name)
        elif type(value) is tuple:
            for item in value:
                _check(item, T, path)
        elif value is not None and type(value) not in (bool, int, str, Decimal):
            raise TypeError(path + ": immutable result required")
        elif type(value) is Decimal and not value.is_finite():
            raise ValueError(path + ": finite result required")
        return
    if origin in (Union, type(int | str)):
        for item in args:
            try:
                _check(value, item, path)
                return
            except (TypeError, ValueError):
                pass
        raise TypeError(path + ": incompatible union value")
    if origin is Literal:
        if not any(type(value) is type(v) and value == v for v in args):
            raise ValueError(path + ": invalid literal")
    elif origin is tuple:
        if type(value) is not tuple:
            raise TypeError(path + ": immutable tuple required")
        if len(args) == 2 and args[1] is Ellipsis:
            for item in value:
                _check(item, args[0], path)
        else:
            if len(value) != len(args):
                raise ValueError(path + ": tuple length")
            for item, hint in zip(value, args):
                _check(item, hint, path)
    elif annotation is Decimal:
        if type(value) is not Decimal or not value.is_finite():
            raise TypeError(path + ": finite exact Decimal required")
    elif annotation is int:
        if type(value) is not int:
            raise TypeError(path + ": integer excluding bool required")
    elif annotation is str:
        if type(value) is not str or not value:
            raise TypeError(path + ": nonempty string required")
    elif annotation is None or annotation is type(None):
        if value is not None:
            raise TypeError(path + ": null required")
    elif annotation is bool:
        if type(value) is not bool:
            raise TypeError(path + ": bool required")
    elif origin is not None and is_dataclass(origin):
        if not isinstance(value, origin):
            raise TypeError(path + ": record required")
    elif isinstance(annotation, type) and not isinstance(value, annotation):
        raise TypeError(path + ": wrong record type")


class _Record:
    __slots__ = ()

    def __post_init__(self):
        for name, hint in get_type_hints(type(self)).items():
            value = getattr(self, name)
            _check(value, hint, type(self).__name__ + "." + name)
            if type(value) is int and value < 0 and name != "offset_numerator":
                raise ValueError(name + ": negative integer")
            if name.endswith("sha256") and value is not None:
                if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                    raise ValueError(name + ": lowercase SHA256 required")
        _semantics(self)


def _semantics(v):
    name = type(v).__name__
    if name == "TickPeriod":
        if v.numerator <= 0 or v.denominator <= 0:
            raise ValueError("positive tick period required")
        f = Fraction(v.numerator, v.denominator)
        object.__setattr__(v, "numerator", f.numerator)
        object.__setattr__(v, "denominator", f.denominator)
    if name == "Configuration":
        if (
            v.contract_version != WIRE_VERSION
            or v.enabled_transition_ids != ENABLED
            or v.activation_matrix_sha256 != APPROVED_ACTIVATION_MATRIX_SHA256
        ):
            raise ValueError("unsupported contract or transition activation")
        for items, key in (
            (v.clock_mappings, "mapping_id"),
            (v.authorization_registry, "authorization_id"),
        ):
            if len({getattr(x, key) for x in items}) != len(items):
                raise ValueError("duplicate configuration identity")
    if name == "ClockMapping":
        if v.scale_numerator <= 0 or v.scale_denominator <= 0 or v.offset_denominator <= 0:
            raise ValueError("invalid affine mapping")
    for attr in ("valid_interval", "valid_source_interval", "requested_permission_interval_ticks"):
        if hasattr(v, attr):
            start, end = getattr(v, attr)
            if start < 0 or start >= end:
                raise ValueError(attr + ": empty or reversed")
    for attr in (
        "control_tick_bounds",
        "publication_latency_tick_bounds",
        "application_tick_bounds",
    ):
        if hasattr(v, attr) and getattr(v, attr) is not None:
            lo, hi = getattr(v, attr)
            if lo < 0 or lo > hi:
                raise ValueError(attr + ": invalid bounds")
    if name == "Uncertainty":
        if v.representation == "UNKNOWN" and not v.reason:
            raise ValueError("unknown uncertainty needs reason")
        if v.representation == "BOUNDED_SET" and not v.bounded_set_ref:
            raise ValueError("bounded set reference required")
        if v.representation == "COVARIANCE" and v.covariance_si is None:
            raise ValueError("covariance required")
    if name == "ClockStamp" and v.control_tick_bounds is None and not v.unknown_reason:
        raise ValueError("unknown clock needs reason")
    if name in ("Proposal", "Packet"):
        b = v.timestamp_control_tick_bounds
        if len(b) != len(v.timestamps_s) or len(b) < 2:
            raise ValueError("timestamp lengths")
        if any(lo < 0 or lo > hi for lo, hi in b) or any(x[1] >= y[0] for x, y in zip(b, b[1:])):
            raise ValueError("timestamp bounds must be strictly ordered")
        if any(x >= y for x, y in zip(v.timestamps_s, v.timestamps_s[1:])):
            raise ValueError("source timestamps must be strictly ordered")
        if v.authority_start_tick != b[0][1] or v.authority_end_tick != b[-1][0]:
            raise ValueError("authority interval must use actual timestamp bounds")
        if v.handoff_mode == "FIXED" and (
            v.fixed_deadline_tick is None or v.ready_tick > v.fixed_deadline_tick
        ):
            raise ValueError("fixed deadline missed")
        if name == "Packet" and (
            v.accepted_tick < v.ready_tick or v.accepted_tick >= v.authority_end_tick
        ):
            raise ValueError("packet acceptance chronology")
    if name in ("Evidence", "Permission") and v.valid_from_tick >= v.valid_until_tick:
        raise ValueError("empty validity interval")
    if (
        name == "Command"
        and not v.requested_application_tick <= v.latest_application_tick <= v.held_until_tick
    ):
        raise ValueError("command time ordering")
    if name == "Command":
        if v.mode == "NOMINAL" and v.source_packet_id is None:
            raise ValueError("nominal command requires source packet")
        if v.source_packet_id is None and v.nonpacket_reason is None:
            raise ValueError("nonpacket command requires explicit reason")
    if name == "FaultLatch":
        if v.first_detected_tick > v.last_observed_tick or (
            v.cleared_tick is not None and v.cleared_tick < v.last_observed_tick
        ):
            raise ValueError("fault chronology")
    if name == "EndpointObservation":
        if v.commit_tick is None and v.applied_control_si is not None:
            raise ValueError("applied control requires supplied commit observation")
    if name == "BarrierAck":
        if v.outcome == "UNKNOWN" and v.unknown_reason is None:
            raise ValueError("unknown barrier requires reason")
    if name == "Snapshot":
        for attr, key in (
            ("commands", "command_id"),
            ("permissions", "permission_id"),
            ("evidence", "evidence_id"),
            ("fault_latches", "fault_id"),
            ("event_ledger", "event_id"),
            ("sequence_floors", "producer_id"),
            ("event_high_watermarks", "producer_id"),
        ):
            items = getattr(v, attr)
            if len({getattr(x, key) for x in items}) != len(items):
                raise ValueError("duplicate " + attr)
        if v.held_observation is None and not v.held_unknown_reason:
            raise ValueError("unknown held input needs reason")
        if any(x.trace_sequence > v.last_trace_sequence for x in v.trace_ledger):
            raise ValueError("trace sequence exceeds persistence watermark")
    if name == "Reduction" and v.endpoint_outputs != ():
        raise ValueError("S1-A endpoint outputs must be empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class ClockStamp(_Record):
    clock_id: str
    clock_session_id: str
    source_tick: int
    mapping_id: str | None
    control_tick_bounds: tuple[int, int] | None
    unknown_reason: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class Uncertainty(_Record):
    representation: Literal["BOUNDED_SET", "COVARIANCE", "UNKNOWN"]
    bounded_set_ref: str | None
    covariance_si: (
        tuple[
            tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal],
            tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal],
            tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal],
            tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal],
            tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal],
            tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal],
        ]
        | None
    )
    interpretation_ref: str | None
    reason: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class Estimate(_Record):
    estimate_id: str
    state_si: tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal] | None
    capture: ClockStamp | None
    publication: ClockStamp | None
    receipt: ClockStamp
    quality: Literal["VALID", "DEGRADED", "INVALID", "MISSING"]
    frame_id: str | None
    map_id: str | None
    uncertainty: Uncertainty
    health_evidence_id: str | None
    publication_latency_tick_bounds: tuple[int, int] | None
    unknown_reason: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class Evidence(_Record):
    evidence_id: str
    kind: Literal[
        "NOMINAL",
        "CONTINUATION",
        "RECOVERY",
        "DECELERATION",
        "STOP",
        "REST_HOLD",
        "HEALTH",
        "REENTRY",
        "QUEUE_BARRIER",
        "FEASIBILITY",
        "ACCEPTANCE",
        "ACTUATOR_CONSTRAINTS",
        "SELECTION",
        "TRANSFER",
        "FAULT_CLEARANCE",
        "REAUTHORIZATION",
    ]
    result: Literal["SATISFIED", "VIOLATED", "UNKNOWN"]
    claim_scope: Literal["SYNTHETIC_ASSUMPTION"]
    policy_id: str | None
    estimate_id: str | None
    source_packet_id: str | None
    context_revision: str
    domain_ids: tuple[Literal["D_NOMINAL", "D_PACKET", "D_RECOVERY", "D_DECEL", "D_STOP"], ...]
    assumption_set_ref: str
    terminal_or_transfer_ref: str | None
    uncertainty_interpretation_ref: str | None
    fault_model_ref: str | None
    valid_from_tick: int
    valid_until_tick: int
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Packet(_Record):
    packet_id: str
    source_controller_id: str
    source_manifest_sha256: str
    timestamps_s: tuple[Decimal, ...]
    timestamp_control_tick_bounds: tuple[tuple[int, int], ...]
    clock_mapping_id: str
    ready_tick: int
    accepted_tick: int
    acceptance_id: str
    acceptance_evidence_id: str
    authority_start_tick: int
    authority_end_tick: int
    handoff_mode: Literal["VARIABLE", "FIXED"]
    fixed_deadline_tick: int | None
    frame_id: str
    map_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Command(_Record):
    command_id: str
    session_id: str
    producer_id: str
    sequence: int
    payload_sha256: str
    payload_utf8: str
    source_controller_id: str
    source_manifest_sha256: str
    source_packet_id: str | None
    nonpacket_reason: str | None
    policy_id: str
    mode: Literal["NOMINAL", "RECOVERY", "DECELERATION", "STOP"]
    generation_epoch: int
    generated: ClockStamp
    estimate_id: str
    requested_application_tick: int
    latest_application_tick: int
    held_until_tick: int
    requested_control_si: tuple[Decimal, Decimal]


@dataclass(frozen=True, slots=True, kw_only=True)
class Permission(_Record):
    permission_id: str
    command_id: str
    session_id: str
    source_controller_id: str
    source_packet_id: str | None
    policy_id: str
    generation_epoch: int
    permission_epoch: int
    valid_from_tick: int
    valid_until_tick: int
    latest_application_tick: int
    held_until_tick: int
    estimate_id: str
    evidence_ids: tuple[str, ...]
    reauthorization_of_permission_id: str | None
    transition_id: str | None
    claim_scope: Literal["LOGICAL_PERMISSION_ONLY"]


@dataclass(frozen=True, slots=True, kw_only=True)
class Cancellation(_Record):
    cancellation_id: str
    session_id: str
    command_id: str
    permission_id: str
    requested_tick: int
    endpoint_delivery_tick: int | None
    ack_id: str | None
    outcome: Literal["REQUESTED", "SIMULATED_CANCELLED", "TOO_LATE", "UNKNOWN"]
    unknown_reason: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class EndpointObservation(_Record):
    ack_id: str
    endpoint_session_id: str
    command_id: str
    permission_id: str
    installed_epoch: int
    endpoint_sequence: int
    receipt_tick: int
    decision_tick: int
    commit_tick: int | None
    ack_observed_tick: int | None
    outcome: Literal["SIMULATED_APPLIED", "SIMULATED_CANCELLED", "REJECTED", "TOO_LATE", "UNKNOWN"]
    applied_control_si: tuple[Decimal, Decimal] | None
    held_until_tick: int | None
    physical_feedback: None
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class BarrierAck(_Record):
    ack_id: str
    barrier_id: str
    endpoint_session_id: str
    control_session_id: str
    installed_epoch: int
    endpoint_delivery_tick: int
    installation_tick: int | None
    ack_observed_tick: int
    queue_cleared: bool
    outcome: Literal["INSTALLED", "REJECTED", "UNKNOWN"]
    unknown_reason: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class FaultLatch(_Record):
    fault_id: str
    reason: str
    first_detected_tick: int
    last_observed_tick: int
    latched: Literal[True]
    cleared_tick: int | None
    clearance_evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Snapshot(_Record):
    schema_version: Literal["apex-s1-authority/0.2.0"]
    state: Literal[
        "DISARMED",
        "NORMAL",
        "WARNING",
        "RECOVERY",
        "DECELERATING",
        "STOP_REQUESTED",
        "STOPPING",
        "STOPPED_LATCHED",
        "NO_VALID_POLICY",
    ]
    control_session_id: str
    current_tick: int
    desired_epoch: int
    endpoint_installed_epoch: int | None
    endpoint_session_id: str | None
    epoch_barrier_ack_id: str | None
    active_packet: Packet | None
    active_policy_id: str | None
    proposals: tuple[Proposal, ...]
    accepted_packet_history: tuple[Packet, ...]
    cancellation_history: tuple[Cancellation, ...]
    acknowledgement_ledger: tuple[EndpointObservation, ...]
    barrier_acknowledgement_ledger: tuple[BarrierAck, ...]
    latest_estimate: Estimate | None
    evidence: tuple[Evidence, ...]
    permissions: tuple[Permission, ...]
    revoked_permission_ids: tuple[str, ...]
    commands: tuple[Command, ...]
    pending_command_ids: tuple[str, ...]
    held_observation: EndpointObservation | None
    held_unknown_reason: str | None
    fault_latches: tuple[FaultLatch, ...]
    sequence_floors: tuple[SequenceFloor, ...]
    command_ledger: tuple[CommandLedgerEntry, ...]
    event_high_watermarks: tuple[ProducerWatermark, ...]
    last_trace_sequence: int
    persistence_revision: str
    event_ledger: tuple[EventLedgerEntry, ...]
    operation_ledger: tuple[OperationLedgerEntry, ...]
    configuration_sha256: str
    prepared_barrier_ids: tuple[str, ...]
    trace_ledger: tuple[Trace, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Proposal(_Record):
    packet_id: str
    source_controller_id: str
    source_manifest_sha256: str
    timestamps_s: tuple[Decimal, ...]
    timestamp_control_tick_bounds: tuple[tuple[int, int], ...]
    clock_mapping_id: str
    ready_tick: int
    authority_start_tick: int
    authority_end_tick: int
    handoff_mode: Literal["VARIABLE", "FIXED"]
    fixed_deadline_tick: int | None
    frame_id: str
    map_id: str
    feasibility_evidence_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Trace(_Record):
    trace_sequence: int
    at_tick: int
    phase: int
    microstep: int
    event_id: str
    causal_parent_ids: tuple[str, ...]
    stage: Literal["S1-A"]
    state_before: str
    state_after: str
    transition_path: tuple[str, ...]
    control_session_id: str
    desired_epoch: int
    endpoint_installed_epoch: int | None
    source_packet_id: str | None
    command_id: str | None
    permission_id: str | None
    estimate_id: str | None
    evidence_ids: tuple[str, ...]
    decision: Literal[
        "ACCEPT",
        "REJECT",
        "REPLAY_PRIOR_OUTCOME",
        "REVOKE",
        "REQUEST_CANCEL",
        "OBSERVE",
        "NO_CHANGE",
    ]
    reason_codes: tuple[str, ...]
    granted_permission_ids: tuple[str, ...]
    revoked_permission_ids: tuple[str, ...]
    fault_ids: tuple[str, ...]
    endpoint_observation: EndpointObservation | None
    unknowns: tuple[UnknownField, ...]
    physical_actuation_claim: Literal["NOT_OBSERVED_NOT_VALIDATED"]
    decision_scope: Literal["HOST_LOGICAL", "SUPPLIED_OBSERVATION"]
    denial: Denial | None
    transition_records: tuple[TransitionRecord, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Configuration(_Record):
    configuration_id: str
    tick_period_s: TickPeriod
    control_clock_id: str
    expected_frame_id: str
    expected_map_id: str
    nominal_max_estimate_age_ticks: int | None
    continuation_policy_id: str | None
    warning_policy_evidence_id: str | None
    reentry_policy_evidence_id: str | None
    claim_scope: Literal["SYNTHETIC_PROTOCOL_ONLY"]
    enabled_transition_ids: tuple[str, ...]
    clock_mappings: tuple[ClockMapping, ...]
    authorization_registry: tuple[AuthorizationAssumption, ...]
    contract_version: str
    activation_matrix_sha256: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ClockMapping(_Record):
    mapping_id: str
    source_clock_id: str
    source_session_id: str
    control_clock_id: str
    scale_numerator: int
    scale_denominator: int
    offset_numerator: int
    offset_denominator: int
    lower_error_ticks: Tick
    upper_error_ticks: Tick
    valid_source_interval: tuple[Tick, Tick]
    assumption_ref: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthorizationAssumption(_Record):
    authorization_id: str
    producer_id: str
    allowed_event_kinds: tuple[str, ...]
    valid_interval: tuple[Tick, Tick]
    claim_scope: Literal["SYNTHETIC_ASSUMPTION"]


@dataclass(frozen=True, slots=True, kw_only=True)
class EventLedgerEntry(_Record):
    event_id: str
    producer_id: str
    producer_sequence: Tick
    payload_sha256: str
    original_trace_sequences: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationLedgerEntry(_Record):
    operation_kind: str
    operation_key: tuple[str, ...]
    content_sha256: str
    result_trace_sequences: tuple[int, ...]
    permission_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class TransitionRecord(_Record):
    transition_id: str
    state_before: State
    state_after: State
    at_tick: Tick
    cause_event_id: str
    evidence_ids: tuple[str, ...]
    revoked_permission_ids: tuple[str, ...]
    fault_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Denial(_Record):
    reason_codes: tuple[str, ...]
    denied_operation_key: tuple[str, ...]
    unknowns: tuple[UnknownField, ...]
    permission_created: Literal[False]


@dataclass(frozen=True, slots=True, kw_only=True)
class SealedBatch(_Record):
    batch_id: str
    at_tick: Tick
    events: tuple[Event, ...]
    configuration_sha256: str
    initial_snapshot_sha256: str
    canonical_input_sha256: str


@dataclass(frozen=True, slots=True, kw_only=True)
class InputError(_Record):
    path: str
    reason_code: str
    message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DecodeSuccess(_Record, Generic[T]):
    value: T


@dataclass(frozen=True, slots=True, kw_only=True)
class DecodeFailure(_Record):
    errors: tuple[InputError, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Reduction(_Record):
    snapshot: Snapshot
    traces: tuple[Trace, ...]
    transitions: tuple[TransitionRecord, ...]
    denials: tuple[Denial, ...]
    cancellation_intents: tuple[Cancellation, ...]
    endpoint_outputs: tuple[()] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class RestartInput(_Record):
    event_id: str
    at_tick: Tick
    boot_control_session_id: str
    endpoint_session_id: str
    saved_snapshot_sha256: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class BoundSuccess(_Record):
    lower: Tick
    upper: Tick
    mapping_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class BoundFailure(_Record):
    reason_codes: tuple[str, ...]
    unknowns: tuple[UnknownField, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Event(_Record):
    event_id: str
    producer_id: str
    producer_sequence: Tick
    at_tick: Tick
    causal_parent_ids: tuple[str, ...]
    kind: str
    payload: EventPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class PermissionRequest(_Record):
    command: Command
    permission_id: str
    supersedes_permission_id: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class UnknownField(_Record):
    field: str
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SequenceFloor(_Record):
    producer_id: str
    sequence: Tick


@dataclass(frozen=True, slots=True, kw_only=True)
class ProducerWatermark(_Record):
    producer_id: str
    sequence: Tick


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLedgerEntry(_Record):
    command_id: str
    producer_id: str
    sequence: Tick
    payload_sha256: str
    first_decision_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class TickPeriod(_Record):
    numerator: int
    denominator: int


@dataclass(frozen=True, slots=True, kw_only=True)
class AdvancePayload(_Record):
    target_tick: int


@dataclass(frozen=True, slots=True, kw_only=True)
class EmergencyPayload(_Record):
    fault_id: str
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class RevokeRequestPayload(_Record):
    new_epoch: int
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EpochInstallPayload(_Record):
    new_epoch: int
    target_control_session_id: str
    endpoint_session_id: str
    barrier_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ArmRequestPayload(_Record):
    operator_authorization_id: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class RenewalWarningPayload(_Record):
    evidence_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ReentryRequestPayload(_Record):
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ResetRequestPayload(_Record):
    operator_authorization_id: str
    new_session_id: str
    queue_barrier_evidence_id: str
    clearance_evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicySelectPayload(_Record):
    policy_id: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ApplicationCheckPayload(_Record):
    permission_id: str
    command_id: str
    application_tick_bounds: tuple[int, int]
    hold_end_tick: int


@dataclass(frozen=True, slots=True, kw_only=True)
class EndpointCommitPayload(_Record):
    permission_id: str
    command_id: str
    application_tick_bounds: tuple[int, int]
    hold_end_tick: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ReauthorizePayload(_Record):
    command_id: str
    prior_permission_id: str
    new_permission_id: str
    transition_id: str
    evidence_ids: tuple[str, ...]
    requested_permission_interval_ticks: tuple[Tick, Tick]


@dataclass(frozen=True, slots=True, kw_only=True)
class RestartPayload(_Record):
    snapshot_revision: str | None
    endpoint_session_id: str
    restored_latch_ids: tuple[str, ...]
    integrity_evidence_id: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class WarningClear(_Record):
    evidence_ids: tuple[str, ...]
    acceptance_id: str


EventPayload = (
    Estimate
    | Evidence
    | Proposal
    | Packet
    | Command
    | PermissionRequest
    | EndpointObservation
    | BarrierAck
    | Permission
    | AdvancePayload
    | EmergencyPayload
    | RevokeRequestPayload
    | EpochInstallPayload
    | Cancellation
    | ArmRequestPayload
    | RenewalWarningPayload
    | ReentryRequestPayload
    | ResetRequestPayload
    | PolicySelectPayload
    | ApplicationCheckPayload
    | EndpointCommitPayload
    | ReauthorizePayload
    | RestartPayload
    | WarningClear
)

PAYLOAD_TYPES = {
    "ESTIMATE_OBSERVED": Estimate,
    "EVIDENCE_OBSERVED": Evidence,
    "PROPOSAL_READY": Proposal,
    "AUTHORITY_ACCEPT": Packet,
    "COMMAND_SUBMIT": Command,
    "PERMISSION_REQUEST": PermissionRequest,
    "ENDPOINT_OBSERVATION": EndpointObservation,
    "BARRIER_ACK_OBSERVED": BarrierAck,
    "COMMAND_DELIVER": Command,
    "PERMISSION_DELIVER": Permission,
    "ENDPOINT_ESTIMATE_DELIVER": Estimate,
    "ENDPOINT_EVIDENCE_DELIVER": Evidence,
    "ADVANCE": AdvancePayload,
    "EMERGENCY": EmergencyPayload,
    "REVOKE_REQUEST": RevokeRequestPayload,
    "EPOCH_INSTALL": EpochInstallPayload,
    "CANCEL_REQUEST": Cancellation,
    "CANCEL_DELIVER": Cancellation,
    "ARM_REQUEST": ArmRequestPayload,
    "RENEWAL_WARNING": RenewalWarningPayload,
    "REENTRY_REQUEST": ReentryRequestPayload,
    "RESET_REQUEST": ResetRequestPayload,
    "POLICY_SELECT": PolicySelectPayload,
    "APPLICATION_CHECK": ApplicationCheckPayload,
    "ENDPOINT_COMMIT": EndpointCommitPayload,
    "REAUTHORIZE": ReauthorizePayload,
    "RESTART": RestartPayload,
    "WARNING_CLEAR": WarningClear,
}
