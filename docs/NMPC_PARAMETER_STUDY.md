# Task006.2 — synchronous NMPC parameter study

## Purpose and dependency

Task006.1 is present and validated: bounded combined-grip NumPy/CasADi equations, archived
parity and regression evidence. This study characterizes the current synchronous direct
multiple-shooting IPOPT controller. It does not implement new solvers, asynchronous planning,
compensation, a codriver or racing objectives. No global/convex optimum is claimed.

## Reference and immutable physics

Reference:20 Hz,T=.05,N20,1 s coverage,5 RK4 substeps, grip physics, unchanged Task006 weights,
terminal DARE schedule, slack penalties, actuator/model constraints and IPOPT defaults.
Synthetic vehicle, periodic tracks,2 m/s reference, initial cornering vy/r, zero held input,
plant step<=.005 s, preview approximation and baseline fallback remain unchanged.
Circle/oval zero and measured runs are repeated before screening. Old Task006.1 artifacts
are preserved, not relabeled as current measurements.

## Predeclared development acceptance envelope

Before classifying candidates, full-run oval RMS thresholds are set to:

- lateral<=.025 m (above prior .005–.017 m NMPC/LQR results, well inside narrow .3 m boundary),
- heading<=.06 rad (allows startup/transient degradation, about3.4degrees),
- speed error<=.08 m/s (4% of2 m/s reference),
- no physical boundary or model-validity failure,
- no solver failure/fallback dependence, all required laps completed,
- maximum predicted slack<=1e-4 m (0.1 mm; every positive slack is still logged),
- tire utilization<=1+1e-12.

This is a provisional synthetic development envelope, not measured vehicle safety or a
requirement for submillimeter circle tracking. Any solver failure is conservatively excluded,
stricter than rejecting repeated failures alone. Candidates outside the RMS envelope remain
visible but cannot win compute-efficiency selection. Tiny interior-point slack differences
below the material gate are not treated as separate Pareto objectives.

Integration gate:80seeded valid snapshots,seed60062, speed1–3 m/s,vy±.15 m/s,r±.8 rad/s,
heading/lateral±.1,steering±.25 rad,acceleration±1 m/s²,curvature±.8/m. Compare one interval
with DOP853 applied to the independent NumPy derivative (rtol1e-11,atol1e-12), with the
same frozen curvature on both sides. Error scales in canonical order are[.5,.5,1,.1,.1,.1].
Require maximum scaled norm<=.02,RMS scaled norm<=.005 and no invalid internal plant stages.
These explicit conservative accuracy gates prevent selecting a cheap but distorted prediction.
Per-channel SI errors and independent equal-step NumPy/CasADi parity are also retained.

## Staged design and observation windows

A: fresh circle/oval zero and measured latency,2laps (80 s cap).
B: N8/10/12/15/20/25,20 Hz,5 substeps,1oval lap (45 s cap).
C: substeps1/2/3/5 for best compute and best tracking quality-qualified B horizons.
D:10/15/20/25 Hz,N=frequency for1 s coverage, zero and measured latency. Preserve the
literal selected substep comparison; separately refine inaccurate intervals. Afterward test
the Stage B compute winner's coverage (0.4 s in this run) at all four rates, rounding N to
an integer (N4/6/8/10). This small follow-up separates release frequency from horizon cost;
no full Cartesian horizon/rate/integration search is performed.
E: grouped one-factor changes from the chosen structural anchor: lateral/heading,vy/r,
speed andR multipliers .5/1/2;W .25/.5/1/2. At most one combination of independently
promising tracking/speed changes; never a Cartesian product.
F: terminal multipliers0/1/.5/2; no terminal equality.
G: unchanged IPOPT, max40 iterations, tol1e-6, stricter tol1e-8, limited-memory Hessian and
warm_start_init_point=yes. Existing independent feasibility acceptance remains<=1e-6.
No relaxed actuator/friction/slack domain or intentionally poor-success tolerance.

