# Task007D-VIS protocol — VIS-0 review proposal

**Stage:** WORK, documentation only. **Status:** `WORK_COMPLETE_PENDING_REVIEW`.
**Audited baseline:** `f072052cd4481df6d987deb6d8d721f1b1b99cb2`, clean `main` at entry.
**Reviewed scientific source:** `935e98b7af6c2fda8458551f1fbcbddb3bf8932d`.
The baseline's later changes are verification documentation. This proposal implements nothing
and authorizes no experiments. VIS-1 needs Engineering Review and a new assignment; VIS-2 needs
successful VIS-1 review and separate authorization. VIS-3 export/rendering and VIS-4 formal
verification also remain unstarted. The containing documentation commit is reported after push.

Authority: Primary APEX's supplied full-lap/holdout specification, narrowed by its accompanying
VIS-0 assignment. A remains the reference and intended synthetic Performance direction; C70
remains experimental. No architecture promotion, Performance freeze, Efficiency optimization,
B/lightweight prediction, retuning or new physical features are proposed. Work follows the
[verification workflow](CODEX_VERIFICATION_WORKFLOW.md) and [test guide](CODEX_TEST_GUIDE.md).
The parent request to agree a Workbench schema is a later integration dependency: VIS-0 permits
only the [standalone proposal](TASK007D_VIS_WORKBENCH_CONTRACT_PROPOSAL.md), pending Workbench review.

## 1. Evidence basis and frozen configuration

Read with the [reuse audit](TASK007D_VIS_REUSE_AUDIT.md),
[Task007C results](TASK007C_RESUMED_RESULTS.md), [C results](TASK007D_C_RESULTS.md),
[CX results](TASK007D_CX_RESULTS.md) and [CX verification](TASK007D_CX_VERIFICATION.md).
CX's short runs do not establish full-lap completion or a production winner. Its C70 10/189
misses and C80 3/185 misses, including 120.735/337.787 ms preparation tails, remain historical
evidence; this proposal neither deletes nor repeats them. No new N4 campaign is needed.

| Item | Frozen value or source |
|---|---|
| Formulation | N=8, dt=0.1 s, H=0.8 s; alpha_vy=alpha_r=1; lambda_s=0 |
| Costs | Q=diag(4,4,1,200,200) on [vx,vy,r,e_psi,e_y]; R=diag(25,1); W=diag(1,0.1) |
| Construction | `scripts/task007dcx/worker.py::frozen_config`, existing terminal construction, IPOPT options and warm starts |
| Predictor / reference | Legacy A only; `committed_prefix_prediction=False`; gamma=2.0, unchanged offline Planning package |
| A | `fixed_handoff_offset=None`; rolling estimator and variable-availability handoff unchanged |
| C70 | `fixed_handoff_offset=0.070`; prescribed target release+70 ms, including accepted urgent-grid, miss, busy, reserve and fallback rules |
| Rates / physics | Existing 100 Hz TVLQR, nominal 10 Hz planner and 5 ms maximum plant step; unchanged RK4 event partitioning, model, tires, actuator/track constraints |
| Vehicle / margins | Existing synthetic dynamic vehicle; 0.08 m synthetic tracking margin, not certified clearance |
| Timing isolation | Fresh sequential SINGLE workers; actual backend/process-thread observations retained |
| Initial state | Existing worker convention at s_abs=1 m: [v_ref,0,v_ref*kappa_ref,e_psi_ref,1,e_y_ref]; startup preparation/prepositioning remains gated |

A and C70 deliberately have different forecast targets. An observed difference cannot be
attributed to fixed scheduling alone. Solver readiness, accepted authority, first TVLQR use and
physical command application remain different events. Pending commands from an old packet survive
handoff with their original source identity. No timing or controller defaults change.

### Exact identity anchors

All five package files in `configs/planning/task007b/gamma_2p000/` are byte-identical to their
counterparts in `configs/planning/task007c_resume/gamma_2p000/` at this audit. This establishes
fixture compatibility, not timing/source equivalence of every historical run. Track length is
154.76345492731022 m; left/right half-widths are each 0.55 m.

