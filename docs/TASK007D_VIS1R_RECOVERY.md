# VIS-1R — bounded prerequisite recovery

**Stage/status: WORK_COMPLETE_PENDING_REVIEW.** Exactly one fresh 2 s parity_A recovery and,
after its complete pipeline passed, one fresh 2 s parity_C70 ran successfully. The six long
VIS-1 runs, VIS-2/3/4 and Efficiency were not executed. This is prerequisite recovery, not a
full-lap scientific result or architecture selection.

**Exact tested scientific/export revision:** `c6990572045e61ee443dc715de9e8c44396e5b41`, clean
`main` during both workers. No executable, test, configuration, fixture, controller, scheduler,
predictor, solver, tire or integrator changes were made in VIS-1R. The containing delivery commit
adds this report, compact evidence and a handoff prepend; its SHA/URL are reported after push.
See [verification/source hashes](task007d/vis/vis1r/verification.json).

## Authorization, original failure and applicability

Engineering Review explicitly authorized one additional A execution because the previous A
physical trace passed but its required observer/export evidence was lost. The NumPy serialization
correction already committed in c699057 was inspected and hash-checked against its recorded
delivery source. Fresh tests exercise actual detached release snapshots, NumPy arrays/scalars,
nonfinite rejection, immutability and exclusive file creation. No new fix or relaxed assertion
was needed during recovery.

The delivery diff check flagged CRLF endings in the three-line compact CSV. They were normalized
to LF with parsed rows verified identical; no raw/export evidence changed. This documentation-only
correction is retained as a followup commit, with no history rewrite or experiment rerun.

The original failed worker, raw/segments, traceback and exact parity evidence remain unchanged at
`results/task007d/vis/vis1_execution/parity_A/`. The earlier pre-simulation JSON tuple/list
comparison failure also remains intact. The [original VIS-1 report](TASK007D_VIS1_RESULTS.md)
is preserved as historical evidence, including its blocked status.

Fresh root: `results/task007d/vis/vis1r_c699057/`. The
[authorization/predecessor record](task007d/vis/vis1r/authorization.json) identifies the failed
attempt by hashes and permits only A then C70, one execution each. The original 8,001-entry
timing matrix was copied byte-for-byte; its historical source metadata is not relabeled as new.
Current source-bound gates are separately recorded in
[prerequisites](task007d/vis/vis1r/prerequisites.json) and
[contract validation](task007d/vis/vis1r/export_validation.json).

The approved N8/gamma2 controller and synthetic_grand_prix_v1 Planning fixture remain frozen.
Readiness uses the existing 35/55/45/25 ms imposed planner pattern and 5 ms imposed codriver delay;
A has variable availability and C70 has its existing fixed 70 ms target, both predictor A.
No additional timing history, configuration or optimization was introduced.

## Prerequisite tests and resource checks

Fresh affected selection: `tests/unit/test_vis_exports.py` — **30 passed, 0 failed/errors/skipped,
15.41 s**. It covers serialization, isolated chronology/authority, terminal RK4 coverage, lap
counting, missing/empty exports, source provenance and observer noninterference. Scoped Ruff
lint and format both pass on the unchanged 13 VIS Python files.

**384 unaffected prerequisite cases are reused**, not newly run. Their prior 410-case JUnit/log,
source inventory and exact node identities are retained in the prerequisite record. Initial
VIS source differences are confined to the already reviewed VIS adapter/launcher and its test;
all other source/tests, vehicle/Planning configuration and dependency lock are unchanged. All
originally tracked files except the historical handoff/decision documentation match their initial
hashes. Python, OS and numerical package versions also match. Thus the current applicable
prerequisite set is 384 inherited plus 30 fresh = **414 distinct cases**. Complete regression
remains deferred to separately authorized VIS-4; it was not repeated.

Environment: macOS 26.5.1 arm64, Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1, CasADi 3.8.1,
psutil 7.2.2, threadpoolctl 3.7.0, pytest 9.1.1. Existing measurement guards were clear; process
inspection found ordinary desktop activity and no competing measurement/test/controller workload.
Fresh SINGLE workers ran sequentially, with no analysis/test/rendering concurrent with simulation.
About 6.7 GiB free space exceeded the unchanged 1 GiB floor plus 1.5 GiB headroom requirement.
The existing launcher checked source, prerequisite, contract, predecessor, disk and active guards.

One local audit setup assertion initially omitted the known VIS launcher from the list of files
changed since the first VIS test run. Its reviewed followup provenance resolved this inventory
oversight before any gate was written or worker launched. No runtime guard, source or assertion
in the repository was changed. This was not a new scientific/test failure.

## Complete pipeline acceptance

Both worker exits are zero. Each produced raw.json, segments.json, release_contexts.json,
input_configuration.json, applicability.json, parity.json, summary.json, analysis.json and the
complete scientific package. Source hashes remained unchanged through each worker.

| Required evidence | Recovered A | C70 |
|---|---:|---:|
| Physical duration (s) | 1.9999999999999787 | 1.9999999999999787 |
| Historical C3 exact comparison groups | 19 / 19 | 19 / 19 |
| Release-context forecast → NMPC matches | 19 / 19 | 19 / 19 |
| Independent saved-JSON forecast matches | 19 / 19 | 19 / 19 |
| Observed process thread counts | [1] | [1] |
| Native states, including terminal endpoint | 401 | 401 |
| Recorded RK4 segments / applied controls | 400 / 200 | 400 / 200 |
| Runtime cycles / accepted handoffs | 19 / 19 | 19 / 19 |
| Scientific / chronology gate issues | 0 / 0 | 0 / 0 |
| apex-run/0.1.0 adapter validation | PASS | PASS |