Identical experimental configurations are reused and marked with every applicable stage,
preventing redundant runs. Hashes include mode,track,lap/duration target,disturbance and all
controller settings. Screening uses one full oval lap for equal exposure. Reference and
selected confirmations use two laps; compare those windows separately. Failed runs retain
their shorter observed windows and missing lap times. No failed-run RMS is treated as a
successful full-lap result. Finalists confirm circle,oval,combined disturbance and measured
latency; deterministic25/45/60 ms cases characterize selectedC.

At different periods, preserve stage-sum cost semantics (no new dt multiplier) and nominal
steering increment limit rate*dt. Terminal matrices remain the provisional Task005100 Hz
schedule; terminal multiplier scales the complete lateral+speed terminal term. Grouped stage
multipliers do not silently recompute the terminal matrix. Frequency therefore also changes
stage density relative to terminal cost; that coupling is reported rather than hidden.

## Timing and runtime reuse

Set OPENBLAS_NUM_THREADS=1,OMP_NUM_THREADS=1. Runs are serialized; no parallel benchmark
workers. perf_counter measures preview, geometry/reference subparts, warm preparation,
parameter packing, solver adapter, backend solve, output validation/postprocessing and total
controller computation. Nested timings must not be summed twice. Construction is outside
repeated solves; each experiment builds one MPCProblem and one IPOPT instance. No symbolic
reconstruction occurs in compute_control. No defect requiring a graph-reuse change was found.

The existing measured physical latency remains actual solver-call time, preserving Task006
semantics. Total compute is additionally reported; solver-only deadline margin is optimistic
for end-to-end hardware actuation. These are local Darwin/arm64 measurements, not Raspberry
Pi timings. Background host scheduling/thermal effects can change measured outcomes.

The event runner already splits exact events. Only RunConfig validation was extended to
permit fractional controller/plant ratios when explicit event-based latency is enabled;
legacy integer-grid mode remains strict. This permits15 Hz exactly, without rounding to a
multiple of5 ms. Unit tests verify release times and maximum plant step.

## Pareto analysis and selection

Do not collapse outputs into a scalar score. The principal nondominated set compares
quality-qualified one-lap oval zero-latency configurations on p95 solve time, lateral RMS,
speed RMS and heading RMS. Failure/slack/boundary/grip conditions are hard gates. A record
is dominated if another is no worse on all four and strictly better on at least one.
Separate measured-latency plots show deadline reliability and observed tracking; failed runs
are labeled and excluded from viable selections. A projection into two dimensions need not
itself look like a two-criterion frontier.

A: smallest lateral RMS among front candidates with p95/period<=1 when available.
B: lowest p95 solve among the quality-qualified front.
C: initially lowest p95/period; after measured two-lap confirmations choose lowest lateral
RMS among quality passes with<=5% missed releases. If none pass, explicitly report the
lack of a validated synchronous real-time candidate rather than inventing one.
D: fresh current/reference configuration. Roles may coincide; no artificial distinct winner.

Compute ratios mean/p95=solve statistic/period. Categories:<.5 comfortable,.5–.8 moderate,
.8–1near deadline,>1nominal real-time infeasible. These are engineering labels, not guarantees.
A cold first solve can miss a deadline even if repeated-solve p95 is comfortable.

## Artifacts and future tasks

results/mpc_parameter_study/experiments.csv is the machine-readable database. Each run has
configuration.json,experiment.json,summary.json,states.csv,controls.csv,solver_events.csv and
predictions.jsonl. Configuration hashes and serialized settings make candidates reproducible.
Stage choices and selected A/B/C/D configs are explicit JSON. Re-running stages reuses cached
configurations; set APEX_STUDY_REPLICATE to a new label to record fresh timing replicates.

Predictions retain state/input trajectories, absolute node timestamps, sampled state, actual
completion state/time, scheduled completion, applied/completed flags and nominal remaining
horizon. Pending-at-end results have no actual completion; negative reserve is retained.
No trajectory buffers, interpolation policy or asynchronous consumer is implemented.

Task006.4 preparation includes lateral-state ranges, nominal4-state/1-steering-input model,
offline baseline-versus-NMPC command differences,100/200 Hz codriver options and existing
BaselineController timing (including geometry/reference lookup). It is not a TVLQR or linear
MPC codriver implementation, nor a claim about attainable Pi frequency.

