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
    from .closed_loop import _forced_step, closed_loop_pair, nominal_defects, transition_products
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
        IndexInterval,
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
            "reasons": [asdict(r) if hasattr(r, "code") else r for r in reasons],
            "data": _payload(kind, data, schema, pair) if data is not None else None,
        }
        result = append_record(writer, kind, record)
        result.unwrap()
        record_ids.append(record["record_id"])
        return record["record_id"]

    def event(name, detail):
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
        )

    def emit_pair(p, point, mid, label, qualification):
        p = replace(
            p, key=replace(p.key, source_binding_set_sha256=binding_id), qualification=qualification
        )
        value = source_transition(bound, point, mid).value
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
        config = getattr(np.__config__, "CONFIG", {})
        if "accelerate" not in json.dumps(config, default=str).lower():
            raise ValueError(
                "Actual NumPy build backend not confirmed Accelerate; do not infer backend from env"
            )
        packages = []
        for name in ("numpy", "scipy", "casadi", "psutil", "pytest", "threadpoolctl", "PyYAML"):
            packages.append(
                {"name": name, "version": metadata.version(name), "binary_sha256": None}
            )
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
            raise ValueError("Prerequisite test failure; no candidate analysis or favorable retry")
        if job == "tests":
            termination = "MISSING_COVERAGE"
        else:
            bundle = build_sources(inputs).unwrap()
            snapshot = snapshot_geometry(bundle).unwrap()
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
            for candidate in inputs.candidates:
                token.poll()
                completed = []
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
                tuples = load_candidate_tuples(inputs, candidate.candidate_id)
                if tuples.value is None:
                    row.update(qualification="INVALID", reasons=[r.code for r in tuples.reasons])
                    continue
                packet = load_original_packet(inputs, candidate.packet_id).unwrap()
                history = load_authority_and_command_history(
                    inputs, candidate.candidate_id
                ).unwrap()
                bound = _with_packet(bundle, packet)
                local_defects = {}
                for role_point in tuples.value:
                    for mid in MapId:
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
                            continue
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
                            continue
                        fixed_k = _curvature(bound, point)
                        jet = geometry_jet(snapshot, point.x[4]).unwrap()
                        if not physical:
                            jet = replace(jet, kappa_1pm=fixed_k, kappa_s_1pm2=0.0)
                        if physical:
                            geometry_stencil = check_geometry_stencil(
                                snapshot,
                                tuple(
                                    point.x[4] + sign * h
                                    for h in (2e-5, 1e-5, 5e-6)
                                    for sign in (-1, 1)
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
                                continue
                            geometry_check = crosscheck_curvature_derivative(
                                jet,
                                snapshot.source_geometry_value,
                                inputs.metrics["finite_difference"]["geometry_kappa_s"],
                            )
                            if (
                                geometry_check.value is None
                                or geometry_check.value["comparison"] != "PASS"
                            ):
                                raise ValueError("Physical curvature derivative check failed")

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
                            j = geometry_jet(snapshot, float(x[4])).unwrap() if physical else jet
                            q = continuous_pair(
                                local, parameters, j, policy=point.kappa_policy
                            ).unwrap()
                            return q.A, q.B

                        if MAPS[mid][0] is None:
                            manual = continuous_pair(
                                point, parameters, jet, policy=point.kappa_policy
                            ).unwrap()
                            manual = replace(manual, key=replace(manual.key, map_id=mid))
                            value_function = f
                        else:
                            dt, n = MAPS[mid]
                            manual = compose_rk4(
                                point,
                                dt_s=dt,
                                substeps=n,
                                f=f,
                                df=df,
                                stage_guard=lambda x, u: Outcome.available(_domain(bundle, x, u)),
                            ).unwrap()
                            value_function = lambda x, u, dt=dt, n=n: (
                                crosscheck_rk4(
                                    x,
                                    u,
                                    parameters,
                                    dt_s=dt,
                                    substeps=n,
                                    curvature=None if physical else fixed_k,
                                    geometry_value=snapshot.source_geometry_value
                                    if physical
                                    else None,
                                ).value
                            )
                        primary = emit_pair(manual, point, mid, ident + ":manual", qualification)
                        references = [(ident + ":manual", primary)]
                        if not physical:
                            ad = source_symbolic_pair(bound, point, mid).unwrap()
                            ad = emit_pair(ad, point, mid, ident + ":AD", qualification)
                            references.append((ident + ":AD", ad))
                            primary = ad
                        fd = central_pair(
                            point, value_function, mid, scales, steps, lambda p, m, s: stencil
                        ).unwrap()
                        for j, p in enumerate(fd.pairs_per_step):
                            emit_pair(p, point, mid, ident + ":FD:" + str(j), qualification)
                        fd = replace(
                            fd,
                            pairs_per_step=tuple(
                                replace(p, key=replace(p.key, source_binding_set_sha256=binding_id))
                                for p in fd.pairs_per_step
                            ),
                        )
                        # Independently transcribed values AND accepted source values are differenced.
                        # For physical maps this checks tangent/source agreement without a symbolic geometry graph.
                        fd_bundle = bound if physical else _with_fixed_curvature(bound, fixed_k)
                        source_fd = central_pair(
                            point,
                            lambda x, u: (
                                source_transition(
                                    fd_bundle, replace(point, x=tuple(x), u=tuple(u)), mid
                                )
                                .unwrap()
                                .value
                            ),
                            mid,
                            scales,
                            steps,
                            lambda p, m, s: stencil,
                        ).unwrap()
                        source_fd = replace(
                            source_fd,
                            pairs_per_step=tuple(
                                replace(p, key=replace(p.key, source_binding_set_sha256=binding_id))
                                for p in source_fd.pairs_per_step
                            ),
                        )
                        for j, p in enumerate(source_fd.pairs_per_step):
                            emit_pair(p, point, mid, ident + ":source_FD:" + str(j), qualification)
                        for reference_name, reference in references:
                            for fd_name, estimate in (("FD", fd), ("source_FD", source_fd)):
                                token.poll()
                                comp = compare_pairs(
                                    reference, estimate, inputs.metrics["finite_difference"]
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
                                    raise ValueError(
                                        "Derivative comparison failed; retained, no tolerance change"
                                    )
                        # Same nominal endpoint and declared held-input map, separately for all four discrete maps.
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
                                    check_heading_chart(point.x[3], (next_x[3],)).unwrap(),
                                    "DESIGN_SUPPORT_ONLY",
                                )
                                outcome = nominal_defects(
                                    (nominal_sample,),
                                    lambda x, u: (
                                        source_transition(
                                            fd_bundle, replace(point, x=tuple(x), u=tuple(u)), mid
                                        )
                                        .unwrap()
                                        .value
                                    ),
                                    semantics,
                                )
                                if outcome.value:
                                    local_defect = dict(outcome.value["defects"][0])
                                    local_defect["discontinuity_flags"] = list(
                                        local_defect["discontinuity_flags"]
                                    )
                                    crossed = any(
                                        point.time_s + 1e-10 < t < end_time - 1e-10
                                        for t in packet.timestamps_s[1:-1]
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
                            ca = controllability_audit(sub, inputs.metrics["rank"]).unwrap()
                            pb = stabilizability_audit(sub, inputs.metrics["PBH"]).unwrap()
                            event(
                                "SCOPED_SCHUR_RANK_CROSSCHECK",
                                ident
                                + ":"
                                + subsystem
                                + " "
                                + json.dumps(
                                    _json(pb["rank_revealing_crosscheck"]), allow_nan=False
                                ),
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
                                feedback_app = qualification.applicability
                                if local_defect is not None and any(
                                    v != 0 for v in local_defect["d_dimensional"]
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
                                    tuple(
                                        STATE_UNITS[STATE_NAMES.index(n)] for n in sub.state_names
                                    ),
                                    tuple(
                                        INPUT_UNITS[INPUT_NAMES.index(n)] for n in sub.input_names
                                    ),
                                    qualification=qualification,
                                )
                                ideal = closed_loop_pair(
                                    projected,
                                    np.asarray(packet.original_gains[point.gain_index]),
                                    feedback_app,
                                )
                                emit(
                                    "closed_loop",
                                    ident + ":" + subsystem + ":conditional",
                                    ideal.value,
                                    point,
                                    mid,
                                    status="COMPUTED" if ideal.value is not None else "UNAVAILABLE",
                                    scope="DESIGN_CONDITIONAL",
                                    reasons=ideal.reasons,
                                    pair=sub,
                                )
                        completed.extend(
                            r for r in record_ids if r.startswith(writer.run_id + ":" + ident + ":")
                        )
                        role_tag = (
                            "actual" if role_point.role == TupleRole.ACTUAL_HELD else "nominal"
                        )
                        row["missing_map_ids"].remove(role_tag + ":" + mid.value)
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
                # D02 populations are never mixed. Count original suffix requests BEFORE dedup.
                indices = tuple(range(candidate.gain_index, len(packet.gain_times_s)))
                if len(indices) > 80:
                    raise ValueError("Original candidate suffix exceeds reviewed 80-slot cap")
                token.reserve(len(indices))
                support = []
                for i in indices:
                    token.poll()
                    p = original_tracker_jacobians(bundle, packet, (i,)).unwrap()[0]
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
                        raise ValueError(
                            "Original support domain not qualified; no substitute gain suffix"
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
                gains = audit_packet_gains(packet, tuple(support), inputs.metrics["Riccati"])
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
                if gains.status != OutcomeStatus.AVAILABLE:
                    raise ValueError("Original gain verification failed; original never replaced")
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
                            tuple(STATE_UNITS[STATE_NAMES.index(n)] for n in sub.state_names),
                            tuple(INPUT_UNITS[INPUT_NAMES.index(n)] for n in sub.input_names),
                        )
                        audit = closed_loop_pair(lp, g, qualification.applicability).unwrap()
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
                        design[subsystem].append(sample)
                        if (
                            t >= nominal_point.time_s
                            and t >= history.authority.start_s
                            and t + 0.01 <= min(history.authority.end_s, history.authority.expiry_s)
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
                        chart = check_heading_chart(x[3], (next_x[3],)).unwrap()
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
                                        "detail": "No full reviewed10ms interval in this population; off-grid boundary not approximated",
                                        "source_pointer": None,
                                        "observed": None,
                                        "threshold": None,
                                    },
                                ),
                            )
                            continue
                        sub = extract_subsystem(support[0], subsystem)
                        default = _default_scales(sub)
                        normalization_cases = [
                            ("nominal_scaled", default.Dx_diagonal_SI),
                            ("raw_SI_unit_dependent", np.ones(len(default.Dx_diagonal_SI))),
                        ]
                        for j in range(len(default.Dx_diagonal_SI)):
                            for fscale in (0.1, 10.0):
                                dx = default.Dx_diagonal_SI.copy()
                                dx[j] *= fscale
                                normalization_cases.append((f"x{j}x{fscale}", dx))
                        ranges = tuple(
                            IndexInterval(j, k, sequence[j].time_s, sequence[k - 1].next_time_s)
                            for j in range(len(sequence))
                            for k in range(j + 1, len(sequence) + 1)
                        )
                        # One interval at a time bounds retained memory and exports each completed result.
                        for case_index, (case_name, dx) in enumerate(normalization_cases):
                            for range_index, interval in enumerate(ranges):
                                products = transition_products(
                                    tuple(sequence),
                                    ProductIntervals(
                                        (interval,),
                                        tuple(inputs.metrics["closed_loop"]["time_windows_s"]),
                                        population,
                                    ),
                                    Scales(dx, default.Du_diagonal_SI),
                                    token,
                                )
                                if products.value:
                                    for j, data in enumerate(products.value["products"]):
                                        data = dict(data)
                                        data["rescaling_log"] = list(data["rescaling_log"])
                                        if products.status == OutcomeStatus.RESOURCE_CENSORED:
                                            writer.budget_token = None
                                        data["rescaling_log"].append(
                                            "normalization="
                                            + case_name
                                            + "; Dx="
                                            + json.dumps(dx.tolist())
                                            + "; raw SI norms depend on units"
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
                                        missing_products.extend(data["missing_ranges"])
                                if products.status == OutcomeStatus.RESOURCE_CENSORED:
                                    missing_products.extend(
                                        {
                                            "start_index_inclusive": z.start_index_inclusive,
                                            "end_index_exclusive": z.end_index_exclusive,
                                            "start_time_s": z.start_time_s,
                                            "end_time_s": z.end_time_s,
                                        }
                                        for z in ranges[range_index + 1 :]
                                    )
                                    raise TimeoutError(
                                        "Remaining products/scalings/subsystems/populations not evaluated; see coverage event"
                                    )
                                if products.value is None:
                                    raise ValueError("; ".join(r.detail for r in products.reasons))
                status = (
                    "QUALIFIED"
                    if statuses and all(s == "QUALIFIED" for s in statuses)
                    else "QUALIFIED_BRANCH_SPECIFIC"
                    if "QUALIFIED_BRANCH_SPECIFIC" in statuses
                    else "UNAVAILABLE"
                )
                row.update(
                    qualification=status,
                    reasons=["MAP_COVERAGE_INCOMPLETE"] if row["missing_map_ids"] else [],
                )
    except TimeoutError as exc:
        termination = "RESOURCE_CENSORED"
        failures.append(str(exc))
    except Exception as exc:
        termination = "NUMERICAL_FAILURE"
        failures.append(type(exc).__name__ + ": " + str(exc))
    finally:
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
        except (ValueError, OSError, TimeoutError):
            termination = "RESOURCE_CENSORED"
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
