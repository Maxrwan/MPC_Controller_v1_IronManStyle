# NMPC Lab V1 — consolidated independent Engineering Review PASS

**Disposition: PASS, pending Primary acceptance. No unresolved blocking finding.**
Reviewed presentation revision: `8ee2b868e653d687383d6c4e2d38a3bece31319a` on `codex/nmpc-lab-v1`.
The three genuine attempts executed the earlier exact reviewed revision
`af3956fc2dc8c1a88051e87e2eae66010490a2fb`; frozen scientific source is
`48adbdf64d492592d15e23c917aca71fa58aa8a5`. The later presentation changes did not execute a controller.
This completes the same consolidated independent-context Engineering Review and supports
`NMPC_LAB_V1_WORK_COMPLETE_PENDING_PRIMARY_ACCEPTANCE`, not formal Verification or acceptance.

## Implementation and final presentation

The GUI exposes eight native CostScales fields, baseline reset and one fixed native disturbance.
Actual native configuration/controller construction uses those values; vehicle, tire, constraint,
horizon, timestep, solver, Planning and TVLQR mathematics remain frozen. Versioned drafts bind the
profile/source and remain unreviewed. No general configuration framework, exporter, ROS or hardware work.

All 61 retained optimizer preparations associate exact X/U with native packets. The 9-state/8-command
N=8 horizon selector returns no command at terminal node 8. Raw completion, validity and handoff clocks
remain distinct from pre-scheduler packet observation. Actual weighted objective components are shown
without ranking different weighted objectives. Recorded plant, solver and derived values are labelled.
The Bench at `35f6fa579adc574d73ea834786e53667eddcb585` was a read-only presentation reference;
its four inspected files and clean Git identity match, with no N4/runtime mathematics imported.

The original browser capture showed axes without error traces. Switching four plotting constructors
to SVG Scatter preserves the arrays. A fresh owned server rendered visible disturbance-response curves;
reviewer visual inspection and the recorded 0 GL / 15 SVG trace paths / 2,723 SVG points support closure.
The underlying blank-trace cause was not established. Initial blank/stale captures remain retained.

## Tests and retained evidence

Counts are separate invocations, never aggregated:

- Pre-execution exact-af WORK: 97 passed / 31 deselected; independent correction checks: 7 integrity
  passes plus a separate 2 UI passes. V1-ER1-P1 is closed; its original exact-01ace08 BLOCKED report and
  failed anchor-adoption reproduction are unchanged.
- Pre-SVG presentation WORK on 132a8e3: 98 passed / 31 deselected, 66.587 s. This was not rerun on 8ee2.
- Final exact-8ee2 retained UI: parent 4 passed, 6.052 s; fresh independent 3 passed, 1.657 s. These check
  actual node associations, terminal NULL, native-clock/objective values and late replay quarantine.
  There were zero failures/errors/skips in these final invocations; parent UI retains one harmless
  already-imported-anyio warning. Per-interaction timing is unavailable; only JUnit case durations apply.

The read-only post-run audit verified every committed artifact, exact raw/manifest digests, captured
producer Git bytes, all 333 frozen runtime files, installed environment RECORD hashes and imported
module paths. It executed no optimizer, plant, AsyncRunner or scientific model. Its first two metadata
harness attempts blocked Python platform identity reads; logs remain and the final audit passes.

Exactly three once-only 2.0 s attempts completed, each with 400 native state samples and 200 applied
commands, valid evidence and return code 0. Successful native preparations: 20 / 20 / 21. No recorded
fallback, planner/codriver miss or sampled boundary violation in these windows. No retry occurred.
All three slots are consumed; the fixed software-gate SHA remains
`6a6196f99aa4171feaaca9a50e9643697cd8bb018a8b7ad6b241c4539af95557`.

| Case | Racing lateral RMS [m] | Peak absolute error [m] | Steering total variation [rad] |
|---|---:|---:|---:|
| Baseline lateral=2 | 0.008359 | 0.023551 | 0.275150 |
| Only lateral=1 | 0.010243 | 0.027957 | 0.185171 |
| Baseline + native kick | 0.021431 | 0.072710 | 0.271378 |

