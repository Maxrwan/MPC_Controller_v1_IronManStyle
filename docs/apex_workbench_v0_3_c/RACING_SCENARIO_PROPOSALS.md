# V0.3-C racing-scenario proposals

**DESIGN ONLY — PENDING PRIMARY SCIENTIFIC REVIEW.** Static inspection at source base
`ccd19549a9b3e25d1a5bd2c037a27090eda8dccf`, prepared on branch `codex/apex-workbench-v0-3-c`,
29 October 2026. No project imports, tests, calculations, reference generation, simulations,
new executable scenarios or qualification executions were performed for this document.
The authoritative [handoff](../CODEX_HANDOFF.md) records V0.3-B as verified with final user
acceptance pending. V0.2's accepted finite qualification remains unchanged and does not
extend to any proposal here.

## Minimal complementary shortlist

| Priority | Proposed engineering use | Existing support / missing work |
|---|---|---|
| 1 | **Variable-curvature tracking on the existing oval**, using the unchanged nominal Task005 LQR/PI composition at 2 m/s | Already an executable Workbench `lqr_baseline` choice. It adds useful variety relative to the circular laboratory without new geometry or controller mathematics. Inspect/reuse existing evidence first; a new run is not qualified by V0.2 Q. |
| 2 | **Retained GP sector investigation**, covering straight-to-hairpin, direction changes and a short sector with one original run | Existing full closed geometry, offline references, native histories and sector definitions. Needs a separately reviewed archive/profile mapping before Workbench inspection; no execution adapter exists. Select views of original evidence, preserving its source and full history. |
| 3 | **Rolling straight acceleration/deceleration and isolated turn-in response** | Canonical dynamic model, integer-grid prescribed-input mechanism and analytical component oracles exist. No accepted straight/turn-in executable preset exists. Exact geometry, input transitions, duration and numerical criteria remain a separate scientific contract decision. |

Do not create five presets by changing waypoint shapes. A standalone hairpin, chicane or new
representative sector is deferred: the existing GP can supply complementary retained examples
first. Successful plotting or a completed trajectory supplies neither new qualification nor
controller robustness/stability evidence. Required decisions are in [SCIENTIFIC_DECISIONS.md](SCIENTIFIC_DECISIONS.md).

## Canonical compositions and geometry

All state vectors retain `[vx, vy, r, e_psi, s_abs, e_y]`; inputs retain `[delta, a_cmd]`.
Body lateral velocity, steering, yaw and Frenet lateral offset are left-positive; angles are
radians, progress/positions metres and time seconds. `s_abs` is nonnegative unwrapped
centerline arc progress; only geometry/reference queries wrap. Dynamic `a_cmd=Fx_total/m`
and `dvx/dt=a_cmd+r*vy`. It is not generally a prescribed body-speed derivative.

| Contract | Exact existing mechanism and intended use |
|---|---|
| **L — low-slip dynamic response / centerline baseline** | NumPy `DynamicBicycle`, `LinearAxleTire`, `QuasiStaticLongitudinalLoadTransfer`, synthetic dynamic YAML. The legacy linear default has no longitudinal allocation; `mu` is diagnostic and forces are unsaturated. Open-loop schedules use a controller-protocol input provider and `SimulationRunner`. Closed-loop use is `BaselineController`: nominal steady small-slip feedforward plus `ScheduledLQR`, separate `SpeedPI`, perfect state, 0.010 s control / 0.005 s plant, zero-order-held applied commands. This scheduled LQR is distinct from TVLQR. |
| **G — historical conservative racing-reference baseline** | Task007A's explicit smooth combined-grip `DynamicBicycle` plant and independent CasADi `SymbolicBicycle` prediction, `RACING_TIRE_PHYSICS` with normal-load-proportional longitudinal allocation, `PlanningReference`, always-active APEX Candidate C, N=4 / 0.1 s / four RK4 substeps, progress weight zero, original costs, warm-start IPOPT, one native thread, 0.08 m tracker margin, `TrajectoryPlanner` / packet buffer / `TrajectoryTracker` TVLQR at 100 Hz, `AsyncRunner` plant steps at most 0.005 s. The exact existing composition is `scripts/task007a/run.py`, including its external Candidate-C configuration dependency. It is a future adapter candidate, not a current Workbench launch option or a new qualified profile. |
| **P — separately accepted Performance reference** | [Performance Synthetic v1](../TASK007E4_PERFORMANCE_ACCEPTANCE.md), exact verified scientific source `e603672b209985f11ed26b6f44d3949ffd5675c5`: Architecture A, N8 / 0.1 s / 0.8 s, gamma2 Planning, progress weight zero, original predictor A, 100 Hz TVLQR and the complete manifest-bound conditions. Its evaluation initial state, delay pattern and stop protocol belong to that original evidence. Current Workbench runtime bytes do not acquire P's exact-source identity from configuration resemblance. Do not combine P's N8/gamma2 with G's startup, reference or results. |

