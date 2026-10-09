# Task007D-C — C0 blocked results and Engineering Orchestrator handoff

## 1. Task Completed

**BLOCKED, not complete.** C0 inspection and its urgent-grid counterexample are complete;
fixed-mode implementation and the remaining C0 acceptance tests are not. C1–C3 were not executed.
Baseline/main: `3564bb394c7f49cf430d6f0f976bea153a5da822`. The mandated stop condition is an
observed urgent release at 0.255 s; adding a 70 ms offset yields 0.325 s, outside the global
10 ms grid. See [contract audit](TASK007D_C_FIXED_HANDOFF.md) and [reproduction](TASK007D_C_REPRODUCTION.md).

## 2. Scheduling Contract

Required: exact `valid_from=t_release+T_h`, grid-aligned acceptance, preserved urgent semantics,
early waiting, exact-deadline readiness before acceptance, late permanent discard without solve
cancellation. These cannot all hold for the observed off-grid urgent release. No fixed setting,
packet field or runtime scheduling change was implemented. A remains the default predictor.

## 3. Event Ordering

Verified unchanged ordering: previously due actuator application; preparation completion;
waiting packet acceptance; disturbance/exhaustion; codriver tick; nominal or urgent release;
zero-duration continuation or physics. Completion clears pending before urgent release at the
same timestamp. Pending old-packet commands retain their originating plan ID. No C ordering
claim is made beyond the required contract documented in the audit.

## 4. Grid Alignment

An urgent request latches at 0.160 s while packet 1 (released 0.100 s) is busy. Its readiness
at 0.255 s immediately launches urgent packet 2. Every eligible T_h=n*10 ms preserves the
release's 5 ms off-grid phase. This is much larger than the 1e-10 s event tolerance. The separate
unblocked-urgent fixture releases on-grid at 0.050 s; the conflict specifically includes busy
completion behavior. Rounding takeover, delaying release or suppressing urgent work requires
an explicit policy revision, not a numerical fix.

## 5. Candidate Deadlines

All eligible offsets 10–100 ms were checked **algebraically for grid compatibility**, not for
reliability. All fail for this release. C1/C3 candidates were not selected because C0 stopped.
No 50/60/70/80 ms racing result or ranking exists in this delivery.

## 6. Deadline ECDF

**NOT EXECUTED.** Historical N8 preparation records were not reanalyzed after the C0 stop.
No sample count, quantile, maximum or exceedance estimate is fabricated. The assignment's
approximate historical values are not a newly measured Architecture C reliability result.

## 7. Chronology Test Results

68 focused tests passed in 4.72 s: four new stop-gate tests plus 64 retained chronology,
diagnostic timing, predictor/runtime and tracker tests. The existing default-A fingerprints
for states, handoffs, releases, misses, controls, forecasts and solver inputs pass unchanged.
The reproducer confirms no overlapping solve, old authority/TVLQR/plant continuation during
busy work, unchanged startup, on-grid versus off-grid urgent cases and deterministic replay.
Fixed-mode early/exact/late acceptance, deadline misses, stale/expired handling, consecutive
misses and packet-age/reserve tests remain **NOT EXECUTED** because no fixed mode was built.

## 8. Jitter-Decoupling Results

**NOT EXECUTED — C1 gated by C0.** No sensitivity reduction or same-packet equivalence is claimed.

## 9. Controlled Miss Results

**NOT EXECUTED — C2 gated by C0.** The C0 155 ms fixture is a legacy planner-busy counterexample,
not the requested fixed 70/75 ms miss pilot. It has no fixed miss/discard/acceptance timestamps.

## 10. Variable-Handoff Baseline

Production variable behavior and default fingerprints are preserved. No new N8 gamma2.0 or
gamma1.8 baseline campaign was run. The only new raw physical trace is the existing isolated
straight-chart test at vx=2 m/s, with a deterministic planner and no NMPC solve.

## 11. Fixed-Handoff 50 ms

**ECDF NOT EXECUTED; no closed-loop run performed.** Hypothetical C0 target 0.305 s is off-grid.
The usual phrase “ECDF evaluated” would be inaccurate after this early stop.

## 12. Fixed-Handoff 60 ms

