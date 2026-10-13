# Task007D-C — amended C0 and gated C1–C3 reproduction

Implemented opt-in scheduler on baseline `c56e5095105cd1c70649127e246c48ee70c26428`.
Original blocked reproduction instructions remain verbatim below. They reproduce the original
variable-mode conflict and must not be confused with this amended fixed-mode delivery.

Inspect `git status`, current branch and remote before work. Use the existing `.venv`.
Check running processes and `results/**/MEASURED_ACTIVE` / `results/task007d/D3_ACTIVE`; keep
at least 1 GiB free. Never run workers concurrently, nor alongside tests/analysis/rendering.
All outputs below must be new directories. Do not remove old guards without investigating.

## C0 before racing

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python - <<'PYTEST'
from threading_study.config import configure_accelerate
configure_accelerate(1)
import pytest
raise SystemExit(pytest.main(['-q',
 'tests/unit/test_fixed_handoff_scheduler.py',
 'tests/unit/test_fixed_handoff_analysis.py',
 'tests/unit/test_fixed_handoff_contract.py',
 'tests/unit/test_async_chronology.py',
 'tests/unit/test_diagnostic_timing.py',
 'tests/unit/test_committed_prefix_runtime.py',
 'tests/unit/test_trajectory_tracker.py',
 'tests/unit/test_lightweight_prediction.py',
 'tests/unit/test_prediction_forensics.py']))