| File, relative to gamma_2p000 unless otherwise stated | SHA256 |
|---|---|
| track_source.json | `5f4d1734d7fec7de56d346e8f90bf272a3de9c05ac42f76cd49004e7f9183e55` |
| planning_reference.csv | `6206e18ce3cb105d58d0923564336e28c00ec44aee3fd8a06ff7a37bcf84e2df` |
| planning_manifest.json | `5e7bccf1a300fb6737fc6b6b6e0c9aa921c110b11ffc5762a73f57f830a8660c` |
| speed_polynomial.json | `f335e78fc6c735c952f49078077a573ee989dd2be71497e90451e34a79f2c7ea` |
| planning_validation.json | `279582d2dcf37fdf4008ddc7f926109ef3d730a0e64c188d7003755d08871fa7` |
| configs/vehicles/synthetic_dynamic_test_vehicle.yaml | `df1b853d21a1d3efaf858f7e58401151f2c5237793c40e16bb4189ed651f9cf3` |
| src/apex/simulation/asynchronous.py | `7d14395aa27707f2561bf6bdb32cd613bc2508ab12d6fe617bf45855d378f018` |
| src/apex/simulation/fixed_handoff.py | `8f0bc766b6a7c446f36b6a49f6214864906acbb067c57c977469b54e3ff07c12` |
| src/apex/control/trajectory/prediction.py | `0013fd74299a68993dabbc381ca384837f09b862011956a94fd1d3b138b839ab` |
| src/apex/control/trajectory/planner.py | `6dcc8abe959fa65d7036f90379179703f54091c55a54bedee4db9a47d4622e44` |
| src/apex/control/trajectory/tracker.py | `ffa5d9968650c97411121ba3dedd89a5de04a1a9ce832c50efa351763567ef27` |
| src/apex/control/mpc/problem.py | `b0560718155ff04074633aa92c4374a15ec975f21f5e3a022f4e94d52636087e` |
| scripts/task007dcx/worker.py | `7e581738fe4102fb002fec2cfdf2f586d3a8f0f6c5f6e98bfeb3831bcf72e71b` |
| uv.lock | `8cf85868a456415a898643dbb226d146b0b90e5c98982136cf2abf2465fa16ec` |

The existing complete source/environment inventories remain in
[CX provenance](task007d/cx/tables/provenance.json) and
[formal preservation record](task007d/cx/formal/verification.json). Future workers must save their
own Git SHA, dirty diff if any, full source/test/config/fixture hashes, serialized MPC/TVLQR/async
settings, actual initial state, dependency/backend/OS versions, native-thread controls and
observations, timing arrays, seed (`null` for deterministic fixtures), logs and stop outcomes.
Use existing defaults only after asserting their serialized values against the reviewed freeze.

## 2. Proposed bounded matrix — requires approval

Recommend **eight runs per authorized track: two short parity runs plus six long runs**.
Two measured repetitions per architecture are the smallest order-balanced repeated visual pilot;
they cannot estimate population tail reliability. One controlled pair isolates imposed-history
behavior. No repetitions are added or removed because of favorable or unfavorable outcomes.

| Phase | A runs | C70 runs | Physical budget per run | Timing |
|---|---:|---:|---|---|
| Short prerequisite parity | 1 | 1 | 2 s | Same predeclared controlled pattern below |
| Controlled full-lap pair | 1 | 1 | Two seam crossings; 80 s hard cap | Planner pattern 35,55,45,25 ms; codriver 5 ms |
| Measured full-lap pair 1 | 1 | 1 | Two seam crossings; 80 s hard cap | Actual measured total preparation; codriver imposed 5 ms |
| Measured full-lap pair 2 | 1 | 1 | Two seam crossings; 80 s hard cap | Same measured policy, fresh workers |

VIS-1 uses the existing gamma2 package. VIS-2 would use exactly this matrix on one independently
frozen holdout, only after its own authorization and geometry/reference prerequisite pass.
Thus the conditional parent budget is 16 runs, not a currently authorized campaign. No C80,
gamma sweep, additional laps, pathological timing histories or N4 reruns are included.

Controlled order: short A,C70, then long A,C70. Measured pair orders: A,C70 then C70,A. No concurrent
analysis/rendering/tests. The controlled pattern is the already declared C3 gamma2 pattern in
[retained protocol](task007d/c/amended/protocol.json); it is a deliberately synthetic sub-deadline
history, not a measured trace or a claim about real deadline reliability. Materialize 8,001 planner
entries and 8,001 codriver entries before either run, hash/save them, and never alter them after
outcomes. This covers an 80 s cap at the 100 Hz control grid; positive minimum planner delay
25 ms and single-solve operation also bound any extra urgent launches below that entry budget.
The API indexes planner delays by actual launch ID, not nominal tick. If launches diverge, report
this and compare physical timestamps/progress; do not claim matching launch IDs mean matching
release states. Never pad, loop or select favorable parts of historical measured traces.

