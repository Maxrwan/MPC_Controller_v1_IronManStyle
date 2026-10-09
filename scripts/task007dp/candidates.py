"""Causal lightweight candidates; no solver, physical history or runtime integration."""

import numpy as np
from task007d.forensics import packet_from_record

from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.control.trajectory.packet import TrajectoryBuffer
from apex.control.trajectory.prediction import ActuationPredictor, CommittedControlPrefix
from apex.control.trajectory.tracker import LATERAL, TVLQR, TrackerConfig, TrajectoryTracker
from apex.coordinates.angles import wrap_angle
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.parameters import VehicleParameters
from apex.simulation.prediction_capture import PredictionRelease
from apex.state import StateIndex as S

METHODS = ("A", "P0", "P1a", "P1b", "P2")
TIME_TOL = 1e-10


def read_release(record):
    return PredictionRelease(
        record["plan_id"],
        tuple(record["state"]),
        record["estimated_delay"],
        CommittedControlPrefix(**record["prefix"]),
        None if record["packet"] is None else packet_from_record(record["packet"]),
        VehicleParameters(**record["parameters"]),
        TrackerConfig(**record["tracker_config"]),
        tuple(record["lower"]),
        tuple(record["upper"]),
    )


def intervals(release):
    """Ideal error-recurrence intervals: global driver grid with partial last step."""
    start = release.prefix.release_time
    end = start + release.estimated_delay
    if not np.isfinite(end) or release.estimated_delay < 0:
        raise ValueError("Invalid prediction duration")
    dt = release.tracker_config.dt
    tick = int(np.floor(start / dt)) + 1
    while tick * dt <= start + TIME_TOL:
        tick += 1
    times = [start]
    while tick * dt < end - 1e-12:
        times.append(tick * dt)
        tick += 1
    if end > start + 1e-12:
        times.append(end)
    return times


