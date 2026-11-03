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

## Primary R1/R2 corrective continuation — 2 November 2026

Primary's new decision (SHA-256
`8c5147b33c8da3270558ee43a140a10dd69397bdd9258fb091db24bfb03eb1f8`) authorizes localized
R1/R2 correction and a conditional replacement budget. The original failed nominal claim,
`BLOCKED.json`, gate, logs and independent BLOCKED review remain immutable. Nothing in this
amendment changes the frozen scientific source, scenario, duration, values or resource limits.

R1 uses a single finite JSON-compatible snapshot representation at capture and execution.
Tuple/list sequence representation is normalized; scientific dataclass objects remain intact.
Strict serialized equality still distinguishes numbers from booleans/strings, integer/float
representations and signed zero, and rejects nonfinite/unsupported/malformed values or genuine
non-treatment changes. A fresh no-solve subprocess exercises the actual execution-boundary helper.

R2 authenticates the selected catalog record, canonical immediate M0 run directory, original
claim, adapter, preset, origin and absence of alias conflicts before refresh/reconciliation or
cancellation. Foreign/archive/symlink/forged/conflicting records are quarantined with pure reads.
The UI passes the full selected record. Existing P/C0 viewers remain unchanged. The sole
`jobs.py` correction allocates M0 IDs from the independently pinned gate's two reservations;
other adapters keep their original ID allocation and all lifecycle/resource mechanics.

New admission uses an append-only successor namespace,
`authorizations/primary-r1-r2-20261102/`, under the same ignored output root. It requires the
exact Primary decision, unchanged original failure anchors, an independent corrective-review
**PASS** bound to the exact producer hashes/Git commit, and a fresh source/environment/software
gate. Missing/stale review or authority blocks admission. Original evidence readers retain their
original gate/claim namespace. Each successor preset still has an exclusive single claim; a new
failure writes a successor BLOCKED marker without changing the original.

The gate is prepared before corrective review, without an authority-hash back-reference. The
independent report pins its exact SHA-256, including scientific snapshots, environment, producer
identities, test evidence and two reserved run IDs. The successor authorization then binds that
review. Both admission and retained inspection verify this external pin; a request cannot supply
its own authority by rebinding a changed gate hash. Claims must exactly match their preset's
reserved identity and authority. This acyclic chain also rejects copied successor aliases.

Only after that PASS may one NEW nominal 2.0 s attempt run. The sole exploratory attempt may
follow only if the nominal has a completed, intact, comparable result under the unchanged
contract. Any genuine scientific/solver/runtime/integrity failure stops the continuation with
all evidence preserved. No retry, search, extra scenario or formal Verification is authorized.
After execution, obtain a separate independent assessment of the exact implementation/evidence
and stop at the existing successful or blocked status above.
