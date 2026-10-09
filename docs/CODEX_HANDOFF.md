# APEX handoff — Task007D-C BLOCKED at C0 urgent-grid contract; stop for review

Read TASK007D_C_FIXED_HANDOFF.md, the 36-section TASK007D_C_RESULTS.md and
TASK007D_C_REPRODUCTION.md. Started on clean main
3564bb394c7f49cf430d6f0f976bea153a5da822. No runtime source, predictor, packet schema,
controller mathematics or production defaults changed. Delivery SHA/URL is in Git history and
the final response under the standing commit-and-push workflow.

C0 reproduced an explicit assignment stop gate with the existing isolated StraightPlanner,
straight chart and real NumPy plant: plan 1 releases at 0.100 s, an urgent request latches at
0.160 s while busy, and completion at 0.255 s immediately launches urgent plan 2. Every eligible
10–100 ms grid-aligned offset retains the 5 ms phase error; +70 ms gives target 0.325 s.
Existing immediate urgent release, exact release-plus-offset takeover and global 10 ms alignment
cannot all hold. A late fixed deadline would not cancel the running solve, so discarding its
result at completion does not remove the urgent-release conflict.

No workaround was applied: no rounding, deferred/suppressed urgent work, cancellation or parallel
solve. C0 fixed-mode implementation/tests remain incomplete; ECDF selection, C1 jitter, C2 miss,
C3 racing comparisons and all nine figures are NOT EXECUTED. Full regression is deferred because
it includes NMPC/multilap integration and C0 must clear before those simulations. This is not a
negative finding about fixed scheduling's physical performance; no such comparison occurred.

Verification: 68 focused tests passed (4 new conflict tests plus 64 retained), including the
unchanged pre-D2 default-A fingerprints. Scoped Ruff lint/format passed. Compact C0 provenance,
all-offset grid arithmetic and preservation evidence are under docs/task007d/c/. Ignored raw
unit-fixture chronology is under results/task007d/c/c0_urgent_grid/. All 451 other preexisting
tracked files, all 10,926 prior result size/mtime records and all 74 D3/D4/D5/D-P raw hashes
remain unchanged. Existing negative outcomes and figures remain preserved.

Required Engineering Orchestrator decision: revise the off-grid urgent contract. One candidate
for explicit approval is fixed-mode-only queued urgent release on the next global driver tick,
with pending solve/busy rules preserved. This changes urgent latency by up to one tick and was
NOT selected or implemented. Alternatively revise the exact-offset or grid-alignment condition.
After that review, resume C0 before C1–C3; no deadline candidate is selected yet.

A remains default; B experimental; P0/P1a/P1b not selected. C is not implemented in this blocked
delivery. No System Identification, LMPC, adaptive codriver, opponent/energy work or final profile
freeze began. **STOP AT C0. Task007D-C remains BLOCKED. Await Engineering Orchestrator review.**

---

# APEX handoff — Task007D-P offline prediction study complete; stop for review

Read TASK007D_LIGHTWEIGHT_PREDICTION_STUDY.md and compact docs/task007d/p/ (three figures,
per-state/input tables, benchmarks and provenance). Started on clean main
b1ab2205b1de0ff7a425de7adf68f7a1a376fbc3. Delivery SHA/URL is in the final report and Git
history under the standing commit-and-push workflow. No production code or old study changed.

A/P0/P1a/P1b/P2 were evaluated on 190 retained release contexts: 152 D4 and 38 supplementary
D3 gamma2, keeping A/B-controlled histories separate. All 950 forecasts are comparable; zero
failures, target exclusions or predicted center-boundary crossings. A/P2 reproduce 380/380
retained state/control outputs exactly. There are 170 node targets and 20 interior targets
(the first two releases per history); truth remains 180 recorded events and 10 labeled RK4
reconstructions. No new physical simulation or solver run occurred.

P1b uses existing TVLQR RK4 Jacobians and stored four-state gains in [e_y,e_psi,vy,r] order,
with constant speed/progress errors. It is an ideal unsaturated error approximation, omitting
nominal-flow defect, known-input forcing and delay/cross-coupling; it is not a validated
six-state predictor. All lightweight methods include causal committed-input replay and feasible
ideal future feedback, but their state/input pair is not guaranteed jointly dynamics-consistent.

Five fresh sequential SINGLE predictor-only workers measured 960 warm calls per method.
Median wall ms: A 7.394, P0 4.319, P1a 4.303, P1b 4.607, P2 8.986. Complete costs include
preceding-input preview and domain checks. P1b also needs 10.838 ms cold Jacobian compilation;
context matrix evaluation remains in each warm call. Observed worker threads [1], batch
CPU/wall about 0.999. Historical total preparation is about 61–67 ms; the 2.8–4.7 ms savings
are modest, not a controlled measurement of total preparation improvement.

