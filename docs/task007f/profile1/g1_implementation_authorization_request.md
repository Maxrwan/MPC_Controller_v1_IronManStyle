# F-PROFILE-1 — bounded G1 code authorization request

**PROPOSED — NOT IMPLEMENTED. WORK_COMPLETE_PENDING_REVIEW.** Recorded 23 October 2026.
Base and accepted Phase A delivery: `ff34bd36897c4ed00b850a2d0255132bdebac5fd`.
Branch: `research/efficiency`; documentation/assignment preparation only.

## 1. Decision requested and authority

The human-supplied Primary APEX decision accepts the
[Phase A design](../../F_PROFILE_1_PHASE_A_SPEC.md) with conditions: 22-span accounting, complete
preparation/dispatch measurements, pristine B0 / OFF B1 / ON B2 checks, strict numerical/packet/
RK4/authority parity, independent observer assessment and separate Phase B authorization.
Its exact decision date was not supplied. This document records that subsequent decision without
rewriting the original Phase A or F0 status/evidence. F0 remains bound to
`eaa0a3398515a21f30a850de59a0b44c775fad4d` through its separate acceptance overlay.

The next requested instruction is: **authorize only the G1 implementation described by this
versioned API, ten-path source/test allowlist, field-path policy and failure contract; return for
Engineering Review before G2 execution.** That instruction has not been granted by this assignment.
No recorder code, launcher, source tests, calibration, numerical import/backend construction,
solver call, simulation, profiling or benchmark is performed here.

Authoritative proposed records:

- [Recorder API](g1_recorder_api.json): signatures, bounded storage, exact span catalogs and clocks.
- [Source change manifest](g1_source_change_manifest.json): ten permitted future paths and precise
  functions/insertions; all 19 accepted anchors reinspected against the current branch.
- [Parity field-path policy](g1_parity_field_allowlist.json): 98 duration leaf selectors, 14 individually
  named IPOPT timing keys, strict default comparison and one explicit host-derived predicate.
- [Failure/overflow contract](g1_failure_and_overflow_contract.json): original outcome versus observer
  validity, safe reporting boundaries and incomplete evidence.
- [Verification entry gates](g1_verification_entry_gates.json): exact proposed G2 fixtures, samples,
  independent resources and unresolved decisions.
- [Preflight validation](g1_preflight_validation.json): this delivery's static checks/preservation.

## 2. Exact proposed recorder interface

The API record gives complete signatures and field types. The core is a worker-local recorder
created by `create_recorder(*, mode, identity, limits, clock=None)`, with:

1. `begin_call(kind, plan_id, release_sim_s, estimate_sim_s)` for a construction, startup, recurring
   or separately labelled clock-probe call.
2. `span_begin(call, span_id, expected_parent=...)` returning a reserved slot token; then
   `span_end(token, exit=..., exception_type=...)` in explicit exception-safe paths.
3. `finish_call(call, outcome=...)`, preserving the original returned-packet/None/exception outcome.
4. `stop_requested`, then post-kernel `reconcile`, `seal(legacy_result, termination)` and
   `write_sidecar(sidecar, output_dir=...)`.

Tokens are worker-local integer identities. Each span reserves one bounded slot for both endpoints,
with actual parent token, occurrence count, sequence numbers, raw wall/CPU integer nanoseconds,
exit and coverage. Qualified exception type is sufficient inside hooks; arbitrary exception
formatting is deferred. No numerical arrays or live controller/packet references enter the recorder.

Proposed limits are 64 calls, 8,192 span records, nesting depth eight, 64 diagnostic faults and
16 MiB serialized sidecar per worker. Identity/type lengths are bounded. A first-fault slot is
reserved. These caps do not prove Python RSS or infallible persistence; actual memory is guarded.
No ring overwrite, silent record loss or zero-cost observer assumption is permitted.

The research launcher parses `--efficiency-instrumentation {off,profile1-v1}`, default **off**,
with stdlib only. Unsupported modes fail before numerical imports. OFF does not import the recorder,
allocate capture records/context managers or call added instrumented clocks. Numeric modules accept
an optional `recorder=None` object by injection and do not import the research recorder module.
ON is configured only in a fresh explicitly selected SINGLE worker before numerical imports.
The disabled branch itself can cost time; B0/B1 measures that separately.

