"""Pure S1-A authority transactions. Unverified; no endpoint implementation."""

from __future__ import annotations

from dataclasses import replace

from . import policy as p
from . import records as r
from .codec import canonical_text, command_errors, decode_event, digest, parse_json, snapshot_errors
from .ordering import EXCLUDED, event_key, phase, seal_batch
from .time import boundaries, validate_interval


class _Transaction:
    """Mutable working values are private to one pure call, never returned."""

    def __init__(self, cfg, snapshot, batch_id):
        self.cfg, self.s, self.batch_id = cfg, snapshot, batch_id
        self.initial_state = snapshot.state
        self.traces, self.transitions, self.denials, self.intents = [], [], [], []
        self.bumped_sessions = set()
        self.critical = []
        self.emergencies = []
        self.microsteps = {}

    def revoke(self, identities=None):
        ids = (
            tuple(
                x.permission_id
                for x in self.s.permissions
                if x.session_id == self.s.control_session_id
            )
            if identities is None
            else tuple(identities)
        )
        added = tuple(
            sorted(set(ids) - set(self.s.revoked_permission_ids), key=lambda x: x.encode("utf-8"))
        )
        self.s = replace(
            self.s,
            revoked_permission_ids=tuple(
                sorted(
                    set(self.s.revoked_permission_ids) | set(ids), key=lambda x: x.encode("utf-8")
                )
            ),
        )
        return added

    def bump(self):
        session = self.s.control_session_id
        if session not in self.bumped_sessions:
            self.s = replace(
                self.s, desired_epoch=self.s.desired_epoch + 1, epoch_barrier_ack_id=None
            )
            self.bumped_sessions.add(session)

    def latch(self, code, event, fault_id=None):
        identity = fault_id if fault_id is not None else "F_" + code
        prior = next((f for f in self.s.fault_latches if f.fault_id == identity), None)
        if prior is not None and (
            prior.reason != code
            or any(
                item[2] == identity and item[1].event_id != event.event_id for item in self.critical
            )
        ):
            identity += ":" + event.event_id
            prior = next((f for f in self.s.fault_latches if f.fault_id == identity), None)
        fault = r.FaultLatch(
            fault_id=identity,
            reason=code,
            first_detected_tick=prior.first_detected_tick if prior else self.s.current_tick,
            last_observed_tick=self.s.current_tick,
            latched=True,
            cleared_tick=None,
            clearance_evidence_ids=(),
        )
        self.s = replace(
            self.s,
            fault_latches=tuple(
                sorted(
                    tuple(f for f in self.s.fault_latches if f.fault_id != identity) + (fault,),
                    key=lambda f: (f.reason.encode("utf-8"), f.fault_id.encode("utf-8")),
                )
            ),
        )
        self.revoke()
        self.bump()
        self.critical.append((code, event, identity))

    def emit(
        self,
        event,
        before,
        decision,
        codes=(),
        *,
        transitions=(),
        revoked=(),
        granted=(),
        denial_key=(),
        microstep=0,
        observation=None,
    ):
        codes = r.reasons(*codes) or ("OK",)
        denial = None
        if decision == "REJECT" or any(
            c in ("SCHEMA_INVALID", "BATCH_INVALID", "CAUSALITY_INVALID", "VERSION_UNSUPPORTED")
            for c in codes
        ):
            denial = r.Denial(
                reason_codes=codes,
                denied_operation_key=denial_key or (event.kind, event.event_id),
                unknowns=(),
                permission_created=False,
            )
            self.denials.append(denial)
        payload = event.payload
        command = payload.command if isinstance(payload, r.PermissionRequest) else payload
        trace = r.Trace(
            trace_sequence=self.s.last_trace_sequence + 1,
            at_tick=self.s.current_tick,
            phase=phase(self.cfg, event),
            microstep=microstep,
            event_id=event.event_id,
            causal_parent_ids=event.causal_parent_ids,
            stage="S1-A",
            state_before=before,
            state_after=self.s.state,
            transition_path=tuple(t.transition_id for t in transitions),
            control_session_id=self.s.control_session_id,
            desired_epoch=self.s.desired_epoch,
            endpoint_installed_epoch=self.s.endpoint_installed_epoch,
            source_packet_id=getattr(command, "source_packet_id", None),
            command_id=getattr(command, "command_id", None),
            permission_id=getattr(payload, "permission_id", None),
            estimate_id=self.s.latest_estimate.estimate_id if self.s.latest_estimate else None,
            evidence_ids=getattr(payload, "evidence_ids", ()),
            decision=decision,
            reason_codes=codes,
            granted_permission_ids=tuple(granted),
            revoked_permission_ids=tuple(revoked),
            fault_ids=tuple(f.fault_id for f in self.s.fault_latches if f.cleared_tick is None),
            endpoint_observation=observation,
            unknowns=(
                r.UnknownField(
                    field="physical_application", reason="S1-A produces no endpoint application"
                ),
            ),
            physical_actuation_claim="NOT_OBSERVED_NOT_VALIDATED",
            decision_scope="SUPPLIED_OBSERVATION" if observation is not None else "HOST_LOGICAL",
            denial=denial,
            transition_records=tuple(transitions),
        )
        self.traces.append(trace)
        self.s = replace(
            self.s,
            last_trace_sequence=trace.trace_sequence,
            trace_ledger=self.s.trace_ledger + (trace,),
        )
        return trace

    def transition(self, identity, destination, cause, codes, evidence_ids=()):
        if identity not in self.cfg.enabled_transition_ids:
            raise ValueError("disabled transition dispatch")
        before = self.s.state
        revoked = self.revoke() if identity in ("T06", "T09", "T11", "T13", "T14") else ()
        self.s = replace(self.s, state=destination)
        record = r.TransitionRecord(
            transition_id=identity,
            state_before=before,
            state_after=destination,
            at_tick=self.s.current_tick,
            cause_event_id=cause.event_id,
            evidence_ids=tuple(evidence_ids),
            revoked_permission_ids=revoked,
            fault_ids=tuple(f.fault_id for f in self.s.fault_latches if f.cleared_tick is None),
        )
        self.transitions.append(record)
        step = self.microsteps.get(cause.event_id, 0) + 1
        self.microsteps[cause.event_id] = step
        internal = replace(
            cause, event_id=cause.event_id + ":" + identity, causal_parent_ids=(cause.event_id,)
        )
        self.emit(
            internal,
            before,
            "REVOKE" if identity in ("T06", "T09", "T14") else "OBSERVE",
            codes,
            transitions=(record,),
            revoked=revoked,
            microstep=step,
        )

    def flush_critical(self):
        if not self.critical:
            return
        facts = tuple(self.critical)
        self.critical.clear()
        cause = self.emergencies[0] if self.emergencies else facts[0][1]
        codes = r.reasons(*(x[0] for x in facts if x[0] in r.REASON_ORDER), "NO_VALID_POLICY")
        if self.emergencies and self.s.state in (
            "DISARMED",
            "NORMAL",
            "WARNING",
            "RECOVERY",
            "DECELERATING",
        ):
            self.transition("T06", "STOP_REQUESTED", cause, codes)
        if self.s.state == "STOPPED_LATCHED":
            self.transition("T14", "NO_VALID_POLICY", cause, codes)
        elif self.s.state not in ("NO_VALID_POLICY", "STOPPED_LATCHED"):
            self.transition("T09", "NO_VALID_POLICY", cause, codes)
        self.emergencies.clear()

    def continuation(self, cause):
        if self.s.state in ("RECOVERY", "DECELERATING", "STOP_REQUESTED", "STOPPING"):
            self.latch("NO_VALID_POLICY", cause, "F_POLICY_UNAVAILABLE")
        elif self.s.state in ("NORMAL", "WARNING"):
            # Current packet eligibility does not imply a prepared grant barrier.
            for code in p.nominal_codes(
                self.cfg, self.s, self.s.current_tick, require_barrier=False
            ):
                if code != "FAULT_LATCHED":
                    self.latch(code, cause)
        elif self.s.state == "STOPPED_LATCHED":
            for code in p.rest_codes(self.cfg, self.s, self.s.current_tick):
                self.latch(code, cause, "F_REST_LOST")

    def advance(self, target, *, defer_target=False):
        for tick in boundaries(self.cfg, self.s, target):
            self.s = replace(self.s, current_tick=tick)
            event = r.Event(
                event_id=self.batch_id + ":boundary:" + str(tick),
                producer_id="S1A_BOUNDARY",
                producer_sequence=tick,
                at_tick=tick,
                causal_parent_ids=(),
                kind="ADVANCE",
                payload=r.AdvancePayload(target_tick=tick),
            )
            before = self.s.state
            expired = tuple(
                x.permission_id
                for x in self.s.permissions
                if x.valid_until_tick <= tick
                and x.permission_id not in self.s.revoked_permission_ids
            )
            revoked = self.revoke(expired)
            if not (
                defer_target
                and tick == target
                and self.s.state in ("RECOVERY", "DECELERATING", "STOP_REQUESTED", "STOPPING")
            ):
                self.continuation(event)
            self.emit(
                event,
                before,
                "REVOKE" if revoked or self.critical else "NO_CHANGE",
                ("EXPIRED",) if revoked or self.critical else (),
                revoked=revoked,
            )
            if tick < target or not defer_target:
                self.flush_critical()
        self.s = replace(self.s, current_tick=target)

    def result(self):
        return r.Reduction(
            snapshot=self.s,
            traces=tuple(self.traces),
            transitions=tuple(self.transitions),
            denials=tuple(self.denials),
            cancellation_intents=tuple(self.intents),
        )


