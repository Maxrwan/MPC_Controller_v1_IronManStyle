# Architectural decisions

Tasks 001–006; accepted unless explicitly marked provisional.

## ADR-001 — Python simulation-first architecture

Keep early development accessible on macOS without hardware middleware.

## ADR-002 — Generic configurable 1/10-scale race car

Represent unknown physical parameters explicitly; require measurements before simulation.

## ADR-003 — SI units exclusively

Avoid conversion ambiguity at subsystem boundaries.

## ADR-004 — Canonical state ordering fixed

Use named indices for [vx, vy, r, e_psi, s_abs, e_y].

## ADR-005 — Continuous unwrapped progress s_abs

Wrap only geometry queries; preserve multi-lap state.

## ADR-006 — Acceleration command rather than drivetrain torque in v0

Control ordering is [delta, a_cmd]; drivetrain modeling is deferred.

## ADR-007 — Plant and prediction models separated

Allow independently injected equations, parameters and discretizations.

## ADR-008 — CasADi + IPOPT used initially behind solver abstraction

Intended backend only; no solver implementation yet. Preserve alternative solvers.

## ADR-009 — Quasi-static longitudinal load transfer planned for first dynamic model

Start with front/rear axle loading; improved lateral and four-wheel effects are later.

## ADR-010 — No ROS initially

The first platform is a standalone Python simulation.

## ADR-011 — uv used for Python dependency/environment management

Use pyproject.toml and a reproducible lockfile.

## ADR-012 — Closed-track simulation continues across lap boundaries

Lap events never imply termination or truncation.

## ADR-013 — System identification is a first-class project subsystem

Keep learning model updates independent of controllers and trajectory storage.

## ADR-014 — Energy management precedes opponent/defensive racing

Follow the agreed roadmap ordering.

## ADR-015 — Defensive strategy is architecturally separated from low-level vehicle dynamics

Tactics modify planning inputs and controller constraints/objectives.

## ADR-016 — Bootstrap representation and tooling choices

Python 3.12 development pin; NumPy float64 one-dimensional validated vectors; PyYAML safe loading; pytest and Ruff. Protocol context/problem payloads remain deliberately minimal.

## ADR-017 — Conservative configuration readiness validation

Require all numeric template fields before simulation; positive finite values except nonnegative CG height; positive braking-limit magnitude; wheelbase consistency. Axle cornering-stiffness interpretation is provisional and needs confirmation.

## ADR-018 — Periodic cubic centerline interpolation

Task 002 uses SciPy CubicSpline with periodic boundary conditions and raw cumulative
waypoint chord parameter q. Enforce C2 closure and guard degenerate tangent magnitudes.
At least four distinct ordered planar waypoints are required; one repeated endpoint is removed.

## ADR-019 — Numerically arc-length-consistent public progress (choice A)

Integrate spline speed by segment and invert with bounded Brent root finding. Public
length/progress measure numerical arc length, while chord_length is diagnostic only.
This avoids passing chord-parameter distortions into future controller equations.
Quadrature uses 1e-11 absolute/relative tolerances; inversion uses 1e-12/1e-13.

## ADR-020 — Continuity through nearest lap equivalence

Wrapped projection and unwrapped race progress remain separate. Given a previous/expected
s_abs hint, choose the nearest nonnegative lap equivalent; forward wins half-lap ties.
Changes must be below half a lap. Do not enforce monotonicity or infer missing laps.
Recognize represented exact multiples without epsilon-snapping adjacent measurements.

## ADR-021 — Simple planar closed tracks initially

Assume non-self-intersecting centerlines, race-ordered waypoints and first-waypoint origin.
Reverse motion and branch-aware projection are deferred. No full topological validator is
claimed; periodic spline overshoot and offset boundary validity need human review.

## ADR-022 — Independent explicit constant half-widths

Left and right widths are positive SI values supplied by callers, with progress-dependent
query methods for future variation. No physical track widths are invented.

## ADR-023 — Bounded polynomial projection candidates

Rather than sampling a coarse nearest point, solve the distance-stationarity polynomial
on every normalized cubic segment, include endpoints, and select minimum distance.
This removes a coarse-grid resolution assumption at O(segment count) cost. It is not a
real-time performance claim. A previous-progress hint resolves lap number, not branch ambiguity.

## ADR-024 — Canonical angle and immutable coordinate records

