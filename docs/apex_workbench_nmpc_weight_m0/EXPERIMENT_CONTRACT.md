# M5-A / NMPC Weight Lab M0 — bounded experimental contract

Primary's bounded WORK grant binds Workbench base `5831f22f8d64a69efd119edd181802adcd82dde2`
and scientific source `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
Accepted C0 remains `d246f1e9639737e4ecbbd12f8bd0c9b2f1574712`, descriptive-only with G1 OPEN.
Performance profile `configs/performance/apex_performance_synthetic_v1.json` SHA-256 is
`5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.

## Scientific preflight and permitted difference

Read-only inspection of the exact frozen Git objects confirms:

- `cost.py` defines `STATE_WEIGHTS=[4,4,1,100,100]`. Its generic `CostScales.lateral` default
  is 1, while the accepted `task007dcx.worker.frozen_config()` explicitly selects 2.
  `stage_components()` multiplies only heading/lateral coefficients by `lateral`.
- Nominal selects `lateral=2.0`: stage coefficients `[4,4,1,200,200]`. Exploratory selects
  `lateral=1.0`: `[4,4,1,100,100]`. Every other configuration field is identical.
- `problem.py` applies `costs.terminal` independently to `terminal_cost()`. The terminal schedule
  uses unchanged baseline design and alpha_vy/alpha_r, not `lateral`. TVLQR, constraints, plant,
  combined-grip tires, reference, solver options and warm start are unchanged.
- `controller.py` publishes `objective_components` using the native `evaluate_components()`
  only after independently validating optimizer decision/constraint values. These are controller
  post-solve evaluations, not native IPOPT instrumentation. Missing contributions stay unavailable.
- Native `TrajectoryPlanner.prepare()` propagates diagnostics into plan events. Contributions
  and predictions may be attached only to that exact successful, solver-attempted plan event.
  Planner preparation/optimization success is distinct from later packet acceptance/application.

## One scenario, two single attempts

Use frozen `task007dcx.worker.geometry()` and `frozen_config()`, original `TrajectoryPlanner`,
TVLQR/TrajectoryTracker and `AsyncRunner`. Architecture A, original predictor; synthetic GP gamma2;
N8, 0.1 s, four RK4 substeps; original IPOPT options with warm-start initialization enabled.
Use `task007dvis.protocol.availability()` for a controlled A case of duration **2.0 s**: original
35/55/45/25 ms replay pattern and 5 ms codriver delay. Startup is prelaunch and consumes no replay
entry. Initial state is the frozen reference sample at s_abs=1, as in the accepted VIS worker.
Do not equate modeled delays, simulated clocks and measured host durations or assume identical
realized optimizer timings/event chronology between presets.

Only one nominal and one exploratory numerical attempt are authorized, after software gates.
Consume each append-only budget claim before worker launch. Retain failure, timeout, cancellation,
partial results and original stop reasons; never automatically retry. Source/isolation/contract
failure blocks further numerical execution. This grant does not authorize a new campaign.

## Isolation, evidence and presentation

Materialize immutable Git blobs only under ignored `results/apex_workbench_nmpc_weights/`.
Check runtime bytes, actual imported module paths/hashes, locked profile/environment identities
and complete resolved configuration before constructing/executing the controller. Reject any
Workbench/R0 controller import. Retain original source files unchanged; no independent equations.
Reuse the owned worker, inherited lease, cancellation/resource safeguards and atomic evidence
publication. All new operational/evidence outputs for this task stay under that ignored root.

Retain complete native raw result plus available optimization predictions, plan events, commands,
plant segments, timing, slack/feasibility diagnostics and partial journals. Never fill missing
actions, acceptance, states or feasibility margins. Any supplemental journal is explicitly tagged
with its native source/callback and coverage; it is not a reconstructed native runner result.

All views/comparisons are **EXPERIMENTAL / UNQUALIFIED — synthetic**. Use native clocks, explicit
missingness and coverage; requested and applied commands remain distinct. Descriptive physical
metrics must define their samples and units. Differently weighted objective totals are not a
common performance measure. No numerical/physical/controller-performance qualification follows.

Only focused software checks, the two bounded experiments and independent Engineering Review are
authorized. No full formal Verification, active Pre-SID R0 change, M5-B, SID, Safety or hardware.
Successful stop: `NMPC_WEIGHT_LAB_M0_ENGINEERING_REVIEW_COMPLETE_PENDING_VERIFICATION`.
Blocking stop: `NMPC_WEIGHT_LAB_M0_BLOCKED_PENDING_PRIMARY_DECISION`.
