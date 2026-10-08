# Task 007B: progress-seeking APEX and nominal Planning intent

Task 007A was accepted by the explicit Task 007B brief. Task 007B implements the approved
optional objective and controlled experiments. The results and final selection are recorded
in [TASK007B_RESULTS.md](TASK007B_RESULTS.md); adaptive codriver work remains deferred.

## Ownership and frozen architecture

Planning owns both the offline global racing line and velocity profile. The synthetic generator
is temporary test infrastructure. The accepted Task 007A line, track, margin and nominal-state
construction are unchanged. APEX remains always active at 10 Hz, followed by its timestamped
trajectory buffer and unchanged 100 Hz TVLQR. There is no new Planning optimizer or mode selector.

Candidate C stays at N=4, dt=0.1 s, four RK4 substeps, exact Hessian, native SINGLE and warm start.
TVLQR gains, longitudinal P gain 1, 1 rad/s steering-rate limit and 0.08 m tracking margin are frozen.
Plant and symbolic prediction remain separate; simulation remains independent of controller choice.

## Progress objective

The approved addition is

    J = J_existing - lambda_s * (s_N - s_0) / (v_max * N * dt).

Here s is continuous unwrapped centerline progress, v_max=6 m/s and H=N*dt=0.4 s.
The denominator is 2.4 m: a normalization scale, not an upper bound on Frenet progress.
No new decision variable is introduced. `MPCConfig.progress_weight` defaults to zero, validates
finite nonnegative values, and leaves the previous objective expression unchanged when zero.
No direct grip, steering or acceleration reward exists. Hard constraints remain unchanged.

## Frozen cost terms

For stage error order [vx, vy, r, e_psi, e_y], Candidate C uses
Q=diag(4,4,1,200,200). Input-reference R=diag(25,1) and successive-input W=diag(1,0.1),
with input order [delta, a_cmd]. The increment term uses input differences, not derivatives.
Stage terms are summed without a dt multiplier.

The terminal term is z'P(v)z + 4*(vx-vref)^2, with z=[ey_error,epsi_error,vy_error,r_error].
P uses the existing Task 005 100 Hz DARE matrices, interpolated at 1,2,3 m/s and clipped beyond
that range. The terminal multiplier is 1. Slack costs remain 1e4*sum(E)+1e5*sum(E^2), including
the terminal node. The actuator, grip, load, speed and Frenet constraints are unchanged.

Every accepted solution exports state tracking, input/reference, input increment, terminal
tracking, linear/quadratic slack, progress and total contributions through a separate symbolic
evaluation of those same terms. Offline state-channel attribution independently checks the
tracking-group sum. Tiny barrier slacks must be distinguished from material slack use.

## Aggression packages

The ladder uses v_gamma(s)=min(gamma*v_007A(s),6 m/s), with gamma=1,1.25,1.5,1.75,2,2.25,2.5.
There is no offset, heading, curvature, track or profile-shape repair. a_ref remains omitted.
Each manifest records gamma, the scaling/cap policy and the base reference SHA256.

At gamma=1 the accepted CSV is copied byte-for-byte. At uncapped levels the periodic speed
cubic is the base cubic multiplied by gamma. For capped levels, offline code splits the base
cubic at its 6 m/s crossings and serializes cubic/constant pieces in `speed_polynomial.json`.
Runtime loads the declared polynomial; it neither refits nor clips the request. This represents
the explicitly approved cap without interpolation overshoot or a new velocity optimizer.
Generator v2 preserves every original non-speed CSV field verbatim. Each experiment also retains
its actual fixture, including early float reserializations with at most 1.4e-14 m geometry drift.

## Hard validity and feasibility diagnostics

The default loader remains strict for Task 007A. Task 007B explicitly requests advisory feasibility.
Schema, finite values, track identity, monotonic progress, periodic seam, coordinate/geometry
consistency, forward-domain validity, physical corridor, 0.08 m margin and global 0.5–6 m/s speed
validity remain rejection conditions. Conservative lateral-acceleration, geometric steering/rate,
and acceleration/braking gates become reported warnings. No failed reference is repaired.

Serialized speed polynomials validate coefficient shape/finiteness, continuity, seam, every
cubic extremum against the speed domain, and agreement with CSV samples. Roundoff allowance
at the speed cap is 1e-12 m/s. This does not authorize a physical-domain change.

## Frozen nominal-state approximation

Control still constructs vx=vref, vy=0, r=vref*kappa_ref, supplied ey/epsi,
delta_ff=atan(0.30*kappa_ref), and absent a_ref=0. This geometric construction is not an exact
nonlinear equilibrium. Centerline curvature stays in Frenet dynamics and packet geometry;
racing curvature remains distinct. Neither reference-state construction nor terminal schedule
is redesigned as demand increases.