Use one wrap_angle utility with (-pi,pi], frozen GlobalPose and FrenetProjection records,
and an expanded immutable TrackSample. The Track protocol accepts arbitrary geometric
progress and exposes explicit widths and point projection. Canonical vehicle state is unchanged.

## ADR-025 — CG-based kinematic bicycle

Task 003 uses the center of gravity as vehicle reference; L=lf+lr. Require only wheelbase/lf/lr through model-specific validation; preserve strict full-vehicle validation.

## ADR-026 — Body-longitudinal vx at the CG

vx is not total speed. vy=vx*tan(beta) and total speed=hypot(vx,vy); do not substitute the latter for vx in the requested equations.

## ADR-027 — Algebraic kinematic vy and r

Integrate only [vx,e_psi,s_abs,e_y]. Reconstruct vy and r at each stage and output; ignore incoming finite vy/r in this model. No fake lateral/yaw acceleration equations.

## ADR-028 — Ideal a_cmd equals dvx/dt

Task 003 directly commands body-longitudinal acceleration; no drivetrain or braking force physics is introduced.

## ADR-029 — Configurable fixed-step RK4

Default dt=0.01 s in one named constant, configurable on construction or each step. Classical RK4 integrates the reduced state; use the exact linear vx result to remove endpoint roundoff.

## ADR-030 — Zero-order-held control

Hold delta and a_cmd throughout each step; recompute stage algebraic quantities from stage vx. Time-script changes take effect at step boundaries.

## ADR-031 — Ideal instantaneous steering

No steering actuator state/rate constraints. Steering changes can instantly change vy/r. Enforce any configured angle bound without clipping; require the principal tangent branch and guard abs(cos(delta))<=1e-8 as a mathematical domain restriction.

## ADR-032 — Forward-only stopping event

Reject materially negative vx. Under braking, integrate only until exact t_stop, then hold at zero for the rest of the step. Numerical speed-boundary tolerance is 1e-10 m/s. Physical command bounds are rejected, never silently clipped.

## ADR-033 — Explicit Frenet validity errors

Require 1-kappa*e_y>1e-3 at input, evaluated RK4 stages and final state. Reject negative denominators as outside the chosen regular branch; never clip. This is not race termination or a dense event guarantee.

## ADR-034 — Track injection preserves model protocol

Supply Track to KinematicBicycle constructor, keeping DynamicsModel.step(state,control,dt) unchanged. Diagnostics are a separate frozen record; the demo driver logs directly to CSV without a new framework.

## ADR-035 — Dynamic CG body equations

Task 004 integrates all six canonical channels using the prescribed force/moment balances. No steering-frame force rotation terms are silently added.

## ADR-036 — Axle-aggregate linear cornering stiffness

Cf/Cr are axle aggregate N/rad. Preserve existing front_cornering_stiffness/rear_cornering_stiffness keys, without per-wheel conversion.

## ADR-037 — Exact atan2 slip definitions

Use alpha_f=delta-atan2(vy+lf*r,vx) and alpha_r=-atan2(vy-lr*r,vx). Positive slip generates leftward lateral force; no small-angle slip approximation.

## ADR-038 — Dynamic Fx=m*a_cmd semantics

Dynamic a_cmd=dvx/dt-r*vy. This differs explicitly from Task 003 and drives quasi-static transfer directly; no drivetrain/force-allocation model is introduced.

## ADR-039 — Explicit dynamic low-speed validity

Default v_dynamic_min=0.5 m/s is configurable. Values materially below it raise LowSpeedValidityError; a 1e-10 m/s tolerance accepts roundoff without changing vx. No epsilon regularization or automatic switch.

## ADR-040 — Quasi-static longitudinal load transfer

Use the specified front/rear loads with a_cmd, CG height and shared configurable default g=9.81. Reject actual/static loads <=1e-9 N rather than clamp or simulate axle lift.

## ADR-041 — Provisional load-scaled stiffness

C_eff=C*Fz/Fz0 is an educational first-order approximation only, not a complete tire load-sensitivity law.

## ADR-042 — Friction coefficient diagnostic only

mu is optional metadata. When supplied, report lateral abs(Fy)/(mu*Fz); absent mu yields None. This ratio excludes longitudinal force and does not alter forces.

## ADR-043 — No tire-force saturation

Task 004 intentionally has no friction-circle, combined-slip or nonlinear saturation. Large-slip finite outputs do not establish physical validity.