Lightweight accuracy is substantially worse. R4_A lateral RMS A/P0/P1a/P1b/P2 is
0.000245/0.009417/0.009621/0.007084/0.000129 m. P1b yaw RMS is 1.26042 rad/s, versus
0.125324 A and 0.086552 P2. P1a sometimes improves P0 but does not dominate; later releases
remain weak. Near R4_B's clearance excursion, P1a/P1b lateral errors reach centimetre scale.
D5's retained B minimum clearance 0.102185 m and 0.022185 m remaining synthetic margin are
unchanged. Offline prediction accuracy does not establish closed-loop safety.

Verification: 89 focused tests (27 new, 62 retained) passed; scoped Ruff lint/format passed.
Three PNGs regenerate identically within the same environment and were visually reviewed.
Numerical exports reproduce byte-for-byte. All 430 other preexisting tracked files are
unchanged, as are all 61 D3/D4 file hashes and 10,912 prior result size/mtime records. Only
ignored results/.DS_Store metadata changed during the task; it is neither evidence nor staged.
Raw D-P results stay ignored; compact review artifacts only are committed.

Recommendation: none of P0/P1a/P1b for immediate closed-loop testing or Architecture C
integration. P1a is the simplest candidate for a separately authorized offline consistency
investigation if desired; do not silently invent missing dynamics. Keep A default and B
experimental. **STOP AFTER D-P. Task007D remains incomplete. Await Engineering Orchestrator
review. No Architecture C, production integration or further campaign is authorized.**

---

# APEX handoff — Task007D-D5 offline forensics complete; stop for review

Read TASK007D_D5_CAUSAL_REVIEW.md and compact docs/task007d/d5/. D5 analyzes retained D4
records only: no new forecast, solver/plant execution, campaign or controller/runtime edit.
Started on clean main feb7c706f3f4b16d2a50240f151070b57e9cf50e. Delivery SHA/URL is in the
final report and Git history under the standing commit-and-push workflow.

R4 minima reproduce exactly: A 0.22866129128417373 m at 1.865 s, s=11.454454794338089 m;
B 0.10218470460178081 m at 1.890 s, s=11.537880251173657 m. Both are right-limited in the
synthetic long_straight, with constant 0.55 m half-widths. B leaves 0.022184704601780805 m
beyond the unchanged 0.08 m margin. At B's minimum time the gap is -0.129529941 m; nominal
position contributes -0.129652013 m, tracking difference +0.000122072 m. At matched progress
the gap remains approximately -0.127621029 m. Width/progress alone do not explain the loss.
Nominal starts inherit the diverging physical states: this algebra does not prove a unique
upstream cause or a newly unsafe packet. Plan 18 inherits an already large lateral gap.

First chain verified: identical release context at 0.100 s, differing predicted x0/previous
input and optimized packet 1, acceptance at 0.160 s, acceleration split at 0.175 s, state
split at 0.180 s. Steering stays identical until the packet-6 request at 0.700 s applies at
0.715 s; subsequent heading/lateral separation grows. Full NLP/warm-start/internal forecast
traces are unavailable, so causal attribution to a single release remains unresolved.

Low-latency release 2 dominates aggregate A squared errors. Later B heading/lateral RMS
worsens in R1/R2/R3 on both host histories. Worst added absolute errors across those histories:
0.00229321 rad/s yaw, 0.000140944 rad heading, 0.0000128980 m lateral. These are above roundoff
but small absolute errors; ratios alone do not justify predictor changes. Unknown future
latency cannot explain zero-latency R1; held-curvature approximation/error cancellation is
a hypothesis, not an established cause. The large R4 clearance loss is a separate risk.

Verification: 15 focused offline tests pass; scoped Ruff lint/format pass. Export is byte-
reproducible. All 1,400 driver references, 152 handoff residuals and 152 retained active
forecast inputs match exactly; no chronology issue. All 40 D4 files retain SHA-256, all
10,913 prior results retain size/mtime, all other 417 prior tracked files are unchanged.
No raw archives committed. Existing D4 scientific gates remain clear; synthetic recorded
clearance does not certify continuous-time body safety or physical vehicle validity.

Recommendation: retain A default and B experimental. A separately authorized bounded C
investigation is scientifically reasonable, including legacy A to isolate fixed-handoff
effects. Do not select B automatically. A common-release checkpoint with full optimizer and
tracker traces is the minimum next diagnostic for causal attribution; it was not executed.
**STOP AFTER D5. Task007D remains incomplete. Await Engineering Orchestrator review.**

---

# APEX handoff — Task007D-D4 complete; stop for review

D4 ran exactly eight sequential SINGLE synthetic N8/gamma2 pilots, two seconds each:
A/B at planner/codriver delays 35/0, 35/5, 60/5 and 60/15 ms. Reused D3 35/15 ms evidence
without rerunning it. Read TASK007D_AB_TIMING_SENSITIVITY.md and docs/task007d/d4/.
Only pilot CLI/worker delay plumbing and offline analysis/tests were extended; all src/
modules, controller mathematics, estimator, scheduler and production defaults are unchanged.

