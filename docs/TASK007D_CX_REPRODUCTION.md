# Task007D-CX — Studies 1–2 reproduction

Status: **WORK_COMPLETE_PENDING_REVIEW**. [Results](TASK007D_CX_RESULTS.md),
[predeclared protocol](TASK007D_CX_CLOSURE.md), [Primary specification](TASK007D_CX_SPEC.txt).
Study 3/full laps/Performance freeze/Efficiency are **NOT EXECUTED — AWAITING ENGINEERING REVIEW**.
Commands below document reproduction; they do not authorize another campaign or verification stage.

## Revision and environment

Experimental core: `77ba86f28e24d2780d01b5b0058e5405dde3d6ec`; existing source/configuration is
unchanged. Use the delivered CX scripts/tests, whose hashes are in
[verification.json](task007d/cx/verification.json). Per-run source, fixture, vehicle, package and
platform hashes are in [provenance.json](task007d/cx/tables/provenance.json); raw summary.json also
records exact configuration, initial state, timing, native controls, thread counts and CPU/wall.
The containing Git commit is the delivery revision, supplied in the final handoff.

Use the existing `.venv`, not freshly upgraded dependencies. Recorded environment:
macOS 26.5.1 arm64; Python environment from uv.lock; NumPy 2.5.3, SciPy 1.18.1,
CasADi 3.8.1, psutil 7.2.2, threadpoolctl 3.7.0. Native Accelerate SINGLE must be configured
before importing NumPy/CasADi. The launcher uses the existing threading_study bootstrap.
This Mac setup is not a portable promise for other BLAS backends.

## Resource and prerequisite gate

From the repository root, inspect `git status`, `df -h .`, active scientific workers and
`results/**/MEASURED_ACTIVE` / `results/task007d/D3_ACTIVE`. Investigate any live guard; never
remove it merely to proceed. The launcher's floor is 1 GiB free. Do not overlap runs with tests,
analysis, rendering, compression or benchmarks. Close heavy background scans; the original
Storage-scan deferral and later process snapshot remain in local evidence. The launcher does not
promise automatic isolation from unrelated OS work.

The following focused selection passed **225 tests before the dependent experiments**, using
Accelerate SINGLE. The final CX test file subsequently gained portable/censoring coverage;
its final focused rerun passed **13 tests**. Full tests/ is intentionally deferred to formal
VERIFICATION of the reviewed revision. No regression fingerprint/tolerance was altered.

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tests/unit/test_cx_closure.py \
 tests/unit/test_fixed_handoff_scheduler.py tests/unit/test_fixed_handoff_contract.py \
 tests/unit/test_fixed_handoff_analysis.py tests/unit/test_async_chronology.py \
 tests/unit/test_diagnostic_timing.py tests/unit/test_prediction_diagnostics.py \
 tests/unit/test_trajectory_tracker.py tests/unit/test_mpc.py \
 tests/unit/test_dynamic_bicycle.py tests/unit/test_grip_tire.py \
 tests/unit/test_task007c_physics.py tests/unit/test_threading_study.py
```

Final affected analysis-test rerun:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tests/unit/test_cx_closure.py
.venv/bin/ruff check scripts/run_task007dcx.py scripts/task007dcx tests/unit/test_cx_closure.py
.venv/bin/ruff format --check scripts/run_task007dcx.py scripts/task007dcx tests/unit/test_cx_closure.py
git diff --check
```

Logs retained under results/task007d/cx/: prerequisites.log, cx_tests_final.log (the intermediate
fixture-diagnostic failure), cx_tests_verified.log, ruff_final.log. The fixture correction supplies
StraightPlanner's explicit release-plus-estimate target; it does not modify production behavior.

## Reuse audit, no optimizer rerun

Requires retained local raw C1 evidence at results/task007d/c/amended/C1_steady and C1_jitter.
The audit replays recorded packets through the current scheduler/TVLQR/plant and checks every
causal preparation input. It runs no optimizer. Write to a new path; never overwrite the delivered
audit or historical files:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_module("task007dcx.reuse", run_name="__main__")' \
--output /private/tmp/task007dcx_reuse_new.json
```

[reuse_audit.json](task007d/cx/reuse_audit.json) records 85/87 source matches, exact five Planning
files/vehicle, no urgent demand, and exact replay of states, chronology, control, reserve and RK4.
The two accepted urgent-bookkeeping source differences do not affect these histories. No fresh
fixed-C jitter simulation was required.

## Authorized campaign design and original commands

[protocol.json](task007d/cx/protocol.json) contains all explicit cases, timing histories, seed=null,
2 s duration, gamma2, 5 ms imposed codriver delay and balanced rotating order. Every worker uses
predictor A, frozen N8/dt0.1/H0.8/Q/R/W/lambda0/alpha1 and original tire/solver/TVLQR/warm starts.
Study 1 planner timing is imposed; Study 2 uses the fresh actual complete preparation measurement.
No future measurement enters a forecast. Study 2 has ten repetitions EACH of A/C70/C80, not a
five-run reduction. All 32 runs succeeded scientifically; no unfavorable case was replaced.

Each original case was launched sequentially as follows (the original destination now exists and
will deliberately fail if reused):

```sh
.venv/bin/python scripts/run_task007dcx.py \
 --case S1_A_steady --output results/task007d/cx/S1_A_steady
```

For an explicitly authorized reproduction, use a NEW campaign directory, retain logs and stop at
the first nonzero return. This preserves the precise ordering without a general experiment framework:

```sh
.venv/bin/python - <<'PY'
import json
import subprocess
from pathlib import Path
p = json.loads(Path('docs/task007d/cx/protocol.json').read_text())
root = Path('results/task007d/cx/reproduction_new')
root.mkdir(parents=True, exist_ok=False)
for case in p['order']:
    subprocess.run([
        '.venv/bin/python', 'scripts/run_task007dcx.py', '--case', case,
        '--output', str(root / case),
    ], check=True)
PY
```

Run folders contain raw.json, segments.json, release_contexts.json, summary.json and worker.log.
Measured wall timings and therefore closed-loop histories need not repeat exactly across sessions.
Deterministic Study 1 and causal reuse evidence have different reproducibility claims from measured
host timing. All source hashes must be checked before claiming applicability to another revision.

## Analysis and figures after workers finish

The original raw campaign remains in results/task007d/cx/. The report requires no running guard
and a fresh output directory. It reads accepted retained C1 evidence plus the 32 new cases. It
reuses existing C/D metrics and adds common-grid quality, per-miss consequences, timing/censoring
and per-run uncertainty. No future physical information is used inside prediction.

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_module("task007dcx.report", run_name="__main__")' \
--source results/task007d/cx --output /private/tmp/task007dcx_tables_new

MPLBACKEND=Agg VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -m task007dcx.figures \
--tables docs/task007d/cx/tables --output /private/tmp/task007dcx_figures_new
```

Figures can be rebuilt from the committed compact tables without raw histories. Full table/reuse
reconstruction requires retained raw files, intentionally excluded from Git. Table JSON/CSV hashes
allow audit of local raw evidence against the delivered summary. Initial analysis remains ignored
at results/task007d/cx/analysis_initial/; the final table set adds explicit authority-gap/derived
pre-recovery reserve fields and retains every miss.

The canonical compact set is docs/task007d/cx/tables/; ten rendered PNGs are in figures/. All ten
were inspected. No full-lap figures were generated. The authoritative 39-section interpretation is
[TASK007D_CX_RESULTS.md](TASK007D_CX_RESULTS.md). Formal acceptance remains pending review.