def _event_replay(tx, event):
    old = next((x for x in tx.s.event_ledger if x.event_id == event.event_id), None)
    if old is None:
        return False
    tx.emit(event, tx.s.state, "REPLAY_PRIOR_OUTCOME", ("DUPLICATE_PRIOR_OUTCOME",))
    return True


def _store_operation(tx, kind, key, content, trace, permissions=()):
    tx.s = replace(
        tx.s,
        operation_ledger=tx.s.operation_ledger
        + (
            r.OperationLedgerEntry(
                operation_kind=kind,
                operation_key=key,
                content_sha256=digest(content),
                result_trace_sequences=(trace.trace_sequence,),
                permission_ids=permissions,
            ),
        ),
    )


def _receipt(tx, event, command):
    errors = command_errors(command)
    if errors:
        tx.latch("IDENTITY_CONFLICT", event)
        return ("IDENTITY_CONFLICT",), False
    if command.session_id != tx.s.control_session_id:
        return ("SESSION_MISMATCH",), False
    old = next((c for c in tx.s.commands if c.command_id == command.command_id), None)
    if old is not None:
        if old != command:
            tx.latch("IDENTITY_CONFLICT", event)
            return ("IDENTITY_CONFLICT",), False
        return (), True
    floor = next(
        (f.sequence for f in tx.s.sequence_floors if f.producer_id == command.producer_id), -1
    )
    if command.sequence <= floor:
        return ("SEQUENCE_REORDERED",), False
    # Event registry grants a synthetic gateway role to carry this command.
    # It is not cryptographic producer authentication.
    tx.s = replace(
        tx.s,
        commands=tx.s.commands + (command,),
        sequence_floors=tuple(
            f for f in tx.s.sequence_floors if f.producer_id != command.producer_id
        )
        + (r.SequenceFloor(producer_id=command.producer_id, sequence=command.sequence),),
        command_ledger=tx.s.command_ledger
        + (
            r.CommandLedgerEntry(
                command_id=command.command_id,
                producer_id=command.producer_id,
                sequence=command.sequence,
                payload_sha256=command.payload_sha256,
                first_decision_id=event.event_id,
            ),
        ),
    )
    return (), False


