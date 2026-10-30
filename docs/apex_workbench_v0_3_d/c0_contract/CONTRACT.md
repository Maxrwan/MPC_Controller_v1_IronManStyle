# C0 original155 — blocked archive-inspection contract draft

**Draft version:** `c0-original155-inspection/1` (a new descriptive contract, not a historical
producer schema). **ADMISSION BLOCKED — capture source binding is not established.**
Audit base `f80a105d9ab3c1fcf5e28e97a0876fcb422c1c60`; 30 October 2026.
[Gap report](AUDIT.md), [source/evidence/type inventory](evidence_inventory.json).
No Workbench profile is enabled, no adapter is implemented and no independent review is claimed.

## Identity and trust boundary

Only `results/task007d/c/amended/c0_export/original155.json`, exactly **152,600 bytes**, SHA256
`2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5`, is a candidate.
Its known bytes match the prior MVP scenario anchor and its summary matches the committed amended
C0 summary. Neither match authenticates the exact capture-time code/environment.

The immutable **reference**, not a proven capture revision, is amended-C delivery
`44e0471680bb22ea1ee790173d1f2481a905f386`, tree
`f4af6a2825970bb643ad4b570b850f17d4c79fb3`.
Its export entrypoint calls `test_fixed_handoff_scheduler.simulate` with the injected
`StraightPlanner`, synthetic vehicle fixture and analytical `straight_geometry` fixture; it writes
raw results directly through `task007d.worker.write`. The serializer converts NumPy arrays/scalars,
uses `json.dump(indent=2, allow_nan=False)`, exclusive creation and a final newline. It adds **no
schema/source/configuration/environment envelope**. The 69-file reference inventory is a conservative
static local-import superset plus vehicle YAML, not a certified capture/runtime closure.

Reference-source meanings below are consistent with the recorded data and published protocol;
they must not be represented as authenticated capture provenance. Current runtime bytes, neighboring
pilot hashes, a later test pass or output similarity cannot substitute for the missing binding.
A contemporary inventory must remain labeled as such, never backdated as an original manifest.

## Exact payload shape and capability/missingness contract

The raw root is an object with exactly 18 observed keys. JSON has no duplicate members or nonfinite
numbers. The machine inventory lists every observed collection field, type, absence and null count.

| Collection / scalar | Actual retained coverage | Permitted interpretation after the binding gate |
|---|---|---|
| `states` | 120 rows, time 0 through 0.595 s, six canonical state values plus applied state-row control, plan ID, mode, utilization and sampled boundary flag |Synthetic plant-state observations at native times; no terminal 0.600 s state. |
| `controls` | 60 applied-request rows, time 0 through 0.590 s; computation/application time and physical latency present |Keep request, application, source plan and mode separate. All recorded latencies are 0 and the two clocks coincide in this fixture; this is not a universal clock rule. |
| `reserves` | 120 rows, time 0 through 0.595 s |Recorded packet reserve/category/plan ID; negative/exhausted reserve can coexist with fallback. Never clamp, extend authority or infer physical recovery margin. |
| `plans` |Startup 0 plus runtime 1/2; all status `test_success` |Injected test-planner metadata, never an IPOPT result. Startup intentionally lacks runtime-only completion/fixed-delay fields; runtime plans contain readiness-state/error fields. Missing startup fields stay not applicable. |
| `packets` |Three packets; each 5 timestamps, 5×6 nominal states, 4×2 controls, 4×4 gains |Test-generated nominal/prediction data, distinct from plant states. Startup omits `valid_from`; runtime packets include it. Empty curvatures are unavailable preview, not recorded zero curvature. |
| `fixed_handoffs` |Two rows, both `missed` |Each row's release, target, readiness and late-discard timestamps retain separate meaning. `t_accept`, `first_TVLQR_use`, `packet_age`, `reserve_at_acceptance` are null in both. |
| `urgent_demands` |One row, status `fallback` |Recorded trigger/idle/release/busy/grid/fixed-offset fields. Accepted plan/time and trigger-to-authority are null, not0 or a delayed acceptance. |
| `triggers`, `releases`, `misses`, `fallbacks` | 2, 2, 3, 1 rows respectively |Native per-collection records; planner-busy skips differ from fixed misses. `busy` is absent for the disturbance trigger, not false. |
| `handoffs`, `lap_times`, `codriver_misses` |Empty lists |No recorded runtime handoff/lap/codriver-miss rows. Empty handoffs do not erase the startup buffer insertion described by reference source. |
| `failure`, `stop_reason`, `end_time`, `pending_at_end` |null, `duration`, 0.600, false |Recorded execution disposition, not current Workbench worker status, valid provenance, controller availability success or numerical qualification. |

No native world XY, serialized track/reference geometry, capture environment, source manifest,
run UUID or actual optimizer telemetry is present. Mark unavailable; do not build a track, invoke
Frenet conversion, reconstruct telemetry or borrow P/VDL identities to populate a panel.

