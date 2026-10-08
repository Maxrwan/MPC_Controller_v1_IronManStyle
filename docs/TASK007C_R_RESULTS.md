# Task007C-R — reproducibility and timing-causality results

Completed 2026-10-05. **Gate: YES — scientifically safe to resume the original C1–C4 intent.**
This is a reproducibility decision, not physical safety approval. C1–C4 were not executed.
All paths below are relative to the repository unless stated otherwise. See
[TASK007C_R_REPRODUCIBILITY.md](TASK007C_R_REPRODUCIBILITY.md) for methods and
[TASK007C_R_REPRODUCTION.md](TASK007C_R_REPRODUCTION.md) for executable commands.

## 1. Task Completed

Task007C-R diagnoses the existing high-demand E/F behavior with frozen mathematics. Task007C
C1–C4 have not run. No controller tuning or formulation improvement is included.

## 2. Historical Artifact Audit

The initial preservation check verified 675 Task007B and 293 Task007C artifacts. Historical E/F/C
release/completion/command-application events, preparation/solver/preview/gain timing, skipped
releases, handoffs, states, active packets, iterations/status, objective components, predictions,
reference previews and actuator commands exist. Exact old guesses, previous-solution vectors,
complete numeric NLP requests and duals do not. New equivalent requests were captured during
exact physical-history replay. Unapplied in-flight work at termination has no invented delay.
`results/task007cr/historical_audit.json` gives the per-file hashes and missing-data inventory.

## 3. Configuration / Hash Audit

All61 study-run fixture bytes, Candidate C configuration, native SINGLE control, runtime hashes and
E/F physical simulation configurations match the original cases. Only the optional timing hook
changes existing runtime source; one schedule module was added. Q=diag(4,4,1,200,200),
R=diag(25,1), W=diag(1,0.1), slack weights 1e4/1e5, N=4, dt=0.1 s and four RK4 substeps remain
frozen, as do terminal-P generation, references, plant, tire law, TVLQR and solver options.
`configuration_audit.json` records exact hashes, captured graphs/options and vehicle parameters.
Original Task007C E/F and repeat anchors also match their Task007B configurations, sources and
fixtures. The synthetic vehicle YAML hash and all captured vehicle values match the retained baseline.

The previously disclosed early-B0 loader hash differs (old `bcf095bd...`, current `d147a6eb...`).
Its exact old source body is unavailable. Current lookup reproduces **all 1,765 retained old B0
previews/progress arrays exactly** (maximum difference 0). This is behavioral evidence, not a
reconstruction of the missing source. Primary original E/F/C loader hashes match the frozen code.

## 4. Randomness Audit

The active plant/controller/preview/buffer/TVLQR path contains no RNG draws, randomized noise,
initialization or shuffled ordering. Python and NumPy seeds are 0; PYTHONHASHSEED=0 in fresh
workers. The base simulator's stochastic-seed comment describes future work. Search evidence is
`randomness_search.txt`. Wall-clock timing remains variable despite fixed seeds.

## 5. Timing Semantics

`tau_ready[k]` is planner release-to-completion/availability delay, copied from logged
`physical_delay`; actual accepted vehicle handoff may be later because the unchanged buffer
checks timestamps and validity. Handoff events are verified separately. `tau_codriver[j]` is
release-to-actuator-command availability, copied from `controls.csv:physical_latency` with
round-trip float parsing. Reconstructed differences match completion−release/application−release
within 1e-12 s. Full planner preparation, IPOPT time, ready delay and accepted handoff are distinct.

Index only launched computations; skipped nominal releases consume no trace entry. Startup is
planned while gated and consumes no replay entry. Actual computation always executes and is timed.
Only diagnostic availability is imposed. Physics continues, and the 100 Hz TVLQR follows the
active valid trajectory while planning is pending. Actuator commands remain held during codriver
latency. Normal measured timing remains the default. Missing trace entries cause an explicit stop.

## 6. Original Latency History Availability

| Case | Nonstartup planner entries | Applied codriver entries | Historical end [s] |
|---|---:|---:|---:|
| E | 323 | 3221 | 32.21 |
| F | 315 | 3158 | 31.58 |
| C | 941 | 9420 | 94.195833333 |

`trace_e.json`, `trace_f.json`, `trace_c.json` preserve these exact logged delays. E/F same-history
replays complete their original laps. No padding, cycling or extrapolation is used for other runs.

## 7. Fixed-Latency Repetition Results

