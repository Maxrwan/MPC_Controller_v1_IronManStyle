# Tracking NMPC and computational latency — Task 006

> Task 006.1 update: racing-development composition now explicitly selects
> `SmoothCombinedGripTire` and normal-load proportional longitudinal allocation in both
> NumPy plant and CasADi prediction. The linear law and its legacy constructor defaults
> remain available for reference regression. Statements below about unlimited force or
> diagnostic-only mu describe that historical linear selection. See
> [GRIP_LIMITED_TIRE_SPEC.md](GRIP_LIMITED_TIRE_SPEC.md) for the current grip physics,
> domain reserve, diagnostics and limitations. No body/Frenet equations changed.


## Purpose and architecture

Task 006 establishes constrained tracking, solver reliability and measurable computation
latency. It does not optimize lap time, progress, racing line, energy or opponents. Physical
plant remains the unchanged NumPy DynamicBicycle from Task 004. Canonical SI state is
[vx,vy,r,e_psi,s_abs,e_y], control [delta,a_cmd], positive lateral quantities point left.
Task 005 baseline behavior and all track geometry/progress algorithms remain unchanged.

- control/mpc/symbolic_model.py independently transcribes the approved equations in CasADi.
- preview.py evaluates ordinary numeric track geometry outside the NLP.
- cost.py defines costs and cached terminal DARE matrices; warm_start.py shifts primal data.
- problem.py builds the multiple-shooting NLP and bounds once, then supplies numeric data.
- controller.py composes preview, guesses, injected Solver and application-time fallback.
- optimization/base.py retains a backend-neutral Solver/SolverResult and adds numeric
  NLPRequest plus statistics. optimization/solvers/ipopt.py owns all IPOPT calls/options.
- simulation/runner.py retains Task 005 synchronous behavior by default. Explicit latency
  configuration selects the generic simulation/timing.py event loop, not an MPC simulator.
- simulation/latency_metrics.py calculates physical-time-weighted metrics on irregular events.

MPCController neither owns nor calls a physical plant object. make_mpc is a composition
factory; alternative adapters can implement Solver.solve(NLPRequest). Prediction and plant
parameters may differ later; initial parity deliberately uses the same synthetic parameters.

## Symbolic equations and domain

Parameters are validated VehicleParameters constants baked into an independently constructed
symbolic graph; curvature is an interval parameter. With L=lf+lr, gravity9.81 m/s²:

    alpha_f = delta-atan2(vy+lf*r,vx)
    alpha_r = -atan2(vy-lr*r,vx)
    Fzf0=m*g*lr/L; Fzr0=m*g*lf/L
    Fzf=Fzf0-m*a_cmd*h/L; Fzr=Fzr0+m*a_cmd*h/L
    Fyf=Cf*(Fzf/Fzf0)*alpha_f; Fyr=Cr*(Fzr/Fzr0)*alpha_r
    dvx=a_cmd+r*vy
    dvy=(Fyf+Fyr)/m-r*vx
    dr=(lf*Fyf-lr*Fyr)/Iz
    D=1-kappa*e_y
    ds=(vx*cos(e_psi)-vy*sin(e_psi))/D
    de_psi=r-kappa*ds
    de_y=vx*sin(e_psi)+vy*cos(e_psi)

No force rotation, slip approximation, clipping, saturation, friction circle, or speed
regularization is introduced. Cf/Cr are axle aggregates. Symbolic evaluation itself does
not raise Python domain errors; the NLP enforces hard domain constraints. IPOPT trial
iterates can still be infeasible; invalid/nonfinite final results are rejected.

## Prediction integration and parity

Physical plant: RK4 steps at most5ms. Prediction: five classical RK4 substeps of10ms per
50ms shooting interval, with held U and held preview curvature. This is a separate CasADi
RK4 graph, not symbolic values passed into NumPy integration. All four evaluation states
of every substep are exposed for domain constraints. Shooting nodes also have guards.

Heading remains locally unwrapped inside the NLP for smooth differentiation; the plant
retains canonical post-step wrapping. Tracking operates far from the heading branch cut.
s_abs is never wrapped in either state. Geometry queries wrap progress normally.

Derivative parity compares independently implemented equations. Integrator parity uses a
constant-curvature local chart on BOTH implementations, because changing real-track
curvature versus a frozen preview interval would measure preview error, not equation parity.
Tests also compare prediction refinement to independent DOP853 integration. Actual closed-loop
validation always uses the real periodic spline and Task 004 plant, never the test chart.

## Preview and references

