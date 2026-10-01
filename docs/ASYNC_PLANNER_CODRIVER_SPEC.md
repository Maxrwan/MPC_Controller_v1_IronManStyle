# Task 006.3 — asynchronous NMPC planner and high-rate codriver

## Scope and ownership

This task changes control execution, not Candidate C tuning. The planner owns its nonlinear
optimization, warm start, nominal X/U and packet construction. The buffer owns the active
immutable packet, physical timestamps, interpolation and reserve. The codriver owns local
feedback and high-rate command generation. The independent NumPy plant owns actual state.
No component silently mutates another component's private state. The predictor clones
tracker state before forecasting. One event scheduler coordinates explicit transfers.

Candidate C remains 10 Hz, N=4, 0.4 s horizon, four RK 4 substeps, exact Hessian, shifted
primal guesses, IPOPT warm-start initialization and the selected Q/R/W/terminal cost.
One native Accelerate thread is configured before numerical imports in fresh experiment
workers. No new optimizer, OS-thread architecture, Task 006.4 MPC or Task 007 objective.

The only authorized planner-constraint change is a provisional **0.08 m per-side tracker
margin**. MPCConfig.tracker_margin defaults to zero for backward compatibility; asynchronous
cases explicitly use 0.08. The inequalities use width-minus-margin with the original slack
mechanism and penalties. Vehicle geometry and physical track widths are unchanged. This is
a synthetic design reserve, not an empirically certified invariant tube.

## Physical-time chronology

The simulator executes computations sequentially but emulates their physical chronology.
Preparing a plan immediately produces nominal data plus a measured computation duration.
The data are unavailable to the buffer until their scheduled physical completion. Meanwhile,
the NumPy plant advances in steps no greater than 5 ms, with codriver releases every 10 ms.
The codriver follows the old valid trajectory, not one frozen 10 Hz actuator command.

Planner releases remain on the fixed 100 ms grid. A busy planner records a missed release
and starts no overlapping solve. One urgent-request bit can request an early solve when idle.
Completed plans whose nominal start is still in the future wait until that start; they do
not cause future-state references to be used early. Late plans are interpolated and trimmed
at their actual acceptance time.

Coincident events process completed actuator work, planner completion/handoff, disturbance,
codriver release, then planner release. Zero-latency work completes at the same physical
timestamp without duplicate plant rows. Simulation event processing never advances time
backward or pauses moving physics for a runtime solve.

Measured-primary runs also model the measured codriver update delay, including command validation:
the prior command remains applied until that separate computation completes. Codriver
releases while its command computation is busy are counted separately. Deterministic
injected-planner experiments use zero codriver latency to isolate the planner-delay variable,
while still measuring codriver CPU/wall cost and recording computation-over-period events.
This is explicit in AsyncConfig.codriver_delay (None means measured, 0 means zero).

No OS-level concurrent execution or contention guarantee is claimed. Event ordering
reproduces the control chronology, not a hardware scheduler.

## Gated launch

The approved dynamic bicycle is invalid at standstill; no low-speed model or launch maneuver
is invented. Before physical time zero, the synthetic vehicle is **not released**:
the first plan and feedback gains are prepared, validated and installed. The first nominal
actuator command is prepositioned during this unrestricted prelaunch phase. Physical
simulation then starts from the documented 2 m/s rolling-launch state, with the same
cornering-reference vy/r convention used by the prior studies.

Initial planning and actuator prepositioning are not runtime deadlines. This assumption
must be replaced by a separately validated launch controller for a real stationary vehicle.
The synchronous historical architecture retains its original startup chronology; this
startup difference must accompany comparisons of whole-run RMS.

## Packet contract

TrajectoryPacket stores:

- plan_id; planner_release_time; planner_sample_time; intended_handoff_time;
  actual_completion_time;
- physical timestamps, states in canonical [vx,vy,r,e_psi,s_abs,e_y] order and controls
  [delta,a_cmd];
- source_sampled_state and predicted_handoff_state;
- solver_status, solve_duration and total_computation_duration;
- gain_times, 1×4 lateral gains, and nominal stage curvature preview;
- validity flag and validation reason;
- derived horizon_end_time and remaining_reserve_at_completion.