Planner 35 ms / codriver 1 ms: ten E, ten F, two C runs. All 45 E pairs, 45 F pairs and the C pair
have **maximum and RMS difference 0**, with no beyond-tolerance first divergence in states,
controls, complete predictions, warm starts, numeric inputs, objectives, iterations, tracking/
adaptation channels and aggregate metrics. See `repeatability.json` for all fields and tolerances.

| Case | Identical lap [s] | Max slack [m] | Min clearance [m] |
|---|---:|---:|---:|
| E | 31.147662089 | 0.077245976 | 0.007662292 |
| F | 33.503139641 | 0.100332113 | −0.019712313 |
| C | 31.267129230 | See raw outcomes | See raw outcomes |

**Reproducibility is not safety:** fixed-history F crosses the physical boundary; E has material
slack and very low clearance. No run was retuned or discarded.

## 8. Recorded-Latency Replay Results

Five E and five F replays agree exactly pairwise. Each reproduces the original Task007B states,
actuator commands, full optimized predictions, slacks, active references and accepted handoffs
exactly, with identical physical sample grids. Thus the specific rejected behavior reappears.

| Outcome | E original/replay | F original/replay |
|---|---:|---:|
| Lap [s] | 32.206657233 | 31.576226702 |
| Sweeper planned heading TV [rad] | 6.328775414 | 0.278812036 |
| Sweeper steering-rate-limit time [s] | 2.35 | 0 |
| Maximum predicted slack [m] | 9.09e-11 | 0.027471299 |
| Minimum physical clearance [m] | 0.134604922 | 0.060095466 |

C's one-lap replay also matches the original first-lap prefix exactly. Its original covers three
laps, so whole-run TV/saturation aggregates across those unequal durations are not equivalence tests.

## 9. Cross-Latency Replay Results

E under F's delay history and F under E's history both stop at codriver trace exhaustion, at
launch indices 3158 and 3221 respectively. Retain supported prefixes; no completed lap time is
assigned. These counterfactuals cannot alone decide whether pathology follows configuration or
history; configuration and trajectory feedback interact. The two same-history cells are R2.

| Supported prefix | End progress [m] | Sweeper TV [rad] | Max slack [m] | Min clearance [m] |
|---|---:|---:|---:|---:|
| E under F history | 153.852 | 6.05755 | 0.031305 | 0.055730 |
| F under E history | 148.580 | 5.34040 | 0.139694 | −0.062492 |

Both prefixes cover the sweeper and technical sectors. F under E history crosses the physical
boundary. The outcome does not simply transfer unchanged with the latency trace; controller
configuration and history jointly influence the trajectory.

## 10. Fresh Measured Repeat Results

Ten E and ten F runs executed sequentially in fresh SINGLE workers, without concurrent tests,
analysis or benchmarks. All completed a lap. All raw runs are retained, including one F boundary
crossing. Timing outliers and planner/codriver misses remain in their original logs.

## 11. Outcome Distributions

`results/task007cr/DISTRIBUTIONS.md`, `outcome_distributions.json` and `outcomes.csv` report
min/p25/median/p75/p95/max for every requested outcome, run-wise timing and pooled individual
nonstartup solver/availability/codriver calls and iterations.

| Metric (min / median / max) | E | F |
|---|---|---|
| Sweeper heading TV [rad] | 0.278 / 0.282 / 5.987 | 0.276 / 0.283 / 4.988 |
| Lap [s] | 30.122 / 30.554 / 31.572 | 30.282 / 30.500 / 33.341 |
| Predicted slack [m] | Effectively zero throughout | Effectively zero to 0.11976 |
| Minimum clearance [m] | 0.10532 to 0.16419 | −0.03976 to 0.14042 |

Separate indicators: high sweeper TV (>3 rad) occurs in 2/10 E and 2/10 F; material slack
(>1e-6 m) in 0/10 E and 5/10 F; physical boundary crossing in 0/10 E and 1/10 F. Thresholds and
±20% sensitivity counts are disclosed individually. No combined bad-run score is used.

## 12. First-Divergence Analysis

Original-history E replay versus measured `r4_e_01` (minimum measured E sweeper TV):

| First observed difference | Physical time [s] |
|---|---:|
| Codriver delay metadata / availability timestamp differs at release | 0 |
| Earliest differing command-availability time (initial command unchanged) | 0.000922458 |
| First nontrivial command-availability split | 0.010857625 |
| Common sampled plant state and requested codriver control | 0.02 |
| Planner source/forecast state, initial guess, numeric input, optimized output | 0.1 |
| First differing accepted handoff (original timestamp) | 0.131935542 |
| Sampled active lateral reference | 0.14 |
| Previous optimized solution used for the next warm start | 0.2 |