Results, rejected configurations and data-derived recommendations are appended after the
staged experiments. Next is Task006.3 asynchronous planner plus high-rate trajectory codriver;
Task006.4 will compare a small linear MPC codriver with LQR/TVLQR afterward. Neither is
implemented here.


## Repeated equivalent observations and numerical ties

The initial cache distinguished JSON integer1 from floating1.0, so the unit-weight anchor
was unintentionally measured several times during E/F. These observations remain in the
raw database with their original hashes and IDs; no unfavorable timing is discarded.
`semantic_configuration_hash` now groups numerically equivalent serialized settings and
future cache lookup treats1 and1.0 identically. Use these repeats to assess timing spread,
not as distinct control designs. The exact four-criterion Pareto computation retains raw
observations for traceability. Small timing or sub-micrometer tracking differences between
solver settings are not evidence of a meaningful controller improvement. Candidate A's
literal minimum can therefore be numerically tied in practical terms with a cheaper design.

## Screening findings

The fresh two-lap grip reference completed circle and oval with zero latency. Oval full-run
RMS lateral/heading/speed errors were0.00538274 m/0.0163324 rad/0.0148811 m/s. Backend mean/p95
were82.39/96.53 ms; total controller mean/p95 were95.62/112.88 ms. The50 ms nominal period is
therefore exceeded even before accounting for all preprocessing. Measured-latency reference
runs failed model validity after5.055 s on circle and2.000 s on oval, with64.71%/70.73% missed
releases. Grip utilization remained within the model; computational delay is not repaired by
the bounded tire law. Zero-latency oval front/rear peaks were0.5260/0.3657.

At20 Hz with5 substeps, N8/10/12/15/20/25 gave p95 solves37.50/41.29/60.11/71.79/144.99/188.93 ms.
All completed one lap. Lateral RMS increased from4.02 mm atN8 to6.39 mm atN25, while speed
RMS improved from0.0230 to0.01275 m/s. Longer coverage is thus a speed-versus-compute tradeoff,
not a universal tracking improvement. The one-lap N20 timing differs from the two-lap
reference; host timing variability and observation windows must remain visible.

Both compute and lateral-tracking selectors choseN8, so Stage C has one representative
horizon rather than duplicating it. Substeps1/2/3/5 gave maximum scaled one-step errors
0.62888/0.06553/0.006829/0.0005778 and p95 solves11.02/21.42/31.49/37.50 ms. One and two
substeps fail the predeclared accuracy gate despite good nominal closed-loop metrics.
Equal-step NumPy/CasADi parity remains within4.5e-16. Three substeps are justified at50 ms;
accuracy must be rechecked when the interval changes. At100 ms, three fail and four pass;
at66.667 ms and40 ms, three pass.

With one-second coverage, the accuracy-qualified10/15/20/25 Hz measured runs missed
2.44/4.88/62.86/80.77% of releases. The15 Hz full-run lateral RMS0.02520 m narrowly exceeded
the0.025 m envelope;20/25 Hz failed model validity. With0.4 s coverage instead, all four
measured runs passed, missed0.61/0.82/2.14/1.46%, and achieved9.94/14.89/19.55/24.62 Hz.
The10 Hz,N4,4-substep anchor had the strongest p95/period margin and lower full-run measured
lateral RMS than the faster short-horizon rates in this realization. This is direct evidence
that increasing nominal frequency can make synchronous behavior worse.

On that10 Hz,N4 anchor, doubling lateral/heading weights reduced full-run lateral RMS from
3.066 to2.770 mm but increased speed RMS from0.01932 to0.02575 m/s. Doubling speed weight
reduced speed RMS to0.01302 m/s with a small lateral increase to3.090 mm. HalvingR improved
speed RMS to0.01674 m/s and lateral RMS to3.004 mm. Dynamic-state andW multipliers had smaller
lateral effects;W changes produced nearly unchanged iteration counts. The combined lateral2
and speed2 candidate gave2.787 mm lateral and0.01737 m/s speed RMS. It remains a useful tradeoff,
even though the lateral-only winner anchors the terminal screen. Most mean iterations stayed
near9; changes of fractions of a millisecond among these settings are not established speedups.