def _command_operation(tx, event):
    payload, kind = event.payload, event.kind
    is_reauth = kind == "REAUTHORIZE"
    if is_reauth:
        command = next((c for c in tx.s.commands if c.command_id == payload.command_id), None)
        if command is None:
            tx.emit(event, tx.s.state, "REJECT", ("IDENTITY_CONFLICT",))
            return
        prior = next(
            (
                x
                for x in tx.s.permissions
                if x.permission_id == payload.prior_permission_id
                and x.command_id == command.command_id
            ),
            None,
        )
        key = (kind, command.command_id, payload.new_permission_id, payload.transition_id)
        pid, supersedes = payload.new_permission_id, payload.prior_permission_id
        start, end = payload.requested_permission_interval_ticks
        receipt_codes, duplicate = (), False
    else:
        command = payload.command if kind == "PERMISSION_REQUEST" else payload
        receipt_codes, duplicate = _receipt(tx, event, command)
        pid = payload.permission_id if kind == "PERMISSION_REQUEST" else None
        supersedes = payload.supersedes_permission_id if kind == "PERMISSION_REQUEST" else None
        key = (kind, command.command_id) + ((pid,) if pid else ())
        start, end = (
            max(tx.s.current_tick, command.requested_application_tick),
            command.held_until_tick,
        )
        prior = next((x for x in tx.s.permissions if x.permission_id == supersedes), None)
    if receipt_codes:
        tx.emit(event, tx.s.state, "REJECT", receipt_codes, denial_key=key)
        return
    old_op = next((x for x in tx.s.operation_ledger if x.operation_key == key), None)
    if old_op is not None and old_op.content_sha256 != digest(payload):
        tx.latch("IDENTITY_CONFLICT", event)
        tx.emit(event, tx.s.state, "REJECT", ("IDENTITY_CONFLICT",), denial_key=key)
        return
    if kind == "COMMAND_SUBMIT":
        codes = ("DUPLICATE_PRIOR_OUTCOME",) if duplicate else ()
        trace = tx.emit(event, tx.s.state, "REPLAY_PRIOR_OUTCOME" if duplicate else "ACCEPT", codes)
        if old_op is None:
            _store_operation(tx, kind, key, payload, trace)
        return
    # State/epoch/session/expiry/revocation guards precede historical replay.
    applied = any(
        x.command_id == command.command_id and x.outcome in ("SIMULATED_APPLIED", "TOO_LATE")
        for x in tx.s.acknowledgement_ledger
    )
    codes = p.permission_codes(
        tx.cfg,
        tx.s,
        command,
        tx.s.current_tick,
        start=start,
        end=end,
        bounds=(start, start),
        hold=command.held_until_tick,
        reauthorize=is_reauth,
    )
    extra = ["TOO_LATE"] if applied else []
    existing = next((x for x in tx.s.permissions if x.permission_id == pid), None)
    if existing is not None and old_op is None:
        extra.append("IDENTITY_CONFLICT")
    if is_reauth:
        if payload.transition_id in r.DISABLED:
            extra.append("TRANSITION_DISABLED")
        if prior is None or prior.session_id != tx.s.control_session_id:
            extra.append("SESSION_MISMATCH")
        if start < tx.s.current_tick or start < command.requested_application_tick:
            extra.append("TIME_INVALID")
        extra.extend(
            p.reauthorization_codes(tx.s, command, payload.evidence_ids, tx.s.current_tick, end)
        )
    elif supersedes is not None:
        if (
            prior is None
            or prior.command_id != command.command_id
            or prior.session_id != tx.s.control_session_id
            or prior.permission_id in tx.s.revoked_permission_ids
            or not prior.valid_from_tick <= tx.s.current_tick < prior.valid_until_tick
        ):
            extra.append("REVOKED")
    # Replay of an old denied attempt remains denied; no implicit retry/grant.
    if old_op is not None:
        if any(identity in tx.s.revoked_permission_ids for identity in old_op.permission_ids):
            extra.append("REVOKED")
        if any(
            x.permission_id in old_op.permission_ids and tx.s.current_tick >= x.valid_until_tick
            for x in tx.s.permissions
        ):
            extra.append("EXPIRED")
    all_codes = r.reasons(*codes, *extra)
    if all_codes:
        trace = tx.emit(event, tx.s.state, "REJECT", all_codes, denial_key=key)
    elif old_op is not None:
        tx.emit(
            event, tx.s.state, "REPLAY_PRIOR_OUTCOME", ("DUPLICATE_PRIOR_OUTCOME",), denial_key=key
        )
        return
    else:
        evidence_ids = (
            payload.evidence_ids
            if is_reauth
            else tuple(
                e.evidence_id
                for e in tx.s.evidence
                if e.kind in ("NOMINAL", "HEALTH", "QUEUE_BARRIER")
                and not p.evidence_codes(tx.s, e, tx.s.current_tick, through=end)
            )
        )
        permission = r.Permission(
            permission_id=pid,
            command_id=command.command_id,
            session_id=command.session_id,
            source_controller_id=command.source_controller_id,
            source_packet_id=command.source_packet_id,
            policy_id=command.policy_id,
            generation_epoch=command.generation_epoch,
            permission_epoch=tx.s.desired_epoch,
            valid_from_tick=start,
            valid_until_tick=end,
            latest_application_tick=command.latest_application_tick,
            held_until_tick=command.held_until_tick,
            estimate_id=tx.s.latest_estimate.estimate_id if is_reauth else command.estimate_id,
            evidence_ids=evidence_ids,
            reauthorization_of_permission_id=supersedes,
            transition_id=payload.transition_id if is_reauth else None,
            claim_scope="LOGICAL_PERMISSION_ONLY",
        )
        if supersedes is not None:
            tx.revoke((supersedes,))
        tx.s = replace(tx.s, permissions=tx.s.permissions + (permission,))
        trace = tx.emit(event, tx.s.state, "ACCEPT", granted=(pid,))
    if old_op is None:
        _store_operation(tx, kind, key, payload, trace, (pid,) if not all_codes else ())


