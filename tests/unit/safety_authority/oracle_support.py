"""O4B literal comparator, authored but NOT EXECUTED or independently accepted.

Only actual inputs/results use the SUT. Expected records are read literally.
The sole representation projection is dataclass -> object, tuple -> array, with
exact JSON number values (int/Decimal, excluding bool); no ID/text/hash mapping.

Future entry requires APEX_S1A_REVIEW_FILE (an absolute file outside this repo)
and APEX_S1A_REVIEW_SHA256 (its independently supplied byte digest). The owner or
review authority must authenticate that review out of band: environment values
and reviewer attestations alone cannot prove a person's independence. This chat
must not author an approval. Review admission is NOT execution authorization.

Review document schema apex-s1a/independent-review/1 requires candidate_revision,
materialization_version, decision=APPROVED_FOR_FOCUSED_SELECTION, reviewer_id,
review_record_ref, independent_of_implementation_and_oracle_authors=true,
comparison_policy=EXACT_LITERAL_NO_IDENTIFIER_MAPPING,
file_sha256 (all seven source, four fixture and two comparator paths),
accepted_case_ids (nonempty), and excluded_cases [{case_id, reason,
status: NOT_RUN_NOT_PASS}]. These sets must partition the entire population.
Partial/unresolved cases cannot be accepted. Fixture review flags stay unchanged.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from pprint import pformat

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests/fixtures/safety_authority/s1a"
CANDIDATE_REVISION = "f3c80f3aaeb18318e08f9ef976cfce711bb1690f"
SOURCE_PATHS = tuple(
    "src/apex/safety_authority/" + name + ".py"
    for name in ("__init__", "records", "codec", "time", "ordering", "policy", "reducer")
)
REVIEW_PATHS = SOURCE_PATHS + tuple(
    "tests/fixtures/safety_authority/s1a/" + name + ".json"
    for name in ("configurations", "snapshots", "cases", "expected_traces")
) + (
    "tests/unit/safety_authority/oracle_support.py",
    "tests/unit/safety_authority/test_oracle_cases.py",
)
MISSING = object()


def _json(text, *, exact=True):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Non-finite JSON number: " + value)

    return json.loads(
        text, parse_float=Decimal if exact else float,
        parse_constant=invalid, object_pairs_hook=unique,
    )


def load(name):
    return _json((FIXTURES / (name + ".json")).read_text())


def cases():
    return load("cases")["cases"]


def resolve(reference, records, namespace):
    """Resolve RFC6901 tokens in the fixture's virtual records namespace."""
    prefix = "#/" + namespace + "/"
    if not isinstance(reference, str) or not reference.startswith(prefix):
        raise ValueError("Unexpected fixture reference: " + repr(reference))
    value = records
    for token in reference[len(prefix):].split("/"):
        value = value[token.replace("~1", "/").replace("~0", "~")]
    return value