Terminal scales0/.5/1/2 gave lateral RMS22.84/4.120/2.770/2.888 mm. Removing the terminal term
still passed the broad nominal envelope, but substantially degraded short-horizon lateral
control without a meaningful compute saving. The current scale1 is retained; there is no
terminal-equality or formal stability claim. This screen holds horizon fixed and does not
establish terminal robustness across every horizon.

IPOPT max40, looser1e-6 and stricter1e-8 tolerances all preserved nominal feasibility. Their
p95 timings were14.70/13.15/13.14 ms versus13.16 ms for the current options in this screen.
The warm-start flag gave13.01 ms; this marginal difference is inside observed repeat variability.
Limited-memory Hessians gave39.20 ms p95 and20.80 mean iterations versus about9 for the exact
Hessian. They are not a useful speed optimization here. Solver-setting lateral differences
are nanometer-scale and should not be interpreted as meaningful tracking gains. All retained
solutions still pass the independent1e-6 primal feasibility check.

Detailed per-configuration dimensions, timing distributions, effort, rate/slack/boundary
activity, failures and lap metrics are generated in NMPC_PARAMETER_STUDY_RESULTS.md and
experiments.csv. Rejected rows remain available, including the deliberately inaccurate
integration candidates and measured-latency failures. Exact Pareto membership can change
with timing noise or numerically negligible tracking differences; no global optimum is claimed.

## Selected candidates and confirmation

Candidate A is the literal minimum lateral-RMS screening result under the compute gate:
10 Hz,N4,4 substeps,lateral multiplier2, all other multipliers1, limited-memory Hessian.
Candidate B is the fastest quality-qualified screening result: the same controller with
exact Hessian and `ipopt.warm_start_init_point=yes`. Candidate C is B after measured two-lap
confirmation. Candidate D is the unchanged20 Hz,N20,5substep reference with all multipliers1.
All use shifted primal guesses. Full effective IPOPT options, MPC configuration and NLP
sizes are in selected_candidates.json. C has48 variables,30 equalities,168 inequalities.

A's screening lateral advantage over B is only about20 nanometers. It is a numerical tie
for engineering purposes, not a reason to pay its higher compute cost. A remains labeled
because the declared minimum rule is applied honestly; B/C is the practical selection.
The exact front has15nondominated observations, including long-horizon/speed and terminal/
heading tradeoffs. pareto.json lists every dominated and nondominated ID, plus separate
one-lap and two-lap measured deadline/lateral fronts. Do not read a two-axis projection as
if speed/heading objectives had been discarded.

Both A and B/C completed two-lap circle/oval runs and the combined circle disturbance
(ey=.08 m,epsi=-.04 rad) without solver or nominal physical-boundary failures. On the two-lap
measured oval, A gave6.878 mm lateral RMS,48.80 ms p95,1.23% misses and9.87 Hz achieved. B/C gave
4.147 mm,15.85 ms,zero misses and10.02 Hz achieved. The small effective-rate excess above10 Hz
comes from finite-window endpoint counting, not a faster release clock. D failed at2 s with
70.73% missed releases. These findings support C for the synchronous handoff, without
claiming repeat-run worst-case reliability.

C's measured heading/speed RMS were0.01645 rad/0.02940 m/s, peak lateral0.02577 m, peak
front/rear utilization0.6385/0.3699, max predicted slack9.09e-11 m, and max primal residual
6.26e-9. Its zero-latency two-lap run completed in32.425 s. At deterministic25/45/60 ms delays,
full-run lateral RMS was4.797/6.914/9.174 mm; each completed two laps with zero misses.
All delays remain below the100 ms period. Timing outliers still occur: an actual backend
call took261 ms in the45 ms-injected experiment. In injected mode physical delay is deliberately
fixed, so that wall-time outlier does not change its simulated deadline count. Never treat
the zero measured misses in a different run as a bound on future latency.

