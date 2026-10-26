"""Immutable analysis contracts. Importing this module never imports numerical libraries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, Mapping, TypeVar

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    F64Vector = NDArray[np.float64]
    F64Matrix = NDArray[np.float64]
else:
    F64Vector = Any
    F64Matrix = Any
JsonValue = Any
Vec6 = tuple[float, float, float, float, float, float]
Vec2 = tuple[float, float]
T = TypeVar("T")
STATE_NAMES = ("vx", "vy", "r", "e_psi", "s_abs", "e_y")
INPUT_NAMES = ("delta", "a_cmd")
STATE_UNITS = ("m/s", "m/s", "rad/s", "rad", "m", "m")
INPUT_UNITS = ("rad", "m/s^2")
LATERAL = (5, 3, 1, 2)
SOURCE_REVISION = "e603672b209985f11ed26b6f44d3949ffd5675c5"
ASSIGNMENT_REVISION = "3898704102e7570bcaff9b1654b7b345db1f9b6f"
PERFORMANCE_REVISION = "48adbdf64d492592d15e23c917aca71fa58aa8a5"
MANIFEST_SHA256 = "5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf"


def _freeze_value(value):
    from collections.abc import Mapping as MappingABC
    from types import MappingProxyType

    if hasattr(value, "setflags") and hasattr(value, "copy"):
        owned = value.copy()
        owned.setflags(write=False)
        return owned
    if isinstance(value, MappingABC):
        return MappingProxyType({k: _freeze_value(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(v) for v in value)
    return value


def _freeze_record(record):
    from dataclasses import fields

    for field_info in fields(record):
        object.__setattr__(record, field_info.name, _freeze_value(getattr(record, field_info.name)))


class TupleRole(StrEnum):
    ACTUAL_HELD = "ACTUAL_HELD"
    PACKET_NOMINAL = "PACKET_NOMINAL"
    ORIGINAL_GAIN_GRID_SUPPORT = "ORIGINAL_GAIN_GRID_SUPPORT"


class CurvaturePolicy(StrEnum):
    FROZEN_EXOGENOUS = "FROZEN_EXOGENOUS"
    GEOMETRY_PROGRESS = "GEOMETRY_PROGRESS"


class MapId(StrEnum):
    C_FIXED = "C_FIXED"
    C_PHYSICAL = "C_PHYSICAL"
    D_TRACKER = "D_TRACKER"
    D_NMPC = "D_NMPC"
    D_PLANT_10 = "D_PLANT_10"
    D_PLANT_100 = "D_PLANT_100"


MAPS = {
    MapId.C_FIXED: (None, None),
    MapId.C_PHYSICAL: (None, None),
    MapId.D_TRACKER: (0.01, 2),
    MapId.D_NMPC: (0.1, 4),
    MapId.D_PLANT_10: (0.01, 2),
    MapId.D_PLANT_100: (0.1, 20),
}


class Method(StrEnum):
    ANALYTIC = "ANALYTIC"
    CASADI_AD = "CASADI_AD"
    INDEPENDENT_FD = "INDEPENDENT_FD"
    RK4_TANGENT = "RK4_TANGENT"


class QualificationStatus(StrEnum):
    QUALIFIED = "QUALIFIED"
    QUALIFIED_BRANCH_SPECIFIC = "QUALIFIED_BRANCH_SPECIFIC"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"


class OutcomeStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"
    FAILED_COMPARISON = "FAILED_COMPARISON"
    RESOURCE_CENSORED = "RESOURCE_CENSORED"
    NOT_EXECUTED = "NOT_EXECUTED"


@dataclass(frozen=True)
class Reason:
    code: str
    detail: str
    source_pointer: str | None = None
    observed: Any = None
    threshold: Any = None

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class Outcome(Generic[T]):
    status: OutcomeStatus
    reasons: tuple[Reason, ...] = ()
    value: T | None = None

    def unwrap(self) -> T:
        if self.status != OutcomeStatus.AVAILABLE or self.value is None:
            raise ValueError(
                "; ".join(r.code + ": " + r.detail for r in self.reasons) or self.status
            )
        return self.value

    @classmethod
    def available(cls, value: T) -> Outcome[T]:
        return cls(OutcomeStatus.AVAILABLE, (), value)

    @classmethod
    def unavailable(cls, code: str, detail: str) -> Outcome[T]:
        return cls(OutcomeStatus.UNAVAILABLE, (Reason(code, detail),))

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class FileBinding:
    path: str
    sha256: str
    json_pointer: str | None = None

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class InputSpec:
    repo_root: Path
    archive_root: Path
    assignment_root: Path
    expected_revision: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class CandidateBinding:
    candidate_id: str
    original_candidate_json: Mapping[str, JsonValue]
    candidate_object_canonical_sha256: str
    original_panel_sha256: str
    raw_state_row: int
    raw_control_row: int
    packet_id: int
    gain_index: int

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class VerifiedInputs:
    spec: InputSpec
    source_bindings: tuple[FileBinding, ...]
    candidates: tuple[CandidateBinding, ...]
    metrics: Mapping[str, JsonValue]

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class OperatingTuple:
    tuple_id: str
    candidate_id: str
    role: TupleRole
    x: Vec6
    u: Vec2
    time_s: float
    packet_id: int
    gain_index: int
    kappa_policy: CurvaturePolicy

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class BranchSpec:
    side: str = "SMOOTH"
    segment_index: int | None = None
    q_interval: tuple[float, float] | None = None
    s_interval: tuple[float, float] | None = None
    heading_lift_multiple_2pi: int = 0
    inversion_metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class DomainAudit:
    checks: tuple[Mapping[str, Any], ...] = ()
    all_source_checks_pass: bool = False
    strict_central_interior: bool = False
    minimum_reported_margins: Mapping[str, float | None] = field(default_factory=dict)
    missing: tuple[str, ...] = ()

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class ApplicabilityAudit:
    ideal_unsaturated_immediate_feedback_applicable: bool = False
    flags: tuple[str, ...] = ()
    previous_delta_rad: float | None = None
    pending_information_complete: bool = False
    nominal_actual_mismatch: Vec6 | None = None
    hybrid_event_map_available: bool = False

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class Qualification:
    status: QualificationStatus
    reasons: tuple[Reason, ...]
    tuple_id: str
    map_id: MapId
    branch: BranchSpec | None
    domain: DomainAudit | None
    applicability: ApplicabilityAudit

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class EvaluationKey:
    candidate_id: str
    tuple_id: str
    map_id: MapId
    curvature_policy: CurvaturePolicy
    source_binding_set_sha256: str
    gain_index: int
    branch: BranchSpec | None = None
    physical_interval: tuple[float, float] | None = None

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class Linearization:
    key: EvaluationKey
    A: F64Matrix
    B: F64Matrix
    state_names: tuple[str, ...] = STATE_NAMES
    input_names: tuple[str, ...] = INPUT_NAMES
    row_units: tuple[str, ...] = STATE_UNITS
    column_units: tuple[str, ...] = INPUT_UNITS
    method: Method = Method.ANALYTIC
    qualification: Qualification = None

    def __post_init__(self):
        if self.qualification is None:
            object.__setattr__(
                self,
                "qualification",
                Qualification(
                    QualificationStatus.UNAVAILABLE,
                    (
                        Reason(
                            "NOT_YET_QUALIFIED",
                            "Producer pair requires the separate reviewed qualification pipeline",
                        ),
                    ),
                    self.key.tuple_id,
                    self.key.map_id,
                    None,
                    None,
                    ApplicabilityAudit(),
                ),
            )
        if hasattr(self.A, "shape"):
            n, m = len(self.state_names), len(self.input_names)
            if (
                self.A.shape != (n, n)
                or self.B.shape != (n, m)
                or len(self.row_units) != n
                or len(self.column_units) != m
            ):
                raise ValueError("Linearization shape/order/unit metadata mismatch")
            if str(self.A.dtype) != "float64" or str(self.B.dtype) != "float64":
                raise ValueError("Linearization requires float64 buffers")
        # Own the buffers without importing a numerical library at module import.
        for name in ("A", "B"):
            source = getattr(self, name)
            if hasattr(source, "setflags"):
                owned = source.copy()
                owned.setflags(write=False)
                object.__setattr__(self, name, owned)


@dataclass(frozen=True)
class FrozenParameters:
    values: Mapping[str, Any]
    source_binding_set_sha256: str = ""

    def __post_init__(self):
        from types import MappingProxyType

        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def __getattr__(self, name):
        try:
            return self.values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


@dataclass(frozen=True)
class AuthorityInterval:
    start_s: float
    end_s: float
    expiry_s: float
    superseded_at_s: float | None
    packet_id: int
    origin: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class ArchivedPacket:
    raw_fields: Mapping[str, Any]
    timestamps_s: Any
    states: Any
    controls: Any
    gain_times_s: Any
    original_gains: Any
    curvatures: Any
    source_binding: FileBinding
    authority_intervals: tuple[AuthorityInterval, ...]

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class PendingRequest:
    requested_control: Vec2
    request_time_s: float
    application_due_s: float | None
    source_packet_id: int
    observed_applied_time_s: float | None
    completeness: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class CausalHistory:
    native_state: Vec6
    time_s: float
    held_control: Vec2
    held_source_packet_id: int
    last_application_time_s: float
    previous_applied_steering_rad: float
    pending_request: PendingRequest | None
    pending_information_complete: bool
    authority: AuthorityInterval
    codriver_request_rows: tuple[Mapping[str, Any], ...]
    reasons: tuple[Reason, ...] = ()

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class SourceBundle:
    root: Path
    parameters: Any
    plant: Any
    prediction: Any
    tracker_jacobian_builder: Any
    track: Any
    binding_set_sha256: str
    module_origin_paths: Mapping[str, Path]

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class GeometrySnapshot:
    q_knots: Any
    arc_knots_m: Any
    segment_coefficients: tuple[Any, ...]
    length_m: float
    q_from_s: Callable[[float], float]
    source_geometry_value: Callable[[float], float]
    source_binding_set_sha256: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class GeometryJet:
    s_abs_m: float
    track_s_m: float
    q: float
    segment_index: int
    kappa_1pm: float
    kappa_s_1pm2: float | None
    q_first_second_third_derivatives: tuple[tuple[float, float], ...]
    branch: BranchSpec
    qualification: QualificationStatus
    reasons: tuple[Reason, ...] = ()

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class HeadingChart:
    anchor_theta_rad: float
    lifted_endpoints_rad: tuple[float, ...]
    lift_multiples: tuple[int, ...]
    branch_resolved: bool

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class Scales:
    Dx_diagonal_SI: Any
    Du_diagonal_SI: Any
    tau_s: float = 1.0
    state_names: tuple[str, ...] = STATE_NAMES
    input_names: tuple[str, ...] = INPUT_NAMES

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class FDSteps:
    multipliers: tuple[float, float, float]
    state_scales_SI: Any
    input_scales_SI: Any

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class QualificationPolicy:
    plant_limits: Mapping[str, Any]
    NLP_limits: Mapping[str, Any]
    FD_criteria: Mapping[str, Any]
    geometry_criteria: Mapping[str, Any]
    allow_branch_specific: bool = False

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class StencilDomain:
    map_id: MapId
    tuple_id: str
    column_indices: tuple[int, ...]
    step_multipliers: tuple[float, ...]
    stage_states: tuple[Any, ...]
    stage_checks: tuple[DomainAudit, ...]
    branch: BranchSpec | None
    central_available: bool
    unavailable_columns: tuple[int, ...]

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class ForcePartials:
    forces_N: tuple[float, float]
    loads_N: tuple[float, float]
    slip_angles_rad: tuple[float, float]
    force_state_partials: Any
    force_input_partials: Any
    load_input_partials: Any
    sqrt_arguments_N2: tuple[float, float]

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class StepJet:
    value: Any
    Jx: Any
    Ju: Any
    stages: tuple[Any, ...]
    stage_domains: tuple[DomainAudit, ...] = ()

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class MapValue:
    value: Any
    stages: tuple[Any, ...]
    chart: HeadingChart | None = None

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class FDPair:
    pairs_per_step: tuple[Linearization, ...]
    steps: FDSteps
    stencil: StencilDomain
    method: Method = Method.INDEPENDENT_FD

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class SubsystemPair:
    parent_key: EvaluationKey
    subsystem: str
    A: Any
    B: Any
    state_names: tuple[str, ...]
    input_names: tuple[str, ...]
    omitted_couplings: tuple[Any, ...] = ()

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class NormalizedPair:
    dimensional: SubsystemPair
    A_scaled: Any
    B_scaled: Any
    scales: Scales
    normalization_case_id: str = "nominal"

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class ClosedLoopSample:
    key: EvaluationKey
    time_s: float
    next_time_s: float
    Acl: Any
    original_gain: Any
    original_gain_index: int
    authority_scope: str
    applicability: ApplicabilityAudit

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class IndexInterval:
    start_index_inclusive: int
    end_index_exclusive: int
    start_time_s: float
    end_time_s: float

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class ProductIntervals:
    ranges: tuple[IndexInterval, ...]
    requested_windows_s: tuple[float, ...]
    authority_scope: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class NominalSample:
    key: EvaluationKey
    time_s: float
    x: Any
    u: Any
    next_time_s: float
    next_x: Any
    original_gain: Any
    same_packet_through_endpoint: bool

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class MapSemantics:
    map_id: MapId
    dt_s: float | None
    substeps: int | None
    curvature_policy: CurvaturePolicy
    curvature_value: float | None
    chart: HeadingChart
    authority_scope: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class Budget:
    max_candidates: int = 12
    gain_samples_before_dedup: int = 960
    wall_s: int = 300
    rss_bytes: int = 1073741824
    output_bytes: int = 1073741824
    initial_free_bytes: int = 2147483648

    def __post_init__(self):
        _freeze_record(self)


@dataclass
class BudgetToken:
    deadline_monotonic: float
    gain_limit: int = 960
    reserved_gain_slots: int = 0

    def poll(self):
        from time import monotonic

        if monotonic() >= self.deadline_monotonic - 5:
            raise TimeoutError("RESOURCE_CENSORED: finalization reserve")

    def reserve(self, count):
        self.poll()
        if count < 0 or self.reserved_gain_slots + count > self.gain_limit:
            raise TimeoutError("RESOURCE_CENSORED: gain slots before dedup")
        self.reserved_gain_slots += count


@dataclass(frozen=True)
class ExecutionGrant:
    assignment_sha: str
    implementation_sha: str
    authorized_stage: Literal["L3"]
    test_paths: tuple[str, ...]
    host_seconds: int
    expiry_utc: str
    output_root: Path

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class BackendIdentity:
    name: str
    distribution_path: Path
    binary_sha256: str | None
    supported_control: str
    control_source_binding: FileBinding
    unknown_fields: tuple[str, ...] = ()

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class NativeSetup:
    requested_threads: int
    set_status: int
    observed_mode: str
    backend: BackendIdentity
    environment: Mapping[str, str]
    exact_active_thread_count_available: bool = False

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class GuardOwner:
    path: Path
    owner_pid: int | None
    owner_job_id: str | None
    mtime_ns: int
    state: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class ResourcePreflight:
    free_bytes: int
    available_memory_bytes: int | None
    competing_workers: tuple[str, ...]
    owned_measurement_guards: tuple[GuardOwner, ...]
    initial_process_inventory_sha256: str
    output_root: Path
    granted_allocation_s: int

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class FileReceipt:
    path: str
    sha256: str
    bytes: int
    complete_records: int
    truncated_tail_bytes: int = 0

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class SupervisorReport:
    worker_exit_code: int | None
    termination: str
    elapsed_wall_s: float
    peak_observed_worker_RSS_bytes: int
    hard_RSS_enforcement: bool
    monitoring_gap_max_s: float
    final_index: FileReceipt | None
    missing_result_ids: tuple[str, ...]

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class WorkerReport:
    job: str
    exit_code: int
    termination: str
    source_binding_set_sha256: str
    records_written: tuple[str, ...]
    missing_candidate_ids: tuple[str, ...]
    elapsed_wall_s: float

    def __post_init__(self):
        _freeze_record(self)


@dataclass(frozen=True)
class SchemaIssue:
    json_pointer: str
    keyword: str
    detail: str

    def __post_init__(self):
        _freeze_record(self)


@dataclass
class EvidenceWriter:
    root: Path
    schema_path: Path
    run_id: str
    bytes_written: int = 0
    receipts: tuple[FileReceipt, ...] = ()
    budget_token: BudgetToken | None = None


DerivativeCriteria = Mapping[str, Any]
GeometryCriteria = Mapping[str, Any]
RankCriteria = Mapping[str, Any]
PBHCriteria = Mapping[str, Any]
RiccatiCriteria = Mapping[str, Any]
GainCriteria = Mapping[str, Any]
ComparisonAudit = Mapping[str, Any]
ControllabilityAudit = Mapping[str, Any]
PBHAudit = Mapping[str, Any]
RiccatiAudit = Mapping[str, Any]
GainComparison = Mapping[str, Any]
ClosedLoopAudit = Mapping[str, Any]
ProductAudit = Mapping[str, Any]
DefectAudit = Mapping[str, Any]
RunIndex = Mapping[str, Any]
StreamKind = str
EvidenceRecord = Mapping[str, JsonValue]
Termination = str
ValueFunction = Callable[[Any, Any], Any]
PairFunction = Callable[[Any, Any], tuple[Any, Any]]
StageGuard = Callable[[Any, Any], Outcome[DomainAudit]]
StencilGuard = Callable[[OperatingTuple, MapId, FDSteps], Outcome[StencilDomain]]