The initial guess changes at 0.1 s because it embeds the changed initial state even while the
previous stored solution is still the same. Startup NLP solutions match. This orders physical
history differences before different optimizer requests; it does not identify different solver
outputs for an identical request. `first_divergence.json` and the CSV preserve tolerances,
first progress and per-channel maxima/RMS. Common timestamps are used without interpolation;
first observed physical-state divergence is resolution-limited.

## 13. Exact NLP Snapshot Format

Each run saves `nlp_model.json` (serialized CasADi f/g graph, variable/constraint bounds, all
vehicle/config values, Q/R/W, solver options, backend/reference identity) and `nlp_snapshots.json`
(per-call x0/reference/terminal-P parameter vector, exact decision guess, previous optimized
solution, returned solution/status/statistics). `nlp_snapshot_index.json` decodes release state,
actual applied release command, forecast optimizer state/command, preview curvatures/widths/
references and terminal P. The forecast previous command in p[6:8] is explicitly distinguished
from the actual applied command at release. Backend audit records IPOPT/runtime identity.

Nine selection roles span before oscillation, first input divergence, strong sector predictions,
maximum slack and matched-progress lower-TV measured runs. E before/first-divergence refer to the
same request: **nine roles, eight unique requests**, each role receives twenty repeated solves.
E's max-slack request has negligible slack and is a negative control; F has material slack.

## 14. Exact NLP Repeatability

All 180 repeated solves are identical in optimized vectors, objective and iteration count within
each selected request. Every reconstructed solution equals its captured solution exactly; each
fresh-backend reconstruction also agrees exactly. Maximum primal residual is 8.258e-8 and raw
unscaled stationarity infinity norm is 9.216e-6. IPOPT primal/dual diagnostics and multipliers
are retained separately. See `nlp_replay.json` and `numerical_summary.json`.

## 15. Warm-Start Sensitivity

45 deterministic variants (zero controls/tiled state, production cold start, ±1e-4 rad steering
guess changes, shifted previous solution from the selected lower-TV run) all solve successfully.
Largest full-vector change is 4.017e-6, first steering change 2.128e-8 rad and first acceleration
change 3.705e-6 m/s². Maximum objective change is 1.567e-5. No qualitatively different local
solution branch was found in this probe set. Production warm-start policy was not changed.

## 16. State-Perturbation Sensitivity

One-channel ± perturbations use the actual early E optimizer-state difference: vx 3.633e-7 m/s,
vy 4.036e-6 m/s, r 1.790e-5 rad/s, epsi 7.410e-7 rad, ey 1.368e-7 m. Across 90 successful solves,
maximum full-vector change is 5.330e-5, first-steering change 9.880e-7 rad and first-acceleration
change 5.330e-5 m/s². Maximum objective change is 0.010739 (different physical problems).
These sampled ± probes show small, approximately sign-reversing local changes, not different
branches. They do not prove global smoothness or establish a pure-state closed-loop causal effect.

## 17. Timing-Perturbation Sensitivity

Selected E launch index99 / plan100 at t=10 s, physical source progress43.337091502 m.
Only that planner ready delay changes. All other planner entries and all codriver entries match
exactly; selected-update parameters/solution remain identical. State differences are **zero before
the earliest changed ready event**. The next optimizer input changes at10.1 s in all six probes.
Common-time downstream lateral-state differences reach0.281–0.492 m, despite only one changed delay.

| Delay change [ms] | Sweeper TV [rad] | Completed lap [s] | Final progress [m] |
|---:|---:|---:|---:|
| −5 | 6.029222 | Trace exhausted | 150.618 |
| −2 | 6.028402 | Trace exhausted | 151.648 |
| −1 | 5.685726 | 31.427644329 | 154.726 |
| 0 | 6.328775 | 32.206657233 | 154.731 |
| +1 | 6.331663 | 31.746225688 | 154.733 |
| +2 | 6.331654 | Trace exhausted | 151.680 |
| +5 | 6.331688 | 32.161077088 | 154.758 |

All prefixes cover the full sweeper. None removes the high-variation event. Minimum clearance
0.134604922 m and maximum |beta|0.393669121 rad remain identical because their extrema precede
the intervention; predicted slack stays negligible. Incomplete runs stop at32.21 s with no
fabricated tail. Whole-prefix steering TV has unequal coverage and is labeled accordingly.

