# Codex handoff — Task 006

## Implemented scope and boundaries

Tracking nonlinear MPC using CasADi/IPOPT, direct multiple shooting, hard actuator/domain
constraints, soft track constraints, shifted primal warm starts and application-time baseline
fallback. Generic simulation timing models zero, measured and deterministic injected latency,
held previous control, exact completion events, skipped fixed releases and state staleness.
No racing objective or latency compensation. Task 007 remains unimplemented.

Read AGENTS.md, NMPC_BASELINE_SPEC.md, MPC_FORMULATION.md and ADRs059–080. The physical
NumPy DynamicBicycle, canonical [vx,vy,r,e_psi,s_abs,e_y], [delta,a_cmd], left-positive
conventions, geometry, continuous progress and Task005 baseline equations are unchanged.
All vehicle/track/control limits are synthetic. Generic physical APEX values remain null.

## Components and API

- control/mpc/symbolic_model.py: independent SymbolicBicycle.derivative(x,u,kappa) and
  rk4(dt,substeps), exposing internal RK4 evaluation states for validity constraints.
- preview.py: nominal reference-speed progress preview, seven rows and N+1 nodes.
- cost.py: Q/R/increment/slack costs and cached100Hz baseline DARE terminal matrix schedule.
- problem.py: MPCConfig and MPCProblem, symbolic NLP, exact bounds, pack/unpack and guesses.
- warm_start.py: one-stage primal X/U/slack shifting, sampled X0 replacement.
- controller.py: MPCController with injected Solver, application-time finalize_control,
  diagnostics/prediction snapshots; make_mpc is the IPOPT composition factory.
- optimization/base.py: backward-compatible SolverResult statistics, numeric NLPRequest.
- optimization/solvers/ipopt.py: sole backend call/options/high-resolution solve timer.
- simulation/timing.py: LatencyConfig and generic discrete-event runner implementation.
- simulation/runner.py: preserves the Task005 path when latency=None; optional finalizer,
  prediction diagnostics and initial held input. RunResult adds events/predictions/timing.
- simulation/latency_metrics.py: physical-time-weighted tracking/effort and latency summaries.

Use RunConfig(dt_control=.05,latency=LatencyConfig('zero'|'measured'|'injected',seconds)),
with controller diagnostics/reset/finalize and prediction callbacks for NMPC. An application
callback requires explicit latency mode even when zero. Plant integration remains at most
.005s, split only at exact off-grid release/completion events. Initial held control is zero.
The physical plant is never owned/called by the controller.

## Mathematics/configuration

Approved Task004 body/slip/load/Frenet equations are independently transcribed, not changed.
Prediction interval .05s = five .01s RK4 substeps. N20, horizon1s. Nominal preview advances
by reference speed and freezes curvature within each interval. Local predicted heading is
unwrapped for differentiability; real plant post-step wrapping remains unchanged.

Tracking error [vx-vref,vy-vyref,r-rref,epsi,ey], Q=diag(4,4,1,100,100), input reference
[delta_ff,0], R=diag(25,1), increment W=diag(1,.1). No s_abs cost/progress reward. Preserve
requested epsi_ref=0; the previous handoff's alternative heading reference was NOT adopted.
Terminal z=[ey,epsi,vy-vyref,r-rref], z'Pz+4*speed_error²; P uses the Task005100Hz DARE
construction at1/2/3m/s and convex interpolation. Provisional, no terminal-stability proof.

Left/right track slacks at all21nodes:10000*sum(epsilon)+100000*sum(epsilon²). Every positive
slack is logged, including interior-point remnants; counts above1µm are secondary diagnostics.
Hard steering±.4rad, acceleration[-3,+2]m/s²; synthetic steering increments±.05rad relative
to actual prior command and within predictions. Hard .5<=vx<=6, FrenetD>=.01 at shooting
nodes and all400 RK4 evaluation states, loads>=1e-6N per input, and nonnegative s_abs.
No friction-circle/nonlinear tire saturation was introduced.

Default NLP:208 variables (126 state,40 input,42 slack),126 equalities,944 general
inequalities,1070 total g entries; variable box bounds additional.171 numeric parameters.
IPOPT max_iter100,tol1e-7,acceptable_tol1e-6,constr_viol_tol1e-7,bound_relax_factor0,
honor_original_bounds=yes; print output disabled,error_on_fail=False. Other backend defaults
unchanged. Success requires finite feasible output, independently checked by the controller.