The NLP retains its existing numerical preview schedule. No new spline expression of
decision-state progress is introduced. Analysis queries Planning at each predicted progress
and records preview-versus-node curvature differences. A 10 ms nominal-state defect uses two
independent 5 ms plant steps and compares against the next geometric nominal at its nominal
Frenet progress rate. This diagnoses the approximation, not a solver constraint violation.

## Study and selection protocol

- B0: measured three laps at gamma=1, lambda=0.
- B1: measured one-lap aggression screens at lambda=0.
- B2: gamma=1 weights 0,.1,.25,.5,1,2,4,8, with B0 supplying the zero baseline.
- B3: weights 1 and 2 at gamma=2 and 2.5.
- B4: startup plus two complete comparable laps for gamma=1 weights 1/2 and gamma=2 weights 0/1/2.
- Supporting runs: gamma=1, lambda=2 with zero and 150 ms injected planner latency.

Measured benchmarks run sequentially in fresh workers that configure the supported native
SINGLE backend before initialization. Tests, rendering and bulk analysis run only afterward.
Zero/injected cases support chronology; they are not primary performance claims.

Before B2, a 0.2% lap-time reduction was declared the operational definition of meaningful
benefit. Confirm on two complete comparable measured laps with both gains positive, then inspect
constraints, local tracking, solver behavior, timing and reserve. This is not a mathematical
safety threshold. No combined ranking score is used. Prefer the smallest eligible weight;
retain lower weights and all rejected/limited cases. No Q/R/W or slack retuning occurred.

Physical failure/fallback/boundary events or predicted |ey|>0.4 m / |epsi|>0.8 rad trigger review.
Those inspection triggers are not new controller constraints or proof of coordinate gaming.
Material predicted slack uses the existing feasibility-check scale of 1e-6 m; barrier values
around 1e-10 m do not demonstrate corner cutting. Coordinate audit checks denominator, heading,
lateral offset, physical path distance, oscillation and steering variation.

## Two first-class error layers

`planning_apex_nodes.csv` evaluates nominal Planning independently at EVERY predicted node's
own s_abs. It records state deviations, beta, slack, clearance, denominator and domain margins.
Those deviations measure nominal-intent adaptation, not codriver tracking error.

`telemetry.csv` uses vehicle-minus-active-packet errors at codriver release and the packet
actually available then. Physical states are sampled independently from the plant log; errors
are checked against logged errors within 1e-8, with heading wrapped. Actuator panels use the
command held at that same instant. Pending commands and application progress are retained
separately. The physical log remains authoritative for boundary/grip/held-command audits.

Node distributions weight nodes equally. Local means/RMS weight physical release intervals;
p95 is a sample quantile. Three-lap local results use laps 2/3; node results use solves released
during those laps. Constraint extremes and objective distributions retain the whole run.
One-lap cases are explicitly startup screens. Both error families remain available for reanalysis.

## Timing and review artifacts

The unchanged simulator advances physics while planners compute, keeps TVLQR tracking the prior
valid packet, and holds the previous actuator command during codriver computation. Independent
audits verify packet availability, interpolation, held commands, fixed deadlines, rate/actuator/grip
limits and solver nonoverlap. Planner misses and codriver misses remain distinct.

Preview, solve, prediction, gain preparation, full planner preparation, codriver components,
CPU core-seconds per physical second, iterations, deadlines and RSS are reported separately.
Measured timing is not an exact CI gate. Full-trend dashboards include sector shading, objective
groups, both error layers and sideslip. No difficulty index or controller switching is constructed.

## Scoped selection and high-demand rejection

Lambda=1 fails the predeclared benefit threshold on complete conservative laps. Lambda=2 meets
it, with about 0.362% improvement at gamma=1, and is selected only for that experimental scope.
Neither lambda=1 nor 2 improves the mean complete-lap result at gamma=2. Default lambda remains 0.

At gamma=2.5, lambda=1 produces sustained planned lateral/heading oscillations and a slower lap
than lambda=0. TVLQR mostly follows those oscillations. Lambda=2 uses about 27 mm predicted
tracking-margin slack; physical clearance falls below 80 mm while remaining inside the boundary.
Both are rejected. Escalation stops there without modifying the objective, state construction,
slack penalties or codriver. This is not a universal near-limit operating envelope.

The rejected cases have healthy denominators and progress/distance ratios near or below one;
there is no demonstrated near-singular coordinate-progress exploitation. Oscillation, large
heading/sideslip and slack remain unacceptable even without that specific failure. Frozen
preview, geometric nominal states, short horizon, local nonlinear solutions and closed-loop
timing are possible contributors. The experiment does not isolate a unique cause.