Known L/G synthetic vehicle values are inherited from
[`synthetic_dynamic_test_vehicle.yaml`](../../configs/vehicles/synthetic_dynamic_test_vehicle.yaml):
mass 2 kg, yaw inertia 0.025 kg m², wheelbase 0.30 m, lf/lr 0.15/0.15 m, CG height
0.04 m, front/rear axle stiffness 45/45 N/rad, mu=1, configured steering bound 0.4 rad,
acceleration/braking bounds +2/−3 m/s² and speed bound 6 m/s. These are software fixtures,
not identified APEX values or newly approved operating ranges. Vehicle width/length and
YAML steering-rate limit are unspecified. G/P's controller rate limit comes from their
controller configuration; it does not identify a physical steering actuator.

The existing `KinematicBicycle` may support a separate geometry oracle, not the proposed
racing plant: vy/r are algebraic, its `a_cmd=dvx/dt`, and its stop-at-zero policy has no
dynamic braking-force interpretation. Do not silently switch models when dynamic braking
reaches the low-speed guard.

| Asset | Representation / validity / exact reuse |
|---|---|
| Circle / oval | `run_lqr_baseline.make_track`: radius-5-m circle with 64 waypoints and half-widths 0.6/0.9 m; oval is 72 radius-one circle points scaled by `[7,3]`, half-widths 0.3/0.5 m. `ClosedTrack.from_waypoints` constructs the actual periodic cubic spline. The oval is an ellipse-derived spline, not an exact analytical ellipse. |
| Synthetic GP | `configs/planning/synthetic_grand_prix_v1/track_source.json`: 43 ordered SI points, explicit constant half-widths 0.55/0.55 m. `planning_reference.track.load_track` uses the same canonical constructor. Public progress is numerical spline arc length. Named sectors and their start positions come from the committed manifest; nominal primitive radii/names are not exact spline curvature guarantees. |
| Straight | There is no production infinite-straight constructor or accepted straight-track asset. `straight_geometry` in tests is an analytical local test double. GP `long_straight` is an existing nominal straight sector of the closed spline; exact-zero curvature must not be assumed. |

A view window must retain the whole original periodic track/reference. Do not cut a sector's
points into a new periodic loop or reinterpret a cropped start as an independent equilibrium.
Waypoint order, seam regularity, nondegenerate tangent, spline overshoot, self-intersection,
offset-boundary topology and unique local projection require explicit checks for any future
geometry. The constructor does not prove absence of self-intersection or corridor overlap.

Located retained starting points are `results/lqr_baseline/oval_2mps/` and
`results/task007a/{measured,zero,injected}/`; the latter contain states, controls, plans,
packets, handoffs, reserves, misses, events and sector exports. Their presence and historical
summaries were inspected; no source/evidence applicability was newly certified. P's compact
original evidence index is [evidence_links.json](../task007e/e2/evidence_links.json).
The shared G diagnostic set is native state/input and reference channels; global-reference
versus packet errors; slips, axle forces/loads, lateral capacity and combined utilization;
centerline/racing curvature and D; solver status/infeasibility/slack; forecast/readiness
residuals; packet ID/age/reserve, handoffs, fallback, planner preparation and actual codriver
application/misses. Only genuinely retained channels may be displayed.