## ADR-044 — Dynamic RK4 default 0.005 s

Use independent pure RK4 integration with held input and freshly evaluated state-dependent components at every stage plus final validation. Keep kinematic dt=0.01 unchanged.

## ADR-045 — Replaceable tire/load components and shared geometry guard

Use minimal evaluate protocols and immutable axle results. Extract the existing Frenet denominator rule into a shared helper without changing kinematic behavior. Expose NumPy derivative independently of stepping.

## ADR-046 — Centerline baseline

Task 005 tracks e_y_ref=0 to establish a benchmark, without racing-line optimization.

## ADR-047 — Perfect state feedback

Use estimated_state=true_state; no estimator/noise claims or algorithms.

## ADR-048 — Requested lateral error ordering

Use [e_y,e_psi,vy-vy_ref,r-r_ref]. Preserve raw e_psi; document the homogeneous design's
neglected affine vy_ref and expected steady bias rather than silently shift heading state.

## ADR-049 — Nominal steady linear cornering references

Solve static-stiffness lateral-force/moment balance at current vx and local curvature.
No nonlinear equilibrium solve; references remain approximate on the nonlinear plant.

## ADR-050 — Dynamic curvature feedforward

Use L*kappa+m*vx²*kappa/L*(lr/Cf-lf/Cr); log atan(L*kappa) as comparison only.

## ADR-051 — Cached speed-scheduled discrete LQR

Exact ZOH and DARE at construction; linear gain interpolation online, with only the
scheduling variable clamped outside the grid and explicit clamp diagnostics.

## ADR-052 — Synthetic schedule nodes 1/2/3 m/s

Validate these development speeds; they are not physical APEX operating limits.

## ADR-053 — Controller 100 Hz, plant 200 Hz

Hold commands for two RK4 plant steps. Do not modify model default rates globally.

## ADR-054 — Bryson initial cost

Q=diag(100,100,4,1), R=25 from supplied SI design scales. No weight tuning/optimization.

## ADR-055 — Independent longitudinal PI with anti-windup

Kp=1, Ki=.5 synthetic; conditional integration, configured [-braking,+acceleration]
saturation and explicit reset. No hidden cancellation of dynamic r*vy coupling.

## ADR-056 — Nonlinear Task 004 validation plant

Preserve existing dynamic physics while the controller uses a small-slip design model.

## ADR-057 — Generic runner and explicit failure accounting

Integer rate ratios, optional reset/diagnostic callbacks, continuous s_abs, duration cap
and optional travelled-lap target. Sample CG boundary violations without implicit stop;
model failures retain last valid sample and explicit failure type/message.

## ADR-058 — Transparent command limiting and metric windows

Clip steering/acceleration in the controller; plant raw-input validation remains strict.
Enforce steering rate only if configured; otherwise report diagnostic differences from
previous command (initially zero). Report full-run metrics alongside fixed t>=5 s metrics.

## ADR-059 — Nonlinear tracking MPC

Task 006 uses nonlinear tracking MPC; racing and progress optimization remain Task 007.

## ADR-060 — Independent CasADi prediction

Transcribe approved Task 004 equations independently and gate closed-loop work on NumPy parity. Never use symbolic prediction as the validation plant.

## ADR-061 — Direct multiple shooting

Use canonical state/input nodes with explicit initial-state and RK4 shooting equalities.

## ADR-062 — Nominal MPC release at 20 Hz

Fixed 50 ms release clock, independent of solver completion and plant integration.

## ADR-063 — Twenty-step horizon

One-second horizon with twenty independent control actions; no control blocking.

## ADR-064 — Five symbolic RK4 substeps

Each prediction interval uses five 10 ms RK4 steps; physical plant retains at most 5 ms integration steps.

## ADR-065 — Centerline tracking reference

Use ey_ref=0 and epsi_ref=0 exactly; reuse steady body cornering references without inventing a heading correction.

## ADR-066 — No progress objective

s_abs selects geometry but receives neither tracking penalty nor direct reward in Task 006.

## ADR-067 — Reuse Task 005 cornering utilities

Generate nominal vy/r/feedforward from speed-reference preview; curvature is frozen per shooting interval.

## ADR-068 — Hard configured actuator limits

Use synthetic steering ±.4 rad and acceleration [-3,+2] m/s²; validate returned commands.