The unchanged future-timestamp policy clamps negative-perturbation handoffs to10.030345167 s;
baseline handoff is10.030689416 s. Thus ready-delay change is not necessarily the same handoff
change. The rolling delay estimate also changes subsequent optimizer forecasts. Some earliest
small state differences precede a different sampled command because availability events partition
the frozen RK4 integrator. The causal claim is therefore **one availability-history intervention
changes this implemented closed loop**, not an isolated continuous-time actuator effect.
`timing_sensitivity.json` retains per-channel differences and first observed times.

## 18. Solver Determinism Audit

Python3.12.14, CasADi3.8.1, IPOPT3.14.19, macOS26.5.1 arm64. Current loaded libraries identify
IPOPT/MUMPS and Accelerate BLAS/LAPACK; the retained same-version installed-backend banner names
MUMPS5.8.2. Native Accelerate SINGLE was accepted. Separate100-solve audit CPU/wall=0.999857,
maximum observed process threads=1 at20 ms polling. Polling cannot exclude shorter transients.
Environment values alone and empty threadpoolctl are not used as proof. Sandbox CPU-brand query
returned no identifier; no chip model is invented. `backend_audit.json` retains exact details.

## 19. E Case Diagnosis

The original sweeper oscillation is exactly reproducible when physical availability history is
restored. Fresh timing often suppresses that specific sector behavior but does not make the
whole lap benign. Close TVLQR tracking coexists with varying APEX trajectories. The tested exact
solver inputs are deterministic and the sampled warm/state probes do not reveal alternate branches.

## 20. F Case Diagnosis

Original slack/margin behavior reproduces exactly; fresh timing varies slack from negligible to
0.11976 m and can produce a physical boundary crossing. Original maximum slack occurs around
progress13.584 m, before the hairpin, rather than in E's sweeper. F also has variable later-sector
oscillation. Identical-input nondeterminism is not supported by the selected NLP probes.

## 21. Physical-Time Causality Findings

Restoring full physical history restores the old trajectory exactly. Different measured delay
histories first alter command availability, then plant/controller inputs, then optimized outputs.
A new request is not an identical-input solver test. Physics is never paused during availability
delays. The unchanged event scheduler also partitions RK4 integration at availability events;
this study does not independently isolate all integration-partition effects from command timing.

## 22. Failure-Source Classification

**A: highly reproducible under fixed timing, plus B: latency-history sensitive** are directly
supported. C (identical-input solver nondeterminism), D (alternate warm-start branches), and F
(primary configuration mismatch) are not supported by these tests. State history mediates the
closed loop, but the local state probes do not independently establish classification E as a
pure-state closed-loop intervention. Do not call the behavior chaos or claim a global theorem.

## 23. Evidence For / Against Solver Nondeterminism

Against: zero differences across fixed/replayed histories and180 exact request repeats, including
fresh solver reconstruction. For: no observed evidence in this environment/probe set. This does
not exclude nondeterminism in an untested backend, machine, state or threading configuration.

## 24. Evidence For / Against Multiple Local Solutions

All45 alternative initializations converge very close to the captured solution with small
residuals. This finds no competing branch at the eight unique sampled requests; it does not prove
uniqueness of the nonconvex NLP everywhere. All variants, not just favorable ones, are retained.

## 25. Evidence For / Against Timing Sensitivity

For: exact recovery of E/F original failures under original delay histories and broad measured
outcome distributions with unchanged mathematics. R3 supported prefixes provide additional
counterfactual evidence but incomplete lap coverage. R7 independently changes one availability delay, preserves the pre-intervention state history,
and changes subsequent trajectories without changing the selected NLP solution.

## 26. Evidence For / Against State Sensitivity

Early optimizer-state changes are tiny and single-NLP effects remain small under the explicit
probes. Full histories later diverge substantially as timing, state, references and warm starts
interact. This supports history dependence without attributing the whole closed-loop difference
to a single initial-state perturbation or claiming chaos.

## 27. Required Figures

All under `results/task007cr/`:

1. `task007cr_fixed_latency_repeat_overlay.png`
2. `task007cr_original_latency_replay.png`
3. `task007cr_measured_repeat_distribution.png`
4. `task007cr_first_divergence_timeline.png`
5. `task007cr_exact_nlp_repeatability.png`
6. `task007cr_warmstart_sensitivity.png`
7. `task007cr_state_sensitivity.png`
8. `task007cr_timing_sensitivity.png`

