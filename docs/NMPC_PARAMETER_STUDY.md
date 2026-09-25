# Task006.2 — synchronous NMPC parameter study

## Purpose and dependency

Task006.1 is present and validated: bounded combined-grip NumPy/CasADi equations, archived
parity and regression evidence. This study characterizes the current synchronous direct
multiple-shooting IPOPT controller. It does not implement new solvers, asynchronous planning,
compensation, a codriver or racing objectives. No global/convex optimum is claimed.

## Reference and immutable physics

Reference:20Hz,T=.05,N20,1s coverage,5RK4 substeps, grip physics, unchanged Task006 weights,
terminal DARE schedule, slack penalties, actuator/model constraints and IPOPT defaults.
Synthetic vehicle, periodic tracks,2m/s reference, initial cornering vy/r, zero held input,
plant step<=.005s, preview approximation and baseline fallback remain unchanged.
Circle/oval zero and measured runs are repeated before screening. Old Task006.1 artifacts
are preserved, not relabeled as current measurements.

## Predeclared development acceptance envelope

Before classifying candidates, full-run oval RMS thresholds are set to:

- lateral<=.025m (above prior .005–.017m NMPC/LQR results, well inside narrow .3m boundary),
- heading<=.06rad (allows startup/transient degradation, about3.4degrees),
- speed error<=.08m/s (4% of2m/s reference),
- no physical boundary or model-validity failure,
- no solver failure/fallback dependence, all required laps completed,
- maximum predicted slack<=1e-4m (0.1mm; every positive slack is still logged),
- tire utilization<=1+1e-12.

This is a provisional synthetic development envelope, not measured vehicle safety or a
requirement for submillimeter circle tracking. Any solver failure is conservatively excluded,
stricter than rejecting repeated failures alone. Candidates outside the RMS envelope remain
visible but cannot win compute-efficiency selection. Tiny interior-point slack differences
below the material gate are not treated as separate Pareto objectives.

Integration gate:80seeded valid snapshots,seed60062, speed1–3m/s,vy±.15m/s,r±.8rad/s,
heading/lateral±.1,steering±.25rad,acceleration±1m/s²,curvature±.8/m. Compare one interval
with DOP853 applied to the independent NumPy derivative (rtol1e-11,atol1e-12), with the
same frozen curvature on both sides. Error scales in canonical order are[.5,.5,1,.1,.1,.1].
Require maximum scaled norm<=.02,RMS scaled norm<=.005 and no invalid internal plant stages.
These explicit conservative accuracy gates prevent selecting a cheap but distorted prediction.
Per-channel SI errors and independent equal-step NumPy/CasADi parity are also retained.

## Staged design and observation windows

A: fresh circle/oval zero and measured latency,2laps (80s cap).
B: N8/10/12/15/20/25,20Hz,5substeps,1oval lap (45s cap).
C: substeps1/2/3/5 for best compute and best tracking quality-qualified B horizons.
D:10/15/20/25Hz,N=frequency for1s coverage, zero and measured latency. Preserve the
literal selected substep comparison; separately refine inaccurate intervals. Afterward test
the Stage B compute winner's coverage (0.4s in this run) at all four rates, rounding N to
an integer (N4/6/8/10). This small follow-up separates release frequency from horizon cost;
no full Cartesian horizon/rate/integration search is performed.
E: grouped one-factor changes from the chosen structural anchor: lateral/heading,vy/r,
speed andR multipliers .5/1/2;W .25/.5/1/2. At most one combination of independently
promising tracking/speed changes; never a Cartesian product.
F: terminal multipliers0/1/.5/2; no terminal equality.
G: unchanged IPOPT, max40iterations, tol1e-6, stricter tol1e-8, limited-memory Hessian and
warm_start_init_point=yes. Existing independent feasibility acceptance remains<=1e-6.
No relaxed actuator/friction/slack domain or intentionally poor-success tolerance.

Identical experimental configurations are reused and marked with every applicable stage,
preventing redundant runs. Hashes include mode,track,lap/duration target,disturbance and all
controller settings. Screening uses one full oval lap for equal exposure. Reference and
selected confirmations use two laps; compare those windows separately. Failed runs retain
their shorter observed windows and missing lap times. No failed-run RMS is treated as a
successful full-lap result. Finalists confirm circle,oval,combined disturbance and measured
latency; deterministic25/45/60ms cases characterize selectedC.