## Warm-start and cost profiling

C's ordinary screening first solve took23.89 ms/17 iterations; subsequent shifted solves
averaged12.67 ms/about9.03 iterations. D's first took216.54 ms/25 iterations and subsequent
solves averaged82.18 ms/about9.63 iterations. These changing-problem observations are not
controlled proof of warm-start benefit.

Eight alternating-order identical-problem cold/warm pairs on a fixed disturbed circle NLP
all succeeded. C: cold26.42 ms/18 iterations versus shifted warm24.76 ms/17 iterations, about6.3%
mean reduction, with warm faster in all eight pairs. D:189.22 versus190.14 ms,20 iterations
in both. Thus only a modest, case-specific C benefit is supported; there is no general or
dual-warm-start claim. The initial seed solves and per-pair objectives/residuals are retained.

C screening mean/p95 times in milliseconds: preview2.896/3.280, parameter packing.019/.024,
backend12.742/13.012, postprocessing.114/.134,total15.910/16.586. Warm preparation averages
.040 ms. The adapter includes backend plus extraction; do not add its time to backend time.
The measured confirmation total was17.664 ms mean/19.898 ms p95. Backend solving dominates,
then numeric geometry preview. CasADi's per-solve callback means for C included6.223 ms
Hessian and2.855 ms constraint Jacobian, versus43.029/19.659 ms for D. Full callback statistics
are in selected_timing_profiles.json and raw logs. Separate factorization/linear-system/
barrier internals were not instrumented; no invented decomposition of the remaining time.

## Proposed development defaults for Task006.3

These are recommendations for the next specification, not implemented behavior or safety
certification. Begin with frozen Candidate C at10 Hz and0.4 s coverage. Its measured minimum
nominal reserve was0.3511 s (mean0.3859 s); A fell to0.0480 s in a long-tail solve. Preserve
completion-time validity checks and do not assume every solve stays near p95.

- Minimum usable trajectory reserve:0.20 s, two nominal planner periods. Reject a newly
  completed plan with less reserve and monitor the currently active plan independently.
  C's observed261 ms backend outlier would consume too much of a0.4 s plan; asynchronous
  execution must handle such late plans rather than silently accepting stale trajectories.
- Interpolate at100 Hz: time-indexed linear state interpolation with continuous heading and
  unwrapped progress; initially use ZOH input segments. Check actuator/rate/domain constraints
  after feedback; interpolation details need tests before adoption.
- Actuation-time prediction: propagate the latest measured state through known held/applied
  input history to the intended handoff time. This is future work, not present in006.2.
- Codriver:100 Hz initial target; evaluate200 Hz later. Track the four lateral errors
  [ey,epsi,vy_error,r_error], using trajectory feedforward steering plus LQR/TVLQR feedback;
  retain separately specified bounded longitudinal tracking. Linearization and gain schedule
  about the actual planned trajectory need a006.3 specification.
- Handoff: accept only a newer, valid, sufficiently future trajectory, align it to current
  time and check state/input continuity; preserve actual actuator limits and1 rad/s rate.
- Planner failure: continue the already validated unexpired trajectory while reserve is
  sufficient; otherwise end the development run explicitly. A physical controlled-stop law
  requires an approved specification; do not invent one or blindly hold indefinitely.
- Exhaustion: no unbounded extrapolation. Raise/terminate the simulation before the usable
  trajectory ends if no replacement exists; log the reason and remaining reserve.
- Initial replan trigger: trajectory tracking error above.05 m lateral or.10 rad heading for
  two100 Hz samples, with hysteresis to be specified. These are provisional; current metrics
  are centerline errors, not measurements of a future trajectory tracker's error distribution.
- Initial tracker margin:0.08 m per side of the planned center-point corridor. This exceeds
  the observed.0569 m peak at60 ms fixed delay, but is not a robust bound, footprint allowance
  or validated tracker tube. Re-estimate it from006.3 tracking data and physical dimensions.

Still needed for006.3: target hardware/OS and timing budget, sensor/actuator delay and state
estimation interface, approved physical failure/stop behavior, footprint and uncertainty
allowances, and agreement on these development defaults. They do not block completion of006.2.