No global time patching, solver replacement, tracing framework, background writer or new dependency
is proposed. Test-only clock injection uses the explicit `ClockReader` argument, not a global patch.

## 3. Bounded future source diff

The source manifest is an explicit allowlist. Only the following runtime/test paths may change
after a separate G1 approval; every other source change requires review:

| Future path | Permitted change |
|---|---|
| `src/apex/control/trajectory/planner.py` | Optional constructor injection; prediction/controller/packet/gain/return spans. `prepare` arguments and result unchanged. |
| `src/apex/control/mpc/controller.py` | Optional constructor/composition injection; construction/reference/warm/packing/adapter/validation spans. Preserve original computation/evaluation order and exactly one execution. |
| `src/apex/control/mpc/preview.py` | Optional keyword-only recorder; executed geometry/reference child occurrences. |
| `src/apex/optimization/solvers/ipopt.py` | Optional constructor injection; backend-call versus adapter-validation spans; existing backend/options/exception semantics retained. |
| `src/apex/control/trajectory/tracker.py` | TVLQR-only optional injection and Jacobian/DARE/backward blocks. No changes to `TrajectoryTracker.command/update`. |
| `src/apex/simulation/asynchronous.py` | Optional recorder, startup/full-call/dispatch envelope and explicit observer-invalid reporting stop. No normal scheduling/authority/timing-policy change. |
| `scripts/task007f/profile1/recorder.py` | New stdlib-only bounded recorder. |
| `scripts/task007f/profile1/run_phase_a.py` | New research-only parser/composition/export entry point. Defining its worker is G1; executing it is G2. |
| `tests/unit/test_profile1_recorder.py` | New focused recorder/failure checks, authored only after G1 approval; no collection/execution until G2. |
| `tests/integration/test_profile1_parity.py` | New controlled parity/observer harness; execution is G2 only. |

Construction can be observed at existing composition call sites. Avoid changes to `problem.py`,
`cost.py`, `warm_start.py`, `prediction.py`, `packet.py`, `DiagnosticTiming`, frozen worker factories,
threading configuration, existing tests, fixtures and dependencies. No recorder package initializer
is required; existing namespace-module conventions suffice. Documentation/handoff updates stay
within the manifest's separate documentation allowlist.

Candidate code lives only on the research branch; the immutable frozen branch/tag and source
snapshot never move. Existing formulas, source packet semantics, solver settings, warm-start
mechanics, RK4 stages and controller/tracker results must remain unchanged. A future ON return
expression may bind the original tuple to close its observation span; it must return that same tuple,
not regenerate the numerical work. B1's OFF branch preserves original expressions where possible.

## 4. Finalized boundaries, clocks and accounting

The API copies the exact 22 recurring span IDs and parent graph from the accepted contract. Their
source anchors remain byte/hash-identical. Repeated preview children have distinct occurrences;
gain Jacobians are one block, not extra per-interval microspans. Construction has a separate eight-node
catalog; gated startup has its own call population. Clock calibration has three test-only auxiliary
IDs under `clock_probe` and never contributes preparation samples or simulated seconds.

Use `perf_counter_ns` then `process_time_ns` at each entry and exit. Retain each raw pair, clock
domain, implementation/resolution and missing reason. CPU includes worker native threads and may
exceed wall; do not clamp. Only complete disjoint immediate children are subtracted from a parent.
Partial coverage yields unknown exclusive cost, not a fabricated zero. Preserve signed residuals.
An empirical reconciliation allowance remains a review prerequisite; this request invents none.

Preserve legacy timer meanings/endpoints, including planner totals at planner lines 84–85, successful
and exceptional `solve_time` branches, and packet duration metadata. Added observation inside a
legacy interval naturally changes its measured value; it does not change its meaning. In particular,
the new backend-only child is not a renamed historical solver-adapter timer.

`prepare_full` starts immediately before the existing caller invokes `prepare` and ends after the
returned tuple/exception reaches that caller. It includes final packet replacement/return assembly.
The dispatch envelope begins before the release's prefix/capture block, **after** original estimator
calculation, and ends after prepare/record append, before the unchanged delay selection. Its prologue
exclusion is explicit. The current release callback cannot alone bracket its capture argument.
The final endpoint publication/return tail is explicitly unmeasured; independent observer assessment
must address it. An observer cannot measure its own last publication for free.

