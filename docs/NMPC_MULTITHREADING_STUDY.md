# Task 006.2.2 — multicore latency study

## Scope and frozen dependency

Task006.2 is complete with380passing tests and Candidate C frozen in its selected JSON.
This study preserves that exact controller and the heavy Candidate D reference. No NMPC
mathematics, physical parameters, tolerance, warm-start policy, horizon or integration change.
No asynchronous planner, codriver, new optimizer or independent-solve throughput experiment.

C:10Hz,N4,4RK4 substeps,lateral/heading scale2,current terminal term,exact Hessian,
shifted primal warm starts and IPOPT warm-start flag. D:20Hz,N20,5substeps,reference costs
and solver options. Each experiment uses one optimizer instance, called serially.

## Stack and supported controls

Actual host inspection: Apple M1,8physical/logical cores,4performance plus4efficiency cores;
macOS26.5.1,Python3.12.14. AC power,charged battery,low-power mode disabled at inspection.
Affinity is not controlled; no P-core-only or E-core-only claim is made.

NumPy2.5.3 and SciPy1.18.1 report Apple Accelerate BLAS/LAPACK. CasADi3.8.1's installed
IPOPT3.14.19 uses MUMPS5.8.2. Both IPOPT and MUMPS dylibs link to Accelerate. Dependency
inspection does not show an OpenMP runtime. The current SX NLP is an ordinary serial graph;
its Hessian/Jacobian callbacks do not become parallel by setting an environment variable.
Plugin availability alone does not mean a plugin participates in the active solver path.

Each fresh worker receives VECLIB_MAXIMUM_THREADS=1/2/4/8 before native libraries load.
BLASSetThreading sets SINGLE for the baseline and automatic MULTI for higher ceilings;
BLASGetThreading verifies acceptance. The API controls threading mode, not an exact worker
count. Thus all labels denote REQUESTED CEILINGS, not proof of that many active cores.
Inactive OpenBLAS/MKL/OpenMP controls are removed from worker environments, not represented
as effective knobs. The installed SDK header provides the mode constants.

threadpoolctl does not enumerate this Accelerate pool; its empty listing is not evidence
of no threads. Native API state, process CPU time and sampled process thread counts provide
the empirical evidence. A separate2048x2048dense BLAS probe checks the available mechanism;
its timings are never presented as NMPC speedups. psutil and threadpoolctl are development
profiling dependencies only; the control runtime is unchanged.