At different periods, preserve stage-sum cost semantics (no new dt multiplier) and nominal
steering increment limit rate*dt. Terminal matrices remain the provisional Task005100Hz
schedule; terminal multiplier scales the complete lateral+speed terminal term. Grouped stage
multipliers do not silently recompute the terminal matrix. Frequency therefore also changes
stage density relative to terminal cost; that coupling is reported rather than hidden.

## Timing and runtime reuse

Set OPENBLAS_NUM_THREADS=1,OMP_NUM_THREADS=1. Runs are serialized; no parallel benchmark
workers. perf_counter measures preview, geometry/reference subparts, warm preparation,
parameter packing, solver adapter, backend solve, output validation/postprocessing and total
controller computation. Nested timings must not be summed twice. Construction is outside
repeated solves; each experiment builds one MPCProblem and one IPOPT instance. No symbolic
reconstruction occurs in compute_control. No defect requiring a graph-reuse change was found.

The existing measured physical latency remains actual solver-call time, preserving Task006
semantics. Total compute is additionally reported; solver-only deadline margin is optimistic
for end-to-end hardware actuation. These are local Darwin/arm64 measurements, not Raspberry
Pi timings. Background host scheduling/thermal effects can change measured outcomes.

The event runner already splits exact events. Only RunConfig validation was extended to
permit fractional controller/plant ratios when explicit event-based latency is enabled;
legacy integer-grid mode remains strict. This permits15Hz exactly, without rounding to a
multiple of5ms. Unit tests verify release times and maximum plant step.

## Pareto analysis and selection

Do not collapse outputs into a scalar score. The principal nondominated set compares
quality-qualified one-lap oval zero-latency configurations on p95 solve time, lateral RMS,
speed RMS and heading RMS. Failure/slack/boundary/grip conditions are hard gates. A record
is dominated if another is no worse on all four and strictly better on at least one.
Separate measured-latency plots show deadline reliability and observed tracking; failed runs
are labeled and excluded from viable selections. A projection into two dimensions need not
itself look like a two-criterion frontier.

A: smallest lateral RMS among front candidates with p95/period<=1 when available.
B: lowest p95 solve among the quality-qualified front.
C: initially lowest p95/period; after measured two-lap confirmations choose lowest lateral
RMS among quality passes with<=5% missed releases. If none pass, explicitly report the
lack of a validated synchronous real-time candidate rather than inventing one.
D: fresh current/reference configuration. Roles may coincide; no artificial distinct winner.

Compute ratios mean/p95=solve statistic/period. Categories:<.5 comfortable,.5–.8 moderate,
.8–1near deadline,>1nominal real-time infeasible. These are engineering labels, not guarantees.
A cold first solve can miss a deadline even if repeated-solve p95 is comfortable.

## Artifacts and future tasks

results/mpc_parameter_study/experiments.csv is the machine-readable database. Each run has
configuration.json,experiment.json,summary.json,states.csv,controls.csv,solver_events.csv and
predictions.jsonl. Configuration hashes and serialized settings make candidates reproducible.
Stage choices and selected A/B/C/D configs are explicit JSON. Re-running stages reuses cached
configurations; set APEX_STUDY_REPLICATE to a new label to record fresh timing replicates.

Predictions retain state/input trajectories, absolute node timestamps, sampled state, actual
completion state/time, scheduled completion, applied/completed flags and nominal remaining
horizon. Pending-at-end results have no actual completion; negative reserve is retained.
No trajectory buffers, interpolation policy or asynchronous consumer is implemented.

Task006.4 preparation includes lateral-state ranges, nominal4-state/1-steering-input model,
offline baseline-versus-NMPC command differences,100/200Hz codriver options and existing
BaselineController timing (including geometry/reference lookup). It is not a TVLQR or linear
MPC codriver implementation, nor a claim about attainable Pi frequency.

Results, rejected configurations and data-derived recommendations are appended after the
staged experiments. Next is Task006.3 asynchronous planner plus high-rate trajectory codriver;
Task006.4 will compare a small linear MPC codriver with LQR/TVLQR afterward. Neither is
implemented here.