def _process(tx, event):
    before, v, kind = tx.s.state, event.payload, event.kind
    if kind in EXCLUDED:
        tx.emit(event, before, "REJECT", ("STAGE_NOT_ENABLED",))
        return
    if _event_replay(tx, event):
        return
    operator = getattr(v, "operator_authorization_id", None)
    if not p.authorized(tx.cfg, event, operator):
        tx.emit(event, before, "REJECT", ("AUTHORIZATION_UNKNOWN",))
        return
    if kind in ("COMMAND_SUBMIT", "PERMISSION_REQUEST", "REAUTHORIZE"):
        _command_operation(tx, event)
        return
    if kind in ("ESTIMATE_OBSERVED", "EVIDENCE_OBSERVED"):
        identity = v.estimate_id if kind == "ESTIMATE_OBSERVED" else v.evidence_id
        key = (kind, identity)
        old = next((x for x in tx.s.operation_ledger if x.operation_key == key), None)
        seed = tx.s.latest_estimate if kind == "ESTIMATE_OBSERVED" else p.evidence(tx.s, identity)
        same_id = (
            seed is not None
            and getattr(seed, "estimate_id" if kind == "ESTIMATE_OBSERVED" else "evidence_id")
            == identity
        )
        if (old is not None and old.content_sha256 != digest(v)) or (same_id and seed != v):
            tx.latch("IDENTITY_CONFLICT", event)
            tx.emit(event, before, "REJECT", ("IDENTITY_CONFLICT",))
            return
    codes, decision, transition = (), "OBSERVE", None
    if kind == "EMERGENCY":
        tx.latch("EMERGENCY", event, v.fault_id)
        tx.emergencies.append(event)
        decision, codes = "REVOKE", ("NO_VALID_POLICY",)
    elif kind == "REVOKE_REQUEST":
        if v.new_epoch != tx.s.desired_epoch + (
            0 if tx.s.control_session_id in tx.bumped_sessions else 1
        ):
            codes, decision = ("EPOCH_MISMATCH",), "REJECT"
        else:
            tx.revoke()
            tx.bump()
            codes, decision = ("REVOKED",), "REVOKE"
    elif kind == "ESTIMATE_OBSERVED":
        tx.s = replace(tx.s, latest_estimate=v)
        codes = p.estimate_codes(tx.cfg, v, tx.s.current_tick)
        for code in codes:
            tx.latch(code, event)
        if codes:
            decision, codes = "REVOKE", r.reasons(*codes, "NO_VALID_POLICY")
        elif p.uncleared(tx.s):
            codes = ("FAULT_LATCHED",)
    elif kind == "EVIDENCE_OBSERVED":
        # Keep adverse evidence by kind effective even if an older ID was SATISFIED.
        tx.s = replace(
            tx.s, evidence=tuple(e for e in tx.s.evidence if e.evidence_id != v.evidence_id) + (v,)
        )
        codes = p.evidence_codes(tx.s, v, tx.s.current_tick)
        if v.kind == "REST_HOLD":
            if before == "NO_VALID_POLICY":
                codes = p.rest_codes(tx.cfg, tx.s, tx.s.current_tick, v)
                if not codes:
                    transition = ("T11", "STOPPED_LATCHED")
            elif before == "STOPPED_LATCHED" and codes:
                tx.latch("REST_LOST", event)
                codes, decision = ("NO_VALID_POLICY",), "REVOKE"
        elif v.kind in ("HEALTH", "NOMINAL", "CONTINUATION") and codes:
            for code in codes:
                tx.latch(code, event)
            decision, codes = "REVOKE", r.reasons(*codes, "NO_VALID_POLICY")
        if codes and decision == "OBSERVE":
            decision = "REJECT"
    elif kind == "PROPOSAL_READY":
        if any(x.packet_id == v.packet_id and x != v for x in tx.s.proposals):
            codes, decision = ("IDENTITY_CONFLICT",), "REJECT"
        else:
            tx.s = replace(
                tx.s, proposals=tx.s.proposals if v in tx.s.proposals else tx.s.proposals + (v,)
            )
            codes = ("PROPOSAL_ONLY",)
    elif kind == "AUTHORITY_ACCEPT":
        proposal = next((x for x in tx.s.proposals if x.packet_id == v.packet_id), None)
        acceptance = p.evidence(tx.s, v.acceptance_evidence_id)
        candidate = replace(
            tx.s, active_packet=v, active_policy_id=acceptance.policy_id if acceptance else None
        )
        codes = r.reasons(
            *p.packet_codes(tx.cfg, v), *p.evidence_codes(candidate, acceptance, tx.s.current_tick)
        )
        if (
            acceptance is None
            or acceptance.kind not in ("ACCEPTANCE", "NOMINAL")
            or not {"D_PACKET", "D_NOMINAL"} <= set(acceptance.domain_ids)
            or acceptance.source_packet_id != v.packet_id
        ):
            codes = r.reasons(*codes, "DOMAIN_UNKNOWN")
        if proposal is not None:
            codes = r.reasons(
                *codes,
                *p.evidence_codes(
                    candidate, p.evidence(tx.s, proposal.feasibility_evidence_id), tx.s.current_tick
                ),
            )
        if v.accepted_tick != tx.s.current_tick or v.ready_tick > tx.s.current_tick:
            codes = r.reasons(*codes, "TIME_INVALID")
        if proposal is None or any(
            getattr(proposal, name) != getattr(v, name)
            for name in (
                "source_controller_id",
                "source_manifest_sha256",
                "timestamps_s",
                "timestamp_control_tick_bounds",
                "clock_mapping_id",
                "authority_start_tick",
                "authority_end_tick",
                "frame_id",
                "map_id",
            )
        ):
            codes = r.reasons(*codes, "IDENTITY_CONFLICT")
        if p.uncleared(tx.s):
            codes = r.reasons(*codes, "FAULT_LATCHED")
        changing_owner = tx.s.active_packet is not None and (
            tx.s.active_packet.packet_id,
            tx.s.active_packet.source_controller_id,
        ) != (v.packet_id, v.source_controller_id)
        next_epoch = tx.s.desired_epoch + (
            0 if tx.s.control_session_id in tx.bumped_sessions else 1
        )
        prepared = (
            p.barrier(tx.s, tx.s.current_tick, session=tx.s.control_session_id, epoch=next_epoch)
            if changing_owner
            else None
        )
        if changing_owner and prepared is None:
            codes = r.reasons(*codes, "BARRIER_UNACKNOWLEDGED")
            tx.latch("BARRIER_UNACKNOWLEDGED", event)
        if codes:
            decision = "REJECT"
        else:
            if changing_owner:
                tx.revoke()
                tx.bump()
            tx.s = replace(
                tx.s,
                active_packet=v,
                active_policy_id=acceptance.policy_id,
                accepted_packet_history=tx.s.accepted_packet_history
                if v in tx.s.accepted_packet_history
                else tx.s.accepted_packet_history + (v,),
            )
            if prepared is not None:
                tx.s = replace(
                    tx.s,
                    endpoint_installed_epoch=prepared.installed_epoch,
                    endpoint_session_id=prepared.endpoint_session_id,
                    epoch_barrier_ack_id=prepared.ack_id,
                )
            decision = "ACCEPT"
    elif kind == "EPOCH_INSTALL":
        # Journal supplied installation facts in the operation ledger, not as an acknowledgement.
        key = (
            "EPOCH_INSTALL",
            v.barrier_id,
            v.target_control_session_id,
            v.endpoint_session_id,
            str(v.new_epoch),
        )
        old = next((x for x in tx.s.operation_ledger if x.operation_key == key), None)
        trace = tx.emit(event, before, "OBSERVE")
        if old is None:
            _store_operation(tx, kind, key, v, trace)
            tx.s = replace(
                tx.s,
                prepared_barrier_ids=tuple(sorted(set(tx.s.prepared_barrier_ids) | {v.barrier_id})),
            )
        return
    elif kind == "BARRIER_ACK_OBSERVED":
        prior = next((x for x in tx.s.barrier_acknowledgement_ledger if x.ack_id == v.ack_id), None)
        if prior is not None and prior != v:
            tx.latch("IDENTITY_CONFLICT", event)
            codes, decision = ("IDENTITY_CONFLICT",), "REJECT"
        elif (
            v.ack_observed_tick > tx.s.current_tick
            or v.installation_tick is not None
            and not v.endpoint_delivery_tick <= v.installation_tick <= v.ack_observed_tick
        ):
            codes, decision = ("TIME_INVALID",), "REJECT"
        else:
            tx.s = replace(
                tx.s,
                barrier_acknowledgement_ledger=tx.s.barrier_acknowledgement_ledger
                if prior
                else tx.s.barrier_acknowledgement_ledger + (v,),
            )
            key = (
                "EPOCH_INSTALL",
                v.barrier_id,
                v.control_session_id,
                v.endpoint_session_id,
                str(v.installed_epoch),
            )
            if (
                any(x.operation_key == key for x in tx.s.operation_ledger)
                and v.control_session_id == tx.s.control_session_id
                and v.installed_epoch == tx.s.desired_epoch
                and v.outcome == "INSTALLED"
                and v.queue_cleared
                and v.installation_tick is not None
            ):
                tx.s = replace(
                    tx.s,
                    endpoint_session_id=v.endpoint_session_id,
                    endpoint_installed_epoch=v.installed_epoch,
                    epoch_barrier_ack_id=v.ack_id,
                )
    elif kind == "ENDPOINT_OBSERVATION":
        old = next((x for x in tx.s.acknowledgement_ledger if x.ack_id == v.ack_id), None)
        if old is not None and old != v:
            tx.latch("IDENTITY_CONFLICT", event)
            codes, decision = ("IDENTITY_CONFLICT",), "REJECT"
        elif v.receipt_tick > tx.s.current_tick or (
            v.ack_observed_tick is not None and v.ack_observed_tick > tx.s.current_tick
        ):
            codes, decision = ("TIME_INVALID",), "REJECT"
        else:
            tx.s = replace(
                tx.s,
                acknowledgement_ledger=tx.s.acknowledgement_ledger
                if old
                else tx.s.acknowledgement_ledger + (v,),
            )
            # A delayed observation never asserts a presently held input.
            tx.emit(event, before, "OBSERVE", ("APPLICATION_UNKNOWN",), observation=v)
            return
    elif kind in ("POLICY_SELECT", "REENTRY_REQUEST"):
        codes = r.reasons("TRANSITION_DISABLED", *("FAULT_LATCHED",) if p.uncleared(tx.s) else ())
        for identity in v.evidence_ids:
            codes = r.reasons(
                *codes, *p.evidence_codes(tx.s, p.evidence(tx.s, identity), tx.s.current_tick)
            )
        decision = "REJECT"
    elif kind == "ARM_REQUEST":
        codes = p.nominal_codes(tx.cfg, tx.s, tx.s.current_tick)
        for identity in v.evidence_ids:
            codes = r.reasons(
                *codes, *p.evidence_codes(tx.s, p.evidence(tx.s, identity), tx.s.current_tick)
            )
        if before != "DISARMED":
            codes = r.reasons(
                *codes, "FAULT_LATCHED" if p.uncleared(tx.s) else "TRANSITION_DISABLED"
            )
        if not codes:
            transition, decision = ("T01", "NORMAL"), "ACCEPT"
        else:
            decision = "REJECT"
    elif kind in ("RENEWAL_WARNING", "WARNING_CLEAR"):
        codes = p.nominal_codes(tx.cfg, tx.s, tx.s.current_tick)
        ids = (v.evidence_id,) if kind == "RENEWAL_WARNING" else v.evidence_ids
        required = (
            tx.cfg.warning_policy_evidence_id
            if kind == "RENEWAL_WARNING"
            else tx.cfg.reentry_policy_evidence_id
        )
        if required not in ids:
            codes = r.reasons(*codes, "DOMAIN_UNKNOWN")
        for identity in ids:
            codes = r.reasons(
                *codes, *p.evidence_codes(tx.s, p.evidence(tx.s, identity), tx.s.current_tick)
            )
        expected = "NORMAL" if kind == "RENEWAL_WARNING" else "WARNING"
        if before != expected:
            codes = r.reasons(*codes, "TRANSITION_DISABLED")
        if kind == "WARNING_CLEAR" and (
            tx.s.active_packet is None
            or tx.s.active_packet.acceptance_id != v.acceptance_id
            or not any(x.acceptance_id == v.acceptance_id for x in tx.s.accepted_packet_history)
        ):
            codes = r.reasons(*codes, "DOMAIN_UNKNOWN")
        if not codes:
            transition, decision = (
                (("T02", "WARNING") if kind == "RENEWAL_WARNING" else ("T03", "NORMAL")),
                "ACCEPT",
            )
        else:
            decision = "REJECT"
    elif kind == "RESET_REQUEST":
        codes = p.rest_codes(tx.cfg, tx.s, tx.s.current_tick)
        if tx.s.control_session_id in tx.bumped_sessions:
            codes = r.reasons(*codes, "FAULT_LATCHED", "RESET_NOT_ADMISSIBLE")
        for identity in v.clearance_evidence_ids:
            codes = r.reasons(
                *codes, *p.evidence_codes(tx.s, p.evidence(tx.s, identity), tx.s.current_tick)
            )
        ev = tuple(p.evidence(tx.s, identity) for identity in v.clearance_evidence_ids)
        if not {"HEALTH", "REST_HOLD", "FAULT_CLEARANCE"} <= {x.kind for x in ev if x is not None}:
            codes = r.reasons(*codes, "RESET_NOT_ADMISSIBLE")
        ack = p.barrier(
            tx.s,
            tx.s.current_tick,
            session=v.new_session_id,
            barrier_id=v.queue_barrier_evidence_id,
            epoch=tx.s.desired_epoch + 1,
        )
        if ack is None or p.evidence_codes(
            tx.s, p.evidence(tx.s, v.queue_barrier_evidence_id), tx.s.current_tick
        ):
            codes = r.reasons(*codes, "BARRIER_UNACKNOWLEDGED", "RESET_NOT_ADMISSIBLE")
        if before != "STOPPED_LATCHED" or v.new_session_id == tx.s.control_session_id:
            codes = r.reasons(*codes, "RESET_NOT_ADMISSIBLE")
        if not codes:
            # Clearance assertion applies to the initiating fault set only under
            # this explicit reset; retain every historical record and ledger.
            tx.revoke()
            tx.s = replace(
                tx.s,
                control_session_id=v.new_session_id,
                desired_epoch=ack.installed_epoch,
                fault_latches=tuple(
                    replace(
                        f,
                        cleared_tick=tx.s.current_tick,
                        clearance_evidence_ids=v.clearance_evidence_ids,
                    )
                    if f.cleared_tick is None
                    else f
                    for f in tx.s.fault_latches
                ),
                active_packet=None,
                active_policy_id=None,
                endpoint_session_id=ack.endpoint_session_id,
                endpoint_installed_epoch=ack.installed_epoch,
                epoch_barrier_ack_id=ack.ack_id,
                pending_command_ids=(),
            )
            transition, decision = ("T13", "DISARMED"), "ACCEPT"
        else:
            decision, codes = "REJECT", r.reasons(*codes, "RESET_NOT_ADMISSIBLE")
    elif kind == "CANCEL_REQUEST":
        permission = next(
            (
                x
                for x in tx.s.permissions
                if x.permission_id == v.permission_id
                and x.command_id == v.command_id
                and x.session_id == v.session_id
            ),
            None,
        )
        if (
            permission is None
            or v.session_id != tx.s.control_session_id
            or v.outcome != "REQUESTED"
            or v.ack_id is not None
            or v.endpoint_delivery_tick is not None
            or v.requested_tick != tx.s.current_tick
        ):
            codes, decision = ("SCHEMA_INVALID",), "REJECT"
        elif any(
            x.cancellation_id == v.cancellation_id and x != v for x in tx.s.cancellation_history
        ):
            codes, decision = ("IDENTITY_CONFLICT",), "REJECT"
        else:
            tx.revoke((v.permission_id,))
            if v not in tx.s.cancellation_history:
                tx.s = replace(tx.s, cancellation_history=tx.s.cancellation_history + (v,))
                tx.intents.append(v)
            decision, codes = "REQUEST_CANCEL", ("CANCEL_PENDING",)
    elif kind == "APPLICATION_CHECK":
        permission = next(
            (
                x
                for x in tx.s.permissions
                if x.permission_id == v.permission_id and x.command_id == v.command_id
            ),
            None,
        )
        command = next((x for x in tx.s.commands if x.command_id == v.command_id), None)
        if permission is None or command is None:
            codes = ("IDENTITY_CONFLICT",)
        elif permission.session_id != tx.s.control_session_id:
            codes = ("SESSION_MISMATCH",)
        elif permission.permission_id in tx.s.revoked_permission_ids:
            codes = (
                ("EXPIRED",) if tx.s.current_tick >= permission.valid_until_tick else ("REVOKED",)
            )
        elif permission.permission_epoch != tx.s.desired_epoch:
            codes = ("EPOCH_MISMATCH",)
        elif (
            v.application_tick_bounds[0] < tx.s.current_tick
            or v.hold_end_tick > permission.held_until_tick
        ):
            codes = ("TIME_INVALID",)
        else:
            codes = r.reasons(
                *(
                    x.reason_code
                    for x in validate_interval(
                        start=permission.valid_from_tick,
                        end=permission.valid_until_tick,
                        application_bounds=v.application_tick_bounds,
                        latest_application=permission.latest_application_tick,
                        hold_end=v.hold_end_tick,
                    )
                )
            )
            if not codes:
                codes = p.permission_codes(
                    tx.cfg,
                    tx.s,
                    command,
                    tx.s.current_tick,
                    start=permission.valid_from_tick,
                    end=permission.valid_until_tick,
                    bounds=v.application_tick_bounds,
                    hold=v.hold_end_tick,
                    reauthorize=permission.reauthorization_of_permission_id is not None,
                )
                if permission.reauthorization_of_permission_id is not None:
                    codes = r.reasons(
                        *codes,
                        *p.reauthorization_codes(
                            tx.s,
                            command,
                            permission.evidence_ids,
                            tx.s.current_tick,
                            v.hold_end_tick,
                        ),
                    )
        decision = "REJECT" if codes else "ACCEPT"
    elif kind == "ADVANCE":
        if v.target_tick != event.at_tick:
            codes, decision = ("TIME_INVALID",), "REJECT"
        else:
            decision = "NO_CHANGE"
    elif kind == "RESTART":
        valid = (
            v.snapshot_revision == tx.s.persistence_revision
            and v.endpoint_session_id == tx.s.endpoint_session_id
            and set(v.restored_latch_ids) == {x.fault_id for x in tx.s.fault_latches}
            and not p.evidence_codes(
                tx.s, p.evidence(tx.s, v.integrity_evidence_id), tx.s.current_tick
            )
        )
        if not valid:
            tx.latch("PERSISTENCE_UNKNOWN", event)
            decision, codes = "REVOKE", ("PERSISTENCE_UNKNOWN", "NO_VALID_POLICY")
        else:
            codes = ("FAULT_LATCHED",) if p.uncleared(tx.s) else ()
    else:
        decision, codes = "REJECT", ("SCHEMA_INVALID",)
    trace = tx.emit(event, before, decision, codes)
    if kind in ("ESTIMATE_OBSERVED", "EVIDENCE_OBSERVED") and old is None:
        _store_operation(tx, kind, key, v, trace)
    if transition is not None:
        tx.transition(*transition, event, codes, getattr(v, "evidence_ids", ()))