The scheduler continues to consume its original `planner_total_time` field or original controlled
replay interface. No new timer affects the estimator, pending queue, packet activation, fixed/variable
deadline or application. After measurement, report legacy duration, full-call/envelope duration,
paired observer-cost estimates and clearly named hypothetical measured readiness differences.
Counterfactual host-duration mapping is never actual accepted authority, including under injected
timing. A later full-boundary availability policy remains a separate Phase B decision.

## 5. Exhaustive comparison policy

The parity record defines the G2 comparison-bundle roots and **98 individually expanded duration
leaf selectors**. The only wildcard is an array-index segment. Exact key sets, ordering, types,
shapes/dtypes and finite values are the default for every other leaf; no statistics/diagnostics/
authority object is omitted. Binary numerical arrays are compared bytewise where available.

Fourteen IPOPT timing keys were individually identified by read-only inspection of two retained
Task007C-R snapshot files and are individually listed. Their hashes and limited purpose are recorded.
Call counts, iterations/iteration histories, solver status, objective and feasibility stay exact.
An unknown backend timing key is a stop/review condition, not a new wildcard. These old snapshots
are not accepted-A contexts or a substitute for missing Phase B warm state; no replay was performed.

Original packet values, prediction/preview, X/U/slacks, terminal matrices, gains, physical and
predictor RK4 traces and source/request identities remain strict. Causal release, target, completion,
acceptance, expiry, application and actual physical latency timestamps are never timing exclusions
under controlled replay. Build-specific source hashes are checked against their reviewed manifests;
the deliberately changed B1 source cannot be required to equal B0 bytes. B1/B2 source bytes must match.

One original host-derived field requires an explicit predicate rule:
`computational_deadline_exceeded` must equal **that build's** `total_time > tracker_dt`, and any
cross-build difference is reported. It is not physical `codriver_misses` or a permission/deadline
waiver. The existing test helper already separates this host-cost telemetry. Treating it as a strict
cross-build boolean would conflict with permitting genuine wall-cost differences. Actual due/miss,
readiness, acceptance and application traces remain exact for controlled cases.

Only the newly introduced `/instrumentation_sidecar` namespace is ON-only and outside legacy-schema
equivalence; its own identity/tree/clock/outcome validity is checked independently. Legacy fields
cannot migrate under that namespace. Test-only in-memory numerical spies are identical across
controlled builds and separated from the observer-cost workers, where dense spies are disabled.
They do not create a persistent warm-history capture feature.

## 6. Exceptions, incomplete data and safe reporting

Numerical outcome and observer validity are independent axes. A block can complete and return a
failed solver result; a preparation can return a packet without gaining accepted authority. Preserve
the exact original returned tuple/status or escaping exception. Ordinary recorder errors must not
leak into the existing planner's ValueError or adapter's RuntimeError catch and masquerade as a
numerical failure. An exception-closing hook cannot mask the original exception or traceback.

Prediction, backend, optimizer validation, gain and packet failures close only reached spans; remaining
spans are not reached, not zero. Waiting/late/rejected handoffs retain original chronology. Full host
preparation CPU is charged even if its physical completion remains pending when the run ends. A host
call interrupted before return has only partial cost/lower-bound evidence.

Overflow, wrong nesting, clock anomalies and serialization failure latch an observer fault; they
never silently drop/overwrite records or request a fallback command. Finish active original numerical
work if possible, preserve its outcome, then stop at the existing end-of-release reporting boundary
before a new physics/application/completion event or preparation. Startup observer failure is reported
before startup acceptance/prepositioning. Such deliberate recorder-fault fixtures compare the original
preparation result and exact validated physical prefix; they are unsuccessful interrupted runs, not
full-trace parity successes.

After measurement, preserve original raw output separately before observer export. Serialize into a
fresh owned directory with exclusive partial-file creation; publish a fresh complete artifact only
after flush/fsync. Keep partial bytes and report missing evidence on failure. Catastrophic memory or
process failure can defeat even an emergency slot; retain process exit/log and unknown coverage
honestly. No universal zero-cost/nonthrowing recorder or guaranteed persistence is assumed.