Warm start shifts primal X/U/slacks once even after missed releases. No dual warm start.
Failure clears cached trajectories. At application time, failed MPC can use the unchanged
baseline configured at20Hz with a copied1rad/s rate bound only if current speed1–3m/s,
CG within track and model domain valid. Otherwise terminate cleanly. No emergency law.
Missing, nonnumeric, nonfinite or infeasible claimed-success solutions are rejected.

## Timing semantics

Solver wall duration encloses only actual IPOPT call, not preview/build/postprocessing.
Total controller wall duration is separately logged; measured physical latency intentionally
uses solver duration alone. This exclusion is a limitation, not a hardware timing guarantee.
A synchronous solve creates a pending result, then physical time is replayed under old input
before application. This models uninterrupted vehicle motion without threads or sleeping.

Fixed releases at k*.05. Busy releases are missed. At a release/completion tie, busy wins;
apply then wait for strictly subsequent release.60ms tends to10Hz;100ms tends to6.67Hz.
No overlapping optimization or implicit reset at a seam. Pending results at run end remain
logged but unapplied. Effective rate=applied results/physical duration, with small endpoint
counting effects for nonintegral-duration runs.

Staleness logs all six raw x_apply-x_sample components. Normalized index excludes s_abs
and uses [.5,.5,1,.1,.1] scales for vx,vy,r,epsi,ey. It is NOT physical distance. Raw heading
difference would require care at angle branch crossings, outside tested tracking behavior.

## Validation and experiments

NumPy/CasADi gate:1000 deterministic random cases, two parameter sets including asymmetric
geometry/stiffness. Derivative max channel errors [0,1.776e-15,2.842e-14,0,0,0]. Five-step
50ms RK4 max errors [0,2.776e-17,4.441e-16,8.535e-16,0,4.857e-17]. Fixed curvature on BOTH
sides isolates parity from preview approximation. Real closed-loop runs use real splines.
DOP853 refinement: largest channel error (yaw rate)1.2567e-5,6.6301e-7,3.8087e-8 at5/10/20
substeps; ratios18.95/17.41 support fourth-order convergence. See parity.json for each channel.

Full regression:350 passed in594.39s. Final focused checks additionally cover malformed
solver output, actual forced IPOPT iteration failure, warm-cache reset and repeated real-plant
injected latency. Ruff and locked dependency sync are checked before final handoff.

Experiments use unchanged Task005 circle/oval, same vehicle/reference/initial cornering
vy/r; initial epsi/ey zero unless disturbed. Zero-latency NMPC, LQR100Hz and LQR20Hz each
run two laps on both tracks. Oval injection0/10/25/45/60/100ms plus measured latency.
Five required disturbances and ey=.59m active-steering case run12s. Additional circle1/3m/s.
Baseline comparisons retain their originally unconfigured steering-rate limit; NMPC adds
its specified constraint. This difference is explicit. All metrics use the same physical-time
weighting, with full-run and fixed t>=5s results. Failed runs have no invented settled metrics
or lap time. Common-duration comparisons against zero avoid mixing different observation windows.

## Artifacts and scripts

Root results/mpc_baseline: parity.json, warm_start_benchmark.json, suite_summary.json,
verification.json, validation.txt and latency_sweep.png. Each named case contains states.csv,
controls.csv, solver_events.csv (NMPC), predictions.jsonl (NMPC), summary.json, diagnostics.png.
Prediction logs include preview, X/U/slack trajectories and full backend statistics.

Scripts: check_mpc_parity.py; run_mpc_baseline.py; benchmark_mpc_warm_start.py;
audit_mpc_results.py. --plots-only reuses existing logs. Audit validates old-command holding,
step durations, sampled/application states, staleness arithmetic and hard command bounds.
See measured-results section below for outcomes; raw logs remain authoritative.

## Known limitations and next task

Frozen nominal-progress preview, no latency compensation, synthetic physical limits,
unsaturated linear tires and perfect state are central limitations. No footprint, model
uncertainty, formal terminal guarantee, dual warm start, preprocessing-latency inclusion or
hard real-time qualification. Valid predictions from stale samples do not guarantee physical
constraints after delayed application. The plant guards remain strict; failure is recorded.

Task007: retain independent model/solver/constraint/timing/logging infrastructure. Specify
new progress/minimum-time objective and reference/horizon changes. Do not treat this linear
unsaturated tire plant as credible at the grip limit: approve a tire-force limit/nonlinear
tire model before making physically meaningful racing-performance claims.

