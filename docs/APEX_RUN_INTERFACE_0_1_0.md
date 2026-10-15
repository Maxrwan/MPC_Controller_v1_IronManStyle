# apex-run/0.1.0 scientific export interface

**Status:** candidate implementation under the VIS-1 Workbench acceptance addendum.
The scientific model is conditionally accepted; final interface acceptance still requires
representative-package ingestion by the separately supervised Workbench. Control owns this
adapter, not the Workbench importer or UI. No new runtime observer is introduced.

This version implements the [VIS-0 proposal](TASK007D_VIS_WORKBENCH_CONTRACT_PROPOSAL.md)
with the normative amendments below. Source scientific revision and export-tool revision are
independent provenance fields. A dirty source tree is identified by its file hashes, not claimed
to be fully represented by the base Git SHA. All VIS simulation mathematics and timing semantics
remain unchanged.

## Files, identity and encoding

Required: manifest.json, states.csv, segments.csv, controls.csv, planning.csv, packets.json,
cycles.csv, events.csv, boundaries.csv, metrics.csv and fixture/ (or an immutable fixture reference).
reserves.csv is optional. The current adapter copies the original five-file fixture; it does not
generate a new reference. Every required CSV exists even when empty, with its valid header.
UTF-8 JSON/CSV, comma delimiter, LF records and ordinary decimal SI numbers are used. Lists/maps
inside CSV cells are JSON. No NaN/Infinity, synthetic zero observations or -1 timestamps are allowed.

The manifest identifies `schema="apex-run/0.1.0"`, run_id, architecture, termination, coverage,
channel_availability, request_coverage, accepted_authority_intervals, packet_status, provenance,
metric_definitions and artifacts. `artifacts` maps each data/fixture path to SHA256, bytes and CSV
data-row count (excluding header); non-tabular counts are null. `manifest.sha256` authenticates
the manifest separately, avoiding a self-referential hash. Export validation records are outside
the package. Hashes detect accidental changes; they are not a signing/authentication scheme.

`provenance.scientific_revision` and `scientific_source_sha256` describe the run implementation.
`export_revision`, `export_source_sha256` and `dirty_status` describe this adapter at export time.
Retained-evidence validation excerpts keep their original scientific revision and have
`evidence_kind="retained_evidence_censored_view; not_new_experiment"`. They are never new measured
racing outcomes. Raw hashes point to the original retained files, not fictitious truncated runs.

## States, controls and geometry

Canonical state order: `[vx,vy,r,e_psi,s_abs,e_y]`, units `[m/s,m/s,rad/s,rad,m,m]`.
Input order: `[delta,a_cmd]`, units `[rad,m/s²]`. Dynamic a_cmd is Fx/m, not measured dvx/dt.
Frenet lateral is positive left; angles are radians CCW. Simulation physical seconds are the
authoritative clock. Host computation durations remain separate descriptive fields.

states.csv retains native time, canonical state, delta/a_cmd, plan_id, mode and recorded physical
diagnostics. `sample_kind=runtime_event` identifies simulator rows;
`recorded_RK4_endpoint_before_next_events` identifies the actual final step endpoint missing from
the runtime row list. Both have `sample_provenance=native`. The latter must not be presented as a
sample after unprocessed endpoint events. segments.csv contains start/end/dt, state_before,
state_after and held control from existing calls to the original integrator.

`plan_id` is accepted high-level authority. `applied_source_plan_id` identifies the packet that
generated the held physical command; these may differ after a handoff. A source ID of 0 before
the first runtime application denotes the recorded startup prepositioning, not an invented command.
controls.csv retains original `time` (generation), `application_time`, plan_id (generation source),
requested_delta/requested_a_cmd, delta/a_cmd (actually applied), nominal controls and sampled
reference/error channels. Steering is piecewise constant between actual applications. Its
application-time rate limiting is preserved. Never interpolate packet IDs or steering between
applications to manufacture intermediate physical commands.

Derived world coordinates use the hashed track's existing periodic centerline:
`x=c_x(s)-e_y*sin(psi_c(s))`, `y=c_y(s)+e_y*cos(psi_c(s))`,
`psi_world=psi_c(s)+e_psi`, with geometry queried at s_abs modulo track length.
They are reconstructed coordinates of native Frenet evidence, not independent world-position
measurements. Center clearance is not a continuous swept-body collision certificate.

planning.csv preserves original Planning fields including s_track_m, e_y_ref_m, e_psi_ref_rad,
kappa_ref_1pm and v_ref_mps. Six-state Planning targets, when provided in state views, use the
existing derived vy_ref=0 and r_ref=v_ref*kappa_ref construction. packets.json preserves original
packet serialization including all available prepared, missed/rejected and pending packets;
manifest packet_status joins these by plan_id. Packet states are nominal predictions, not future
physical truth. Reconstructed active-reference fields sample only accepted packets using the
existing interpolation/hold policy.

