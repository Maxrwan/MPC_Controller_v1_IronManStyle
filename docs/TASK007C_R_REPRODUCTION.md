# Task007C-R reproduction

Run from the repository root. Preserve existing output folders; workers reject overwriting
completed cases. Measured latency is environment-dependent, so fresh measured outcomes need
not match, whereas fixed/replayed physical histories are the controlled reproducibility tests.
No analysis, tests, rendering or another benchmark may overlap measured repetitions.

## Audit and diagnostic preparation

```bash
PYTHONPATH=scripts .venv/bin/python -m task007cr.audit
.venv/bin/python -m pytest -q tests/unit/test_diagnostic_timing.py tests/unit/test_nlp_snapshot.py
```

Original Task007B/007C files are read-only inputs. Audit output records available/missing data
and exact file hashes. `trace_e.json`, `trace_f.json`, `trace_c.json` retain original launch-indexed
planner and codriver physical delays; no extrapolated entries are inserted.

## Serialized campaigns

```bash
.venv/bin/python scripts/task007cr/campaign.py fixed
.venv/bin/python scripts/task007cr/campaign.py replay
.venv/bin/python scripts/task007cr/campaign.py cross
.venv/bin/python scripts/task007cr/campaign.py measured
```

Each launch uses a fresh worker with native Accelerate SINGLE configured before numerical
imports. Primary runs preserve Candidate C, initial state, fixture, solver options and warm starts.
Fixed/replay modes impose availability only; computations still execute and are timed. Startup
planning remains gated. Historical trace exhaustion stops explicitly and produces a censored
prefix, not a full-lap result. Never use parallel measured workers.

The recorded continuation driver first analyzes completed runs and performs focused/backend
checks, then executes cross replay and measured repeats sequentially:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/task007cr/continue_campaign.py
```

Check `results/task007cr/campaign_stage.json` before launching work; never start a second driver
while one is running. Completed cases are retained, not repeated automatically.

## Offline analysis, after all benchmark workers finish

```bash
PYTHONPATH=scripts .venv/bin/python scripts/task007cr/analyze_all.py
PYTHONPATH=scripts .venv/bin/python -m task007cr.outcomes
PYTHONPATH=scripts .venv/bin/python -m task007cr.divergence
PYTHONPATH=scripts .venv/bin/python -m task007cr.select_snapshots
PYTHONPATH=scripts .venv/bin/python scripts/task007cr/nlp_replay.py --selection results/task007cr/snapshot_selection.json
PYTHONPATH=scripts .venv/bin/python -m task007cr.config_audit
```

`nlp_replay.py` dispatches a fresh SINGLE worker. It runs twenty solves with identical captured
inputs per snapshot, then a fresh-backend check and separately labeled initialization/state
perturbations. Bounds, solver options and nonlinear graph remain fixed. State perturbation sizes
come from the observed early optimizer-input divergence; all sizes are retained in the selection.

The remaining controlled-diagnostic commands are below. Task007C C1–C4 are not part of this
reproduction task.

## Remaining controlled diagnostics

After all R1–R4 case analyses exist:

```bash
PYTHONPATH=scripts MPLCONFIGDIR=/private/tmp/apex-mpl .venv/bin/python scripts/task007cr/finish_diagnostics.py
```

This writes pairwise comparisons, outcomes, the first-divergence timeline and snapshot
selection; performs exact NLP/warm-start/state replay in a fresh SINGLE subprocess; predeclares
the first E source-state release at progress ≥43 m; and changes only that planner delay by
−5, −2, −1, +1, +2, +5 ms. The unmodified R2 E run is the zero-change case. All codriver delays
and every other planner delay retain their original values. The generated `timing_selection.json`
records the zero-based nonstartup launch index and source progress before any outcomes are read.

After that driver finishes:

```bash
PYTHONPATH=scripts .venv/bin/python -m task007cr.numerical_summary
PYTHONPATH=scripts MPLCONFIGDIR=/private/tmp/apex-mpl .venv/bin/python -c 'from task007cr.plots import closed_loop_figures, numerical_figures, timing_figure; closed_loop_figures(); numerical_figures(); timing_figure()'
.venv/bin/python -m pytest -q
.venv/bin/ruff check scripts/task007cr scripts/run_task007cr.py src/apex/simulation/diagnostic_timing.py src/apex/simulation/asynchronous.py tests/unit/test_diagnostic_timing.py tests/unit/test_nlp_snapshot.py
```

## Final verification and packaging

After all workers and figure generation finish:

```bash
PYTHONPATH=scripts .venv/bin/python -m task007cr.timing_summary
PYTHONPATH=scripts .venv/bin/python -m task007cr.instrumentation_cost
PYTHONPATH=scripts .venv/bin/python -m task007cr.report_tables
PYTHONPATH=scripts .venv/bin/python -m task007cr.config_audit
PYTHONPATH=scripts MPLCONFIGDIR=/private/tmp/apex-mpl .venv/bin/python -c 'from pathlib import Path; from async_study.analysis import audit; audit(Path("results/task007cr"))'
PYTHONPATH=scripts .venv/bin/python -m task007cr.archive
```

The independent chronology auditor checks every retained case, including the initial smoke case.
Archive only after final documentation/log/figure edits, so the SHA256 manifest describes the
completed result set. The archive script verifies every retained original Task007B/Task007C
artifact before writing the diagnostic source ZIP and manifest.