| Task007 decision | Why it matters | Proposed development starting point |
|---|---|---|
| Progress objective | Defines racing incentive | Reward horizon progress s_N-s_0; preserve unwrapped progress. |
| Minimum-time approximation | Fixed-horizon progress is not exact lap-time minimization | Start fixed-time progress reward and evaluate complete lap times explicitly. |
| Centerline vs free corridor | Determines racing-line freedom | Permit lateral freedom inside measured/synthetic track bounds after footprint margin decision. |
| Speed reference | Fixed2m/s tracking conflicts with racing | Replace speed tracking by agreed speed/domain caps and effort regularization. |
| Terminal progress reward | Can duplicate telescoping stage reward | Use one terminal progress reward initially; do not double-count equivalent stage increments. |
| Horizon strategy | Preview versus solver cost | Compare1s and2s horizons only after profiling; retain explicit latency for both. |
| Tire/grip constraints | Unsaturated tires permit nonphysical optimum | Approve axle force limits or validated nonlinear tires first; combined slip needs longitudinal allocation specification. |
| Track margin | CG bounds omit body clearance | Request width/length/uncertainty; optional synthetic.05m margin must not be called measured. |
| Racing-line emergence | Requires geometry consistent with decision progress | Couple preview/track representation to optimized progress; test seam and geometric fidelity. |
| Objective scaling | Balances speed, control and violation penalties | Normalize progress by horizon/reference distance, retain explicit actuator/constraint terms; no automatic tuning. |
| Lap-time benchmark | Avoids unfair improvement claims | Same plant/track/start/constraints, full laps, report violations and failed runs beside times. |
| Latency-aware racing evaluation | More aggressive racing may amplify stale-state failures | Retain zero/measured and0/10/25/45/60/100ms cases; agree computation budget before hardware claims. |

All proposals are unadopted algorithm choices. Real mass/inertia/CG/stiffness/grip, actuator
limits/rates/delays, dimensions, sensor and computation timing require physical measurements.
No Task007 code was implemented.

## Measured results — completed Task006 experiments

Metrics are physical-time weighted. Full-run windows end at each recorded duration; settled means t>=5s and is unavailable for early failures. Timing is host dependent (Darwin arm64, Python3.12.14, single BLAS/OMP thread).

| Case | Duration s | Full RMS ey m | Full RMS heading rad | Full RMS speed m/s | Settled RMS ey m | Lap times s | Boundary samples | Max predicted slack m |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| circle_1mps | 62.500 | 0.0001533772 | 0.02548095 | 0.005037133 | 0.00012008490113305514 | 31.25034, 31.24832 | 0 | 9.09155e-11 |
| circle_3mps | 21.005 | 0.0006645269 | 0.009837962 | 0.00829856 | 5.552207595196195e-05 | 10.50040, 10.50079 | 0 | 9.09155e-11 |
| circle_lqr100 | 31.315 | 0.01440242 | 0.01206766 | 0.001733264 | 0.014588330574353504 | 15.65271, 15.66095 | 0 | 0 |
| circle_lqr20 | 31.310 | 0.01499079 | 0.01206447 | 0.001732931 | 0.015184946944270474 | 15.65090, 15.65908 | 0 | 0 |
| circle_zero | 31.320 | 0.0002255646 | 0.01210998 | 0.006155258 | 9.619255679545553e-05 | 15.65955, 15.65839 | 0 | 9.09155e-11 |
| combined | 12.000 | 0.01256288 | 0.01861713 | 0.008699875 | 9.6160400032837e-05 | none | 0 | 9.09155e-11 |
| constraint_active | 12.000 | 0.109122 | 0.07090008 | 0.126119 | 9.639362082969113e-05 | none | 0 | 9.09156e-11 |
| ey_negative | 12.000 | 0.01801053 | 0.01479406 | 0.006056413 | 9.63403185289671e-05 | none | 0 | 9.09155e-11 |
| ey_positive | 12.000 | 0.01705897 | 0.02045199 | 0.01084749 | 9.614720623706336e-05 | none | 0 | 9.09155e-11 |
| heading_negative | 12.000 | 0.002024266 | 0.01293305 | 0.005884969 | 9.620896424210372e-05 | none | 0 | 9.09155e-11 |
| heading_positive | 12.000 | 0.001759507 | 0.01286754 | 0.00617599 | 9.617511330972034e-05 | none | 0 | 9.09155e-11 |
| oval_100ms | 1.770 | 0.2101894 | 0.4604832 | 0.4947106 | N/A | none | 0 | 0.210421 |
| oval_10ms | 32.585 | 0.006369408 | 0.01736593 | 0.01459565 | 0.005508754592942355 | 16.31528, 16.26952 | 0 | 9.09173e-11 |
| oval_25ms | 32.600 | 0.007677818 | 0.01879529 | 0.01468721 | 0.00639385702441859 | 16.32301, 16.27204 | 0 | 9.09178e-11 |
| oval_45ms | 32.605 | 0.009366913 | 0.02182739 | 0.01502801 | 0.00742399792063254 | 16.32935, 16.27467 | 0 | 9.09172e-11 |
| oval_60ms | 1.600 | 0.1656606 | 0.332994 | 0.4986753 | N/A | none | 30 | 0.0963942 |
| oval_lqr100 | 32.545 | 0.01605024 | 0.0136567 | 0.02306413 | 0.0163192240589785 | 16.27164, 16.27183 | 0 | 0 |
| oval_lqr20 | 32.545 | 0.01680216 | 0.01339262 | 0.0233744 | 0.016819367084128012 | 16.27103, 16.27246 | 0 | 0 |
| oval_measured | 1.700 | 0.2205462 | 0.482727 | 0.5138876 | N/A | none | 0 | 0.200683 |
| oval_zero | 32.580 | 0.005469545 | 0.01661413 | 0.01460213 | 0.004885135648261764 | 16.30958, 16.26764 | 0 | 9.09184e-11 |

