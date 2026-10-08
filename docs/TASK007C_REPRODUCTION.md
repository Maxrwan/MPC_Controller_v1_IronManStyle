# Task007C reproduction

**Status: stopped at the mandatory reproduction gate.** E/F each have an initial and one
additional measured run, neither reproducing the original specific rejected behavior. Do not
start C1–C4 or modify the runtime to force agreement. See `TASK007C_RESULTS.md`.

## Measured anchor generation

Run from the repository root. The recorded runs already exist. Drivers protect completed cases;
do not overwrite them. To conduct a newly authorized repetition campaign, use a new output
location/case identity in a copied driver and retain the current artifacts.

```bash
export MPLCONFIGDIR=/private/tmp/apex-mpl
.venv/bin/python scripts/task007c/anchors.py
.venv/bin/python scripts/task007c/repeat_rejected.py
```

A–F run sequentially in fresh SINGLE workers, using archived Task007B fixtures, unchanged
Candidate C and matching lap counts/durations. Do not run analysis, tests or rendering during
measured benchmarks. Measured outcomes depend on the actual latency trace; these commands
do not promise an identical trajectory. Zero/injected/measured chronology remains supported
by the unchanged runtime and regression suite; no new computational controller was introduced.

## Offline analysis of the retained runs

After all workers have finished:

```bash
export MPLCONFIGDIR=/private/tmp/apex-mpl
.venv/bin/python scripts/run_task007b.py analyze --output results/task007c
PYTHONPATH=scripts .venv/bin/python -m task007c.anchor_review
PYTHONPATH=scripts .venv/bin/python -m task007c.provenance
PYTHONPATH=scripts .venv/bin/python -c "from pathlib import Path; from task007c.metrics_export import export; export(Path('results/task007c'))"
PYTHONPATH=scripts .venv/bin/python -m task007c.anchor_plots
PYTHONPATH=scripts .venv/bin/python -m task007c.anchor_zooms
.venv/bin/python -m pytest -q
.venv/bin/ruff check scripts/task007c tests/unit/test_task007c_metrics.py
```

The analysis command includes the independent physical-time audit. It writes derived analysis
only. Original Task007B artifacts remain read-only inputs; provenance verifies all 675 original
artifact hashes and current runtime preservation. A's early B0 loader source exception is
explicitly documented in Task007B and the new provenance report; B–F match exactly.

## Gate interpretation

The gate report lists original, first and additional repeated metrics without discarding runs.
Conservative/near-limit lap inspection bands are 0.5%/2%; rejected E must reproduce large
sweeper heading variation (>3 rad) and persistent rate-limit activity (>1 s), while F must
reproduce material predicted slack (>1e-6 m) and clearance below the retained 0.08 m margin.
These are disclosed reproduction inspection checks, not controller thresholds or a universal
oscillation definition. They were recorded before E/F analysis. Visual review and all metric
differences remain necessary. Initial checks fail; additional repeats also fail the same E/F
behavior criteria. Do not reinterpret the slight F sweep oscillation as reproduction of its
original slack failure.

No C1–C4 commands exist because the prerequisite was not passed. The planned protocol in
`TASK007C_NEAR_LIMIT_APEX_DIAGNOSIS.md` is explicitly unexecuted. Planning, plant, TVLQR,
progress formula, state ordering, dt and horizon remain unchanged for Task007C.
