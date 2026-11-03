"""Local checks using the existing canonical validators and native packet rules."""

from math import isfinite

from .records import Feedback


class BoundaryError(ValueError):
    def __init__(self, *reasons):
        self.reasons = tuple(dict.fromkeys(reasons))
        super().__init__(";".join(self.reasons))


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise BoundaryError(label + "_INVALID")
    if value < 0:
        raise BoundaryError(label + "_NEGATIVE")
    return float(value)


def identity(value, label):
    if type(value) is not int or value < 0:
        raise BoundaryError(label + "_INVALID")
    return value


def feedback(value, now, clock, last_time, previous_sample):
    from apex.state import state_vector

    now = number(now, "TIME")
    if now < last_time:
        raise BoundaryError("TIME_BACKWARDS")
    if not isinstance(value, Feedback):
        raise BoundaryError("FEEDBACK_MISSING")
    reasons = []
    try:
        identity(value.sample_id, "SAMPLE_ID")
    except BoundaryError as error:
        reasons.extend(error.reasons)
    try:
        capture = number(value.time, "CAPTURE")
    except BoundaryError as error:
        capture = None
        reasons.extend(error.reasons)
    if value.clock != clock:
        reasons.append("CLOCK_MISMATCH")
    if capture is not None and capture != now:
        reasons.append("STALE_FEEDBACK" if capture < now else "FUTURE_FEEDBACK")
    try:
        x = state_vector(value.state)
    except ValueError as error:
        if reasons:
            raise BoundaryError(*reasons, "STATE_INVALID") from error
        raise
    if reasons:
        raise BoundaryError(*reasons)
    if previous_sample is not None:
        if value.sample_id < previous_sample.sample_id:
            raise BoundaryError("SAMPLE_REPLAY")
        if value.sample_id == previous_sample.sample_id and value != previous_sample:
            raise BoundaryError("SAMPLE_CONFLICT")
    return x


def command(value, lower, upper):
    import numpy as np

    from apex.state import control_vector

    u = control_vector(value)
    if np.any(u < lower) or np.any(u > upper):
        raise BoundaryError("COMMAND_BOUNDS")
    return u


def authority(packet, now):
    number(now, "TIME")
    if packet is None or not packet.valid:
        raise BoundaryError("AUTHORITY_UNAVAILABLE")
    if now < packet.actual_completion_time - 1e-10 or now < packet.timestamps[0] - 1e-10:
        raise BoundaryError("AUTHORITY_NOT_READY")
    if packet.horizon_end_time - now <= 1e-10:
        raise BoundaryError("AUTHORITY_EXPIRED")
    if not len(packet.gains):
        raise BoundaryError("GAINS_UNAVAILABLE")
    packet.sample(now)


def continuity(packet, x, now, track, diagnostics):
    import numpy as np

    from apex.coordinates.angles import wrap_angle

    ref, nominal, _ = packet.sample(now)
    error = x - ref
    error[3] = wrap_angle(error[3])
    # The exact accepted synthetic handoff envelope, not a new physical domain.
    if np.any(abs(error) > [0.5, 0.5, 1.0, 0.20, 0.75, 0.15]):
        raise BoundaryError("HANDOFF_MISMATCH")
    track.sample(x[4] % track.length)
    diagnostics(ref, nominal)
