# Independent Engineering Review — C0 descriptive-only contract v1

**Outcome: BLOCKED at the exact reviewed revision.** 30 October 2026.

Reviewed revision: `5f73ce324d698568d8ca03f881cbeb3c9d621406`, branch
`codex/apex-workbench-c0-descriptive-contract-v1`, [draft PR #1](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/pull/1).
Contract: [CONTRACT_DESCRIPTIVE_ONLY_V1.md](../../../../apex_workbench_v0_3_d/c0_contract/CONTRACT_DESCRIPTIVE_ONLY_V1.md),
SHA-256 `d85e41e91c0b768071434b24d78b8ca4bc3e945c6d94771b3d75e493c1d73070`.
The separate reviewer context did not author or amend the candidate contract.

**G1 remains OPEN.** A meaningful `descriptive_only / source_unverified` profile is feasible:
raw fields, collection counts, original pointers, missingness and recorded chronology can be
inspected without authenticating controller behavior. The block is the contract's conflicting
normative examples and field descriptions, not a requirement to recover G1 before descriptive
inspection. Correct the four findings below and independently review the new exact revision
before Primary considers a bounded WORK assignment. This revision is **not suitable as the
implementation contract**. No implementation, tests, formal Verification or scientific acceptance
is authorized by this review.

## Findings and required corrections

All line references below refer to the contract at the reviewed revision.

### R1 — P1: normative literal-number examples do not match the pinned bytes

Sections 3–4, particularly lines 65–71, call the examples **exact field contents** and require
original tokens, while supplying decimal forms absent at the cited fields. The normative positive
example at line 109 repeats the problem. Lines 50–51 and 57 also describe coverage/disposition with
normalized forms. Numeric equality does not establish lexical identity.

| Original JSON pointer | Actual numeric token | Contract form |
|---|---|---|
| `/fixed_handoffs/0/valid_from` | `0.17` | `0.170` |
| `/fixed_handoffs/1/valid_from` | `0.33` | `0.330` |
| `/urgent_demands/0/trigger_time` | `0.16` | `0.160` |
| `/urgent_demands/0/release_time` | `0.26` | `0.260` |
| `/misses/0/time`, `/misses/1/time`, `/misses/2/time` | `0.2`, `0.3`, `0.4` | `0.200`, `0.300`, `0.400` |
| `/fallbacks/0/time` | `0.4` | `0.400` |
| `/end_time` | `0.6` | `0.600` |
| `/controls/59/time` | `0.59` | `0.590` |
| `/states/0/time`, `/reserves/0/time` | `0.0` | `0` in coverage prose |

The long representations `/fixed_handoffs/1/t_ready = 0.41500000000000004` and
`/urgent_demands/0/grid_alignment_wait = 0.0050000000000000044` are correctly retained.
Additional lexical examples worth preserving are `/plans/0/release_time = 0` versus
`/states/0/time = 0.0`, and `/controls/0/acceleration_correction = -0.0`.
The packet solve-duration token is `0.01`; line 81's `0.010` is numerically equivalent but
must not be represented as a copied raw token. Line 33 is expressly conditional on lexemes
being present; `0.400` is not present at the fallback pointer in this admitted artifact.

**Risk:** an implementation or acceptance check following the positive examples would invent
trailing zeros while claiming literal preservation, directly violating lines 59 and 65.

**Correction:** replace claimed original tokens with the actual pointer-specific forms throughout
the successor contract and its examples. Distinguish any explanatory numerical notation from an
original token. Keep original-byte/token preservation mandatory; do not weaken it to make the
examples pass, and do not rewrite any historical audit, blocked draft or original JSON.

### R2 — P2: present-null fields are described as missing

Line 83 calls `first_TVLQR_use` and trigger-to-authority fields "missing". In this exact record,
`/fixed_handoffs/0/first_TVLQR_use` and `/fixed_handoffs/1/first_TVLQR_use` are **present and null**.
`/urgent_demands/0/trigger_to_authority`, `/accepted_time` and `/accepted_plan_id` within that
urgent-demand object are likewise present-null. Both fixed-handoff `t_accept` fields are null.
By contrast, `/packets/0/valid_from` and `/triggers/0/busy` are genuinely absent.

**Risk:** "missing" can cause the unavailable acceptance/use values to be exported as absent
members, contradicting the explicit absence/null distinction at lines 59 and 61.

**Correction:** say "present with JSON null; authority/use unavailable" for these exact fields.
Use "absent" only for an omitted member and retain full original pointers. No zero time,
estimated authority, acceptance, perfect tracking or successful recovery may be inferred.

### R3 — P2: the purported literal latency key does not exist

Line 40 refers to a literal control field called `latency`. None of the 60 control rows has
that key. Every row contains `physical_latency`; the corresponding original time keys are
`time` and `application_time`. Historical reference runner line 477 also writes
`row["physical_latency"]`, without establishing capture provenance.

**Risk:** a glossary, table or export could invent/rename a raw field while claiming that the
original field name is authoritative. The word "physical" in the actual key does not authenticate
its physical interpretation.

**Correction:** use `controls[i].physical_latency` and its JSON pointer; keep any meaning/unit
explicitly reference-derived and unverified. State that `time` is the recorded key if explaining
the reference source's computation-clock interpretation.

### R4 — P2: rejection example conflicts with expected unknown provenance

Line 115 requires rejection for "unknown producer or schema" alongside an unsupported second
archive. The one expressly admitted artifact has an unknown capture producer and no embedded
producer schema (lines 19–25); that uncertainty is the purpose of this narrower profile.

**Risk:** applying this normative rejection rule literally would reject the correctly pinned
artifact, or pressure implementation to invent a producer/schema identity to admit it.

**Correction:** reject an unlisted artifact, wrong size/hash or unsupported **contemporary
inspection-contract identity/version**. Explicitly allow the pinned historical unversioned JSON
under `source_unverified` while leaving its capture producer/schema/environment unknown. Add a
paired positive example for exact approved bytes with G1 OPEN. Do not admit other unknown-source
files or create a historical capture envelope.

## Independent evidence and contract assessment

Only standard-library JSON inspection, hashing, filesystem reads and historical Git reads were
used. JSON numeric-token inspection used `json.loads(..., parse_int=str, parse_float=str)` on the
original bytes; tokens in the evidence record are not reconstructed from parsed floats. A separate
standard-library inspection recorded duplicate members, nonstandard constants, finite numbers,
types, absent/null counts and nested array lengths. This is an audit of retained data, not a
parser/adapter implementation or numerical qualification.

| Area | Independent finding |
|---|---|
| Exact artifact | Original path exists as a regular non-symlink file; **152,600 bytes**, SHA-256 `2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5`. No duplicate JSON members, nonstandard NaN/Infinity or nonfinite numbers found. |
| Original evidence | Section A `AUDIT.md`, blocked `CONTRACT.md` and `evidence_inventory.json` are identical between `acf34015157d237a979fd11263982be6b82c523c` and the candidate. All 15 context-file hashes match the inventory. Both retained compact original155 summaries match the corresponding raw fields. |
| Source identity | All **69** inventoried historical reference blobs and all **16** final-delivery source hashes match immutable Git at `44e0471680bb22ea1ee790173d1f2481a905f386`. This authenticates reference bytes only; the 69-file static superset is not a capture/runtime closure. |
| G1 remains open | The reference exporter directly serializes the result without a source/environment envelope. C1's neighboring receipt identifies different asynchronous/fixed-handoff hashes. CX's original155 entry records size/mtime, not a capture source map. The V0.3-A hash anchor identifies retained bytes only. The older source-bearing C0 summary describes a different 0.8-duration, variable-handoff blocked case. None binds amended original155 capture. |
| Shape/type inventory | All 18 root keys and every declared collection's row count, field/type union, absent/null counts and time coverage match. States/reserves: 120 each; controls: 60; plans/packets: three each; fixed handoffs: two; urgent demands: one; triggers/releases/misses/fallbacks: 2/2/3/1. Handoffs/laps/codriver misses are empty collections, not proof of real-world absence. |
| Nested/conditional data | Each packet retains five timestamps, 5×6 states, 4×2 controls and four flattened four-value gain rows; empty curvatures remain empty. Startup packet lacks `valid_from`; runtime packets contain it. Startup/runtime plan key sets remain distinct; no generic fill rule is justified. |
| Chronology | Literal targets `0.17`/`0.33`, readiness/discard `0.255`/`0.41500000000000004`, urgent trigger/eligible/release `0.16`/`0.255`/`0.26`, busy/grid waits `0.095`/`0.0050000000000000044` are recorded. Busy-skip rows `0.2`/`0.3`/`0.4` remain distinct from missed fixed commitments. Fallback reason is recorded at `0.4`; end declaration `0.6` exceeds last state/reserve `0.595` and control `0.59`. This establishes recorded contents, not authenticated controller causality. |
| Planner/timing meaning | All plan `status` and packet `solver_status` strings are `test_success`. Reference `StraightPlanner` supplies the strings and constants `0.017`/`0.01`; it does not run IPOPT. Host diagnostic names do not authenticate capture environment or measured optimizer performance. Packet `valid=true`, `validation_reason="solver_and_model_valid"`, plan `success=true` and fallback `valid_domain=true` are also raw assertions only. |
| Units/frames/fallback | Reference `state.py` declares `[vx,vy,r,e_psi,s_abs,e_y]` and SI; dynamic model describes `a_cmd=Fx/m`. Reference fallback sets reference to the current state and error/correction to zero. The contract correctly requires unverified reference labels and prohibits perfect-tracking, physical safety and authority claims. These meanings cannot authenticate the capture. |
| Meaningful views | Fixed metadata/limitations, raw JSON, pointer-bound tables, native numeric markers, explicit missingness and a visibly reference-only glossary/export are viable without G1 resolution. No geometry, terminal row, held-input reconstruction, source-verified execution identity, numerical metric or cross-profile comparison is justified. |
| Fail-closed design | Fixed path/size/hash before parsing, duplicate/type/shape checks, bounded I/O/render/export, linked/escaping-path rejection, operation-local bytes and before-publication/after-serialization identity checks are appropriate design requirements. Quarantine must withhold stale figures/status/export. They have **not** been implemented or behaviorally verified; R4's rejection ambiguity must first be corrected. |

The immutable inventory is a descriptive union/count audit, not a complete per-index schema.
A future bounded WORK specification should make the actual conditional key sets and nested
dimensions explicit using the pinned record and contemporary reviewed constraints. The exact
hash gate remains primary; this clarification licenses neither a generic importer nor relaxing
hash/shape checks, and requires no alteration of the historical inventory.

## Positive/negative example disposition

| Candidate example line | Disposition at this review |
|---|---|
| 107 — null `t_accept` | Correct: show JSON null and original pointer; no acceptance inference. |
| 108 — `plans[1].status` | Exact string matches; required reference/unverified warning is appropriate. |
| 109 — fallback literal | Reason/flag match; timestamp lexeme fails R1. No recovery/safety inference is allowed. |
| 110 — omitted startup `valid_from` | Correct: absent, not null or inferred authority. |
| 111 — requested XY/terminal state | Correct refusal; no serialized geometry/native terminal state exists. The requested `0.600` notation is not an original source token. |
| 112 — SI/frame annotation | Acceptable only as visibly unverified reference interpretation, preserving raw names/vectors. |
| 113 — `IPOPT solved in 0.017 s` | Correctly prohibited; named timing does not authenticate optimizer activity/performance. |
| 114 — changed/resealed data | Correct SHA-based quarantine requirement, including same-size/mtime changes. No fault was injected. |
| 115 — second archive/unknown producer/schema | Unsupported archive rejection is correct; expected unknown provenance conflicts with admission under R4. |

No hypothetical changed, partial, duplicate-key or symlink fixture was created or executed.
Negative-example review assesses the written required outcome only, not demonstrated software behavior.

## Preservation, delivery and stop

Read-only audit records are retained in
`results/apex_workbench_c0_descriptive_review_20261030/inspection.json` and before/after
preservation records. The final preservation comparison covers **1,398** preexisting files,
including all 888 paths from the original Section A protection map, tracked implementations,
original/context evidence and Section A raw audit materials: zero changed/missing files.
Candidate contract/request also remain byte-identical to the reviewed Git revision.
Only this new review, its [machine record](review_record.json) and the mandatory handoff are
delivered. The separate review branch preserves PR #1's candidate branch; no PR review/comment,
merge, scientific source change or acceptance was submitted.

No tests, project/scientific imports, Workbench launch, producer/exporter invocation, simulation,
fault-injection campaign, numerical qualification, physical/hardware action or frozen-source edit
occurred. Historical passes remain historical; none is claimed as a fresh pass here.

**Next gate:** correct R1–R4 in separately authorized documentation work, then independently
review that exact revision. Primary may subsequently consider an explicit bounded descriptive-only
WORK assignment with G1 OPEN; this review grants no such authority. Existing RBT, G/P, numerical,
Performance/Efficiency/CT/Safety and hardware gates remain closed unless separately authorized.

**Stop:** `C0_DESCRIPTIVE_CONTRACT_REVIEW_COMPLETE_PENDING_PRIMARY_WORK_DECISION`;
contract outcome **BLOCKED**. No automatic implementation progression.
