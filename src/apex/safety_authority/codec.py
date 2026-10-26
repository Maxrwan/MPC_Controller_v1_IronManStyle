"""Strict immutable wire codec, exact decimal JSON and reference checks."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Literal, Union, get_args, get_origin, get_type_hints

from . import records as r


def freeze(value):
    """Convert a parsed JSON value to the explicit immutable input representation."""
    if isinstance(value, dict):
        return tuple(
            (k, freeze(v)) for k, v in sorted(value.items(), key=lambda x: x[0].encode("utf-8"))
        )
    if isinstance(value, (tuple, list)):
        return tuple(freeze(x) for x in value)
    if value is None or type(value) in (str, int, bool, Decimal):
        return value
    raise ValueError("non-exact JSON scalar")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def parse_json(text: str) -> r.FrozenJsonObject:
    def invalid(value):
        raise ValueError("nonfinite JSON: " + value)

    value = json.loads(
        text, parse_float=Decimal, parse_int=int, parse_constant=invalid, object_pairs_hook=_pairs
    )
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return freeze(value)


def _object(value):
    if type(value) is not tuple or any(
        type(x) is not tuple or len(x) != 2 or type(x[0]) is not str for x in value
    ):
        raise ValueError("FrozenJsonObject required")
    keys = tuple(x[0] for x in value)
    if keys != tuple(sorted(set(keys), key=lambda x: x.encode("utf-8"))):
        raise ValueError("duplicate or unsorted UTF-8 keys")
    return dict(value)


def _read(hint, value):
    origin, args = get_origin(hint), get_args(hint)
    if origin in (Union, type(int | str)):
        for member in args:
            try:
                return _read(member, value)
            except (TypeError, ValueError):
                pass
        raise ValueError("invalid union field")
    if origin is Literal:
        r._check(value, hint, "literal")
        return value
    if origin is tuple:
        if type(value) is not tuple:
            raise ValueError("tuple required")
        hints = (args[0],) * len(value) if len(args) == 2 and args[1] is Ellipsis else args
        if len(value) != len(hints):
            raise ValueError("tuple length")
        return tuple(_read(t, v) for t, v in zip(hints, value))
    if hint is Decimal:
        if type(value) not in (int, Decimal):
            raise ValueError("exact numeric scalar required")
        return Decimal(value)
    if is_dataclass(hint):
        data = _object(value)
        hints = get_type_hints(hint)
        if set(data) != set(hints):
            raise ValueError(hint.__name__ + ": missing or extra fields")
        return hint(**{key: _read(hints[key], val) for key, val in data.items()})
    r._check(value, hint, "scalar")
    return value


def _wire(value):
    if is_dataclass(value):
        return {f.name: _wire(getattr(value, f.name)) for f in fields(value)}
    if type(value) is tuple:
        return [_wire(x) for x in value]
    return value


def canonical_text(value) -> str:
    """Exact canonical JSON numbers; never reserialize Command.payload_utf8 for hashing."""
    value = _wire(value)
    if isinstance(value, dict):
        return (
            "{"
            + ",".join(
                json.dumps(k, ensure_ascii=False) + ":" + canonical_text(v)
                for k, v in sorted(value.items(), key=lambda x: x[0].encode("utf-8"))
            )
            + "}"
        )
    if isinstance(value, list):
        return "[" + ",".join(canonical_text(x) for x in value) + "]"
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("nonfinite number")
        return (
            format(value, "f").rstrip("0").rstrip(".")
            if "." in format(value, "f")
            else format(value, "f")
        )
    if value is None or type(value) in (str, bool, int):
        return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    raise ValueError("unsupported canonical value")


def digest(value) -> str:
    return sha256(canonical_text(value).encode("utf-8")).hexdigest()


def command_errors(command: r.Command) -> tuple[r.InputError, ...]:
    try:
        if sha256(command.payload_utf8.encode("utf-8")).hexdigest() != command.payload_sha256:
            raise ValueError("exact command digest mismatch")
        decoded = _object(parse_json(command.payload_utf8))
        hints = get_type_hints(r.Command)
        names = set(hints) - {"payload_sha256", "payload_utf8"}
        if set(decoded) != names:
            raise ValueError("command payload fields differ")
        if any(_read(hints[k], decoded[k]) != getattr(command, k) for k in names):
            raise ValueError("command payload values differ")
        return ()
    except (TypeError, ValueError, ArithmeticError) as exc:
        return (
            r.InputError(
                path="command.payload_utf8", reason_code="IDENTITY_CONFLICT", message=str(exc)
            ),
        )


def _failure(path, message, code="SCHEMA_INVALID"):
    return r.DecodeFailure(errors=(r.InputError(path=path, reason_code=code, message=message),))


def decode_configuration(
    document: r.FrozenJsonObject,
) -> r.DecodeSuccess[r.Configuration] | r.DecodeFailure:
    try:
        data = _object(document)
        if data.get("contract_version") != r.WIRE_VERSION:
            return _failure("contract_version", "explicit 0.2.0 required", "VERSION_UNSUPPORTED")
        cfg = _read(r.Configuration, document)
        if any(x.control_clock_id != cfg.control_clock_id for x in cfg.clock_mappings):
            raise ValueError("mapping target clock mismatch")
        return r.DecodeSuccess(value=cfg)
    except (TypeError, ValueError, ArithmeticError) as exc:
        return _failure("configuration", str(exc))


def snapshot_errors(
    snapshot: r.Snapshot, configuration: r.Configuration
) -> tuple[r.InputError, ...]:
    errors = []
    if snapshot.configuration_sha256 != digest(configuration):
        errors.append(
            r.InputError(
                path="configuration_sha256",
                reason_code="PERSISTENCE_UNKNOWN",
                message="configuration fingerprint mismatch",
            )
        )
    commands = {x.command_id: x for x in snapshot.commands}
    permissions = {x.permission_id: x for x in snapshot.permissions}
    for c in snapshot.commands:
        errors.extend(command_errors(c))
    for p in snapshot.permissions:
        c = commands.get(p.command_id)
        if c is None or (
            p.source_controller_id,
            p.source_packet_id,
            p.policy_id,
            p.generation_epoch,
            p.session_id,
        ) != (
            c.source_controller_id,
            c.source_packet_id,
            c.policy_id,
            c.generation_epoch,
            c.session_id,
        ):
            errors.append(
                r.InputError(
                    path="permissions",
                    reason_code="IDENTITY_CONFLICT",
                    message="permission source/generation reference mismatch",
                )
            )
    for c in snapshot.command_ledger:
        v = commands.get(c.command_id)
        if v is None or (v.producer_id, v.sequence, v.payload_sha256) != (
            c.producer_id,
            c.sequence,
            c.payload_sha256,
        ):
            errors.append(
                r.InputError(
                    path="command_ledger",
                    reason_code="PERSISTENCE_UNKNOWN",
                    message="command ledger reference mismatch",
                )
            )
    if not set(snapshot.pending_command_ids) <= set(commands) or not set(
        snapshot.revoked_permission_ids
    ) <= set(permissions):
        errors.append(
            r.InputError(
                path="snapshot.references",
                reason_code="PERSISTENCE_UNKNOWN",
                message="dangling identity",
            )
        )
    if (
        snapshot.active_packet is not None
        and snapshot.active_packet not in snapshot.accepted_packet_history
    ):
        errors.append(
            r.InputError(
                path="active_packet",
                reason_code="PERSISTENCE_UNKNOWN",
                message="active acceptance absent from history",
            )
        )
    if snapshot.trace_ledger and tuple(x.trace_sequence for x in snapshot.trace_ledger) != tuple(
        range(snapshot.trace_ledger[0].trace_sequence, snapshot.last_trace_sequence + 1)
    ):
        errors.append(
            r.InputError(
                path="trace_ledger",
                reason_code="PERSISTENCE_UNKNOWN",
                message="noncontiguous trace ledger",
            )
        )
    for ledger in snapshot.event_ledger:
        if any(n > snapshot.last_trace_sequence for n in ledger.original_trace_sequences):
            errors.append(
                r.InputError(
                    path="event_ledger",
                    reason_code="PERSISTENCE_UNKNOWN",
                    message="future trace reference",
                )
            )
    return tuple(errors)


def decode_snapshot(
    document: r.FrozenJsonObject, *, configuration: r.Configuration
) -> r.DecodeSuccess[r.Snapshot] | r.DecodeFailure:
    try:
        if _object(document).get("schema_version") != r.WIRE_VERSION:
            return _failure("schema_version", "explicit 0.2.0 required", "VERSION_UNSUPPORTED")
        snapshot = _read(r.Snapshot, document)
        errors = snapshot_errors(snapshot, configuration)
        return r.DecodeFailure(errors=errors) if errors else r.DecodeSuccess(value=snapshot)
    except (TypeError, ValueError, ArithmeticError) as exc:
        return _failure("snapshot", str(exc))


def decode_event(
    document: r.FrozenJsonObject, *, configuration: r.Configuration
) -> r.DecodeSuccess[r.Event] | r.DecodeFailure:
    try:
        data = _object(document)
        if set(data) != set(get_type_hints(r.Event)):
            raise ValueError("event fields differ")
        kind = data["kind"]
        if kind in (
            "COMMAND_DELIVER",
            "PERMISSION_DELIVER",
            "ENDPOINT_ESTIMATE_DELIVER",
            "ENDPOINT_EVIDENCE_DELIVER",
            "CANCEL_DELIVER",
            "ENDPOINT_COMMIT",
        ):
            return _failure("event.kind", "S1-B entry unavailable", "STAGE_NOT_ENABLED")
        if kind not in r.PAYLOAD_TYPES:
            raise ValueError("unknown event kind/version")
        payload = _read(r.PAYLOAD_TYPES[kind], data["payload"])
        values = {
            k: _read(t, data[k]) for k, t in get_type_hints(r.Event).items() if k != "payload"
        }
        event = r.Event(**values, payload=payload)
        c = payload.command if isinstance(payload, r.PermissionRequest) else payload
        if isinstance(c, r.Command):
            errors = command_errors(c)
            if errors:
                return r.DecodeFailure(errors=errors)
        return r.DecodeSuccess(value=event)
    except (TypeError, ValueError, ArithmeticError) as exc:
        return _failure("event", str(exc))


def encode_snapshot(snapshot: r.Snapshot) -> r.FrozenJsonObject:
    return freeze(_wire(snapshot))