def _journal(tx, events):
    ledger = list(tx.s.event_ledger)
    known = {x.event_id for x in ledger}
    watermarks = {x.producer_id: x.sequence for x in tx.s.event_high_watermarks}
    for e in events:
        if e.event_id not in known:
            traces = tuple(
                t.trace_sequence
                for t in tx.traces
                if t.event_id == e.event_id or e.event_id in t.causal_parent_ids
            )
            ledger.append(
                r.EventLedgerEntry(
                    event_id=e.event_id,
                    producer_id=e.producer_id,
                    producer_sequence=e.producer_sequence,
                    payload_sha256=digest(e),
                    original_trace_sequences=traces,
                )
            )
            watermarks[e.producer_id] = max(e.producer_sequence, watermarks.get(e.producer_id, -1))
    batch_key = ("SEALED_BATCH", tx.batch_id)
    if not any(x.operation_key == batch_key for x in tx.s.operation_ledger):
        tx.s = replace(
            tx.s,
            operation_ledger=tx.s.operation_ledger
            + (
                r.OperationLedgerEntry(
                    operation_kind="SEALED_BATCH",
                    operation_key=batch_key,
                    content_sha256=digest(events),
                    result_trace_sequences=tuple(t.trace_sequence for t in tx.traces),
                    permission_ids=tuple(
                        pid for t in tx.traces for pid in t.granted_permission_ids
                    ),
                ),
            ),
        )
    tx.s = replace(
        tx.s,
        event_ledger=tuple(sorted(ledger, key=lambda x: x.event_id.encode("utf-8"))),
        event_high_watermarks=tuple(
            r.ProducerWatermark(producer_id=k, sequence=v)
            for k, v in sorted(watermarks.items(), key=lambda x: x[0].encode("utf-8"))
        ),
    )


