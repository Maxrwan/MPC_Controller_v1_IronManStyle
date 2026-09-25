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
