# Task007D-VIS / VIS-1 WORK — prerequisite stop

**Status: BLOCKED — partial WORK delivered for Engineering Review.** The requested
`WORK_COMPLETE_PENDING_REVIEW` exit is not achieved. One 2 s A physical trace completed;
its worker failed during offline snapshot export. C70 parity and all six long runs are
**NOT EXECUTED**. No full-lap, sector-performance or A/C70 scientific conclusion is available.

Both the VIS-1 authorization and its Workbench acceptance addendum are applied. The addendum
changes the export interface, not the experiment matrix. Base revision:
`d55d7b299217d6b62efc90cb525c2493224a7cca`, clean `main` at entry. The final delivery commit is
reported after push. Run source and corrected delivery source are separately hashed in
[execution source](task007d/vis/vis1/evidence/execution_source.json) and
[delivery source](task007d/vis/vis1/evidence/delivery_source.json).

## Scope and implementation

New research-only `scripts/task007dvis/` plus `scripts/run_task007dvis.py` provide a strict ordered
launcher, frozen CX worker construction, lap/sector coverage, native physical/export analysis,
historical parity audit, candidate interface validation and an offline report. No existing source,
test assertion, fixture, controller, scheduler, dynamics, integrator or historical research script
is modified. The same original RK4 calls are observed through the existing RecordedPlant.
No runtime request observer is added. Production defaults remain unchanged.

The frozen controller is N8, dt=0.1 s, H=0.8 s, gamma2, Q=diag(4,4,1,200,200), R=diag(25,1),
W=diag(1,0.1), lambda_s=0, alpha_vy=alpha_r=1, original TVLQR/solver/warm starts, synthetic
0.08 m tracking margin. Predictor A only; C70 remains an experimental scheduler. Initial
s_abs=1 m, accepted synthetic_grand_prix_v1 Planning fixture, imposed 5 ms codriver delay.

The [approved protocol](TASK007D_VIS_PROTOCOL.md) remains intact. Controlled readiness repeats
35/55/45/25 ms, with 8,001 planner and codriver entries materialized before any simulation.
The [compact protocol record](task007d/vis/vis1/evidence/protocol.json) identifies the exact saved
matrix/configuration hashes. Long runs would request two crossings and have an 80 s cap; the
first rolling partial traversal is never counted as a complete lap.

| Ordered case | Execution and coverage |
|---|---|
| parity_A | Physical duration 1.9999999999999787 s; exact retained C3 parity; offline export failed |
| parity_C70 | NOT EXECUTED — predecessor pipeline incomplete |
| controlled_A, controlled_C70 | NOT EXECUTED — prerequisite gate |
| measured_A_1, measured_C70_1 | NOT EXECUTED — prerequisite gate |
| measured_C70_2, measured_A_2 | NOT EXECUTED — prerequisite gate |

There was also one failed **pre-simulation** A compatibility attempt. It did not construct or
run a controller and is not a second physical parity run. Both attempts are retained.

## Failures, corrections and stop disposition

1. The first preflight compared JSON `failed_plan_ids=[]` with the live dataclass tuple `()`.
   Every serialized configuration value matched. The comparison now normalizes the live value
   through JSON without changing values or tolerances; a test also rejects changed delay, lap
   count and failure IDs. This correction preceded the sole physical run. The original
   [preflight failure](task007d/vis/vis1/evidence/initial_preflight_failure.log) remains available.
2. The A worker saved raw.json and segments.json, then failed writing release_contexts.json:
   `TypeError: Object of type ndarray is not JSON serializable`. This occurred **after** physical
   execution. The [full traceback](task007d/vis/vis1/evidence/parity_A_export_failure.log) is
   retained. The JSON writer now handles NumPy arrays/scalars, rejects nonfinite/unsupported
   values, serializes before file creation and uses exclusive creation. Focused tests exercise
   actual isolated-scheduler release snapshots, immutability and overwrite prevention.
3. No racing rerun followed. The stopped process did not save its detached release contexts,
   thread-count observations, environment summary or execution timer. These values are missing,
   not reconstructed or borrowed from historical runs. Exact NMPC-input parity is established
   from saved plans; the distinct release-context forecast replay remains unverified.

The launcher cannot advance past this failed predecessor. Corrected exporter tests are not
substitutes for a complete parity worker pipeline. Engineering Review must decide how to resume
the prerequisite without silently expanding the two-case parity budget. No controller tuning,
assertion weakening or scientific outcome replacement occurred.

## Retained parity and physical audit

Both A and C70 historical applicability checks pass after serialization normalization: frozen
configuration, simulation configuration, vehicle and all fixture hashes agree. Of 87 retained
source hashes, the only differences are the previously reviewed urgent-demand bookkeeping in
asynchronous.py and fixed_handoff.py; the C3 comparison histories have no urgent triggers/demands.
C70 applicability alone is not a new C70 parity result.

The saved A trace passes all **20 exact comparisons**: states, applied controls (excluding host
duration telemetry), handoffs, reserves, releases, misses, codriver misses, triggers, fallbacks,
lap times, termination/failure/pending flags, fixed/urgent records, RK4 segments, packet contents
(excluding host solve/computation durations) and NMPC inputs. See
[exact comparison](task007d/vis/vis1/evidence/parity_A_exact_comparison.json).
No tolerance was introduced for physical parity.

