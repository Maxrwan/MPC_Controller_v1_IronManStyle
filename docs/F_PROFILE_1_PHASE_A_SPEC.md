# F-PROFILE-1 — Phase A execution specification

**WORK_COMPLETE_PENDING_REVIEW — documentation and specification only.** Recorded 22 October 2026.
Inspected source: `eaa0a3398515a21f30a850de59a0b44c775fad4d` on `research/efficiency`.
No instrumentation, numerical tests, profiling, simulation or benchmark is implemented or executed.

## 1. Authority and immutable references

Primary APEX's **APPROVED WITH CONDITIONS** decision is recorded in the separate
[F0 acceptance overlay](task007f/f0/primary_acceptance.json), bound to the exact F0 delivery above.
The human-supplied assignment is the authority evidence; no independent Primary transcript or
exact acceptance date was supplied. The recording date does not invent that decision date.
Original F0 specification/evidence retain their historical pending-review labels and bytes.

Primary accepts the lexicographic objectives (validity → authority/reliability → compute/resources
→ acceptable racing/tracking), Pareto comparison and research order. F-PROFILE-1 is the first
proposed experimental workstream. The two-phase structure and 10×2-second plus 10×12-context
research basis are conditionally approved; this assignment authorizes this specification only.
RMS/TV floors, peak thresholds and nonuniform-grid cost policies are deferred until their dependent
scientific studies. They do not block writing passive instrumentation and cannot be invented later.

