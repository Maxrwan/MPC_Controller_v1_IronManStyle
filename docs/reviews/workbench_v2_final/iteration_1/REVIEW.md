# Independent Engineering Review — V2 final

**PASS** for exact candidate `740a268a2d2c6b92a67a45456292a3b2cafb2479` on
`codex/workbench-v2-ui`. No actionable defect was found in the authorized display/admission
change. This is one focused Engineering Review, not formal scientific Verification or Primary
acceptance. The reviewer did not install policy, claim an attempt, start a numerical worker,
run a controller/plant/optimizer probe, or modify retained evidence.

## Source and scope

The review read `AGENTS.md`, the verification workflow/test guide, the literal
`docs/workbench_v2_final/PRIMARY_WORK.md`, WORK and work record. Comparison starts at accepted
presentation delivery `e45059cb0fff41a8610761e83bdd69c4a2dff1e2`, whose reviewed UI is
`b1cc8b3d7b306a56adf99a63d8dc689c13856114`. Frozen science remains
`48adbdf64d492592d15e23c917aca71fa58aa8a5`.

All 47 current producer files match both the exact candidate Git blobs and the WORK producer
inventory. The Primary brief SHA-256 is
`52114eba8c67422e3c8e4e02f37b9da21153dbea9c6f41a06ac93f9f04efe785`; current profile SHA-256 is
`849cac0a38188c11e42e5a903ac8d45bae64681cf5c39e847fb6195879393096`.
The review applies to those contents. A behavior-changing descendant needs an applicable review.

## Findings and direct reproductions

1. **Display mathematics and authority: PASS.** The four camera modes transform display coordinates
   only. Follow Prediction frames `snapshot().active`, irrespective of a manual historical selection.
   The unchanged native clock gates active packets by native plan/mode, validity, completion and
   timestamp coverage. Wheel rotation uses the latest actual application delta, held native
   initialization before the first application, and client-only ratio 12 by default. Nominal belongs
   to that applied request and is separately labelled. An independent linear-search oracle over
   all 2,000 retained states made 8,005 assertions on actual/nominal steering, the visual mapping,
   active identity and input nonmutation. At 0.125 s it recovered actual delta
   `0.020027495934949978` rad, nominal `-0.003984999314297534` rad and active packet 0.

2. **Prediction reference semantics: PASS.** `reference_view.py:47` calls the pinned
   `PlanningReference.sample(state[4])`, then canonical `frenet_to_global` and `wrap_angle`.
   Direct source comparison confirms `[vx, vy, r, e_psi, s_abs, e_y]`, lateral error
   `state[5] - e_y_ref` and heading error `wrap(state[3] - e_psi_ref)` with canonical
   `(-pi, pi]` endpoints. The focused geometry-only seam/endpoint check passed. All nine actual
   predicted nodes and eight original controls are retained, with no terminal control. Retained
   prediction XY must equal the canonical projection exactly. Missing reference remains unavailable.
   Connectors and heading glyphs are labelled derived/schematic, never actual-future residuals.

3. **Read-only helper and window continuation: PASS.** The isolated helper uses original approved
   runtime/dependency checks and import guarding, a parent PID/birth owner, a 45-second query bound,
   bounded input/packet counts and an eight-entry captured-input/helper-hash cache. Runtime hashes
   are checked before cached projection use and after fresh calculation. The review's geometry
   helper imported no controller, plant, simulation or CasADi module and was explicitly closed.
   `ui_replay.py:34` holds the current and one next window, rechecks the complete evidence anchor
   before publication, and quarantines a failed prefetch. The browser resumes only with matching
   previous epoch and identical overlapping native boundary time; the boundary pause adds no
   simulated time. Historical packet selection cannot grant active authority.

4. **Resource correction and original pilot: PASS.** Only Full Lap wall/CPU change, to 900/720 s.
   The original conservative projection method remains unchanged: CPU `551.42816` s and wall
   `588.889137327671` s fit the new caps. RSS, output, file and simulation ceilings, native
   two-crossing completion, Extended and V1 remain unchanged. `config.py:26` admits the exact old
   profile only to retained readers when the complete current profile equals the old profile plus
   those two fields; strict new-execution validation rejects the old digest. The genuine historical
   pilot read and unchanged manifest/anchor checks passed. Comparison classification is unchanged.