## Five family contracts

### 1. Straight-line acceleration/deceleration and turn-in

**Open-loop response**, with L as the proposed model and no feedback controller. Separate
the longitudinal response and steering-onset cases before considering combined braking and
turning. The dynamic-demo amplitudes/schedule and VDL steering onset are existing examples,
not an accepted schedule for a new straight asset. The fixed VDL registry must not be extended
or relabeled as this family.

Candidate initial-state form is `[v0,0,0,0,s0,0]` on an explicitly selected nominal straight
location, with a forward rolling speed. The existing 2 m/s synthetic seed can be proposed;
the actual track location, finite observation interval, acceleration/braking segments and
steering amplitude/onset require a reviewed versioned contract. Do not guess them or claim
the GP label supplies a straight-line guarantee. A minimal future adapter would inject the
approved existing Track, literal initial state and integer-tick `PrescribedInputs`-style
schedule into `SimulationRunner`, retaining canonical dynamics and raw failures.

Insight: distinguish longitudinal load redistribution, the `a_cmd`/body-acceleration distinction,
and the yaw/slip transient after turn-in. Primary signals: vx, vy, r, actual delta/a_cmd,
alpha_f/r, Fzf/r, Fyf/r, nominal/effective stiffness, lateral utilization, D, e_y and coverage.
Brake only within a separately qualified rolling window: the dynamic model cannot reach
standstill, reverse or provide stopping-distance claims. Closed-loop tracking would answer
a different question and would need a specified reference/provider and reference-relative errors.

Oracles: zero-steering/zero-slip body-motion identities and analytical axle-load/force/moment
balances; steering-sign symmetry where assumptions match; event-aligned numerical refinement.
On a truly straight analytical fixture the existing zero-slip acceleration solution is an
oracle for the component equations. On a curved spline its straight-coordinate progress
formula is not a Frenet oracle. See the shared qualification requirements below.

### 2. Straight-to-hairpin

**Closed-loop control is essential for a racing benchmark.** Prefer retained G or P GP
histories through `long_straight` and `hairpin`, using each history's original composition,
reference and startup. Manifest sector starts are 0 and 21.023586308047943 m; the hairpin
ends at the next sector start, 27.78530681910763 m. These are existing view boundaries,
not newly selected track dimensions or termination conditions.

For a future conservative execution proposal use G unchanged: the full existing offline
reference, not prescribed steering or a newly designed brake point. G initializes at s=1 m
as `[v_ref,0,v_ref*kappa_ref,e_psi_ref,1,e_y_ref]` sampled from the original package and
gates the rolling launch with a prepositioned first command. Do not initialize at the
hairpin by resetting vy/r, tracker history or planner warm start. Minimum adapter: bind
the existing G runner, exact candidate configuration/fixtures and native chronology to the
owned worker/evidence protocol; this still needs separate approval and qualification.

Insight: approach-speed lag, braking/turning demand, steering angle/rate activity, reference
approximation versus feasible local planning and local tracking. Use all shared G diagnostics,
especially both curvatures, global-reference errors versus packet errors, front/rear capacity,
slack, reserve and actual command application time. Approximate `v_ref²*|kappa_ref|` is a
reference demand diagnostic, not measured lateral acceleration or a sufficient feasibility test.
Oracles: original reference/geometry consistency, independent NumPy/CasADi model parity,
force/load identities, native chronology audit and refined plant integration with the same
documented timing protocol. No exact nonlinear hairpin trajectory oracle is available.

### 3. Left-right chicane