At release generate N+1 numeric samples. Start s_nom[0]=sampled s_abs, then advance
s_nom[k+1]=s_nom[k]+T*v_ref(s_nom[k]). Query wrapped track geometry at each position.
Preview rows: curvature,left_width,right_width,v_ref,vy_ref,r_ref,delta_ff.
Curvature is constant over each50ms prediction interval; widths/references are node values.
No symbolic SciPy calls. The nominal preview does not move with optimized s_abs, sideslip,
lateral offset or latency. No latency compensation is implemented.

Reuse Task 005 steady linear cornering references at v_ref and preview curvature:

    r_ref=v_ref*kappa
    vy_ref=v_ref*kappa*(lr-m*v_ref²*lf/(L*Cr))
    delta_ff=L*kappa+m*v_ref²*kappa/L*(lr/Cf-lf/Cr)

Use e_y_ref=0 and **e_psi_ref=0**, exactly as specified for Task 006. This supersedes the
Task 005 handoff's unadopted proposal of sideslip-compensated heading reference. Those
references need not form an exact nonlinear Frenet equilibrium. No s_abs tracking cost
or progress reward exists. Constant and progress-callable speed providers are supported.

## Multiple shooting and exact dimensions

Default T=.05s, N=20, horizon1s, all20 input decisions independent. Variables are X(6,21),
U(2,20), epsilon(2,21), concatenated column-major:126+40+42=208 variables.
Numeric parameters: sampled state6, actual prior input2, preview147, terminalP16 =171.

Equalities: X0=x_sample (6), X[k+1]=F_RK4(X[k],U[k],preview[k]) (120), total126.
General inequalities: track42, steering increments20, node-domain42, RK4-stage-domain800,
axle loads40, total944. Total g size1070. Variable box bounds are additional, not counted
as general inequalities. For each nonterminal stage ordering is track2, node-domain2,
steering increment1, loads2, internal stage domains40; terminal contributes track2/domain2.

## Costs and terminal mapping

    e=[vx-vref,vy-vyref,r-rref,e_psi,e_y]
    uref=[delta_ff,0]
    stage=e'Qe+(u-uref)'R(u-uref)+(u-u_previous)'W(u-u_previous)
    Q=diag(4,4,1,100,100)
    R=diag(25,1)
    W=diag(1,0.1)

Q/R use the supplied Bryson scales. W is a conservative synthetic incremental-command
penalty, not a time derivative penalty; no division by T and no automatic tuning. Sum stage
costs without multiplying by T. First increment uses the actuator command actually held at
solve release; it remains held throughout that computation. Later increments use prior U.

At every node including terminal, add 10000*sum(epsilon)+100000*sumsqr(epsilon), with slack
in metres. Both finite penalties are explicit. Every strictly positive optimized slack is
flagged as a violation, including tiny interior-point remnants; no reporting threshold hides
it. A separate count above1micrometre distinguishes magnitude, without redefining zero.
Physical plant boundary violations are monitored separately and cannot be inferred from
predicted slack alone.

Terminal cost uses z=[e_y,e_psi,vy-vyref,r-rref] and z'P(vref_terminal)z+4*(vx-vref)².
P comes from the unchanged Task 005 lateral Q/R and its100Hz discrete model/DARE at1/2/3m/s.
Interpolate P linearly, clamping its scheduling speed only. Positive-definite matrices retain
positive definiteness under convex interpolation. No terminal equality/set or stability
claim; using the baseline's100Hz P for a20Hz NMPC is explicitly provisional.

## Constraints

Hard configured synthetic actuator boxes: delta±.4rad; a_cmd[-3,+2]m/s². Synthetic steering
rate1rad/s means |delta[k]-delta[k-1]|<=.05rad, including U0 versus actual previous steering.
No continuous actuator dynamics are added. This is an increment constraint on nominal
50ms prediction intervals, not an assertion of a continuously differentiable actuator.

Soft node track bounds, using positive-left convention:

    e_y <= left_width + epsilon_left
    e_y >= -right_width - epsilon_right
    epsilon_left,right >= 0

Hard domain constraints at shooting nodes AND every RK4 derivative-evaluation state:
.5<=vx<=configured maximum_speed6m/s; 1-kappa*e_y>=.01. The denominator margin exceeds
Task 004's .001 guard. Axle loads>=1e-6N for every input, exceeding the plant's1e-9N guard.
All X s_abs>=0. No invented friction/slip-force limit. Bounds and constraints are validated
again on the returned optimizer result, within numerical feasibility tolerance1e-6.

## Solver and warm starting