## ADR-069 — Synthetic steering rate

Constrain increments to ±.05 rad at nominal 50 ms, including actual previous steering. The 1 rad/s development value requires physical measurement later.

## ADR-070 — Explicit soft track constraints

Independent nonnegative left/right slacks at every node, linear/quadratic penalties 10000/100000. Flag every nonzero slack; physical boundary monitoring stays separate.

## ADR-071 — IPOPT through solver abstraction

Backend calls/options/timer belong to the adapter. SolverResult carries statistics; controller independently rejects invalid output.

## ADR-072 — Shifted primal warm starts

Shift successful X/U/slack trajectories one stage and replace sampled X0; clear after failure. No dual warm-start claim.

## ADR-073 — Application-time baseline fallback

On failed solve, assess the current application state and baseline domain, then use rate-limited baseline or terminate cleanly. No hidden emergency law.

## ADR-074 — Three distinct clocks

Separate physical time, fixed release schedule and monotonic solver wall duration; also log total controller computation separately.

## ADR-075 — Plant advances during computation

Replay the full solve latency with unchanged prior input before making the new result available; split plant steps at exact events.

## ADR-076 — Skipped fixed deadlines

No overlapping solves. Releases while busy, including exact completion ties, are missed; next solve starts at the strictly subsequent nominal release.

## ADR-077 — Normalized staleness

Log all raw state differences and the specified five-channel normalized index excluding progress. It is dimensionless, not distance.

## ADR-078 — Zero measured and injected modes

Zero for algorithm comparison, measured for host-dependent timing, deterministic injection for reproducible latency degradation.

## ADR-079 — Mandatory future latency tests

Future computational controllers must retain plant-motion, command-hold, staleness, deadline and deterministic-latency tests; wall timing is not an exact CI threshold.

## ADR-080 — Prediction-domain and metric policy

Hard speed/denominator guards at all RK4 evaluation states and shooting nodes, positive loads per input. Use physical-time-weighted metrics for all controller comparisons.

## ADR-081 — Preserve linear reference

LinearAxleTire semantics and legacy constructor defaults remain unchanged; racing composition explicitly selects grip.

## ADR-082 — Smooth combined-force envelope

Add SmoothCombinedGripTire as an engineering approximation, not a named fitted tire model.

## ADR-083 — Friction capacity

Use configured positive mu times current axle normal load; never fabricate missing mu.

## ADR-084 — Idealized axle allocation

Use replaceable normal-load proportional longitudinal allocation in synthetic racing configuration; this is no physical AWD claim.

## ADR-085 — Smooth tanh saturation

Fy=capacity*tanh(C_eff*alpha/capacity); retain provisional load-scaled stiffness and exact small-slip slope.

## ADR-086 — No hard lateral clipping

The primary force law remains differentiable; no clip corners or hidden sqrt max regularization.

## ADR-087 — Longitudinal demand rejection

Reserve dimensionless1e-6 of longitudinal capacity; reject excessive requests. Matching NLP constraints and acceleration bounds protect trial-domain evaluations.

## ADR-088 — Combined utilization diagnostics

Expose longitudinal/lateral forces, limits, remaining capacities, utilization, slips, loads and stiffness; keep lateral-only legacy fields.

## ADR-089 — Independent matched prediction

Transcribe grip physics independently in CasADi and gate use on derivative/force/utilization/RK4 parity.

## ADR-090 — No fitted tire model yet

Pacejka/Fiala/Dugoff fitting, wheel slip/speed dynamics and measured identification remain unimplemented.

## ADR-091 — No lateral transfer or force rotation change

Preserve current axle longitudinal transfer and body balances; steering-frame rotation remains a documented limitation.

## ADR-092 — Preserve computational baseline

No cost tuning or solver optimization. Save grip results separately and profile construction, solve/evaluation statistics and sparsity for Task006.2.


## ADR-093 — Stage tuning before architectural change

Task006.2 screens the unchanged synchronous grip NMPC in stages A–G. Preserve physics,
independent models, direct multiple shooting, IPOPT and held-input latency semantics.
Asynchronous planning and alternative codrivers remain future tasks.

## ADR-094 — Pareto selection without weighted score

Use nondominance on solve p95 and lateral/heading/speed RMS after explicit quality,
feasibility and prediction-accuracy gates. Keep rejected data. Select role-specific
A/B/C/D candidates; no claim of a global optimum or guaranteed real-time execution.

