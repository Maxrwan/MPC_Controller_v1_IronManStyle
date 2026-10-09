# APEX handoff — Task007D-D2 complete; stop for review

Updated 2026-10-09. D2 integrates the existing committed-prefix predictor into
`AsyncRunner`/`TrajectoryPlanner` behind `AsyncConfig.committed_prefix_prediction=False`.
Only a real boolean is accepted. Explicit True enables Architecture B with the same
estimated target and variable-availability handoff; Architecture A remains the default.
Normal/urgent releases capture applied input, last application and any pending request/time
after the current codriver tick/skip. New same-time zero-latency work stays pending.
Startup, event ordering, model/RK4, packet acceptance, fallback and NMPC remain unchanged.

Read `TASK007D_COMMITTED_PREFIX_CONTRACT.md` for the D2 interface, telemetry and verification.
The existing readiness-state mismatch is not an aligned handoff error. Incompatible B
planner signatures fail explicitly; legacy planners still work when B is disabled.

Verification: 101 focused tests passed in 4.51s (16 D2 plus all 85 D1/related tests).
Default/explicitly disabled A exactly match the pre-D2 physical/chronology/solver-input
fingerprints. B capture, pending/zero-latency/urgent order, causal inputs, repeatability,
startup and buffer-authority cases pass. Scoped Ruff check/format passed. No measured
campaign was active before testing; no laps, benchmark repetitions or old-result exports ran.

Standing GitHub workflow is now in AGENTS.md: commit and push authorized verified work,
preserving unrelated changes; report SHA/branch/URL only after successful push verification.
This supersedes older commit-permission notes below. D2 started on clean main at
`4a7026eac13e2a5d976a0dfb2a6756dfa5de6afb`; delivery commit identity is in the final D2 report
and Git history. No force push or history rewrite is authorized.

STOP for Engineering Orchestrator review. Task007D is not complete; Architecture C and major
timing experiments remain excluded. Recommend a separately bounded review/validation plan
for A/B before any fixed-handoff implementation. Prior handoffs are retained below.

---

# APEX handoff — Task007D-D1 complete; stop for review

Updated 2026-10-09. Only D1 is implemented and verified. Task007D is not complete.
`ActuationPredictor.predict` now accepts optional immutable `CommittedControlPrefix`
release-known actuator state. It replays the one already-pending application with the
existing elapsed-time steering clamp, skips busy forecast ticks, then resumes causal
ideal-timing TVLQR forecasting on the release-active packet. At the target, due committed
applications precede return; same-time new feedback follows handoff and is excluded.

Read `TASK007D_COMMITTED_PREFIX_CONTRACT.md` for fields, capture phase, endpoint semantics,
causal limits and proposed later integration. `TASK007D_CURRENT_TIMING_AUDIT.md` remains
the pre-D1 audit. No AsyncRunner/planner wiring, Architecture B/C activation, fixed handoff,
model, cost, horizon, solver, packet, buffer, default or prior-result change was made.

Verified: 85 focused tests passed (37 new committed-prefix cases plus existing tracker,
async chronology and diagnostic timing cases); scoped Ruff check/format passed. Exact
pre-D1 golden outputs pass; four short comparisons against unchanged AsyncRunner pass.
No active measured campaign was found before testing; no laps or benchmarks were run.
Preexisting work remains in this dirty tree. Do not commit unrelated changes.

Next: Engineering Orchestrator review, then a separately authorized D2 opt-in integration
capturing applied/pending command state at planner release. Do not implement it automatically.
The accepted review candidate remains N8/dt0.1s/lambda0/gamma2 with frozen weights and TVLQR;
production defaults remain unchanged. Earlier C1–C4 handoff is retained verbatim below.

---

# APEX handoff — Task007C C1–C4 ready for final review

Updated2026-10-08. Task007C C1–C4 is COMPLETE and stopped for user review. Scientific experiments, reports,
physical-chronology checks and the inventory are complete. No experiment worker or measured
campaign remains active. No further implementation is authorized before this review.

## Start here

- `TASK007C_RESUMED_RESULTS.md`: original48-section scientific report, four-axis comparison,
  recommendation and bounded provisional operating-point evidence.
- `TASK007C_ARTIFACT_INDEX.md`: verified absolute links to reports, dashboards, sector zooms,
  physics plots, measured distributions, failures and raw evidence.
- `TASK007C_RESUMED_REPRODUCTION.md`: exact executable commands and finite-history rules.
- `TASK007C_MEASURED_RESULTS.md`: every measured run, outcome, coverage and distribution.
- `TASK007C_SUSTAINED_CONFIRMATION.md`: exact N6/N8 parity and24 separately reported lap segments.

Current user brief: attachment `6fa32293-b32a-4ccb-9110-ac5a34e1787d/Pasted text.txt`.
Original detailed brief/48-section requirement: `f3aef931-588b-4af1-be06-3450fc5a54cf/Pasted text.txt`.
Original Task007C gate-stop reports are historical; Task007C-R passed, and C1–C4 have now run.
Do not restart the grids or reopen the old gate as if this work were still unexecuted.

## Recommendation for review, not a production change

