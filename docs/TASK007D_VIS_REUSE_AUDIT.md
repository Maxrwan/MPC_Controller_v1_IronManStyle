# Task007D-VIS implementation and evidence reuse audit

VIS-0 WORK audit at `f072052cd4481df6d987deb6d8d721f1b1b99cb2` on main; scientific
source `935e98b7af6c2fda8458551f1fbcbddb3bf8932d`. Documentation only. No module below was
modified, imported to run a simulation, or benchmarked during this audit. See the
[proposed protocol/budget](TASK007D_VIS_PROTOCOL.md) and
[Workbench contract proposal](TASK007D_VIS_WORKBENCH_CONTRACT_PROPOSAL.md).

## Reuse map

Paths below are repository-relative. “Adapt” means a future research-only adapter, not permission
to change a historical script or the controller. Functions were inspected in the current tree.

| Capability | Existing implementation | Reuse decision and limit |
|---|---|---|
| Lap termination/counting | `src/apex/simulation/asynchronous.py::AsyncConfig`, `AsyncRunner.run`; `scripts/task007c_resume/run.py::run` | Reuse runtime unchanged. `laps` counts seam crossings; s_abs=1 m starts a partial lap. Two crossings yield one following complete lap. `lap_times` uses interpolated crossing time, not a seam event sample. |
| Event-driven plant history | `AsyncRunner.run`; `scripts/task007dcx/worker.py::RecordedPlant.step`; `tests/unit/test_cx_closure.py::test_recorded_plant_observer_has_exact_rk4_parity` | Reuse the call-through segment observer; save actual step endpoints, dt and held control. Do not reschedule readiness, inject seam events or change RK4. Final step endpoint is available in segments even when absent from raw state rows. |
| A/C70 scheduling | `src/apex/simulation/fixed_handoff.py::FixedHandoffs`; `src/apex/control/trajectory/packet.py::TrajectoryPacket`, `TrajectoryBuffer`; `scripts/task007dcx/worker.py::frozen_config`, `availability` | Reuse runtime/config construction; A offset None versus C70 .070, predictor A in both. Adapt only fixture/duration/lap selection in new worker. Keep old-command application before handoff and approved urgent grid behavior. |
| Fresh measured workers | `scripts/run_task007dcx.py::main`; `scripts/threading_study/config.py::environment`, `configure_accelerate`; `scripts/task007c_resume/run.py::dispatch` | Reuse fresh SINGLE bootstrap, process evidence, exclusive guard and disk-floor pattern. CX launcher restricts case names/output root; old resume launcher has old defaults and looser folder reuse. New VIS launcher must be strict/fresh, not repoint an old campaign. |
| Controlled replay/timing | `src/apex/simulation/diagnostic_timing.py::DiagnosticTiming`, `ReplayExhausted`; `scripts/task007c_resume/run.py::run` | Fixed one-value histories and finite launch-indexed replay are supported. Startup excluded from runtime planner history. Exhaustion is explicit; never pad a measured trace. VIS synthetic pattern is declared before runs. |
| Physical/Planning/APEX telemetry | `scripts/task007b/analysis.py::analyze_case`, `sectors`; `scripts/task007b/metrics.py::planning_deviation`, `local_tracking_error`; runtime states/controls/plans/packets | Reuse mathematical channel definitions and sector lookup. Adapt raw readers: old analysis expects predictions.json, interpolates channels and hardcodes .55 m clearance. Use actual track widths and native validity samples; keep world heading, Frenet heading and target-error clocks separate. |
| Validity/stop gates | `scripts/task007d/metrics.py::chronology`, `physical_metrics`, `stop_reasons`; `scripts/task007dcx/worker.py::run`; `scripts/task007dc/analysis.py::extra` | Reuse checks and slack gate 1e-6 m. `stop_reasons` expects `duration`, so a separate tested lap-aware adapter must accept proved `target_laps` completion and mark capped runs incomplete. Extend validity audit to the terminal recorded step endpoint without changing physics. |
| Lap/sector/common-coverage metrics | `scripts/task007c/metrics.py::traversal_metrics`, `steering_activity`, `prediction_metrics`; `scripts/task007c/metrics_export.py::export_case`; `scripts/task007c_resume/common_coverage.py::compare` | Reuse wrapped differences, native interval weighting, traversal boundaries and no-tail logic. Do not reuse its `complete_laps=len(lap_times)` label: it counts the initial partial traversal. New window labels must correct this in new exports only. |
| Timing/reserve/misses | `scripts/task007dc/analysis.py::cycles`, `compare`; `scripts/task007dcx/analysis.py::cycle_rows`, `timing_summary`, `miss_consequences`, `quality` | Reuse missing/censored/completed/accepted distinctions and descriptive distributions. `quality` has a short-run end default (1.99 s); its fixed sampling/window assumptions need an explicit full-lap adapter. Do not extrapolate recovery after a stopped run. |
| Prediction/physics diagnostics | `scripts/task007c_resume/physics.py::variable_step`, `prediction_errors`, `export`; `scripts/task007d/diagnostics.py`; CX worker offline A forecast audit | Reuse only where applicable: symbolic frozen-curvature step is a diagnostic, not a second plant. Realized packet-horizon residuals include later replanning/feedback and interpolated states. Readiness mismatch is not aligned target-state error. Retain causal A forecast→NMPC check offline. |
| Static plotting | `scripts/task007b/plots.py::dashboard`, `comparison`; `scripts/task007c_resume/dashboard.py::dashboard`; `scripts/task007c_resume/physics_plots.py::plots`, `phase_portraits`; `scripts/task007dcx/figures.py::build` | Reuse plotting conventions and numerical inputs. Existing dashboards target old folder schemas/sectors or short three-architecture CX cases. New A/C70 lap panels should read new exports, preserve raw data and label native/derived quantities. |
| Animation/replay | `scripts/task007b/replay.py::main`; retained replay/diagnostic modules | This “replay” drives deterministic timing experiments, not a video renderer. No Matplotlib animation/FFmpeg/PillowWriter or .mp4/.gif output path was found under scripts/src. Optional later video needs a small offline renderer and dependency review; no promise of an existing animation pipeline. |
| Closed track construction | `src/apex/track/centerline.py::PeriodicCenterline`; `src/apex/track/closed_track.py::ClosedTrack.from_waypoints`; `src/apex/track/synthetic.py::circle_waypoints`; `src/apex/planning_reference/track.py::load_track` | General ordered waypoint/spline/width loading works. Circle helper is not a mixed-corner circuit designer. No automatic holdout generator is claimed; introduce one deterministic data fixture later. |
| Offline Planning generation | `scripts/task007a/generate.py::generate`; `scripts/task007b/references.py::generate`, `package_name` | Reuse reference geometry/speed-envelope and gamma/cap algorithms. A generator hardcodes GP corner indices 6,11,17,31,36,42; B generator hardcodes base/output paths. A fixture-specific anchor/path adapter is required; changing controller/reference semantics is excluded. |
| Reference validation | `src/apex/planning_reference/reference.py::PlanningReference`, `intersection_count`; `src/apex/planning_reference/speed_polynomial.py::load_speed_polynomial` | Reuse schema/hash/seam/domain/geometry validation and serialized cap polynomial. Existing sampled intersection checks are not a continuous proof and omit some touching/parallel cases; validate the new fixture's corridor as well as its centerline/reference. |
| Exports/provenance | `scripts/task007c_resume/run.py::run`; `scripts/task007dc/export.py::export`, `csv_rows`; `scripts/task007dcx/report.py::build`; `scripts/task007dcx/worker.py::hashes` | Retain raw.json + segments.json + release_contexts.json + summary.json as raw evidence, export separate flat CSV views and packet JSON. Old writers select fields and may omit fixed cycles/urgent demands. `scripts/async_study/export.py::export` is an old architecture-design export, not current vehicle telemetry. |

