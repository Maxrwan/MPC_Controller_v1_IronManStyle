# Independent corrective Engineering Review — PASS

Candidate: `fdd494eb7ddf9b456b88cba243fbc704a4fd83c0` on `codex/workbench-v2-lap`.
Accepted V1 base: `511b0a884e0f8474760817620fcdef46e7860142`.
Frozen science: `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
Reviewer: independently delegated agent `/root/workbench_v2_lap_independent_review`.
Completed: 2026-11-10 14:41 UTC.

**Outcome: PASS for the exact corrective software candidate. No blocking scientific, functional or integrity finding remains in this bounded review.**
This is Engineering Review, not formal Verification, final Primary acceptance, resource qualification or a claim that a genuine lap succeeds.

## Findings and correction disposition

- **R1 resolved.** `analysis.resource_budget()` now requires `state=completed`, `scientific_outcome=completed`, `evidence_state=valid` and worker `returncode=0`, in addition to baseline identity, complete coverage, no native failure and bounded extrapolation. The unchanged full-lap access path calls this function before consuming the full-lap slot. Independent metadata checks reject each unsuccessful field and each missing field while retaining the valid control case. Failed/cancelled/interrupted evidence and consumed history are not rewritten.
- **R2 resolved.** The new V2-only `lap/replay.py` binds its epoch to the full retained evidence anchor and selected native window endpoints/count. Component identity changes with that window; the original run identity and source anchor stay intact. A full presentation operation resends a verified payload, while acknowledged fragment updates carry only heartbeats. This handles changing windows and returning to an earlier window. The quarantine latch spans the entire run. Accepted V1 Python payload/bridge/browser files remain byte-exact.
- **R3 resolved.** Sector maximum slack uses finite numeric observations only and reports both available and missing observation counts. Missing/null/nonfinite values do not become zero. Independent metadata checks exercise absent, null and nonfinite slack alongside a valid value, with correct missing and solver-failure counts. The candidate tests also exercise all-missing sectors.
- **Draft error containment verified.** Invalid and duplicate drafts produce contained UI errors without replacing saved bytes. Configuration semantics and exclusive-write behavior remain unchanged.
- No new blocking findings. No correction to controller equations, vehicle parameters, frozen scientific source, native scheduling/crossing logic, execution limits, shared lease, evidence reader or access policy was made.

## Independent evidence

1. **56 focused tests passed, 0 failures/errors/skips, 34.41 s.** Full current `tools/apex_workbench/tests/test_lap_v2.py` was independently run. The result is separate from the parent's 17-test correction selection and the historical iteration-1 results; counts are not added together.

   Command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src:scripts VECLIB_MAXIMUM_THREADS=1 /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tools/apex_workbench/.venv/bin/python -B -m pytest -q -p no:cacheprovider tools/apex_workbench/tests/test_lap_v2.py --basetemp=results/apex_workbench_v2_lap/review/iteration_2/fixtures --junitxml=results/apex_workbench_v2_lap/review/iteration_2/focused.xml`.

   The only scientific configuration subprocess is the explicitly guarded no-solve composition check: `casadi.nlpsol`, `AsyncRunner.run` and `DynamicBicycle.step` are blocked. The suite's other subprocesses are metadata-only lease/ownership/monitor helpers with explicit wait/finally cleanup. No genuine scientific execution is inferred from these checks.

2. **Additional independent metadata/transport checks passed.** `independent_checks.py` and `independent_checks.json` cover:

   - Eight separately unsuccessful/missing terminal-pilot fields rejected, with successful control accepted.
   - Evidence mutation after component publication detected by the real integrity check; restored bytes and a different selected window cannot bypass the run-wide latch; explicit reopen is required.
   - A wrong acknowledgement retains payload retransmission; a correct acknowledgement permits warm heartbeat-only updates.
   - Absent/null/nonfinite sector slack stays missing; one valid observation supplies the maximum and all failure counts remain explicit.

   Only Streamlit transport/session/rerun calls were stubbed. The actual V2 bridge, accepted payload builder, native-window selection and evidence-current check were used. No browser/server was launched by the reviewer.

3. **Preservation and exact identity pass.** `static_audit.json` records:

   - 12,546 historical files and 508 links match `preservation_before.json`; no changed files or links.
   - Seventeen accepted V1 protected producers/launcher/replay entries match the accepted base.
   - All 333 frozen runtime files match pinned source `48adbdf...`.
   - Iteration-1 BLOCKED report and record are tracked byte-exact under `docs/reviews/workbench_v2_lap/iteration_1/` and remain unchanged in their original ignored evidence directory.
   - Current work-record source/evidence hashes and Primary authority hash match bytes. The new replay bridge is automatically included in current producer bindings.
   - No V2 access policy has been created; the genuine run root is absent or empty.
   - HEAD stayed the exact candidate and tracked status stayed clean. Reviewer writes are confined to this fresh ignored iteration directory.

4. **Static checks pass.** Candidate diff has no whitespace errors; the V2 launcher passes `zsh -n`. Source, dependency, V1 producer/renderer, and scientific prefixes have no change from the accepted baseline. Worker/config/execution/evidence/profile/app/launcher code is unchanged from iteration 1; its earlier direct source inspection remains applicable by exact byte identity. All corrective source and added tests were read directly.

## Scientific, functional and lifecycle scope

The existing synthetic GP/Planning gamma2, dynamic bicycle with combined-grip tires, Architecture A, NMPC N8 and TVLQR composition remains frozen. Native `AsyncRunner` is still used. Two native finish-line crossings exclude the partial first crossing from the original `s_abs=1 m`; `lap_times[1]` describes one complete same-phase interval. Genuine states and events retain their original timestamps, all retained observations feed scientific summaries, and display reduction is separate. Target-time prediction matching retains missing observations rather than interpolating them. Comparisons retain their non-cost condition/coverage checks and do not rank weighted objective totals.

Independent finite V2 ceilings and the original V1 limits remain unchanged. The same inherited execution lease, verified process identities, cancellation/supervisor-loss/resource monitors, chunk publication and integrity-checked reader remain in place. Software tests support their protocol mechanics, not actual full-run resource feasibility or hard real-time behavior. Full host process enumeration was sandbox-denied in iteration 1 and was not repeated; no whole-host inventory is claimed.

## Stop and next gate

**All reviewer tests and audits are terminated before any parent pilot.** All explicit reviewer subprocess sessions exited, including the focused suite and metadata helpers. This reviewer performed zero optimizer solves, controller runs, plant steps, genuine extended/full-lap attempts, browser control/server launch, hardware work, broad regression or formal Verification.

The original Primary authorization remains the only execution authority: after this exact-candidate PASS and live source/policy/resource preflight, at most one baseline 10-second pilot may be considered. Only a successfully completed/valid pilot and a retained finite pilot/host-supported preflight can permit the one baseline full-lap attempt. No retry/campaign or repeated interactive operation is granted by this review; final Primary acceptance remains pending.