Retain alpha_vy=alpha_r=1, lambda0, dt0.1s and frozen100Hz TVLQR. Extend horizon only.
N8/gamma2 is the stronger current end-to-end review candidate: five measured completions,
heading TV8.179–8.417rad, tracking ey RMS1.261–1.307mm, measured planner mean55.52–56.47ms,
p95 68.15–69.57ms, planner demand0.554–0.560core-s/s. Minimum measured reserve0.570s.
No observed boundary/solver/fallback failure in those five runs. Occasional deadline misses
and frequent smaller steering corrections remain; do not claim perfect smoothness or a
hard-real-time guarantee. The demonstrated gamma2 point is not a certified continuous envelope.
Adjacent controlled N8 gamma1.8/1.9 results support review; N8 gamma2.1/2.2 lacks measured evidence.

N6 is the smaller broadly promising mathematical extension, but one of five measured gamma2
runs exhausted its trajectory. Its five gamma2.2 completions cannot erase that failure.
Gamma2.2 N6 also worsens on the third smooth sustained lap. Keep it as upper stress evidence,
not the fastest automatic envelope selection. All production defaults remain unchanged.

## Completed evidence

- C1:16 baseline fixed/smooth cells at gamma1.5–2.2 plus6 informative lambda2 screens.
- C2:36 initial grid cells plus4 follow-ups. Half-vy and weakened yaw costs are not robust.
- C3:18 primary horizon cells plus gamma1.9 and gamma2.2 supplemental coverage.
- C4:30 static-weight cells; nonmonotonic, chronology-dependent effects; no justified gate.
- Gamma2 retained-history matrix:25 records, including the rejected half-vy and lambda4 cases.
- Gamma2.1 matrix:15 records; gamma2.2:7 records (N6 five histories, N4 fixed/smooth stress).
- Fresh measured:20 records, five per gamma2 N4/N6/N8 and gamma2.2 N6. N4/N8 gamma2 and N6
  gamma2.2 each complete5/5; N6 gamma2 completes4/5. No unfavorable run is discarded.
- Eight sustained cases all complete three crossings without boundary/solver/fallback/deadline
  failures. First crossing starts at s_abs=1m; only the next TWO are complete geometric laps.
- Exact fixed N6/N8 repeats pass across physical/NLP channels; candidate control offsets use6(N+1).
- Four0.8s zero/injected checks pass physical chronology. Injection150ms planner/25ms driver
  yields4 planner/53 driver misses each, moving physics and application staleness.
- Native backend audits observe max1 process thread, N6/N8 CPU/wall0.9970/0.9993.
- Internal physics and measured worst-case dashboards/phase portraits exported and inspected.
- 533 full regression tests passed before later diagnostics;13 ablation tests,27 DARE checks,
  three current physics/extraction tests and Ruff checks passed. Runtime mathematics unchanged
  since those checks. `regression.log`, `focused_tests.log`, `physics_tests.log` retain evidence.

The measured all-formulation common prefix is1–97.042m because N6 failed before technical
entry. Do not compare its shorter whole-record TV with completed rolling segments. Common
progress tables and whole-record failure counts are separate. No finite trace is extended.

## Retained failures and causal check

Five formulation boundary rejections remain: baseline2.2 fixed (44 samples), combined(.25,.25)
fixed (159), zero-yaw smooth (62), half-vy E (59), lambda4 F (100). The latter two have unsafe
nominals, material slack and local position error below0.010m; no solver/deadline failure.
All are hash-bound in `reviewed_failures.json`; do not measure the rejected alpha/lambda variants.

Measured N6 gamma2 repetition00 stops at18.756621s outside the baseline fallback domain.
Pending plan182 succeeds in13 iterations but uses593.021ms wall versus118.649ms CPU; its
availability18.793021s exceeds the old trajectory end. Physics advances3.1085m during the
observed pending interval.5 planner/6 driver misses, no boundary or solver failure.
The wall/CPU gap's OS cause is unresolved; never discard it as a presumed external outlier.

Replaying that exact recorded history reproduces N6's physical and NLP channels exactly.
Transferred N8 remains valid until driver trace exhaustion18.760s, with0.196621s reserve and
no fallback. It is censored before the replacement completes, not a completed recovery test.
`measured_n6_failure_replay_parity.json` and `trace_measured_n6_exhaustion.json` retain evidence.
No invented driver tail or new fixed-handoff architecture was introduced.

## Preservation and finalization

155 formulation records, baseline parity and four latency cases total160 raw cases. The final
auditor PASSED and verified current runtime against case hashes, configurations/fixtures/native mode,
original B/C/CR hashes (675/293/1907 files), and event-level held commands, nonoverlap,
timestamped references and rate constraints. `provenance.json` inventories results/source/docs.
The previous disk interruption affected derived exports; raw evidence was verified and exports
regenerated. No prior results were deleted. Last checked free space was about7GiB.

Only approved alpha weights and compatible terminal construction change runtime mathematics
relative to resumption. Earlier task changes were already present in this dirty checkout.
Do not revert preexisting changes or commit without a new request.

## Deferred work: stop here

Review the48-section report and the horizon-only recommendation before further implementation.
No adaptive codriver, LMPC, Planning redesign, online SI, energy or opponents are authorized.
After formulation review, compare current variable availability, committed-control-prefix MPC
and fixed future30/40/50ms handoffs on the10ms codriver grid; document-only so far.

AFTER ONLINE SI IS IMPLEMENTED AND ACCEPTED: update the workbench for identified parameters,
spatial maps, uncertainty, residuals, nominal/identified predictions, learned grip and lap
comparisons. Then study estimation cost/scheduling/rate, asynchronous model adoption delay,
HIL/bench execution where available, sensor/actuator latency, missed updates and uncertainty
response. This mandatory future checkpoint remains in `PROJECT_ROADMAP.md`; do not implement it now.
