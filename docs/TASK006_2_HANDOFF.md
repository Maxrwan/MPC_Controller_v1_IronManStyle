# Codex handoff — Task 006.2

## Goal and completed scope

Characterize the existing synchronous grip NMPC before changing architecture. Tasks001–006.1
remain in place; Task006.1 dependency and its validation were verified before this study.
Its prior handoff is archived in TASK006_1_HANDOFF.md; Task006 history is in TASK006_HANDOFF.md.

Task006.2 includes stagesA–G, the0.4 s frequency follow-up, Pareto analysis, finalist circle/
oval/disturbance tests, measured/fixed latency confirmation, paired warm-start tests and
complete timing/trajectory exports. No asynchronous planning, new solver, latency compensation,
trajectory buffer, TVLQR/linear-MPC codriver, racing objective or physical-parameter change.

## Read first

AGENTS.md; NMPC_PARAMETER_STUDY.md; generated NMPC_PARAMETER_STUDY_RESULTS.md;
NMPC_BASELINE_SPEC.md; GRIP_LIMITED_TIRE_SPEC.md; ADR093–100 in DECISIONS.md.
Full machine-readable data live under results/mpc_parameter_study.

## Primary result and exact handoff

Candidate C (also B): `ipopt_warm_flag_d5e0d799d8`.
10 Hz,dt=.1 s,N4,0.4 s horizon,4 RK4 substeps; CostScales(lateral=2, all others=1).
Q=[4,4,1,200,200],R=[25,1],W=[1,.1], current complete terminal cost scale1.
Exact Hessian, default IPOPT options plus warm_start_init_point=yes; shifted primal guesses.
48 variables,30 equalities,168 inequalities. Grip, plant dt<=.005 s, slack penalties and all
actuator/domain constraints are unchanged. Library defaults remain the reference, not C.

Full MPC config, effective solver options, source configuration hash and scenario fields are
in selected_candidates.json. Reproduce frozen settings with scripts/replay_mpc_candidate.py.
Candidate A has identical control settings with limited-memory Hessians and about20 nanometers
smaller screening lateral RMS: a practical numerical tie, with substantially worse timing.
Candidate D remains20 Hz,N20,5 substeps,all scales1 and default solver options.

C two-lap measured oval: lateral RMS.004147 m,heading.016451 rad,speed error.029399 m/s;
solver mean/p95=14.114/15.848 ms,total mean/p95=17.664/19.898 ms;0misses,10.017 Hz effective.
Max slack9.09e-11 m,primal residual6.26e-9,front/rear utilization.6385/.3699. Two-lap zero
oval completes32.425 s with lateral RMS.002778 m. Circle and combined disturbance also pass.
Fixed25/45/60 ms delays complete two laps, lateral RMS.004797/.006914/.009174 m,0misses.

Reference two-lap zero oval lateral RMS.005383 m,solver p95=96.53 ms,total p95=112.88 ms.
Measured reference fails at2 s with70.73% missed releases. Zero-latency good tracking does not
establish real-time feasibility. A measured confirmation passes but has1.23% misses and
6.878 mm lateral RMS. All host wall times are observations, not deadline guarantees.

## Study evidence and caveats

68 observations represent62numerically distinct scenario configurations. The original hash
cache distinguished1 from1.0, causing extra nominal measurements; retained raw IDs/hashes
are grouped by semantic_configuration_hash, and future lookup handles numeric equivalence.
15exact four-criterion nondominated observations remain. Tiny solver-setting tracking/time
differences should not be overinterpreted; full lists and measured fronts are in pareto.json.

One/two RK4 substeps at50 ms fail the independent accuracy gate despite nominal tracking.
Three pass at50/66.667/40 ms;100 ms requires four. The10 Hz,N4 structural setting supplies most
of the speedup. Doubling lateral weights trades speed tracking for lateral improvement.
Terminal removal degrades lateral RMS to22.84 mm. Quasi-Newton is slower, ordinary option
changes marginal. Controlled C warm guesses save one iteration and about6.3% on one fixed
problem; reference warm guesses show no convincing benefit.

Measured physical latency deliberately remains backend solver time; total controller time
is separately logged. No graph rebuild defect was found. Geometry preview is the main
non-solver cost. Callback profiling covers Hessian/Jacobian evaluation, not separate IPOPT
factorization/barrier internals. A261 ms backend outlier occurred during a45 ms-injected run;
injected physical latency remains45 ms by definition. C's zero measured misses are not a
worst-case latency bound. No Raspberry Pi performance or real vehicle safety claim.

## Code changes

- CostScales and MPCConfig parameterize existing grouped/terminal costs.
- Controller/preview expose nested timing and timestamped prediction exports.
- run_mpc_baseline accepts explicit config/options without changing default physics.
- RunConfig permits fractional control/plant ratios on the event runner for exact15 Hz.
- Study modules implement staged cache, accuracy tests, selection, plots and measured tables.
- Audits check variable-period steering limits, plant clocks, hashes, timing partitions and
  exported trajectory timestamps/states/reserve. Canonical ordering and force laws unchanged.

## Validation

Both result audits passed:68 experiments,245844 plant samples,15700applied updates,
15708 solver events/predictions. All raw command holds, application states, staleness indices,
plant step limits and grip checks pass. Full regression result: 380 passed in 493.57s (0:08:13).
Ruff check/format passes. See validation_tests.txt, study_verification.json and
runs/verification.json in the result directory for final evidence.

## Next task and proposed defaults

Next: Task006.3 asynchronous NMPC trajectory planner plus high-rate trajectory-following
codriver. Start from frozen C; planner10 Hz,codriver100 Hz,minimum future reserve.20 s,
time-aligned linear state interpolation with continuous heading/progress and initial ZOH
inputs; predict intended actuation-time state using applied-input history. Track four lateral
errors with trajectory feedforward plus LQR/TVLQR; specify longitudinal tracking separately.

Accept newer valid plans with sufficient reserve and continuity checks. Continue valid active
plans on failed solves; explicitly terminate development simulations before exhaustion rather
than inventing a physical stop law. Initial trigger=.05 m lateral/.10 rad heading for two ticks;
initial per-side center-point margin=.08 m. These are proposals, not implemented or certified.
Read task0063_development_defaults.json and the study's rationale/limitations. C measured
reserve min/mean=.3511/.3859 s, but long-tail solves require explicit late-plan handling.

Need hardware/OS timing budget, estimation/delay interfaces, physical stopping policy and
footprint/uncertainty allowances before treating these as vehicle requirements.

After006.3, Task006.4 compares a small high-rate linear MPC codriver with LQR/TVLQR and
assesses Raspberry-Pi-class feasibility. Preserve future_codriver_data.json:4 states/1input,
100/200 Hz options, raw ranges, offline command differences and full Task005 baseline timing
(.634 ms mean,.723 ms p95 on this host). Actual future tracker corrections are not measured.

## Commands

```sh
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export XDG_CACHE_HOME=/private/tmp/apex-cache MPLCONFIGDIR=/private/tmp/apex-matplotlib
.venv/bin/python scripts/run_mpc_parameter_study.py --stage A
# Repeat --stage with B,C,D,E,F,G in order, or use all.
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

The cache retains old observations; unique APEX_STUDY_REPLICATE labels force fresh runs.
New wall measurements need not reproduce exact timing or measured-latency trajectories.
All deterministic configuration values, seeded fidelity snapshots and injected clock rules
are reproducible. Reproduction source archive and SHA256 manifest accompany final results.
