# F-PROFILE-1 G1 implementation handoff

`WORK_COMPLETE_PENDING_REVIEW` — `CODE_CREATED_NOT_EXECUTED`, 26 October 2026.
Branch: `research/efficiency`. Authorized starting revision:
`83f360b2a96e8f6d9fe429d2cc2e5447da2f47c8`.
The human G1 code-creation assignment supersedes the historical authorization-preparation
records only for this bounded implementation. Their original statuses/bytes remain intact.
Exact decision date was not supplied; this is the recording date.

The delivery revision is the commit containing this handoff and the source hashes in
[g1_static_validation.json](g1_static_validation.json). Its exact SHA/URL is supplied in
the final delivery message, avoiding a self-referential metadata commit.

## Scope

Exactly ten runtime/test paths:

- `src/apex/control/trajectory/planner.py`
- `src/apex/control/mpc/controller.py`
- `src/apex/control/mpc/preview.py`
- `src/apex/optimization/solvers/ipopt.py`
- `src/apex/control/trajectory/tracker.py`
- `src/apex/simulation/asynchronous.py`
- `scripts/task007f/profile1/recorder.py`
- `scripts/task007f/profile1/run_phase_a.py`
- `tests/unit/test_profile1_recorder.py`
- `tests/integration/test_profile1_parity.py`

Documentation scope is this handoff, `g1_static_validation.json`,
`g1_source_projection_audit.md` and updates to `docs/CODEX_HANDOFF.md`,
`docs/DECISIONS.md` and `docs/PROJECT_ROADMAP.md`. No other runtime, existing test,
fixture, configuration, dependency, protected profile or scientific export is changed.

## Recorder and source hooks

The stdlib-only recorder is worker-local and scalar-only, with explicit `off`/
`profile1-v1` modes and the twelve accepted signatures. Numerical objects receive
optional injection and never import it. OFF uses the original numerical statements
without new spans, clock reads or capture containers; branch/attribute overhead still
requires B0/B1 measurement. It has no background writer or global production hooks.

Reserved slots retain both endpoints, worker/call/span/parent/occurrence identity,
wall-then-process-CPU integer nanoseconds, exit status and missing reasons. The exact
22 preparation IDs and eight construction IDs match the accepted contract; auxiliary
clock-only records have their own three IDs/population. All reviewed capacities remain
caps: 64 calls, 8192 spans, depth 8, 64 fault records, 128 identity bytes, 256 exception
bytes, 2048 status bytes and 16 MiB serialized sidecar. Post-run scalar outcome joins
reuse the 8192-record cap and explicitly mark overflow. These are not an RSS proof.

Reconciliation subtracts complete immediate children only and retains signed residuals.
Partial parents/children have unknown exclusive time. Missing phases distinguish
`not_reached` from observer-unavailable; missing roots/slots are invalid. No endpoint,
zero, parent repair or clock allowance is synthesized. The launcher requires a reviewed
nonnegative wall/CPU allowance with bounded provenance before any numerical ON worker.
Its input hash/values and sidecar reconciliation remain visible. No ns tolerance or
negligible-overhead threshold was selected here.

Legacy timer start/end expressions and the scheduler's
`c.delay(plan_id, event["planner_total_time"])` consumer are preserved. Full preparation
and dispatch envelopes remain observations. Dispatch excludes the estimator/release
prologue and final endpoint publication/return tail. Hypothetical full/envelope
completion is computed only after the run, never fed to queues, estimator, packets,
acceptance, command application or Safety. It is not end-to-end latency.

## Launcher and failure boundaries

The new research launcher is independent of production entry points. It rejects unknown
modes before numerical imports and keeps OFF free of recorder imports. A fresh child
checks exact reviewed HEAD, clean source and accepted manifest, and uses the existing
Mac Accelerate SINGLE bootstrap before numerical construction. C0/C1/M0 select the
reviewed gamma2 fixture/initial state and 0.24 s conditions; no broad campaign runs
implicitly. There is no source tuning, extra solve/model/Jacobian/packet validation,
warm reconstruction or Phase B capture.

A separately selected `clock_probe` child uses stdlib only, 1000 disjoint empty spans
and 1000 empty parent/child pairs, retains every record plus counts/clock metadata,
and deliberately cannot approve its own allowance or continue into numerical work.
The clock branch is also unexecuted and requires separate authorization.

