"""Shared Frenet coordinate validity and kinematics, without vehicle physics."""

from math import cos, isfinite, sin

from apex.models.errors import FrenetGeometryError

FRENET_DENOMINATOR_MIN = 1e-3


def validated_denominator(curvature: float, e_y: float, s_abs: float) -> float:
    """Preserve Task 003's positive-branch validity rule and descriptive error."""
    denominator = 1.0 - curvature * e_y
    if not isfinite(denominator) or denominator <= FRENET_DENOMINATOR_MIN:
        raise FrenetGeometryError(
            f"Invalid Frenet geometry: 1-kappa*e_y={denominator:g} "
            f"must exceed {FRENET_DENOMINATOR_MIN:g}; "
            f"kappa={curvature:g}, e_y={e_y:g}, s_abs={s_abs:g}"
        )
    return float(denominator)


def frenet_rates(
    vx: float, vy: float, r: float, e_psi: float, curvature: float, denominator: float
) -> tuple[float, float, float]:
    """Return de_psi/dt, ds_abs/dt, de_y/dt for already validated geometry."""
    ds = (vx * cos(e_psi) - vy * sin(e_psi)) / denominator
    return r - curvature * ds, ds, vx * sin(e_psi) + vy * cos(e_psi)
