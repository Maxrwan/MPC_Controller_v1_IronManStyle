# Task 006.4 — small lateral MPC versus TVLQR

## Preregistered scope and selection gate

Only the four-state lateral correction changes. Candidate C, physical model, packet/buffer,
planner chronology, longitudinal P law, margins and global fallback stay frozen. Task 007 is
not implemented. The Task 006.3 handoff is archived in TASK006_3_HANDOFF.md.

Before examining results, adoption requires no new boundary/model failures and at least one
material benefit relative to fresh TVLQR: (a) >=20% and >=0.2 mm reduction in trajectory RMS,
(b) >=20% and >=2 mm reduction in peak lateral trajectory error, (c) >=20% reduction in steering
total variation with no >10% degradation in peak tracking error, or (d) >=20% and >=0.1 s
improvement in disturbance recovery. A single favorable nominal metric is insufficient:
check disturbance and constraint stress for regressions. Full p95 callback should be <4 ms
(comfortable 100 Hz margin), with local failure/overrun replacement <0.1% in primary runs.
These are engineering screening thresholds for synthetic data, not statistical significance.

Horizon screening uses N=3,5,8,10,15 (30–150 ms). Prefer the smallest horizon within 5% of the
best trajectory RMS, subject to constraint behavior and cost. Study correction-rate penalties
W=0,0.5,1,2 and frozen versus varying Jacobians on a small subset, not a broad search.
Warm-start and cold-start timing use identical fixed inputs. No result is deleted for losing.

## Fair comparison and timing

Phase A supplies both trackers the same frozen Task 006.3 packet X/U/K, release times and
availability durations. High-level urgent replanning cannot alter a frozen replay. The normal
handoff validation and reserve policy still apply. Phase B uses the actual frozen planner
and each tracker's state. All timing experiments run in fresh native-SINGLE workers,
sequentially, without concurrent tests or plot generation.

The completed measurements are in LINEAR_MPC_CODRIVER_RESULTS.md; interpretation follows below.

## Model, objective and dimensions

The local state is [e_y−e_y*, wrapped(e_psi−e_psi*), vy−vy*, r−r*]. Nominal speed,
progress and acceleration schedule the model; they are not additional optimization variables.
The approved six-state smooth-grip RK4 map uses dt=0.01 s and two substeps. Its Jacobians
are extracted into A4×4/B4×1. The affine defect is F(x*,u*)−x*_next, restricted to the four
lateral channels, including wrapped heading. This matters because interpolated nominal states
do not exactly satisfy the 10 ms dynamics. LTI freezes the first Jacobians over the horizon;
LTV evaluates them at each nominal point. Both retain the time-varying nominal affine defect.

The condensed variable is N scalar steering corrections. State recursion eliminates all
4N future error states. Cost uses Q=diag(100,100,4,1), R=25 and the last local A/B DARE
terminal P. Intermediate states e1…e(N−1) have Q; terminal eN has P. Omitting the constant
e0 term changes no optimizer. Optional W penalizes consecutive corrective-steering changes;
its first difference is relative to previous actual steering minus current nominal steering.
Absolute actual-steering slew is independently enforced, including feedforward changes.

There are N decisions, zero equalities, 2N two-sided rows (4N scalar inequalities).
H is dense N×N with N(N+1)/2 stored upper entries; constraint matrix [I;D] is 2N×N
with 3N−1 nonzeros, D the first-difference matrix. R>0 makes the condensed Hessian positive
definite. Bounds constrain delta*+du to the shared steering box and each actual steering
increment to ±0.01 rad. No hard tracking-state constraints or global track optimization.

## Solver and interface extensions

