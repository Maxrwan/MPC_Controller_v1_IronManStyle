# Codex handoff — Task 006.2.2

## Completed scope and read-first files

Task006.2.2 investigates whether the SAME frozen NMPC gains single-solve latency from
multicore execution. Tasks001–006.2 remain intact; prior handoff is TASK006_2_HANDOFF.md.
Read AGENTS.md, NMPC_MULTITHREADING_STUDY.md, NMPC_MULTITHREADING_RESULTS.md,
NMPC_PARAMETER_STUDY.md, NMPC_BASELINE_SPEC.md and ADR101–106 in DECISIONS.md.

No production controller code changed. No asynchronous planner, new solver, mapped-stage
rewrite, custom optimizer threads, codriver, racing or physical-parameter changes.

## Frozen controller and outcome

C: 10 Hz, dt=0.1 s, N=4, horizon 0.4 s, four RK4 substeps, smooth combined-grip physics,
lateral/heading scale2, all other scales1, existing terminal cost. Q=[4,4,1,200,200],
R=[25,1], W=[1,.1]. Exact Hessian, ordinary IPOPT warm-start flag, shifted primal.
ID ipopt_warm_flag_d5e0d799d8. 48 variables, 30 equalities, 168 inequalities.
D remains the 20 Hz, N20, five-substep stress reference. Frozen configuration file is
byte-identical to Task006.2 selected_candidates.json.

Apple M1 (4P+4E), 8 physical/logical cores; macOS26.5.1, Python3.12.14.
NumPy2.5.3/SciPy1.18.1 use Accelerate; CasADi3.8.1, IPOPT3.14.19, MUMPS5.8.2.
No affinity control. AC power and low-power mode off at original stack inspection.
Fresh workers set requested Accelerate ceilings1/2/4/8 before numerical imports, then verify
SINGLE versus automatic MULTI native mode. No exact active pool count is exposed.
All NMPC measurement windows sampled one process thread; CPU/wall≈1. Higher ceilings
are requested settings, not verified parallel workers.

Three randomized fresh-process replicates per workload/ceiling; ten warmups then120
representative deterministic snapshot solves each (2,880 measured). No overlapping benchmarks.
Every solve succeeded. All compared objective/control/X/U/slack values are bitwise identical
across matching ceilings; status/residual checks pass.

C single-thread solve mean/p95=13.288/13.570 ms; total mean/p95=16.680/17.175 ms.
Ceilings2/4/8 solve p95=13.682/13.703/13.972 ms. No material improvement.
D single-thread total p95=112.410 ms; others112.897–113.670 ms, over the50 ms deadline.
T1/Tbest-latency/Tbest-efficiency/Trecommended are ALL1; selected_threading.json records
the predeclared material-benefit policy and paired replicate ratios.

## CPU and scheduling interpretation

C whole-controller CPU mean/p95=16.603/17.088 ms, average demand0.166 core-seconds/s at10Hz.
Mean wall duty16.68%, total p95 period fraction17.18%; active solve occupies≈1 core.
C process-lifetime peak≈190.5MiB, D≈207.5MiB. RSS variation is nonmonotonic.
Headroom is substantial on average, but future codriver/perception costs and joint deadline
behavior are unknown. headroom.json marks illustrative1ms codriver budgets as assumptions.
No exact Pi percentages, transferred scaling factors or hard worst-case guarantees.

Hessian/Jacobian callback means C≈6.4/2.9 ms and D≈42.5/19.5 ms do not materially scale.
Supplementary timing-print probes expose coarse KKT/factor/backsolve/barrier data but are
excluded from primary timings. See solver_components.csv and components/*/worker.log.

## Closed-loop evidence and important exception

Fresh frozen C two-lap measured-latency oval confirms all four ceilings:
n1 lateral4.062mm, total p9517.744ms, zero misses;
n2 lateral4.050mm, total p9516.978ms, zero misses;
n4 lateral4.264mm, total p9517.976ms, ONE miss/325 (0.3077%);
n8 lateral4.093mm, total p9518.613ms, zero logged misses.
All tracking/constraint quality checks pass; no solver failure/fallback/boundary violation.
n4 retained108.704ms solve /170.821ms total spikes. n8 total maximum115.890ms.
The simulator's physical delay remains backend solve time, not whole controller time:
n8 zero logged misses does NOT certify zero total-compute deadline violations.
Closed-loop clock audit: four cases,27,262 plant rows,1,299 updates.
Optional accepted20Hz short-horizon experiment was deferred, not failed or implemented.

## Results, tooling and verification

results/mpc_threading_study contains experiments.csv (24 benchmark +4 closed-loop rows),
pooled.csv, phases.csv, closed_loop.csv, solver_components.csv, selected_threading.json,
frozen_candidates.json, parity.json, verification.json, portability.json, headroom.json,
stack.json, eight plots, raw observations/solutions, subprocess monitor logs, BLAS calibration
and supplementary diagnostic logs. Reproduction source ZIP and manifest accompany results.
Original Task006.2 result/source archives are preserved.

scripts/run_mpc_threading_study.py provides inspect/probe/benchmark/all/closed-loop/
components/analyze/audit commands. scripts/threading_study contains small isolated helpers.
tests/unit/test_threading_study.py covers parsing, environment isolation, true fresh-process
parity/repeat determinism and retained closed-loop consistency. Native API tests skip off macOS.
The harness itself is Mac-specific; port verified controls before claiming a Pi run.
Development dependencies added: psutil and threadpoolctl only.
Final validation: 399 tests passed in 788.58 s; repository lint passes and all 153 Python
files are formatted. Exact output is in results/mpc_threading_study/validation_tests.txt
and validation_lint.txt. Primary parity and four physical-clock audits passed.

## Next task — do not implement without its specification

Task006.3: asynchronous APEX NMPC trajectory planner plus high-rate trajectory-following
codriver. Preserve C, its release clock, trajectory timestamps/staleness, held-control plant
motion, constraints and single-thread debug mode. Reserve measured planner cost; measure
joint scheduling/tail behavior rather than counting nominal cores as equivalent reserves.
Then Task006.4 compares lightweight LQR/TVLQR and small linear-MPC codriver cost/behavior.
Task007 remains deferred.

For copy-paste commands and target benchmarking requirements, see the study document.
Use a NEW replicate number to collect fresh observations; otherwise valid cached conditions
are reused. Do not run timing conditions or the regression suite concurrently.