## CLI audit and integration boundary

`scripts/run_task007c_resume.py` exposes `--case`, `--fixture`, `--output`, `--gamma`,
`--progress-weight`, `--horizon`, `--alpha-vy`, `--alpha-r`, `--laps`, `--duration`,
`--mode {zero,injected,measured}`, `--timing {normal,fixed,replay}`, `--trace`, `--plan-delay`,
`--driver-delay`, `--injected-delay`, `--perturb-index`, `--perturb-ms`, `--capture/--no-capture`
and internal `--worker`. Its defaults include N4, gamma2.5, lambda1, laps1 and duration100;
these are **not** the VIS configuration. It has no fixed-handoff offset option. It also loads
`results/mpc_parameter_study/selected_candidates.json`; do not accidentally make the new frozen
constructor depend on an untracked historical file when CX already has explicit construction.

`scripts/run_task007dcx.py` exposes `--case`, `--output` and internal `--worker`; protocol cases
come from `docs/task007d/cx/protocol.json`. It accepts output only under results/task007d/cx.
Its worker fixes the GP fixture and uses protocol duration=2 s. `scripts/run_task007dc.py` likewise
serves the historical C protocol. Neither is a generic `--laps`/`--fixture` VIS command.
No command shown here authorizes a run. A proposed VIS CLI is not yet implemented.