Use the existing GP `direction_change` or `technical_section` as a **candidate retained
direction-change investigation**, not a claim that either is an accepted standalone chicane
preset. Source anchors are 66.19665359010386–81.04324569067502 m and
97.27700976544726–123.38300452685894 m respectively. A later signed-curvature audit must
establish the intended left/right ordering and characterize the actual chosen window; this
design performed no curvature calculation.

For a future closed-loop proposal retain G's complete model/controller/reference and rolling
initialization from family 2. No new steering waveform, lane-change controller, time shift,
local restart or geometry is required for the retained investigation. A prescribed alternating
steering schedule would instead be a separately specified open-loop reversal experiment.
Standalone chicane point coordinates, widths, spacing and speed schedule remain unspecified.

Insight: direction-change feedforward/feedback interaction, steering slew, packet continuity,
and whether extra reversals arise in Planning intent, APEX packets or actual commands. Inspect
signed curvature, delta/raw/limited control, heading, vy/r, errors to each reference owner,
slip/utilization, handoffs/reserve and planner/codriver misses. Expected sign changes are not
automatically oscillation. No new reversal deadband, variation score or ranking threshold is
introduced. Oracles: geometry signs/seam checks, independently transcribed dynamics and native
event/application chronology; no analytical closed-loop chicane response exists.

### 4. Variable-radius sweeping corner

**First choice: existing oval with L closed-loop centerline tracking at ConstantSpeed(2).**
This is an already supported experiment composition, not a new racing preset. The precise
existing initial state is `[speed, ref.vy, ref.yaw_rate, 0, 0, 0]`, where
`ref=cornering_reference(p,speed,track.sample(0).curvature)`; default PI integral/previous
steering reset are retained. The existing Workbench example uses its unchanged 12 s duration,
2 m/s speed and zero initial e_y/e_psi defaults, with oval selected instead of circle. The optional existing core-script speed profile
`2+0.5*sin(2*pi*track_s/L)` is a separate reference condition and is not exposed by the
current Workbench form. Do not add it under a cosmetic preset.

Geometry changes along the ellipse-derived spline, giving a low-slip gain/reference tracking
study with no lookahead. Keep reference speeds in the existing [1,3] m/s domain and report
actual speed and scheduling clamps. The scheduled LQR reference is a nominal static-load
small-slip force balance, not an exact six-state path equilibrium; raw-heading steady bias
is expected and must remain visible. Primary signals: geometry curvature, vx/reference speed,
vy/r references, feedforward/feedback, gains/clamps, PI state, saturation/rate flags,
e_y/e_psi, native full/settled coverage and boundary/domain outcomes. Canonical tire diagnostics
are useful only when genuinely exported by the applicable profile; missing data stays missing.

No software adapter is needed for the existing nominal oval. New reference, longer/cropped
metrics or tire composition requires its own contract. A second, higher-complexity option is
retained GP `fast_sweeper` (41.07079866745727–66.19665359010386 m) with original G/P
identity. It must not be pooled with the oval as an isolated curvature-only comparison.
Oracles: ellipse geometry only as a spline-fit reference, independent arc-length quadrature,
nominal linear force/moment references and existing frozen-speed LQR design checks. These
do not prove nonlinear or time-varying stability; numerical trajectory qualification remains separate.

### 5. Short representative racing sector

Recommend a **view of one original GP traversal covering long_straight → hairpin →
acceleration_zone → medium_corner**, ending at the original `fast_sweeper` boundary
41.07079866745727 m. It combines longitudinal and lateral transitions without a new track.
Use the original native timestamps/progress and full original startup/authority history;
select complete versus rolling-start partial traversals explicitly. No new sector aggregate
or acceptance limit is defined here. Existing exporter sector metrics retain their original
window/quadrature/reference definitions.

Closed-loop G/P data is essential to interpret planner and codriver behavior. A future G
execution uses family 2's exact full-track reference and initialization; a fresh sector start,
cropped reference or distance-based stop is a new initial-condition/termination contract.
The minimal initial software work is a source-bound read-only profile mapping for the
original archive, including packets, controls, events and missing/partial fields. It is not
implemented or automatically admitted by V0.3-C's fixed-grid Workbench replay.

