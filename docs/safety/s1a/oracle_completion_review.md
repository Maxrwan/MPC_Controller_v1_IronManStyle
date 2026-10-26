# S1-O1/O2 — Independent oracle and fixture completion review

**WORK_COMPLETE_PENDING_REVIEW. PENDING_INDEPENDENT_REVIEW.**

Basis: `research/safety-s0` at `6392092d68c1e2dd75120fbd87c32714e530e44e`; owner-supplied Primary S1-O1/S1-O2 approved with conditions. This is fixture/documentation authoring only. No source/test/dependency change or execution is authorized. This review document supplies the scoped handoff; the task-specific seven-path allowlist excludes the otherwise standing CODEX_HANDOFF/DECISIONS edits.

## Authorship versus acceptance

| Population | Complete literal candidates | Partial/unresolved | Independently accepted |
|---|---:|---:|---:|
| Original100 designs | 98 | 2 | 0 |
| Original17 S1-A scenarios | 14 | 3 | 0 |
| Additional V05 old/current-epoch chain | 1 | 0 | 0 |

Five S1-B scenarios remain explicitly deferred. There are305 structurally inspected Trace records, two configurations and128 seed/checkpoint Snapshot records. Complete means every Trace field and requested semantic effect is authored as a concrete candidate; it does not assert unique derivation, independent acceptance, native implementation byte equality, runnable wiring or a pass. All presentation/identity conventions remain reviewable and pending. `full_trace_status` remains `PENDING_INDEPENDENT_REVIEW`.

The two unresolved original100 cases are `T06-NORMAL-BOUNDARY` and `T06-WARNING-BOUNDARY`: packet expiry and emergency coincide, while the projection names only F_EMERGENCY. Primary must settle whether expiry is separately latched or how its cause is represented without loss. Their original projections remain unchanged; no complete fault/trace placeholder is inserted. DISARMED and unsupported-state boundary contexts are resolved separately: no initial Permission exists, expiry is retained as knowledge, and accepted emergency takes T06/T09. See the per-case context derivations.

## Four barrier gaps

| Case | Required? | Authored resolution |
|---|---|---|
| `E13-LOGICAL-GRANT` | Yes: G_NOMINAL/A06/PC03 | Explicit BOOT_BARRIER_A acknowledgement; SESSION_A/ENDPOINT_A, epoch1, cleared queue, delivery=installation=observed0 <= initial tick10. |
| `T01-DISARMED-POSITIVE` | Yes: G_NOMINAL/A06/PC03 | Explicit BOOT_BARRIER_A acknowledgement; SESSION_A/ENDPOINT_A, epoch1, cleared queue, delivery=installation=observed0 <= initial tick10. |
| `T02-NORMAL-POSITIVE` | Yes: G_NOMINAL/A06/PC03 | Explicit BOOT_BARRIER_A acknowledgement; SESSION_A/ENDPOINT_A, epoch1, cleared queue, delivery=installation=observed0 <= initial tick10. |
| `T03-WARNING-POSITIVE` | Yes: G_NOMINAL/A06/PC03 | Explicit BOOT_BARRIER_A acknowledgement; SESSION_A/ENDPOINT_A, epoch1, cleared queue, delivery=installation=observed0 <= initial tick10. |

This is newly declared synthetic fixture prehistory, never a claim of measured delivery or physical acknowledgement. Merely possessing a prepared-barrier ID is not treated as an acknowledgement. The same omitted bootstrap record is completed in59 seed snapshots sharing that already-declared context, so negative cases retain their intended isolated cause. Existing UNKNOWN/rejected new-session RESET_ACK records are retained. Before/after hashes and every affected original100 case are recorded in provenance; positive intent is retained, not silently relabelled.

## Original scenario disposition matrix

| Original case | Disposition | Complete row coverage / original rows | Missing item |
|---|---|---:|---|
| `V01-A-expiry` | COMPLETE_LITERAL_CANDIDATE | 4/4 | — |
| `V01-B-endpoint-expiry` | DEFERRED_S1_B | 0/1 | Later endpoint gate; no execution |
| `V05-A-missing` | COMPLETE_LITERAL_CANDIDATE | 3/3 | — |
| `V05-A-invalid` | COMPLETE_LITERAL_CANDIDATE | 3/3 | — |
| `V05-A-degraded` | COMPLETE_LITERAL_CANDIDATE | 3/3 | — |
| `V05-A-map` | COMPLETE_LITERAL_CANDIDATE | 3/3 | — |
| `V05-A-frame` | COMPLETE_LITERAL_CANDIDATE | 3/3 | — |
| `V05-A-clock` | COMPLETE_LITERAL_CANDIDATE | 3/3 | — |
| `V05-A-uncertainty` | COMPLETE_LITERAL_CANDIDATE | 3/3 | — |
| `V05-A-stale-capture` | PARTIAL_UNRESOLVED | 2/3 | Repeated stale-fault epoch/latch refresh at row3 |
| `V06-A-identities` | COMPLETE_LITERAL_CANDIDATE | 6/6 | — |
| `V06-A-conflicting-payload` | COMPLETE_LITERAL_CANDIDATE | 1/1 | — |
| `V06-B-at-most-once` | DEFERRED_S1_B | 0/3 | Later endpoint gate; no execution |
| `V07-A-explicit-reauthorization` | PARTIAL_UNRESOLVED | 3/5 | New Permission policy/transition identity binding at rows4–5 |
| `V07-A-unacknowledged-handoff` | COMPLETE_LITERAL_CANDIDATE | 2/2 | — |
| `V07-A-mode-fault` | COMPLETE_LITERAL_CANDIDATE | 2/2 | — |
| `V15-A-same-tick-fault` | COMPLETE_LITERAL_CANDIDATE | 1/1 | — |
| `V15-B-cancel-at-commit` | DEFERRED_S1_B | 0/2 | Later endpoint gate; no execution |
| `V15-B-cancel-too-late` | DEFERRED_S1_B | 0/3 | Later endpoint gate; no execution |
| `V15-B-undelivered-revocation` | DEFERRED_S1_B | 0/5 | Later endpoint gate; no execution |
| `V19-A-latch-restart-reentry` | COMPLETE_LITERAL_CANDIDATE | 8/8 | — |
| `V19-A-missing-persistence` | PARTIAL_UNRESOLVED | 0/2 | Independent boot epoch/initial Snapshot at rows1–2 |