Frozen Architecture A remains N8, H=0.8 s, predictor A, variable handoff and 100 Hz TVLQR with the
independent NumPy plant and native SINGLE policy. The release branch and annotated tag stay at
E4 `48adbdf64d492592d15e23c917aca71fa58aa8a5`; scientific source/profile remains
`e603672b209985f11ed26b6f44d3949ffd5675c5`. The original manifest SHA256 remains
`5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
No runtime profile, accepted-manifest flag, solver option, grid or default is changed.
Historical C70 misses, exhaustion and incomplete export remain negative evidence.

S0/S1 are independent Safety work. The inspected
[S0 authority proposal](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/3747e0d9a7e834a5df34c4b089a5292c0a749fa4/docs/safety/s0/authority_interface.json)
separates **feasible proposal**, **accepted trajectory authority**, and **application permission**.
Instrumentation may observe these distinctions; it cannot create a Safety grant. Frozen A does
not implement S0 permissions or guaranteed recovery. Simulated application is not a physical
actuator acknowledgement. No S1 implementation status is presumed.

## 2. Versioned contracts and proposed implementation surface

- [Instrumentation contract](task007f/profile1/instrumentation_contract.json): source revisions,
  file hashes, function/line anchors, span tree, clock/record fields and accounting.
- [Parity and observer checks](task007f/profile1/parity_and_observer_checks.json): exact semantic
  channels, controlled cases, timing exclusions and independent observer assessment.
- [Phase B readiness](task007f/profile1/phase_b_readiness.json): conditional campaign basis,
  inspected retained evidence, read-only context procedure and recovery blockers.
- [Review gates](task007f/profile1/review_gates.json): explicit future authorizations, unresolved
  decisions, hard stops and independent Safety reference.

These JSON records specify future behavior; none is a runtime configuration or a completed check.
Their schema identifiers and typed record fields are versioned 1.0.0. The instrumentation contract
is the normative boundary/field inventory; the checks record defines comparison requirements.
Future implementation changes to either require review before execution.

Propose a new research-only launcher, `scripts/task007f/profile1/run_phase_a.py`, with explicit
`--efficiency-instrumentation profile1-v1`; this path and flag do not exist yet. Use optional
recorder injection with default `None`, scoped to that worker. OFF must add no recorder imports,
record allocations, capture copies or added clock reads. Preserve existing diagnostics/packet
schemas and the frozen profile. Unknown modes reject; environment variables cannot silently enable
profiling. A source diff and candidate identity remain mandatory even for supposedly neutral hooks.
Observe both disabled-hook overhead versus pristine A and enabled-observer overhead versus OFF.

Future recurring hooks are confined to planner/controller/preview/IPOPT/tracker boundaries listed
below; construction uses wrappers at the research composition root. No global clock patching,
tracing framework, backend replacement, changed equations, repeated solver/validation work or
extra scheduler/RK4 events is permitted. New data live in a bounded in-memory sidecar keyed by
worker, plan, span and occurrence; serialize after the measured kernel/worker. Hashing and snapshot
copies have observable costs and cannot be hidden inside an excluded category.

## 3. One-time construction, startup and recurring boundaries

All source anchors below refer to the inspected revision, not moving `main`. Exact hashes and
immutable source links are in the instrumentation contract. Recheck anchors before implementation.

| Population / phase | Existing boundary and future measurement requirement |
|---|---|
| Construction | Research composition root before fixture/vehicle/reference loading until completed plant/controller/planner/tracker construction. Nest `MPCProblem.__init__` graph work; `IpoptSolver.__init__` / `ca.nlpsol`; `MPCController.__init__` / `TerminalSchedule`; `TrajectoryPlanner.__init__` / TVLQR Jacobian creation. Keep residual setup visible. |
| Gated startup | Entire `prepare(0,...,startup=True)`, separately from construction and recurring work. Preserve prepositioning, launch gate and startup rejection behavior. |
| Full recurring preparation | Immediately before `TrajectoryPlanner.prepare` invocation through returned tuple receipt or original exceptional exit. Includes final packet replacement and returned dict/list construction. |
| Prediction | Planner lines 38–47: startup branch or `ActuationPredictor.predict`, including the private tracker clone. Preserve release-known state and previous-command provenance. |
| Reference | Controller lines 69–80: complete `make_preview`. Geometry/reference loop children are nested; array construction and progress advancement remain parent residual. |
| Warm start | Controller lines 81–89: terminal lookup and exactly one shifted/cold guess. Separate terminal lookup from `shift_solution` / `cold_start`; retain the legacy combined timing field. |
| Parameter preparation | Controller lines 90–95: `NLPRequest`, packed initial vector and parameter vector. |
| IPOPT | Controller's complete solver adapter call, with a child enclosing only `IpoptSolver.solve`'s `self.backend(...)` invocation. Adapter statistics/extraction/feasibility are another executed child/residual. |
| Solution validation | Controller lines 99–170: existing shape/finite/bounds/constraint evaluation, solution copies, objective components and rejected-solution reset. Never rerun evaluation for a timer. |
| Initial packet | Planner lines 54–73: nominal packet and curvature replacement, including existing packet validation and copies. |
| TVLQR gains | Existing `TVLQR.compute`: 100 Hz sampling/Jacobians, terminal DARE, backward recursion and return array. No change to design, rate or numerical ordering. |
| Packet completion | Gain attachment at planner line 76; final duration replacement at 86–87; return assembly at 88–110. Each is disjoint from the new gain-compute span. |

Timing each existing packet-construction invocation at its caller includes
`TrajectoryPacket.__post_init__` without changing the packet implementation or validation.
Historical `gain_time` includes gain attachment; the new compute-only gain span has a distinct name.
Historical `planner_total_time` and `planner_cpu_time` stop at lines 84–85, before final replacement
and return assembly. Preserve them exactly as legacy measurements and report the full-call boundary
difference explicitly. Successful historical `solve_time` starts before backend keyword evaluation;
the backend-only child is a new measurement, not a renamed historical field.

## 4. Clocks, nesting and causal readiness

Use `perf_counter_ns` for monotonic host wall time and `process_time_ns` for worker-process CPU.
Store integer nanosecond endpoints and derive seconds without replacing raw values. Read wall then
CPU at both ends and record implementations, resolution and empirical clock-pair skew. CPU may
exceed wall because it covers the whole process; do not clamp it. UTC is metadata only.

Each span has an inclusive duration. Subtract only its **complete immediate children** to derive
exclusive work/residual on the same clock. Sum disjoint siblings, never parents plus descendants.
Preview geometry/reference are inside preview; IPOPT and adapter validation are inside adapter;
gain children are inside gain compute; controller is inside preparation. Preserve signed residuals
and investigate negative/uncovered accounting against the reviewed clock calibration allowance.
Missing or partial coverage is null/partial with a reason, not zero. The allowance is an unresolved
review decision, not an arbitrary tolerance installed by this specification.

Also observe a research dispatch envelope from the existing release boundary before optional
capture/recorder work through prepare return and sidecar append, immediately before delay selection.
This requires a reviewed passive opt-in hook around `AsyncRunner.run.release` lines 222–245;
the existing release-observer callback starts after its capture argument has been constructed and
cannot alone enclose that cost. The hook must not alter delay selection or create a physical event.
Report preparation, capture/append, later serialization and whole-worker CPU separately. No export
or process monitoring probe is inserted inside the solver. Any monitoring overhead must be identified.

Keep three clock domains explicit: monotonic host wall, process CPU, and simulated physical seconds.
Never add a host timestamp to simulated time. Release time, estimate-at-release, forecast target,
modeled completion, observed completion, acceptance, packet interval, request and application remain
distinct. Future outcomes are null until observed; they cannot enter the captured causal context.
Preserve current event order: due application → preparation completion → waiting/fixed resolution
→ disturbance/exhaustion → codriver → nominal/eligible urgent release → held-input physics.

**Readiness accounting is an explicit gate.** `AsyncRunner.run.release` currently consumes the
legacy `planner_total_time` for measured dispatch (lines 246–254), or the existing controlled timing
interface. Phase A must not silently redirect that consumer or replace packet duration metadata.
Controlled parity uses identical imposed delays. Observer probes report the legacy modeled result,
full preparation and full dispatch envelope, plus the corresponding would-be readiness difference;
the counterfactual has no authority. A later Phase B decision must distinguish legacy A timing from
an independently versioned full-boundary timing policy. Full-preparation availability claims require
charging the declared full envelope, including observer cost, under a separately reviewed mapping.
Neither ignoring that overhead nor silently changing A scheduling is acceptable.

## 5. Required future numerical and authority parity

Compare three fresh-process builds: **B0** pristine frozen implementation, **B1** future hook build
OFF, **B2** that same build ON. Freeze fixtures, actual backend, source diff, dependencies, replay
traces, seed and threading before execution. B0/B1 tests the disabled path; B1/B2 tests observation.

Under zero and predeclared injected planner/codriver timing require exact relevant finite numerical
values, shapes and dtypes, and binary equality where binary arrays are available. Compare:

- all canonical states `[vx,vy,r,e_psi,s_abs,e_y]`, controls `[delta,a_cmd]` and previous/pending
  commands; SI units and dynamic `a_cmd=Fx_total/m` remain unchanged;
- prediction inputs/results, preview/progress, terminal matrix, complete pre-call optimizer
  X/U/slacks, packed request, solver status/iterations/objective/feasibility, solution and reset state;
- every packet's semantic fields, including `valid_from` even where a historical serializer omits
  it, nominal trajectories, curvature, gain timestamps/gains, validity and source IDs;
- each physical/predictor RK4 interval, held input, internal stage/end state and validation outcome;
- startup, release/busy/completion/wait/accept/reject/reserve/expiry, codriver deadlines, physical
  applications, original command provenance, fallback and stop/censoring chronology.

Do not wrap headings, interpolate states or weaken existing tolerances to conceal a difference.
Exclude only explicit clock/duration field paths, including packet `solve_duration` and
`total_computation_duration`; keep their values for timing analysis. Enumerate returned IPOPT
timing keys individually; never exclude a whole statistics object. Complete the codriver/new-field
path allowlist in the reviewed implementation test manifest before use. Controlled authority
timestamps cannot be excluded. Measured wall equality and measured closed-loop trace equality
are not assertions: instrumented readiness may change, and those changes must be reported.

The checks contract lists P01–P09 and applicable existing test paths. Add focused tests for default
OFF, exact parity, nesting, recorder failure, partial paths and censored tails only in the future
authorized implementation. Negative fixtures must exercise prediction/solver/validation/gain failure,
waiting/late/rejected packets, busy deadlines, expired authority and pending completion. They compare
to the uninstrumented oracle; they are not new successful scientific runs. Full regression remains
a separately authorized exact-reviewed-revision gate, not something executed for this prose.

## 6. Independent observer-effect assessment and outcome accounting

Before any authorized measured use, predeclare an independent Phase A observer plan: exact cold/warm
test contexts, paired OFF/ON and pristine/OFF repetitions/order, and its own RAM/disk/host budget.
These values are unresolved; the conditional Phase B budget does not authorize Phase A probes.
Measure empty clock/span/append overhead separately from actual tracing and any snapshot-copy mode.
Use fresh sequential SINGLE processes with actual backend/thread observations; an environment value
or empty threadpool listing alone is insufficient. Do not change the backend or run stack probes
that solve a problem merely to recover documentation context.

Retain raw CPU/wall deltas, counts, maxima, cold/recurring distinction, run-level uncertainty,
clock calibration, RSS and any changed readiness/ownership. Do not subtract a favorable assumed
overhead or declare a cost negligible without review. No numerical observer-overhead threshold is
invented. Exact controlled parity is mandatory regardless of measured overhead magnitude.

Every launched call has a record, including exceptions, rejected/late preparations and those physically
pending when the simulation stops. Use `finally`-safe observation without masking the original
exception. Reached spans remain; unexecuted children have explicit status/reason. Recorder overflow
or failure cannot silently drop samples or trigger numerical fallback; report it and stop the
affected worker at the existing safe reporting boundary. Preserve the original solver/preparation
outcome separately from instrumentation failure.

The recurring metric uses launch cohort `[t0,t1)`: charge each observed full call's CPU, including
a terminal physically pending call, and mark its physical completion censored. If the host call
itself is interrupted, retain observed partial cost as a lower bound and mark the aggregate incomplete.
Do not imply acceptance or application from solver success. Offline context panels have no simulated
duration and provide per-call CPU/wall only. Preserve all outliers and unsuccessful attempts; no
replacement or outcome-selected rerun is authorized.

## 7. Phase B readiness and retained-context blockers

The conditional basis remains ten fresh 2-second A workers with measured planner availability and
imposed 5 ms codriver, plus ten fresh offline workers with twelve contexts each: four straight,
four sustained corner, four transition. Native SINGLE and isolated sequential execution are required.
The proposed 20-minute host allocation, 1 GiB worker peak RSS and 1 GiB output reservation are
ceilings, not predictions or authorization. Require 1 GiB free plus remaining output headroom
(initially at least 2 GiB). Inspect measurement guards and actual processes before each worker;
never delete a guard or historical evidence to proceed. Stop starting workers if resources expire.

Read-only schema/hash inspection found 622 controlled-A and 620 measured-A release contexts in the
retained VIS1R/VIS1L scientific archive. Exact paths and hashes are in the readiness record. They
contain release state/time/estimate, active packet, tracker configuration/limits and applied/pending
command prefix. Raw plans have scalar slack diagnostics. **They do not contain the full pre-call
optimizer X/U/slacks and reset lineage needed to establish faithful warm-start recovery.** An
active authority packet is not necessarily the latest optimizer solution; aggregate slack values
cannot reconstruct the array. This finding is scoped to the inspected files, not a claim that every
historical archive was searched.

No twelve-context panel or exact IDs were selected. The readiness record defines the read-only
procedure: verify immutable provenance; join causal release/authority records; establish complete
pre-call warm state; review Planning-curvature/progress strata and sustained/entry/exit criteria;
choose geometry-only progress representatives with deterministic ties; then freeze IDs, JSON
pointers and full-context/file hashes in a new manifest. Do not rank contexts by solver cost.
Exact geometry quantile/dwell definitions remain a review decision. Missing strata remain missing.

**Phase B is blocked** until exact contexts and faithful warm starts are established, or Engineering
explicitly approves a labelled cold-start diagnostic amendment. No guessed slacks, packet-derived
substitute warm start, historical regeneration or new experiment may fill the gap. A cold panel
cannot establish recurring warm preparation cost. Two-second workers cannot certify lap criteria,
rare-deadline reliability or embedded real-time performance.

## 8. Gates, preservation and handoff

Review G0–G6 separates specification review, implementation authorization, Phase A execution,
engineering acceptance, formal verification, Phase B authorization and later candidate acceptance.
D1–D6 records exact API/exclusion, fixture/observer budget, clock calibration, readiness mapping,
context recovery and later scientific decisions. No status automatically authorizes the next gate.

Stop the affected branch for unexplained parity/chronology changes, future leakage, invalid model/
actuator/grip state, recorded boundary crossing, predicted slack above 1e-6 m, unexpected solver/
gain failure or fallback, lost authority/exhaustion, unreconciled timing, provenance mismatch or
resource/isolation failure. Predeclared negative test cases have their own expected oracle outcomes;
new unexplained scientific failures are retained and returned for review, never tuned away.

This delivery changes documentation only, on the already checked-out `research/efficiency`; a second
worktree on that branch would conflict. Future implementation should use a separately coordinated
clone or authorized task branch/worktree. Do not disturb the independent Safety checkout, move
frozen refs or merge into `main`.

Only strict JSON/structure, source/hash/line references, documentation links, Git identity/protection,
whitespace and preservation checks apply now. Their compact record is
[validation](task007f/profile1/validation.json). Historical numerical passes are not rerun or claimed
to validate unimplemented instrumentation. Normal scoped commit/push delivers these documents;
the final handoff supplies its containing SHA without a self-hash cycle.
**Stop at WORK_COMPLETE_PENDING_REVIEW.**
