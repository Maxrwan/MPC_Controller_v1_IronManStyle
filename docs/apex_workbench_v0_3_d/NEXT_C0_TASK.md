# Prepared next engineering task — retained C0 availability-failure inspection

**PREPARED, NOT STARTED.** 30 October 2026. Documentation preparation only.
Repository: `Maxrwan/MPC_Controller_v1_IronManStyle`.
Accepted Workbench implementation: `c5f3db6852af8f8ffccf4e5e9e6f11d01fa861b4`;
Verification delivery: `af9311ed19e41045aa16dd1029d7191f8eae9c45`.
[User acceptance](../reviews/apex_workbench_v0_3_d/PRIMARY_ACCEPTANCE.md) records the accepted scope
and platform limits. This brief grants no implementation or experiment authority by its existence.

## Objective and first dispatch boundary

Make one original retained **synthetic C0 controller-availability failure** inspectable using the
existing Home/Inspect, native-signal/event presentation and source-linked export infrastructure.
The next bounded assignment must first audit and document its producer/archive contract, then
obtain **separate independent-context contract review before implementation**. Stop the initial
contract assignment at `C0_ARCHIVE_CONTRACT_COMPLETE_PENDING_INDEPENDENT_REVIEW`.
The proposed conditional WORK scope below is for a subsequent explicit assignment after that gate.
Do not begin that assignment while recording V0.3-D acceptance.

## One candidate, with exact retained bytes

| Item | Existing identity / meaning |
|---|---|
| Primary candidate | `results/task007d/c/amended/c0_export/original155.json` |
| SHA256 / size checked during task preparation | `2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5` / 152,600 bytes; matches the prior MVP acceptance-scenario anchor |
| Historical export entrypoint to audit, not run | `scripts/task007dc/c0.py`, introduced in amended-C delivery `44e0471680bb22ea1ee790173d1f2481a905f386` |
| Actual construction pathway to audit | `tests/unit/test_fixed_handoff_scheduler.py::simulate`, `tests/unit/test_async_chronology.py::StraightPlanner`, `tests/conftest.py` fixtures, canonical asynchronous runner/packet/tracker/tire/vehicle/configuration and serialization helper |
| Existing documentary authorities | `docs/TASK007D_C_FIXED_HANDOFF.md`, `docs/task007d/c/amended/c0_summary.json`, `verification.json`, original/amended C findings and later CX source-preservation records; `docs/apex_workbench_v0_3_a/ACCEPTANCE_SCENARIOS.md`, scenario 3 |
| Observed software fixture coverage | 120 state/reserve records, time 0–0.595 s; 60 control records, time 0–0.590 s; declared end 0.600 s, stop `duration`, `failure=null` |
| Recorded planner statuses |`test_success` from an injected `StraightPlanner`, not an IPOPT execution or optimizer-convergence result |

This is not the accepted P racing run, a physical failure measurement or a new NMPC execution.
Availability failure can coexist with successful fixture planner status and `failure=null`.
Do not conflate fixed C0 scheduling with variable Architecture A/Performance P or a production default.

## A — producer/archive contract audit and independent review

Use read-only file/Git inspection and hashes. No scientific module execution or numerical trajectory
is needed to establish the contract. Do not run the exporter, `simulate`, `AsyncRunner`, a worker,
packet-replay plant propagation or any prior research reproduction command.

1. Establish the original producer/serialization and transitive scientific/test-fixture identities
   against immutable Git and historical records. Distinguish export-entrypoint introduction from
   the actual capture revision; do not assume they are identical or substitute current runtime bytes.
   The raw JSON has **no embedded schema version or source-revision envelope**. Its known hash binds
   bytes, not by itself the complete source/meaning. Identify any unresolved provenance explicitly.
2. Specify a separate, externally versioned **read-only inspection contract** for this legacy raw
   profile. It must disclose the historical unversioned producer format, pin original bytes and
   authority records, define required/optional fields, types, finite values and missingness, and
   safely reject unsupported sources/combinations. Do not rewrite the original JSON or manufacture
   an apparently historical manifest, environment record or execution identity.
3. Bind state order/units/frame and Dynamic `a_cmd=Fx/m` from the actual producer. Separate physical
   states, recorded controls, nominal packet predictions, reference/error fields, host computation
   durations, imposed availability and computation/application clocks. Never relabel packet states
   as physical measurements. Audit each stream's native coverage and terminal/censoring rules;
   do not invent a state at 0.600 s or import V0.2's N+1 rule.
