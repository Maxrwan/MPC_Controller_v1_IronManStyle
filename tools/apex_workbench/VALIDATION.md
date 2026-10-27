# Workbench V0.1 focused WORK validation

**WORK_COMPLETE_PENDING_REVIEW — 27 October 2026.** Base revision
`37b3f19a5d58f9a76cfd9dee5cb5bf4352edc980`; isolated branch
`codex/apex-workbench-v0-1`. The containing delivery commit binds the tested source hashes in
[validation_record.json](validation_record.json). Exact delivery SHA/URL is supplied after push.
These are focused WORK demonstrations, not formal verification or acceptance of a new scientific profile.

## Results

- Initial Workbench selection: **16 passed**. Dynamic CLI and LQR function parity produced
  byte-identical states/summary files; LQR controls were byte-identical too. No measured timing
  field is compared. Configuration validation, failure/log retention, timeout, cancellation,
  lock rejection, exclusive output, append-only notes and CSV-driven plotting passed.
- Applicable existing unit selection: **127 passed** (`test_config.py`, `test_dynamic_bicycle.py`,
  `test_baseline.py`, `test_runner.py`). No canonical scientific source or test was modified.
- After the final UI metadata caption, the real-run/malformed-input UI test passed again:
  **1 passed**. The inherited worker-lifetime lock/cancellation test and new guard/disk-floor
  test then passed: **2 passed**. There are **17 distinct current Workbench tests**, all covered
  by these logs; the unchanged scientific unit selection was not repeated.
- Ruff check/format and Git whitespace checks passed. New-document relative links and the final
  source/preservation audit are checked separately in the delivery evidence.

All test invocations used the separate Workbench Python 3.12.14 environment with current core
versions retained: NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.6, matplotlib 3.11.2, CasADi 3.8.1.
Tool versions: Streamlit 1.66.1, Plotly 6.9.0, psutil 7.2.2, threadpoolctl 3.7.0.
The core `.venv` and core dependency manifest were not changed.

The shared test-command prefix, run from the repository root, was:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))'
```

Append `-q tools/apex_workbench/tests` for the tool selection. The initial selection also used
`--durations=5`; the existing-unit selection used the four explicit files above and the same
option. Final affected tests use explicit node IDs recorded in the JSON and fresh `--basetemp`
directories. Successful logs and retained failure/timeout fixtures are under
`results/apex_workbench_delivery_20261027/` (ignored local evidence). Tests used
[Streamlit AppTest](https://docs.streamlit.io/develop/concepts/app-testing/get-started)
and real scientific worker subprocesses; they did not mock the numerical experiment.

## Live browser demonstration

The loopback server launched successfully with the README command (headless mode avoids the
first-launch email prompt). Chrome/CUA form submissions produced three fresh completed runs:

| Run | Adapter | Effective change | Outcome |
|---|---|---|---|
| `20261027T162115750326Z_c5c6a9c8ab24` | Original dynamic demo | duration 10 s, dt 0.005 s | Completed; actual XY/state/control plots |
| `20261027T162143537820Z_2dc88d2a1ec3` | Original LQR/PI | circle, speed 2 m/s, duration 12 s, ey 0.1 m | Completed; 0 sampled boundary violations, 0 model failures |
| `20261027T162319201355Z_8cda800d3492` | Original LQR/PI | circle, speed 2 m/s, duration 1 s, ey 0 m | Completed; short-run settled metrics remain null |

The disturbed run's learner notes survived reload/reselection. Observation/explanation entries
are explicitly labeled UI persistence checks, not a supplied engineering explanation. The two
LQR runs overlay their actual CSV samples in Compare runs. Screenshots are retained locally as
`workbench.jpg`, `workbench-result.jpg` and `comparison.jpg` in the delivery evidence directory.
No full lap completion or real vehicle safety/performance is inferred from these demonstrations.
The owned preview server is stopped after checks; relaunch it with the README command.

Native control was set through the existing macOS Accelerate SINGLE API before numerical imports.
Live worker peak sampled process thread counts were 1 (dynamic) and 2 (LQR); loaded pool inspection
returned no recognized pools. This is retained descriptive evidence, not a claim of parallel
numerical execution, exact peak resource bounds, or timing qualification.

## Requested acceptance demonstrations

| Criterion | Evidence |
|---|---|
| Local launch and real UI execution | Live server + three CUA submissions; AppTest real worker |
| Invalid/malformed input rejected | Strict allowlist/finite/bounds/tick tests; negative duration in UI |
| Original-entry-point consistency | Byte-identical CSV/JSON parity for both adapters |
| Actual data behind graphs | CSV-value assertions + live XY/state/control inspection |
| Failed runs retain error/logs | Invalid-worker fixture; timeout fixture; final status/artifact manifests |
| Historical evidence preserved | All original tracked hashes outside authorized docs match; 11,677 original result files retain size/mtime |
| New run cannot overwrite old | Exclusive directory and original-output refusal tests; unique supervised runs |
| Unsupported inputs not exposed | Conditional UI + unknown-key rejection + capability matrix |
| Canonical models/controllers/profiles unchanged | Before/after original tracked-file hash audit |

Historical ignored results were checked by size/mtime; this is not a full 9.4 GiB content rehash
or backup claim. Existing frozen refs were only read. No existing experiment result was overwritten.

## Deferred checks

Full integration/regression, formal verification of the reviewed delivery SHA, NMPC or asynchronous
execution, latency benchmarks, VIS ingestion, unseen-track generalization, physical parameter
identification and hardware safety remain unexecuted. No new controller, tire law, vehicle equation,
optimization objective, solver, fallback policy or scientific tuning was implemented.

Engineering Review should inspect adapter scope, execution supervision, evidence and UX, then
explicitly authorize any formal verification or later adapter work. Stop at the current WORK boundary.