def reduce_batch(
    configuration: r.Configuration, snapshot: r.Snapshot, batch: r.SealedBatch
) -> r.Reduction:
    sealed = seal_batch(
        configuration, snapshot, batch_id=batch.batch_id, at_tick=batch.at_tick, events=batch.events
    )
    errors = sealed.errors if isinstance(sealed, r.DecodeFailure) else ()
    if isinstance(sealed, r.DecodeSuccess) and sealed.value != batch:
        errors += (
            r.InputError(
                path="batch.fingerprints",
                reason_code="BATCH_INVALID",
                message="stale/forged sealed input",
            ),
        )
    if errors:
        known = tuple(
            e
            for e in batch.events
            if e.kind in ("EMERGENCY", "ESTIMATE_OBSERVED", "EVIDENCE_OBSERVED")
            and p.authorized(configuration, e)
        )
        return reject_batch(
            configuration,
            snapshot,
            batch_id=batch.batch_id,
            at_tick=batch.at_tick,
            errors=errors,
            known_critical_events=known,
        )
    tx = _Transaction(configuration, snapshot, batch.batch_id)
    tx.advance(batch.at_tick, defer_target=True)
    zero = tuple(e for e in batch.events if phase(configuration, e) == 0)
    for e in zero:
        _process(tx, e)
    tx.flush_critical()
    for e in (x for x in batch.events if phase(configuration, x) in (1, 2)):
        _process(tx, e)
        tx.flush_critical()
    cause = (
        batch.events[0]
        if batch.events
        else r.Event(
            event_id=batch.batch_id + ":continuation",
            producer_id="S1A_BOUNDARY",
            producer_sequence=batch.at_tick,
            at_tick=batch.at_tick,
            causal_parent_ids=(),
            kind="ADVANCE",
            payload=r.AdvancePayload(target_tick=batch.at_tick),
        )
    )
    tx.continuation(cause)
    tx.flush_critical()
    for e in (x for x in batch.events if phase(configuration, x) >= 3):
        _process(tx, e)
        tx.flush_critical()
    _journal(tx, batch.events)
    return tx.result()