Apple documents the per-calling-thread mode setting in
[BLASSetThreading](https://developer.apple.com/documentation/accelerate/blassetthreading(_:)).
CasADi documents explicit mapped parallel evaluation in its
[map documentation](https://web.casadi.org/docs/#for-loop-equivalents).
The current graph has no such mapped stage structure. Introducing one and changing derivative
graph construction would exceed this backend-only study; that optional experiment is deferred.
No Python threads call an optimizer concurrently and no manual worker architecture is adopted.

## Predeclared experimental method

Three independent fresh-process replicates per workload and ceiling,120measured solves each,
preceded by10warm-up solves. Configuration order is shuffled with seeds6220,6221,6222.
No benchmark conditions run concurrently, and test suites wait until benchmarks finish.
A parent process samples thread count/RSS approximately every10ms; its CPU is excluded from
child process CPU measurements. This observation overhead and ordinary OS activity remain
potential timing influences. Sampled peak thread counts are not guaranteed absolute peaks.

Inputs are deterministic, evenly selected snapshots from each frozen candidate's saved oval
zero-latency solver-event log. They include actual sampled states and previous controls. The
same sequence, controller configuration and warm-up procedure are used at every ceiling.
The existing one-stage primal-shift policy is retained. This is representative problem replay,
not a claim that discontinuous sampled snapshots form a new physical closed-loop trajectory.
C and D have different frozen source windows; compare thread counts within each workload.

A benchmark-only proxy brackets the native backend call with perf_counter/process_time.
The controller's established timing decomposition remains available. Aggregate process CPU
includes native worker threads. CPU/wall ratios report average effective cores, not physical
core identities. RSS and process-lifetime peak RSS include imports, construction and profiling;
between-solve and sampled measurement-window RSS are reported separately where available.

All120solutions per replicate are retained, including objectives, controls, predicted states,
inputs, slacks, statuses and primal residuals. Threaded parity against matching single-thread
samples requires objective relative/absolute1e-6, first/all controls absolute1e-6, states1e-5,
slacks1e-7, successful status and primal residual<=1e-6. These are far below the development
tracking envelope and do not loosen physical/controller acceptance. Nonfinite/failing data
must remain visible and cannot win selection.

Material timing benefit is predeclared as at least10%lower pooled p95, with improvement in
at least two of three paired replicate comparisons and numerical parity. Smaller differences
are observational, not evidence to complicate the default. Report mean/p95 speedup S=T1/Tn
and requested-count efficiency E=S/n, explicitly distinguishing that denominator from
measured active cores. Lowest p95 can be reported even when it is not a reliable improvement.

Fresh Candidate C two-lap measured-latency confirmations cover all four ceilings. Existing
solver-only physical latency semantics remain unchanged; total controller time is used for
compute-margin ratios. No change to Candidate C's official10Hz rate is made. The optional
20Hz question may be deferred; heavy D is a compute stress test, not a preferred controller.

## Measured results and recommendation

The 24 primary conditions contain 2,880 measured solves: 360 per workload/ceiling.
All solves succeeded. All retained first controls, complete predicted trajectories, objectives
and slacks were bitwise equal across ceilings within matching replicates; residual/status
checks passed. This is evidence for the installed serial execution path, not a guarantee
for a future parallel solver build. Full tables are in
[NMPC_MULTITHREADING_RESULTS.md](NMPC_MULTITHREADING_RESULTS.md).
Raw evidence is in ../results/mpc_threading_study.

| Requested ceiling | C mean / p95 solve ms | C p95 total ms | D mean / p95 solve ms | D p95 total ms |
|---|---|---|---|---|
| 1 | 13.288 / 13.570 | 17.175 | 81.098 / 97.583 | 112.410 |
| 2 | 13.210 / 13.682 | 17.264 | 82.381 / 98.149 | 112.897 |
| 4 | 13.417 / 13.703 | 17.301 | 82.578 / 99.114 | 113.670 |
| 8 | 13.375 / 13.972 | 17.519 | 81.767 / 98.079 | 112.711 |

No ceiling provides a material, reliable improvement. Every higher ceiling has a worse pooled
p95 in both workloads. The 2-thread ceiling improves C's mean by only 0.6%, while its p95
gets worse. All T1, Tbest-latency, Tbest-efficiency and Trecommended selections are **1**.
The installed runtime accepted SINGLE versus automatic MULTI mode, but NMPC used about
0.988–0.996 effective cores across both workloads and all ceilings; sampled peak process
thread count during measurement was one. No evidence demonstrates concurrent native solve
workers. These are failed acceleration experiments, not verified 2/4/8-thread solves.

C's mean/p95 requested-count efficiencies for n=1/2/4/8 are respectively
100/50.29/24.76/12.42% and 100/49.59/24.76/12.14%.
These values use E=S/n as requested. They do **not** mean that 8 physical cores were allocated
or that seven cores were wasting CPU time. Actual resource consumption stayed near one active
core and approximately 13.2–13.3 ms backend CPU per solve.

## Components and portable workload

C has 48 variables, 30 equalities and 168 inequalities. Its 198×48 constraint Jacobian has
943 structural nonzeros; the 48×48 Lagrangian Hessian has 139 upper-triangular entries
(235 in the full symmetric structure). D has 208 variables, 126 equalities and 984
inequalities; Jacobian 1110×208 with 5631 entries; Hessian 208×208 with 651 upper entries
(1115 full). The full-horizon RK4 expression contains 64 RHS sites for C and 400 for D.
These are structural sites, not measured counts of dynamically executed AD operations.

Across all ceilings, C averages 9.142 IPOPT iterations and D 9.900. C averages
11.333 objective, 12.333 constraint, 11.142 gradient, 11.142 Jacobian and 9.142 Hessian
callbacks per solve. D averages 12.208 objective/constraint, 11.900 gradient/Jacobian and
9.900 Hessian callbacks. Counts are identical across ceilings.

C mean accumulated Hessian callbacks range 6.351–6.456 ms and Jacobian 2.928–2.968 ms;
objective about 0.046 ms and gradient 0.064–0.065 ms. D Hessian ranges 42.500–43.140 ms,
Jacobian 19.512–19.933 ms, objective 0.187–0.195 ms and gradient 0.292–0.311 ms.
No material derivative acceleration is visible. The current symbolic graph is serial.

Single-thread C mean preview/packing/backend/postprocessing costs are
3.010/0.023/13.288/0.140 ms, with 16.680 ms total. D is
12.524/0.026/81.098/0.354 ms, with 94.308 ms total. Warm-start preparation and nested
adapter overhead are retained in phases.csv; do not sum overlapping timers.

Supplementary IPOPT timing-print logs expose PD system solve, symbolic factorization,
numerical factorization, backsolve and barrier update timers. solver_components.csv retains
all 16 diagnostic calls. They use only two calls per condition, no warmup and 1 ms printed
resolution, so no factorization speedup claim is justified. Printed zeros mean below that
resolution. These calls and their altered diagnostic options are excluded from primary
timing and parity comparisons; primary solver settings remain frozen.

## CPU, memory and headroom for later work

Single-thread C backend CPU mean is 13.222 ms; whole-controller CPU mean/p95 is
16.603/17.088 ms. At 10 solves/s, average controller demand is **0.166 CPU-core-seconds/s**.
Mean wall duty is 16.68%; p95 total computation occupies 17.18% of the 100 ms period.
An active solve occupies approximately one CPU core. Multiplying the per-call p95 CPU time
by 10 gives 0.171 core-seconds/s as a repeated-p95 scenario, not a measured p95 over
one-second scheduling windows.

Subtracting the average planner demand from a nominal eight-core count gives 7.834 core
equivalents. This is arithmetic accounting only: M1 cores are heterogeneous, OS and observer
load are excluded, and no seven-core reservation or measured available-capacity guarantee
follows. Even a one-core accounting view leaves about 0.834 average core-seconds/s before
other work. The 82.825 ms p95 period remainder is a timing budget, not a hard guaranteed slot.

A future codriver requires measured demand f_codriver × CPU_seconds_per_call. Illustratively,
1 ms CPU per call at 100/200 Hz adds 0.1/0.2 core-seconds/s. These are assumed cost examples,
not measured TVLQR or small-MPC performance. Existing Task005 LQR timing is historical
context, not a measurement of a new trajectory-following codriver. Lightweight codriver
work appears plausible on this host; its high-rate deadlines and contention still require
joint experiments. Perception, identification, energy, opponents and defensive planning
have no measured budgets here.

C mean RSS is 181.8–189.3 MiB across ceilings; process-lifetime peaks are 190.4–190.5 MiB.
D mean RSS is 138.9–204.9 MiB and lifetime peaks 207.0–207.5 MiB. RSS is a process-level
snapshot influenced by OS residency and imports, with no monotonic thread-dependent growth.
The differences do not establish memory savings from threading. Lifetime peaks include
construction, profiling and imported packages; they are not isolated solver allocation costs.

D's hypothetical demand at 20 Hz is 1.878–1.899 CPU-core-seconds/s, but it actually uses
one core per active solve and cannot sustain those releases. Do not interpret this demand
projection as evidence it utilized two cores.

## Closed-loop consistency and real-time qualification

Every fresh two-lap oval measured-latency run passes tracking, finite solve, residual,
slack, boundary and tire-utilization checks. All use frozen Candidate C at 10 Hz.

| Ceiling | lateral RMS mm | heading RMS rad | speed RMS m/s | solve p95 ms | total p95 ms | missed releases | effective Hz |
|---|---|---|---|---|---|---|---|
| 1 | 4.062 | 0.016456 | 0.029324 | 14.403 | 17.744 | 0/325 | 10.017 |
| 2 | 4.050 | 0.016467 | 0.029301 | 13.501 | 16.978 | 0/325 | 10.015 |
| 4 | 4.264 | 0.016880 | 0.029598 | 14.504 | 17.976 | 1/325 | 9.985 |
| 8 | 4.093 | 0.016513 | 0.029365 | 15.018 | 18.613 | 0/325 | 10.015 |

Lap times are approximately 16.267 and 16.178 s (exact values in closed_loop.csv).
All have zero solver failures, fallbacks and boundary violations, maximum slack
9.092e-11 m, and maximum front/rear tire utilization approximately 0.63854/0.36987.
Tracking is consistent with Task006.2's 4.147 mm lateral RMS, with expected timing-related
trajectory differences; this is not bitwise closed-loop parity.

The n=4 run includes a 108.704 ms solve spike, 170.821 ms total spike and one missed
release (0.3077%). The n=8 run has a 78.242 ms solve maximum and 115.890 ms total maximum.
The existing simulator delays physical application by measured **backend solve time**,
not total controller time, so n=8's zero logged misses must not be read as proof of zero
end-to-end deadline violations. This inherited latency-model limitation is preserved and
disclosed, not silently changed. The general event-clock audit passed 27,262 plant rows
and 1,299 applied updates.

Repeated-solve C total p95/period is 0.172–0.175: large observed margin (<0.25).
D is 2.248–2.273: synchronous real-time infeasible (>1). Remaining engineering categories
are comfortable [0.25,0.50), moderate [0.50,0.80), near deadline [0.80,1.00].
The optional 20 Hz accepted short-horizon experiment was not performed: flat threading
results provide no evidence that threading enables it. Candidate C remains officially 10 Hz.

## Jitter and limitations

C repeated-solve standard deviation is 2.12–2.30 ms, CV 0.161–0.172, p99 19.88–23.14 ms
and maximum 34.83–36.23 ms. D standard deviation is 15.35–18.76 ms, CV 0.189–0.227,
p99 104.44–185.13 ms and maximum 222.95–273.42 ms. No consistent jitter reduction appears;
D's higher ceilings show worse observed tails in this sample. Closed-loop spikes remain
visible. Timing variation includes changing snapshot difficulty as well as OS noise; it is
not a pure scheduler-jitter measurement. Three replicates and finite samples cannot
establish a causal threading penalty or bound worst-case execution time.

No affinity control, exact Accelerate pool-size query, reliable per-thread CPU breakdown,
thermal isolation or hard-real-time scheduling was available. psutil per-thread CPU access
was denied; aggregate process CPU and sampled thread counts were available. The current
build's absence of observed parallelism does not prove all MUMPS/Accelerate builds or
larger problems are inherently serial. The separate dense BLAS calibration also did not
demonstrate more than one effective core; mode acceptance is not worker-count activation.
No new backend, custom thread architecture, asynchronous planner or codriver was added.

## Acceptance questions and target interpretation

- **Q1:** Yes, C meets the observed single-thread development deadline with large p95
  margin and zero missed releases in its confirmation; this is not a hard-real-time proof.
- **Q2:** No material Candidate C latency improvement.
- **Q3:** One is the maximum demonstrated useful setting for this stack/workload.
- **Q4:** No higher ceiling reduced pooled p95.
- **Q5:** No systematic C jitter benefit; D tails worsened in some runs. The data do not
  isolate thread setting as the cause of desktop spikes.
- **Q6:** No disproportionate extra CPU was measured: all settings stayed near one active
  core. There is also no useful latency benefit.
- **Q7:** No. D's total p95 remains over twice its 50 ms deadline.
- **Q8:** Measured C demand leaves substantial average headroom, supporting investigation
  of lightweight codriver work. No future codriver or jointly contending stack is validated.
- **Q9 measured:** M1 timing/core-time/RSS, fixed NLP workload, one useful setting and
  flat scaling are measured facts about this stack.
- **Q9 inferred:** Low intra-solve parallelism makes single-core performance and derivative
  cost important portability concerns. Symbolically T_target ≈ T_Mac/r only if r measures
  relative performance of this exact workload with comparable libraries.
- **Q9 unknown:** Pi 4/Pi 5 wall-time tails, active numerical backend, useful thread count,
  memory residency, thermals, power limits and system contention. No Pi CPU percentage
  or real-time feasibility claim is supported without target measurements.

portability.json contains per-workload dimensions, callback counts, CPU cost, memory,
frequency and p95 deadline. On each target, first inspect the actual BLAS/IPOPT/MUMPS build,
implement its verified native controls (this Accelerate harness is macOS-specific), repeat
the same frozen samples/three replicates, then run measured-latency two-lap and sustained
thermal/joint-codriver tests. Mac speedups must not be transferred as Pi scaling factors.

## Handoff and reproduction

Task006.3 remains next: asynchronous APEX NMPC trajectory planner plus high-rate
trajectory-following codriver. Use frozen C, 10 Hz, 0.4 s preview and one-thread baseline.
A separate architecture can address staleness, release scheduling and independent codriver
updates; increasing a thread ceiling did not remove those concerns. Reserve measured
planner cost and test contention rather than assuming all eight cores accelerate planning.
Task006.4 must measure LQR/TVLQR and small linear-MPC CPU cost and tail deadlines separately.
Neither task is implemented here.

Run commands from the repository root. A completed condition is reused; choose a new
replicate number for fresh data. Changed sample/warmup counts or frozen configurations
cannot silently reuse an incompatible cache. All timing experiments must run sequentially.

```sh
.venv/bin/python scripts/run_mpc_threading_study.py benchmark --threads 1 --replicate 3
.venv/bin/python scripts/run_mpc_threading_study.py benchmark --threads 2 --replicate 3
.venv/bin/python scripts/run_mpc_threading_study.py benchmark --threads 4 --replicate 3
.venv/bin/python scripts/run_mpc_threading_study.py benchmark --threads 8 --replicate 3
.venv/bin/python scripts/run_mpc_threading_study.py benchmark --workload D --threads 1 --replicate 3
# Repeat D with --threads 2, 4, 8 to complete matching comparisons.
for n in 1 2 4 8; do
  .venv/bin/python scripts/run_mpc_threading_study.py closed-loop --threads "$n" --replicate 1
done
.venv/bin/python scripts/run_mpc_threading_study.py audit
.venv/bin/python scripts/audit_mpc_results.py --output results/mpc_threading_study/closed_loop
MPLCONFIGDIR=/private/tmp/apex-matplotlib .venv/bin/python scripts/run_mpc_threading_study.py analyze
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

The inspect, probe and components actions retain stack inspection, separate dense BLAS
calibration and supplementary solver diagnostics. The all action replays/reuses the original
three randomized replicates and regenerates tables/plots. When adding replicates, complete
all matching workload/ceiling pairs before comparing pooled data.

## Validation and provenance

The retained numerical audit covers all 2,880 samples, and closed-loop consistency covers
all four ceilings. Fresh subprocess tests additionally check deterministic repeated SINGLE
mode, SINGLE/MULTI solution parity, invalid thread settings and environment isolation.
Final regression: **399 passed in 788.58 s**. Repository lint passed; all 153 Python files
passed format checks. See results/mpc_threading_study/validation_tests.txt and
validation_lint.txt for exact output.

Aggregate backend CPU/wall≈0.995 for C means roughly 99.5% of **one core** while solving,
not 99.5% of the entire M1. Both sampled mean and sampled peak process thread counts were
one during primary measurement. The sampling interval can miss transient threads; process
CPU accounting supplies a separate check against sustained multicore execution.

The source archive and provenance manifest retain the condition shuffle seeds/order,
source/result hashes, and verification that all 65 production source files match the prior
Task006.2 manifest. The original candidate JSON is byte-identical. Reproduction uses the
preserved Task006.2 snapshot source files, whose hashes appear in each run summary.
