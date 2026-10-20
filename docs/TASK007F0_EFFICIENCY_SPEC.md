# Task007F-0 — Efficiency research specification

**WORK_COMPLETE_PENDING_REVIEW — specification and Git preservation only.**
Authority: Primary APEX's revised F0 assignment and nonuniform-grid amendment. Base is E4 acceptance
`48adbdf64d492592d15e23c917aca71fa58aa8a5`. No Efficiency controller, profiling, numerical tests,
new racing run, default change, Safety implementation or exporter repair is authorized or executed.

## 1. Accepted reference and scope

The [accepted Performance checkpoint](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/tree/48adbdf64d492592d15e23c917aca71fa58aa8a5)
is preserved separately from `research/efficiency`; see the [Git guide](TASK007F0_GIT_REFERENCES.md).
Its [manifest](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/configs/performance/apex_performance_synthetic_v1.json)
has SHA256 `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
The [E4 acceptance overlay](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/docs/task007e/e4/primary_acceptance.json)
records Primary's later acceptance without changing the original proposal flags. Scientific source/
profile verification remains `e603672b209985f11ed26b6f44d3949ffd5675c5`, E3 delivery
`ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9`; E4 is not a new scientific execution.

Reference A: N8, dt=0.1 s, H=0.8 s, four symbolic RK4 substeps, full two-input sequence,
Q=diag(4,4,1,200,200), R=diag(25,1), W=diag(1,0.1), lambda_s=0, alpha_vy=alpha_r=1;
original terminal schedule, IPOPT options/primal warm start, predictor A, variable handoff, 100 Hz
TVLQR, independent NumPy plant, combined grip, gamma2 Planning and 0.08 m synthetic margin.
State order `[vx,vy,r,e_psi,s_abs,e_y]`, inputs `[delta,a_cmd]`, SI units, with dynamic
`a_cmd=Fx_total/m`. Exact construction/settings/vehicle/fixture/dependency hashes stay in the
immutable manifest rather than being duplicated into another runtime profile.

Keep three references separate: accepted Performance A, historical **unoptimized C70**, and each
individually versioned Efficiency candidate. Nonuniform-grid work initially uses A scheduling;
fixed commitment changes are a later independent factor. B, lightweight predictors, solver
retuning in the accepted profile, energy control, System Identification, LMPC, unseen-track and
Workbench development are outside this assignment.

## 2. Decision policy and measurable gates

Approved scientific policy is lexicographic: **physical/numerical validity → valid authority and
deadline reliability → computational/resource reduction → acceptable racing/tracking**. After hard
gates pass, use a Pareto comparison of separate metrics. Do not trade a validity failure for lower
CPU, average timing, a faster lap or a weighted score.

The versioned [metrics and gates](task007f/f0/metrics_and_gates.json) define units, populations,
missing/censored values and uncertainty. Primary compute is **total preparation CPU seconds per
simulated second**; primary latency is **p95 total preparation wall time**. Report all outcomes,
mean/median/p99/max/n, process duty, RSS, iterations, feasibility, misses and availability separately.
CPU per simulated second differs from CPU divided by host elapsed time. Startup/NLP/backend
construction are separate; full recurring costs include predictor, reference, warm start, solve,
gains, validation and packet overhead. A launch-cohort boundary charges each observed full call,
including a terminal physically pending call, while explicitly censoring its physical completion.

Hard gates preserve finite/model/actuator/grip validity, chronology and authority, no recorded
boundary crossing, slack ≤1e-6 m, no unexplained preparation/solver/model failure or unapproved
fallback, and no exhaustion in a run labelled successful. A model-valid simulation is not continuous
swept-body safety. Stop the affected branch and retain evidence; do not silently repair or rerun.

| Provisional research criterion | Threshold | Interpretation |
|---|---|---|
| Complete lap vs matched A | target ≤+1%; maximum +3% | Requires an actual complete lap; short pilots cannot satisfy this gate |
| Lateral/heading RMS | ≤+20%, with justified absolute floors | Floors require review before dependent acceptance; no inflated ratios near zero |
| Applied steering TV | ≤+15% | Common physical coverage; absolute tolerance required near zero |
| Peak tire utilization, each axle | ≤A+0.05 absolute | Physical validity independently mandatory |
| Sector degradation | investigate >5% | Preserve incomplete sectors; no extrapolation |
| Peak beta and tracking peaks | independently justified thresholds | Unresolved values block candidate acceptance, not permission to invent them |
| Normal reserve | ≥0.20 s; no normal sample <0.05 s | Evaluate native trajectory-mode samples/endpoints and acceptances; report time below each level |
| Fixed commitment miss fraction / streak | ≤0.5% / ≤2 consecutive | Long enough measured coverage and clustered uncertainty required |
| C70 preparation p95 / p99 | ≤60 / ≤70 ms | Provisional targets, not proven bounds or installed deadlines |

These numerical research criteria remain **provisional**. Architecture A's fixed-commitment miss
rate is **not applicable**, not zero. Planner-busy opportunities, codriver busy ticks, late/invalid
handoffs and loss of authority are distinct. A successful run below a provisional performance target
still requires comparison review; passing does not promote a production profile.

## 3. Matched evidence, uncertainty and censoring

Match source/fixture/environment, initial conditions, gamma, delay policy, physical window and
all frozen mathematics except the declared factor. Use new matched A measurements for a future
host-cost comparison rather than pretending old timing is contemporaneous. Controlled timing
isolates numerical/controller changes; fresh measured timing evaluates availability consequences.
Retain every outlier, failure and incomplete package. Do not extend or replace an unfavourable run.

Propose at least ten independent fresh runs per measured arm in balanced AB/BA blocks, predeclared
before results. Report per-run and paired differences with 95% whole-run/block bootstrap intervals;
within-run solver samples are correlated. Quantiles use nearest rank. p99/reliability interpretation
requires at least 1,000 calls/due deadlines respectively across at least ten runs, and remains limited
by correlation and tail coverage. Short experiments give descriptive counts, not proof of ≤0.5%
miss probability or hard-real-time deadlines. Larger counts require separate budget/authorization.

Report full coverage and a common physical-time window plus a separate common-progress comparison.
Do not normalize truncated TV into a claimed gain or compare own-reference tracking as racing
superiority. First seam from rolling start is partial. Lap time is between subsequent crossings;
state extrema use native integration endpoints, not display interpolation. Missing/censored values
are null with reasons. Pending fixed deadlines beyond coverage are censored; observed misses and
ready-but-rejected authority remain explicit.

Absolute floors must be predeclared from an independently assessed sampling/reconstruction error
bound and the smallest scientifically material SI difference. For RMS above its approved floor,
use C≤1.2A. Below it, report absolute errors and require C−A≤0.2×floor; no relative improvement
claim. F0 deliberately leaves numerical floor and peak thresholds null pending that justification.
This is an explicit prerequisite for acceptance studies, not an unresolved runtime setting.

## 4. First proposed experiment: preparation profiling

The [profiling protocol](task007f/f0/profiling_protocol.json) proposes two complementary views:

1. Ten fresh two-second A workers: real closed-loop physical duration for CPU/simulated-s and
   complete-preparation wall latency; measured planner availability and imposed 5 ms codriver as
   an evaluation condition, not a new controller default.
2. Ten fresh diagnostic workers over twelve predeclared release contexts: four straight, four
   sustained corner, four transition. Select from valid retained A history by geometry/progress,
   never by solver cost. Report per-call CPU/wall only; this offline panel has no simulated duration.

Exact context IDs/hashes, warm-state recoverability and selection rules need review before any
execution. If raw evidence lacks the optimizer warm-start state, a cold panel must be labelled and
approved; do not claim faithful recurring preparation from guessed state. No panel was created here.

Use monotonic wall and process CPU clocks. Separate one-time graph/backend construction from
recurring predictor, preview/reference, warm-start, parameter packing, IPOPT, validation, 100 Hz gain
preparation, packet creation and residual overhead. Existing timers are nested; do not sum preview
children twice or solver internals on top of the full adapter. The present planner total stops before
final replacement/return assembly: any full-call wrapper retains this historical field and explicitly
measures the boundary difference. Missing phase coverage is unknown, not zero.

Future instrumentation requires numerical/physical/authority/RK4 parity under zero/injected timing
before measured use. Clock overhead and changed measured readiness are reported honestly; measured
wall-time equality is not a parity assertion. No new scheduler events, future-truth inputs, disk
export inside the kernel or simultaneous rendering/tests. Existing SINGLE backend configuration
must occur before numeric imports, with actual process/backend observations and limits recorded.

## 5. Nonuniform grid and later research order

The [temporal-grid audit](task007f/f0/temporal_grid_audit.md) covers all mandatory implementations,
cost derivation, steering-time convention, warm starts, geometry/domain coverage and asynchronous
compatibility. The [matrix](task007f/f0/experiment_matrix.json) retains A, E-G1–G4 and reviewable
ablations. **E-G1 is the first proposed grid candidate** after profiling and separately approved
preceding low-risk investigations. Its 88→68 variables (−22.7%) do not imply runtime savings:
matched ≤25 ms integration retains 32 substeps and H=0.8 retains about 80 gain intervals.

The present NLP uses scalar dt, node-based costs/slacks and one-column warm starts. Nonuniform
support needs explicit duration vectors and cumulative timestamps. Four fixed substeps coarsen
internal integration to 50/75 ms on 0.2/0.3 s intervals; matching A's 25 ms resolution yields total
substeps A/G1/G2/G3/G4 = **32/32/48/64/96**. Longer H increases TVLQR work independently of N.
Steering increments at interval starts are separated by the preceding interval, and the first-input
slew budget needs review. A blanket substitution of dt by the current stage length would hide this.

Research order: profiling → separate overhead/cache/solver-option/warm-start/compilation studies →
G1 nonuniform grid → move blocking/shortened independent controls → independently validated bounded-
suboptimal IPOPT → combinations only after isolated benefit. Profiling may justify reordering 2–4
through Engineering Review. Solver options and compilation are not presumed mathematically neutral.
An early iterate cannot be accepted without independent numerical, physical, preparation/gain and
application-authority validation. No such termination implementation is authorized here.

## 6. Resources, preservation and Safety S0

[Resource and review gates](task007f/f0/resource_and_review_gates.json) propose a 20-minute host
allocation and 1 GiB output reservation for the initial 20-worker profiling plan (ten short runs plus
ten context panels); these are planning ceilings, not runtime estimates or execution authorization.
Require at least 1 GiB remaining free **plus remaining output headroom**, inspect all measurement
guards and active processes, run fresh sequential SINGLE workers, and stop starting new work on
resource shortfall. Do not reduce repetitions based on outcomes. A later two-arm screening contrast
has a separate proposed ten-per-arm ×2 s cap; full laps/tail-reliability campaigns require new review.

Frozen A's observed controlled/measured laps are 31.171900/31.317756 s. Historical C70 controlled
31.172038 s differs by only 0.138 ms, below the 5 ms native crossing reconstruction scale. Its
measured run exhausted at 48.670 s: 485 releases, 455 accepts, 30 misses including eight terminal,
packet 477 expiry and vx=5.960492971 m/s outside baseline admission. No completed measured C70
lap; later export failure is separate and remains incomplete. See the immutable
[VIS closure](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/docs/TASK007E0_VIS1_CLOSURE.md)
and [fallback audit](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/docs/TASK007E1_FALLBACK_DOMAIN_AUDIT.md).
This negative evidence cannot be discarded or described as a host-runtime root cause proven by a tail.

Safety S0 terminology: release is sampled causal context; ready is completed preparation;
accepted authority is buffer ownership over a valid interval; applied command is physical input with
its original request provenance; reserve is time until active expiry; loss of valid trajectory is not
safe stopping. Existing fallback admission is 1–3 m/s and center-corridor containment; no guarantee
of recovery, uninterrupted authority, standstill braking, application-time eligibility or swept-body
safety. No Safety implementation occurs in F0. Hardware identification, sensors, actuator supervision,
watchdog/emergency-stop, continuous safety and device timing remain separate versioned gates in
[the accepted limitations](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/docs/task007e/e3/remaining_limitations.json).
Mac SINGLE results cannot certify target hardware.

## 7. Verification and handoff

Only static JSON/structure/link/source/hash, Git-ref/protection and preservation checks are executed.
[Validation](task007f/f0/validation.json) records exact scope and inherited E3 evidence (750 passes,
633.76 s), not a new test execution. Source/configuration/tests/fixtures and accepted manifest remain
unchanged; no numerical modules or solver constructors are needed for these checks. Historical
files remain intact. Git refs protect tracked snapshots only: ignored raw histories, environment,
solver binaries and machine state still need a separately authorized content-hashed independent
backup. Metadata preservation is not a content-hash backup claim.

Outstanding decisions before dependent work: metric floors and peak thresholds, recoverable profiling
contexts, instrumentation boundaries/parity, objective/slack quadrature, first/inter-stage slew-time
convention, time-based warm-start extension, coarse-node/curvature validity and ablation budgets.
The specification makes these decisions explicit; none is silently implemented. Review F0 before
authorizing any Efficiency code or profiling. **Stop at WORK_COMPLETE_PENDING_REVIEW.**