These are single synthetic observations over actual samples from 0 to 1.995 s. Native duration
termination is near 2.0 s; no endpoint state was invented. Baseline/treatment differ only in lateral
cost and are controlled comparisons. The disturbance comparison is labelled illustrative and does
not compare incompatible recovery metrics. Raw objective totals are not performance ranks.

The only plant-segment discontinuity is the declared +0.08 m lateral / −0.04 rad heading increment at
exactly 0.5 s. The pre-kick physical prefix matches baseline; the pre-third single-point native domain
check equals the actual disturbed state. All application clocks are 5 ms after request clocks, and
actual command holds match the plant segments. Both undisturbed runs exactly match the original M5-A
400-state/200-command physical channels, with host timing excluded.

At the descriptive 0.01 m band / 0.25 s minimum tail, the disturbance record first stays within band
from 0.965 s through observation end: 0.465 s after the kick. This is within-window behavior only.
An insufficient remaining tail correctly reports unavailable settling; no step overshoot is assigned.
All 4,880 stored local Jacobian/gain associations preserve native order, 10 ms RK4×2 and negative
feedback. Nominal-packet eigenvalues/products remain local indicators; the mixed-SI product norm can
reach about 14.54 despite instantaneous spectral radii below 1. Clamps, handoffs, longitudinal coupling
and nonlinear/hybrid guarantees remain excluded.

Worker wall observations are approximately 18 s and sampled RSS 229–242 MB, within unchanged caps.
Process samples show 4 total threads and 3 at preparation; Accelerate SINGLE control is recorded,
with exact active numerical thread count unavailable. No one-thread, WCET or hard real-time claim.

## Preservation, delivery and remaining limits

Fresh checks match 6,329 original M5-A files / 324 links with no additions, 56 primary scientific /
345 qualification / 25 GP / 4 oval files, and the original 152,600-byte C0. All 333 frozen files match
Git. PRE-INT scientific/config/dependency prefixes match verified 90e20cb; its clean current checkout
and all 66 retained inactive guard bytes are unchanged. No authority, gate or consumed claim was reset.
The owned browser server/tab are closed, port 8516 refuses connection, and the shared lease is free.

One nonblocking final-documentation follow-up remains: owned shutdown appended `Stopping...` to the
old operational browser server log after its candidate checksum was recorded. The stable closed-log
SHA is `086d73cbd63f1f282f874fc65f1031b4598fac810fe0d1bc529b324b560e32c9`.
Parent acknowledged updating that binding in the planned documentation-only delivery while preserving
prior declarations/history. This affects no raw result, gate or scientific identity. No new source
review cycle is required for an exact-copy report/documentation delivery with unchanged source/tests/profile.

Raw evidence remains local/ignored; published hashes alone do not provide off-host retrieval. The
isolated checkout lacks its local tools environment: the original one-click launcher is unchanged,
and the explicit approved-primary-interpreter command was actually demonstrated from `/private/tmp`.
One-click setup in this checkout is not established.

Primary acceptance remains required. No additional numerical attempt, accepted-interactive policy,
formal Verification, physical validation, scientific/performance superiority, nonlinear/hybrid stability,
real-time qualification or deployment follows. Future exporter work must explicitly select a versioned
configuration/hash and review, reuse the canonical native factory, and receive separate scope; it is absent.

Evidence paths are repository-relative strings so this exact report can be copied into tracked docs.
Detailed machine evidence is under `results/apex_workbench_nmpc_lab_v1/work/review/final_evidence/`:
`retained_audit.json`, `descriptive_metrics.json`, `timing_association_audit.json`,
`preservation_audit.json`, `independent_old_m5_parity.json`, `final_source_bindings.json`,
`final_presentation_command.json`, `final_presentation.log`, `final_presentation.xml`, and
`browser_and_finalization_review.json`. The fixed admission report remains under
`work/review/correction1/software_gate_review.json`; final consolidated record is `final_review_record.json`.