Insight: connect speed intent, turn-in, local trajectory adaptation and actual command timing
across a mixed sector. Use the full G diagnostic set plus exact source/run/traversal identity.
Oracles are the family-2 geometry/dynamics/chronology checks and cross-checks to original
exported values. A cropped successful traversal is not a new independent benchmark, proof
of whole-lap success, or robustness/stability result.

## Coupled validity and numerical qualification

These are existing requirements and future qualification obligations, not newly approved bounds:

- Dynamic propagation checks finite shape, nonnegative progress, forward vx at least 0.5 m/s
  (existing 1e-10 m/s roundoff tolerance), configured controls/speed, positive axle loads above
  1e-9 N, and `D=1-kappa_centerline*e_y>1e-3` at evaluated RK4 stages and final states.
  Braking through the speed floor raises; no clamp, reset, model switch or safe-stop policy exists.
- G/P prediction also has its own stricter configured denominator/load constraints (P: 0.01
  and 1e-6 N). Tire law, allocation, longitudinal command, load transfer, speed, curvature,
  steering/rate and Frenet state must be valid together. For smooth grip,
  `abs(Fx_axle)/(mu*Fz_axle)<=1-1e-6`; demand is rejected without longitudinal clipping.
  The linear law has no physical slip-validity threshold supplied by its equations.
- The GP reference loader separately checks its schema/track hash, SI conventions, dense
  ordered progress and seam, geometry consistency, forward heading, [0.5,6] m/s speed,
  0.08 m margin and reference D>0.1. G uses its original strict feasibility policy;
  Task007B/P advisory demand warnings retain the hard file/domain checks. These offline
  reference checks do not replace plant-stage validity or dynamic trajectory qualification.
- Centerline curvature drives Frenet dynamics; racing curvature drives approximate nominal
  reference yaw/feedforward. The global file's vy_ref=0 and geometric feedforward are not a
  nonlinear tire equilibrium. Optional reference acceleration means Fx/m; absent a_ref is
  zero input-reference target, not a zero body-acceleration constraint.
- Record native state, applied-control and terminal informational rows separately, including
  partials, failed guards, boundary excursions, fallback and missing fields. CG corridor checks
  are sampled observations; no swept-body, continuous-boundary or collision guarantee follows.
- Before any new scientific execution: approve exact source/fixture/configuration, initial
  state, schedule, stop/coverage rule, diagnostic availability, operating window, grid/event
  alignment, convergence criteria and treatment-specific comparison eligibility. Use independent
  canonical-runner parity and analytical component checks; numerical refinement alone cannot
  establish model validity. The existing DOP853 regression shares `model.derivative`, so it
  checks an alternative integrator rather than an independent equation implementation.
- Computational-controller qualification must cover zero/injected/measured latency, physical
  motion during solving, stale application state and skipped fixed releases. G/P keep the
  valid active trajectory and 100 Hz codriver during preparation; synchronous prior-command
  hold semantics are different. Separate planner misses, codriver computation/application
  misses, startup and runtime. Use fresh serialized deterministic single-thread workers with
  actual backend observation; host measured timing is descriptive, not an exact CI limit.
- Global-reference error, local packet-tracking error, model/reference defect and solver
  constraint residual are different quantities. Solver success is not global optimality,
  reference feasibility, guaranteed recovery or stability. Preserve rejected high-demand and
  censored evidence; do not retune, repair references or substitute favorable reruns.
- V0.2 Q covers its five literal linear-tire cases, 0.5 s schedule, three grids and four
  permitted BASE/treatment comparisons only. Its slip/utilization/corridor teaching filters,
  numerical tolerances and 17 retained trajectories do not qualify the oval, GP, new excitation,
  new controller adapter or a three-way experiment. Preserve Q and all 56 frozen source files.

## Inspected source pointers

All local pointers below were read statically at the source base above; historical results are
inherited evidence, not results regenerated by this design.