The measured series measures the planner only: codriver latency stays imposed at 5 ms as in CX.
Save actual codriver computation times descriptively, separately from its physical 5 ms delay.
This is not an all-components measured-latency study. Do not substitute replay for fresh measured
preparation or mix controlled and measured populations. Record startup cost separately.

Before long runs, check the new short observer/export path against applicable retained C3 records
(`results/task007d/c/amended/C3_g2.0_variable/` and `C3_g2.0_fixed70/`) using a source/fixture audit.
Historical urgent-bookkeeping differences require explicit applicability analysis, as in CX reuse;
do not assume equal filenames prove parity. Require exact unchanged event/physical results under
identical deterministic inputs; host timings are excluded. If an applicable comparator cannot be
established, report the gap for review rather than treating a new output as its own baseline.

### Lap and comparison rules

`AsyncConfig.laps` counts seam crossings. From s_abs=1 m, crossing 1 is a partial rolling segment;
crossings 1→2 provide the first genuinely complete geometric lap. Set `laps=2` and retain both
segments. Exclude the partial first traversal from the primary complete-lap table, but retain all
its validity/timing evidence. The subsequent lap is called post-transient by this operational
definition, not a claim that a periodic steady state has been proved.

The runner derives crossing times by linear progress interpolation inside the final RK4 step.
Its final post-step state may be absent from `raw.states`; retain the existing `RecordedPlant`
step bracket and final state so coverage can be proved without changing the physical schedule.
Label crossing times derived and report the bracket duration. Do not manufacture a sampled state
exactly at the seam. Use native samples for validity extrema; do not let plotting interpolation
turn derived crossing positions into ground truth.

Report whole-run, initial partial traversal, complete lap and named sector traversals separately.
Sectors come from each frozen manifest. Reset differences at lap/sector boundaries. A terminated
or capped run is incomplete/censored even when a shorter interval looks smoother. Compare common
observed physical-time and unwrapped-progress coverage; record both bounds and never extrapolate.
Use native timestamps for chronology and extrema, native traversal metrics for quality, and label
any optional aligned display grid as derived. Retain RK4 segment boundaries and first divergence.

For each architecture report six-state APEX→vehicle RMS/max with wrapped heading residuals,
Planning→APEX adaptation and Planning→vehicle deviation separately; lap times/progress rate;
front/rear tire utilization, beta, Frenet margin, sampled left/right clearance and limiting location;
predicted slack; actual/nominal steering and both world/Frenet heading TV; rate occupancy/reversals,
acceleration variation; accepted latency, preparation distributions, misses/rejections, reserve,
packet age, fallback and censored cycles. Own-reference tracking improvement alone does not prove
a better racing line. Existing empirical p99 stays null below 100 samples; even larger within-run
samples are correlated. Preserve per-run distributions and all outliers rather than claiming
independent repeated-trial confidence from thousands of solver cycles.

## 3. Resource estimate, not a new benchmark

Observed records read during VIS-0:

| Evidence | Historical observation | Applicability |
|---|---|---|
| `results/task007c_resume/g2_w0_vy1_r1_n8_measured_l1_rep00` through `rep04` | Partial rolling traversal 30.932–30.963 s; 308–309 runtime launches; peak RSS 187.59–214.94 MiB | Same fixture bytes; historical source and measured codriver differ from proposed VIS |
| `results/task007c_resume/measured_events_g2_n4_n6_n8.jsonl` | Dispatch-to-result elapsed 85.356715,85.402370,86.226773,84.752942,84.483439 s for those N8 runs | End-to-end journal interval includes startup/export, not pure solver or real-time timing |
| `g2_w0_vy1_r1_n8_fixed_l3/summary.json` and `smooth_l3/summary.json` under the same root | Subsequent full laps 31.185/31.173 s and 31.152/31.123 s; peak RSS about 314/340 MiB | Three crossings, not three complete laps; fixed/smooth historical cases |
| Same raw run directories | About 31 MiB for ordinary one-crossing captured runs; 90–92 MiB for sustained three-crossing runs; some rendered folders 50–51 MiB | Directory sizes include existing exports/figures where present, not uniform raw-only sizes |
| CX 2 s measured A/C70 summaries | Worker `wall_seconds` roughly 3.67–3.78 s; run folders about 1.5 MiB | Timer covers `AsyncRunner.run`, excludes construction and offline export; cannot replace whole-process estimate |