### Timing and staleness

All suite MPC optimizations returned valid solutions, with zero solver failures/fallbacks. Nevertheless60ms,100ms and measured latency runs terminated at the unchanged low-speed guard, at1.60/1.77/1.70s. They completed no laps. Solver success is not delayed closed-loop safety.

| Case | Solve ms mean/p50/p95/max | Iterations mean/max | Effective Hz | Missed/nominal | Staleness mean/p95/max | Mean/max abs ey drift m | Mean/max abs heading drift rad | Mean/max progress drift m |
|---|---|---|---:|---|---|---|---|---|
| circle_1mps | 104.228/102.818/111.583/331.62 | 15.008/25 | 20 | 0/1250 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| circle_3mps | 60.0291/58.6455/67.9278/235.419 | 8.03088/19 | 20.0428 | 0/421 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| circle_zero | 66.0279/65.1783/68.6002/163.101 | 10.0175/21 | 20.0192 | 0/627 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| combined | 71.9037/71.0124/77.6002/165.567 | 10.0417/20 | 20 | 0/240 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| constraint_active | 76.2667/72.6824/86.48/209.076 | 10.1083/24 | 20 | 0/240 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| ey_negative | 81.3504/80.6747/83.0439/186.524 | 10.0625/20 | 20 | 0/240 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| ey_positive | 83.9219/81.2329/92.0141/191.517 | 10.05/21 | 20 | 0/240 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| heading_negative | 71.0738/69.797/74.26/153.516 | 10.05/20 | 20 | 0/240 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| heading_positive | 81.0923/80.9756/87.612/198.962 | 10.0417/20 | 20 | 0/240 | 0/0/0 | 0/0 | 0/0 | 0/0 |
| oval_100ms | 157.75/114.303/295.352/371.59 | 20.0833/44 | 6.77966 | 24/36 | 1.22657/1.90395/1.94127 | 0.0525221/0.107504 | 0.0900988/0.174622 | 0.143644/0.199525 |
| oval_10ms | 76.4962/72.0321/88.1391/295.934 | 9.66258/23 | 20.0092 | 0/652 | 0.003639/0.00754292/0.530025 | 7.52297e-05/0.00178538 | 0.000174536/0.0107253 | 0.0200618/0.0204953 |
| oval_25ms | 84.6241/80.367/97.792/310.364 | 9.66258/23 | 20 | 0/652 | 0.0105427/0.0257271/1.02301 | 0.000223087/0.00537766 | 0.000505872/0.0282139 | 0.0501389/0.0512373 |
| oval_45ms | 82.7387/80.6503/97.3678/251.146 | 9.6876/23 | 19.9969 | 0/653 | 0.0272808/0.0766227/1.38507 | 0.000495219/0.0118789 | 0.00120366/0.0542327 | 0.0902253/0.0922584 |
| oval_60ms | 143.781/122.216/205.616/225.088 | 18.7647/30 | 10 | 16/33 | 0.644278/1.085/1.56014 | 0.026174/0.0504933 | 0.0414372/0.0912162 | 0.0946382/0.120067 |
| oval_measured | 127.176/98.7924/228.083/245.942 | 18.1538/37 | 7.05882 | 22/35 | 1.6232/3.18285/3.56072 | 0.0655904/0.225143 | 0.128194/0.236469 | 0.17316/0.365278 |
| oval_zero | 68.5112/65.8894/80.8047/293.727 | 9.64571/23 | 20.0123 | 0/652 | 0/0/0 | 0/0 | 0/0 | 0/0 |

