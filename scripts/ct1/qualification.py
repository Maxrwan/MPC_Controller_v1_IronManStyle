"""Domain qualification is distinct from validity of an ideal feedback interpretation."""

from __future__ import annotations

from dataclasses import replace

from .contracts import (
    ApplicabilityAudit,
    ArchivedPacket,
    CausalHistory,
    DomainAudit,
    FDSteps,
    MapId,
    OperatingTuple,
    Outcome,
    Qualification,
    QualificationPolicy,
    QualificationStatus,
    Reason,
    SourceBundle,
    StencilDomain,
    VerifiedInputs,
)
from .geometry import check_geometry_stencil, check_heading_chart, geometry_jet, snapshot_geometry
from .inputs import load_authority_and_command_history, load_original_packet
from .source_adapter import _curvature, _with_fixed_curvature, source_transition


def _domain(bundle, x, u, strict=False):
    d = bundle.plant.diagnostics(x, u)
    v = float(x[0])
    D = d.frenet_denominator
    p = bundle.parameters
    mu = p.tire_road_friction_coefficient
    checks = []
    margins = {
        "speed_lower": v - 0.5,
        "speed_upper": 6 - v,
        "D": D - 0.001,
        "front_load": d.fzf - 1e-9,
        "rear_load": d.fzr - 1e-9,
        "steering": 0.4 - abs(float(u[0])),
        "acceleration_lower": float(u[1]) + 3,
        "acceleration_upper": 2 - float(u[1]),
        "front_longitudinal": (1 - 1e-6) * mu * d.fzf - abs(d.fx_front),
        "rear_longitudinal": (1 - 1e-6) * mu * d.fzr - abs(d.fx_rear),
    }
    for name, value, unit, threshold in [
        ("vx", v, "m/s", "[0.5,6]"),
        ("D", D, "1", ">0.001"),
        ("Fzf", d.fzf, "N", ">1e-9"),
        ("Fzr", d.fzr, "N", ">1e-9"),
        ("front_utilization", d.front_combined_utilization, "1", "<=1"),
        ("rear_utilization", d.rear_combined_utilization, "1", "<=1"),
        ("front_sqrt", (mu * d.fzf) ** 2 - d.fx_front**2, "N^2", ">0"),
        ("rear_sqrt", (mu * d.fzr) ** 2 - d.fx_rear**2, "N^2", ">0"),
    ]:
        checks.append(
            {
                "name": name,
                "value": float(value),
                "unit": unit,
                "source_threshold": threshold,
                "state": "PASS",
            }
        )
    sample = bundle.track.sample(float(x[4]) % bundle.track.length)
    for name, value, unit in [
        ("alpha_front", d.alpha_f, "rad"),
        ("alpha_rear", d.alpha_r, "rad"),
        ("Fy_front", d.fyf, "N"),
        ("Fy_rear", d.fyr, "N"),
        ("delta", float(u[0]), "rad"),
        ("a_cmd", float(u[1]), "m/s^2"),
    ]:
        checks.append(
            {
                "name": name,
                "value": float(value),
                "unit": unit,
                "source_threshold": "accepted diagnostic; boxes [-0.4,0.4]rad/[-3,2]m/s^2",
                "state": "PASS",
            }
        )
    for name, attr in [("width_left", "left_width"), ("width_right", "right_width")]:
        value = getattr(sample, attr, None)
        checks.append(
            {
                "name": name,
                "value": float(value) if value is not None else None,
                "unit": "m",
                "source_threshold": "planning margin 0.08 m; material slack 1e-6 m; not a plant validity guard",
                "state": "PASS" if value is not None else "NOT_EVALUATED",
            }
        )
    left = getattr(sample, "left_width", None)
    right = getattr(sample, "right_width", None)
    for name, value in [
        ("planning_left_margin", None if left is None else left - 0.08 - float(x[5])),
        ("planning_right_margin", None if right is None else right - 0.08 + float(x[5])),
    ]:
        checks.append(
            {
                "name": name,
                "value": value,
                "unit": "m",
                "source_threshold": "planning corridor only; negative margin requires slack, material-slack threshold 1e-6 m; not physical safety",
                "state": "NOT_EVALUATED" if value is None else "PASS" if value >= 0 else "FAIL",
            }
        )
    interior = all(v > 0 for v in margins.values()) and float(x[4]) > 0
    return DomainAudit(tuple(checks), True, interior, margins)


