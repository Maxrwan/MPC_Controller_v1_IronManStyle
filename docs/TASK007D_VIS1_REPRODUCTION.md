# VIS-1 partial WORK reproduction and stop record

Read [results](TASK007D_VIS1_RESULTS.md), the [approved protocol](TASK007D_VIS_PROTOCOL.md) and
[interface](APEX_RUN_INTERFACE_0_1_0.md). This delivery stops for Engineering Review. Commands
below audit saved evidence or focused tests; they do not authorize another racing experiment.
Use repository root and the existing `.venv`. Preserve all old paths; write new output directories.

## Retained paths

| Path | Contents |
|---|---|
| results/task007d/vis/vis1/ | Initial preservation/source inventory, frozen matrix, full prerequisite log/XML, initial failed preflight |
| results/task007d/vis/vis1_execution/ | Updated preflight/test applicability, unchanged timing matrix, single A physical attempt, affected checks/report log |
| results/task007d/vis/vis1_execution/parity_A/ | input_configuration.json, applicability.json, raw.json, segments.json, exit.json, worker.log, offline_parity_audit.json |
| docs/task007d/vis/vis1/evidence/ | Compact failure logs, exact physical comparison, offline diagnostics/cycles, source/configuration hashes, tests and preservation |
| docs/task007d/vis/vis1/contract_fixtures/ | Four candidate apex-run packages and validation record; approximately 5.4 MiB total |
| docs/task007d/vis/vis1/tables/ | Case status, empty comparison tables, explicit deferred figure record |

Raw archives remain ignored. The physical attempt's release_contexts.json and summary.json were
never successfully written. Do not infer their absent observations. The corrected delivery
source differs from the physical attempt in exporter/report/test files; both inventories are saved.

## Focused checks

Check disk/process/measurement guards first; never overlap tests or offline rendering with
measurements. The original 410-case command is stored verbatim in
`docs/task007d/vis/vis1/evidence/verification.json`. It is historical execution evidence, not an
instruction to repeat the full selection. If separately requested, copy that argument list and
replace the JUnit/log destinations with fresh paths before executing it.

Latest focused adapter command (use fresh log/XML filenames when repeating):

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tests/unit/test_vis_exports.py --durations=5
.venv/bin/ruff check scripts/run_task007dvis.py scripts/task007dvis tests/unit/test_vis_exports.py
.venv/bin/ruff format --check scripts/run_task007dvis.py scripts/task007dvis tests/unit/test_vis_exports.py
```

Final adapter result: 30 passes. No full regression was run for this WORK stage.

## Recheck saved parity and physical evidence without a simulation

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python - <<'PY'
from threading_study.config import configure_accelerate
configure_accelerate(1)
import json
from pathlib import Path
from task007dvis.parity import compare
from task007dvis.protocol import CASES
from task007dvis.analysis import analyze
from task007dcx.worker import geometry, RecordedPlant
from apex.models.tire.config import RACING_TIRE_PHYSICS
p = Path('results/task007d/vis/vis1_execution/parity_A')
raw = json.loads((p / 'raw.json').read_text())
segments = json.loads((p / 'segments.json').read_text())
assert compare(CASES[0], raw, segments)['passed']
track, reference, parameters = geometry()
plant = RecordedPlant(parameters, track, tire_physics=RACING_TIRE_PHYSICS)
report, rows, cycles = analyze(raw, segments, plant, reference, CASES[0], [], [])
# Empty observer/thread lists are deliberately not a successful execution gate.
assert report['stop_gate'] == ['release_context_A_forecast_mismatch', 'native_thread_policy']
print(json.dumps({'physical': report['physical'], 'coverage': report['coverage'],
                 'unverified': ['release_context_replay', 'native_thread_observations']}, indent=2))
PY
```

Those two generic gate labels arise from absent inputs, not observed forecast/thread failures.
The committed offline report labels them explicitly missing/unverified. This audit neither
restores the missing release capture nor advances the launcher.

## Candidate interface validation and report

Validate existing bytes independently of Workbench:

```sh
PYTHONPATH=scripts:src .venv/bin/python - <<'PY'
from pathlib import Path
from task007dvis.validation import validate
for p in Path('docs/task007d/vis/vis1/contract_fixtures').iterdir():
    if p.is_dir():
        print(p.name, validate(p))
PY
```

To regenerate views from retained historical evidence into a **new** directory, use
`task007dvis.fixtures --output <fresh-directory>` under the SINGLE bootstrap shown above
(with `runpy.run_module('task007dvis.fixtures', run_name='__main__')`). This copies/censors
recorded evidence; it performs no solver run. Export provenance/dirty status can differ between
revisions, so byte identity of new manifests is not assumed. Existing package hashes must match.

The exact report invocation used for this delivery was:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_module("task007dvis.report",run_name="__main__")' \
--source results/task007d/vis/vis1_execution --output docs/task007d/vis/vis1/tables
```

That output already exists. Choose a fresh destination for any audit rerun. No paired figure is
generated without paired completed scientific exports. Workbench ingestion remains a separate
team's pending check.

## Scientific execution record — do not rerun without review

The initial invocation was `PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py
--case parity_A`. It stopped before simulation at JSON/config representation comparison.
After the tested serialization-comparison correction, the sole physical invocation was:

```sh
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
--root results/task007d/vis/vis1_execution --case parity_A
```

It exited 1 after saving physical evidence and failing snapshot serialization. Fresh-directory,
source-bound prerequisite/export gates and required predecessor completion intentionally prevent
reuse of that directory or progression. Do not fabricate a passing manifest, erase a failed
attempt or use a new root to bypass review. Review must resolve the missing prerequisite evidence
and whether another physical parity run is authorized. The original six-run long matrix, balanced
order, frozen controls, resources and stop conditions remain unchanged and unexecuted.