Every positive slack is flagged, including about9.1e-11m interior-point remnants. No >1µm slack occurred in zero/10/25/45ms nominal cases.60/100/measured had5/3/2 solves above1µm. The60ms case had30 physical boundary-violating samples; other nominal latency cases had0. Steering-rate bounds activated8 times in the ey=.59m constraint case, with no physical boundary violation.

Cold versus warm oval: cold167.43ms/23iterations, subsequent warm mean68.36ms/9.63iterations; problems differ so this is observational. Six paired identical-NLP comparisons: cold194.36ms, warm192.17ms, both20iterations; no demonstrated iteration benefit.

Full tests:350 passed in594.39s. Final focused tests:54 passed in6.99s. Independent saved-trace audit:21cases,91229plant rows,14171applied updates. Audit checks exact held commands, application state, staleness, release accounting, steering increments and plant step limits. See validation.txt and verification.json.

### Reproduction commands

```sh
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle
env -u VIRTUAL_ENV uv sync --locked
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export XDG_CACHE_HOME=/private/tmp/apex-cache MPLCONFIGDIR=/private/tmp/apex-matplotlib
.venv/bin/pytest -q
.venv/bin/pytest -q tests/unit/test_mpc.py tests/unit/test_latency.py
.venv/bin/python scripts/check_mpc_parity.py
.venv/bin/python scripts/run_mpc_baseline.py --suite zero
.venv/bin/python scripts/run_mpc_baseline.py --track oval --mode measured --name oval_measured
.venv/bin/python scripts/run_mpc_baseline.py --suite latency
.venv/bin/python scripts/run_mpc_baseline.py --suite comparisons
.venv/bin/python scripts/run_mpc_baseline.py --suite disturbances
.venv/bin/python scripts/run_mpc_baseline.py --suite speeds
.venv/bin/python scripts/benchmark_mpc_warm_start.py
.venv/bin/python scripts/audit_mpc_results.py
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python scripts/run_mpc_baseline.py --plots-only
```
Rerunning measured latency changes wall-clock-dependent results. `--plots-only` regenerates figures and aggregate comparisons from existing logs. `change_vs_zero` uses matched physical windows; sweep lateral-error plot uses common0–1.6s window across all injected cases. Full-run tables deliberately retain each case duration.

### Matched-window changes relative to zero latency

Each row compares both controllers over0 to the listed window end. Effort is integral of squared held input. Slack change compares whole-run maxima.

| Case | End s | Delta RMS ey m | Delta RMS heading rad | Delta RMS speed m/s | Delta steering effort rad²s | Delta acceleration effort m²/s³ | Delta mean lap s |
|---|---:|---:|---:|---:|---:|---:|---:|
| oval_10ms | 32.58 | 0.0008996526 | 0.0007491519 | -1.179226e-05 | 0.0009262557 | 0.002765727 | 0.003793328 |
| oval_25ms | 32.58 | 0.002206325 | 0.002172614 | 6.584627e-05 | 0.002766122 | 0.008318693 | 0.008916472 |
| oval_45ms | 32.58 | 0.003893414 | 0.00520677 | 0.0004051973 | 0.007205327 | 0.0197442 | 0.01339704 |
| oval_60ms | 1.6 | 0.1516539 | 0.2901553 | 0.4826362 | 0.03191504 | 3.775422 | N/A |
| oval_100ms | 1.77 | 0.1968628 | 0.4196944 | 0.4794354 | 0.05846426 | 4.711339 | N/A |
| oval_measured | 1.7 | 0.2069522 | 0.4411315 | 0.4983114 | 0.07411306 | 4.713562 | N/A |