def _preview_checks(bundle, x, u, k):
    d = bundle.plant.diagnostics(x, u)
    fields = (
        ("NLP_preview_vx_lower", float(x[0]) - 0.5, "m/s", ">=0"),
        ("NLP_preview_vx_upper", 6 - float(x[0]), "m/s", ">=0"),
        ("NLP_preview_D", 1 - k * float(x[5]) - 0.01, "1", ">=0; D>=0.01"),
        ("NLP_preview_front_load", d.fzf - 1e-6, "N", ">=0; Fzf>=1e-6"),
        ("NLP_preview_rear_load", d.fzr - 1e-6, "N", ">=0; Fzr>=1e-6"),
    )
    checks = tuple(
        {
            "name": name,
            "value": value,
            "unit": unit,
            "source_threshold": threshold,
            "state": "PASS" if value >= 0 else "FAIL",
        }
        for name, value, unit, threshold in fields
    )
    if any(value < 0 for _, value, _, _ in fields):
        raise ValueError("Separate NLP preview domain violation")
    return checks, all(value > 0 for _, value, _, _ in fields)


def classify_feedback_applicability(
    point: OperatingTuple, history: CausalHistory, packet: ArchivedPacket
) -> ApplicabilityAudit:
    from math import pi

    import numpy as np

    from .inputs import _sample

    reference, nominal, gain, _ = _sample(packet, point.time_s)
    e = np.asarray(point.x) - np.asarray(reference)
    e[3] = (e[3] + pi) % (2 * pi) - pi
    desired = np.asarray(nominal) + [-np.dot(gain, e[[5, 3, 1, 2]]), -e[0]]
    flags = ["AUGMENTED_HYBRID_EVENT_MAP_UNAVAILABLE"]
    lower = np.array([-0.4, -3.0])
    upper = np.array([0.4, 2.0])
    if np.any(desired < lower) or np.any(desired > upper):
        flags.append("SATURATED_BOX")
    if np.any(desired == lower) or np.any(desired == upper):
        flags.append("CLIP_TIE_NONDIFFERENTIABLE")
    clipped = np.clip(desired, lower, upper)
    lo, hi = (
        history.previous_applied_steering_rad - 0.01,
        history.previous_applied_steering_rad + 0.01,
    )
    if clipped[0] < lo or clipped[0] > hi:
        flags.append("SLEW_ACTIVE")
    if clipped[0] in (lo, hi):
        flags.append("CLIP_TIE_NONDIFFERENTIABLE")
    flags.append("PREVIOUS_APPLIED_STEERING_REQUIRED")
    if history.pending_request is not None or not history.pending_information_complete:
        flags.append("PENDING_OR_DELAYED_COMMAND")
    if point.time_s >= history.authority.expiry_s:
        flags.append("AUTHORITY_EXPIRED")
    if point.time_s >= history.authority.end_s:
        flags.append("AUTHORITY_SUPERSEDED")
    if np.any(e != 0):
        flags.append("NOMINAL_ACTUAL_TUPLE_MISMATCH")
    if any(
        r.get("physical_latency", 0) > 0.01
        for r in history.codriver_request_rows
        if abs(r["time"] - point.time_s) < 0.02
    ):
        flags.append("SKIPPED_CODRIVER_TICK")
    relevant = [
        f
        for f in flags
        if f not in ("AUGMENTED_HYBRID_EVENT_MAP_UNAVAILABLE", "PREVIOUS_APPLIED_STEERING_REQUIRED")
    ]
    return ApplicabilityAudit(
        not relevant,
        tuple(dict.fromkeys(flags)),
        history.previous_applied_steering_rad,
        history.pending_information_complete,
        tuple(float(v) for v in e),
        False,
    )


