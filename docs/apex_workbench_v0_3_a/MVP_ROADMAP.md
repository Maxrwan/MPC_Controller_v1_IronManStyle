# Prioritized roadmap

Current progress (30 October 2026): M1/V0.3-B's separate acceptance is not inferred. V0.3-C is
accepted within scope by Primary record `7da7100`. V0.3-D at exact implementation
`c5f3db6852af8f8ffccf4e5e9e6f11d01fa861b4` is now [formally accepted by the user](../reviews/apex_workbench_v0_3_d/PRIMARY_ACCEPTANCE.md)
after one Verification with 1,089 passes / 17 gated G2 skips. M4's single P archive inspection,
source-linked HTML and oval shortcut are accepted only within that verified scope, retaining the
download and terminal observations. The [next C0 task](../apex_workbench_v0_3_d/NEXT_C0_TASK.md)
has completed its initial Section A audit with a [source-binding blocker](../apex_workbench_v0_3_d/c0_contract/AUDIT.md):
known artifact bytes/reference sources do not establish the exact capture producer. Contract review
and explicit adapter WORK remain ahead; M4 controller-failure inspection is incomplete.
RBT-S/N/V, S1/S2/S3, future G/P execution,
new scientific experiments, generic telemetry, CT and hardware remain separately gated.
The original ordering/gates below remain historical design context.

Goal: everyday engineering use of accepted simulations and retained evidence. Do not preserve an
older V0.3 lettering plan or build separate new laboratories. Complexity is qualitative: **Small**
reuses existing values/views; **Medium** adds a bounded presentation/data contract; **Large** adds
execution/scientific or cross-department dependencies. These are not time estimates.

## Phase I — Engineering MVP

| Order | Delivery / engineering value | Dependencies and boundary | Complexity / exit |
|---|---|---|---|
| M1, recommended next | **Engineering workspace and run inspection:** home/catalog, supported experiments, failures/status/evidence, Run/Inspect/Compare; current three adapters; two-run comparison as primary; existing metrics, gains and diagnostics; optional engineering notes | Accepted W/Q; additive presentation over the unchanged 56-file engine, source-aware read-only Q discovery, existing worker/qualification/launcher protections. No new controller, scientific metric or generic import | **Medium**; scenario 1, two-run portion of 2 and existing export/reopen subset of 5. Exact next task in [decision document](DECISIONS_AND_NEXT_TASK.md) |
| M2 | **Comparison and common-time inspection:** small multi-selection, pairwise compatibility matrix, linked native-time cursor and available-channel/reference selection. Source-bound existing LQR analysis when appropriate | M1; raw timebases and identity preserved; use existing summary definitions. Show existing node gains/poles as design-model results only after their export/source binding is established | **Medium**; scenario 2 including the three-run mixed-eligibility case; no new math/rank threshold |
| M3 | **Recorded-data replay:** versioned software bundle opening/import, play/pause/seek, synchronized native signals/stored XY and genuine events, missing-data states | M1/M2; first profile is current Workbench evidence. Preserve original artifacts/source/qualification. Viewer time does not drive a plant. No generic physical telemetry or hardware command schema | **Medium**; scenario 4 and synchronized portion of 5 |
| M4 | **Failure investigation and practical exports:** one explicit C0/async software-archive profile, solver/reference/control/event inspection where present, source-linked figure/HTML/evidence export | M1–M3; known producer/schema/unit/time mapping, original failure/censoring preserved. Older incomplete archives remain descriptive/unverifiable as appropriate. No live NMPC adapter | **Medium to Large**, depending on archive provenance; scenarios 3 and 5 complete |

This MVP launches the three genuinely supported experiments and makes historical controller work
inspectable. NMPC/TVLQR are explicitly labeled **recorded inspection only / execution unavailable**
until a reviewed adapter exists. That is preferable to promising a generic controller selector.
M2–M4 may share a small inspection context and viewer state; no plugin system, database framework,
simulation engine or broad frontend migration is required. Split only when a stage is independently useful.

Early analytical value is part of Phase I: existing tracking summaries/reference identities,
commands/saturation/gains, accepted numerical/slip/utilization diagnostics, and archived solver/timing
fields. Defer recomputation when data already exists. Do not make advanced CT a prerequisite for
being able to reopen a failed run, compare traces or export a usable engineering demonstration.

## Phase II — professional expansion

| Priority / retained goal | Prerequisite / scientific gate | Complexity |
|---|---|---|
| Approved canonical NMPC/async execution adapters | Exact execution profile, scientific source identity, latency/plant chronology, resource/ownership and artifact contracts. Dynamic-lab Q does not qualify a controller adapter. Fixed modes remain opt-in; no fallback/speed/profile tuning | **Large** |
| Control Performance & Systems Analysis within the same inspector | C review, aggregate timer resolution and separately authorized qualification/execution; explicit map/scaling/original-gain authority. Add source-bound controllability, PBH, transient products/defects and declared robustness results | **Large** |
| Defined observability/estimation studies | Actual measurement model and producer/clock/frame/uncertainty contract; no physical C=I or inherited estimator assumptions | **Large** |
| Deeper solver/efficiency profiling | F observer allowance/reconciliation and execution gates; separate solver, preparation, application and hardware clocks. No net-cost correction/speedup assertion before acceptance | **Large** |
| Richer comparisons, figures and concise reports | Versioned metric semantics, tested exports and existing evidence IDs; introduce only formats that help engineering decisions | **Small to Medium** |
| Raspberry Pi / physical-test **read-only monitoring** and archive ingestion | Control/Perception/Embedded producer contract, frames/units/clocks, validity/missingness and record provenance. No actuator/arming/Safety authority path in this roadmap | **Large**, cross-department |
| Broader disturbance/robustness or new physical models | Individually approved operating points, excitations, uncertainty sets and numerical/physical qualification; existing rejected evidence retained | **Large**, separately scientific |

Each implementation stage ends at WORK review, then independent Engineering Review and applicable
exact-revision Verification before acceptance. Reuse unchanged applicable evidence with its identity;
do not repeat the 17-trajectory campaign or frozen research merely because presentation changes.
If a required scientific dependency changes, the old qualification cannot silently transfer.

The five [acceptance scenarios](ACCEPTANCE_SCENARIOS.md) define the MVP completion criterion. No
implementation, replay run, model test, scientific campaign or hardware work was performed here.