- Governance: [V0.3-A audit](../apex_workbench_v0_3_a/ENGINEERING_CAPABILITY_AUDIT.md),
  [roadmap](../apex_workbench_v0_3_a/MVP_ROADMAP.md),
  [scientific decisions](../apex_workbench_v0_3_a/DECISIONS_AND_NEXT_TASK.md),
  [analysis limits](../apex_workbench_v0_3_a/CONTROL_ANALYSIS_BACKLOG.md),
  [B Verification](../reviews/apex_workbench_v0_3_b/VERIFICATION.md).
- Geometry/state: [state](../../src/apex/state.py), [constructors](../../src/apex/track/synthetic.py),
  [closed track](../../src/apex/track/closed_track.py),
  [periodic centerline](../../src/apex/track/centerline.py),
  [track specification](../TRACK_MODEL_SPEC.md), [GP loader](../../src/apex/planning_reference/track.py),
  [GP source](../../configs/planning/synthetic_grand_prix_v1/track_source.json),
  [GP manifest](../../configs/planning/synthetic_grand_prix_v1/planning_manifest.json),
  [track asset limitations](../../configs/tracks/README.md).
- L: [Task005 composition](../../scripts/run_lqr_baseline.py),
  [baseline controller](../../src/apex/control/baseline/controller.py),
  [references](../../src/apex/control/baseline/references.py), [LQR specification](../LQR_BASELINE_SPEC.md),
  [dynamic demo](../../scripts/run_dynamic_bicycle_demo.py),
  [VDL schedule/composition](../../tools/apex_workbench/lab_configuration.py),
  [input provider](../../tools/apex_workbench/dynamic_lab.py),
  [Workbench execution allowlist](../../tools/apex_workbench/configuration.py).
- Models/runner: [dynamic specification](../DYNAMIC_BICYCLE_SPEC.md),
  [linear tire](../LINEAR_TIRE_SPEC.md), [grip specification](../GRIP_LIMITED_TIRE_SPEC.md),
  [kinematic specification](../KINEMATIC_BICYCLE_SPEC.md),
  [dynamic guards](../../src/apex/models/vehicle/dynamic_bicycle.py),
  [Frenet guard](../../src/apex/models/frenet.py),
  [runner](../../src/apex/simulation/runner.py),
  [allocation](../../src/apex/models/vehicle/force_allocation.py).
- G/P and prior limits: [Task007A composition](../../scripts/task007a/run.py),
  [reference contract](../TASK007A_RACING_REFERENCE_INTERFACE.md),
  [runtime reference loader](../../src/apex/planning_reference/reference.py),
  [original NMPC contract](../NMPC_BASELINE_SPEC.md),
  [asynchronous specification](../ASYNC_PLANNER_CODRIVER_SPEC.md),
  [Task007B contract](../TASK007B_PROGRESS_SEEKING_RACING.md),
  [Task007B retained rejections](../TASK007B_RESULTS.md),
  [near-limit diagnosis](../TASK007C_NEAR_LIMIT_APEX_DIAGNOSIS.md),
  [physics review](../TASK007C_PHYSICS_REVIEW.md),
  [P manifest](../../configs/performance/apex_performance_synthetic_v1.json),
  [P acceptance overlay explanation](../TASK007E4_PERFORMANCE_ACCEPTANCE.md).
- Oracle/qualification mechanisms: [body identities](../../tests/unit/test_dynamic_bicycle.py),
  [alternative integrator](../../tests/regression/test_dynamic_accuracy.py),
  [geometry tests](../../tests/unit/test_track_geometry.py),
  [geometry regression](../../tests/regression/test_geometry_accuracy.py),
  [grip parity](../../tests/unit/test_grip_tire.py),
  [reference checks](../../tests/unit/test_planning_reference.py),
  [baseline checks](../../tests/unit/test_baseline.py),
  [original finite Q report](../apex_workbench_v0_2_d/QUALIFICATION.md).