## Units, frames and diagnostic roles

The reference producer uses canonical `[vx,vy,r,e_psi,s_abs,e_y]`, SI units
`[m/s,m/s,rad/s,rad,m,m]`, body velocities/yaw rate, unwrapped centerline progress,
left-positive Frenet error and CCW angles. Inputs `[delta,a_cmd]` are rad and m/s²;
Dynamic `a_cmd=Fx/m` is not body `dvx/dt`. These declarations come from the reference source/spec,
not embedded unit tags in the raw file. Nominal packet states follow that same order.

`front_utilization`/`rear_utilization` map in the reference runner to **combined** utilization,
dimensionless, under explicit synthetic smooth-combined-grip/normal-load-proportional allocation
and canonical quasi-static longitudinal loads. The sampled boundary flag is a center-corridor
check on an analytical test chart, not swept-body or real-vehicle safety. No tire/slip/force/load
channels absent from this export may be recreated by calling model diagnostics.

Control `reference_*`/`error_*` are producer diagnostics at computation, including producer packet
sampling; they are not new observations at a viewer cursor. In `baseline_fallback`, reference source
sets `reference=x`, `error=0`, `correction=0` and `nominal=proposed`. The recorded zero errors must
not be presented as perfect baseline path tracking or an independent reference target. Buffer
`plan_id=0` remains recorded even in fallback; mode determines command provenance, not that ID alone.

`planner_total_time`/`planner_cpu_time` 0.017 s and packet solve/total duration 0.010/0.017 s are
**injected fixture constants**, not measured optimizer timings. Control CPU/wall/interpolation/
feedback/validation/kernel durations are host diagnostics in seconds in the reference source.
They remain distinct from imposed planner availability 0.155 s and codriver physical latency 0.
Manual fixture gains are not a newly computed TVLQR design or evidence for CT/stability claims.

## Native chronology and coverage

Preserve these literal values, including floating representation; no snapping, replacement times,
interpolation, inferred holds, additional endpoint rows or cross-stream causal total ordering:

- Fixed plan 1: release 0.100, target/miss 0.170, ready/discard 0.255 s.
- Fixed plan 2: release 0.260, target/miss 0.330, ready/discard 0.41500000000000004 s.
- Urgent trigger 0.160, idle 0.255, release 0.260 s; recorded busy wait 0.095 and grid wait
  0.0050000000000000044 s. These are different causes; trigger-to-authority is null.
- Planner-busy skips 0.200/0.300/0.400 s are separate records from the two fixed misses.
- Fallback 0.400 s, `trajectory_exhausted`, recorded `valid_domain=true`; simulation continues
  in `baseline_fallback`. This proves neither optimizer failure nor guaranteed recovery/safety.
- End clock 0.600 s is later than the last state/reserve 0.595 and control 0.590 s. The reference
  loop records before propagation and stops at duration; do not apply the VDL N+1 convention.

Use `(artifact SHA256, JSON collection, original array index[, timestamp field])` for display
identity. A marker may project an existing recorded timestamp field with its JSON pointer; it must
not become a new native event or an assumed same-time phase rank. Keep collection order and tied
records explicit. Reference loop phase descriptions explain the implementation, but this format
records no portable cross-stream tie ordinal. Copies remain the same fixture, not new executions.

## Proposed fail-closed admission/render/export rules

These requirements are design only; the source-provenance gate currently rejects admission.
Before any future implementation: independent contract review and explicit WORK assignment.

- Pin this exact artifact plus external approved contract/authority/source inventories. Required
  capture binding must be genuine existing evidence, not a generated claim. Missing binding cannot
  be downgraded silently to a qualified or source-verified plot.
- Allow only the declared local source; reject escaping/linked paths and arbitrary import roots.
  Read exactly the pinned size/hash before parsing; changed/missing/truncated/resealed files fail.
  The 152,600-byte limit and fixed member/row shapes bound I/O; these are format, not scientific limits.
- Strict JSON duplicate/finite/type validation: numeric fields accept finite int/float excluding
  bool, IDs/indices strict integers, flags strict bool, text strict string and declared null/absence
  preserved. Startup/runtime shapes are conditional as inventoried, not a generic fill rule.
- Use operation-local verified bytes only. Recheck artifact and authority epochs before publishing
  and after serialization; withhold/clear stale plots/labels/exports. No metadata-only cache shortcut.
- No source import/construction, controller/worker/reconciliation/cancellation/Safety path, geometry
  regeneration, new metric, causal comparison or qualification. Reuse existing presentation/export
  infrastructure only where its semantics fit; neither P `apex-run/0.1.0` nor VDL contracts fit C0.

**Current disposition: `C0_ARCHIVE_CONTRACT_BLOCKED_PENDING_DECISION`.** No parser or adapter is
implemented, and this draft does not license an unverified scientific view.
