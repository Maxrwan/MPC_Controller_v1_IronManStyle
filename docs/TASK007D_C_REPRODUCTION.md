# Task007D-C — reproduce the C0 stop gate

Baseline: `3564bb394c7f49cf430d6f0f976bea153a5da822`. Use the repository `.venv` and existing
dev dependencies. No runtime C implementation or racing campaign exists in this delivery.

## Preconditions

Inspect active processes and `results/**/MEASURED_ACTIVE` plus `results/task007d/D3_ACTIVE`.
Do not overlap tests/export with timing-sensitive work. Keep at least 1 GiB free. The audit
script also checks guards/disk and refuses existing output directories. Use a fresh directory
under `results/task007d/c/` and preserve every earlier outcome. Existing synthetic test fixtures
are reused directly; the audit script requires pytest's fixture definitions, not a new model.

## Focused C0 and retained chronology regressions

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src XDG_CACHE_HOME=/private/tmp/apex-cache MPLCONFIGDIR=/private/tmp/apex-matplotlib .venv/bin/python - <<'PYTEST'
from threading_study.config import configure_accelerate
configure_accelerate(1)
import pytest
raise SystemExit(pytest.main(['-q',
    'tests/unit/test_fixed_handoff_contract.py',
    'tests/unit/test_async_chronology.py',
    'tests/unit/test_diagnostic_timing.py',
    'tests/unit/test_committed_prefix_runtime.py',
    'tests/unit/test_trajectory_tracker.py']))
PYTEST
.venv/bin/ruff check scripts/audit_task007dc_c0.py tests/unit/test_fixed_handoff_contract.py
.venv/bin/ruff format --check scripts/audit_task007dc_c0.py tests/unit/test_fixed_handoff_contract.py
```

Observed: **68 passed in 4.72 s**, including four new stop-gate tests. Existing fingerprint
assertions and tolerances were not changed. New arithmetic checks use 1e-12 s absolute tolerance
with zero relative tolerance where stated; the demonstrated 5 ms phase conflict is not roundoff.
This test set validates the counterexample and legacy behavior, not the missing fixed-mode tests.

## Raw reproducer export

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python scripts/audit_task007dc_c0.py --output results/task007d/c/c0_urgent_grid_reproduction
```

The delivered ignored raw run is `results/task007d/c/c0_urgent_grid/`. `raw.json` retains the
ordinary variable-mode event/state/control record including measured diagnostic durations.
`summary.json` records the configuration, vehicle, source hashes, SINGLE setting, triggers,
releases, busy misses and all ten hypothetical fixed offsets. No random seed is used.
Expect urgent release at 0.255 s and exact +70 ms target at 0.325 s, 5 ms off-grid. Wall-clock
telemetry need not match bitwise; physical chronology and requested/applied controls do.

Compact committed evidence is `docs/task007d/c/c0_summary.json`, `offset_grid_audit.csv` and
`verification.json`. To regenerate the first two after a new export:

```sh
.venv/bin/python - <<'PY'
import csv, json
from pathlib import Path
source = Path('results/task007d/c/c0_urgent_grid_reproduction/summary.json')
out = Path('/private/tmp/apex-c0-compact-reproduction')
out.mkdir(exist_ok=False)
s = json.loads(source.read_text())
(out / 'c0_summary.json').write_text(source.read_text())
with (out / 'offset_grid_audit.csv').open('x', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(s['targets'][0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(s['targets'])
PY
```

A later delivery commit changes the audit's recorded source Git SHA; do not replace the baseline
field in the retained original. Source hashes identify actual code. No ECDF selection, C1/C2/C3
run or figure command is provided because the explicit C0 stop gate prohibited those phases.
The complete regression suite is deferred: it includes costly NMPC/multilap integration cases,
whereas this assignment requires C0 completion before racing simulations. No full-suite pass
is claimed. Await urgent-policy review before resuming C0 implementation or pilot work.
