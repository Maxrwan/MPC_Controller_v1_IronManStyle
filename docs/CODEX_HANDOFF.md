# Codex handoff — Task006.1

## Scope

Smooth combined-grip axle tire physics added to independent NumPy plant and CasADi
prediction, preserving linear reference and all Task006 costs, horizon and solver options.
Task006.2 solver optimization and Task007 racing objective are NOT implemented.
Prior measured results and implementation details remain in TASK006_HANDOFF.md and
results/mpc_baseline; this task saves new data in results/tire_model and results/mpc_grip.

## Start here

Read AGENTS.md, GRIP_LIMITED_TIRE_SPEC.md, NMPC_BASELINE_SPEC.md and ADR081–092.
Canonical state/control, body/Frenet equations, exact slip angles, existing load transfer,
track/progress and latency event semantics are unchanged. All physical parameters are
synthetic. Generic APEX vehicle YAML remains unknown/null.

## APIs and model selection

- models/tire/grip.py: SmoothCombinedGripTire(mu), evaluate_combined(...,fx),
  CombinedTireResult, TireForceValidityError. LinearAxleTire remains unchanged.
- models/vehicle/force_allocation.py: LongitudinalForceAllocation protocol and
  NormalLoadProportionalAllocation; no physical AWD claim.
- models/tire/config.py: TirePhysics; RACING_TIRE_PHYSICS explicit development selection.
- apex.config.load_tire_physics loads configs/models/*.yaml separately from vehicle values.
- DynamicBicycle(...,tire_physics=RACING_TIRE_PHYSICS) selects grip plant.
- MPCConfig(tire_physics=RACING_TIRE_PHYSICS) selects matched independent prediction.
- Low-level default constructors remain LINEAR for historical compatibility. New racing
  scripts explicitly select grip on both sides. Never mix selections unintentionally.
- run_mpc_baseline.py now defaults to grip and results/mpc_grip; --tire-model linear
  restores reference selection. --tire-config selects an explicit allocation/model YAML.

## Mathematical contract

Fx_total=m*a_cmd; Fx_axle=Fx_total*Fz/(Fzf+Fzr).
C_eff=C*Fz/Fz0; F_limit=mu*Fz; cap=sqrt(F_limit²-Fx²).
Fy=cap*tanh(C_eff*alpha/cap); utilization=hypot(Fx,Fy)/(mu*Fz).
Hard longitudinal reserve |Fx|/(mu*Fz)<=1-1e-6; excessive demand raises, never clips.
No hidden sqrt regularization. Mu must be explicitly positive. Current synthetic mu=1.

NLP adds40 longitudinal utilization constraints:208 variables,126 equalities,984 general
inequalities,1110 total g,171 numeric parameters. Per-stage load/friction acceleration
box intersections keep IPOPT trial controls in the valid square-root domain, with the
existing bound_relax_factor=0. No solver optimization or objective tuning.
Application-time validation rejects invalid optimizer/fallback longitudinal commands.

Force Jacobians are smooth and finite inside the reserved domain. The diagnostic force
norm is nondifferentiable at exactly zero force; it is not an NLP constraint/objective.
References and terminal matrices are still the Task005 linear low-slip design, not exact
grip-model equilibria; tracking changes are reported without automatic retuning.

## Logging and tests

All selected plant tire diagnostics are saved as tire_* state CSV columns. Existing solver
events/predictions preserve raw IPOPT evaluation counts/times, iterations and warm-start flags.
Construction times are instrumented separately from actual solve timing.
Tests cover envelope math, small-slip tolerance, invalid demand, load allocation, symbolic
parity/Jacobians, friction-safe NLP bounds and real grip-plant latency behavior. Existing
Task006 latency tests remain mandatory. Wall times are not exact test assertions.

## Interpretation and limitations

This is an engineering tanh envelope, NOT Pacejka/Fiala/Dugoff or a fitted real-tire model.
Axle aggregates, idealized allocation, no slip-ratio/wheel-speed dynamics, measured tire
parameters, temperature/wear, camber, lateral transfer, individual wheel loads or steering-
frame force rotation correction. Synthetic grip and perfect state; no latency compensation.
The constant-radius demand sweep uses linear-reference snapshots, not achieved steady
grip-model circles beyond feasibility. Tire-only a=6 curve does not change vehicle limits.

## Next task

Task006.2: reduce NMPC compute cost and computation-induced control latency. Retain
independent grip parity, hard domain, constraints, fallback and physical-time semantics.
Use timing_baseline.json for construction/solve/evaluation timing and derivative sparsity.
Inspect iterations, Hessian/Jacobian costs and preview/plant geometry separately; do not
attribute total experiment runtime to IPOPT. No horizon timing extrapolation is claimed.
Candidate changes require a new specification and controlled comparison, not hidden tuning.

## Early validation evidence

Full regression:371 passed in528.74s. Two subsequently added unit checks plus configuration/
integration coverage passed in a focused43-test run (4.70s). Final checks are recorded below.
1000-case independent parity: derivative max2.842e-14, forces1.776e-15N, utilization4.441e-16,
50ms RK4 max1.020e-15. Steering Jacobian central-difference discrepancy7.412e-9;12 tested
near-boundary/ordinary Jacobians finite. Small-slip relative loss at1e-5rad <=7.738e-10.
Scripted low demand max lateral trajectory difference1.210e-6m; high demand linear
utilization1.83486 versus grip0.95030. No grip bound exceedance in characterization.
R=2m equilibrium search accepts32 speeds from1 to4.1m/s, maxutilization0.93187; maximum
nonprogress state drift after0.5s8.296e-10. Roots at4.2–4.4m/s exceed steering limit and
are rejected, without claiming this proves global infeasibility.

The circle run overlapped the tail of regression tests: its timing is observational, not the
isolated nominal-oval timing benchmark. The oval timing run starts after tests finish.


## Reproduction commands

```sh
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle
env -u VIRTUAL_ENV uv sync --locked
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export XDG_CACHE_HOME=/private/tmp/apex-cache MPLCONFIGDIR=/private/tmp/apex-matplotlib
.venv/bin/pytest -q
.venv/bin/pytest -q tests/unit/test_grip_tire.py tests/integration/test_grip_tracking.py tests/unit/test_latency.py
.venv/bin/python scripts/analyze_tire_model.py
.venv/bin/python scripts/compare_tire_models.py
.venv/bin/python scripts/check_grip_equilibria.py
.venv/bin/python scripts/check_grip_parity.py
.venv/bin/python scripts/run_grip_regression.py --case all
# Re-run the nominal timing experiment without concurrent tests:
.venv/bin/python scripts/run_grip_regression.py --case oval
# Regenerate timing/sparsity report from saved runs (no new closed loop):
.venv/bin/python scripts/run_grip_regression.py --case timing
.venv/bin/python scripts/audit_mpc_results.py --output results/mpc_grip
.venv/bin/python scripts/run_mpc_baseline.py --plots-only --output results/mpc_grip
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Do not infer dedicated-host timing from the circle run that overlapped test execution.
Reproducible injected physics does not make measured wall-clock times reproducible.

## Final measured closed-loop results

All runs use unchanged Task006 costs/reference/terminal/horizon/options. Full-run metrics include startup; settled means t>=5s.

| Case | Duration s | Laps travelled | Full RMS ey m | Settled RMS ey m | Full RMS heading rad | Full RMS speed m/s | Peak front/rear utilization |
|---|---:|---:|---:|---:|---:|---:|---|
| circle_zero | 31.320 | 2.000143 | 0.0002248198 | 9.3817344e-05 | 0.012069549 | 0.0061668613 | 0.0875673/0.08234463 |
| oval_zero | 32.580 | 2.000126 | 0.00538274 | 0.0046511725 | 0.016332452 | 0.014881107 | 0.5260263/0.3657023 |
| combined | 12.000 | 0.767478 | 0.012563347 | 9.378537e-05 | 0.018581515 | 0.0087198609 | 0.1437416/0.09903898 |
| oval_45ms | 32.610 | 2.000127 | 0.0092645286 | 0.0071757171 | 0.021539985 | 0.015478615 | 0.6385381/0.4188042 |

All four runs had0solver failures,0fallbacks,0physical boundary violations. Every small positive predicted slack is logged (maxabout9.1e-11m); none exceeds1µm. Circle and both oval cases complete2laps. Combined disturbance runs12s and recovers.

| Track | Task006 full RMS ey m | Grip full RMS ey m | Task006 full RMS speed m/s | Grip full RMS speed m/s |
|---|---:|---:|---:|---:|
| circle_zero | 0.00022556458 | 0.0002248198 | 0.0061552578 | 0.0061668613 |
| oval_zero | 0.0054695448 | 0.00538274 | 0.014602127 | 0.014881107 |

## Task006.2 timing baseline (no optimization performed)

Nominal oval:652solves; wall mean87.0216ms,p50 79.9217ms,p95 120.8005ms,max248.5770ms. Iterations mean9.65798,max25 (old9.64571,max23). Saved Task006 mean68.5112ms,p50 65.8894ms,p95 80.8047ms,max293.7274ms. Observed mean increase27.018%; this historical host comparison does not isolate every load/runtime influence. All new oval solves exceed50ms.

Oval construction: NLP51.136ms, solver149.272ms, total controller208.217ms. These are one-time costs, excluded from solve latency. Controller compute including preview/postprocessing averages101.608ms versus87.022ms inside solver.

Mean per-solve CasADi/IPOPT evaluation wall times: Hessian44.859ms, constraint Jacobian20.882ms, constraints2.157ms, objective0.212ms, objective gradient0.323ms. Hessian+Jacobian dominate observed evaluation cost; unassigned solver time also includes linear algebra/other overhead and is not separately profiled. Counts and maxima are in timing_baseline.json.

NLP structure:208vars,1110constraints (126eq+984ineq),171parameters. Constraint Jacobian1110x208 with5631structural nonzeros; returned upper-triangular Lagrangian Hessian208x208 with651nonzeros. No horizon sweep/extrapolated solve-time estimates.

Oval cold solve248.577ms/25iterations;651subsequent warm solves mean86.773ms/9.634iterations. This is observational, not a controlled warm-start speedup claim. Primal shift semantics unchanged.

45ms injection:652applied updates,19.9939Hz,0missed releases,one pending solve at termination. Mean/p95/max staleness0.027164/0.077093/1.366304. State motion/held commands and all logged tire utilization were independently audited:4cases,21706plant rows,2171applied updates.

Information still needed for Task006.2: target hardware and50ms budget interpretation, acceptable tracking/constraint tradeoffs, profiling of solver linear-system work, allowable horizon/integration changes, and approved warm-start/code-generation strategy. No such change is adopted here.

## Final verification

371-test full regression passed before the final added unit checks. Final complete unit suite
plus grip integration tests:344 passed in the recorded final run; see validation.txt for exact
duration. All lint checks passed;130files already formatted. Locked offline dependency sync
passed. Plots inspected and results audited. All Task006.1 work complete; Task006.2/007
remain unimplemented.