CasADi's IPOPT adapter is constructed once. Defaults:

    print_time=False, error_on_fail=False
    ipopt.print_level=0, ipopt.sb='yes', ipopt.max_iter=100
    ipopt.tol=1e-7, ipopt.acceptable_tol=1e-6
    ipopt.constr_viol_tol=1e-7, ipopt.bound_relax_factor=0
    ipopt.honor_original_bounds='yes'

Other settings use bundled IPOPT defaults. A high-resolution monotonic perf_counter timer
encloses the actual backend call, excluding graph construction, preview and postprocessing.
Success requires backend success, finite decision/constraint vectors and primal violation
<=1e-6; the controller independently verifies the returned candidate. Log status, objective,
iterations, timing, primal infeasibility and raw backend statistics, including failures.
No optimizer output is applied merely because a success string was returned.

Cold guess rolls the symbolic model forward with bounded/rate-limited feedforward and
zero acceleration. After success cache X/U/slacks. Shift each one stage, duplicate tail,
and overwrite X0 with the new sample. This is a primal warm start only; no dual warm start
or ipopt.warm_start_init_point option is claimed. A long missed-release interval still
shifts one stage as requested; this can worsen the initial guess. Failure clears the cache.
Warm/cold timing is logged observationally, not asserted faster on every solve.

## Failure and application-time fallback

compute_control returns a pending candidate plus success diagnostics. A failed solve's
placeholder is the prior command, NEVER silently applied as an optimizer success. Runner
must use finalize_control after latency has elapsed, with the CURRENT state and held input.
An application callback requires explicit latency mode, including zero.

On failure, check current state finite, speed within baseline1–3m/s, CG within track bounds,
and valid Frenet geometry. Then call the unchanged BaselineController configured at20Hz,
with a copied parameter object specifying the synthetic1rad/s command-rate limit; synchronize
its previous steering to actual applied steering. This adds no new baseline law. Reject
invalid command/load/state limits and terminate cleanly if no eligible fallback exists.
Do not invent an emergency control. Log fallback separately. Solver success also receives
application-time domain/command checks, but no state prediction or compensation.

## Separate clocks and event semantics

There are three different quantities: physical simulation time, fixed nominal release clock,
and measured solver wall duration. CPU process time is not substituted for wall duration.
Total controller wall duration (including preview/etc.) is also logged separately. For this
specified task measured physical latency equals solver duration alone; preprocessing latency
is not included and remains a stated limitation.

At nominal release k*T, sample current plant state and actual previous input. Execute the
synchronous solve to obtain its duration and pending result. **Before making that result
available**, integrate all physical time up to completion under the previous held input.
This serial discrete-event replay is causally equivalent to concurrent simulation with held
input: the solve depends only on its release sample and no intermediate plant feedback.
It does not require threads or sleeping, and never pauses simulated physics during latency.

Modes: zero physical latency; measured latency=actual solver duration; injected latency=
configured nonnegative deterministic duration while still recording real wall solve time.
Plant steps remain at most5ms. Exact release/completion times split grid intervals when
needed; measured latency is never rounded down or up to a grid. Post-event state rows record
the input acting on the following interval, including additional off-grid event samples.

Nominal releases occur on the fixed k*T grid. A single pending solve makes the controller
busy; every release while busy is counted as skipped. At an exact completion/release tie,
the release sees busy first and is skipped. Apply the result, then wait for the strictly
subsequent nominal release. Thus60ms injection approaches10Hz and100ms approaches6.67Hz.
No overlapping solves, backlog replay, or conversion to instantaneous behavior occurs.

Initial held actuator command is explicitly zero in these experiments for all comparisons.
Terminal physical duration/lap events cancel any still-pending application; logs retain its
sample/status and scheduled completion, with completed/applied flags false. No new release
occurs at the run's terminal endpoint. Effective update rate is number of applied results
(including fallback) divided by physical run duration; the initial t=0 application can cause
a small endpoint counting excess over20Hz in a zero-latency run ending between releases.

## Staleness and performance metrics

At completion record x_apply-x_sample in all canonical channels, without wrapping s_abs.
The requested raw heading difference is used; heading branch-cut crossings would need
careful interpretation, but none are expected in the tested small-error regime.

    index=sqrt((delta_vx/.5)²+(delta_vy/.5)²+(delta_r/1)²
               +(delta_e_psi/.1)²+(delta_e_y/.1)²)

This dimensionless normalized control-state index excludes progress and is NOT physical
distance. Report progress drift separately. Report mean/p50/p95/max solve time, latency
relative to50ms, below/above-period fractions, iterations, warm/cold statistics, mean/p95/max
staleness, mean/max absolute lateral/heading/progress drift, deadlines and effective rate.