## Chronology and authority

events.csv contains time, phase, within_phase_order, source_stream/source_row, event_kind, plan_id
where applicable and the original payload. It is a partial-order view, not a new scheduler log.

| Phase | Existing scheduler meaning |
|---:|---|
| 1 | Previously requested actuator application |
| 2 | Preparation completion; immediate variable-mode handoff if eligible; late fixed discard |
| 3 | Waiting variable or fixed handoff eligibility; fixed deadline miss |
| 4 | Disturbance and fallback processing |
| 5 | Codriver generation/busy tick and associated urgent trigger |
| 6 | Nominal/urgent planner release or planner-busy miss |

For variable A, a handoff coincident with its readiness belongs to phase 2; a waiting handoff
belongs to phase 3. Fixed handoffs belong to phase 3. Original per-stream indices preserve identity.
`within_phase_order=null`, reason `ordering_not_recorded`, avoids inventing a cross-stream tie
order. Same-time zero-duration loop continuations cannot be globally ranked from these raw logs;
the manifest states this limit. No extra event sequence is fed back to simulation.

cycles.csv retains release, forecast target, readiness, scheduled valid_from, actual acceptance,
first TVLQR use, expiry, preparation/wait/deadline/age/reserve and status/censoring data. Startup is
represented by the initial authority interval and raw packet/plan, not fabricated as a runtime cycle.
For A, fixed deadline fields are null/not_applicable. C70 late results remain missed and cannot
create accepted intervals. Solver-ready, accepted and physically applied are distinct events.
Variable first-use coverage comes from available applied-command logs; a terminal unobserved
request can censor that information.

accepted_authority_intervals derive from recorded startup/accepted handoffs, nominal expiry and
any recorded fallback. They are left-inclusive, normally right-exclusive; the observation endpoint
may be included when no subsequent event was processed. Supersession, expiry and right censoring
are explicit. These intervals never reassign an older pending command to the new packet.

## Availability and coverage

The accepted request contract is exactly:

```json
{
  "mode": "applied_records_plus_available_release_snapshots",
  "unapplied_tail_complete": false,
  "terminal_unobserved_request": "unknown"
}
```

There is no exhaustive request observer. A missing terminal request is unknown, not known absent.
Raw release_contexts.json remains available with release-known pending snapshots; the scientific
package advertises the coverage rather than synthesizing absent request records.

channel_availability distinguishes available, empty and unavailable with reasons. Every emitted
CSV row includes missing_reasons for its explicit null fields. An absent optional field in a
heterogeneous event row is not_applicable to that event type. Numeric nulls are empty CSV cells
or JSON null; reasons include not_applicable, censored, ordering_not_recorded,
not_observed_or_not_applicable and channel-level not_recorded. A header-only required stream is
empty, not a missing file. Consumers must not infer zero measurements from either case.

`sample_provenance` is native, reconstructed or display_interpolated. The current adapter emits
no display-interpolated acceptance data. Manifest field_provenance distinguishes reconstructed
world/reference fields within otherwise native state rows. Aggregate metrics and boundary
crossing times are reconstructed from recorded inputs and are labeled accordingly.

Termination records the simulator reason/failure, scientific gates, intended duration/crossings,
simulated end and native observed bounds. coverage lists crossing brackets and lap windows;
from s_abs=1 m the first traversal is initial_partial, not a completed lap. A final incomplete
traversal is censored_partial. boundaries.csv crossing times use linear progress interpolation
inside a recorded RK4 bracket and do not invent independently sampled seam truth.

## Metric definitions and validation

metrics.csv uses definition ID `vis1.native_window.v1` and explicit aggregation_scope (run, lap,
sector, common_time or common_progress), intended and sampled bounds, sample count and completeness.
RMS/signed means use left-held time weights over native sample intervals; angular residuals wrap.
Maxima/minima use native samples including recorded final endpoints. Variation uses adjacent
native differences within the window; actuator rates use actual application intervals. Boundary
times/durations are derived and their integration brackets are retained. No missing tail is padded.
Per-sector and lap scopes reset variation rather than adding fictitious seam jumps.

Scientific checks and four export-validation packages precede claiming adapter compatibility.
Tests cover canonical ordering, finite values, timestamps, nulls/empty streams, native provenance,
source preservation, packet status and accepted-authority reconstruction. They do not substitute
for Workbench ingestion. A schema/importer disagreement must not change scientific runtime behavior.