## ADR-095 — Horizon screening

At20Hz with5RK4 substeps compare N8,10,12,15,20,25 on one complete oval lap;
confirm finalists on two laps, circle and disturbance rather than expanding every setting.

## ADR-096 — Independent prediction-fidelity gate

Compare1/2/3/5RK4 substeps with high-accuracy integration of the independent NumPy
plant over seeded frozen-curvature intervals. Equal-step parity alone does not establish
integration accuracy. Retain inaccurate cheap settings as rejected observations.

## ADR-097 — Frequency and exact event clocks

Compare10/15/20/25Hz with one-second coverage. Keep the literal selected substep count;
if it fails accuracy at a larger interval, separately test the least refined passing count.
Permit fractional release/plant ratios only on the event runner; keep plant steps<=5ms.

## ADR-098 — Grouped sensitivity and terminal separation

Screen lateral/heading,vy/r,speed,R,W one factor at a time with at most one promising
combination. Scale the complete terminal term separately at0/.5/1/2. Preserve stage-sum
semantics and the existing terminal schedule; report frequency-dependent cost coupling.

## ADR-099 — Explicit nested timing decomposition

Time preview, reference/geometry subparts, warm preparation, parameter packing, backend,
adapter, validation/postprocessing and total compute. Keep solver-call physical latency
for Task006 comparability and disclose its end-to-end optimism. No symbolic rebuild was
found in the control loop. Serialized local timings do not establish Pi feasibility.

## ADR-100 — Evidence-led synchronous handoff

Candidate C is chosen after measured-latency confirmation, with explicit quality and
missed-release gates; if no candidate qualifies, state that limitation. Export exact
configuration, trajectory timing/reserve and baseline workload data for Task006.3.
Do not implement asynchronous buffers or Task006.4 linear MPC in this study.

The completed study selects `ipopt_warm_flag_d5e0d799d8`: 10 Hz, N=4, four RK4 substeps,
lateral/heading scale2, other scales1, current terminal term, exact Hessian and the ordinary
warm-start flag. Two-lap measured oval RMS lateral error was4.147mm with15.848ms solver
p95,19.898ms total p95 and no missed releases. Preserve the20Hz,N20 reference separately.
This is a synthetic host-specific starting point, not a real-time or safety guarantee.

## ADR-101 — Retain a verified single-thread baseline

Task006.2.2 retains deterministic native single-thread execution for debugging, comparisons
and tests. The Mac Accelerate SINGLE mode is set before numerical imports and read back.
Fresh-process repeated C solutions match bitwise. This is a benchmark control, not a change
to controller equations or an unconditional cross-platform backend API.

## ADR-102 — Configure the detected numerical backend explicitly

Inspect active BLAS/LAPACK, IPOPT and its linear solver before choosing thread controls.
The installed stack uses Accelerate; record native mode and requested ceilings separately
from measured active cores. Do not claim that OMP/OPENBLAS variables activate parallelism.
Do not add an OpenMP/solver thread knob without evidence the active build supports it.

## ADR-103 — Isolate timing conditions in fresh serial subprocesses

Apply startup environment controls before native initialization. Each benchmark condition
uses a fresh worker and one serially invoked optimizer. Warm up, use deterministic frozen
inputs, randomize condition order, repeat and retain raw data. Never overlap latency
benchmarks with one another or tests. Cache settings must match and failed runs remain
visible. psutil/threadpoolctl are development-only observation dependencies.

## ADR-104 — Distinguish intra-solve latency from task concurrency

Independent simultaneous solves are throughput experiments, not evidence of reduced
latency for one optimization. No manual optimizer worker pool, mapped-stage redesign,
asynchronous planner or codriver is adopted in Task006.2.2. Later task-level concurrency
must measure contention and latency semantics explicitly.

## ADR-105 — Recommend one native thread for current development evidence

Across 24 conditions / 2,880 solves, C/D do not meet the predeclared 10% p95 improvement
gate at higher ceilings. Measured effective core use remains approximately one.
T1, Tbest-latency, Tbest-efficiency and Trecommended are all one. Keep C frozen at 10 Hz,
N=4 with four RK4 substeps and the selected Task006.2 costs/solver policy. Retain the
4-ceiling closed-loop missed release and total-compute spikes as evidence, not discarded
outliers. This decision can be revisited only with a verified different execution path.

