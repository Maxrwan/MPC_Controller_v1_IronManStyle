"""Single-owner nominal-control lifecycle. No physics, threads or physical permissions."""

import traceback
from dataclasses import replace
from math import isfinite
from uuid import uuid4
from weakref import WeakValueDictionary

from . import validation as v
from .records import Event, Output, Prepared, freeze

_owners = WeakValueDictionary()
_owned_fields = ("controller", "planner", "tracker", "buffer", "estimator", "urgent")


def _claim(owner, candidate, previous):
    for name in _owned_fields:
        value = getattr(candidate, name)
        prior_owner = _owners.get((name, id(value)))
        if prior_owner is not None and prior_owner is not owner:
            raise ValueError("MUTABLE_COMPONENT_ALREADY_OWNED: " + name)
        if previous is not None and value is getattr(previous, name):
            raise ValueError("RESET_REQUIRES_FRESH_COMPONENT: " + name)
    if previous is not None:
        for name in _owned_fields:
            _owners.pop((name, id(getattr(previous, name))), None)
    for name in _owned_fields:
        _owners[(name, id(getattr(candidate, name)))] = owner


class ControlSession:
    def __init__(self, factory, *, clock="local-simulation", journal=None):
        if type(clock) is not str or not clock:
            raise ValueError("Explicit local clock required")
        self.factory, self.clock, self.journal = factory, clock, journal
        self.events = []
        self.evidence_valid = True
        self.reset()

    def reset(self):
        previous = getattr(self, "components", None)
        self.session_id = uuid4().hex
        self.closed, self.inhibited = False, True
        if previous is not None:
            previous.buffer.active = None
        self.last_time, self.last_sample = -1.0, None
        self.request_id, self.proposal_id = 0, 0
        self.pending, self.waiting = None, None
        self.issued, self.consumed = {}, set()
        self.checked, self.observed = {}, set()
        try:
            candidate = self.factory()
            _claim(self, candidate, previous)
        except Exception as error:
            self._failure("reset", None, error)
            raise
        self.components = candidate
        self.buffer = self.components.buffer
        self.last_tracker_diagnostics = {}
        self.inhibited, self.evidence_valid = False, True
        self._event("reset", None, "NOT_READY")
        return self.session_id

    def _event(self, operation, time, status, reasons=(), **details):
        event = Event(
            len(self.events),
            self.session_id,
            operation,
            time,
            status,
            tuple(reasons),
            freeze(details),
        )
        self.events.append(event)
        if self.journal is not None:
            try:
                self.journal(event)
            except Exception:
                self.inhibited, self.evidence_valid = True, False
                raise

    def _failure(self, operation, now, error):
        self.inhibited = True
        observed_time = now
        if not isinstance(now, (int, float)) or isinstance(now, bool) or not isfinite(now):
            observed_time = None
        reasons = error.reasons if isinstance(error, v.BoundaryError) else ("BOUNDARY_EXCEPTION",)
        detail = {
            "exception_type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        try:
            self._event(
                operation,
                observed_time,
                "INHIBITED",
                reasons,
                **detail,
                supplied_time_representation=repr(now),
            )
        except Exception:
            reasons = ("EVIDENCE_WRITE_FAILURE",)
        return Output("INHIBITED", self.session_id, observed_time, reasons)

    def _check(self, feedback, now):
        if self.closed:
            raise v.BoundaryError("SESSION_CLOSED")
        if self.inhibited:
            raise v.BoundaryError("SESSION_INHIBITED")
        x = v.feedback(feedback, now, self.clock, self.last_time, self.last_sample)
        self.components.validator(x, self.components.tracker.previous)
        self.last_time, self.last_sample = float(now), feedback
        return x

    def bind_buffer(self, buffer):
        """Local runner supplies its sole buffer before startup; never a shadow authority."""
        if self.pending is not None or self.issued or self.buffer.active is not None:
            raise ValueError("Cannot replace live authority buffer")
        self._bind("buffer", buffer)
        self.buffer = buffer

    def _bind(self, name, value):
        owner = _owners.get((name, id(value)))
        if owner is not None and owner is not self:
            raise ValueError("MUTABLE_COMPONENT_ALREADY_OWNED: " + name)
        _owners.pop((name, id(getattr(self.components, name))), None)
        setattr(self.components, name, value)
        _owners[(name, id(value))] = self

    def bind_urgent(self, urgent):
        """The local runner owns scheduling; bind its sole urgent state before startup."""
        if self.pending is not None or self.issued or self.buffer.active is not None:
            raise ValueError("Cannot replace live scheduling state")
        self._bind("urgent", urgent)

    def prepare(self, feedback, now, estimate, *, plan_id, applied, startup=False):
        try:
            x = self._check(feedback, now)
            v.identity(plan_id, "PLAN_ID")
            v.number(estimate, "ESTIMATE")
            previous = v.command(
                applied, self.components.tracker.lower, self.components.tracker.upper
            )
            if self.pending is not None:
                raise v.BoundaryError("PREPARATION_BUSY")
            if startup:
                if self.buffer.active is not None or plan_id != 0:
                    raise v.BoundaryError("STARTUP_CONTEXT")
            elif self.buffer.active is None:
                raise v.BoundaryError("STARTUP_REQUIRED")
            self.components.validator(x, previous)
            self.components.tracker.previous = previous.copy()
            packet, diagnostics = self.components.planner.prepare(
                plan_id, x, now, estimate, self.buffer, self.components.tracker, startup=startup
            )
            self.request_id += 1
            prepared = Prepared(
                self.session_id, self.request_id, plan_id, packet, now, freeze(diagnostics)
            )
            self.pending = prepared
            self._event(
                "prepare",
                now,
                "PREPARED" if packet is not None else "REJECTED",
                plan_id=plan_id,
                diagnostics=diagnostics,
            )
            return prepared, diagnostics
        except Exception as error:
            return self._failure("prepare", now, error), None

    def observe_completion(self, prepared, completion, *, observe_delay=True):
        """Resolve identity only; shared-runner acceptance remains the runner's operation."""
        v.number(completion, "COMPLETION")
        if self.closed or self.inhibited or prepared.session != self.session_id:
            raise v.BoundaryError("COMPLETION_SESSION")
        if prepared is not self.pending or completion < prepared.release_time:
            raise v.BoundaryError("COMPLETION_IDENTITY")
        self.pending = None
        if observe_delay and prepared.plan_id != 0:
            self.components.estimator.observe(completion - prepared.release_time)
        self._event("completion", completion, "COMPLETED", plan_id=prepared.plan_id)

    def complete(self, prepared, feedback, now):
        """Public caller-owned completion/offer. A future nominal start remains waiting."""
        try:
            x = self._check(feedback, now)
            self.observe_completion(prepared, now)
            if prepared.packet is None:
                self._event("offer", now, "REJECTED", ("PREPARATION_FAILED",))
                return Output("REJECTED", self.session_id, now, ("PREPARATION_FAILED",))
            packet = replace(prepared.packet, actual_completion_time=float(now))
            if now < packet.timestamps[0] - 1e-10:
                self.waiting = packet
                return Output("NOT_READY", self.session_id, now, ("NOMINAL_START_PENDING",))
            return self._offer(packet, x, now)
        except Exception as error:
            return self._failure("complete", now, error)

    def _offer(self, packet, x, now):
        try:
            v.continuity(packet, x, now, self.components.track, self.components.validator)
            accepted, why = self.buffer.insert(packet, now)
        except ValueError as error:
            accepted, why = False, str(error)
        self._event(
            "offer", now, "ACCEPTED" if accepted else "REJECTED", (why,), plan_id=packet.plan_id
        )
        return Output("ACCEPTED" if accepted else "REJECTED", self.session_id, now, (why,))

    def offer_waiting(self, feedback, now):
        try:
            x = self._check(feedback, now)
            if self.waiting is None:
                return Output("NOT_READY", self.session_id, now, ("NO_WAITING_PACKET",))
            if now < self.waiting.timestamps[0] - 1e-10:
                return Output("NOT_READY", self.session_id, now, ("NOMINAL_START_PENDING",))
            packet, self.waiting = self.waiting, None
            return self._offer(packet, x, now)
        except Exception as error:
            return self._failure("offer_waiting", now, error)

    def propose(self, feedback, now, applied):
        try:
            x = self._check(feedback, now)
            v.authority(self.buffer.active, now)
            tracker = self.components.tracker
            previous = v.command(applied, tracker.lower, tracker.upper)
            self.components.validator(x, previous)
            tracker.previous = previous.copy()
            command, diagnostics = tracker.update(x, self.buffer, now)
            command = v.command(command, tracker.lower, tracker.upper)
            if (
                abs(command[0] - previous[0])
                > tracker.config.steering_rate * tracker.config.dt + 1e-6
            ):
                raise v.BoundaryError("PROPOSAL_RATE")
            self.components.validator(x, command)
            self.proposal_id += 1
            output = Output(
                "VALID_NOMINAL",
                self.session_id,
                now,
                command=tuple(command),
                proposal_id=self.proposal_id,
                plan_id=self.buffer.active_plan_id,
                sample_id=feedback.sample_id,
                requested=tuple(diagnostics["desired"]),
            )
            self.issued[output.proposal_id] = (output, self.buffer.active)
            self.last_tracker_diagnostics = diagnostics
            self._event("propose", now, output.status, output=output.__dict__)
            return output
        except Exception as error:
            return self._failure("propose", now, error)

    def check_application(self, proposal, feedback, now, applied, last_application):
        try:
            x = self._check(feedback, now)
            if not isinstance(proposal, Output) or proposal.session != self.session_id:
                raise v.BoundaryError("PROPOSAL_SESSION")
            entry = self.issued.get(proposal.proposal_id)
            if entry is None or entry[0] != proposal or proposal.stage != "proposal":
                raise v.BoundaryError("PROPOSAL_IDENTITY")
            if proposal.proposal_id in self.consumed:
                raise v.BoundaryError("DUPLICATE_APPLICATION")
            if now < proposal.time:
                raise v.BoundaryError("APPLICATION_BEFORE_PROPOSAL")
            v.authority(entry[1], now)  # Original packet, not necessarily the newest active one.
            tracker = self.components.tracker
            prior = v.command(applied, tracker.lower, tracker.upper)
            command = v.command(proposal.command, tracker.lower, tracker.upper)
            prior_time = v.number(last_application, "LAST_APPLICATION")
            if prior_time > now:
                raise v.BoundaryError("APPLICATION_TIME")
            import numpy as np

            rate = tracker.config.steering_rate * max(0.0, now - prior_time)
            command[0] = np.clip(command[0], prior[0] - rate, prior[0] + rate)
            self.components.validator(x, command)
            self.consumed.add(proposal.proposal_id)
            output = replace(
                proposal,
                time=now,
                sample_id=feedback.sample_id,
                command=tuple(command),
                stage="application_checked",
            )
            self.checked[proposal.proposal_id] = output
            self._event("check_application", now, output.status, output=output.__dict__)
            return output
        except Exception as error:
            return self._failure("check_application", now, error)

    def observe_applied(self, checked, feedback, now):
        """Caller assertion only. This records no physical acknowledgement."""
        try:
            self._check(feedback, now)
            if (
                checked.session != self.session_id
                or checked.stage != "application_checked"
                or self.checked.get(checked.proposal_id) != checked
                or checked.proposal_id in self.observed
                or now < checked.time
            ):
                raise v.BoundaryError("OBSERVATION_IDENTITY")
            self.observed.add(checked.proposal_id)
            self._event("caller_observed", now, "OBSERVED_BY_CALLER", output=checked.__dict__)
            return Output("OBSERVED_BY_CALLER", self.session_id, now, stage="caller_observed")
        except Exception as error:
            return self._failure("observe_applied", now, error)

    def close(self):
        self.closed = True
        self.pending, self.waiting = None, None
        self.issued.clear()
        return Output("CLOSED", self.session_id, None)