4. Specify per-collection order, plan/command identity, null acceptance/use/latency and cross-stream
   ties. Do not synthesize a causal total order from sorting. World XY/serialized GP geometry are
   not present in this raw fixture; show unavailable unless another explicitly bound native source
   is reviewed. Do not construct a new straight/GP track or reconstruct missing coordinates/events.
5. Identify recorded fixed deadlines versus planner-busy skips, readiness versus acceptance, late
   discard, urgent-demand servicing, packet reserve and fallback. Preserve the original failed C0
   gate and amended resolution as distinct historical evidence; no scheduler or threshold change.
6. Define trust/currentness/invalidation, unsafe-path handling, resource bounds and quarantine before
   rendering/export. Reuse verified infrastructure where semantically applicable; do not coerce C0
   into the P `apex-run/0.1.0` or V0.2 qualification contracts. Copies retain the same original
   fixture identity (hash + collection + original row index), never another scientific execution.

Deliver a concise contract, capability/missingness table, exact source/evidence inventory and gap
report. A separate reviewer must check original bytes, producer semantics and provenance before
any adapter is implemented. If sufficient binding cannot be established, stop with
`C0_ARCHIVE_CONTRACT_BLOCKED_PENDING_DECISION`; do not regenerate the fixture or simulate a substitute.

## B — proposed conditional presentation WORK, after contract approval and assignment

Admit only the reviewed `original155` profile, read-only, through existing Workbench navigation.
Show actual states/controls/references where present, native reserve/plan/packet records and a
linked chronology that retains original sample identities and missing values. Provide on-demand
raw/provenance and a source-linked export only if it reuses the existing trustworthy path.
No controller selector, worker start/cancel/reconciliation, Safety command, new replay engine,
generic importer, cross-profile controlled comparison, new metric or qualification label.

Literal chronology assertions must be checked against the retained data, including:

- Fixed targets/misses at 0.170 and 0.330 s; readiness/late discard at 0.255 and 0.41500000000000004 s.
- Urgent trigger 0.160 s, planner idle 0.255 s and release 0.260 s: recorded busy/grid waits remain distinct.
- Planner-busy nominal skips at 0.200/0.300/0.400 s are not the two fixed deadline misses.
- `trajectory_exhausted` fallback at 0.400 s with recorded `valid_domain=true`; missing acceptance,
  first-TVLQR-use and trigger-to-authority remain null. Logged fallback/admission does not prove
  guaranteed recovery, physical safety, stopping or optimizer failure.

Do not enlarge this first profile to `recovery35`, the preliminary serialization-failure archive,
C70 or other histories. Those remain separately contracted future work, even if convenient for demos.

## C — proposed focused acceptance and delivery

Use original evidence read-only for positives; disposable copies for changed/missing/resealed-source,
malformed-field and during-render replacement cases. Assert literal native values/row IDs/clocks,
status meanings, partial coverage and quarantine. Tests must parse retained records; do not obtain
expected results by rerunning the fixture planner/plant. A provenance failure must not leave stale
scientific plots or accepted labels. Archive operations must be demonstrably lifecycle-free.

Preserve the accepted 56-file scientific closure, original 345-file qualification, 25-file P archive,
legacy oval evidence and failed/reviewer records. Keep original V0.1/V0.2/V0.3-B/C/D paths and both
platform observations intact. Use focused parser/UI/integrity regressions plus read-only production
qualification consumption; do not repeat the 17-trajectory campaign or automatically run full formal
Verification. Retain exact source, environment, commands and every negative attempt separately.

After bounded WORK, obtain independent Engineering Review of the exact implementation and stop at
`C0_INSPECTION_ENGINEERING_REVIEW_COMPLETE_PENDING_VERIFICATION`. Any later full functional
Verification/user acceptance needs separate authorization. Routine software decisions can be made
within an assigned scope; new parameter semantics, scientific assumptions or canonical changes cannot.

## Unchanged scientific gates

RBT-S/N/V and component budgets remain pending. No RBT implementation, future G/P controller
execution/profile choice, new racing simulation, numerical qualification, frozen Performance/
Efficiency/CT/Safety campaign, physical telemetry, actuator or hardware work is included.
The goal is one useful, trustworthy investigation of retained software availability failure.