Extrapolation for the existing track: about 62 s physical time per long run, roughly 620 runtime
preparations at 10 Hz plus startup (busy misses reduce and urgent launches can increase counts).
At the 80 s cap there are about 800 nominal opportunities, not a promise of 800 actual solves.
Historical cost implies about 85 s host elapsed per 31 s traversal, or about 170 s for two;
budget **3–5 minutes per long run** for capture/longer C70 targets and host variation. There is no
measured full-lap C70 runtime yet. Six long runs imply roughly 3,720 runtime preparations and
18–30 minutes, plus two short runs, focused tests and offline analysis. A full physical lap alone
would cost roughly 1–2 minutes by extrapolation, but each run must retain its rolling transient.

Budget **60–120 MiB per long run**, about 0.4–0.8 GiB per-track raw/export data before rendered
media; allow **1.5 GiB per track** including compact plots and working files. Conditional two-track
work is approximately 36–60 minutes of runs and 3 GiB disk allocation, not a runtime guarantee.
Peak worker RSS was below 0.35 GiB in retained sustained cases; budget 0.5–1 GiB for the proposed
capture and 1–2 GiB for one-run-at-a-time offline analysis. These are reservations, not measurements.
No credible separate figure/video timing record was identified; do not quote an invented render
duration. Optional video size/time requires separate budgeting after schema/renderer review.

At VIS-0 entry about 7.30 GiB was free. Recheck before execution and each worker: preserve the
**1 GiB free-space floor**, require enough additional headroom for the planned track budget, inspect
all `results/**/MEASURED_ACTIVE`, `results/task007d/D3_ACTIVE` and actual processes. Never clear an
unknown guard or delete old evidence. Pause for resources instead of shrinking repetitions after
outcomes. Any budget change requires a recorded review before the affected runs. Use fresh,
exclusive directories proposed under `results/task007d/vis/`; compact reviewed exports later under
`docs/task007d/vis/`. Do not overwrite any earlier Task007 artifact.

## 4. Prerequisites and stop gates

These are future tests, **not executed in VIS-0**. Run affected focused prerequisites under the
existing SINGLE bootstrap before dependent experiments, retaining full logs. No blanket full-suite
run is needed for this documentation stage. Formal broad regression belongs to authorized VIS-4.

| Requirement | Existing focused tests, relative to tests/ | Needed addition in later research code |
|---|---|---|
| Canonical/model/tire validity | unit/test_state.py, test_config.py, test_dynamic_bicycle.py, test_grip_tire.py; integration/test_dynamic_track.py, test_grip_tracking.py | Assert frozen constructor/limits and independent observer noninterference |
| NMPC/predictor initialization | unit/test_mpc.py, test_progress_objective.py, test_trajectory_tracker.py, test_cx_closure.py | Exact active A forecast→NMPC input and startup parity; no future truth input |
| Chronology/deadlines | unit/test_async_chronology.py, test_diagnostic_timing.py, test_fixed_handoff_contract.py, test_fixed_handoff_scheduler.py | Preserve default A, C70 urgent grid/misses and pending old-command identity through export |
| RK4 / diagnostic sampling | unit/test_prediction_diagnostics.py, test_task007c_physics.py, test_cx_closure.py | Terminal step bracket, no new physical partition, missing/censored samples |
| Track/reference loading | unit/test_track_geometry.py, test_track_io.py, test_frenet.py, test_planning_reference.py, test_aggressive_reference.py; regression/test_geometry_accuracy.py | Holdout seam/intersection/corridor fixtures before VIS-2 |
| Sector/lap/metrics/export | unit/test_task007b_export.py, test_task007c_metrics.py, test_task007c_physics.py, test_fixed_handoff_analysis.py, test_cx_closure.py | Partial first lap, two-crossing completion, native interval clipping, optional fields/nulls, six-state/clock round trips, endpoint/extrema preservation |
| Resources | unit/test_threading_study.py | Strict fresh folder, guards/disk-floor checks and serialized frozen protocol |

Bare test names in a row inherit its `unit/` prefix; explicit integration/regression paths do not.
Keep existing mathematical assertions and tolerances; new extraction tests need documented
round-trip/clock tolerances, not relaxed physical limits. The inherited 709-test CX verification
is historical evidence, not a newly run VIS prerequisite pass.