Smallest new research code for a later assignment:

1. A thin VIS launcher/worker assembly with explicit immutable cases/fixture path/duration/two-crossing
   setting. Reuse `frozen_config`, `RecordedPlant`, timing API and runtime. Save full effective
   configuration and preserve instrumentation across A/C70. Keep core, old scripts and fixtures intact.
2. A tested lap/sector/window and lap-aware gate adapter. Preserve final-step coverage, partial/censored
   status, clearance extrema, misses and authoritative event identities; no new plant model or scheduler.
3. An offline schema adapter for raw channels, Planning, packet nodes and metrics. Use packet/gain
   outputs already available; full NLP snapshots need not be captured on every long-run cycle. Preserve
   all packet states/controls/statuses, slack, solver inputs needed for the causal initialization audit.
4. Later VIS-2 only: fixture-specific corner/sector anchors and a deterministic reference generator
   wrapper, plus corridor/intersection validation. Stop for review if existing geometry/speed methods
   cannot satisfy the accepted contract without a semantic change.
5. Later VIS-3 only: progress/time plotting and optional replay against reviewed exports. No UI or
   general experiment framework. Workbench acceptance remains with its separate supervising chat.

One telemetry limitation needs explicit handling: `AsyncRunner` appends a control row only on
physical application. A request still pending at termination need not appear in `controls`; release
snapshots expose pending requests only at planner releases. The proposal therefore marks request
coverage and missing tail data. It must not invent a final request or falsely claim exhaustive
computation-time samples. If Workbench requires every such request, review a non-mutating observer
approach and its timing/parity impact separately before implementation; no core change is authorized
by this audit. Normal applied rows already retain requested and applied values/timestamps.

No demonstrated core incompatibility blocks the proposed study. The lap, gate, export and fixture
gaps are visible research-tool limitations; they have not been “fixed” in VIS-0. A later implementation
that cannot address them within the unchanged-runtime boundary must stop for Engineering Review.

## Historical evidence applicability

| Evidence | Defensible reuse | Exclusions / required checks |
|---|---|---|
| CX verification at f072052; scientific 935e98b | Existing 709 passes, source/fixture preservation, exact C1 retained-packet replay, byte-identical 51 tables/10 figures; provenance in linked formal report | Inherited, not freshly run VIS tests. New observer/export/window code needs its own prerequisite tests. |
| C C1 and CX Study 1 | Jitter mechanism/partition findings and plotting context; retain their existing applicability audit | Short 2 s results cannot substitute for complete laps. Two accepted urgent-bookkeeping source differences were inactive in retained C1; do not generalize this to other histories without checking. |
| C C3 gamma2 A/C70 | Same constructor, fixture, 5 ms codriver and predeclared 35/55/45/25 ms pattern; useful short parity comparator | Audit original source/urgent-event applicability before exact parity claim. Existing 64-entry history is not enough for a lap; only the declared synthetic pattern may be materialized longer. |
| Task007C N8 fixed/smooth three-crossing records | Full subsequent-lap geometry, resource estimates and historical N4/N8 illustration | First crossing partial; different codriver timing/source. Do not pool into new measured A/C70 estimates or claim an exact current C70 baseline. |
| Task007C measured N4/N8 records | Retained historical formulation comparison on its own common observed coverage | Some N6 cases failed; preserve them. No new N4 simulations. Distinguish historical formulation comparison from current architecture comparison. |

## VIS-0 checks and deferred work

Read-only audit used actual source, CLI declarations, tests, manifests, raw summaries/journal and
existing reports. Reference names/paths, local Markdown links/fences, hashes, changed-file scope
and `git diff --check` are checked for this documentation delivery. The local check record is
`/private/tmp/apex-vis0-checks.json`: 18 local links, 72 source/test path references, 42 qualified
API references, eight Markdown tables, 14 SHA256 anchors and three static CLI declarations pass.
Short exploratory reads that
looked for nonexistent module names or used an obsolete summary-key spelling were corrected by
inspecting the actual tree/schema; no experimental evidence was altered or produced.

No pytest collection/execution, Ruff (no Python edits), NMPC run, measured experiment, track
generation, rendering or Workbench modification was performed. Historical outputs were read, not
regenerated. A before/after inventory protects all 630 baseline tracked files except the authorized
handoff prepend, and 11,362 existing raw-result file size/mtime entries. Future experiment hashes
must be captured at execution, not inferred from this documentation-only audit.