OSQP 1.1.3 uses persistent CSC sparsity, numerical Hessian/vector updates, shifted primal warm
starts and zeroed dual initialization. Cold comparison zeros both. Settings: eps_abs/eps_rel
1e−6, maximum 400 iterations, check every 10 iterations, adaptive rho every 25, no polishing.
The initial fixed-rho attempt failed a valid abrupt-feedforward constraint test; adaptive rho
passed without loosening residual checks. Numeric Hessian updates can require refactorization;
workspace reuse does not mean factorization is free. See the
[official OSQP interface](https://osqp.org/docs/interfaces/python.html).

The main workspace and OSQP import are constructed before launch. A local horizon shortens
when necessary to remain inside packet validity; smaller workspaces are cached on first use.
With less than one complete 10 ms stage, the current update uses TVLQR. Solver failure, nonfinite
output or unacceptable primal/dual residual also selects TVLQR locally. The accepted solution
must satisfy physical inequalities within 1e−5 and dual residual <=1e−3.

Two narrow interfaces extend the frozen scheduler/predictor: forecast_command lets a cloned
MPC generate the same kind of local feedback during actuation-state prediction, and
finalize_update checks the 10 ms deadline after physical command validation. A deadline failure
replaces the proposed lateral command with the precomputed exact TVLQR command and logs the
reason, cost and replacement. The same longitudinal law is used. Elapsed computation cannot
be undone: the replacement retains the measured delay and any missed codriver release.
TVLQR controllers use the unchanged original branches. QP failures never request global
Task 005 fallback. Each forecast clone owns its solver state; its QP costs count toward planner
computation. High-level TVLQR gain preparation remains available for immediate local fallback.

The reference defect uses the planner's frozen curvature preview, while the independent NumPy
plant refreshes geometry along its actual motion. Local parity therefore also measures this
short-step geometry approximation. No global nonlinear-accuracy claim is intended.

## Horizon and configuration selection

All five horizons completed two laps with identical offered packets. N=3/5/8/10/15 gave
trajectory lateral RMS 1.121/1.186/1.064/1.234/1.338 mm and full-update p95
2.765/2.945/3.509/4.174/4.579 ms. N=8 is the smallest within 5% of the best MPC
RMS; N=3 misses that threshold narrowly (5.33%). This is an engineering screening choice,
not a statistically established optimum. No longer horizon earned its extra work.

The selected *experimental MPC* is N=8, LTV, W=0, shifted primal start, 100 Hz,
Q=diag(100,100,4,1), R=25, DARE terminal cost and retained affine defect. Steering box
is [-0.4,0.4] rad, slew 1 rad/s; acceleration box remains [-3,2] m/s². Other settings
are frozen in results/linear_mpc_codriver/selected_configuration.json. Library/CLI defaults
remain the initial N=5; reproducing the selected candidate requires explicit `--horizon 8`.

At N=8, W=0.5/1/2 increased trajectory RMS to 1.182/1.217/1.292 mm. Steering variation
fell from 2.733 to 2.682/2.664/2.654 rad, too small a benefit to justify the tracking loss.
Frozen LTI gave 1.161 mm and p95 3.145 ms versus LTV 1.064 mm and 3.509 ms.
Retain LTV for the candidate; neither approximation beats TVLQR on fixed packets.

## Identical packets versus closed-loop replanning

Phase A TVLQR/N8 MPC trajectory RMS is 0.447/1.064 mm, p95 and all four error channels
are exported in tracker_envelopes.csv, and peak lateral error is 6.425/14.344 mm.
Steering variation is 2.827/2.733 rad (only 3.35% lower). Centerline RMS improves from
3.836 to 3.413 mm, but this does not reverse the worse tracking of the authoritative
trajectory. Replay freezes availability and does not execute the planner: its recorded
availability delay is not a new planner CPU measurement. Acceptance gates remain active;
identical offered packets do not imply identical acceptance decisions or vehicle states.

Phase B nominal TVLQR/MPC centerline RMS is 3.903/2.711 mm and trajectory RMS
0.415/0.287 mm. Peak trajectory lateral error is 6.397/5.420 mm. Heading RMS is
0.017952/0.015207 rad; speed RMS 0.030172/0.029765 m/s. Lap times are
16.2495+16.1738 s and 16.2477+16.1723 s. Those millisecond lap differences do not
establish a racing benefit. All 26 cases completed two laps without boundary violations
or global fallback. Full outcome, tire-utilization, deadline and envelope tables are in
LINEAR_MPC_CODRIVER_RESULTS.md and raw per-case summaries.

Fresh timing is not identical to Task 006.3: nominal TVLQR had two skipped codriver releases
and one >10 ms callback; MPC had zero skipped releases/overruns but two strict-status local
replacements (0.062%). Historical Task 006.3 had none. Desktop jitter is retained, not erased.

## Disturbance, stress and delay behavior

The unchanged disturbance at 5 s is +0.08 m lateral and -0.04 rad heading. TVLQR/MPC
trajectory RMS is 3.105/3.366 mm and peak 80.013/79.997 mm. Recovery is 0.470/0.463 s:
first continuous 1 s inside |centerline e_y|<=0.02 m and |e_psi|<=0.05 rad, searched
within 5 s after perturbation. A 7 ms gain fails the preregistered 0.1 s/20% recovery gate.
Both request one urgent replan at 5.010 s; launch occurs at 5.04244/5.05268 s.
Steering variation improves 3.024 to 2.399 rad, but local
tracking RMS worsens 8.4%. This supports a smoothness tradeoff, not unqualified superiority.

The controlled stress applies +0.06 m/+0.06 rad at 7.7 s near a curvature transition.
It changes the disturbance only, not plant parameters or actuator limits. Both remain valid.
TVLQR/MPC trajectory RMS is 2.477/2.721 mm, peak 63.998/65.022 mm and recovery
0.516/0.533 s. Time at the steering-rate limit falls 0.889 to 0.676 s; steering variation
falls 3.248 to 2.673 rad (17.7%). The QP handles constraints but did not materially improve
recovery. Both request one urgent replan at 7.710 s; launch occurs at 7.74659/7.75642 s.
Exact request/launch records remain in events.json.

At 60/100/150 ms planner delays, trajectory RMS TVLQR/MPC is 0.378/0.245,
0.403/0.304 and 1.036/0.505 mm. Both have 0/0/162 skipped planner releases,
respectively, no global fallback, and no codriver scheduling misses. These controlled cases
use zero *simulated* codriver delay, while recording callback work and enforcing its local
10 ms replacement guard; they isolate planner-reserve behavior rather than total real-time feasibility.
The isolated 150 ms spike amid 25 ms delays yields 0.328/0.245 mm and one planner miss
for each controller. Full reserve statistics and stale/handoff records remain available.

Injected QP failure at 6 s produces the exact TVLQR command for that MPC update without
global fallback. Separate tests cover nonfinite output/residual, bad status, constraint residual
and deadline failure. Solved-inaccurate and iteration-limit results are intentionally rejected;
we did not relax tolerances or retune the iteration cap after seeing the results.

## Actuator activity and computational cost

Nominal TVLQR/MPC steering variation is 2.729/2.177 rad; RMS steering rate
0.229/0.179 rad/s; peak rate 1/1 rad/s; time at limit 0.577/0.270 s. Requested correction
RMS is 0.00747/0.00402 rad and maximum 0.0934/0.0622 rad. Requested correction is
before the common actuator clipping; separate applied-correction columns prevent confusion.
Acceleration variation is 1.639/1.390 m/s² despite an identical longitudinal feedback law,
because nominal packets and vehicle states differ in full replanning.

The fixed-input benchmark uses 800 sampled states repeated in three rotated controller orders
(2400 callbacks each). TVLQR/warm MPC mean is 1.029/2.837 ms, p95 1.175/3.060 ms,
p99 1.228/3.312 ms and maximum 1.522/32.950 ms. Mean CPU is 1.028/2.832 ms.
Warm MPC has two deadline replacements; TVLQR and cold MPC have zero in this benchmark.
Compute ratios mean/p95 are 0.103/0.117 for TVLQR and 0.284/0.306 for warm MPC.
These are excellent/comfortable p95 margins, not worst-case real-time guarantees.

Warm starts did not help this sampled fixed-input workload: mean iterations 28.97 versus
26.43 cold, p95 50 versus 40; solver p95 31.14 versus 25.18 microseconds. Warm/cold
full p95 is 3.060/3.002 ms. Inputs are sampled every fourth historical update, so this is
not proof that warm starts cannot help consecutive 100 Hz operation. The frozen experimental
candidate remains warm; no retrospective warm/cold retuning is hidden in the reported runs.

QP numerical update averages 6.61 microseconds inside OSQP (32.30 microseconds including
Python update and warm-start calls), and solve averages 16.96 microseconds. Model/DARE/
condensing averages 1.592 ms: the tiny solver is not the dominant cost. Online workspace
lookup averages 0.24 microseconds; main setup is prelaunch, and complete tracker/plant/planner
construction is reported separately rather than mislabeling lookup as initial solver setup.
No independent factorization timer is exposed. OSQP 1.1.3 reports the builtin algebra;
installed numerical package versions are unchanged from Task 006.3.

Nominal planner+codriver CPU demand is 0.4104+0.1044=0.5149 core-seconds/s for TVLQR
and 0.5156+0.2837=0.7993 for MPC, a 55.2% increase. Forecasting cloned MPC corrections
also costs planner CPU. These exclude simulation integration, logging, transport and sensing.
Configured Accelerate SINGLE mode and measured effective callback cores near 1 agree;
exact native active thread counts are unavailable. Final process RSS is 146.75/153.25 MiB,
lifetime peak 182.13/190.81 MiB; this is whole-worker RSS, not solver workspace memory.

## Embedded workload and Pi portability

The N=8 condensed QP has nx=4, nu=1, 8 decisions, no equalities, 16 two-sided rows
(32 scalar inequalities), H 8x8 (64 full/36 stored upper entries), A 16x8 (23 nonzeros),
and a 24x24 KKT system. Dense response/cost recursion requires approximately 5504 multiplies
and 4768 adds, excluding Jacobians, DARE, rate penalty, solver factorization/iterations and
validation. Core H/A/q/l/u float64 payload is 1016 bytes, excluding indices, factors and
Python/CasADi objects. Detailed workload and timing exports are machine-readable JSON.

With T_target≈T_M1/rho, p95 requires rho>=0.117/0.235 for TVLQR to fit 10/5 ms;
warm MPC requires >=0.306/0.612. These are relevant single-core throughput requirements,
not Raspberry Pi measurements. Under the additional simplifying assumption that *all*
planner and codriver work scales by the same rho on one shared core, average utilization
would require rho>0.515/0.799 before sensing and transport. That average necessary condition
is not sufficient for deadlines; the >10 ms tails explicitly fail a hard bound on this M1.

Pi 4 and Pi 5 both need direct complete-callback and concurrent-planner measurements with
the intended OS, governor, thermal policy, BLAS and OSQP build. Verify native wheels/ABI,
allocation and process RSS, scheduling tails and actuator I/O. Single-core performance matters
more than headline core count for this callback. TVLQR is the first target benchmark; the
small MPC remains technically benchmarkable, but this study does not justify its deployment.
No Pi hardware, CPU percentage or deployment is claimed.

## Selection and practical significance

**A — retain TVLQR.** MPC's full-loop nominal steering variation improves 20.2%, satisfying
that individual preregistered smoothness screen with no peak-error regression. Its trajectory
RMS improvement is only 0.128 mm, below the 0.2 mm absolute gate; peak improvement is
0.978 mm, below the 2 mm gate. More importantly, identical-packet RMS increases 138.4%
and peak error 123.3%, while disturbance/stress recovery and tracking offer no material gain.
The 55.2% architecture CPU increase, numerical local replacements and added complexity
outweigh the limited smoothness benefit. Passing one screen was necessary, not sufficient.
A conditional hybrid is not implemented or recommended for adoption from this evidence.

Carry Candidate C at 10 Hz, N=4/0.4 s, one native thread, the existing trajectory buffer,
100 Hz TVLQR plus unchanged longitudinal P, reserve/urgent/global-fallback policies and
0.08 m margin into the PRE-TASK-007 REVIEW GATE. Keep MPC as an experimental alternative.
The disturbance peak approximately equals the existing margin; perfect-state nominal millimeter
errors cannot justify reducing a robust margin. No margin change is made.

## Prediction validation, limitations and implementation deviations

108 independent nonlinear/local horizon comparisons cover speeds 1/2/3 m/s, progress
0/4/8/12 m, steering 0/0.15/0.3 rad and error scales 0.001/0.01/0.05. Across these cases,
maximum endpoint lateral discrepancy is below 0.078 mm and heading discrepancy below
0.000601 rad over 80 ms. Error is not necessarily monotonic in perturbation size because
nominal curvature discretization contributes a residual floor. Detailed speed, steering,
curvature and error-magnitude groupings are in model_parity/summary_by_condition.csv.
This verifies local behavior only; speed/progress perturbation coupling is excluded from
four-state prediction and the synthetic model is not identified vehicle physics.

There is one measured run per dynamic condition, not confidence intervals over hardware jitter.
Timing benchmark order is rotated but shares a process; cold means zero solver start, not
fresh process per sample. Simulated overlapping planner/actuator timelines are event-driven,
not a measured multicore deployment. Delay-study zero codriver delay is explicit above.
Optional 200 Hz, hard local state bounds and terminal-free tuning were not pursued.

The only existing runtime-file extensions are the optional forecast and finalization hooks.
Replay disables new urgent scheduling to preserve exact offered plans. Stress is an explicitly
new controlled perturbation. The finalization guard cannot undo elapsed computation and its
last bookkeeping/backup-validation work remains in total callback timing; backup validation
is not separately added to the command-validation component. The dependency addition is
OSQP and its transitive packages; previous package versions remain frozen.

Final review added an explicit nonfinite dual-residual guard with a fault-injection regression.
No accepted experiment contained a nonfinite residual, so recorded decisions are unaffected;
measured source is preserved under benchmark_sources and final source is archived separately.
The tiny added guard's timing is not rebenchmarked and is not presented as part of the archived
measurements. This is the only post-measurement runtime difference.

## Planning reference handoff and next step

Task 007 is not implemented. Planning must provide a versioned offline progress-indexed
racing reference: e_y_ref(s), e_psi_ref(s), kappa_ref(s), v_ref(s), optionally a_ref(s),
with units/frames, periodic closed-track interpolation and seam consistency, track identity,
feasibility/width/grip/slew validation and explicit handling of invalid references. Control
consumes this data; it does not generate the team's global racing line or velocity profile.
See PRE_TASK007_CONTROL_REQUIREMENTS.md for the complete contract. The next action is the
PRE-TASK-007 REVIEW GATE, not automatic implementation of racing features.

## Completed validation

Full regression: 454 passed in 817.84 s. Final local suite: 21 passed in 1.73 s, including
nonfinite-residual and zero-latency cases added after full-suite collection; 456 distinct tests
are covered across these runs. All 26 physical chronology and local-fallback/replay audits pass.
Ruff lint and formatting pass for 148 active Python files. All 411 archived Task 006.3 result
files remain byte-identical, and every recorded case source hash matches benchmark_sources.
28 plots cover all requested categories; paired replay and stress-recovery figures were visually
reviewed. Results, validation logs, final source archive and provenance are in
results/linear_mpc_codriver. No Task 006.4 work remains pending.
