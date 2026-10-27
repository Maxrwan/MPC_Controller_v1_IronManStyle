# V0.1 delegated stabilization

**V0.1_VERIFIED_PENDING_USER_ACCEPTANCE.** Recorded 28 October 2026. Initial baseline:
`5acdf4ff4db927bfaf3828b8714dfe39619a5db8`, branch `codex/apex-workbench-v0-1`.
Cycle-1 candidate: `aeedf18e0df9b40ef7294ba15fc73e19b0d5884b`.
Cycle-2 candidate: `ca5c72fd255bd2b9511d891485087dc3174b9aea`.
Final reviewed/tested implementation: `77d018b11bbbfc39ab81d98c9bef70e90ab82725`.
The final delivery is a documentation-only descendant. [Separate-context review](../../docs/reviews/apex_workbench_v0_1_stabilization/REVIEW.md)
passes; [complete functional Verification](../../docs/reviews/apex_workbench_v0_1_stabilization/VERIFICATION.md)
reports **855 passed, 17 separately gated G2 skips**. Historical WORK results follow.
Historical [failed review](../../docs/reviews/apex_workbench_v0_1_corrections/REVIEW.md),
reproductions and result files remain unchanged.

| Finding | Correction and focused evidence |
|---|---|
| C-R2 | Validate retained request/status types and required UI fields. Exclude malformed records with a warning; revalidate and hash-check a selected terminal request before displaying metadata. A selected-record read race is quarantined without an app exception. Evidence is never repaired. |
| C-R6 | Verify manifest membership before treating absent output as optional. A manifest-listed missing file always fails. Successful version-2 exports require states, geometry, XY, summaries, telemetry contract/environment and LQR controls. The selected UI and comparison check those required exports before plots; absent dynamic reference controls remain explicitly unavailable. |
| R1 test synchronization | Keep real supervisor-SIGKILL, live-worker admission rejection and worker-exit assertions. Wait for the inherited lease to become available before asserting conservative recovery. Both cancellation/no-cancellation variants passed. UI quarantine does not hide a legacy active owner from admission checks. |
| Launcher | Reuse the TCP address during the pre-bind check and distinguish EADDRINUSE from other bind errors. Actual same-checkout listener identity/readiness and job safeguards remain required. |

Manifest-listed stdout/stderr and selected JSON/CSV contents are verified on consumption.
Supervisor diagnostics remain explicitly unverified. Required-export presence checks do not claim
a complete archive hash scan; unchanged selected-artifact hashing/cache rules remain in force.
Failed executions that never produced exports remain inspectable and retain their failure labels.
No canonical model, controller, vehicle/tire configuration, profile or core dependency changed.

The separate-context [cycle-1 review](../../docs/reviews/apex_workbench_v0_1_stabilization/CYCLE1_REVIEW.md)
failed on two additional lifecycle gaps. Cycle 2 now inspects legacy/verified owners independently
of UI evidence-field validation, blocks admission on unreadable identifiable lifecycle records,
and validates the in-lock status reread. Malformed records remain unchanged. Four real sleeping
legacy-command sentinels and a controlled status-replacement regression cover these findings;
no second scientific execution is admitted by the sentinel tests.

The [cycle-2 review](../../docs/reviews/apex_workbench_v0_1_stabilization/CYCLE2_REVIEW.md)
closed those lifecycle gaps but retained a receipt-consumption failure: deleting manifest-listed
`execution.json` left charts visible without warning. Cycle 3 checks the presence and containment
of **every manifest-listed file**, plus required exports, before selected-record plots/comparison.
Selected bytes still undergo checksum verification; unrelated contents are not read merely to
check presence. The real-copy missing-artifact regression now includes the immutable receipt.

## Focused checks

The first combined invocation executed all Workbench tests plus existing configuration, dynamic
bicycle, canonical state, Frenet, baseline and runner unit files: **218 passed, 2 failed** in 54.67 s.
Both failures were in new test fixtures: a normal Streamlit terminal rerun intercepted the intended
selected-read race, and a failed-execution fixture incorrectly rejected its expected failure message.
Those two fixtures were corrected without changing production code; the affected selection then
passed **2/2** in 4.44 s. The full negative log remains. The current 220-case selection is covered
by those applicable results; this is **not** a claim that one invocation freshly passed all 220.

Cycle-1 coverage: **72 Workbench cases and 148 existing scientific unit cases**. Original dynamic/LQR
entry-point parity, full supervised-worker parity, R1–R6 regressions and the new malformed/missing
artifact probes are included. The 218 unchanged passes remain applicable: production source,
fixtures, environment and their test assertions did not change afterward; only the two failing
test bodies changed. Source snapshots and precise commands are in the JSON/local evidence.

After the lifecycle corrections, the complete Workbench selection passed freshly: **77 passed,
zero failures/skips**, 49.24 s. This includes both original/full-worker parity checks, all prior
regressions and five additional lifecycle cases. The 148 scientific-unit passes are reused as
applicable: no canonical/script/configuration/dependency/scientific-test contents changed, and
the lifecycle/storage corrections do not enter their import/dependency graph. No claim of a fresh
combined 225-pass invocation is made.

Cycle 3 complete Workbench selection: **78 passed, zero failures/skips**, 49.96 s. This adds the
receipt-deletion case and reruns all Workbench lifecycle, UI, integrity and parity checks against
the final corrective contents. At that WORK stage, formal Verification awaited exact-revision
review; its subsequently executed result is recorded above.

The actual launcher smoke passed: unrelated working directory, health 200/ok, repeated click
reuses its live server, owned SIGINT shutdown, immediate reusable-address bind, foreign listener
rejection without termination and an exact launcher copy with no environment reporting setup missing.
Syntax, scoped Ruff/format, whitespace, documentation links and preservation audits accompany delivery.

Local evidence: `results/apex_workbench_stabilization_20261028/`. Native controls remain Accelerate
SINGLE before numerical imports. These are functional software checks, not host-timing benchmarks
or physical model validation. Existing negative reviews and measurements are not overwritten.

## Review and Verification gate

The exact cycle-3 commit passed separate-context technical review, then the complete applicable
repository/Workbench acceptance suite under the explicit delegation. No named external Secondary
approval or Primary scientific acceptance is claimed. The 17 frozen G2 cases remain skipped because
their independent scientific authorization/allowance was not delegated. Final user/scientific
acceptance remains separate. No new research campaign, frozen-profile change, V0.2 or physical
acceptance is authorized. All three corrective cycles are complete; stop for user acceptance.