[A acceptance](task007d/vis/vis1r/parity_A_acceptance.json) and
[C70 acceptance](task007d/vis/vis1r/parity_C70_acceptance.json) include required-file hashes,
thread observations, complete parity maps and export validation. C3 applicability still has
only the two previously reviewed urgent-bookkeeping source differences; no urgent event occurs
in these histories. Physical states, controls, chronology, packet contents, NMPC inputs and RK4
segments match exactly; host-duration telemetry is excluded as documented by the existing audit.

**Reporting correction:** the prior VIS-1 prose/final response said 20 exact comparisons. The
actual retained parity JSON and current comparator contain **19 groups**, all true. This count
correction changes no comparison, tolerance or scientific result. Original evidence is preserved.

The separate [serialized-context audit](task007d/vis/vis1r/serialized_forecast_audit.json)
deserializes saved packet/vehicle/tracker/release values and calls predictor A with private
buffer/tracker instances. It loads actual plan results only afterward for comparison. All
38 predicted state/preceding-control pairs are exactly equal; release states/times/durations
also match. No solver execution, physical simulation or future input is used for those forecasts.

Native policy evidence includes successful Accelerate SINGLE configuration and actual process
thread-count observations before/after preparation, always one. threadpoolctl returns no supported
pool inventory for this Accelerate environment; the API does not expose an exact continuously
sampled active BLAS count. These bounded observations are not embedded real-time certification.

## Physical validity, chronology and timing

| Recorded short-run metric | A | C70 |
|---|---:|---:|
| Minimum center clearance (m) | 0.4373138184 | 0.4373138184 |
| Maximum predicted slack (m) | 9.0915e-11 | 9.0915e-11 |
| Minimum active reserve (s) | 0.667 | 0.635 |
| Progress reached (m) | 12.5238266411 | 12.5251900617 |
| Boundary / solver failures | 0 / 0 | 0 / 0 |
| Rejected handoffs / planner busy misses | 0 / 0 | 0 / 0 |
| Codriver busy ticks | 0 | 0 |
| Fixed deadline misses | not applicable | 0 / 19 |
| Complete laps / seam crossings | 0 / 0 | 0 / 0 |

No model-domain, packet-authority, trajectory-exhaustion or unexpected-fallback gate fired.
Complete physical/coverage/timing diagnostics are in
[A analysis](task007d/vis/vis1r/parity_A_analysis.json),
[C70 analysis](task007d/vis/vis1r/parity_C70_analysis.json) and
[compact table](task007d/vis/vis1r/parity_summary.csv).
Center clearance is recorded synthetic center clearance, not swept-body safety.

The preparation durations in analysis/summary include descriptive host costs; simulated readiness
is imposed by the saved pattern. For example, a host duration longer than 70 ms does not create
a fixed miss in this replay. C70's zero misses here do not estimate measured deadline reliability.
Neither the small progress difference nor own-reference tracking differences establish a racing
performance gain. This assignment makes no A-versus-C70 full-lap interpretation.

## Export, hashes and preservation

Both scientific packages pass independent adapter revalidation, with 401 state rows, 400 segment
rows, 200 applied controls, 19 cycles, 457 events, zero boundary events (valid header), three
metric windows and all 15 data/fixture artifacts accounted for. Artifact SHA256, byte sizes and
CSV row counts are retained in the copied
[A manifest](task007d/vis/vis1r/parity_A_manifest.json) and
[C70 manifest](task007d/vis/vis1r/parity_C70_manifest.json).
[Run inventory](task007d/vis/vis1r/run_artifacts.json) hashes every saved raw/export/log file.

Scientific and export revisions are both c699057, with clean working trees during execution.
Native and reconstructed channels, partial event ordering, accepted packet authority versus
physical application and incomplete request-tail coverage retain the existing interface semantics.
The four prior representative packages also passed revalidation without byte changes. Workbench
ingestion and final interface acceptance remain a separate pending process.

[Preservation](task007d/vis/vis1r/preservation.json) verifies the original failed attempt and all
prior raw histories unchanged, and all existing tracked files unchanged except this task's handoff
prepend. No historical results were relabeled or overwritten. The short worker artifacts stay
under the fresh ignored root; only compact evidence/documentation is committed.

## Readiness and next decision

**Recommend ready for Engineering Review to resume the six-run VIS-1 campaign under its unchanged
protocol.** The short physical parity, complete capture/export and source-bound prerequisite
blockers are resolved. This recommendation is not execution authorization. All six long runs
remain unexecuted in VIS-1R; a new review instruction is needed to proceed. Long-run memory/export
cost, full-lap completion, sector performance and measured timing consequences remain untested.
No architecture promotion, Performance freeze, Efficiency, VIS-2/3/4 or UI work occurred.

## Reproduction

Do not overwrite the existing root or rerun the physical cases without new authorization. Exact
executed commands, from repository root after gates were established:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tests/unit/test_vis_exports.py --durations=5 \
--junitxml=results/task007d/vis/vis1r_c699057/focused.xml
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
--root results/task007d/vis/vis1r_c699057 --case parity_A
# A acceptance audit passed before the following command.
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
--root results/task007d/vis/vis1r_c699057 --case parity_C70
```

Worker logs and test log/XML remain under that root. The existing
`task007dvis.parity.compare` and `task007dvis.validation.validate` reproduce saved physical/export
checks without rerunning simulation. The serialized forecast audit uses
`packet_from_record`, `SymbolicBicycle(parameters, RACING_TIRE_PHYSICS)`, `ActuationPredictor`,
`TrajectoryBuffer` and `TrajectoryTracker` with the saved fields, exactly as in the worker's
offline loop; load scored plan outputs only after forecasts. No new timing experiment is required
to audit the compact evidence.