Arrays are copied and marked read-only. Dimensions, finite values, strictly increasing time,
gain schedule shape and nondecreasing unwrapped progress are checked. State heading is
unwrapped before interpolation. Six state channels interpolate linearly; nominal inputs use
zero-order hold over planner intervals. Gains use zero-order hold on their 10 ms schedule.
Progress is never wrapped for interpolation; only geometry queries wrap modulo track length.

No query may extend past the horizon. An exact terminal state can be queried from a packet
for validation, but the active buffer treats the horizon endpoint as exhausted. Trimming
inserts the correctly interpolated current state and retains only subsequent state nodes,
with consistent input, gain and curvature intervals. Numerical node comparisons use a
1 e-10 s tolerance so representational roundoff cannot select the previous ZOH interval.

## Codriver design

Lateral error is [e_y−e_y*, wrapped(e_psi−e_psi*), vy−vy*, r−r*].
The steering law is delta*=feedforward minus K(t) times this error.

TVLQR linearizes the approved smooth-grip symbolic bicycle around interpolated nominal
states and nominal controls. Its discrete map is RK 4 at 10 ms with two internal substeps.
The lateral subsystem is A:4×4, B:4×1. Speed, progress and acceleration are nominal scheduling
quantities rather than additional lateral optimization states. Curvature uses the planner's
existing stage preview with its same within-stage hold; it is not rebuilt by 40 redundant
geometry queries. The full six-state model still drives physical prediction and validation.

Weights reuse Task 005 DesignScales: Q_lateral=diag(100,100,4,1), R_lateral=25.
The terminal P is the discrete algebraic Riccati solution at the final nominal linearization.
A backwards finite-horizon Riccati recursion produces approximately 40 gains per packet.
This is planner-side preparation, included in total planner cost and availability delay.
There is no optimization or Riccati solve in the high-rate callback.

Longitudinal control is a_cmd* + 1.0×(vx*−vx), a proportional correction in inverse seconds.
No integral state is necessary in this first design. Playback disables both feedback
corrections, keeping the same planner, gains, packet, interpolation and physical limits.
Task 006.4 must reuse this longitudinal logic.

The runtime lateral dot product has four multiplications and three additions, plus error
subtractions and feedforward addition. One scalar speed-feedback multiplication is added.
There is one state interpolation (six channels), one control lookup and one gain lookup per
trajectory update; no model linearization at 100 Hz.

Commands obey the planner's physical actuator/grip/load-domain box bounds. Steering is
limited at the codriver period and again at actual application using elapsed physical time
since the previous application. This prevents timing jitter from producing an excessive
physical steering increment. Plant validity is checked using the independent physical model.

## Delay estimator and actuation-state prediction

RollingDelay is replaceable, initialized to 17 ms from Task 006.2.2, using the median of the
last ten completed planner durations, bounded to [0,0.30] seconds. In injected experiments,
the observed duration is the injected physical planner duration; in measured experiments,
it is total measured planner preparation, including prediction and gains.

At release, ActuationPredictor clones the tracker and propagates the six-state approved
symbolic bicycle under the active trajectory/feedback at the codriver grid, using RK 4
substeps no greater than 5 ms and geometry refreshed along predicted progress. It begins
from the actually applied command. The forecast assumes ideal codriver execution timing;
measured codriver delay is not recursively predicted, and an already-in-flight command
is not explicitly replayed by the forecast. Future feedback starts on the next codriver grid.
This approximation is
observable in the logged state-prediction error.

The new NMPC starts from the forecast state at release+estimated delay, with the forecast
prior control. RK 4 evaluation stages are checked against speed and Frenet-domain bounds.
No nominal trajectory is extrapolated through exhaustion. A forecast requiring
an unavailable trajectory fails explicitly, leaving current valid control in place.

Logs retain predicted/actual completion, delay-estimation error, sampled and forecast states,
actual state at completion and all six prediction-error components. Comparing forecast state
at intended handoff with state at actual completion includes delay-estimation error; aligned
handoff mismatch is logged separately.

## Acceptance, continuity and reserve

The existing MPC adapter independently validates solver output, NLP residuals and bounds.
A prepared packet requires successful validated output and finite gains. Buffer insertion
requires a newer ID, availability, monotonic timestamps and at least 50 ms remaining reserve.
At handoff, the nominal state/control also undergo model validation.

