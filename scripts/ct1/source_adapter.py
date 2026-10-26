"""Read-only accepted-source adapters. Numerical imports occur inside L3-called functions."""

from __future__ import annotations

from pathlib import Path

from .contracts import (
    MAPS,
    ArchivedPacket,
    CurvaturePolicy,
    EvaluationKey,
    F64Vector,
    HeadingChart,
    Linearization,
    MapId,
    MapValue,
    Method,
    OperatingTuple,
    Outcome,
    OutcomeStatus,
    Reason,
    SourceBundle,
    TupleRole,
    VerifiedInputs,
)
from .inputs import _canonical, _read


def _binding_id(inputs):
    import hashlib

    return hashlib.sha256(
        _canonical([{"path": b.path, "sha256": b.sha256} for b in inputs.source_bindings])
    ).hexdigest()


def build_sources(inputs: VerifiedInputs) -> Outcome[SourceBundle]:
    try:
        import sys

        from apex.control.mpc.symbolic_model import SymbolicBicycle
        from apex.control.trajectory.tracker import TVLQR
        from apex.models.tire.config import RACING_TIRE_PHYSICS
        from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
        from apex.models.vehicle.parameters import VehicleParameters
        from apex.planning_reference.track import load_track

        root = inputs.spec.repo_root.resolve()
        origins = {}
        for name, module in tuple(sys.modules.items()):
            if name == "apex" or name.startswith("apex."):
                p = getattr(module, "__file__", None)
                if p is not None:
                    path = Path(p).resolve()
                    if not path.is_relative_to(root / "src/apex"):
                        raise ValueError("Foreign APEX module origin: " + name)
                    origins[name] = path
        manifest = _read(root / "configs/performance/apex_performance_synthetic_v1.json")
        parameters = VehicleParameters(**manifest["profile"]["vehicle"]["parameters"])
        track, _, _ = load_track(root / "configs/planning/task007b/gamma_2p000/track_source.json")
        plant = DynamicBicycle(parameters, track, tire_physics=RACING_TIRE_PHYSICS)
        model = SymbolicBicycle(parameters, tire_physics=RACING_TIRE_PHYSICS)
        jac = TVLQR(model, track, dt=0.01)
        return Outcome.available(
            SourceBundle(root, parameters, plant, model, jac, track, _binding_id(inputs), origins)
        )
    except (OSError, ValueError, KeyError, ImportError) as exc:
        return Outcome(OutcomeStatus.INVALID, (Reason("SOURCE_ADAPTER_FAILURE", str(exc)),))


def _curvature(bundle, point):
    if point.kappa_policy == CurvaturePolicy.FROZEN_EXOGENOUS:
        fixed = getattr(bundle, "_fixed_curvature", None)
        if fixed is not None:
            return float(fixed)
    if (
        point.kappa_policy == CurvaturePolicy.GEOMETRY_PROGRESS
        or point.role == TupleRole.ACTUAL_HELD
    ):
        return float(bundle.track.sample(point.x[4] % bundle.track.length).curvature)
    # packet source lookup is injected by the worker into its own bundle cache, not accepted source.
    packet = getattr(bundle, "_packet", None)
    if packet is None:
        raise ValueError("Nominal curvature requires bound original packet")
    import bisect

    i = max(
        0,
        min(
            bisect.bisect_right(packet.timestamps_s, point.time_s + 1e-10) - 1,
            len(packet.curvatures) - 1,
        ),
    )
    return float(packet.curvatures[i])


def _with_packet(bundle, packet):
    """Owned adapter wrapper; never add attributes to accepted classes or frozen bundle."""

    class Bound:
        def __init__(self, source, p):
            self._source, self._packet = source, p

        def __getattr__(self, name):
            return getattr(self._source, name)

    return Bound(bundle, packet)


def source_f(
    bundle: SourceBundle, point: OperatingTuple, *, policy: CurvaturePolicy
) -> Outcome[F64Vector]:
    try:
        import numpy as np

        if policy == CurvaturePolicy.GEOMETRY_PROGRESS:
            value = bundle.plant.derivative(np.array(point.x), np.array(point.u))
        else:
            value = np.asarray(
                bundle.prediction.derivative(point.x, point.u, _curvature(bundle, point))
            ).ravel()
        if not np.isfinite(value).all():
            raise ValueError("Nonfinite source derivative")
        return Outcome.available(np.array(value, dtype=float, copy=True))
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("SOURCE_DOMAIN", str(exc))


def source_transition(
    bundle: SourceBundle, point: OperatingTuple, map_id: MapId
) -> Outcome[MapValue]:
    try:
        import numpy as np

        mid = MapId(map_id)
        dt, n = MAPS[mid]
        x = np.asarray(point.x, dtype=float)
        u = np.asarray(point.u, dtype=float)
        if dt is None:
            return Outcome.available(
                MapValue(
                    source_f(
                        bundle,
                        point,
                        policy=CurvaturePolicy.GEOMETRY_PROGRESS
                        if mid == MapId.C_PHYSICAL
                        else CurvaturePolicy.FROZEN_EXOGENOUS,
                    ).unwrap(),
                    (x.copy(),),
                )
            )
        if mid in (MapId.D_TRACKER, MapId.D_NMPC):
            value, stages = bundle.prediction.rk4(dt, n)(x, u, _curvature(bundle, point))
            result = np.asarray(value).ravel()
            states = tuple(
                np.asarray(stages)[:, j].copy() for j in range(np.asarray(stages).shape[1])
            ) + (result.copy(),)
        else:
            h = dt / n
            states = []
            result = x.copy()
            for _ in range(n):
                a = bundle.plant.derivative(result, u)
                b = result + h * a / 2
                c = result + h * bundle.plant.derivative(b, u) / 2
                d = result + h * bundle.plant.derivative(c, u)
                states.extend((result.copy(), b.copy(), c.copy(), d.copy()))
                nxt = bundle.plant.step(result, u, h)
                chart = _source_heading_chart(float(result[3]), (float(nxt[3]),)).unwrap()
                result = np.array(nxt, copy=True)
                result[3] = chart.lifted_endpoints_rad[0]
                states.append(result.copy())
            states = tuple(states)
        if not np.isfinite(result).all():
            raise ValueError("Nonfinite transition")
        chart = _source_heading_chart(float(x[3]), (float(result[3]),)).unwrap()
        result = np.array(result, copy=True)
        result[3] = chart.lifted_endpoints_rad[0]
        return Outcome.available(MapValue(result, states, chart))
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("SOURCE_MAP_DOMAIN", str(exc))


