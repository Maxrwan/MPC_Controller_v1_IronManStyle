# Focused test selection

Use this map with the [staged workflow](CODEX_VERIFICATION_WORKFLOW.md). Select tests for changed
behavior and its callers; these are starting sets, not substitutes for explicit scientific gates.
Paths in the unit-test column are relative to `tests/unit/`. No test layout or markers change.

| Subsystem | Focused unit files | Broader checks when required |
|---|---|---|
| Geometry and coordinates | `test_state.py`, `test_frenet.py`, `test_track_geometry.py`, `test_track_io.py` | `tests/regression/test_geometry_accuracy.py`; affected track/model integration |
| Vehicle dynamics and tire physics | `test_config.py`, `test_kinematic.py`, `test_dynamic_components.py`, `test_dynamic_bicycle.py`, `test_grip_tire.py` | `tests/integration/test_kinematic_track.py`, `tests/integration/test_dynamic_track.py`, `tests/integration/test_grip_tracking.py`; `tests/regression/test_kinematic_accuracy.py`, `tests/regression/test_dynamic_accuracy.py` |
| NMPC formulation and solver | `test_mpc.py`, `test_nlp_snapshot.py`, `test_progress_objective.py`, `test_progress.py` | `tests/integration/test_mpc_tracking.py`; `test_parameter_study.py` for study configuration and `test_latency.py` for application-state behavior |
| TVLQR and trajectory buffers | `test_trajectory_tracker.py`, `test_committed_prefix.py`, `test_committed_prefix_runtime.py` | `test_local_mpc.py` only when that codriver/interface is affected; `test_async_chronology.py` and historical readers for packet changes |
| Asynchronous scheduling and latency | `test_async_chronology.py`, `test_latency.py`, `test_diagnostic_timing.py`, `test_committed_prefix_runtime.py`, `test_fixed_handoff_contract.py`, `test_fixed_handoff_scheduler.py` | `test_prediction_diagnostics.py` for observation noninterference; `test_threading_study.py` for native-thread policy; baseline `test_runner.py` / `test_baseline.py` for fallback changes |
| Task 007 scientific analysis | `test_planning_reference.py`, `test_aggressive_reference.py`, `test_task007b_export.py`, `test_task007c_metrics.py`, `test_task007c_physics.py`, `test_timing_sensitivity.py` | As relevant: `test_prediction_diagnostics.py`, `test_prediction_forensics.py`, `test_pseudo_reference_ablation.py`, `test_lightweight_prediction.py`, `test_lightweight_figures.py`, `test_fixed_handoff_analysis.py` |
| Full integration and regression | Affected unit set above | `tests/integration/`, `tests/regression/`; complete acceptance set: `tests/` |

All bare `test_*.py` references are unit tests; integration/regression paths are explicit. Confirm
paths with `rg --files tests`. Integration includes actual controller/plant simulations and can be expensive;
see the existing [integration](../tests/integration/README.md) and
[regression](../tests/regression/README.md) notes. Test names do not authorize racing campaigns.

## Existing pytest selection

From the repository root, with the existing environment and no conflicting timing workload,
use file paths, a node ID or a narrow `-k` expression. This Mac command preserves the established
Accelerate SINGLE setup before importing numerical modules; it forwards ordinary pytest options:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tests/unit/test_async_chronology.py tests/unit/test_trajectory_tracker.py --durations=10
```

Replace the final selection/options as appropriate:

| Intent | pytest arguments after the bootstrap |
|---|---|
| One mathematical assertion | `-q tests/unit/test_mpc.py::test_known_zero_cost_trajectory` |
| Matching tests within one relevant file | `-q tests/unit/test_mpc.py -k 'parity or warm_start'` |
| Confirm selected node IDs without executing tests | `--collect-only -q tests/unit/test_async_chronology.py` |
| Authorized full integration/regression directories | `-q tests/integration tests/regression --durations=20` |
| Authorized complete regression suite | `-q tests --durations=20` |

Collection still imports test modules; do not run it during an isolated measurement. A filtered
selection can accidentally omit coverage: inspect its selected/deselected counts. Use `-x` while
investigating a first failure if helpful, but report unexecuted remainder explicitly. Do not add
broad markers or run tests in parallel to conceal cost. On another backend, inspect and use its
documented supported controls in a fresh process; the Mac bootstrap is not a portable substitute.

Capture full output with `> /path/to/fresh/task-log.txt 2>&1` on the invocation and retain its exit
status. Summarize successful runs; inspect detailed logs for failures/anomalies. `--durations=10`
or `--durations=20` reports slow test/setup/teardown entries during an already authorized run;
it is not a controlled solver benchmark. Do not launch an extra suite solely to time it.

Historical reference: Task007D-C recorded **696 passes in 649.73 s** and **140 focused passes in
5.17 s**, delivered at `44e0471680bb22ea1ee790173d1f2481a905f386`. See the retained
[verification record](task007d/c/amended/verification.json). These are prior host observations,
not new runs for this workflow update, a future fixed test count, or guaranteed runtimes.
Collect more detailed duration data at the next authorized complete verification run.

## Scoped lint and documentation checks

For changed Python files, use the existing Ruff settings without installing new tooling:

```sh
.venv/bin/ruff check path/to/changed_file.py
.venv/bin/ruff format --check path/to/changed_file.py
git diff --check
```

For documentation-only work, check instructions for consistency, relative links/anchors and
referenced test paths; inspect Markdown fences/tables and `git diff --check`. Audit the changed
file list and preservation of historical evidence. Ruff does not validate Markdown; do not run
the numerical suite or NMPC simulations merely to verify prose. An unexpected need for executable
changes requires review rather than automatic scope expansion.

## Reusing a previous result

Record the prior exact SHA, test selection and log. Compare that revision with the new revision
for tested source and transitive dependencies, tests, fixtures, configuration and environment.
For example, use `git diff <verified-sha> <reviewed-sha> -- <relevant-paths>` after identifying
those paths; an empty diff on the test file alone proves nothing about its dependencies.
State why the prior evidence applies, label it inherited, and rerun affected checks if it does
not. Honor any explicit gate requiring a fresh complete run. See the workflow's revision rules.