Provisional per-component handoff mismatch limits are:
vx 0.5 m/s, vy 0.5 m/s, r 1 rad/s, heading 0.20 rad, progress 0.75 m, lateral 0.15 m.
These are explicit synthetic rejection thresholds, not proven safety bounds. All mismatch
components and nominal input jumps are logged. No aggressive blending hides mismatch.
High-rate feedback and physical steering slew limits control the applied command transition.

Reserve is horizon_end−physical_time, clipped to zero for reporting:
healthy ≥0.20 s; warning [0.05,0.20) s; critical (0,0.05) s; exhausted ≤0.
Reserve is logged at plant events and planner completions. A new plan with less than 50 ms
reserve is rejected. The codriver may use an already-active critical trajectory until its
exact endpoint; it never extends it beyond that endpoint.

## Failure, exhaustion and urgent replanning

A failed solve, failed forecast or invalid gain construction produces no new active packet.
The existing valid packet and codriver remain active. Future fixed/urgent replans can retry.

Exhaustion transitions to the existing Task 005 centerline LQR/PI only inside its documented
1–3 m/s and in-track domain. Its commands are still checked against physical limits. Outside
that domain, the development run terminates with a logged reason. Once entered, fallback
is latched for the run; late planner results cannot silently restore trajectory tracking.
Re-entry/recovery arbitration is deferred. Completion under fallback is therefore reported
separately from successful continuous operation of the planned architecture.

An optional urgent request triggers after two consecutive codriver samples with lateral
trajectory error >0.05 m or heading trajectory error >0.10 rad. One pending bit is retained
while busy, with no queue or overlapping optimizer. Persistent error does not create one
request per sample; a new threshold episode requires the error to clear first.

## Experiments and accounting

The primary comparison is synchronous Candidate C measured latency, asynchronous nominal
playback, and asynchronous TVLQR at 2 m/s on the oval for two laps. The synchronous case
preserves the prior backend-only latency semantics; asynchronous measured latency includes
the full planner preparation pipeline. This asymmetry is disclosed rather than silently
changing historical behavior.

Injected planner delays are 0,25,60,100,150,250 and 450 ms. There are paired synchronous runs,
an isolated 150 ms event surrounded by 25 ms solves, an isolated failed solve, and the approved
synthetic combined offset (0.08 m lateral,−0.04 rad heading) applied at 5 s with both feedback
and playback. No failing case is erased or relabeled as successful trajectory tracking.

Computational accounting separates:
planner NLP/preview/prediction/gain preparation and aggregate CPU;
codriver interpolation, feedback, command validation and aggregate CPU (kernel also separate);
their summed average CPU-core-seconds per physical second.
Simulator integration, logging and periodic plant diagnostics are outside
this algorithm-work estimate; the codriver command-validity check is included. Deployment dispatch/transport/validation overhead and actual
OS contention require later measurements. Construction and startup are separate.

The measured runtime tracker is intentionally small, but no desktop timing sample guarantees
a hard 100 Hz deadline. No Raspberry Pi utilization is inferred from M 1 values.

## Task 006.4 replacement boundary

Replace only lateral correction, preserving nominal X/U, physical timestamps, buffer,
longitudinal proportional correction, rate/application limits, replan/fallback policies and
experiment definitions. Start from the existing four-state lateral A/B linearization at
100 Hz and one steering correction input. Preserve the 10 ms end-to-end codriver deadline;
measure a new controller's full cost rather than assigning it the TVLQR dot-product cost.
No small linear MPC is implemented in Task 006.3.

## Final experiment findings

The 21 final cases are tabulated in ASYNC_PLANNER_CODRIVER_RESULTS.md and machine-readable
results/asynchronous_planner_tracker/experiments.csv. On the measured two-lap oval,
synchronous Candidate C lateral RMS was 5.135 mm, asynchronous nominal playback 4.583 mm,
and TVLQR 3.867 mm. TVLQR heading RMS 0.01808 rad, speed RMS 0.03017 m/s, laps 16.250/16.174 s.
No measured-primary boundary violations, solver failures, fallback or planner/codriver misses.
These are individual host runs, not statistically replicated timing comparisons.

