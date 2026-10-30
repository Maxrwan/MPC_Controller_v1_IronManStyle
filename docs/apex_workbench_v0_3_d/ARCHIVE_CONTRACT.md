# V0.3-D archive profile P/VIS-1R — preimplementation contract

Scope: one existing `apex-run/0.1.0` producer/case, read-only inspection. Primary C acceptance is
`7da7100fe624481e6066390d503abea5b4292b4d`, accepting exact source `34f98a4`/delivery `6d3a368`.
No controller, exporter, scientific model, lifecycle, qualification reader or accepted data changes.
Independent review of this contract is required before adapter implementation.

## Identity and trust

Only `results/task007d/vis/vis1r_c699057/controlled_A` is offered. Its scientific worker/exporter is
`8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae`, frozen ancestor `c699057`; current runtime bytes are
never substituted for historical sources. Profile P is accepted by E4 Recommendation B at
`48adbdf`, verified profile `e603672`, E3 delivery `ecbbc5c`. This is historical synthetic acceptance,
not V0.2 laboratory qualification or new execution authority. The manifest's original
`candidate_pending_representative_Workbench_ingestion` flag remains visible and unchanged.

Trust chain (SHA256, not mutable path or self-seal alone):

| Record | SHA256 |
|---|---|
| `configs/performance/apex_performance_synthetic_v1.json` | `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf` |
| `docs/task007e/e2/evidence_links.json` | `5e788c428bd706f20792b1852b3400bf0eeb7fe11d93285bbc5bc7accec8fced` |
| `docs/task007d/vis/vis1l/verification.json` | `8055a017dbbbf19b0d0143311a8299d97c0c860583f233685270a4980a9d9a67` |
| Original scientific manifest | `5375580236b5e4b9305babe5d25e6459f91f80e31bb3fdb937e3e4c054d85a10` |

The pinned VIS inventory binds **all 25 original files** including raw evidence, input configuration,
summary, scientific artifacts and fixture. Each presentation operation verifies this inventory,
manifest self-seal, all 15 manifest artifact entries and schema/source/case identity. It consumes
only verified bytes held within that operation. Rehash all inventory files before publishing plots
or downloadable derived views; on replacement/missingness/unsafe paths withhold the entire view.
No persistent cache or metadata-only validity shortcut. Tests use disposable copies with the same
original execution identity; copies are never discovered as new scientific executions. No recursive
archive importer. Missing archive or unsupported producer is explicitly unavailable/quarantined.

Before delivery audit all 294 recorded source hashes against historical Git blobs and preserve the
original archive inventory. Runtime inspection checks the pinned record, never requires the current
implementation to equal historical P. Git evidence is source identity, not proof of physical validity.

## Signals, clocks, units and missingness

- State order `[vx, vy, r, e_psi, s_abs, e_y]`, units `[m/s, m/s, rad/s, rad, m, m]`.
  Inputs `[delta, a_cmd]` in rad and m/s². Dynamic `a_cmd=Fx/m`, not body `dvx/dt`.
- States use native simulated physical `time` seconds. Controls expose **both computation `time`
  and actual `application_time`**, first 0/0.005 s. Applied controls plot against application time;
  requested controls, errors/references and computation costs retain computation time. Never join
  asynchronous streams by row index, infer a hold or interpolate a sample.
- Cycles retain `t_release`, `t_ready`, `t_accept`, first TVLQR use and measured solver duration.
  Cycle `status` is packet availability; actual solver status stays in recorded event payloads.
  Host durations are seconds and separate from simulated timestamps. Missing `valid_from` for A
  remains missing; do not replace it by release/accept time. No new staleness rule or threshold.
- Events are read verbatim from `events.csv`, including time/phase/source stream/source row/plan ID,
  payload, provenance, missing reasons and unspecified same-time ties. Preserve export row order;
  do not sort ties into a claimed causal total order or call the producer's event reconstruction.
- Read only actual CSV columns. Empty optional fields remain absent/NaN; no zero fill. Unknown
  units are explicitly undeclared, never guessed. Core state/control units come from the manifest;
  references/errors inherit the named physical channel; utilization is dimensionless.
- Physical states/endpoints are native. Stored world XY, reference sampling and authority intervals
  are **producer reconstructions**, not independently measured/native geometry. Offline planning
  CSV is recorded reference geometry. Show these distinctions. Do not reconstruct XY, boundaries,
  events, solver statuses, metrics or missing requests. Raw provenance/missingness remains inspectable.

## Views and interpretation

Use existing Home/Inspect navigation and catalog with a distinct read-only archive profile; do not
coerce it into the V0.2 record reader, qualification or comparison contracts. No GP Run button,
cancellation, reconciliation, note writes, replay engine or cross-profile comparison. A source-linked
HTML report may serialize the current verified native view and original provenance; it is a derived
inspection document, never a new execution/evidence package or scientific score.

Full run and named sectors use the original fixture's sector starts and track length
154.76345492731022 m. A sector is a half-open interval `[start,next_start)` in native `s_abs modulo L`;
the last ends at L. Retain original `s_abs`, timestamp, export row and whole-run identity. Select
states only by their own recorded progress. Controls/events/cycles have no native progress channel:
keep them full-run and label this explicitly, rather than inventing sector membership from nearest
states. Planning reference filtering uses its own recorded `s_track_m`. Never interpolate crossings
or treat a sector as an independently closed track. Display original coverage: two crossings,
one initial partial plus one complete lap; no new lap/sector score. Original interpolated crossing
metadata is historical producer output and is not rederived or promoted to native sample timing.
Use markers in sector views so separate visits are never connected across omitted track/time.

P uses Architecture A, N8/0.1 s/four RK4 substeps, gamma2, progress0, TVLQR; imposed planner delays
35/55/45/25 ms and 5 ms codriver delay are this archive's evaluation conditions, not production
defaults. Synthetic/unmeasured vehicle; no physical validation, hard real-time, continuous swept-body
Safety, guaranteed recovery or standstill braking. C70 incomplete export remains unsupported;
G (Task007A, gamma1/N4) remains a separate historical profile, not silently migrated into P.

## Acceptance checks

Use actual retained bytes plus disposable negative fixtures: changed manifest/source/schedule,
missing/truncated artifacts, replacement during rendering, unsafe paths, native control clocks,
event/payload exactness, sector half-open membership, original identity and read-only operations.
Verify focused prior presentation regressions and production V0.2 qualification consumption without
rerunning trajectories. All56 scientific files, original qualification/archive bytes and launcher
remain unchanged. Final exact implementation requires separate independent Engineering Review;
full formal Verification and new scientific execution remain deferred.