**ECDF NOT EXECUTED; no closed-loop run performed.** Hypothetical C0 target 0.315 s is off-grid.

## 13. Fixed-Handoff 70 ms

**ECDF NOT EXECUTED; no closed-loop run performed.** Hypothetical C0 target 0.325 s is off-grid.

## 14. Fixed-Handoff 80 ms

**ECDF NOT EXECUTED; no closed-loop run performed.** Hypothetical C0 target 0.335 s is off-grid.

## 15. Optional 90 ms

**NOT SELECTED; ECDF/closed-loop analysis NOT EXECUTED.** No feasibility justification was made.
The general offset-grid proof includes this offset without selecting it for a pilot.

## 16. Track Clearance

**NOT EXECUTED for C3.** All prior D3/D4/D5/D-P evidence remains preserved, including the adverse
R4-B recorded center-clearance result. The wide straight unit-test chart is not racing clearance
evidence or continuous swept-body certification.

## 17. Slack

**NOT EXECUTED.** The deterministic C0 planner has no optimizer slack variables. No synthetic
zero-slack result is substituted for a fixed-mode NMPC measurement.

## 18. Tire / Beta

**NOT EXECUTED for C3.** Existing plant diagnostics ran in the unit fixture without a reported
model failure; no gamma2/gamma1.8 tire-utilization or beta comparison was performed.

## 19. Steering / Rate

Existing requested/applied controls and their source plan IDs are preserved in C0 raw evidence.
Repeat fixture controls match exactly. **C3 utilization/reversal/rate-occupancy comparisons NOT
EXECUTED.** No physical law or clamp was changed.

## 20. Smoothness

**NOT EXECUTED.** No fixed/variable heading, steering or acceleration variation ranking exists.
A short straight counterexample cannot establish racing smoothness improvement.

## 21. APEX→Vehicle Tracking

**NOT EXECUTED for C3.** No six-state N8 tracking RMS/max comparison is available. C0 verifies
that the existing urgent threshold can latch while the planner is busy; it is not an optimizer
performance test. Canonical ordering and angle conventions remain unchanged.

## 22. Timing Metrics

Observed C0 times: release 0.100 s; urgent trigger 0.160 s; busy nominal miss 0.200 s; readiness
and subsequent urgent release 0.255 s. Urgent packet 2 completes at 0.410 s, with nominal busy
misses at 0.300/0.400 s. These are existing variable-mode events. Fixed valid_from, acceptance,
wait, deadline margin and consecutive fixed misses are **not applicable**, not fabricated zeros.
There was no fictional cancellation and no parallel planner launch.

## 23. Deadline Reliability

**NOT EXECUTED.** No actual Architecture C handoff deadline was scheduled. Planner-busy misses
in the unit fixture must not be counted as fixed-handoff misses or historical ECDF estimates.

## 24. Trajectory Reserve

Existing reserve and old-packet continuation checks pass; the counterexample has no fallback
or reported failure. Fixed acceptance reserve/age, consecutive deadline-miss reserve and
exhaustion outcomes are **NOT EXECUTED**. Existing warning/critical/minimum rules are untouched.

## 25. Responsiveness Cost

Analytical constant-speed distance `d=v*T_h` only, not observed trajectory or actual authority
latency. A missed deadline or deferred release can increase real high-level reaction time.
TVLQR remains active on the prior accepted trajectory during ordinary waiting/busy work.

| T_h | At 1.5 m/s | At 3.0 m/s | At 6.0 m/s |
|---:|---:|---:|---:|
| 50 ms | 0.075 m | 0.150 m | 0.300 m |
| 60 ms | 0.090 m | 0.180 m | 0.360 m |
| 70 ms | 0.105 m | 0.210 m | 0.420 m |
| 80 ms | 0.120 m | 0.240 m | 0.480 m |

## 26. RK4 / Event Findings

Source inspection confirms that pending readiness participates in `next_time`, so it can split
RK4 without changing authority. The observed 0.255 s event is off the codriver grid but lies on
a 5 ms plant subdivision; no numerical divergence is inferred from this alone. C1/C3 partition
counts, segment extrema and common-grid state comparisons are **NOT EXECUTED**. No integrator
change was made to enforce agreement.