def reject_batch(
    configuration: r.Configuration,
    snapshot: r.Snapshot,
    *,
    batch_id: str,
    at_tick: r.Tick,
    errors: tuple[r.InputError, ...],
    known_critical_events: tuple[r.Event, ...],
) -> r.Reduction:
    tx = _Transaction(configuration, snapshot, batch_id)
    # Invalid time cannot move history backwards; retain the known current tick.
    target = (
        max(snapshot.current_tick, at_tick)
        if type(at_tick) is int and at_tick >= 0
        else snapshot.current_tick
    )
    tx.advance(target, defer_target=True)
    marker = r.Event(
        event_id=batch_id + ":rejected",
        producer_id="S1A_REJECTION",
        producer_sequence=target,
        at_tick=target,
        causal_parent_ids=(),
        kind="ADVANCE",
        payload=r.AdvancePayload(target_tick=target),
    )
    accepted = []
    for e in sorted(known_critical_events, key=lambda x: event_key(configuration, x)):
        # Validate each record independently: callers cannot smuggle arbitrary
        # permissive events through the rejected-batch escape path.
        decoded = decode_event(parse_json(canonical_text(e)), configuration=configuration)
        if (
            isinstance(decoded, r.DecodeFailure)
            or e.at_tick != target
            or not p.authorized(configuration, e)
        ):
            continue
        is_critical = (
            e.kind in ("EMERGENCY", "REVOKE_REQUEST")
            or (
                e.kind == "ESTIMATE_OBSERVED"
                and bool(p.estimate_codes(configuration, e.payload, target))
            )
            or (
                e.kind == "EVIDENCE_OBSERVED"
                and e.payload.kind in ("HEALTH", "NOMINAL", "CONTINUATION", "REST_HOLD")
                and bool(p.evidence_codes(snapshot, e.payload, target))
            )
        )
        if is_critical:
            _process(tx, e)
            accepted.append(e)
    for error in errors:
        quarantined = error.path.startswith("untrusted_proposal.") and error.reason_code in (
            "SCHEMA_INVALID",
            "VERSION_UNSUPPORTED",
        )
        if not quarantined and error.reason_code != "STAGE_NOT_ENABLED":
            tx.latch(error.reason_code, marker)
    tx.flush_critical()
    tx.continuation(marker)
    tx.flush_critical()
    closed = any(t.transition_id in ("T06", "T09", "T14") for t in tx.transitions)
    tx.emit(
        marker,
        snapshot.state,
        "REVOKE" if closed else "REJECT",
        r.reasons(*(e.reason_code for e in errors), *("NO_VALID_POLICY",) if closed else ())
        or ("BATCH_INVALID",),
    )
    _journal(tx, tuple(accepted))
    return tx.result()


