# Independent C0 descriptive contract re-review — iteration 2

**Outcome: PASS for the bounded documentation-only contract review.**
Static inspection: 30 October 2026; record finalization: 31 October 2026.
R1–R4 pass at revised candidate `5bf6cce22816bc8fd5a7d7bf84cefef87c69e358`, branch
`codex/apex-workbench-c0-descriptive-contract-v1`.
Reviewed [contract](../../../../apex_workbench_v0_3_d/c0_contract/CONTRACT_DESCRIPTIVE_ONLY_V1.md)
SHA-256: `31afeefac753dead492df26f90b5b6aa1d822de705e3a86c97dfba2a0f72fd62`.
The new independent reviewer context did not author or alter the candidate.

**G1 remains OPEN.** This PASS concerns the exact retained JSON's
`descriptive_only / source_unverified` inspection contract. It establishes neither capture-source
provenance nor software behavior, formal Verification, scientific acceptance or adapter WORK
authorization. A separate explicit Primary bounded WORK assignment is still mandatory.

## Reassessment of the retained findings

Contract line numbers refer to the revised candidate above. Evidence was inspected independently
using standard-library JSON/token/hash inspection and read-only Git/text operations; the author's
reported checks were not used as proof.

| Finding | Decision | Independent evidence and revised requirement |
|---|---|---|
| R1 — exact numeric lexemes | **PASS** | Lines 33, 50–51, 57, 63, 69–73, 83 and 112–114 now use the source tokens. All 25 selected pointer/token comparisons match the original bytes, including `0.17`, `0.33`, `0.16`, `0.26`, `0.2`, `0.3`, `0.4`, `0.6`, `0.59`, initial `0.0` versus integer release `0`, signed `-0.0`, packet `0.01`, and both extended float examples. Line 59 still requires exact lexemes, pointer/index binding, integer/real forms, and original exports; it expressly forbids substituting a reserialized float. No raw-token retention requirement was weakened. |
| R2 — present-null versus absent | **PASS** | Lines 61 and 85 correctly identify all seven requested present-null fields: both fixed-handoff `t_accept` and `first_TVLQR_use` fields; urgent-demand `trigger_to_authority`, `accepted_time` and `accepted_plan_id`. Direct pointer lookup confirms each exists with JSON null. `/packets/0/valid_from` and `/triggers/0/busy` are absent. Lines 59, 61, 110 and 113 retain the distinction without zero-fill or inferred authority. |
| R3 — original control keys | **PASS** | All 60 control rows contain `time`, `application_time` and `physical_latency`; none contains `latency`. Lines 40 and 51 use those original keys and retain unverified reference interpretation. Static reference Git `44e0471680bb22ea1ee790173d1f2481a905f386` writes `row["physical_latency"]` at `asynchronous.py:477`; that consistency does not bind the capture to this source. |
| R4 — expected unknown provenance | **PASS** | Lines 12–25 and positive example 109 expressly admit only the pinned 152,600-byte historical unversioned record with G1 OPEN, under the contemporary inspection contract `c0-original155-descriptive-only/1`. Negative example 118 rejects other artifacts, wrong size/hash and unsupported contemporary contract identity/version. Unknown capture producer/schema/environment is explicitly expected and is not a rejection condition. No historical producer/schema identity is invented. |

No new contradictory normative statement was found in the revised contract. Reference-derived
units, frames, timing constants and fallback explanation remain visibly capture-unverified.
`test_success`, `valid_domain=true`, `failure=null`, missed fixed commitments, busy skips and
fallback retain their roles as literal records, without authenticated optimizer, controller,
causal, recovery, safety or physical-performance conclusions. Unavailable geometry and terminal
state remain unavailable. Sorting provides a visual index, not a causal interstream total order.

## Identity, inventory and historical preservation

The directly read artifact is exactly **152,600 bytes**, SHA-256
`2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5`, and is not a symlink.
Strict parsing found no duplicate members or nonstandard constants; structural inspection found
no nonfinite values. All 18 root keys/order and collection field/type/absence/null/count/time
inventories match the unchanged Section A inventory. Packet dimensions are three sets of five
timestamps, 5×6 states, 4×2 controls and four flattened gain rows of length four; curvatures stay empty.

The candidate diff from original candidate `5f73ce324d698568d8ca03f881cbeb3c9d621406` contains
only the revised contract and `docs/CODEX_HANDOFF.md`; whitespace inspection passes. Section A
`AUDIT.md`, `CONTRACT.md` and `evidence_inventory.json` are byte-identical to both original
candidate and Section A revision `acf34015157d237a979fd11263982be6b82c523c`.
The original **BLOCKED** review and machine record remain unchanged in immutable commit
`02e7a3e82d8baf0c90719d876ce5c6662cc52fb2`; this review does not amend their findings or outcome.
The revised working contract equals the exact reviewed Git blob. This reviewer creates only the
two iteration-2 review files and does not change the contract, handoff, implementation or branch.

## Limits and stop

The exact hash gate is primary. The historical inventory remains an observed field union/count
audit, not a complete per-index schema. Any later explicitly assigned WORK specification must
enumerate the actual conditional row key sets and nested dimensions from the pinned record while
retaining the contract's strict identity/type/shape/currentness rules. This does not relax those
rules or authorize a generic importer.

Admission/currentness/quarantine clauses were assessed as written requirements only. No adapter,
fault fixture, producer, application, project import, test, simulation, controller execution,
numerical work, qualification, campaign or hardware action ran. Their implementation and behavioral
validation remain unperformed. No historical test result is claimed as a new pass.

A static inventory lookup initially used the nonexistent key `collection_inventory` and raised
`KeyError`; inspection was corrected to the actual `collections` key. The corrected comparison
found zero mismatches. This was reviewer inspection code only, with no project execution or edits.

**Stop:** `C0_DESCRIPTIVE_CONTRACT_REVIEW_COMPLETE_PENDING_PRIMARY_WORK_DECISION`.
Primary may now consider a separately bounded descriptive-only WORK assignment. This review
authorizes no parser/adapter, tests, Verification, RBT, G/P, scientific, CT/Safety or hardware work.
G1, capture-environment limitations and all existing scientific gates remain unchanged.