Stop the affected branch and preserve logs/raw partial output on boundary crossing; any predicted
slack >1e-6 m; solver/preparation/model-domain failure; failed prerequisite; nonfinite or invalid
geometry/reference; future-information leakage; timestamp inversion or wrong packet authority;
unexplained exhaustion, reserve exhaustion or fallback; invalid native-thread isolation; corrupt
or missing required coverage/provenance. Do not silently repair executable semantics to proceed.
Use the existing actuator/model bounds and reserve warning/critical/minimum-acceptance rules
(0.20/0.05/0.05 s); no new beta or tire-utilization failure threshold is invented.

An ordinary C70 deadline miss with valid old-packet continuation is an outcome, not automatically
a failure: preserve every miss, busy interval, late discard, accepted recovery or censoring. Worse
tracking/TV/lap time or lower positive clearance is also an unfavorable result to report. Clearance
below the 0.08 m design margin is reported explicitly; the existing physical boundary gate is not
silently redefined as a new margin gate. An 80 s cap without two crossings is incomplete and stops
expansion for review, not permission to extend the run. A successful `target_laps` termination must
be distinguished from failure by a tested research-only gate adapter; the short-pilot gate currently
expects `duration`. Preserve all validity checks in that adapter.

## 5. Holdout concept and validation, conditional on VIS-2

Feasible with the existing closed-spline and Planning schema, but not by calling the hardcoded
Grand Prix reference generator unchanged. Propose an asymmetric elongated loop with a long bend,
an opposite-direction medium corner and a separated left/right transition in a different sequence
from Grand Prix; it must not be a rotation, translation or scaling of the old points. Keep the
0.55 m half-widths and vehicle/Planning conventions. Aim for comparable length for budgeting;
actual geometry/sector anchors must be declared and frozen before controller outcomes, with an
independent reference-only audit. No coordinates or new fixture have been generated in VIS-0.

Minimum objective validation before any controller run:

- Use `PeriodicCenterline`/`ClosedTrack` construction checks and seam tests: finite nondegenerate
  points, regular tangents, periodic position/heading/curvature and arc length. Preserve existing
  tolerances; report curvature extrema and validation sampling resolution.
- Check centerline, both offset boundaries and racing line for nonadjacent crossings, touches and
  overlapping segments, including the seam. The existing `intersection_count` checks sampled proper
  intersections only; it is not a continuous spline certificate. A small fixture-specific adaptive
  geometric audit must account for interpolation error and ambiguous near contacts; ambiguity
  blocks fixture acceptance rather than being hidden behind a coarse plot.
- Require positive widths, separated corridor branches and valid Frenet geometry throughout the
  reference/corridor validation. Apply existing reference denominator >0.1, cos(e_psi)>0.2 and
  0.08 m nominal clearance checks; inspect projection/seam uniqueness. Runtime model guards remain
  independent. Sampled clearance never certifies continuous swept-body safety.
- Preserve schema v1, SI/body-speed/heading conventions, track hash, monotone 0→L samples with
  spacing at most 0.1 m and existing seam/geometry tolerances. Load through `PlanningReference`;
  retain warnings from the established advisory feasibility policy, not new silent speed tuning.
- Reuse the existing offline geometric-offset and speed-envelope method (base acceleration/braking
  passes, gamma2 scaling and exact 6 m/s cap polynomial). Replace only fixture-specific corner/sector
  anchor data and paths. Keep finite speed within the existing 0.5–6 m/s domain; preserve all
  validation diagnostics. If the method cannot validate the fixture without semantic changes,
  stop for review. Do not adjust gamma or costs to make a controller finish.
- Generate deterministically, record ordered source points/anchor data, generator source/environment,
  all five package hashes and validation reports. A repeated reference-only build must agree.
  Freeze one package for both architectures before running either. Any later geometry/reference
  correction invalidates that holdout experiment and needs review; retain the failed version.

## 6. Review decisions and next assignment

Engineering Review should approve or amend the eight-run VIS-1 budget, 80 s cap, controlled pattern,
two measured repetitions with imposed 5 ms codriver latency, lap-window definition and resource
reservation **before outcomes**. The Workbench owner must review schema version, clock conventions,
payload size and required optional channels before claiming compatibility. Exact identities of the
external five-document APEX package were not established from repository files; request those
document links for later cross-references rather than inventing them. This does not block VIS-0.

Recommended VIS-1 assignment: implement the smallest research-only launcher/worker and export/window
adapters identified in the reuse audit; preserve core and historical scripts; add focused extraction,
parity and gate tests; then execute only the reviewed existing-track matrix after prerequisites.
Stop on any gate and return evidence for review. VIS-2 fixture creation, VIS-3 media/UI integration,
VIS-4 broad verification and all later controller work remain separate decisions.