Time-weight RMS tracking errors using trapezoidal integration on physical timestamps,
so extra solver events do not receive excess sample weight. Apply the SAME metric to LQR
100Hz, LQR20Hz and NMPC. Use full-run and fixed t>=5s windows. Actuator effort is integral
of squared held commands; also report steering total variation. Lap times interpolate
complete seam-to-seam crossings. Absolute progress never resets. Track violations count
recorded samples; for irregular measured events that count is not a duration.

Compare every oval delay with zero latency: RMS ey/heading/speed changes, mean completed
lap-time change, squared-input effort, max/summed predicted slack and boundary counts.
Counts/sums of slack over predictions depend on update count; use peak slack and actual
boundary events when interpreting different update rates.

## Experiments, artifacts and reproducibility

Same Task 005 radius5m/64point circle with widths.6/.9m, and7x3m/72point oval with widths.3/.5m.
Same synthetic vehicle and reference2m/s, same initial cornering vy/r and zero heading/lateral
errors. Nominal circle/oval NMPC run two laps at zero latency. Oval injected delays are
0,10,25,45,60,100ms, plus measured latency. Compare native100Hz and rate-matched20Hz LQR
on both tracks; latter recomputes its discrete gains at.05s through the existing constructor.
Baseline steering rate remains unconfigured in those comparisons; this constraint difference
is explicit, not attributed solely to controller architecture. Disturbance cases reuse all
Task 005 offsets. A large but in-track ey=.59m circle seed exercises active steering constraints.
Additional circle1/3m/s runs exercise references at endpoint speeds.

scripts/run_mpc_baseline.py writes states.csv, controls.csv, solver_events.csv,
predictions.jsonl (states/inputs/slacks/preview/raw solver statistics), summary.json and
14-panel diagnostics.png per case under results/mpc_baseline. Root suite_summary.json
and latency_sweep.png aggregate comparisons. --plots-only regenerates images from logs.
Deterministic injected simulations repeat state/timing events; measured wall times themselves
are nondeterministic and must never become exact CI assertions. Thread-count environment
variables and host metadata accompany measured experiments; timing is host/load dependent.

## Limitations and Task 007

Prominent limitations: frozen nominal track preview; NO latency compensation; synthetic
limits; linear UNSATURATED tires; perfect state. Additional limits: no footprint/robustness,
no formal terminal stability guarantee, raw-heading reference mismatch, no hard real-time
solver deadline cancellation, no dual warm start, preprocessing latency excluded, and finite
RK4-stage checks rather than continuous-time constraint guarantees.

Task 007 should retain the independent models, solver abstraction, warm-start infrastructure,
constraint/failure logging, timing runner and mandatory latency tests. Progress/minimum-time
objectives, reference-speed treatment, terminal progress reward, horizon and free-track use
need new specifications. Before exploiting grip for racing, introduce an approved tire-force
limit/nonlinear tire model; unsaturated linear tires permit nonphysical forces and are not
adequate to validate unconstrained time-optimal racing. No Task 007 component is implemented.

## Task006.1 matched grip development configuration

Use MPCConfig(tire_physics=RACING_TIRE_PHYSICS) and the same explicit tire selection on
DynamicBicycle. The experiment script selects this by default and writes results/mpc_grip.
208 variables,126 equalities,984 general inequalities (40 additional axle longitudinal
utilization constraints),1110 total g,171 parameters. Box bounds additionally ensure
longitudinal/load trial-domain validity. No costs, reference utilities, terminal matrix,
horizon, solver settings, warm-start or latency semantics were tuned or redesigned.
The original linear numbers/results remain reproducible through explicit linear selection.
Task006.2 is the next step; Task007 remains unimplemented.


## Task006.2 synchronous characterization

The20Hz,N20,5-substep grip configuration remains the reference; the library default has not
been silently replaced by a study winner. Grouped cost multipliers, ordinary backend options,
explicit N/dt/substeps, and detailed nested controller timings support the staged experiments
in NMPC_PARAMETER_STUDY.md. The event runner supports exact15Hz fractional release times;
its legacy grid mode remains unchanged. Physical measured latency is still backend solver
wall time, so it excludes separately reported preview/packing/validation overhead.

The NLP and backend are constructed once per controller. Prediction logs now carry absolute
node timestamps, solve-start state, completion state/time and remaining nominal horizon.
These exports do not implement trajectory consumption or latency compensation. Selected
candidate JSON and the machine-readable experiment database are the Task006.3 inputs.
Task006.3 will add asynchronous planning and a high-rate codriver; Task006.4 subsequently
compares a small linear MPC codriver with LQR/TVLQR. Neither is implemented by006.2.