def restore_snapshot(
    configuration: r.Configuration,
    *,
    saved: r.Snapshot | r.DecodeFailure | None,
    integrity: r.Evidence | None,
    restart: r.RestartInput,
) -> r.Reduction:
    good = (
        isinstance(saved, r.Snapshot)
        and not snapshot_errors(saved, configuration)
        and restart.saved_snapshot_sha256 == digest(saved)
        and restart.at_tick >= saved.current_tick
        and integrity is not None
        and integrity.result == "SATISFIED"
        and integrity.claim_scope == "SYNTHETIC_ASSUMPTION"
        and integrity.valid_from_tick <= restart.at_tick < integrity.valid_until_tick
        and not p.evidence_codes(saved, integrity, restart.at_tick)
        and restart.boot_control_session_id == saved.control_session_id
        and restart.endpoint_session_id == saved.endpoint_session_id
    )
    if good:
        tx = _Transaction(configuration, saved, restart.event_id)
        tx.advance(restart.at_tick)
        e = r.Event(
            event_id=restart.event_id,
            producer_id="S1A_RESTART",
            producer_sequence=restart.at_tick,
            at_tick=restart.at_tick,
            causal_parent_ids=(),
            kind="ADVANCE",
            payload=r.AdvancePayload(target_tick=restart.at_tick),
        )
        tx.emit(e, saved.state, "OBSERVE", ("FAULT_LATCHED",) if p.uncleared(tx.s) else ())
        return tx.result()
    # Missing/corrupt persistence cannot be guessed or restored from a partial
    # object. Boot data is explicit and grants nothing. Physical input is unknown.
    boot = r.Snapshot(
        schema_version=r.WIRE_VERSION,
        state="DISARMED",
        control_session_id=restart.boot_control_session_id,
        current_tick=restart.at_tick,
        desired_epoch=0,
        endpoint_installed_epoch=None,
        endpoint_session_id=restart.endpoint_session_id,
        epoch_barrier_ack_id=None,
        active_packet=None,
        active_policy_id=None,
        proposals=(),
        accepted_packet_history=(),
        cancellation_history=(),
        acknowledgement_ledger=(),
        barrier_acknowledgement_ledger=(),
        latest_estimate=None,
        evidence=(),
        permissions=(),
        revoked_permission_ids=(),
        commands=(),
        pending_command_ids=(),
        held_observation=None,
        held_unknown_reason="Persistence missing/corrupt; application and held input unknown",
        fault_latches=(),
        sequence_floors=(),
        command_ledger=(),
        event_high_watermarks=(),
        last_trace_sequence=0,
        persistence_revision=restart.event_id,
        event_ledger=(),
        operation_ledger=(),
        configuration_sha256=digest(configuration),
        prepared_barrier_ids=(),
        trace_ledger=(),
    )
    tx = _Transaction(configuration, boot, restart.event_id)
    e = r.Event(
        event_id=restart.event_id,
        producer_id="S1A_RESTART",
        producer_sequence=restart.at_tick,
        at_tick=restart.at_tick,
        causal_parent_ids=(),
        kind="ADVANCE",
        payload=r.AdvancePayload(target_tick=restart.at_tick),
    )
    tx.latch("PERSISTENCE_UNKNOWN", e)
    tx.emit(e, boot.state, "REVOKE", ("PERSISTENCE_UNKNOWN", "NO_VALID_POLICY"))
    tx.flush_critical()
    return tx.result()