def qualify_point(
    inputs: VerifiedInputs,
    bundle: SourceBundle,
    point: OperatingTuple,
    map_id: MapId,
    policy: QualificationPolicy,
) -> Qualification:
    mid = MapId(map_id)
    app = ApplicabilityAudit()
    branch = None
    domain = None
    reasons = []
    try:
        import numpy as np

        try:
            domain = _domain(bundle, point.x, point.u)
        except (ValueError, ArithmeticError) as exc:
            return Qualification(
                QualificationStatus.INVALID,
                (Reason("ORIGINAL_SOURCE_DOMAIN_REJECTED", str(exc)),),
                point.tuple_id,
                mid,
                None,
                None,
                app,
            )
        history = load_authority_and_command_history(inputs, point.candidate_id).unwrap()
        packet = load_original_packet(inputs, point.packet_id).unwrap()
        app = classify_feedback_applicability(point, history, packet)
        snapshot = snapshot_geometry(bundle).unwrap()
        jet = geometry_jet(snapshot, point.x[4]).unwrap()
        branch = jet.branch
        physical = mid in (MapId.C_PHYSICAL, MapId.D_PLANT_10, MapId.D_PLANT_100)
        if physical and jet.kappa_s_1pm2 is None:
            return Qualification(
                QualificationStatus.UNAVAILABLE,
                (
                    Reason(
                        "KNOT_SIDE_UNRESOLVED",
                        "Explicit one-sided map not supplied; unrestricted derivative unavailable",
                    ),
                ),
                point.tuple_id,
                mid,
                branch,
                domain,
                app,
            )
        domain = _domain(bundle, point.x, point.u)
        value = source_transition(bundle, point, mid).unwrap()
        stage_checks = []
        for index, stage in enumerate(value.stages):
            audit = _domain(bundle, stage, point.u)
            stage_checks.extend(
                {**check, "name": f"physical_stage[{index}]/" + check["name"]}
                for check in audit.checks
            )
        domain = replace(domain, checks=domain.checks + tuple(stage_checks))
        if physical:
            check_geometry_stencil(
                snapshot, tuple(float(x[4]) for x in value.stages), branch=branch
            ).unwrap()
        if mid in (MapId.C_FIXED, MapId.D_TRACKER, MapId.D_NMPC):
            k = _curvature(bundle, point)
            preview = []
            preview_strict = True
            for index, stage in enumerate(value.stages):
                checks, strict = _preview_checks(bundle, stage, point.u, k)
                preview_strict = preview_strict and strict
                preview.extend(
                    {**check, "name": f"preview_stage[{index}]/" + check["name"]}
                    for check in checks
                )
            domain = replace(
                domain,
                checks=domain.checks + tuple(preview),
                strict_central_interior=domain.strict_central_interior and preview_strict,
            )
        if domain.strict_central_interior:
            from .contracts import FDSteps

            fixed_steps = FDSteps(
                (2e-5, 1e-5, 5e-6), np.array([0.5, 0.5, 1, 0.1, 0.75, 0.1]), np.array([0.2, 1.0])
            )
            stencil = qualify_stencil(inputs, bundle, point, mid, fixed_steps)
            if stencil.value is None:
                return Qualification(
                    QualificationStatus.UNAVAILABLE,
                    stencil.reasons,
                    point.tuple_id,
                    mid,
                    branch,
                    domain,
                    app,
                )
        status = (
            QualificationStatus.QUALIFIED
            if domain.strict_central_interior
            else QualificationStatus.UNAVAILABLE
        )
        if status == QualificationStatus.UNAVAILABLE:
            reasons.append(
                Reason(
                    "NO_STRICT_CENTRAL_INTERIOR",
                    "Valid source boundary has no unrestricted central neighborhood",
                )
            )
        return Qualification(status, tuple(reasons), point.tuple_id, mid, branch, domain, app)
    except (ValueError, ArithmeticError) as exc:
        return Qualification(
            QualificationStatus.UNAVAILABLE,
            (Reason("POINT_OR_MAP_UNAVAILABLE", str(exc)),),
            point.tuple_id,
            mid,
            branch,
            domain,
            app,
        )


def qualify_stencil(
    inputs: VerifiedInputs,
    bundle: SourceBundle,
    point: OperatingTuple,
    map_id: MapId,
    steps: FDSteps,
) -> Outcome[StencilDomain]:
    try:
        import numpy as np

        if tuple(steps.multipliers) != (2e-5, 1e-5, 5e-6):
            raise ValueError("Unreviewed FD multipliers")
        mid = MapId(map_id)
        physical = mid in (MapId.C_PHYSICAL, MapId.D_PLANT_10, MapId.D_PLANT_100)
        if not physical:
            bundle = _with_fixed_curvature(bundle, _curvature(bundle, point))
        snapshot = snapshot_geometry(bundle).unwrap()
        states = []
        domains = []
        all_s = []
        x, u = np.asarray(point.x), np.asarray(point.u)
        scales = tuple(steps.state_scales_SI) + tuple(steps.input_scales_SI)
        for h0 in steps.multipliers:
            for j, scale in enumerate(scales):
                for sign in (-1, 1):
                    xx, uu = x.copy(), u.copy()
                    if j < 6:
                        xx[j] += sign * h0 * scale
                    else:
                        uu[j - 6] += sign * h0 * scale
                    q = replace(point, x=tuple(xx), u=tuple(uu))
                    d = _domain(bundle, xx, uu)
                    if not d.strict_central_interior:
                        raise ValueError("No strict central domain")
                    value = source_transition(bundle, q, mid).unwrap()
                    check_heading_chart(
                        point.x[3], tuple(float(z[3]) for z in value.stages)
                    ).unwrap()
                    for z in value.stages:
                        dd = _domain(bundle, z, uu)
                        if not dd.strict_central_interior:
                            raise ValueError("Intermediate stencil not interior")
                        if not physical:
                            k = _curvature(bundle, q)
                            _, preview_strict = _preview_checks(bundle, z, uu, k)
                            if not preview_strict:
                                raise ValueError("Preview stencil lacks strict central interior")
                        states.append(z)
                        domains.append(dd)
                        all_s.append(float(z[4]))
        branch = None
        if physical:
            branch = check_geometry_stencil(snapshot, tuple(all_s), branch=None).unwrap().branch
        return Outcome.available(
            StencilDomain(
                mid,
                point.tuple_id,
                tuple(range(8)),
                tuple(steps.multipliers),
                tuple(states),
                tuple(domains),
                branch,
                True,
                (),
            )
        )
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("INVALID_CENTRAL_STENCIL", str(exc))