PYTEST
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -m task007dc.c0 --output results/task007d/c/reproduction_c0
```

This exports the original 155 ms amended case (miss .330, ready/discard .415, fallback .400)
and separate successful urgent case (ready .295, accept .330). The initial pre-racing C0 gate
had 92 passes; final focused count/results are in the results report. Neither fixture runs NMPC.

## ECDF and frozen selection

```sh
PYTHONPATH=scripts:src .venv/bin/python - <<'PY'
from pathlib import Path
from task007dc.ecdf import export
export(Path('results/task007d/c/reproduction_ecdf'))
PY
```

The 1,543 retained durations are read from the five N8 gamma2 measured files named/hashes recorded
in the committed ECDF summary. No new timing measurement occurs. Predeclared timing/configuration
is `docs/task007d/c/amended/protocol.json`: frozen N8/dt=.1, original Q/R/W, lambda=0,
alpha_vy=alpha_r=1, gamma2.0/1.8, 0.08 m synthetic margin, unchanged A/TVLQR/model/solver/warm starts,
2 s each, codriver 5 ms, no seed. Offset selection precedes outcomes.

## Sequential workers with phase gates

Each command spawns a fresh SINGLE worker, refuses an existing output directory and enforces
guards/disk. It returns nonzero on a scientific gate; inspect `summary.json` before continuing.
Do not use a shell loop that continues after failure. The following order reproduces the pilot;
all nine original outcomes are under `results/task007d/c/amended/`.

```sh
.venv/bin/python scripts/run_task007dc.py --case C1_steady --output results/task007d/c/reproduction/C1_steady
.venv/bin/python scripts/run_task007dc.py --case C1_jitter --output results/task007d/c/reproduction/C1_jitter
```

Inspect C1 authority chronology and partition differences. Only after both pass:

```sh
.venv/bin/python scripts/run_task007dc.py --case C2_miss --output results/task007d/c/reproduction/C2_miss
```

Verify plan 4 miss/discard and plan 5 recovery against C1_steady. Only after passing:

```sh
.venv/bin/python scripts/run_task007dc.py --case C3_g2.0_variable --output results/task007d/c/reproduction/C3_g2.0_variable
.venv/bin/python scripts/run_task007dc.py --case C3_g2.0_fixed70 --output results/task007d/c/reproduction/C3_g2.0_fixed70
.venv/bin/python scripts/run_task007dc.py --case C3_g2.0_fixed80 --output results/task007d/c/reproduction/C3_g2.0_fixed80
.venv/bin/python scripts/run_task007dc.py --case C3_g1.8_variable --output results/task007d/c/reproduction/C3_g1.8_variable
.venv/bin/python scripts/run_task007dc.py --case C3_g1.8_fixed70 --output results/task007d/c/reproduction/C3_g1.8_fixed70
.venv/bin/python scripts/run_task007dc.py --case C3_g1.8_fixed80 --output results/task007d/c/reproduction/C3_g1.8_fixed80
```

Imposed histories are retained in protocol and worker summary; only consumed launches count.
Startup does not consume a replay entry. C1 jitter repeats 23/47/61/39 ms; C2 changes the fourth
runtime delay to 75 ms; C3 repeats 35/55/45/25 ms. No tail padding, solver cancellation or
floating-point rounding of releases is applied. Raw files include physical segments, immutable
release contexts, full packet contents, requested/applied controls and all original telemetry.
Source/fixture/vehicle hashes, backend, observed thread counts [1] and CPU/wall ratio are recorded.
Delivery adds offline analysis/docs plus a repeated-urgent-trigger telemetry fix after pilot
capture; the recorded per-run source hashes identify exactly what ran. It changes no pilot
commands/schedules and none of the pilot histories had urgent demand.

## Offline tables, mechanism check and figures

Run only after all workers finish. The final committed tables are under `amended/tables_v2`;
initial analysis tables are retained in ignored `amended/analysis_initial` because they used
unequal sampling density for the supplementary progress interpolation. Primary common-time
comparisons and all raw simulation outputs are unchanged.

```sh
PYTHONPATH=scripts:src .venv/bin/python -m task007dc.export --source results/task007d/c/reproduction --output results/task007d/c/reproduction_tables
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -m task007dc.partition_check --source results/task007d/c/reproduction --output results/task007d/c/reproduction_partition.json
PYTHONPATH=scripts:src .venv/bin/python -m task007dc.metric_tables --source results/task007d/c/reproduction_tables/summary.json --output results/task007d/c/reproduction_metrics.md
MPLCONFIGDIR=/private/tmp/apex-matplotlib PYTHONPATH=scripts:src .venv/bin/python -m task007dc.figures --tables results/task007d/c/reproduction_tables --ecdf docs/task007d/c/amended/ecdf --output results/task007d/c/reproduction_figures
```

The partition check uses only retained held commands/state and the unchanged plant to replay the
first .120–.125 s split offline. This never feeds future truth into a forecast. Compact CSV files
retain numerical figure inputs, event partitions and every planner cycle. Nulls become blank
cells in CSV. Canonical per-state statistics remain separate. Common progress uses derived
linear interpolation of common 10 ms samples within observed overlap; no extrapolation/truth claim.

## Final verification after measurements

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src XDG_CACHE_HOME=/private/tmp/apex-cache MPLCONFIGDIR=/private/tmp/apex-matplotlib .venv/bin/python - <<'PYTEST'
from threading_study.config import configure_accelerate
configure_accelerate(1)
import pytest
raise SystemExit(pytest.main(['-q']))
PYTEST
.venv/bin/ruff check src/apex/simulation/asynchronous.py src/apex/simulation/fixed_handoff.py src/apex/control/trajectory/packet.py scripts/run_task007dc.py scripts/task007dc scripts/task007d/forensics.py tests/unit/test_fixed_handoff_scheduler.py tests/unit/test_fixed_handoff_analysis.py
.venv/bin/ruff format --check src/apex/simulation/asynchronous.py src/apex/simulation/fixed_handoff.py src/apex/control/trajectory/packet.py scripts/run_task007dc.py scripts/task007dc scripts/task007d/forensics.py tests/unit/test_fixed_handoff_scheduler.py tests/unit/test_fixed_handoff_analysis.py
```

Compare preserved historical hashes and review staged diff. Commit only C source/tests/docs and
compact evidence, normally push main, verify remote SHA. Raw archives remain ignored. No larger
campaign, B integration or next subtask is authorized by these reproduction instructions.

---

# Historical original C0 reproduction guide (retained verbatim)

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