5. **Source-bound policy/history transition: PASS.** `admission.py:25` requires an exact independent
   PASS, current/Git producer equality, original review/Primary/source bindings and the intact
   consumed pilot/unused full slot. It preserves exact prior-policy bytes and copies the review and
   committed Primary brief. New authority permits only `full_lap`; `config.py:102` checks those
   bindings and historical used/max-attempt fields on each WORK admission. Temporary-policy tests
   reproduced rejection of changed revision/profile/brief/prior bytes/history/slot, duplicate
   consumption and reuse of an existing transition. Pending acceptance cannot activate
   `accepted-interactive`; only explicit `decision: ACCEPTED` can do so.

6. **Once-only launch gate: PASS within the stated sequential workflow.** `final_attempt.py:80`
   rejects an existing claim or spent full slot, takes a new host observation, verifies the policy
   stayed fixed, verifies frozen runtime and the complete approved numerical environment against
   the original pilot, and records source PASS before claim/consumption. Source failure testing
   left the full slot and claim untouched. Host-floor scalar tests preserve strict greater-than
   2×768 MiB RAM and 1 GiB+2×256 MiB disk rules. The shared lease, owned worker and native execution
   remain unchanged. No host-capacity PASS for a numerical attempt is asserted by this review.

## Independent checks

The four-file focused invocation in `review_record.json` completed with **105 passed,
1 deliberately deselected, 0 failed/skipped in 29.11 s**. The excluded unchanged native-dataclass
composition probe imports scientific execution modules and was outside visual-review authority.
Metadata-only real-process lease/cancellation/resource checks ran; they do not execute scientific
models. The parent review process also reported `REVIEW_FORBIDDEN_IMPORTS []`.

The committed JS display checks were independently rerun against
`results/apex_workbench_v2_final/pilot_display_candidate.json`: **2,847 checks PASS**.
The separate reviewer oracle passed **8,005 assertions**. Counts are separate, not combined.
The first shell attempt lacked `node` on PATH; the existing bundled Node executable was used.
The reviewer oracle's first draft incorrectly treated packet ID 0 as falsy; replacing its `|| null`
with explicit null handling corrected the oracle. That transient assertion was a review-harness
error, not a candidate defect. No implementation was changed.

An independent read-only preservation audit rehashed all **13,280 historical files and 573 links**:
no changes. All **335 canonical files** equal the starting delivery, and all **333 frozen runtime
files** equal the pinned scientific inventory. Original V1 producers, V2 launcher,
`execution.py`, `worker.py` and native clock are unchanged. The original review and Primary authority
hashes and prior Git producer hashes still match.

## Browser evidence and limits

The reviewer opened and inspected the supplied Follow Prediction and Microscope screenshots,
the browser observations and the labelled two-window fixture source. These are retained root
browser observations, not independently recaptured browser proof. They show nine nodes, terminal
absence, derived errors/units, actual versus nominal wheel state, live handoffs, historical packet
99 retaining packet-0 authority at 0.125 s, mobile containment, two-window continuation, and
quarantine withdrawing the iframe after damage to a disposable copy.

The genuine replay's reported 233.3 ms maximum painted-frame gap under tool-driven inspection is a
responsiveness limitation, not proof of a guaranteed frame rate. The 50.1 ms continuation-fixture
gap applies only to that labelled transport fixture. Cold reference initialization around 13 s and
possible verified boundary pauses remain visible limitations. No full-lap archive, physical-mobile
behavior, physical validity, hard realtime/WCET, scientific acceptance or off-host backup was proven.

## Disposition and next gate

At review completion, production `access.json` is still the untouched old reviewed-WORK policy at
`fdd494eb7ddf9b456b88cba243fbc704a4fd83c0`, SHA-256
`03b6fbabdfd6bf5416087c78338a9ef335a4f8205724a1214f5f0a1d39ff3574`.
It has exactly the original consumed pilot, no full-lap use, no final claim and no final launch.
The policy remains stale and fails closed against this candidate until the explicit transition.

This PASS satisfies the focused independent review prerequisite only. The orchestrator must first
terminate all review/tests/UI/helpers, preserve this source identity, install the source-bound WORK
transition, and take the fresh host/source gates before the already conditionally authorized single
baseline Full Lap attempt. At the last read-only process snapshot, the retained 8503 UI server
(PID 83743) and its reference helper (PID 83756) were still active; no numerical worker was found.
The review's own test/helper activity has ended. Retain any ensuing blocked/failed/partial result;
no automatic retry or additional pilot is authorized. A successful full lap may produce only a
pending acceptance proposal until Primary acts.