## 28. Telemetry Overlays

`task007cr_telemetry_overlay_e.png` and `task007cr_telemetry_overlay_f.png` show all ten measured
runs against shared progress axes: speed, ey, epsi, vy, beta, yaw rate, steering/rate, front/rear
utilization, predicted slack, Planning→APEX deviation, APEX→vehicle error, planner delay and
iterations. These overlays reveal sector-specific separation rather than only lap-level summaries.

## 29. Computational Cost of Diagnostic Instrumentation

`instrumentation_cost.json` reports measured copy overhead distributions and per-run totals.
E median copy cost10.58 µs, p9514.46 µs; total2.924–3.897 ms/run; copies account for0.0362% of
summed planner time. F median10.29 µs, p9514.08 µs; copies account for0.0357% of
summed planner time. Context/bookkeeping/cache effects are not independently isolated, so these
are not a complete uninstrumented counterfactual. Capture cost remains inside normal measured
planner availability. JSON/graph serialization occurs after physical simulation. Offline exact
solve times are retained but are not uncontended latency benchmarks.

## 30. Regression Tests

**518 tests passed in785.22 s** (`results/task007cr/regression.log`). The prior focused
timing/chronology/snapshot/protection suite passed23 tests. Default measured timer dispatch
coverage is included in full regression. Scoped Ruff checks also pass.
Mathematics remains frozen; tests exercise real plant behavior and actual NLP reconstruction.
The independent event-log audit passed all62 retained asynchronous cases (61 study runs plus
one smoke case): progressing physics, held commands, nonoverlapping solves, timestamp-valid
references, actual application times, actuator rate limits and release accounting.

## 31. Generated Artifacts

`results/task007cr/`: raw per-run states/controls/events/predictions/packets, exact snapshots,
telemetry, analysis, distributions, pairwise comparisons, divergence timeline, numerical probes,
timing probes, backend/config/randomness audit, figures and final provenance/source archive.
Sources live in `scripts/task007cr/`, opt-in timing support in `src/apex/simulation/`, tests in
`tests/unit/`; methods/reproduction/results/handoff/decision/roadmap documents accompany them.

## 32. Known Limitations

Synthetic fixtures/vehicle are not measured APEX data. Ten measured runs per configuration are
descriptive, not population guarantees. Cross histories and some timing probes can exhaust their
finite traces. Old exact guesses/duals and early-B0 loader source are unavailable. One fixed delay,
one timing-intervention event, eight unique NLP requests and one Mac backend were studied.
Instrumentation can affect measured history. Event-driven RK4 partition effects remain coupled.
No long-horizon pure-state intervention, global uniqueness proof or chaos claim is made.

## 33. Architecture Deviations

No frozen controller/plant/TVLQR/formulation policy changes. DiagnosticTiming is an explicit
optional schedule in AsyncRunner; default measured behavior is unchanged. Exact capture wraps
the solver only in the study script. Optimization remains independent of the physical plant and
the solver interface. No ROS/RL dependencies, threading changes or new control equations.

## 34. Is Original Task 007C Now Scientifically Safe to Resume?

**YES**, for scientific continuation of the original formulation experiments. Original rejected
E/F histories now reproduce sample-for-sample; fixed timing is deterministic; exact solver inputs
are repeatable; all518 regression tests and62 asynchronous chronology audits pass. Timing-history
sensitivity is demonstrated directly, and sampled warm/state probes find no alternate local branch.

This does not accept E/F for physical operation. Resume with matched fixed/replayed physical
histories to isolate formulation effects, then serialized measured repetitions to assess the
implemented system. Preserve C1–C4's scientific intent, rather than tuning against a convenient
measured realization. Finite trace censoring and the integrator/timing coupling remain explicit.

## 35. Recommended Next Step

Do not execute C1–C4 in Task007C-R. The gate passes: resume the original C1–C4
scientific intent with controlled timing comparisons plus serialized measured repeats. Preserve
failure cases and compare complete outcome distributions; a faster/smoother single run cannot
alone establish a formulation improvement. Retain always-active APEX and fixed TVLQR.

## 36. Reproduction Commands

See [TASK007C_R_REPRODUCTION.md](TASK007C_R_REPRODUCTION.md). Run serialized fixed/replay/cross/
measured campaigns first, offline analysis next, then exact NLP and one-event timing probes.
Never overlap numerical work with measured-latency experiments. Existing cases are retained;
use the single-run CLI with a new case name/output folder for an additional run.