## ADR-106 — No unsupported target CPU or deadline claims

Export workload dimensions, sparsity, callback counts, CPU/core-time, memory and deadlines
for Pi benchmarking. Mac measurements establish neither Pi utilization percentages nor
transferred thread scaling. Any relative-performance sensitivity relation is analytical.
Measure target libraries, thermals, sustained timing tails and joint subsystem contention.
Desktop p95 margin is not a hard-real-time guarantee; solver-only simulated latency also
does not certify total-compute deadline compliance.

## ADR-107 — NMPC owns trajectories, not runtime actuator commands

Task006.3 wraps the existing constrained optimizer as a nominal trajectory planner.
The buffer owns accepted immutable packets, the codriver owns local feedback and the
independent NumPy plant owns actual state. Synchronous control remains a comparison path.

## ADR-108 — Preserve Candidate C at 10 Hz

Keep N4,0.4 s horizon,four RK4 substeps, selected Q/R/W and terminal cost, exact Hessian
and shifted-primal/IPOPT warm-start policy. No timing-motivated retuning. The explicit
tracker margin in ADR119 is the sole requested planner-bound change.

## ADR-109 — Retain one native planner thread

Apply and verify Accelerate SINGLE mode before numerical imports in isolated experiment
workers. Task006.2.2 found no useful intra-solve scaling. Do not call one optimizer concurrently.

## ADR-110 — Begin with a 100 Hz codriver

Use a fixed10 ms release grid, independent of the100 ms planner grid. Count missed planner
and codriver releases separately. Measure the full update and kernel costs plus modeled physical application
latency; ordinary planner overruns must not skip otherwise available codriver events.

## ADR-111 — Use nominal feedforward plus trajectory-aware TVLQR

Linearize the approved grip model at nominal X/U, discretize at10 ms and prepare finite-horizon
four-state/one-steering-input Riccati gains on the planner side. Reuse Task005 design weights.
Runtime work is interpolation and local feedback. Longitudinal correction is proportional
speed feedback plus nominal acceleration, common to the future Task006.4 comparison.

## ADR-112 — Use explicit physical-time packets and buffer

Packets own timestamped X/U, curvature/gain schedules, source/forecast state and computation
metadata. Interpolate unwrapped heading and absolute progress; hold nominal inputs/gains.
Reject stale, invalid or insufficient-reserve packets. Trim expired prefixes at handoff.

## ADR-113 — Emulate asynchronous physical chronology deterministically

Actual OS concurrency is unnecessary for this development task. Compute the candidate,
withhold availability until its physical completion, and advance the real plant under the
old trajectory and continuing codriver. Measured planner latency includes state forecasting
and gain preparation. Never pause moving physics during runtime computation.

## ADR-114 — Predict the intended actuation-time state

Use a replaceable rolling-median delay estimate initialized at17 ms, plus an independent
symbolic-model forecast driven by a clone of the active local tracker. Log delay and
state-prediction errors. Refuse forecasts that require extrapolating an exhausted trajectory.

## ADR-115 — Never overlap planner solves or grow an urgent queue

Fixed releases during a pending solve are missed and counted. Urgent requests retain one
pending bit and execute only when idle. A completed early packet waits for its nominal
start. All optimizer work remains serial.

## ADR-116 — Make trajectory reserve a first-class quantity

Reserve=end−physical time. Healthy≥0.20 s; warning[0.05,0.20); critical(0,0.05); exhausted≤0.
Require50 ms reserve for new acceptance. Log active reserve continuously and at completions;
do not count completion under fallback as uninterrupted trajectory operation.

## ADR-117 — Planner failure does not remove valid real-time control

Reject failed optimization/forecast/gain output while continuing the previous valid packet.
Retain failure evidence and retry at future eligible releases. No stale optimizer command is
substituted for current-state feedback.

## ADR-118 — No indefinite extrapolation; explicit development fallback

At exhaustion use existing Task005 LQR/PI only within its1–3 m/s and in-track domain;
otherwise terminate cleanly. Fallback is latched for the run, with no automatic planner re-entry.
Before launch, hold the vehicle unreleased, prepare and preposition the first plan/command,
then begin the validated2 m/s dynamic state. No standstill dynamics are invented.

## ADR-119 — Apply the provisional tracker margin explicitly