class Candidate:
    """P1b uses the authorized ideal design recurrence, not constrained actuator dynamics.

    Its four-state error block omits affine nominal interpolation defects, cross-coupling
    from speed/progress, delay, saturation and known-input forcing. Those limitations are
    explicit; the separate input preview does honor commitment/busy/actuator constraints.
    """

    def __init__(self, method, parameters, track, *, jacobians=None):
        if method not in METHODS:
            raise ValueError("Unknown candidate")
        self.method, self.track = method, track
        self.model = SymbolicBicycle(parameters, RACING_TIRE_PHYSICS)
        self.predictor = ActuationPredictor(self.model, track) if method in ("A", "P2") else None
        self.jacobians = {} if jacobians is None else jacobians

    def precompute(self, releases):
        """Compile required RK4 Jacobian functions only; never cache context matrices.

        Durations come solely from release-known estimates/global grid. Cost is measured
        separately. Each warm call still evaluates A/B at every local nominal sample.
        """
        if self.method != "P1b":
            return
        for release in releases:
            times = intervals(release)
            for t, stop in zip(times, times[1:]):
                h = round(stop - t, 12)
                if h not in self.jacobians:
                    # Exact existing TVLQR discretization: approved model RK4(h, 2).
                    # No Riccati/gain recomputation. Existing stored 10 ms K is used.
                    self.jacobians[h] = TVLQR(self.model, self.track, dt=h).jacobian

    def validate(self, x, u, release, *, check_progress=True):
        x, u = np.asarray(x), np.asarray(u)
        if (
            x.shape != (6,)
            or u.shape != (2,)
            or not np.isfinite(x).all()
            or not np.isfinite(u).all()
        ):
            raise ValueError("Nonfinite or noncanonical candidate output")
        geometry = self.track.sample(x[S.S_ABS] % self.track.length)
        domain = np.asarray(self.model.domain(x, geometry.curvature)).ravel()
        if domain[0] < 0.5 or domain[0] > release.parameters.maximum_speed or domain[1] < 0.01:
            raise ValueError("Candidate state outside existing model domain")
        if (
            check_progress
            and release.estimated_delay > 0
            and x[S.S_ABS] < release.state[S.S_ABS] - 1e-10
        ):
            raise ValueError("Candidate progress reverses from measured release")
        if np.any(u < release.lower) or np.any(u > release.upper):
            raise ValueError("Candidate control outside captured actuator box")
        if (
            np.min(np.asarray(self.model.loads(u))) <= 0
            or np.max(abs(np.asarray(self.model.longitudinal_domain(u)))) >= 1
        ):
            raise ValueError("Candidate input violates load or longitudinal grip domain")
        # Track-boundary clearance is reported as a diagnostic, separately from model domain.
        return min(geometry.left_width - x[S.E_Y], geometry.right_width + x[S.E_Y])

    def __call__(self, release):
        packet = release.packet
        t, end = release.prefix.release_time, release.prefix.release_time + release.estimated_delay
        if (
            packet is None
            or not packet.valid
            or packet.actual_completion_time > t + TIME_TOL
            or packet.horizon_end_time <= t + TIME_TOL
        ):
            raise ValueError("Unavailable or exhausted release-active packet")
        packet.sample(t)
        self.validate(
            np.asarray(release.state),
            np.asarray(release.prefix.applied_control),
            release,
            check_progress=False,
        )
        if release.tracker_config.feedback and not len(packet.gains):
            raise ValueError("Release feedback gains unavailable")
        packet.sample(end)  # No extrapolation by any candidate.
        if self.predictor is not None:
            buffer = TrajectoryBuffer()
            buffer.active = packet
            tracker = TrajectoryTracker(
                release.parameters, release.lower, release.upper, release.tracker_config
            )
            tracker.previous[:] = release.prefix.applied_control
            kwargs = {"committed_prefix": release.prefix} if self.method == "P2" else {}
            x, u = self.predictor.predict(
                release.state, t, release.estimated_delay, buffer, tracker, **kwargs
            )
            self.validate(x, u, release)
            return x, u  # Reference output arithmetic is unchanged, including heading convention.

        error = np.asarray(release.state) - packet.sample(t)[0]
        error[S.E_PSI] = wrap_angle(error[S.E_PSI])
        if self.method == "P0":
            error[:] = 0
        if self.method == "P1b":
            self.precompute([release])  # Cache hits are cheap; unseen compilation is charged.

        tracker = TrajectoryTracker(
            release.parameters, release.lower, release.upper, release.tracker_config
        )
        applied = np.array(release.prefix.applied_control)
        last = release.prefix.last_application_time
        pending = (
            None
            if release.prefix.pending_control is None
            else np.array(release.prefix.pending_control)
        )
        due = release.prefix.pending_application_time
        tick = int(np.floor(t / tracker.config.dt)) + 1
        while tick * tracker.config.dt <= t + TIME_TOL:
            tick += 1
        # Error propagation and the input preview have separate assumptions. Error intervals
        # follow the ideal design grid; pending application splits only the input preview.
        grid = intervals(release)
        errors = [error.copy()]
        if self.method == "P1b":
            for begin, stop in zip(grid, grid[1:]):
                nominal, nominal_u, gain = packet.sample(begin)
                k = (
                    packet.curvature(begin)
                    if len(packet.curvatures)
                    else self.track.sample(nominal[S.S_ABS] % self.track.length).curvature
                )
                h = round(stop - begin, 12)
                full_a, full_b = self.jacobians[h](nominal, nominal_u, k)
                gain = gain if release.tracker_config.feedback else np.zeros(4)
                a = np.asarray(full_a)[np.ix_(LATERAL, LATERAL)]
                b = np.asarray(full_b)[LATERAL, :1]
                error = error.copy()
                error[LATERAL] = (a - b @ gain[None, :]) @ error[LATERAL]
                error[S.E_PSI] = wrap_angle(error[S.E_PSI])
                errors.append(error.copy())
        else:
            errors = [error.copy() for _ in grid]

        def estimate(time):
            # Queries only at release, ideal tick or target: no interpolation of error.
            i = min(range(len(grid)), key=lambda j: abs(grid[j] - time))
            if abs(grid[i] - time) > TIME_TOL:
                raise ValueError("Error state requested off the declared recurrence grid")
            state = packet.sample(time)[0] + errors[i]
            state[S.E_PSI] = wrap_angle(state[S.E_PSI])
            return state

        while True:
            if pending is not None and due <= t + TIME_TOL and due <= end:
                applied = ActuationPredictor._apply(
                    pending, applied, t - last, tracker.config.steering_rate
                )
                last, pending = t, None
            if t >= end - 1e-12:
                break  # Known due application precedes handoff; no new feedback at target.
            next_tick = tick * tracker.config.dt
            if t >= next_tick - TIME_TOL:
                if pending is None:
                    x = estimate(t)
                    self.validate(x, applied, release, check_progress=False)
                    tracker.previous[:] = applied
                    request, *_ = tracker.command(x, *packet.sample(t))
                    applied = ActuationPredictor._apply(
                        request, applied, t - last, tracker.config.steering_rate
                    )
                    last = t
                tick += 1  # Busy ticks are skipped, no catch-up commands.
                next_tick = tick * tracker.config.dt
            t = min(end, next_tick, due if pending is not None else end)
        x = estimate(end)
        self.validate(x, applied, release)
        return x, applied.copy()