## 27. Required Figures

All nine are **NOT GENERATED**, because the required experiments/ECDF are gated. No placeholder
or fabricated traces were substituted:

1. `task007dc_fixed_handoff_timeline.png`
2. `task007dc_deadline_ecdf.png`
3. `task007dc_jitter_decoupling.png`
4. `task007dc_deadline_miss.png`
5. `task007dc_variable_vs_fixed_handoff.png`
6. `task007dc_track_clearance.png`
7. `task007dc_smoothness.png`
8. `task007dc_reserve.png`
9. `task007dc_responsiveness_tradeoff.png`

The observed C0 timeline is a numerical table in the contract audit, not a fixed-scheduler
result. Prior D-P figures were neither regenerated nor edited.

## 28. Regression Tests

68 focused passes; scoped Ruff lint/format pass. Full-suite execution is **deferred**, not passed:
it contains NMPC/multilap integration simulations and C0 has not cleared the required prerequisite.
No existing tests, expected fingerprints or tolerances were modified. Source hashes and final
preservation checks are in [verification.json](task007d/c/verification.json).

## 29. Generated Artifacts

Three documents: this 36-section results report, the contract audit and reproduction guide.
One isolated audit/export script and four new tests. Compact evidence under `docs/task007d/c/`:
`c0_summary.json`, `offset_grid_audit.csv`, `verification.json`. Ignored raw evidence:
`results/task007d/c/c0_urgent_grid/{raw,summary}.json`. Handoff updated; no ADR or roadmap edit
because no alternate urgent policy or scheduling architecture was selected.

## 30. Known Limitations

This proves a scheduling-contract conflict, not that fixed handoff is scientifically ineffective.
No C production code, frozen racing pilot, measured preparation campaign or ECDF result exists.
The analytic straight fixture and synthetic vehicle are not physically identified APEX data.
Only legacy behavior and the counterexample are verified. C0 acceptance coverage remains incomplete.

## 31. Architecture Deviations

**None implemented.** Specifically no rounding, urgent suppression/deferment, scheduler queue,
solve cancellation, predictor change, new physical model, estimator change, packet schema change,
B integration or lightweight runtime activation. C remains a proposed opt-in research mode.
A default, experimental B and the D-P nonselection remain intact. No System Identification,
LMPC, adaptive codriver, opponent handling, energy work or controller/profile freezing began.

## 32. Recommended T_h

**Undetermined.** All grid-aligned offsets share the urgent-phase conflict. No deadline ranking
from lap time or unexecuted reliability data is justified. Resolve the release policy, complete
C0, then conduct the required ECDF selection before observing C3 outcomes.

## 33. Is Architecture C Worth Continuing?

**Further contract work is justified; a larger measured campaign is not yet justified.**
Decision questions A/B/C/D/E/F/G remain unmeasured: there is no jitter, partition-causality,
best-offset, actual fixed-miss, improvement or staleness result. This stop concerns incompatible
requirements rather than a negative physical comparison.

## 34. Is Architecture B Comparison Now Justified?

**Not by new C evidence.** No C pilot ran, so question H cannot be answered affirmatively from
this task. Existing B evidence is unchanged. Finish an authorized A-only C investigation first.

## 35. Recommended Next Step

Engineering Orchestrator should explicitly resolve off-grid urgent releases. One defensible
option for review is fixed-mode-only deferred urgent launch at the next codriver grid tick,
keeping a running solve pending until completion. This changes urgent latency and requires
approval; it was not implemented. Alternatively revise exact-offset or grid-alignment requirements.
Then resume bounded C0 implementation/testing before C1–C3. Do not bypass the stop by disabling
urgent behavior, silently rejecting its work or choosing favorable timing histories.

## 36. Reproduction Commands

See [TASK007D_C_REPRODUCTION.md](TASK007D_C_REPRODUCTION.md) for the exact focused test, Ruff,
SINGLE fixture export and compact evidence commands. They reproduce only the C0 conflict.
Normal commit/push follows the standing workflow; exact delivery SHA/URL is reported in the final
handoff and Git history. **STOP at C0. Await Engineering Orchestrator review.**
