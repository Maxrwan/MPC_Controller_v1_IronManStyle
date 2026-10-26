"""L3 entry only. No numerical import, backend probe or model construction at module import."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Literal, Sequence

from .contracts import (
    SOURCE_REVISION,
    BackendIdentity,
    Budget,
    BudgetToken,
    EvidenceWriter,
    ExecutionGrant,
    FileBinding,
    InputSpec,
    OutcomeStatus,
    VerifiedInputs,
    WorkerReport,
)
from .evidence import STREAMS, _matrix, append_record
from .guards import check_execution_grant, configure_native_single
from .inputs import _git, _read, verify_inputs


def _json(value):
    if hasattr(value, "tolist"):
        return _json(value.tolist())
    from collections.abc import Mapping

    if isinstance(value, Mapping):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _context(binding_id, point=None, mid=None, scope="NONE", branch=None):
    return {
        "candidate_id": point.candidate_id if point else "NOT_APPLICABLE",
        "tuple_id": point.tuple_id if point else "NOT_APPLICABLE",
        "tuple_role": point.role.value if point else "NOT_APPLICABLE",
        "map_id": mid.value if mid else "NOT_APPLICABLE",
        "curvature_policy": point.kappa_policy.value if point else "NOT_APPLICABLE",
        "time_s": point.time_s if point else None,
        "packet_id": point.packet_id if point else None,
        "gain_index": point.gain_index if point else None,
        "branch": branch.side
        if branch and branch.side in ("SMOOTH", "LEFT", "RIGHT", "UNRESOLVED")
        else "NOT_APPLICABLE",
        "authority_scope": scope,
        "source_binding_set_sha256": binding_id,
    }


def _mat(value, field, pair=None):
    from .contracts import INPUT_NAMES, INPUT_UNITS, STATE_NAMES, STATE_UNITS, MapId

    r, c = value.shape
    scaled = "scaled" in field or field in (
        "entry_errors_per_step",
        "PBH_matrix_real",
        "PBH_matrix_imag",
    )
    if pair is not None:
        names = tuple(pair.state_names)
        units = tuple(STATE_UNITS[STATE_NAMES.index(n)] for n in names)
        controls = tuple(pair.input_names)
        cu = tuple(INPUT_UNITS[INPUT_NAMES.index(n)] for n in controls)
        key = pair.key if hasattr(pair, "key") else pair.parent_key
        continuous = key.map_id in (MapId.C_FIXED, MapId.C_PHYSICAL)
    else:
        names = tuple(str(i) for i in range(r))
        units = ("1",) * r
        controls = tuple(str(i) for i in range(c))
        cu = ("1",) * c
        continuous = False
    rn, cn = list(names), list(names)
    ru = list(units)
    cols = list(units)
    if field in ("B", "B_dimensional", "B_scaled", "original_feedback"):
        if field == "original_feedback":
            rn = list(controls)
            cn = list(names)
            ru = list(cu)
            cols = list(units)
        else:
            cn = list(controls)
            cols = list(cu)
    elif field.startswith("controllability"):
        cn = [controls[j % len(controls)] + f":A^{j // len(controls)}" for j in range(c)]
        cols = [
            cu[j % len(cu)] + (f"*s^{j // len(cu) + 1}" if continuous else "") for j in range(c)
        ]
    elif field in ("terminal_P", "terminal_Q", "terminal_R"):
        if field == "terminal_R":
            rn = cn = ["delta"]
            ru = ["1/rad"]
            cols = ["rad"]
        else:
            rn = cn = ["e_y", "e_psi", "vy", "r"]
            u = ["m", "rad", "m/s", "rad/s"]
            ru = ["1/(" + a + ")" for a in u]
            cols = u
    elif field in ("original_gains", "recomputed_gains", "gain_abs_errors"):
        rn = [str(i) for i in range(r)]
        cn = ["e_y", "e_psi", "vy", "r"]
        ru = ["rad"] * r
        cols = ["m", "rad", "m/s", "rad/s"]
    elif field in ("PBH_matrix_real", "PBH_matrix_imag", "entry_errors_per_step"):
        rn = [str(i) for i in range(r)]
        cn = [str(i) for i in range(c)]
        ru = ["1"] * r
        cols = ["1"] * c
    if continuous and field in ("A", "A_dimensional", "B", "B_dimensional"):
        ru = [u + "/s" for u in ru]
    if scaled:
        ru = ["1"] * r
        cols = ["1"] * c
    if len(rn) != r:
        rn = [str(i) for i in range(r)]
        ru = ["1"] * r
    if len(cn) != c:
        cn = [str(i) for i in range(c)]
        cols = ["1"] * c
    return _matrix(value, rn, cn, ru, cols, "SCALED" if scaled else "DIMENSIONAL")


def _payload(kind, data, schema, pair=None):
    """Only declared schema fields are emitted; missing fields fail instead of being invented."""
    result = dict(data)
    for field, value in tuple(result.items()):
        if hasattr(value, "ndim") and value.ndim == 2:
            result[field] = _mat(value, field, pair)
        elif field == "entry_errors_per_step":
            result[field] = [_mat(v, field, pair) for v in value]
        elif field == "omitted_coupling_blocks":
            from .contracts import INPUT_NAMES, INPUT_UNITS, STATE_NAMES, STATE_UNITS, MapId

            key = pair.parent_key
            continuous = key.map_id in (MapId.C_FIXED, MapId.C_PHYSICAL)
            ru = [
                STATE_UNITS[STATE_NAMES.index(n)] + ("/s" if continuous else "")
                for n in pair.state_names
            ]
            other_x = [n for n in STATE_NAMES if n not in pair.state_names]
            other_u = [n for n in INPUT_NAMES if n not in pair.input_names]
            result[field] = [
                _matrix(
                    value[0],
                    list(pair.state_names),
                    other_x,
                    ru,
                    [STATE_UNITS[STATE_NAMES.index(n)] for n in other_x],
                ),
                _matrix(
                    value[1],
                    list(pair.state_names),
                    other_u,
                    ru,
                    [INPUT_UNITS[INPUT_NAMES.index(n)] for n in other_u],
                ),
            ]
        elif field == "PBH_modes":
            result[field] = [
                {
                    **m,
                    "PBH_matrix_real": _mat(m["PBH_matrix_real"], "PBH_matrix_real", pair),
                    "PBH_matrix_imag": _mat(m["PBH_matrix_imag"], "PBH_matrix_imag", pair),
                }
                for m in value
            ]
    definitions = {
        "qualification": "qualification_data",
        "linearization": "linearization_data",
        "finite_difference": "fd_data",
        "linear_system": "linear_system_data",
        "riccati": "riccati_data",
        "closed_loop": "closed_loop_data",
        "product": "product_data",
        "defect": "defect_data",
        "coverage": "coverage_data",
        "event": "event_data",
        "environment": "environment_data",
        "manifest": "manifest_data",
        "resource": "resource_data",
        "index": "index_data",
    }
    required = schema["$defs"][definitions[kind]]["required"]
    return _json({name: result[name] for name in required})


class _GlobalIntegrityFailure(RuntimeError):
    """Common provenance/backend/evidence invalidity: never candidate-local."""

    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


class _EvidenceIntegrityFailure(_GlobalIntegrityFailure):
    pass


class _LocalScientificFailure(RuntimeError):
    def __init__(self, scope, stage, reasons, status="UNAVAILABLE"):
        super().__init__(
            stage
            + ": "
            + "; ".join(r.get("code", "UNKNOWN") + ": " + r.get("detail", "") for r in reasons)
        )
        self.scope, self.stage, self.reasons, self.status = scope, stage, tuple(reasons), status


def _reason_dict(reason):
    if hasattr(reason, "code"):
        return {
            "code": reason.code,
            "detail": reason.detail,
            "source_pointer": reason.source_pointer,
            "observed": _json(reason.observed),
            "threshold": _json(reason.threshold),
        }
    return dict(reason)


def _require_local(result, *, scope, stage):
    reasons = tuple(_reason_dict(r) for r in result.reasons)
    for reason in reasons:
        if reason["code"] in (
            "SOURCE_IDENTITY_FAILURE",
            "L3_AUTHORIZATION_REQUIRED",
            "NATIVE_SINGLE_UNQUALIFIED",
            "EVIDENCE_WRITE_FAILED",
        ):
            raise _GlobalIntegrityFailure(reason["code"], reason["detail"])
    if result.status == OutcomeStatus.AVAILABLE and result.value is not None:
        return result.value
    raise _LocalScientificFailure(
        scope,
        stage,
        reasons or ({"code": result.status.value, "detail": "Required result absent"},),
        result.status.value,
    )


def _require_global(result, stage):
    if result.status == OutcomeStatus.AVAILABLE and result.value is not None:
        return result.value
    raise _GlobalIntegrityFailure(
        "SOURCE_IDENTITY_FAILURE",
        stage + ": " + "; ".join(r.code + ": " + r.detail for r in result.reasons),
    )


def _append_or_stop(writer, kind, record):
    # Poll before the immutable evidence producer can collapse a timeout into Outcome.
    if writer.budget_token is not None:
        writer.budget_token.poll()
    result = append_record(writer, kind, record)
    if result.status != OutcomeStatus.AVAILABLE or result.value is None:
        writer._integrity_failed = True
        raise _EvidenceIntegrityFailure(
            "EVIDENCE_WRITE_FAILED", "; ".join(r.code + ": " + r.detail for r in result.reasons)
        )
    return result.value


def _run_independent(items, execute, on_local_failure, *, scope, budget, check_trust=None):
    """Single forward pass; no retries, substitutions, global catches or cached replacements."""
    for item in items:
        budget.poll()
        if check_trust is not None:
            check_trust()
        try:
            execute(item)
        except _LocalScientificFailure as exc:
            if exc.scope != scope:
                raise
            if check_trust is not None:
                check_trust()
            on_local_failure(item, exc)


def _trust_snapshot(inputs):
    rows = []
    for binding in inputs.source_bindings:
        root = (
            inputs.spec.archive_root
            if binding.path.startswith("results/")
            else inputs.spec.repo_root
        )
        path = (root / binding.path).resolve()
        if not path.is_relative_to(root.resolve()):
            raise _GlobalIntegrityFailure(
                "SOURCE_IDENTITY_FAILURE", "Binding escaped verified root"
            )
        try:
            st = path.stat()
        except OSError as exc:
            raise _GlobalIntegrityFailure("SOURCE_IDENTITY_FAILURE", str(exc)) from exc
        rows.append((path, (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)))
    return tuple(rows)


def _assert_common_trust(inputs, snapshot, native_receipt):
    if _git(inputs.spec.repo_root, "rev-parse", "HEAD") != inputs.spec.expected_revision or _git(
        inputs.spec.repo_root, "status", "--porcelain"
    ):
        raise _GlobalIntegrityFailure(
            "SOURCE_IDENTITY_FAILURE",
            "Reviewed checkout identity/cleanliness changed during execution",
        )
    for path, expected in snapshot:
        try:
            st = path.stat()
        except OSError as exc:
            raise _GlobalIntegrityFailure("SOURCE_IDENTITY_FAILURE", str(exc)) from exc
        if (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns) != expected:
            raise _GlobalIntegrityFailure(
                "SOURCE_IDENTITY_FAILURE", "Pinned input changed during execution: " + str(path)
            )
    if os.environ.get("CT1L_NATIVE_RECEIPT") != native_receipt:
        raise _GlobalIntegrityFailure(
            "NATIVE_SINGLE_UNQUALIFIED", "Common native setup receipt changed"
        )
    # Read the supported control after tests as well as before candidates; no reconfiguration.
    import ctypes

    try:
        library = ctypes.CDLL("/System/Library/Frameworks/Accelerate.framework/Accelerate")
        library.BLASGetThreading.restype = ctypes.c_uint
        mode = library.BLASGetThreading()
    except (OSError, AttributeError) as exc:
        raise _GlobalIntegrityFailure("NATIVE_SINGLE_UNQUALIFIED", str(exc)) from exc
    if mode != 1:
        raise _GlobalIntegrityFailure(
            "NATIVE_SINGLE_UNQUALIFIED", "Actual Accelerate mode no longer SINGLE"
        )


def _assert_workload_policy(inputs):
    from .closed_loop import (
        _PRODUCT_NORMALIZATION_IDS,
        _PRODUCT_PANEL_MAX_FACTORS,
        _PRODUCT_PANEL_MAX_INTERVALS,
        _PRODUCT_SENSITIVITY_COORDINATE,
        _PRODUCT_WINDOW_STEPS,
    )

    try:
        plan = _read(inputs.spec.assignment_root / "l2b_workload_plan.json")
    except (OSError, ValueError) as exc:
        raise _GlobalIntegrityFailure("WORKLOAD_POLICY_INTEGRITY", str(exc)) from exc
    expected = {
        "window_lengths_gain_steps": list(_PRODUCT_WINDOW_STEPS),
        "maximum_factors": _PRODUCT_PANEL_MAX_FACTORS,
        "maximum_selected_intervals": _PRODUCT_PANEL_MAX_INTERVALS,
        "normalization_ids": list(_PRODUCT_NORMALIZATION_IDS),
        "sensitivity_coordinates": _PRODUCT_SENSITIVITY_COORDINATE,
    }
    if plan.get("runtime_constants") != expected:
        raise _GlobalIntegrityFailure(
            "WORKLOAD_POLICY_INTEGRITY",
            "Machine-readable reviewed plan does not match the coded deterministic panel",
        )
    if plan.get("execution_authorized") is not False:
        raise _GlobalIntegrityFailure(
            "WORKLOAD_POLICY_INTEGRITY", "This plan is not an execution grant"
        )
    return plan


def _assert_l3_test_selection(inputs, grant):
    import ast

    if any(os.environ.get(name) for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")):
        raise _GlobalIntegrityFailure(
            "L3_SELECTION_INTEGRITY",
            "Unreviewed pytest options/plugins may alter the exact prerequisite selection",
        )

    try:
        proposal = _read(inputs.spec.assignment_root / "l2b_l3_execution_plan.json")
    except (OSError, ValueError) as exc:
        raise _GlobalIntegrityFailure("L3_SELECTION_INTEGRITY", str(exc)) from exc
    expected = proposal["tests"]
    if tuple(grant.test_paths) != tuple(expected["paths_in_exact_proposed_order"]):
        raise _GlobalIntegrityFailure(
            "L3_SELECTION_INTEGRITY", "Grant does not match exact reviewed file order"
        )
    observed = []
    for path in grant.test_paths:
        tree = ast.parse((inputs.spec.repo_root / path).read_text(), filename=path)
        observed.extend(
            path + "::" + node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        )
    if observed != expected["node_selectors"]:
        raise _GlobalIntegrityFailure(
            "L3_SELECTION_INTEGRITY", "Frozen test-node declaration inventory changed"
        )
    return proposal


def _metadata_product_plans(packet, indices, anchor, history, candidate_id):
    from types import SimpleNamespace

    from .closed_loop import _product_selection

    design = tuple(
        SimpleNamespace(
            time_s=packet.gain_times_s[i],
            next_time_s=packet.gain_times_s[i] + 0.01,
            original_gain_index=i,
            authority_scope="DESIGN_CONDITIONAL",
        )
        for i in indices
        if packet.gain_times_s[i] + 0.01 <= packet.timestamps_s[-1] + 1e-10
    )
    observed = (
        ()
        if history is None
        else tuple(
            SimpleNamespace(
                time_s=x.time_s,
                next_time_s=x.next_time_s,
                original_gain_index=x.original_gain_index,
                authority_scope="OBSERVED_AUTHORITY",
            )
            for x in design
            if x.time_s >= anchor
            and x.time_s >= history.authority.start_s
            and x.next_time_s <= min(history.authority.end_s, history.authority.expiry_s)
        )
    )
    return {
        scope: _product_selection(seq, candidate_id, scope)
        for scope, seq in (("DESIGN_CONDITIONAL", design), ("OBSERVED_AUTHORITY", observed))
    }


def _missing_selected_products(plans, completed):
    """Missing selected endpoints only. Deliberately omitted exhaustive windows are separate."""
    from .closed_loop import _PRODUCT_NORMALIZATION_IDS

    missing = []
    for population, plan in plans.items():
        for subsystem in ("full", "lateral", "speed"):
            for norm_id in _PRODUCT_NORMALIZATION_IDS:
                for index, interval in enumerate(plan["intervals"]):
                    key = (population, subsystem, norm_id, index)
                    if key not in completed:
                        missing.append(
                            {
                                "population": population,
                                "subsystem": subsystem,
                                "normalization": norm_id,
                                "selected_interval_index": index,
                                "range": {
                                    "start_index_inclusive": interval.start_index_inclusive,
                                    "end_index_exclusive": interval.end_index_exclusive,
                                    "start_time_s": interval.start_time_s,
                                    "end_time_s": interval.end_time_s,
                                },
                            }
                        )
    return tuple(missing)


def execute_job(
    inputs: VerifiedInputs,
    grant: ExecutionGrant,
    budget: Budget,
    job: Literal["tests", "qualify-and-analyze"],
) -> WorkerReport:
    # No numerical import occurs without the exact on-disk Primary grant and owning supervisor.
    raw_path = os.environ.get("CT1L_GRANT_PATH")
    if not raw_path:
        raise PermissionError("Explicit L3 grant path absent")
    checked = check_execution_grant(Path(raw_path), inputs, budget)
    if checked.value != grant or not os.environ.get("CT1L_DEADLINE_MONOTONIC"):
        raise PermissionError("L3 grant/allocation mismatch")
    receipt = json.loads(os.environ.get("CT1L_NATIVE_RECEIPT", "{}"))
    if receipt.get("mode") != "SINGLE" or receipt.get("status") != 0:
        raise PermissionError("Actual native setup receipt absent")
    from importlib import metadata

    import numpy as np
    from threadpoolctl import threadpool_info

    from .analytic import continuous_pair
    from .closed_loop import (
        _forced_step,
        _product_normalizations,
        _product_selection,
        closed_loop_pair,
        nominal_defects,
        transition_products,
    )
    from .contracts import (
        INPUT_NAMES,
        INPUT_UNITS,
        MAPS,
        STATE_NAMES,
        STATE_UNITS,
        ClosedLoopSample,
        CurvaturePolicy,
        FDSteps,
        FrozenParameters,
        Linearization,
        MapId,
        MapSemantics,
        NominalSample,
        Outcome,
        ProductIntervals,
        QualificationPolicy,
        QualificationStatus,
        Scales,
        TupleRole,
    )
    from .crosscheck_numpy import crosscheck_f, crosscheck_rk4
    from .finite_difference import central_pair, compare_pairs, crosscheck_curvature_derivative
    from .geometry import (
        check_geometry_stencil,
        check_heading_chart,
        geometry_jet,
        snapshot_geometry,
    )
    from .inputs import (
        _sample,
        load_authority_and_command_history,
        load_candidate_tuples,
        load_original_packet,
    )
    from .linear_systems import (
        _default_scales,
        controllability_audit,
        extract_subsystem,
        stabilizability_audit,
    )
    from .qualification import _domain, qualify_point, qualify_stencil
    from .riccati import audit_packet_gains
    from .rk4 import compose_rk4
    from .source_adapter import (
        _binding_id,
        _curvature,
        _with_fixed_curvature,
        _with_packet,
        build_sources,
        original_tracker_jacobians,
        source_symbolic_pair,
        source_transition,
    )

    if job not in ("tests", "qualify-and-analyze"):
        raise ValueError("Unknown authorized job")
    started = time.monotonic()
    deadline = float(os.environ["CT1L_DEADLINE_MONOTONIC"])
    token = BudgetToken(deadline)
    binding_id = _binding_id(inputs)
    writer = EvidenceWriter(
        grant.output_root,
        inputs.spec.assignment_root / "scientific_evidence.schema.json",
        grant.output_root.name,
        budget_token=token,
    )
    schema = _read(writer.schema_path)
    record_ids = []
    coverage = []
    failures = []
    termination = "COMPLETE"
    gain_slots_evaluated = 0
    missing_products = []
    candidate_states = {}
    trust_stamp = None
    common_native_receipt = os.environ["CT1L_NATIVE_RECEIPT"]
    os.environ["CT1L_ARCHIVE_ROOT"] = str(inputs.spec.archive_root)
    bindings = [asdict(b) for b in inputs.source_bindings]

    def emit(
        kind,
        ident,
        data=None,
        point=None,
        mid=None,
        status="COMPUTED",
        scope="NONE",
        reasons=(),
        pair=None,
        branch=None,
    ):
        record = {
            "schema": "apex-ct1l-scientific-evidence/1.0.0",
            "record_type": kind,
            "record_id": writer.run_id + ":" + ident,
            "run_id": writer.run_id,
            "status": status,
            "context": _context(binding_id, point, mid, scope, branch),
            "source_bindings": bindings,
            "reasons": [_reason_dict(r) for r in reasons],
            "data": _payload(kind, data, schema, pair) if data is not None else None,
        }
        _append_or_stop(writer, kind, record)
        record_ids.append(record["record_id"])
        return record["record_id"]

    def event(name, detail, point=None, mid=None, scope="NONE"):
        emit(
            "event",
            "event:" + str(len(record_ids)),
            {
                "event": name,
                "clock_s": time.monotonic() - started,
                "related_record_ids": [],
                "termination_reason": detail,
                "retention_action": "Retain all completed and failed observations",
            },
            point,
            mid,
            scope=scope,
        )

    def emit_pair(p, point, mid, label, qualification, bound_source):
        p = replace(
            p, key=replace(p.key, source_binding_set_sha256=binding_id), qualification=qualification
        )
        value = _require_local(
            source_transition(bound_source, point, mid), scope="MAP", stage="SOURCE_MAP_VALUE"
        )
        emit(
            "linearization",
            label,
            {
                "A": p.A,
                "B": p.B,
                "method": p.method.value,
                "stage_states": [list(s) for s in value.stages] if value else [],
                "chart_lift": list(value.chart.lift_multiples) if value and value.chart else [],
                "substeps": MAPS[mid][1],
                "dt_s": MAPS[mid][0],
                "qualified_domain": qualification.status.value,
            },
            point,
            mid,
            pair=p,
            branch=qualification.branch,
        )
        return p

    try:
        emit(
            "manifest",
            "manifest",
            {
                "run_id": writer.run_id,
                "authorized_stage": "L3",
                "assignment_sha": grant.assignment_sha,
                "implementation_sha": grant.implementation_sha,
                "source_bindings": bindings,
                "allowlisted_test_paths": list(grant.test_paths),
                "budget_wall_s": budget.wall_s,
                "max_candidates": 12,
                "gain_sample_ceiling_before_dedup": 960,
                "streams": list(STREAMS.values()),
            },
        )
        policy_document = _assert_workload_policy(inputs)
        event(
            "L2B_WORKLOAD_POLICY",
            json.dumps(
                {
                    "rule_id": policy_document["selection"]["rule_id"],
                    "product_records_ceiling": 4608,
                    "normalization_populations": 4,
                    "exhaustive_verification": False,
                },
                allow_nan=False,
            ),
        )
        config = getattr(np.__config__, "CONFIG", {})
        if "accelerate" not in json.dumps(config, default=str).lower():
            raise _GlobalIntegrityFailure(
                "NATIVE_SINGLE_UNQUALIFIED", "Actual NumPy backend is not confirmed Accelerate"
            )
        l3_proposal = _assert_l3_test_selection(inputs, grant)
        if binding_id != l3_proposal["archive"]["source_binding_set_sha256"]:
            raise _GlobalIntegrityFailure(
                "SOURCE_IDENTITY_FAILURE",
                "Current source/evidence binding set does not match exact L3 proposal",
            )
        locked = l3_proposal["numerical_environment"]["locked_versions"]
        packages = []
        for name in ("numpy", "scipy", "casadi", "psutil", "pytest", "threadpoolctl", "PyYAML"):
            try:
                observed_version = metadata.version(name)
            except metadata.PackageNotFoundError as exc:
                raise _GlobalIntegrityFailure("ENVIRONMENT_IDENTITY_FAILURE", str(exc)) from exc
            if observed_version != locked[name.lower()]:
                raise _GlobalIntegrityFailure(
                    "ENVIRONMENT_IDENTITY_FAILURE",
                    "Installed "
                    + name
                    + " does not match reviewed unchanged uv.lock: "
                    + observed_version,
                )
            packages.append({"name": name, "version": observed_version, "binary_sha256": None})
        emit(
            "environment",
            "environment",
            {
                "implementation_sha": grant.implementation_sha,
                "assignment_sha": grant.assignment_sha,
                "source_revision": SOURCE_REVISION,
                "python_binary": sys.executable,
                "python_version": sys.version,
                "platform": sys.platform,
                "package_versions": packages,
                "backend_identity": json.dumps(
                    {"numpy_config": config, "threadpoolctl": threadpool_info()}, default=str
                ),
                "backend_setup_receipt": os.environ["CT1L_NATIVE_RECEIPT"],
                "unknown_binary_identities": [
                    "historical IPOPT plugin/linear solver build; not constructed",
                    "package binary digests not qualified by version metadata",
                ],
                "source_bindings": bindings,
            },
        )
        # Exact prerequisite suite selection; no collection occurs before this explicit L3 path.
        token.poll()
        os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        import pytest

        test_status = pytest.main(
            [
                "-q",
                "--confcutdir=" + str(inputs.spec.repo_root / "tests/ct1l"),
                "--basetemp=" + str(writer.root / "pytest-tmp"),
                "-o",
                "cache_dir=" + str(writer.root / "pytest-cache"),
                "--junitxml=" + str(writer.root / "tests.xml"),
                *grant.test_paths,
            ]
        )
        event("PREREQUISITE_TESTS", str(test_status))
        if test_status != 0:
            raise _GlobalIntegrityFailure(
                "PREREQUISITE_TEST_FAILURE", "Prerequisite failure; no candidate analysis or retry"
            )
        if job == "tests":
            termination = "MISSING_COVERAGE"
        else:
            _require_global(verify_inputs(inputs.spec), "POST_TEST_INPUT_REVALIDATION")
            trust_stamp = _trust_snapshot(inputs)
            _assert_common_trust(inputs, trust_stamp, common_native_receipt)
            bundle = _require_global(build_sources(inputs), "COMMON_SOURCE_ADAPTER")
            snapshot = _require_global(snapshot_geometry(bundle), "COMMON_GEOMETRY_REPRESENTATION")
            parameters = FrozenParameters(asdict(bundle.parameters), binding_id)
            policy_data = _read(inputs.spec.assignment_root / "point_qualification_contract.json")[
                "domain_thresholds"
            ]
            policy = QualificationPolicy(
                policy_data["NumPy_physical"],
                policy_data["NLP_preview_comparison"],
                inputs.metrics["finite_difference"],
                inputs.metrics["finite_difference"]["geometry_kappa_s"],
            )
            steps = FDSteps(
                (2e-5, 1e-5, 5e-6), np.array([0.5, 0.5, 1, 0.1, 0.75, 0.1]), np.array([0.2, 1.0])
            )
            scales = Scales(steps.state_scales_SI, steps.input_scales_SI)

            def numeric_call(function, *args, scope, **kwargs):
                try:
                    return function(*args, **kwargs)
                except np.linalg.LinAlgError as exc:
                    raise _LocalScientificFailure(
                        scope,
                        function.__name__,
                        ({"code": "LOCAL_LINALG_FAILURE", "detail": str(exc)},),
                    ) from exc

            def analyze_candidate(candidate):
                nonlocal gain_slots_evaluated
                token.poll()
                completed = []
                feedback_requests = []
                missing = []
                statuses = []
                row = {
                    "candidate_id": candidate.candidate_id,
                    "qualification": "NOT_EXECUTED",
                    "reasons": [],
                    "completed_record_ids": completed,
                    "missing_map_ids": [
                        role + ":" + m.value for role in ("actual", "nominal") for m in MapId
                    ],
                }
                coverage.append(row)
                state = {
                    "row": row,
                    "plans": None,
                    "completed_products": set(),
                    "point": None,
                    "local_failures": 0,
                }
                candidate_states[candidate.candidate_id] = state
                event("CANDIDATE_BEGIN", json.dumps({"candidate_id": candidate.candidate_id}))
                tuples = load_candidate_tuples(inputs, candidate.candidate_id)
                _require_local(tuples, scope="CANDIDATE", stage="CAUSAL_TUPLE")
                packet = _require_local(
                    load_original_packet(inputs, candidate.packet_id),
                    scope="CANDIDATE",
                    stage="load_original_packet",
                )
                history_result = load_authority_and_command_history(inputs, candidate.candidate_id)
                history = history_result.value
                bound = _with_packet(bundle, packet)
                local_defects = {}
                state["point"] = tuples.value[1]
                indices = tuple(range(candidate.gain_index, len(packet.gain_times_s)))
                if len(indices) > 80:
                    raise _GlobalIntegrityFailure(
                        "GAIN_ALLOCATION_INTEGRITY", "Original suffix exceeds reviewed cap"
                    )
                state["plans"] = _metadata_product_plans(
                    packet, indices, tuples.value[1].time_s, history, candidate.candidate_id
                )

                def analyze_map(item):
                    role_point, mid = item
                    token.poll()
                    physical = mid in (MapId.C_PHYSICAL, MapId.D_PLANT_10, MapId.D_PLANT_100)
                    point = replace(
                        role_point,
                        kappa_policy=CurvaturePolicy.GEOMETRY_PROGRESS
                        if physical
                        else CurvaturePolicy.FROZEN_EXOGENOUS,
                    )
                    qualification = qualify_point(inputs, bound, point, mid, policy)
                    statuses.append(qualification.status.value)
                    ident = point.tuple_id + ":" + mid.value
                    actual, nominal = tuples.value
                    emit(
                        "qualification",
                        ident + ":qualification",
                        {
                            "qualification": qualification.status.value,
                            "actual_state": list(actual.x),
                            "held_control": list(actual.u),
                            "nominal_state": list(nominal.x),
                            "nominal_control": list(nominal.u),
                            "original_gain": list(packet.original_gains[point.gain_index]),
                            "domain_checks": list(qualification.domain.checks)
                            if qualification.domain
                            else [],
                            "applicability_flags": list(qualification.applicability.flags),
                            "missing_fields": [r.code for r in qualification.reasons],
                        },
                        point,
                        mid,
                        branch=qualification.branch,
                    )
                    if qualification.status != QualificationStatus.QUALIFIED:
                        missing.append(mid.value)
                        emit(
                            "linearization",
                            ident + ":unavailable",
                            point=point,
                            mid=mid,
                            status="UNAVAILABLE",
                            reasons=qualification.reasons,
                        )
                        raise _LocalScientificFailure(
                            "MAP",
                            "POINT_QUALIFICATION",
                            tuple(_reason_dict(r) for r in qualification.reasons)
                            or (
                                {
                                    "code": "POINT_UNAVAILABLE",
                                    "detail": "No approved differentiable domain",
                                },
                            ),
                            qualification.status.value,
                        )
                    stencil = qualify_stencil(inputs, bound, point, mid, steps)
                    if stencil.value is None:
                        missing.append(mid.value)
                        emit(
                            "linearization",
                            ident + ":stencil_unavailable",
                            point=point,
                            mid=mid,
                            status="UNAVAILABLE",
                            reasons=stencil.reasons,
                        )
                        raise _LocalScientificFailure(
                            "MAP", "FD_STENCIL", tuple(_reason_dict(r) for r in stencil.reasons)
                        )
                    fixed_k = _curvature(bound, point)
                    jet = _require_local(
                        geometry_jet(snapshot, point.x[4]), scope="MAP", stage="geometry_jet"
                    )
                    if not physical:
                        jet = replace(jet, kappa_1pm=fixed_k, kappa_s_1pm2=0.0)
                    if physical:
                        geometry_stencil = check_geometry_stencil(
                            snapshot,
                            tuple(
                                (
                                    point.x[4] + sign * h
                                    for h in (2e-05, 1e-05, 5e-06)
                                    for sign in (-1, 1)
                                )
                            ),
                            branch=jet.branch,
                        )
                        if geometry_stencil.value is None:
                            missing.append(mid.value)
                            emit(
                                "linearization",
                                ident + ":geometry_FD_unavailable",
                                point=point,
                                mid=mid,
                                status="UNAVAILABLE",
                                reasons=geometry_stencil.reasons,
                            )
                            raise _LocalScientificFailure(
                                "MAP",
                                "CURVATURE_STENCIL",
                                tuple(_reason_dict(r) for r in geometry_stencil.reasons),
                            )
                        geometry_check = crosscheck_curvature_derivative(
                            jet,
                            snapshot.source_geometry_value,
                            inputs.metrics["finite_difference"]["geometry_kappa_s"],
                        )
                        if (
                            geometry_check.value is None
                            or geometry_check.value["comparison"] != "PASS"
                        ):
                            raise _LocalScientificFailure(
                                "MAP",
                                "CURVATURE_COMPARISON",
                                (
                                    {
                                        "code": "CURVATURE_DERIVATIVE_FAILED",
                                        "detail": json.dumps(_json(geometry_check.value)),
                                    },
                                ),
                                "FAILED_COMPARISON",
                            )

                    def f(x, u):
                        return crosscheck_f(
                            x,
                            u,
                            parameters,
                            curvature=float(bundle.track.sample(float(x[4])).curvature)
                            if physical
                            else fixed_k,
                        )

                    def df(x, u):
                        local = replace(point, x=tuple(x), u=tuple(u))
                        j = (
                            _require_local(
                                geometry_jet(snapshot, float(x[4])),
                                scope="MAP",
                                stage="geometry_jet",
                            )
                            if physical
                            else jet
                        )
                        q = _require_local(
                            continuous_pair(local, parameters, j, policy=point.kappa_policy),
                            scope="MAP",
                            stage="continuous_pair",
                        )
                        return (q.A, q.B)

                    if MAPS[mid][0] is None:
                        manual = _require_local(
                            continuous_pair(point, parameters, jet, policy=point.kappa_policy),
                            scope="MAP",
                            stage="continuous_pair",
                        )
                        manual = replace(manual, key=replace(manual.key, map_id=mid))
                        value_function = f
                    else:
                        dt, n = MAPS[mid]
                        manual = _require_local(
                            compose_rk4(
                                point,
                                dt_s=dt,
                                substeps=n,
                                f=f,
                                df=df,
                                stage_guard=lambda x, u: Outcome.available(_domain(bundle, x, u)),
                            ),
                            scope="MAP",
                            stage="compose_rk4",
                        )
                        value_function = lambda x, u, dt=dt, n=n: (
                            crosscheck_rk4(
                                x,
                                u,
                                parameters,
                                dt_s=dt,
                                substeps=n,
                                curvature=None if physical else fixed_k,
                                geometry_value=snapshot.source_geometry_value if physical else None,
                            ).value
                        )
                    primary = emit_pair(manual, point, mid, ident + ":manual", qualification, bound)
                    references = [(ident + ":manual", primary)]
                    if not physical:
                        ad = _require_local(
                            source_symbolic_pair(bound, point, mid),
                            scope="MAP",
                            stage="source_symbolic_pair",
                        )
                        ad = emit_pair(ad, point, mid, ident + ":AD", qualification, bound)
                        references.append((ident + ":AD", ad))
                        primary = ad
                    fd = _require_local(
                        central_pair(
                            point, value_function, mid, scales, steps, lambda p, m, s: stencil
                        ),
                        scope="MAP",
                        stage="central_pair",
                    )
                    for j, p in enumerate(fd.pairs_per_step):
                        emit_pair(p, point, mid, ident + ":FD:" + str(j), qualification, bound)
                    fd = replace(
                        fd,
                        pairs_per_step=tuple(
                            (
                                replace(p, key=replace(p.key, source_binding_set_sha256=binding_id))
                                for p in fd.pairs_per_step
                            )
                        ),
                    )
                    fd_bundle = bound if physical else _with_fixed_curvature(bound, fixed_k)
                    source_fd = _require_local(
                        central_pair(
                            point,
                            lambda x, u: (
                                _require_local(
                                    source_transition(
                                        fd_bundle, replace(point, x=tuple(x), u=tuple(u)), mid
                                    ),
                                    scope="MAP",
                                    stage="source_transition",
                                ).value
                            ),
                            mid,
                            scales,
                            steps,
                            lambda p, m, s: stencil,
                        ),
                        scope="MAP",
                        stage="central_pair",
                    )
                    source_fd = replace(
                        source_fd,
                        pairs_per_step=tuple(
                            (
                                replace(p, key=replace(p.key, source_binding_set_sha256=binding_id))
                                for p in source_fd.pairs_per_step
                            )
                        ),
                    )
                    for j, p in enumerate(source_fd.pairs_per_step):
                        emit_pair(
                            p, point, mid, ident + ":source_FD:" + str(j), qualification, bound
                        )
                    for reference_name, reference in references:
                        for fd_name, estimate in (("FD", fd), ("source_FD", source_fd)):
                            token.poll()
                            comp = compare_pairs(
                                reference, estimate, inputs.metrics["finite_difference"]
                            )
                            if comp["comparison"] == "INCOMPARABLE_METHOD_SEMANTICS":
                                raise _GlobalIntegrityFailure(
                                    "COMPARISON_KEY_INTEGRITY",
                                    "Matched methods unexpectedly have different provenance/map keys",
                                )
                            emit(
                                "finite_difference",
                                reference_name + ":" + fd_name + ":comparison",
                                {
                                    "reference_matrix_id": writer.run_id + ":" + reference_name,
                                    "independent_matrix_id": writer.run_id
                                    + ":"
                                    + ident
                                    + ":"
                                    + fd_name
                                    + ":2",
                                    "column_steps": [
                                        float(m * s)
                                        for m in steps.multipliers
                                        for s in tuple(steps.state_scales_SI)
                                        + tuple(steps.input_scales_SI)
                                    ],
                                    "entry_errors_per_step": comp["entry_errors_per_step"],
                                    "max_abs_error": comp["max_abs_error"],
                                    "max_relative_error": comp["max_relative_error"],
                                    "two_smallest_step_agreement": comp[
                                        "two_smallest_step_agreement"
                                    ],
                                    "comparison": comp["comparison"],
                                    "invalid_columns": [],
                                },
                                point,
                                mid,
                                status="COMPUTED"
                                if comp["comparison"] == "PASS"
                                else "FAILED_COMPARISON",
                                pair=reference,
                            )
                            if comp["comparison"] != "PASS":
                                raise _LocalScientificFailure(
                                    "MAP",
                                    "DERIVATIVE_COMPARISON",
                                    (
                                        {
                                            "code": "DERIVATIVE_COMPARISON_FAILED",
                                            "detail": "Computed comparison retained, no tolerance change",
                                        },
                                    ),
                                    "FAILED_COMPARISON",
                                )
                    local_defect = None
                    if point.role == TupleRole.PACKET_NOMINAL and MAPS[mid][0] is not None:
                        dt, n = MAPS[mid]
                        end_time = point.time_s + dt
                        if end_time <= packet.timestamps_s[-1] + 1e-10:
                            next_x = _sample(packet, end_time)[0]
                            nominal_sample = NominalSample(
                                primary.key,
                                point.time_s,
                                np.asarray(point.x),
                                np.asarray(point.u),
                                end_time,
                                np.asarray(next_x),
                                np.asarray(packet.original_gains[point.gain_index]),
                                True,
                            )
                            semantics = MapSemantics(
                                mid,
                                dt,
                                n,
                                point.kappa_policy,
                                None if physical else fixed_k,
                                _require_local(
                                    check_heading_chart(point.x[3], (next_x[3],)),
                                    scope="MAP",
                                    stage="check_heading_chart",
                                ),
                                "DESIGN_SUPPORT_ONLY",
                            )
                            outcome = nominal_defects(
                                (nominal_sample,),
                                lambda x, u: (
                                    _require_local(
                                        source_transition(
                                            fd_bundle, replace(point, x=tuple(x), u=tuple(u)), mid
                                        ),
                                        scope="MAP",
                                        stage="source_transition",
                                    ).value
                                ),
                                semantics,
                            )
                            if outcome.value is None:
                                _require_local(outcome, scope="MAP", stage="NOMINAL_DEFECT")
                            if outcome.value:
                                local_defect = dict(outcome.value["defects"][0])
                                local_defect["discontinuity_flags"] = list(
                                    local_defect["discontinuity_flags"]
                                )
                                crossed = any(
                                    (
                                        point.time_s + 1e-10 < t < end_time - 1e-10
                                        for t in packet.timestamps_s[1:-1]
                                    )
                                )
                                if crossed:
                                    local_defect["discontinuity_flags"].append(
                                        "NOMINAL_CONTROL_PREVIEW_NODE_INSIDE_HELD_INPUT_MAP"
                                    )
                                local_defect["interpretation"] = (
                                    "Declared held-input map versus same-packet interpolated endpoint; includes preview/geometry and interpolation inconsistency. Any crossed nominal input node is explicit, never an observed event map."
                                )
                                local_defects[mid] = local_defect
                                emit(
                                    "defect",
                                    ident + ":local_nominal_defect",
                                    local_defect,
                                    point,
                                    mid,
                                    scope="DESIGN_SUPPORT_ONLY",
                                )
                        else:
                            emit(
                                "defect",
                                ident + ":local_nominal_defect",
                                point=point,
                                mid=mid,
                                status="UNAVAILABLE",
                                scope="DESIGN_SUPPORT_ONLY",
                                reasons=(
                                    {
                                        "code": "REFERENCE_ENDPOINT_UNAVAILABLE",
                                        "detail": "No packet extrapolation across expiry",
                                        "source_pointer": None,
                                        "observed": None,
                                        "threshold": None,
                                    },
                                ),
                            )
                    for subsystem in ("full", "lateral", "speed"):
                        token.poll()
                        sub = extract_subsystem(primary, subsystem)
                        ca = _require_local(
                            numeric_call(
                                controllability_audit, sub, inputs.metrics["rank"], scope="MAP"
                            ),
                            scope="MAP",
                            stage="numeric_call",
                        )
                        pb = _require_local(
                            numeric_call(
                                stabilizability_audit, sub, inputs.metrics["PBH"], scope="MAP"
                            ),
                            scope="MAP",
                            stage="numeric_call",
                        )
                        event(
                            "SCOPED_SCHUR_RANK_CROSSCHECK",
                            ident
                            + ":"
                            + subsystem
                            + " "
                            + json.dumps(_json(pb["rank_revealing_crosscheck"]), allow_nan=False),
                        )
                        norm = ca["normalized_pair"]
                        emit(
                            "linear_system",
                            ident + ":" + subsystem,
                            {
                                "subsystem": subsystem,
                                "A_dimensional": sub.A,
                                "B_dimensional": sub.B,
                                "A_scaled": norm.A_scaled,
                                "B_scaled": norm.B_scaled,
                                "controllability_dimensional": ca["C_dimensional"],
                                "controllability_scaled": ca["C_scaled"],
                                "spectra_and_scale_cases": ca["scale_cases"],
                                "PBH_modes": pb["modes"],
                                "stabilizability": pb["stabilizability"],
                                "omitted_coupling_blocks": list(sub.omitted_couplings),
                            },
                            point,
                            mid,
                            pair=sub,
                        )
                    if mid in (MapId.D_TRACKER, MapId.D_PLANT_10):
                        feedback_requests.append((point, primary, qualification, local_defect))
                    completed.extend(
                        (r for r in record_ids if r.startswith(writer.run_id + ":" + ident + ":"))
                    )
                    role_tag = "actual" if role_point.role == TupleRole.ACTUAL_HELD else "nominal"
                    row["missing_map_ids"].remove(role_tag + ":" + mid.value)

                def on_map_failure(item, exc):
                    _assert_common_trust(inputs, trust_stamp, common_native_receipt)
                    role_point, mid = item
                    role_point = replace(
                        role_point,
                        kappa_policy=CurvaturePolicy.GEOMETRY_PROGRESS
                        if mid in (MapId.C_PHYSICAL, MapId.D_PLANT_10, MapId.D_PLANT_100)
                        else CurvaturePolicy.FROZEN_EXOGENOUS,
                    )
                    row["reasons"].append(exc.stage + ":" + exc.status)
                    state["local_failures"] += 1
                    event(
                        "L2B_LOCAL_MAP_FAILURE",
                        json.dumps(
                            {
                                "classification": "MAP_LOCAL",
                                "candidate_id": candidate.candidate_id,
                                "stage": exc.stage,
                                "status": exc.status,
                                "reasons": exc.reasons,
                                "retry": False,
                                "replacement": False,
                            },
                            allow_nan=False,
                        ),
                        role_point,
                        mid,
                    )

                _run_independent(
                    ((role, mid) for role in tuples.value for mid in MapId),
                    analyze_map,
                    on_map_failure,
                    scope="MAP",
                    budget=token,
                )
                for frozen_id, physical_id in (
                    (MapId.D_TRACKER, MapId.D_PLANT_10),
                    (MapId.D_NMPC, MapId.D_PLANT_100),
                ):
                    if frozen_id in local_defects and physical_id in local_defects:
                        frozen_d = np.asarray(local_defects[frozen_id]["d_dimensional"])
                        physical_d = np.asarray(local_defects[physical_id]["d_dimensional"])
                        event(
                            "NOMINAL_MAP_DIFFERENCE",
                            json.dumps(
                                {
                                    "candidate_id": candidate.candidate_id,
                                    "definition": "physical defect minus fixed-preview defect at identical nominal x/u/endpoint; model difference, not parity failure",
                                    "frozen_map": frozen_id.value,
                                    "physical_map": physical_id.value,
                                    "difference_SI": (physical_d - frozen_d).tolist(),
                                    "difference_scaled": (
                                        (physical_d - frozen_d) / steps.state_scales_SI
                                    ).tolist(),
                                    "state_order": list(STATE_NAMES),
                                    "state_units": list(STATE_UNITS),
                                },
                                allow_nan=False,
                            ),
                        )
                indices = tuple(range(candidate.gain_index, len(packet.gain_times_s)))
                if len(indices) > 80:
                    raise _GlobalIntegrityFailure(
                        "GAIN_ALLOCATION_INTEGRITY", "Original suffix exceeds reviewed cap"
                    )
                token.reserve(len(indices))
                support = []
                for i in indices:
                    token.poll()
                    p = _require_local(
                        original_tracker_jacobians(bundle, packet, (i,)),
                        scope="CANDIDATE",
                        stage="original_tracker_jacobians",
                    )[0]
                    gain_slots_evaluated += 1
                    p = replace(
                        p,
                        key=replace(
                            p.key,
                            candidate_id=candidate.candidate_id,
                            tuple_id=candidate.candidate_id + ":gain:" + str(i),
                        ),
                    )
                    t = packet.gain_times_s[i]
                    x, u, g, gi = _sample(packet, t)
                    q = replace(
                        tuples.value[1],
                        tuple_id=p.key.tuple_id,
                        role=TupleRole.ORIGINAL_GAIN_GRID_SUPPORT,
                        x=x,
                        u=u,
                        time_s=t,
                        gain_index=i,
                    )
                    qualification = qualify_point(inputs, bound, q, MapId.D_TRACKER, policy)
                    if qualification.status != QualificationStatus.QUALIFIED:
                        emit(
                            "linearization",
                            q.tuple_id + ":source_support",
                            point=q,
                            mid=MapId.D_TRACKER,
                            status="UNAVAILABLE",
                            scope="DESIGN_SUPPORT_ONLY",
                            reasons=qualification.reasons,
                        )
                        raise _LocalScientificFailure(
                            "CANDIDATE",
                            "ORIGINAL_GAIN_SUPPORT",
                            tuple((_reason_dict(r) for r in qualification.reasons))
                            or (
                                {
                                    "code": "GAIN_SUPPORT_UNAVAILABLE",
                                    "detail": "Source support has no approved central domain",
                                },
                            ),
                        )
                    p = replace(p, qualification=qualification)
                    emit(
                        "linearization",
                        q.tuple_id + ":source_support",
                        {
                            "A": p.A,
                            "B": p.B,
                            "method": p.method.value,
                            "stage_states": [],
                            "chart_lift": [],
                            "substeps": 2,
                            "dt_s": 0.01,
                            "qualified_domain": qualification.status.value,
                        },
                        q,
                        MapId.D_TRACKER,
                        scope="DESIGN_SUPPORT_ONLY",
                        pair=p,
                    )
                    support.append(p)
                gains = numeric_call(
                    audit_packet_gains,
                    packet,
                    tuple(support),
                    inputs.metrics["Riccati"],
                    scope="CANDIDATE",
                )
                emit(
                    "riccati",
                    candidate.candidate_id + ":gain_audit",
                    gains.value,
                    tuples.value[1],
                    MapId.D_TRACKER,
                    status="COMPUTED"
                    if gains.status == OutcomeStatus.AVAILABLE
                    else "FAILED_COMPARISON"
                    if gains.value is not None
                    else "UNAVAILABLE",
                    scope="DESIGN_SUPPORT_ONLY",
                    reasons=gains.reasons,
                )
                _require_local(gains, scope="CANDIDATE", stage="RICCATI_REPRODUCTION")
                for point, primary, qualification, local_defect in feedback_requests:
                    ident = point.tuple_id + ":" + point.kappa_policy.value
                    for subsystem in ("full", "lateral", "speed"):
                        token.poll()
                        sub = extract_subsystem(primary, subsystem)
                        feedback_app = qualification.applicability
                        if local_defect is not None and any(
                            (v != 0 for v in local_defect["d_dimensional"])
                        ):
                            feedback_app = replace(
                                feedback_app,
                                ideal_unsaturated_immediate_feedback_applicable=False,
                                flags=feedback_app.flags + ("NONZERO_NOMINAL_DEFECT",),
                            )
                        projected = Linearization(
                            primary.key,
                            sub.A,
                            sub.B,
                            sub.state_names,
                            sub.input_names,
                            tuple((STATE_UNITS[STATE_NAMES.index(n)] for n in sub.state_names)),
                            tuple((INPUT_UNITS[INPUT_NAMES.index(n)] for n in sub.input_names)),
                            qualification=qualification,
                        )
                        ideal = numeric_call(
                            closed_loop_pair,
                            projected,
                            np.asarray(packet.original_gains[point.gain_index]),
                            feedback_app,
                            scope="CANDIDATE",
                        )
                        emit(
                            "closed_loop",
                            ident + ":" + subsystem + ":conditional",
                            ideal.value,
                            point,
                            primary.key.map_id,
                            status="COMPUTED" if ideal.value is not None else "UNAVAILABLE",
                            scope="DESIGN_CONDITIONAL",
                            reasons=ideal.reasons,
                            pair=sub,
                        )
                        _require_local(
                            ideal, scope="CANDIDATE", stage="ORIGINAL_GAIN_CONDITIONAL_FEEDBACK"
                        )
                design = {s: [] for s in ("full", "lateral", "speed")}
                observed = {s: [] for s in design}
                nominal_point = tuples.value[1]
                forced = np.zeros(6)
                for p in support:
                    token.poll()
                    i = p.key.gain_index
                    t = packet.gain_times_s[i]
                    x, u, g, gi = _sample(packet, t)
                    q = replace(
                        nominal_point,
                        tuple_id=p.key.tuple_id,
                        role=TupleRole.ORIGINAL_GAIN_GRID_SUPPORT,
                        x=x,
                        u=u,
                        time_s=t,
                        gain_index=i,
                    )
                    qualification = p.qualification
                    full_acl = None
                    for subsystem in ("full", "lateral", "speed"):
                        sub = extract_subsystem(p, subsystem)
                        lp = Linearization(
                            p.key,
                            sub.A,
                            sub.B,
                            sub.state_names,
                            sub.input_names,
                            tuple((STATE_UNITS[STATE_NAMES.index(n)] for n in sub.state_names)),
                            tuple((INPUT_UNITS[INPUT_NAMES.index(n)] for n in sub.input_names)),
                        )
                        audit = _require_local(
                            numeric_call(
                                closed_loop_pair,
                                lp,
                                g,
                                qualification.applicability,
                                scope="CANDIDATE",
                            ),
                            scope="CANDIDATE",
                            stage="closed_loop_pair",
                        )
                        closed_id = emit(
                            "closed_loop",
                            q.tuple_id + ":" + subsystem,
                            audit,
                            q,
                            MapId.D_TRACKER,
                            scope="DESIGN_SUPPORT_ONLY",
                            pair=sub,
                        )
                        if subsystem == "full":
                            full_acl = audit["Acl_dimensional"]
                        sample = ClosedLoopSample(
                            replace(p.key, tuple_id=closed_id),
                            t,
                            t + 0.01,
                            audit["Acl_dimensional"],
                            np.asarray(g),
                            i,
                            "DESIGN_CONDITIONAL",
                            qualification.applicability,
                        )
                        if t + 0.01 <= packet.timestamps_s[-1] + 1e-10:
                            design[subsystem].append(sample)
                        if (
                            history is not None
                            and t >= nominal_point.time_s
                            and (t >= history.authority.start_s)
                            and (
                                t + 0.01 <= min(history.authority.end_s, history.authority.expiry_s)
                            )
                        ):
                            observed[subsystem].append(
                                replace(sample, authority_scope="OBSERVED_AUTHORITY")
                            )
                    if t + 0.01 <= packet.timestamps_s[-1] + 1e-10:
                        next_x = _sample(packet, t + 0.01)[0]
                        ns = NominalSample(
                            p.key,
                            t,
                            np.asarray(x),
                            np.asarray(u),
                            t + 0.01,
                            np.asarray(next_x),
                            np.asarray(g),
                            True,
                        )
                        chart = _require_local(
                            check_heading_chart(x[3], (next_x[3],)),
                            scope="CANDIDATE",
                            stage="check_heading_chart",
                        )
                        sem = MapSemantics(
                            MapId.D_TRACKER,
                            0.01,
                            2,
                            CurvaturePolicy.FROZEN_EXOGENOUS,
                            _curvature(bound, q),
                            chart,
                            "DESIGN_SUPPORT_ONLY",
                        )
                        defect = nominal_defects(
                            (ns,),
                            lambda xx, uu: np.asarray(
                                bundle.prediction.rk4(0.01, 2)(xx, uu, sem.curvature_value)[0]
                            ).ravel(),
                            sem,
                        )
                        if defect.value is None:
                            _require_local(defect, scope="CANDIDATE", stage="DESIGN_NOMINAL_DEFECT")
                        if defect.value:
                            for j, d in enumerate(defect.value["defects"]):
                                d = dict(d)
                                forced_scaled = _forced_step(
                                    forced, full_acl, d["d_dimensional"], steps.state_scales_SI
                                )
                                forced = forced_scaled * steps.state_scales_SI
                                d["forced_response_scaled"] = forced_scaled.tolist()
                                d["interpretation"] = (
                                    "Affine forced response from zero at original design suffix start using same packet/time/map full Acl; conditional design only, no asynchronous event interpretation."
                                )
                                emit(
                                    "defect",
                                    q.tuple_id + ":defect:" + str(j),
                                    d,
                                    q,
                                    MapId.D_TRACKER,
                                    scope="DESIGN_SUPPORT_ONLY",
                                )
                for population, populations in (
                    ("DESIGN_CONDITIONAL", design),
                    ("OBSERVED_AUTHORITY", observed),
                ):
                    for subsystem, sequence in populations.items():
                        selection = _product_selection(sequence, candidate.candidate_id, population)
                        expected = state["plans"][population]
                        if selection["intervals"] != expected["intervals"]:
                            raise _GlobalIntegrityFailure(
                                "PRODUCT_PLAN_INTEGRITY",
                                "Computed factor metadata does not match predeclared source-only interval plan",
                            )
                        event(
                            "L2B_PRODUCT_SELECTION",
                            json.dumps(
                                _json(
                                    {
                                        **selection,
                                        "subsystem": subsystem,
                                        "intervals": [asdict(z) for z in selection["intervals"]],
                                        "normalization_ids": [
                                            "nominal_scaled",
                                            "raw_SI_unit_dependent",
                                            "selected_coordinate_x0.1",
                                            "selected_coordinate_x10",
                                        ],
                                    }
                                ),
                                allow_nan=False,
                            ),
                            nominal_point,
                            MapId.D_TRACKER,
                            population,
                        )
                        if not sequence:
                            emit(
                                "product",
                                candidate.candidate_id
                                + ":"
                                + population
                                + ":"
                                + subsystem
                                + ":unavailable",
                                point=nominal_point,
                                mid=MapId.D_TRACKER,
                                status="UNAVAILABLE",
                                scope=population,
                                reasons=(
                                    {
                                        "code": "NO_SUPPORTED_INTERVAL",
                                        "detail": "No complete original 10ms factor in this population; no design substitution or off-grid approximation",
                                        "source_pointer": None,
                                        "observed": None,
                                        "threshold": None,
                                    },
                                ),
                            )
                            continue
                        sub = extract_subsystem(support[0], subsystem)
                        normalization_cases = _product_normalizations(sub, _default_scales(sub))
                        for case_name, case_scales in normalization_cases:
                            for range_index, interval in enumerate(selection["intervals"]):
                                products = transition_products(
                                    tuple(sequence),
                                    ProductIntervals(
                                        (interval,),
                                        tuple(inputs.metrics["closed_loop"]["time_windows_s"]),
                                        population,
                                    ),
                                    case_scales,
                                    token,
                                )
                                if products.value:
                                    for data in products.value["products"]:
                                        data = dict(data)
                                        data["rescaling_log"] = list(data["rescaling_log"])
                                        if products.status == OutcomeStatus.RESOURCE_CENSORED:
                                            writer.budget_token = None
                                        data["rescaling_log"].append(
                                            "selection=ct1l-l2b-full-first-three-anchors-v1; normalization="
                                            + case_name
                                            + "; Dx="
                                            + json.dumps(case_scales.Dx_diagonal_SI.tolist())
                                            + "; sampled interval panel, raw SI norm depends on units"
                                        )
                                        emit(
                                            "product",
                                            candidate.candidate_id
                                            + ":"
                                            + population
                                            + ":"
                                            + subsystem
                                            + ":"
                                            + case_name
                                            + ":"
                                            + str(range_index),
                                            data,
                                            nominal_point,
                                            MapId.D_TRACKER,
                                            scope=population,
                                            pair=sub,
                                            status="RESOURCE_CENSORED"
                                            if products.status == OutcomeStatus.RESOURCE_CENSORED
                                            else "COMPUTED",
                                            reasons=products.reasons,
                                        )
                                        if products.status == OutcomeStatus.AVAILABLE:
                                            state["completed_products"].add(
                                                (population, subsystem, case_name, range_index)
                                            )
                                if products.status == OutcomeStatus.RESOURCE_CENSORED:
                                    raise TimeoutError(
                                        "Selected endpoint incomplete; prefixes retained and remaining selected coverage is missing"
                                    )
                                _require_local(
                                    products, scope="CANDIDATE", stage="SELECTED_PRODUCTS"
                                )
                status = (
                    "QUALIFIED"
                    if statuses and all((s == "QUALIFIED" for s in statuses))
                    else "QUALIFIED_BRANCH_SPECIFIC"
                    if "QUALIFIED_BRANCH_SPECIFIC" in statuses
                    else "UNAVAILABLE"
                )
                row.update(
                    qualification=status,
                    reasons=row["reasons"]
                    + (["MAP_COVERAGE_INCOMPLETE"] if row["missing_map_ids"] else []),
                )

                event(
                    "CANDIDATE_END",
                    json.dumps(
                        {
                            "candidate_id": candidate.candidate_id,
                            "local_failures": state["local_failures"],
                        }
                    ),
                    state["point"],
                )

            def on_candidate_failure(candidate, exc):
                state = candidate_states[candidate.candidate_id]
                row = state["row"]
                row["qualification"] = "INVALID" if exc.status == "INVALID" else "UNAVAILABLE"
                row["reasons"].append(exc.stage + ":" + exc.status)
                state["local_failures"] += 1
                event(
                    "L2B_LOCAL_CANDIDATE_FAILURE",
                    json.dumps(
                        {
                            "classification": "CANDIDATE_LOCAL",
                            "candidate_id": candidate.candidate_id,
                            "stage": exc.stage,
                            "status": exc.status,
                            "reasons": exc.reasons,
                            "dependent_conclusions_withheld": True,
                            "retry": False,
                            "replacement": False,
                        },
                        allow_nan=False,
                    ),
                    state["point"],
                )

            _run_independent(
                inputs.candidates,
                analyze_candidate,
                on_candidate_failure,
                scope="CANDIDATE",
                budget=token,
                check_trust=lambda: _assert_common_trust(
                    inputs, trust_stamp, common_native_receipt
                ),
            )
    except TimeoutError as exc:
        termination = "RESOURCE_CENSORED"
        failures.append(str(exc))
    except _GlobalIntegrityFailure as exc:
        termination = (
            "SOURCE_IDENTITY_FAILURE"
            if exc.code == "SOURCE_IDENTITY_FAILURE"
            else "NUMERICAL_FAILURE"
        )
        failures.append(exc.code + ": " + str(exc))
    finally:
        if sys.exc_info()[0] is not None and termination == "COMPLETE":
            termination = "NUMERICAL_FAILURE"
            failures.append("UNHANDLED_PROGRAMMING_OR_COMMON_FAILURE:" + sys.exc_info()[0].__name__)
        for state in candidate_states.values():
            if state["plans"] is not None:
                missing_products.extend(
                    row["range"]
                    for row in _missing_selected_products(
                        state["plans"], state["completed_products"]
                    )
                )
        if termination == "COMPLETE" and any(
            state["local_failures"] for state in candidate_states.values()
        ):
            termination = "MISSING_COVERAGE"
        if termination == "COMPLETE" and any(c["missing_map_ids"] for c in coverage):
            termination = "MISSING_COVERAGE"
        # Finalization reserve is used for truthful missing coverage, never invented matrices.
        writer.budget_token = None
        for c in coverage:
            prefix = writer.run_id + ":" + c["candidate_id"] + ":"
            c["completed_record_ids"][:] = [r for r in record_ids if r.startswith(prefix)]
            if c["qualification"] == "NOT_EXECUTED" and c["completed_record_ids"]:
                c["qualification"] = "UNAVAILABLE"
                c["reasons"].append("PARTIAL_" + termination)
        covered = {c["candidate_id"] for c in coverage}
        for c in inputs.candidates:
            if c.candidate_id not in covered:
                coverage.append(
                    {
                        "candidate_id": c.candidate_id,
                        "qualification": "NOT_EXECUTED",
                        "reasons": [
                            "UNEXECUTED_BUDGET"
                            if termination == "RESOURCE_CENSORED"
                            else termination
                        ],
                        "completed_record_ids": [],
                        "missing_map_ids": [m.value for m in MapId],
                    }
                )
        coverage.sort(
            key=lambda c: next(
                i for i, p in enumerate(inputs.candidates) if p.candidate_id == c["candidate_id"]
            )
        )
        try:
            if getattr(writer, "_integrity_failed", False):
                raise _EvidenceIntegrityFailure(
                    "EVIDENCE_WRITE_FAILED",
                    "Final scientific append suppressed after broken common evidence integrity",
                )
            details = []
            for candidate in inputs.candidates:
                state = candidate_states.get(candidate.candidate_id)
                if state is None or state["plans"] is None:
                    details.append(
                        {
                            "candidate_id": candidate.candidate_id,
                            "planned_selected_records": None,
                            "missing_selected_records": None,
                            "coverage_unknown": True,
                        }
                    )
                else:
                    missing = _missing_selected_products(
                        state["plans"], state["completed_products"]
                    )
                    details.append(
                        {
                            "candidate_id": candidate.candidate_id,
                            "planned_selected_records": sum(
                                p["selected_interval_count"] for p in state["plans"].values()
                            )
                            * 12,
                            "missing_selected_records": len(missing),
                            "completed_selected_records": len(state["completed_products"]),
                            "missing": missing,
                            "coverage_unknown": False,
                            "deliberately_omitted_windows_per_subsystem": {
                                k: p["omitted_interval_count"] for k, p in state["plans"].items()
                            },
                        }
                    )
            event(
                "L2B_SELECTED_COVERAGE",
                json.dumps(
                    _json(
                        {"candidates": details, "denominator": 12, "exhaustive_verification": False}
                    ),
                    allow_nan=False,
                ),
            )
            if failures:
                event("STAGE_TERMINATED", "; ".join(failures))
            emit(
                "coverage",
                "coverage",
                {
                    "total_candidates": 12,
                    "candidate_ids": [c.candidate_id for c in inputs.candidates],
                    "per_candidate_status": coverage,
                    "gain_grid_slots_before_dedup": token.reserved_gain_slots,
                    "gain_grid_slots_evaluated": gain_slots_evaluated,
                    "missing_products": missing_products,
                    "new_trials": 0,
                    "global_stability_guarantee": False,
                },
            )
        except TimeoutError:
            termination = "RESOURCE_CENSORED"
        except _EvidenceIntegrityFailure:
            if termination != "SOURCE_IDENTITY_FAILURE":
                termination = "NUMERICAL_FAILURE"
    return WorkerReport(
        job,
        0 if termination == "COMPLETE" else 1,
        termination,
        binding_id,
        tuple(record_ids),
        tuple(c["candidate_id"] for c in coverage if c["qualification"] == "NOT_EXECUTED"),
        time.monotonic() - started,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--grant", required=True, type=Path)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root / "scripts"), str(root / "src")]
    sha = _git(root, "rev-parse", "HEAD")
    spec = InputSpec(root, args.archive_root.resolve(), root / "docs/ct1/ct1l", sha)
    inputs = verify_inputs(spec)
    if inputs.value is None:
        print("SOURCE_IDENTITY_FAILURE", file=sys.stderr)
        return 2
    grant = check_execution_grant(args.grant, inputs.value, Budget())
    if grant.value is None:
        print("L3_AUTHORIZATION_REQUIRED", file=sys.stderr)
        return 2
    binding = FileBinding(
        "scripts/threading_study/config.py",
        hashlib.sha256((root / "scripts/threading_study/config.py").read_bytes()).hexdigest(),
    )
    backend = BackendIdentity(
        "Accelerate",
        Path("/System/Library/Frameworks/Accelerate.framework/Accelerate"),
        None,
        "BLASSetThreading(1)",
        binding,
        ("historical plugin binary identity",),
    )
    setup = configure_native_single(backend)
    if setup.value is None:
        print("NATIVE_SETUP_UNQUALIFIED", file=sys.stderr)
        return 2
    os.environ["CT1L_NATIVE_RECEIPT"] = json.dumps(
        {
            "mode": setup.value.observed_mode,
            "status": setup.value.set_status,
            "exact_active_thread_count_available": False,
        }
    )
    if "CT1L_DEADLINE_MONOTONIC" not in os.environ:
        print("SUPERVISED_ALLOCATION_REQUIRED", file=sys.stderr)
        return 2

    def stop(signum, frame):
        raise TimeoutError("Supervisor resource stop")

    signal.signal(signal.SIGTERM, stop)
    os.environ["CT1L_GRANT_PATH"] = str(args.grant.resolve())
    report = execute_job(inputs.value, grant.value, Budget(), "qualify-and-analyze")
    print(json.dumps(asdict(report)))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