The14 complete original cases cover45 S1-A rows. Five more rows have complete prefixes in partial cases; the remaining five S1-A rows have concrete unresolved dispositions. All69 original expected rows, hashes and ordering are unchanged, including14 deferred S1-B rows. Direct scenario/row/hash mappings accompany each materialization. New0.2.0 event projections are separate from old0.1.0 compound/salient interpretations.

Original context completion is explicit: the expiry case retains its source-specified2000-tick freshness override; covariance-only data remain uninterpreted; rest/reentry supplies labelled zero-rest toy Estimate/HEALTH assertions; the new SESSION_B barrier consumes the source row’s epoch2 context. These are not measured vehicle parameters, propagated states, braking evidence or safe-zero claims.

## V05 versioned adjudication

- Preserve the original0.1.0 `V05-A-map/row2` reason `FAULT_LATCHED` and its original hash.
- The Primary-adjudicated0.2.0 old epoch1 command is denied with `EPOCH_MISMATCH` first after desired epoch advances to2.
- The additional literal chain then supplies a synthetic current epoch2 barrier acknowledgement, a healthy sample, and a current epoch2 command. Receipt may be recorded; permission is denied `FAULT_LATCHED`.
- Neither request receives a new Permission. F_MAP_MISMATCH, its tick20 cause, original command identities, event history and epoch2 persist. The healthy sample and acknowledgement do not clear the map fault.

These are authored expectations, not observed implementation outcomes. Sibling versioned reason changes and the V06 future-lease label distinction are retained in provenance. The V19 source row explicitly uses new-session epoch2 after the earlier fault selected2; an implementation convention is not substituted for that source context.

## Provenance, representation and test-only amendment

This same chat previously authored the implementation. During this assignment no implementation source body/helper or previous observed output was used to calculate expectations. Documentation tables and explicit manual plans determine states, epochs, reasons, grants and paths; generic tooling formats records and checks JSON/schema/reference/hash/identity consistency. This method is source-independent construction, not independent-person acceptance. Secondary review is still required.

The source/API contracts leave some presentation bytes open. O1 supplies concrete internal-ID, causal-root, text and operation/content-identity conventions as candidates. Review those choices before requiring native byte equality; do not silently rename IDs or normalize differences. Scientific invariants, source/command/permission identities, state/time/epoch/transition/denial/fault effects and unknown physical outcomes remain explicit.

Proposed separate amendment **PROPOSED-S1-O3-TEST-WIRING-ONLY** would touch only:

- `tests/unit/safety_authority/oracle_support.py`
- `tests/unit/safety_authority/test_oracle_cases.py`

It would load reviewed full traces and per-row bindings, compare complete actual trace/effect histories, support multi-batch/restore and the added V05 chain, and retain all actual differences. Actual returned state must be carried forward; expected checkpoints must never replace it to hide divergence. Exact canonical hashes, presentation-field comparison and any bijective internal-identity mapping need explicit review before implementation. The current helper’s salient-projection comparisons do not constitute full-trace checking. Keep the independent-review gate; do not set INDEPENDENTLY_REVIEWED, auto-skip unresolved cases into acceptance, or regenerate expectations from outputs.

**Request separate approval for that test-only wiring amendment after this review.** No test file is changed and no collection/execution is requested or implied here. The two main scientific gaps and three original-case partials also need their stated dispositions before their focused execution can be authorized.

## Static verification and preservation

Performed: documentation-derived structural schemas for50 records;305 Trace checks; configuration/Snapshot/case/hash/reference coverage; causal-parent and event/transition sequence inspection; first-category reason order and no-OK-on-denial checks; full original69-row equality/hash/order inspection; V05 authored old/current denial/history consistency; path and protected-byte audit. These checks inspect documents/data, not reducer behavior.

Seven authorized paths only: four fixture JSON files and these three review documents. Source modules, all test/support files, dependencies, accepted S0/S1/preparation specifications, implementation work evidence, Performance and unrelated worktrees remain protected by hashes. Historical result auditing is metadata-only and establishes no archive restoration qualification.

**NO DETERMINISTIC TESTS EXECUTED.** No project imports, pytest collection, reducer/guard/ordering calls, fault/endpoint simulation, numerical verification, controller or hardware work occurred.

[Validation](oracle_completion_validation.json) records static counts/limits and fixture hashes. [Provenance and disagreements](oracle_provenance_and_disagreements.json) records source bindings, before/after fixture history, all row hashes, unresolved issues and the proposed amendment. Delivery SHA is supplied separately after the containing commit is pushed and remotely verified.

Stop at **WORK_COMPLETE_PENDING_REVIEW**. No automatic focused execution, source amendment, S1-B/C or hardware progression.