Offline audit uses 401 native states including the terminal recorded RK4 endpoint, 400 segments
and 19 runtime planner cycles. It does not execute a solver or propagate a new physical step.

| Short A trace metric | Recorded result |
|---|---:|
| Complete laps / seam crossings | 0 / 0 |
| Progress reached / gain | 12.5238266411 / 11.5238266411 m |
| Recorded center clearance, minimum | 0.4373138184 m |
| Clearance after synthetic tracking margin | 0.3573138184 m |
| Predicted slack, maximum | 9.0915252854e-11 m |
| Minimum active reserve | 0.667 s |
| Boundary crossings / solver failures | 0 / 0 |
| Accepted / rejected handoffs | 19 / 0 |
| Planner / codriver busy misses | 0 / 0 |
| Chronology issues | 0 |

The [offline analysis](task007d/vis/vis1/evidence/parity_A_offline_analysis.json) retains six-state
tracking, native window/sector extraction, smoothness and timing diagnostics, with
[cycle data](task007d/vis/vis1/evidence/parity_A_cycles.json). Its missing release/thread checks
are explicitly unverified; they are not interpreted as observed causal mismatch or multithreading.
Recorded center clearance is not swept-body safety. The short trace provides no new full-lap
performance, measured timing or A-versus-C70 evidence.

## Workbench addendum deliverables

[apex-run/0.1.0](APEX_RUN_INTERFACE_0_1_0.md) is the versioned candidate normative contract.
It defines required/header-only streams, source-preserving partial event order, native versus
reconstructed samples, channel/null reasons, termination/lap coverage, authority intervals,
command application/provenance, geometry, artifact hashes/sizes/counts and metric scopes.
Scientific run revision and export-tool revision remain separate.

Request coverage is exactly `applied_records_plus_available_release_snapshots` with
`unapplied_tail_complete=false`; an unseen terminal request is unknown. No exhaustive observer
or interpolated command/packet authority is introduced.

Four self-contained [representative packages](task007d/vis/vis1/contract_fixtures/validation.json)
use retained evidence, not fabricated or newly measured racing outcomes:

| Package | Retained source and cutoff | Distinct validation |
|---|---|---|
| nominal_A | C3 gamma2 variable, 0.210 s | A handoffs, applied commands |
| C70_miss | C2_miss, 0.500 s | accepted authority; miss at .470 s, discard at .475 s, old authority continues |
| censored_A | C3 gamma2 variable, 0.190 s | unresolved tail; request scheduled at .195 s is outside retained view |
| empty_optional_A | C3 gamma2 variable, 0 s | empty event stream with header, unavailable optional reserves |

Canonical ordering, clocks, nullability, authority, metrics, packet statuses and hashes pass.
Coincident timestamps and old-command provenance also have isolated deterministic tests.
Original scientific source hashes remain in each manifest; the four packages' export hashes
identify their earlier adapter generation. Later writer/report corrections do not alter these
packages; their bytes and validations were rechecked. Workbench ingestion and final interface
acceptance remain **PENDING**. No Workbench UI/importer is implemented.

## Checks, provenance and preservation

The prerequisite selection ran before the physical run: **410 passed**, zero failures/errors/
skips, pytest 165.46 s. Subsequent affected adapter checks passed 27, then 28, then 29, finally
**30 tests in 15.41 s**. These overlap: the final applicable set is 384 unchanged prerequisite
cases plus 30 current adapter cases, **414 distinct cases**, not the sum of invocations.
All final 13 Python files pass Ruff lint and format. Commands, JUnit durations and log hashes are
in [verification](task007d/vis/vis1/evidence/verification.json). Complete numerical regression
is intentionally deferred to authorized VIS-4 VERIFICATION.

Verification environment: macOS 26.5.1 arm64, Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1,
CasADi 3.8.1. The worker was launched with the existing fresh SINGLE bootstrap and guards;
its actual thread observations were lost before summary output and are not claimed verified.
Host timings are descriptive only. No measured campaign was launched. Before launch the process
check found no competing experiment/test; guards were clear and free space was about 6.77 GiB,
above the 1 GiB floor plus 1.5 GiB headroom. Guard cleanup followed worker exit.

All preexisting core/configuration/fixture/script hashes and historical raw size/mtime entries
remain unchanged; the final [preservation audit](task007d/vis/vis1/evidence/preservation.json)
records counts and permitted documentation-only changes. No historical Task007 evidence was
removed, overwritten or relabeled. The old handoff is retained verbatim below the new entry.

## Missing results and next review

Full-lap/per-sector A/C70 comparisons and preliminary comparison figures are **NOT EXECUTED**.
The [report tables](task007d/vis/vis1/tables/summary.json) distinguish the failed worker from
unexecuted cases; header-only comparison tables represent missing coverage. No empty chart is
presented as a scientific result. Paired plotting code remains unvalidated on new VIS long runs.

Review the export fixes, missing evidence and prerequisite continuation first. Do not promote
C70, freeze Performance, start Efficiency, VIS-2/new track, VIS-3/UI/video, B/C80 or new controller
work. No recommendation about full-lap architecture superiority can be made from this delivery.
See [reproduction and retained logs](TASK007D_VIS1_REPRODUCTION.md).