def _binding(name, reference, namespace, expected_hash):
    # Historical authoring hashes use Python JSON's numeric spelling. This raw
    # parse is for input binding only; float values NEVER enter oracle comparison.
    records = _json((FIXTURES / (name + ".json")).read_text(), exact=False)
    literal = resolve(reference, records, namespace)
    encoded = json.dumps(literal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if hashlib.sha256(encoded.encode()).hexdigest() != expected_hash:
        raise ValueError("Fixture binding changed: " + reference)
    return resolve(reference, load(name), namespace)


def _snapshot_literal(reference, expected_hash):
    if reference is None:
        if expected_hash is not None:
            raise ValueError("Missing saved history cannot have a trusted snapshot digest")
        return None
    return _binding("snapshots", reference, "snapshot_records", expected_hash)


def population():
    inputs, expected = load("cases"), load("expected_traces")
    result = {}
    for case in inputs["cases"]:
        cid = case["case_id"]
        literal = expected["full_trace_cases"].get(cid)
        partial = expected["partial_trace_cases"].get(cid)
        if (literal is None) == (partial is None) or cid in result:
            raise ValueError("Missing/ambiguous core identity: " + cid)
        result[cid] = ("core", case, literal or partial)
    for input_group, full_group, partial_group in (
        ("original_materializations", "original_full_trace_cases", "original_partial_trace_cases"),
        ("additional_adjudication_materializations", "additional_adjudication_trace_cases", None),
    ):
        for case in inputs[input_group]:
            cid = case["case_id"]
            literal = expected[full_group].get(cid)
            partial = expected[partial_group].get(cid) if partial_group else None
            if (literal is None) == (partial is None) or cid in result:
                raise ValueError("Missing/ambiguous scenario identity: " + cid)
            result[cid] = (input_group, case, literal or partial)
    return result


def independent_review():
    """Fail closed before selection or any project import; never auto-approve."""
    path = Path(os.environ.get("APEX_S1A_REVIEW_FILE", ""))
    pinned = os.environ.get("APEX_S1A_REVIEW_SHA256", "")
    if not path.is_absolute() or path.resolve().is_relative_to(ROOT) or not path.is_file():
        raise ValueError("BLOCKED: separately supplied external independent review required")
    raw = path.read_bytes()
    if len(pinned) != 64 or hashlib.sha256(raw).hexdigest() != pinned:
        raise ValueError("BLOCKED: externally supplied review digest missing/mismatched")
    approval = _json(raw)
    required = {
        "schema": "apex-s1a/independent-review/1",
        "candidate_revision": CANDIDATE_REVISION,
        "materialization_version": load("expected_traces")["materialization_version"],
        "decision": "APPROVED_FOR_FOCUSED_SELECTION",
        "comparison_policy": "EXACT_LITERAL_NO_IDENTIFIER_MAPPING",
        "independent_of_implementation_and_oracle_authors": True,
    }
    for key, value in required.items():
        if type(approval.get(key)) is not type(value) or approval[key] != value:
            raise ValueError("BLOCKED: invalid independent review field " + key)
    for key in ("reviewer_id", "review_record_ref"):
        if not isinstance(approval.get(key), str) or not approval[key].strip():
            raise ValueError("BLOCKED: missing external review provenance " + key)
    bindings = approval.get("file_sha256", {})
    if set(bindings) != set(REVIEW_PATHS):
        raise ValueError("BLOCKED: review must bind all source/fixture/comparator files")
    for relative in REVIEW_PATHS:
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != bindings[relative]:
            raise ValueError("BLOCKED: reviewed bytes changed: " + relative)
    all_cases = population()
    selected = approval.get("accepted_case_ids")
    exclusions = approval.get("excluded_cases")
    if not isinstance(selected, list) or not selected or not all(isinstance(x, str) for x in selected):
        raise ValueError("BLOCKED: explicit nonempty accepted case list required")
    if len(set(selected)) != len(selected) or not isinstance(exclusions, list):
        raise ValueError("BLOCKED: duplicate selection or missing exclusions")
    excluded_ids = []
    for entry in exclusions:
        if (not isinstance(entry, dict) or entry.get("status") != "NOT_RUN_NOT_PASS"
                or not isinstance(entry.get("reason"), str) or not entry["reason"].strip()
                or not isinstance(entry.get("case_id"), str)):
            raise ValueError("BLOCKED: every exclusion needs identity/reason/NOT_RUN_NOT_PASS")
        excluded_ids.append(entry["case_id"])
    if (len(set(excluded_ids)) != len(excluded_ids) or set(selected) & set(excluded_ids)
            or set(selected) | set(excluded_ids) != set(all_cases)):
        raise ValueError("BLOCKED: selection/exclusions must partition the whole population")
    for cid in selected:
        _, case, literal = all_cases[cid]
        if (literal.get("authorship_status") != "COMPLETE_LITERAL_CANDIDATE"
                or literal.get("unresolved") or literal.get("unresolved_scientific_fields")
                or case.get("authorship_status", "COMPLETE_LITERAL_CANDIDATE")
                != "COMPLETE_LITERAL_CANDIDATE"):
            raise ValueError("BLOCKED: incomplete/contested oracle: " + cid)
    return approval


def approved_selection():
    return tuple(independent_review()["accepted_case_ids"])


def _admit(case_id):
    if case_id not in approved_selection():
        raise ValueError("NOT_RUN_NOT_PASS: case excluded from independent approval: " + case_id)
    return population()[case_id]


def _sut():
    # Called ONLY after admission. No import/guard/ordering helper supplies EXPECTED.
    from apex.safety_authority import codec, ordering, records, reducer

    return records, codec, ordering, reducer


def shape(value):
    """Lossless record projection; preserve all fields, order, nulls and text."""
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: shape(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [shape(item) for item in value]
    return value


@dataclass(frozen=True)
class Difference:
    path: str
    expected: object
    actual: object
    kind: str = "VALUE_MISMATCH"


def differences(expected, actual, path="$"):
    """All structural differences, including extra fields/elements; never repair."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        found = []
        for key in sorted(set(expected) | set(actual)):
            child = path + "/" + key.replace("~", "~0").replace("/", "~1")
            found.extend(differences(expected.get(key, MISSING), actual.get(key, MISSING), child))
        return found
    if isinstance(expected, list) and isinstance(actual, list):
        return [d for i in range(max(len(expected), len(actual))) for d in differences(
            expected[i] if i < len(expected) else MISSING,
            actual[i] if i < len(actual) else MISSING, path + "/" + str(i))]
    if expected is MISSING or actual is MISSING:
        return [Difference(path, expected, actual, "MISSING_EXPECTED" if expected is MISSING
                           else "MISSING_ACTUAL")]
    numeric = (int, Decimal)
    equal = (type(expected) in numeric and type(actual) in numeric and expected == actual)
    if equal or (type(expected) is type(actual) and expected == actual):
        return []
    return [Difference(path, expected, actual)]


@dataclass
class Comparison:
    identity: str
    expected: object
    actual: object
    differences: list = field(default_factory=list)

    def compare(self, label, expected, actual):
        self.differences.extend(differences(expected, actual, "$/" + label))


@dataclass
class ScenarioReport:
    case_id: str
    materialization_version: str
    original_row_bindings: object
    batches: list = field(default_factory=list)
    not_run_steps: list = field(default_factory=list)

    def assert_matches(self):
        if not self.batches or self.not_run_steps or any(batch.differences for batch in self.batches):
            # Exception retains full raw records AND field diffs for an authorized
            # caller to archive. No automatic disk output or fixture mutation.
            raise OracleMismatch(self)


class OracleMismatch(AssertionError):
    def __init__(self, report):
        self.report = report
        super().__init__(pformat(report, width=100, sort_dicts=False))


def _decoded(result, records):
    if not isinstance(result, records.DecodeSuccess):
        raise ValueError("ACTUAL input decode failure: " + repr(result))
    return result.value


def decode_inputs(case):
    _, supplied, _ = _admit(case["case_id"])
    if differences(supplied, case):
        raise ValueError("Unreviewed case input mutation")
    r, codec, _, _ = _sut()
    cfg_data = _binding("configurations", case["configuration_ref"],
                        "configuration_records", case["configuration_sha256"])
    snap_data = _binding("snapshots", case["initial_snapshot_ref"],
                         "snapshot_records", case["initial_snapshot_sha256"])
    cfg = _decoded(codec.decode_configuration(codec.freeze(cfg_data)), r)
    snap = _decoded(codec.decode_snapshot(codec.freeze(snap_data), configuration=cfg), r)
    return cfg, snap


def _reduce(cfg, snapshot, step, batch):
    r, codec, ordering, reducer = _sut()
    if step.get("entry_function") == "restore_snapshot":
        # Preserve the literal restart digest, even if ACTUAL saved state differs.
        # Neither a new SUT digest nor an expected checkpoint replaces this input.
        # Decoder-only envelope; only its supplied literal Evidence payload is
        # passed to restore_snapshot. No fabricated Event reaches the reducer.
        integrity = None
        if step["integrity_evidence"] is not None:
            integrity = _decoded(codec.decode_event(codec.freeze({
                "event_id": step["restart_input"]["event_id"] + "/integrity-input",
                "producer_id": "TOY_INPUT", "producer_sequence": 0,
                "at_tick": step["at_tick"], "causal_parent_ids": [],
                "kind": "EVIDENCE_OBSERVED", "payload": step["integrity_evidence"],
            }), configuration=cfg), r).payload
        return reducer.restore_snapshot(
            cfg, saved=snapshot, integrity=integrity,
            restart=r.RestartInput(**step["restart_input"]),
        )
    events, failures = [], []
    for document in step["events"]:
        decoded = codec.decode_event(codec.freeze(document), configuration=cfg)
        if isinstance(decoded, r.DecodeFailure):
            failures.extend(decoded.errors)
        else:
            events.append(decoded.value)
    args = step.get("entry_arguments")
    if step.get("entry_function") == "reject_batch":
        if failures:
            raise ValueError("Explicit reject_batch also has unaccounted decode failures")
        critical_ids = args.get("known_critical_event_ids")
        critical = events if critical_ids is None else [e for e in events if e.event_id in critical_ids]
        return reducer.reject_batch(
            cfg, snapshot, batch_id=args["batch_id"], at_tick=args["at_tick"],
            errors=tuple(r.InputError(**x) for x in args["errors"]),
            known_critical_events=tuple(critical),
        )
    if failures:
        return reducer.reject_batch(
            cfg, snapshot, batch_id=batch["batch_id"], at_tick=batch["at_tick"],
            errors=tuple(failures), known_critical_events=tuple(events),
        )
    sealed = ordering.seal_batch(
        cfg, snapshot, batch_id=batch["batch_id"], at_tick=batch["at_tick"], events=tuple(events),
    )
    if isinstance(sealed, r.DecodeFailure):
        return reducer.reject_batch(
            cfg, snapshot, batch_id=batch["batch_id"], at_tick=batch["at_tick"],
            errors=sealed.errors, known_critical_events=tuple(events),
        )
    return reducer.reduce_batch(cfg, snapshot, sealed.value)


def run_case(case):
    cfg, snapshot = decode_inputs(case)
    literal = _admit(case["case_id"])[2]
    return snapshot, _reduce(cfg, snapshot, case, literal["batch"])


def _live(snapshot):
    # Interval membership only, NOT a controller/policy or endpoint eligibility oracle.
    return sorted(p["permission_id"] for p in snapshot["permissions"]
                  if p["permission_id"] not in snapshot["revoked_permission_ids"]
                  and p["session_id"] == snapshot["control_session_id"]
                  and p["permission_epoch"] == snapshot["desired_epoch"]
                  and p["valid_from_tick"] <= snapshot["current_tick"] < p["valid_until_tick"])


def _trace_comparison(identity, literal, initial, result):
    actual = shape(result)
    comparison = Comparison(identity, literal, {"initial": shape(initial), "reduction": actual})
    expected_traces = literal["traces"]
    comparison.compare("traces", expected_traces, actual["traces"])
    comparison.compare("transitions", [x for t in expected_traces for x in t["transition_records"]],
                       actual["transitions"])
    comparison.compare("denials", [t["denial"] for t in expected_traces if t["denial"] is not None],
                       actual["denials"])
    # This is independent safety-claim checking, in addition to exact literals.
    comparison.compare("physical_claims", ["NOT_OBSERVED_NOT_VALIDATED"] * len(actual["traces"]),
                       [t["physical_actuation_claim"] for t in actual["traces"]])
    comparison.compare("endpoint_outputs", [], actual["endpoint_outputs"])
    return comparison, actual["snapshot"]


def compare_core(case, initial, result):
    _, supplied, literal = _admit(case["case_id"])
    if differences(supplied, case):
        raise ValueError("Unreviewed case input mutation")
    comparison, final = _trace_comparison(case["case_id"], literal, initial, result)
    before = shape(initial)
    expected_before = _binding("snapshots", literal["initial_snapshot_ref"], "snapshot_records",
                               literal["initial_snapshot_sha256"])
    comparison.expected = {"literal": literal, "initial_snapshot": expected_before}
    comparison.compare("initial_snapshot", expected_before, before)
    projection = literal["expected_final_projection"]
    for key in ("state", "control_session_id", "desired_epoch"):
        comparison.compare("snapshot/" + key, projection[key], final[key])
    comparison.compare("snapshot/current_tick", literal["batch"]["at_tick"], final["current_tick"])
    comparison.compare("snapshot/endpoint_installed_epoch", literal["traces"][-1]["endpoint_installed_epoch"],
                       final["endpoint_installed_epoch"])
    comparison.compare("live_permission_ids", projection["live_permission_ids"], _live(final))
    permission, fault = literal["permission_effects"], literal["fault_effects"]
    comparison.compare("initial/permissions", permission["initial_records"], before["permissions"])
    comparison.compare("snapshot/permissions", permission["initial_records"] + permission["created_records"],
                       final["permissions"])
    comparison.compare("snapshot/revoked_permission_ids", permission["revoked_ids"], final["revoked_permission_ids"])
    comparison.compare("expired_permission_ids", permission["expired_ids"], sorted(
        p["permission_id"] for p in final["permissions"] if p["valid_until_tick"] <= final["current_tick"]))
    comparison.compare("initial/fault_latches", fault["initial_records"], before["fault_latches"])
    comparison.compare("snapshot/fault_latches", fault["final_records"], final["fault_latches"])
    command = literal["command_and_operation_effects"]
    comparison.compare("snapshot/commands", command["retained_commands"] + command["newly_recorded_commands"],
                       final["commands"])
    comparison.compare("snapshot/operation_ledger", expected_before["operation_ledger"] + command["new_operation_records"],
                       final["operation_ledger"])
    old_ledger = expected_before["command_ledger"]
    comparison.compare("retained_command_ledger", old_ledger, final["command_ledger"][:len(old_ledger)])
    if command["newly_recorded_commands"] or final["command_ledger"][len(old_ledger):]:
        # No literal first_decision_id/native ledger rows exist for these new
        # commands. Missing expected data is a discrepancy, never a passing omission.
        comparison.differences.append(Difference("$/new_command_ledger", MISSING,
            final["command_ledger"][len(old_ledger):], "UNSPECIFIED_LITERAL_EXPECTATION"))
    event = literal["event_identity_effects"]
    # Deliberately compare exact schemas. Core oracle rows expose two hash
    # preimages; native EventLedgerEntry exposes payload_sha256. A proposed mapping
    # payload_sha256 <-> canonical_event_content_sha256 needs separate review;
    # immutable_input_payload_sha256 has no native stored counterpart. No mapping applied.
    comparison.compare("snapshot/event_ledger", expected_before["event_ledger"] + event["new_event_bindings"],
                       final["event_ledger"])
    comparison.compare("snapshot/event_high_watermarks", event["producer_watermarks_after"],
                       final["event_high_watermarks"])
    comparison.compare("snapshot/trace_ledger", expected_before["trace_ledger"] + literal["traces"], final["trace_ledger"])
    comparison.compare("snapshot/last_trace_sequence", literal["traces"][-1]["trace_sequence"],
                       final["last_trace_sequence"])
    unknown = literal["unknown_endpoint_information"]
    for key in ("held_observation", "held_unknown_reason"):
        comparison.compare("snapshot/" + key, unknown[key + "_after"], final[key])
    comparison.compare("cancellation_intents", unknown["cancellation_intents"], shape(result.cancellation_intents))
    comparison.compare("snapshot/cancellation_history", expected_before["cancellation_history"] + unknown["cancellation_intents"],
                       final["cancellation_history"])
    comparison.compare("snapshot/acknowledgement_ledger", expected_before["acknowledgement_ledger"],
                       final["acknowledgement_ledger"])
    comparison.compare("snapshot/barrier_acknowledgement_ledger", expected_before["barrier_acknowledgement_ledger"],
                       final["barrier_acknowledgement_ledger"])
    report = ScenarioReport(case["case_id"], load("expected_traces")["materialization_version"], [], [comparison])
    return report


def assert_projection(case, initial, result):
    """Compatibility name: now enforces FULL comparison, never salient fallback."""
    compare_core(case, initial, result).assert_matches()


def run_materialization(case_id):
    kind, material, literal = _admit(case_id)
    if kind == "core":
        raise ValueError("Use run_case/compare_core for a single-batch core case")
    report = ScenarioReport(case_id, load("expected_traces")["materialization_version"],
                            literal["original_row_bindings"])
    if differences(material["original_row_bindings"], literal["original_row_bindings"]):
        raise ValueError("Original versioned row bindings differ")
    audit = {row["row_id"]: row["original_row_sha256"] for row in load("expected_traces")["original_69_row_audit"]}
    for row in literal["original_row_bindings"]:
        if row["original_version"] != "apex-s1-authority/0.1.0" or audit[row["row_id"]] != row["sha256"]:
            raise ValueError("Historical row identity/hash changed")
    steps, batches = material["steps"], literal["batches"]
    if len(steps) != len(batches) or not steps:
        raise ValueError("Missing/extra materialization batches")
    cfg_ref = "#/configuration_records/" + material["configuration_key"]
    cfg_data = _binding("configurations", cfg_ref, "configuration_records", material["configuration_sha256"])
    initial_data = _snapshot_literal(literal["initial_snapshot_ref"], literal["initial_snapshot_sha256"])
    r, codec, _, _ = _sut()
    cfg = _decoded(codec.decode_configuration(codec.freeze(cfg_data)), r)
    snapshot = None if initial_data is None else _decoded(
        codec.decode_snapshot(codec.freeze(initial_data), configuration=cfg), r)
    actual_sequences, actual_cancellations, actual_outputs = [], [], []
    for index, (step, batch) in enumerate(zip(steps, batches, strict=True)):
        if (step["at_tick"] != batch["at_tick"] or step["original_row_ids"] != batch["source_row_ids"]
                or step["expected_checkpoint_ref"] != batch["expected_checkpoint_ref"]
                or step["initial_snapshot_ref"] != batch["initial_snapshot_ref"]):
            raise ValueError("Versioned step/batch identity mismatch")
        expected_before = _snapshot_literal(batch["initial_snapshot_ref"], batch["initial_snapshot_sha256"])
        expected_after = _binding("snapshots", batch["expected_checkpoint_ref"], "snapshot_records",
                                  batch["expected_checkpoint_sha256"])
        try:
            result = _reduce(cfg, snapshot, step, batch)
        except Exception as error:
            failed = Comparison(batch["batch_id"], batch, {"initial": shape(snapshot)},
                [Difference("$/execution", "RETURNED_REDUCTION", repr(error), "ACTUAL_EXECUTION_ERROR")])
            failed.compare("initial_snapshot", expected_before, shape(snapshot))
            report.batches.append(failed)
            report.not_run_steps = list(range(index + 1, len(steps)))
            break
        comparison, final = _trace_comparison(batch["batch_id"], batch, snapshot, result)
        comparison.expected = {"literal": batch, "initial_snapshot": expected_before,
                               "snapshot": expected_after}
        comparison.compare("initial_snapshot", expected_before, shape(snapshot))
        comparison.compare("snapshot", expected_after, final)
        comparison.compare("live_permission_ids", batch["expected_live_ids"], _live(final))
        prior_cancellation_count = 0 if expected_before is None else len(expected_before["cancellation_history"])
        expected_cancellations = expected_after["cancellation_history"][prior_cancellation_count:]
        comparison.compare("cancellation_intents", expected_cancellations, shape(result.cancellation_intents))
        report.batches.append(comparison)
        actual_sequences.extend(t.trace_sequence for t in result.traces)
        actual_cancellations.extend(shape(result.cancellation_intents))
        actual_outputs.extend(shape(result.endpoint_outputs))
        # The ONLY carry-forward assignment. Expected checkpoints are comparison
        # data and are never decoded or passed as saved/reducer input here.
        snapshot = result.snapshot
    if report.batches:
        report.batches[-1].compare("all_trace_sequences", literal["all_trace_sequences"], actual_sequences)
        report.batches[-1].compare("all_cancellation_intents", literal["cancellation_intents"], actual_cancellations)
        report.batches[-1].compare("all_endpoint_outputs", literal["endpoint_outputs"], actual_outputs)
    return report