The parent owns a fresh output directory/guard, checks known measurement guards/process
labels and disk headroom, samples RSS/threads/process CPU outside kernels, and stops on
30 s/1 GiB RSS/1 GiB output/1 GiB remaining-disk ceilings. It does not retry. Actual
backend/thread observations are retained; environment values alone are not proof of
SINGLE behavior. Opaque external workloads and unsampled resource peaks still require
human/environment review. This Mac-specific bootstrap is not a portable backend policy.

Ordinary observation errors latch invalidity without entering original numerical
ValueError/RuntimeError handlers. Already reserved endpoints may close after fault;
new capture/calls stop. The original preparation tuple/status or escaping exception is
preserved. Startup faults stop before acceptance/prepositioning; recurring faults stop
at the existing end-of-release reporting boundary before another physical event. The
existing `stop_reason` reports `instrumentation_stop`. This simulation termination does
not establish physical stopping and grants no fallback, cancellation, zero command,
emergency brake or S1 permission. The borrowed original tuple is retained separately
when observation prevents startup publication. Escaping original exceptions keep their
type/traceback; post-run export failures do not replace them.

Original raw output is written first; sidecars are frozen, written exclusively to a
`.partial`, flushed/fsynced and published via a non-overwriting hard link. Failures keep
partial evidence and a separate export failure where possible. Catastrophic OOM,
process kill, interruption or storage failure can prevent persistence: missing tails
remain incomplete, never reconstructed as complete. A fully returned host preparation
retains full CPU even when its physical completion remains pending/censored.

## Authored verification inventory — all unexecuted

There are 27 statically named test functions, with parameterized cases. This is an AST
inventory, not collection or a pass count. Exact node names are in the static record.

| Case | Authored coverage |
|---|---|
| U01 | OFF allocation/clock factory sentinel; default/unsupported launcher import sentinel |
| U02 | Raw wall-before-CPU order, integer endpoints |
| U03 | Accepted graph, parent nesting, repeated preview occurrences |
| U04 | Borrowed numerical data unchanged; immutable scalar sidecar |
| U05 | Original prediction exception identity and traceback |
| U06 | Original backend RuntimeError result/status |
| U07 | Deliberately invalid optimizer result and original warm reset |
| U08 | Gain failure; no packet promotion |
| U09 | Original packet validation rejects an invalid gain schedule |
| U10 | Complete returned-None root versus partial child and not-reached phases |
| U11 | Missing/wrong/foreign-thread/nesting tokens |
| U12 | Decreasing, noninteger, Boolean and out-of-range clocks |
| U13 | Raised observer clock, retained half-pair and original outcome |
| U14 | Span cap; reserved end retained |
| U15 | Call/depth caps, sticky first fault and diagnostic overflow |
| U16 | Exception/status byte bounds |
| U17 | Export OSError; original raw bytes preserved |
| U18 | Serialized cap, partial retention, no overwrite |
| U19 | Interrupt/open call; no invented endpoint, retained lower bound |
| U20 | Physically pending completion censored; full host work retained |

Additional cases cover signed negative residuals, partial-child accounting, auxiliary
population separation, missing roots/unresolved allowance, bounded outcome joins,
observer-fault tuple preservation/authority stop, strict new-key rejection and per-build
host deadline predicate validation with exposed cross-build flag differences.

The future controlled harness supports B0 (pristine E4 source), B1 (reviewed G1 OFF),
B2 (same G1 bytes ON); C0/C1 plus S0-S4. S0-S4 reuse the existing StraightPlanner and
synthetic dynamic/straight fixtures solely for chronology. They are not an NMPC timing
profile; S3 is the declared negative exhaustion oracle. Real workers use fresh actual
startup/warm state. Test-only instance spies observe actual calls once, including
pre/post X/U/slack, request/bounds, SolverResult/all statistics, diagnostics/prediction,
all packet dataclass fields including valid_from, gains, physical RK4 stages and
predictor map endpoints/stage domains. They add no numerical evaluation.

Test snapshots use bounded slots (64 call/8192 trace rows) and a 16 MiB private IPC
message cap; they stay in RAM and are discarded after comparisons. No dense optimizer
snapshot is persisted as a warm-history archive. Original legacy raw results and scalar
reports may be retained. These bounds and all protocol code remain unexecuted.