Constant planner delays through 150 ms completed with continuous planned tracking. At 150 ms,
162 planner releases were skipped while the codriver maintained its 100 Hz simulated releases.
At 250 ms the first delay underestimate left only 0.167 s in the replacement at completion;
the next 0.25 s forecast exceeded that active horizon. Exhaustion occurred at 0.517 s.
At 450 ms the startup trajectory expired at 0.4 s before the first replacement completed.
Both finished under latched baseline fallback. This is an architectural limit of the frozen
0.4 s horizon, release policy and forecast reserve, not successful unlimited latency tolerance.

One 150 ms spike among 25 ms solves consumed reserve down to 0.175 s, missed one planner release,
missed no codriver release and recovered without fallback. One failed plan similarly retained
control and recovered. The spike was at one phase of this oval, not an exhaustive phase sweep.
The 0.08 m/−0.04 rad perturbation requested one urgent replan in both feedback and playback.
Feedback whole-run lateral RMS 7.232 mm versus 7.904 mm playback is a modest benefit; both returned
to the explicitly reported centerline tolerance in 0.45 s. A much faster apparent trajectory-error
recovery is partly a replanned-reference reset and must not be sold as local feedback alone.

Measured TVLQR trajectory-error lateral RMS/p 95/max were 0.450/0.510/6.389 mm.
The imposed disturbance reached 79.996 mm, nearly all of the provisional 80 mm margin.
The margin is conservative in the nominal oval and has essentially no excess for this imposed
jump. It is not a robust-invariant or real-vehicle safety certificate.

Planner full preparation mean/p 95/max 40.877/44.593/74.282 ms includes approximately 8.931 ms
forecast and 5.574 ms gain building on average. Solver mean 21.046 ms and preview 4.623 ms are
reported separately; Candidate C was not retuned to offset these costs. Codriver full update
mean/p 50/p 95/p 99/max 1.040/0.969/1.187/1.337/7.058 ms includes command validation.
The interpolation/feedback kernel mean is 0.0635 ms. Algorithm CPU demand is 0.4071 planner
plus 0.1037 codriver =0.5108 core-seconds per physical second. No target-hardware inference.

The measured-primary callbacks had no 10 ms overruns, but some injected experiments did:
3 isolated-failure callbacks,1 playback-disturbance callback, and 34/8 callbacks in 250/450 ms
fallback runs. Their zero simulated codriver delay makes physical miss counts remain zero.
Fallback costs include the existing baseline controller. A production fallback also requires
full deadline validation; these deterministic studies do not provide it.

Measured-primary reserve min/mean/p 95 was 0.25546/0.34904/0.39442 s, with no time below 0.20 s.
All 13 asynchronous cases stayed in track and within tire/actuator domains. Maximum combined
front/rear utilization across them was 0.499994/0.398708. High-delay synchronous failures and
boundary excursions are retained in the comparison, with unequal run durations clearly marked.

## Evidence revisions

Exploratory runs before timestamp-boundary and full-validation timing fixes are archived under
results/asynchronous_planner_tracker_preliminary and are not pooled. The final suite's 250 ms
save initially failed on a NumPy boolean; only the event JSON writer changed before rerunning
that case and the remaining conditions. The partial save is retained. Source hashes record both
writer versions. A subsequent reviewed exception-path fix discards a nominal packet when gain
preparation fails; its regression test passes. No final experiment encountered gain failure
(the sole preparation failure was an unavailable forecast), so successful benchmark behavior
is unchanged. Original benchmark sources are retained for verification.

Whole-run RMS uses physical-time weighting: asynchronous logs use left-state quadrature with
steps no greater than 5 ms; historical synchronous summaries use trapezoidal quadrature. Startup,
margin and latency-accounting differences also limit claims of a strictly isolated comparison.

## Task 006.4 comparison outcome

TVLQR remains the recommended codriver. The optional local-MPC tracker changes only lateral
correction, preserves longitudinal P and validates the same actuator limits. Its independent
forecast clone is used by an optional predictor hook. An optional postvalidation finalization
hook replaces a failed/late local QP with TVLQR for that update, retaining elapsed delay and
misses; global fallback is unchanged. See LINEAR_MPC_CODRIVER_STUDY.md and ADR-122–130.
Task 007 remains deferred to the pre-Task-007 review gate.