There are 152 new comparable release contexts: 38 pending due-now, 114 future-pending,
zero no-pending. All active shadow forecasts exactly reproduce runtime NMPC inputs;
no forecast failures or missing targets. Existing isolated no-pending tests still pass.
All six aggregate RMS errors improve in every regime and both host histories, including
when the first runtime release is excluded. Thus aggregate benefit is not restricted to
15 ms driver latency or skipped ticks. This does not establish per-release superiority.

Important adverse findings: low-latency heading/lateral errors worsen on most later releases;
release 2 dominates their aggregate A squared error. An explicitly post hoc releases 3–19
check reveals RMS deterioration in several low-latency channels. R4-B minimum center
clearance falls to 0.102185 m from A's 0.228661 m, leaving only 0.022185 m above the frozen
0.08 m tracking margin, despite improved tracking RMS. No gate triggered, but this material
clearance loss must not be hidden by the favorable prediction averages.

All runs have common recorded coverage 0–1.995 s, 19 accepted handoffs, zero rejected packets,
boundary observations, solver/model failures, exhaustion or fallback; slack <9.1e-11 m.
Planner misses are zero; driver busy ticks are 0 for 0/5 ms and 100 for 15 ms. Readiness/target
mismatch is 18 ms (35 ms planner) or 43 ms (60 ms planner) initially, then zero. Accepted
handoff continuity and aligned prediction errors remain separate. First state divergences
occur at 0.145/0.150/0.170/0.180 s for R1–R4, after accepted packet authority and application.

Verification: 133 focused tests passed in 7.94 s (17 new plus 116 retained), scoped Ruff checks
passed, and repeat export is byte-identical. Raw evidence (~10 MiB) stays ignored under
results/task007d/d4; compact per-state/phase/timestamp data and source hashes are committed.
D3 and all historical evidence remain preserved. Started on clean main
784e86ff0aceb5f779b475fdfb6cf7d0d94912ec; delivery SHA is in the final report/Git history.

Recommendation: keep B as a research candidate, not yet the selected Architecture C predictor.
Authorize a separate bounded causal audit of low-latency release 2/3 regressions and R4-B
clearance loss before any refinement or adoption. **STOP AFTER D4.** Task007D is incomplete;
no Architecture C, production-default change, full lap or measured campaign is authorized.

---

# APEX handoff — Task007D-D3 complete; stop for review

D3 adds opt-in detached release capture and offline same-target A/B scoring. Architecture A
remains the default. No predictor, controller, plant, event scheduling or packet-authority
policy changed. Read `TASK007D_AB_PILOT.md` and compact `docs/task007d/d3` evidence.

Four sequential SINGLE imposed-delay pilots (gamma 2.0 and 1.8, A/B, 2s each) passed the
scientific stop gate. Fixed planner 35 ms/driver 15 ms gives 19 comparable pending releases per
run (76 total); no forecast failures or excluded targets. Offline active forecasts exactly
match runtime NMPC inputs. B reduces all per-state RMS values on each separate host history,
including about 47% yaw rate and 69% heading/lateral-offset error. Worst vx error can increase;
this is short synthetic pending-heavy evidence, not a universal or physical-validation claim.

Common physical coverage is 0–1.995 s. Zero observed boundary crossings, solver/model failures,
handoff rejections or authority issues; max slack <9.1e-11 m, reserve >=0.67 s. Imposed driver
latency causes 100 busy ticks per run; planner busy misses are zero. First forecast difference
is at 0.1 s, handoff 0.135 s, applied acceleration split 0.155 s, first state split 0.16 s. Timing and
per-state handoff-continuity diagnostics are separate from aligned target prediction errors.
Each run has 18 recorded targets and one labelled RK4 reconstruction, with zero bracket closure.

Verification: 116 focused tests passed in 7.40 s; scoped Ruff check/format passed. Capture on/off
preserves exact physical/solver/event/RK4 channels; old default-A fingerprints remain valid.
An initial gamma 1.8 fixture-path failure occurred before simulation and is preserved separately
from the successful retry. Raw ~4.8MiB is retained under results/task007d/d3; only compact
review evidence is committed. No prior B/C/C-R evidence was modified.

D3 started from clean main b27c0465f3cb1a13ad20152c17bcfadb37c2a8c4. Delivery SHA/URL is in
the final report and Git history under the standing commit-and-push workflow.
Recommend review followed by a separately authorized short A/B timing/coverage matrix,
including no-pending cases. **STOP: Task007D is not complete. Do not start Architecture C,
full racing or measured repetitions without the next Engineering Orchestrator instruction.**

---

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