Add MPCConfig.tracker_margin with backward-compatible zero default; async experiments
explicitly request0.08 m per side. Preserve original physical track widths and slack costs.
Measure the tracking envelope before making any robust-margin claim.

## ADR-120 — Trigger one urgent replan after sustained tracking deviation

Two consecutive codriver samples above0.05 m lateral or0.10 rad heading trajectory error
request an early replan if idle, otherwise set one pending bit. Log the request, busy state
and eventual release. Retain fixed10 Hz planning as the normal mechanism.

## ADR-121 — Separate algorithm CPU accounting and future comparison boundaries

Report planner preparation, codriver update including command validation, and their summed
core-seconds/s separately from simulation integration/logging and periodic plant diagnostics. Export full timing distributions,
memory and matrix dimensions. Task006.4 may replace only lateral correction while retaining
the same planner, buffer, longitudinal policy, actuator semantics and experiments. No Pi
percentage or real-time deployment guarantee follows from M1 measurements.

## ADR-122 — Small MPC only owns local lateral correction

Task006.4 adds a four-error-state, one-steering-correction controller. The high-level Candidate C
trajectory remains authoritative. No speed profile, racing line or global planner is added.
The selection thresholds are written before experimental selection in LINEAR_MPC_CODRIVER_STUDY.md.

## ADR-123 — Use approved discrete Jacobians and retain the nominal affine defect

Linearize the existing grip-model RK4 map at the100Hz nominal trajectory. Retain the residual
between a nonlinear nominal step and the next interpolated reference. Condense the four-state
recursion into N corrective inputs; use the same Q/R priorities and local DARE terminal cost.
Compare frozen and varying Jacobians without changing the physical plant or packet reference.

## ADR-124 — Persistent OSQP workspace with independent residual validation

Use OSQP1.1.3 behind a small solver protocol, fixed CSC structure and online numerical updates.
Shift the primal solution; measure against zero-start operation. Main workspace construction
occurs before launch, shortened-horizon workspaces are cached. Adaptive rho every25 iterations
resolved a fixed-rho convergence problem without relaxing physical residual checks.

## ADR-125 — Local failure replaces only the current correction

QP status, nonfinite output, unacceptable residual or a postvalidation deadline overrun
selects the exact TVLQR replacement for this update. Log it; preserve elapsed physical latency.
This never independently requests global Task005 fallback. The predictor clones the active
tracker, including an independent local solver, so its forecast reflects the new control law.

## ADR-126 — Freeze the longitudinal controller

Both codrivers use a_star+1.0*(vx_star−vx) with identical physical clipping. No extra longitudinal
states, integrator, optimization or retuning are introduced.

## ADR-127 — Use paired packet replay before closed-loop planning

Replay the exact saved Task006.3 packet arrays and availability, retaining validation gates.
Suppress new high-level replan scheduling only in this explicitly frozen replay phase.
Then run full unchanged planning; differences in actual state legitimately change new plans.
Controlled planner-delay comparisons retain zero simulated codriver latency, with measured
callback overruns and local QP replacements separately visible; primary runs use measured delay.

## ADR-128 — Export portability requirements instead of Pi utilization claims

Report full-update time, core-seconds/s, QP dimensions/nonzeros and memory separately.
Use T_target≈T_M1/rho for10ms/5ms throughput requirements. Pi4/Pi5 hardware timing, thermal
policy, scheduling and native solver/backend behavior remain unmeasured; no Pi percentage.

## ADR-129 — Select N=8 LTV as the experimental MPC candidate

N=8 is the smallest horizon within 5% of the best MPC fixed-packet RMS. Larger horizons,
rate penalties and LTI approximation did not earn a tracking/cost advantage. Freeze W=0,
Q/R and DARE settings; shifted warm start is measured, not assumed beneficial. The fixed-input
warm benchmark was slightly slower than cold; no post-hoc retuning changes published runs.

## ADR-130 — Retain TVLQR for the pre-Task-007 review

MPC improves nominal full-loop steering variation 20.2% but worsens identical-packet tracking,
adds 55.2% total architecture CPU demand and offers no material disturbance/stress recovery
benefit. Retain TVLQR, longitudinal P and 0.08 m margin. Keep local MPC experimental; do not
implement a hybrid or Task 007. Planning supplies the offline racing reference per
PRE_TASK007_CONTROL_REQUIREMENTS.md; Control consumes and validates it.
