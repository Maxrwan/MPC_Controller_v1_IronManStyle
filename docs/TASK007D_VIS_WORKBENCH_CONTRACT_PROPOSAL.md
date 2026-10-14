# APEX Workbench run package — VIS-0 proposal for separate review

**Status: PROPOSED, NOT ACCEPTED OR IMPLEMENTED.** Draft schema `apex-run/0.1.0-draft`.
Audited source: `f072052cd4481df6d987deb6d8d721f1b1b99cb2`; underlying scientific source
`935e98b7af6c2fda8458551f1fbcbddb3bf8932d`. Submit this standalone document to the separately
supervised Workbench for review. This task sends no external message and changes no UI.
See [protocol](TASK007D_VIS_PROTOCOL.md) and [reuse audit](TASK007D_VIS_REUSE_AUDIT.md).

## Packaging and ownership

Use UTF-8 JSON for the manifest, original fixture and variable-length packet arrays; flat CSV
for time series/events/metrics. These match current C/CX and Task007C formats and require no new
dependency, database or service. Proposed package files below do not yet exist.
Control owns scientific exports/definitions; Workbench owns display and ingestion decisions.
Exports are immutable derivatives of retained raw files, written to a new directory. Manifest
hashes link each export to its source; the viewer cannot rewrite scientific evidence.

| Proposed file | Minimum contents and source |
|---|---|
| manifest.json | Schema/run/track/architecture IDs; status/coverage; software, config, vehicle, track/reference and raw/export SHA256; effective configuration; timing policy; clocks/conventions; channel availability; provenance and validation report |
| fixture/ | Original five-file Planning package and vehicle configuration or exact accessible package reference/hash; sector definitions and centerline geometry |
| states.csv | Native physical rows from raw.states: canonical state, applied control, active packet, model diagnostics and recorded boundary flag; optional derived world coordinates clearly named |
| segments.csv | Recorded RK4 step ID/start/end/dt, canonical state_before/state_after and held command from RecordedPlant; preserves terminal bracket and event partitions |
| controls.csv | Applied command records with original generation time, application time, source plan, requested/applied/nominal inputs, sampled APEX reference, errors and computation/physical latencies |
| planning.csv | Offline Planning geometry/speed intent sampled by unwrapped/modulo progress, sector and units; independent of accepted APEX packets |
| packets.json | Every available prepared packet, including rejected/missed packets: plan_id, timestamps, canonical states, inputs, nominal curvature, applicable metadata and original serialization; status joined by ID |
| cycles.csv | Per-planner-cycle release/target/ready/accept/use/expiry/wait/deadline/busy/urgent/censoring fields, including startup if available |
| events.csv | Handoffs, rejection reasons, fixed deadline misses/late discards, busy ticks, urgent triggers, reserve transitions and fallback; separate source stream/row identity |
| reserves.csv | Native sample time, active plan, remaining horizon, age/status and warning/critical values |
| boundaries.csv | Lap/sector boundary IDs/progress, time brackets, derived crossing time/method, complete/partial/censored flag |
| metrics.csv | Per-run/lap/sector/common-window named metrics with units, sample count, time/progress coverage, definition/version, native/derived sampling method and status |

No duplication of full gain matrices into flat UI time series is required; original packets/raw
data remain available. Full NLP/warm-start arrays are optional debug artifacts, not required for
ordinary replay. A manifest channel-availability table is mandatory even for absent optional files.
Downsampled display files are optional, separately hashed derivatives, never the source of extrema
or acceptance metrics. Packet JSON preserves original optional metadata; old variable-mode files
must not be rewritten to pretend fixed fields existed historically.

## Conventions and clocks

- Canonical vector order is **[vx,vy,r,e_psi,s_abs,e_y]** with units **[m/s,m/s,rad/s,rad,m,m]**.
  Inputs are **[delta,a_cmd]**, units **[rad,m/s²]**. Dynamic `a_cmd=Fx/m`; do not label it measured
  longitudinal `dvx/dt`. Positive lateral is left of directed centerline, headings are radians CCW.
- `s_abs` is unwrapped centerline arc length; `s_mod=s_abs % L` is derived display progress.
  `e_psi` is body heading relative to centerline. Derived world yaw is centerline heading+e_psi;
  yaw rate `r` is not a numerical heading derivative. Preserve wrapped angular residuals and
  explicitly unwrap only for named visualization/variation operations.
- Simulation time in seconds from release of the gated rolling startup is the shared physical
  clock. Host measured durations and UTC/process timestamps are separate fields. No wall-clock
  timestamp replaces a simulated event. Sampling is event-driven, not uniformly 200 Hz.
- Every row has `run_id`, source stream and stable source row ID. Commands additionally identify
  generation and application clocks; packets identify their nominal timeline. Coincident rows
  cannot be sorted arbitrarily to determine authority. Use the existing stream/phase semantics
  and raw IDs: prior application, completion, handoff eligibility, physical checks, codriver,
  planner release, possible same-time continuation. A derived event ordering must retain its
  source and cannot invent a total-order counter absent from raw evidence.
- World x/y are derived from recorded Frenet state and the hashed track, not independently
  observed positions. Drawing a vehicle footprint is illustrative unless independently checked;
  center clearance is not swept-body collision certification.

## Requested, nominal and applied controls

For each available applied row expose `command_id` (stable export ID), `t_compute`, `t_apply`,
`source_plan_id`, `requested_delta`, `requested_a_cmd`, `applied_delta`, `applied_a_cmd`,
`nominal_delta`, `nominal_a_cmd`, `measured_computation_s`, `physical_latency_s` and
`reference_{vx,vy,r,e_psi,s_abs,e_y}` with the actual codriver sampling time. Do not overwrite
the source packet with the packet active at later application. Preserve actual application
steering-rate clamping; held commands between applications are piecewise constant.

