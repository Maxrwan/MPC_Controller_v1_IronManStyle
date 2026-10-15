# VIS-1L reproduction and retained evidence

**Scientific stop: no further worker launch authorized by this report.** Reproduce analysis
from saved histories; do not rerun the failed C70, either successful worker, or the two remaining
cases without Engineering Review. See [results](TASK007D_VIS1L_RESULTS.md).

## Exact revisions and source boundary

- Scientific worker Git revision: `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae`.
- Frozen executable: `c6990572045e61ee443dc715de9e8c44396e5b41`; delivery descendant is docs-only.
- Accepted predecessor root: `results/task007d/vis/vis1r_c699057/`.
- New offline report source: `scripts/task007dvis/long_report.py`, `long_figures.py` and
  `tests/unit/test_vis_long_report.py` in the containing delivery commit. None existed during
  the scientific runs; no existing executable file was modified.
- [Preflight](task007d/vis/vis1l/evidence/vis1l_preflight.json) binds all 294 prior sources/tests,
  environment, budget and inherited gates. Each case's `evidence/<case>/input_configuration.json`
  preserves the full configuration and pre-run source inventory. Successful summaries retain
  fixture/vehicle hashes and native observations. Original hashes and artifact identities are
  in [provenance](task007d/vis/vis1l/provenance.json) and
  [verification](task007d/vis/vis1l/verification.json).

## Historical commands already executed

The existing strict launcher ran, in this exact order:

```sh
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case controlled_A
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case controlled_C70
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case measured_A_1
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case measured_C70_1
```

These are provenance, not instructions to execute them again. Complete acceptance gates were
checked before each subsequent worker. Exit codes are 0,0,0,1; campaign stopped immediately
after the fourth. `measured_C70_2` and `measured_A_2` remain absent. The launcher created fresh
SINGLE workers with the unchanged source/predecessor/disk/process guards. No guard was bypassed.

Each observed case retains raw.json, segments.json, release_contexts.json, input_configuration.json,
analysis.json, exit.json and worker.log. The first three also retain summary.json and valid
scientific packages. The fourth has a partial scientific directory: no manifest, packets/planning
completion or final summary. Do not create substitutes or silently finish it in place.

## Offline report reproduction

After checking there is no isolated measurement, choose a **new** output directory:

```sh
XDG_CACHE_HOME=/tmp/apex-vis1l-cache MPLCONFIGDIR=/tmp/apex-vis1l-mpl \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_module("task007dvis.long_report", run_name="__main__")' \
  --source results/task007d/vis/vis1r_c699057 \
  --output results/task007d/vis/vis1r_c699057/new_offline_review
```

The tool refuses an existing output directory, never launches a worker and never writes to case
folders. It includes a failed worker only when raw/native state CSV identity and its actual
terminal RK4 endpoint pass. It does not mark the incomplete package valid. Missing runtime
observations remain null. All common windows are bounded by both observed histories.

Outputs: `summary.json`, `comparison.json`, `provenance.json`, `lap_sector_metrics.csv`,
`common_coverage_metrics.csv`, `cycles.csv`, `misses.csv`, eight PNG figures and artifact hashes.
The seven numerical files reproduced byte-for-byte in a fresh ignored output. A figure-only
axis-limit adjustment improved the censored lap annotation; no numerical results changed.
Plots read saved native state exports; underlying full precision remains in each raw scientific
state CSV plus raw/segments, and the compact metric/cycle tables are committed. No plot
interpolation contributes to validity or extrema. A Matplotlib font-cache warning on the first
render was nonfatal; all eight images were reviewed.

`steering_limits.json` is the native whole-record maximum absolute `states.csv:delta` divided
by the unchanged 0.4 rad bound, with physical end time attached. It can be recomputed directly
without a simulation. Whole-record measured A and C70 cover unequal intervals; use common-window
tables for comparisons, not their unmatched totals. Crossing times have original RK4 brackets.

## Focused tests, known defect and deferred checks

After guard/process checks, executed:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
  -q tests/unit/test_vis_long_report.py tests/unit/test_vis_exports.py --durations=10 \
  --junitxml=results/task007d/vis/vis1r_c699057/vis1l_focused.xml \
  > results/task007d/vis/vis1r_c699057/vis1l_focused.log 2>&1
```

This returned 40 passed / 1 new-test setup failure. After correcting only the synthetic test
column container, reran `tests/unit/test_vis_long_report.py` to fresh
`vis1l_focused_recheck.log/.xml`: 11 passed. All 30 old export tests passed in the initial run;
there was no reason to repeat them. Both logs/XML are committed under evidence. Final result:
41 unique focused passes, original failure preserved. No assertions/tolerances were relaxed.

The known nested-NumPy-boolean export defect is explicitly reproduced by
`test_retained_nested_numpy_bool_export_defect_is_reproducible`; its expected exception is not
a successful export gate. Existing runtime/export code remains frozen pending review.

```sh
.venv/bin/ruff check scripts/task007dvis/long_report.py \
  scripts/task007dvis/long_figures.py tests/unit/test_vis_long_report.py
.venv/bin/ruff format --check scripts/task007dvis/long_report.py \
  scripts/task007dvis/long_figures.py tests/unit/test_vis_long_report.py
git diff --check
```

The verbatim authorization and initial failing pytest log/XML retain their original trailing
spaces. An unfiltered Git whitespace check reports those three evidence files. Source, authored
documentation and other staged artifacts pass the scoped check; the preserved failure evidence
was not whitespace-edited to hide those notices:

```sh
git diff --cached --check -- . \
  ':(exclude)docs/task007d/vis/vis1l/evidence/vis1l_authorization.txt' \
  ':(exclude)docs/task007d/vis/vis1l/evidence/vis1l_focused.log' \
  ':(exclude)docs/task007d/vis/vis1l/evidence/vis1l_focused.xml'
```

Full numerical regression belongs to separately authorized VIS-4 and is intentionally deferred.
Workbench importer compatibility/final interface acceptance is also unexecuted. No unseen-track
run, rerun, tuning, new controller feature or production promotion is authorized here.