def source_symbolic_pair(
    bundle: SourceBundle, point: OperatingTuple, map_id: MapId
) -> Outcome[Linearization]:
    try:
        import casadi as ca
        import numpy as np

        mid = MapId(map_id)
        if mid not in (MapId.C_FIXED, MapId.D_TRACKER, MapId.D_NMPC):
            return Outcome.unavailable(
                "NO_PHYSICAL_CASADI_TRANSCRIPTION",
                "Physical geometry is not inside accepted symbolic graph",
            )
        x, u, k = ca.SX.sym("ct1_x", 6), ca.SX.sym("ct1_u", 2), ca.SX.sym("ct1_k")
        if mid == MapId.C_FIXED:
            f = bundle.prediction.derivative(x, u, k)
        else:
            dt, n = MAPS[mid]
            f, _ = bundle.prediction.rk4(dt, n)(x, u, k)
        jac = ca.Function("ct1_readonly_jac", [x, u, k], [ca.jacobian(f, x), ca.jacobian(f, u)])
        a, b = jac(point.x, point.u, _curvature(bundle, point))
        a, b = np.asarray(a), np.asarray(b)
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError("Nonfinite AD pair")
        key = EvaluationKey(
            point.candidate_id,
            point.tuple_id,
            mid,
            CurvaturePolicy.FROZEN_EXOGENOUS,
            bundle.binding_set_sha256,
            point.gain_index,
            physical_interval=(point.time_s, point.time_s + (MAPS[mid][0] or 0)),
        )
        return Outcome.available(Linearization(key, a, b, method=Method.CASADI_AD))
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("SYMBOLIC_JACOBIAN_INVALID", str(exc))


def original_tracker_jacobians(
    bundle: SourceBundle, packet: ArchivedPacket, sample_indices: tuple[int, ...]
) -> Outcome[tuple[Linearization, ...]]:
    try:
        import numpy as np

        from .inputs import _sample

        if len(sample_indices) > 80 or len(set(sample_indices)) != len(sample_indices):
            raise ValueError("Gain grid exceeds per-candidate cap or repeats")
        result = []
        for i in sample_indices:
            if i < 0 or i >= len(packet.gain_times_s):
                raise ValueError("Gain index outside original grid")
            t = packet.gain_times_s[i]
            if not packet.timestamps_s[0] <= t < packet.timestamps_s[-1]:
                raise ValueError("Original gain support outside validity")
            x, u, _, _ = _sample(packet, t)
            point = OperatingTuple(
                "packet:" + str(packet.raw_fields["plan_id"]) + ":" + str(i),
                "ORIGINAL_SUPPORT",
                TupleRole.ORIGINAL_GAIN_GRID_SUPPORT,
                x,
                u,
                t,
                packet.raw_fields["plan_id"],
                i,
                CurvaturePolicy.FROZEN_EXOGENOUS,
            )
            a, b = bundle.tracker_jacobian_builder.jacobian(
                x, u, _curvature(_with_packet(bundle, packet), point)
            )
            key = EvaluationKey(
                point.candidate_id,
                point.tuple_id,
                MapId.D_TRACKER,
                point.kappa_policy,
                bundle.binding_set_sha256,
                i,
                physical_interval=(t, t + 0.01),
            )
            result.append(Linearization(key, np.asarray(a), np.asarray(b), method=Method.CASADI_AD))
        return Outcome.available(tuple(result))
    except (ValueError, ArithmeticError) as exc:
        return Outcome.unavailable("ORIGINAL_GRID_UNAVAILABLE", str(exc))


def _source_heading_chart(anchor, endpoints):
    # Source adapter cannot depend on geometry (approved graph is acyclic).
    from math import isfinite, pi

    lifted = []
    multiples = []
    for theta in endpoints:
        delta = (theta - anchor + pi) % (2 * pi) - pi
        if not isfinite(theta) or abs(delta) == pi:
            return Outcome.unavailable("HEADING_CHART_AMBIGUOUS", "No unique finite lift")
        value = anchor + delta
        lifted.append(value)
        multiples.append(round((value - theta) / (2 * pi)))
    return Outcome.available(HeadingChart(anchor, tuple(lifted), tuple(multiples), True))


def _with_fixed_curvature(bundle, value):
    """Owned frozen scalar for a whole x/u stencil, including ACTUAL_HELD tuples."""

    class Fixed:
        def __init__(self, source, curvature):
            self._source, self._fixed_curvature = source, float(curvature)

        def __getattr__(self, name):
            return getattr(self._source, name)

    return Fixed(bundle, value)