## 7. Proposed G2 fixtures and independent resource request

G1 writes approved code/tests and returns for review using static syntax/reference checks only.
G2 requires an explicit separate instruction bound to the reviewed implementation SHA, source diff,
fixture/replay identities and field policy. Its proposed bounded sample allocation is:

| Population | Exact proposal |
|---|---|
| Controlled real A | C0: 0.24 s, zero planner/codriver delay. C1: 0.24 s, injected 60 ms planner / 25 ms codriver. Each B0/B1/B2 once: six fresh workers. Frozen gamma2 state/math; actual new test startup generates warm state. |
| Synthetic chronology | S0–S4 reuse existing StraightPlanner/plant fixtures for busy planner, codriver misses, spike, expected exhaustion and pending tail. Five cases × three builds: fifteen workers. These are chronology fixtures, not NMPC performance evidence. |
| Independent observer | C1 in six fixed complete build-order permutations: eighteen additional workers, six per build. Dense numerical spies disabled. Cold/recurring costs separate; retain negative paired deltas and all failures. |
| Measured readiness | M0: 0.24 s, legacy measured planner / imposed 5 ms codriver, once per build: three workers. Descriptive invariants/outcomes, no wall or full-trace equality claim. |
| Integrity/regression | One fresh worker for twenty enumerated integrity cases and five exact existing regression node IDs, including fixed-deadline and old-command provenance. |
| Clock-only | One stdlib-only worker: 1,000 empty single spans and 1,000 empty nested pairs; no backend imports or dense-BLAS benchmark. |

Total proposal: **44 fresh sequential workers**, including 27 real-fixture workers, 15 synthetic
chronology workers, one integrity worker and one clock worker. The entry contract fixes all timing
values, context provenance, ordering and proposed node IDs. Existing tests/fixtures are not edited.
New tests may adapt an existing helper's duration argument locally. No favorable-outcome reruns.

Request an independent **10-minute G2 allocation**, 1 GiB worker peak RSS, 1 GiB reserved output and
1 GiB remaining free floor plus remaining output headroom (initially at least 2 GiB). Proposed
timeouts: 30 s per data/clock worker, 120 s for the protocol worker, within the shared cap. These are
allocation ceilings, not estimated runtimes or current authorization. Inspect owner guards and
actual processes, configure supported SINGLE before numerical imports, and retain actual backend/
thread observations. No overlapping tests, rendering, analysis or benchmarks. If a cap/guard fails,
stop starting workers, preserve the partial campaign and return for review without replacement.

If empirical clock allowance is still unresolved at G2 approval, authorize **only the one clock
worker**, then stop for review before the other 43 workers. A clock result never authorizes numerical
continuation. No observer-negligibility threshold is invented; report raw costs and seek review.
This proposal does not borrow the separate Phase B 20-minute campaign allocation.

## 8. Preserved restrictions and review outcome

Phase B remains blocked by missing full historical pre-call X/U/slack arrays/reset lineage and
unfrozen diagnostic IDs. No aggregate-slack reconstruction or active-packet substitution is allowed.
A later proposal may request reviewed fresh capture or a labelled cold-start diagnostic amendment;
neither is in this G1 allowlist. No new warm capture, worker campaign or simulation occurs now.

Frozen Performance branch/tag/manifest, main, historical evidence and independent Safety S1 are
unchanged. The live Safety head observed during preflight is
`9f0cbe0f0f48a1e2a62716957bbab79fe2b5b1b4`; it is independent documentation work. Feasible proposal,
accepted trajectory authority and application permission remain distinct; successful solves or
simulated applications never create S1 grants. No emergency recovery or physical safety is inferred.

Remaining review decisions are approval of this exact G1 API/diff/failure-stop/predicate policy,
later review of the G1 implementation and proposed G2 allocation, and a justified empirical clock
allowance. Observer costs remain measurements for review, without an invented threshold. Phase B
context and readiness mapping remain separate prerequisites.

This delivery performs documentation/structure/hash/reference/preservation checks only. Original
F0/Phase A records and previous handoff history remain intact. Commit/push is scoped to documentation
on `research/efficiency`; no second worktree on that occupied branch and no merge into main.
**Stop at WORK_COMPLETE_PENDING_REVIEW. No G1 implementation or G2 execution is authorized.**