## Task006.4 workload export and limits

future_codriver_data.json preserves raw lateral/yaw ranges and a4-state/1-steering-input
model. C's one-lap raw vy/r ranges were.00746–.12415 m/s and.1225–1.9389 rad/s. Offline
Task005 controller-minus-NMPC steering differences had RMS.03653 rad and maximum.24809 rad;
these are workload proxies, not observed future codriver corrections. The existing complete
LQR/PI controller, including geometry/reference lookup, measured.634 ms mean/.723 ms p95 on
this host over300sampled states; reset was outside the timer. This is not a Pi measurement
or isolated feedback-matrix timing. Suggested comparison frequencies are100/200 Hz.

After Task006.3, implement Task006.4: small high-rate linear MPC codriver versus LQR/TVLQR.
Determine whether its tracking/constraint benefits justify its cost on Raspberry-Pi-class
hardware. No small MPC, asynchronous worker, trajectory buffer, compensation, TVLQR tracker
or event-triggered planner was implemented in006.2.

## Limitations and implementation deviations

The study is a finite, staged synthetic search with perfect states, frozen preview curvature,
center-point track bounds, and one host/session's timing. It does not establish worst-case
execution time, statistical reliability, a global optimum, formal stability or physical
vehicle performance. Prediction accuracy tests cover80one-step snapshots, not every possible
state or accumulated horizon/preview error. Finalists receive broader tests than screens.
Solver-only physical latency understates full end-to-end delay; OS/IPC/sensor/actuator costs
and future codriver costs remain unmeasured. No new model parameters or physics were fitted.

Permitted implementation changes were grouped cost/configuration plumbing, timing/export
instrumentation, exact fractional release validation, generalized audit rate limits and
study/report scripts. No runtime graph rebuild defect was found. The numeric-equivalence
cache correction is documented above. Library reference defaults remain unchanged.

## Reproduction commands

Run from the repository root with the existing virtual environment. Cached observations are
reused; set a unique `APEX_STUDY_REPLICATE` value for fresh measurements. The replay command
uses frozen selected settings rather than rerunning candidate selection. No exact wall-time
assertion is used in tests.

```sh
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export XDG_CACHE_HOME=/private/tmp/apex-cache
export MPLCONFIGDIR=/private/tmp/apex-matplotlib
.venv/bin/python scripts/run_mpc_parameter_study.py --stage A
# Run B, C, D, E, F and G in order with the same --stage option.
.venv/bin/python scripts/run_mpc_parameter_study.py --stage all
.venv/bin/python scripts/run_mpc_parameter_study.py --stage analyze
.venv/bin/python scripts/run_mpc_parameter_study.py --stage report
.venv/bin/python scripts/run_mpc_parameter_study.py --stage validate
.venv/bin/python scripts/run_mpc_parameter_study.py --stage warm
APEX_STUDY_REPLICATE=human-check-1 .venv/bin/python scripts/replay_mpc_candidate.py --candidate C --mode measured
.venv/bin/python scripts/audit_mpc_results.py --output results/mpc_parameter_study/runs
.venv/bin/python scripts/audit_mpc_parameter_study.py
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m json.tool results/mpc_parameter_study/selected_candidates.json
```

## Task 006.2.2 follow-up: unchanged candidates, verified thread behavior

The frozen C/D configurations were reused without modifying controller mathematics.
See [NMPC_MULTITHREADING_STUDY.md](NMPC_MULTITHREADING_STUDY.md) and its generated results.
Across 2,880 measured solves, requested Accelerate ceilings 1/2/4/8 produced about one
effective active core and no material p95 improvement. Recommend the verified native
single-thread baseline. C single-thread total p95 was 17.175 ms in snapshot replay and
17.744 ms in a fresh two-lap measured run (4.062 mm lateral RMS, zero misses).
The 4-ceiling closed-loop run retained one missed release; desktop timing is not bounded.
The original Task006.2 timings, candidates and source archive remain historical evidence.
Task006.3 is still next; no asynchronous or codriver implementation was added.
