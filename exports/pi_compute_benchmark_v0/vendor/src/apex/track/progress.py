"""Geometry wrapping and race-progress continuity, without lap-completion logic."""

from math import floor, isfinite, nextafter


def _length(length: float) -> None:
    if not isfinite(length) or length <= 0:
        raise ValueError("track length must be finite and positive")


def wrap_progress(s: float, length: float) -> float:
    """Wrap finite geometric progress into [0, length), including negative queries.

    Exact represented multiples map to zero. No epsilon snapping is used: a point
    immediately below the seam must remain on the preceding lap.
    """
    _length(length)
    if not isfinite(s):
        raise ValueError("progress must be finite")
    ratio = s / length
    if not isfinite(ratio):
        raise ValueError("progress/length exceeds floating-point range")
    # Recognize represented n*length exactly, without snapping nearby measurements.
    nearest = round(ratio)
    if s == nearest * length:
        return 0.0
    result = s % length
    # Floating remainder can round a tiny negative input up to length.
    return nextafter(length, 0.0) if result == length else result


def lap_index(s_abs: float, length: float) -> int:
    """Derive a nonnegative lap index without changing race progress."""
    _length(length)
    if not isfinite(s_abs) or s_abs < 0:
        raise ValueError("s_abs must be finite and nonnegative")
    ratio = s_abs / length
    if not isfinite(ratio):
        raise ValueError("progress/length exceeds floating-point range")
    nearest = round(ratio)
    if s_abs == nearest * length:
        return nearest
    # divmod keeps quotient and remainder consistent near represented boundaries.
    return int(divmod(s_abs, length)[0])


def unwrap_progress(track_s: float, previous_s_abs: float, length: float) -> float:
    """Choose the nearest nonnegative lap equivalent; ties prefer forward progress.

    Consecutive measurements must differ by less than half a lap. This does not
    impose monotonicity or infer missed laps from sparse measurements.
    """
    _length(length)
    if not isfinite(track_s) or not 0 <= track_s < length:
        raise ValueError("track_s must be finite and in [0, length)")
    lap_index(previous_s_abs, length)
    lap = max(0, floor((previous_s_abs - track_s) / length + 0.5))
    result = track_s + lap * length
    if not isfinite(result):
        raise ValueError("unwrapped progress exceeds floating-point range")
    return result