`states.csv.active_plan_id` describes high-level authority at the state timestamp. A separate
`applied_source_plan_id` is derived only when the logged application history establishes it.
These IDs may legitimately differ after handoff. Startup prepositioning gets an explicit origin,
not an invented runtime computation/application event.

Current raw.controls contains commands when they have applied. A last request still in flight at
termination may be absent. Declare `request_coverage=applied_records_plus_available_release_snapshots`
and `unapplied_tail_complete=false` unless a separately tested observer supplies complete data.
Release snapshots may expose a pending request at that release time, but cannot fill unobserved
intervals. Missing command IDs/timestamps remain null with a reason. Workbench must review whether
this coverage is sufficient; exhaustive request logging is not promised by the current API.

## Planning and APEX references

Planning columns retain the existing package names/units (`s_track_m`, `e_y_ref_m`, `e_psi_ref_rad`,
`kappa_ref_1pm`, `v_ref_mps`) and any available debug world coordinates. The package owns geometric
and speed intent; if a six-state target is exported, explicitly identify the controller's existing
construction vy_ref=0 and r_ref=v_ref*kappa_ref as derived, not additional measured Planning data.

Keep all packet nodes as nominal predicted trajectories. Draw the **accepted active reference** by
joining accepted authority intervals to packet sampling, using the existing interpolation/hold
policy. A rejected or late packet may be displayed as such, never as the line followed by TVLQR.
Use actual `controls.reference_*` for controller-sampled tracking. Planning→APEX adaptation,
Planning→vehicle deviation, APEX→vehicle tracking and future prediction residuals require distinct
metric names. A lower own-reference tracking error is not automatically a better physical route.

## Planner chronology and validity

Each cycle includes `plan_id`, `startup`, `urgent`, `t_release`, `estimated_preparation_s`,
`forecast_target`, `t_ready`, `valid_from`, `t_accept`, `first_TVLQR_use`, `expiry`,
`measured_preparation_s`, `measured_solver_s`, `physical_preparation_delay_s`, `wait_s`,
`deadline_margin_s`, `status`, `miss_time`, `late_discard_time`, `reserve_at_accept_s`,
`packet_age_at_accept_s`, `consecutive_misses` and censoring reasons where available.
Original names/values remain traceable through a documented field map.

For A, `valid_from`, fixed margin and fixed-miss fields are null/not_applicable; its estimated
forecast target is not a contractual deadline. For C70 valid_from=release+.070; a late completion
does not become acceptance. A solver's host-returned packet may exist even if simulated completion
lies beyond coverage. Keep `prepared_on_host`, `ready_in_physics` and `accepted` distinct.
`first_TVLQR_use` comes from actual reference sampling, not inferred solely from acceptance; the
first physical application of that packet's command is another event. An incomplete cycle is
censored, not an invented success/failure.

Urgent demand records preserve trigger, eligible time, grid wait, busy wait, servicing/coalescing
release and accepted authority latency when known. Planner-busy misses, codriver busy ticks and
C70 fixed deadline misses are separate counters. Preserve the actual authority sequence, packet
age/reserve and old-command survival; no interpolation between plan IDs.

Raw readiness `prediction_error` compares potentially different timestamps. Export it only with
its readiness-mismatch definition and target-minus-ready time. Aligned target-state errors, if
available, carry target coverage and reconstruction method. Reconstructed off-event states must
be labeled reconstructed; accepted-handoff continuity error is a separate same-time comparison.
No failed forecast or uncovered target gets a zero residual.

## Coverage, missing data and metrics

Manifest status values distinguish completed, incomplete_duration, stopped_gate, runtime_failed
and not_executed. Store stop reasons and intended/observed physical-time/progress ranges; completed
full laps count only seam-to-seam traversals. The first partial rolling segment is explicit.
Each lap/sector row includes `complete`, `partial_start`, `partial_end`, boundary brackets and
actual metric coverage. Preserve failed runs and empty-but-valid event streams.

JSON missing values are `null`, with status/reason such as not_applicable, unavailable, censored
or forecast_failed. CSV uses empty numeric cells plus a companion status/reason column; never
NaN/Infinity, magic zeros or -1 timestamps. Absent files differ from empty streams. Unknown
additional optional fields can be retained; unsupported major versions fail explicitly.

Validity metrics use native physical samples and terminal recorded endpoints; report left/right
center clearance, boundary count, predicted slack and plan ID, front/rear utilization, beta,
steering/rate/acceleration utilization, Frenet denominator, reserve and fallback. Identify whether
a value belongs to nominal prediction or actual plant. Smoothness definitions distinguish world
yaw, Frenet heading, packet-local nominal variation, stitched active-reference variation and
applied steering variation. Reset traversal differences; report boundary jumps separately.
Common-time/progress comparisons include coverage/counts and do not extrapolate missing tails.

## Future acceptance checks and review questions

Before claiming Workbench compatibility, test serialization round trips for six-state order,
units, raw precision, null/empty handling, duplicate timestamps, source IDs and optional legacy
metadata; test fixed misses/late discards and old pending commands; compare native extrema/counts
to raw evidence; prove no observer/RK4/default-mode interference; verify partial/final-lap brackets,
no interpolation across discontinuous authority and no post-termination extrapolation. Export
creation must leave raw hashes unchanged. Numerical plots must be reproducible from exports.

Workbench review must settle: accepted schema version and mandatory files; request-tail coverage;
native versus optional display sampling; packet payload limits; treatment of derived positions and
crossings; expected error/status rendering. It must also supply external documentation-package
links if desired. No UI edits, browser work, video renderer or schema approval occurred in VIS-0.