The comparator preserves exact key sets/order, types, shapes/dtypes, array bytes and
non-excluded leaves. It reads the unchanged 98 explicit duration selectors and fourteen
named IPOPT timing keys. A star matches an array index only; no statistics dictionary is
excluded. The host-derived computational_deadline_exceeded is checked independently
against its own total_time > tracker_dt, and differences are reported. Actual deadlines,
readiness, authority, misses, packets and RK4 remain exact under controlled timing.

M0 and the six declared C1 build-order blocks have separate descriptive reporting
support with dense spies disabled. Signed run-level wall/CPU deltas are retained,
startup and recurring populations stay separate, and no p99, cost threshold or
subtractive correction is claimed. No automatic 44-worker orchestrator was added.

The five existing regression node IDs in `g1_verification_entry_gates.json` were
resolved by AST only and remain unchanged/unexecuted. A future protocol worker must
select U01-U20/support plus exactly those nodes using the existing pre-import SINGLE
bootstrap; do not run the entire integration file in that protocol worker, since its
controlled/measured cases launch their own separately counted workers. The reviewed
44-worker/10-minute proposal is not execution authority. Whole-campaign sequencing,
allocation enforcement and the exact selection remain a separate G2 review decision.

## Static evidence and preservation

[Static record](g1_static_validation.json) binds source hashes, twelve API signatures,
nineteen accepted anchor hashes/function lines, span catalogs/capacities, exact parity
contract hash, test names and five existing regression references. All ten files pass
non-executing AST parse, Ruff check and Ruff formatting checks. Git whitespace and the
16-path diff allowlist pass. No project module, recorder, launcher or test was imported;
no pytest collection, backend construction or code exercise was performed.

[Source projection audit](g1_source_projection_audit.md) reconstructs the original full
module AST for OFF and ON in all six modified modules. ON normalization removes
observation wrappers/return bindings and reverses the reviewed solver constructor
hoist; new fault stops are audited separately. This is source noninterference design
evidence only. It does not prove actual numerical equality, exception containment,
clock accounting, memory sufficiency, physical chronology or latency behavior.

Of 850 original tracked files, only the six allowlisted source files and three shared
documents change; all other original hashes match. Twenty-one retained Efficiency
documents match their original hashes. Metadata (size and mtime_ns) for all 11,646
results files match; this is not a full raw content rehash or backup. No experiment
artifacts were created by G1.

Main and release/performance-synthetic-v1 remain E4
`48adbdf64d492592d15e23c917aca71fa58aa8a5`; annotated tag object
`76d9eaa65af02efb0263916adc75d5247a0e778f` still peels to E4. Original manifest SHA256
`5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf` is unchanged.
GitHub branch/tag freeze rulesets 25418055/25418590 remain active with no bypass actors.
No main merge, shared-history rewrite or frozen-ref update occurs.

The existing Efficiency checkout already owns research/efficiency; reusing it avoids
attaching the branch to a second worktree. CT-1 advanced independently from the initial
snapshot to local/remote `3898704102e7570bcaff9b1654b7b345db1f9b6f` by resumption.
Safety local remains `fa4615ac11a1cf79c14d12eedb9360e33291c182`, while its remote was
observed at `6392092d68c1e2dd75120fbd87c32714e530e44e`. These concurrent workstreams
were neither edited nor synchronized by this task. Final remote visibility is reported
with the delivery SHA after push.

## Unresolved gates and exact limitations

No known out-of-allowlist implementation blocker remains from static inspection.
All behavioral/numerical claims remain unverified, including strict parity, real clock
order/resolution/skew, fault/exception preservation, censoring joins, native-thread
behavior, sidecar export on the host, peak memory and observer costs. Test bodies and
future launch paths require Secondary review on the exact delivery commit; static
success is not formal verification or acceptance.

Primary must separately approve the exact G2 fixture/order/resources/selection and a
justified clock allowance. If unresolved, only a separately authorized stdlib clock
worker may run, followed by review; no automatic continuation to the other 43 workers.
The parent enforces individual-worker limits, not a whole-campaign ten-minute budget.
Phase B context IDs/full historical warm-state/reset lineage and any full-boundary
readiness policy remain separate unresolved work. No tuning, C++ port or native-solver
research, Safety integration, Phase B or automatic follow-on task is authorized.

**NO NUMERICAL TESTS, PROFILING OR BENCHMARKS EXECUTED**.
Stop for Secondary APEX Engineering Review and a separate Primary G2 decision.
