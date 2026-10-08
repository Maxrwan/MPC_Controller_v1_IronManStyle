# Task 007B reproduction

Run from the repository root with the locked environment. Every measured case must run
sequentially in a fresh worker, without tests, plotting or bulk numerical analysis competing
for CPU. Workers select native Accelerate SINGLE through its supported API before numerical
initialization and record the returned setting. No dependencies were added for Task 007B.

```bash
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle
uv sync --locked
export MPLCONFIGDIR=/private/tmp/apex-mpl
.venv/bin/python scripts/run_task007b.py generate --gammas 1 1.25 1.5 1.75 2 2.25 2.5
.venv/bin/python scripts/run_task007b.py validate --gamma 2.5
```

`generate` writes separate Task 007B packages. It preserves the accepted Task 007A fixture
and all non-speed CSV text. Runtime never invokes generation. Capped packages contain an
explicit offline piecewise polynomial for exactly min(gamma*v_base, 6 m/s).

## Selected conservative configuration and controls

Use a fresh output directory; completed cases cannot be overwritten. The selected weight is
limited to the conservative gamma=1 experiment. It is not approved as a universal aggressive
configuration. Baseline progress remains disabled by default.

```bash
OUT=/private/tmp/apex-task007b-reproduction
.venv/bin/python scripts/run_task007b.py run --output "$OUT" --case b0 --laps 3 --duration 250
.venv/bin/python scripts/run_task007b.py run --output "$OUT" --case b4_g1_w2 --gamma 1 --progress-weight 2 --laps 3 --duration 250
.venv/bin/python scripts/run_task007b.py run --output "$OUT" --case support_zero_w2 --gamma 1 --progress-weight 2 --mode zero
.venv/bin/python scripts/run_task007b.py run --output "$OUT" --case support_injected_w2 --gamma 1 --progress-weight 2 --mode injected --injected-delay .15
```

B1 screens gamma=1.25,1.5,1.75,2,2.25,2.5 at lambda=0. B2 screens
lambda=.1,.25,.5,1,2,4,8 at gamma=1. B3 screens lambda=1,2 at gamma=2,2.5.
B4 confirms gamma=1 at lambda=1,2 and gamma=2 at lambda=0,1,2 over three laps.
The first lap is a rolling-launch transient; laps 2 and 3 are comparable complete laps.
Do not mix startup-screen lap times with comparable-lap times.

## Exact archived fixtures and full configuration replay

`results/task007b/study_manifest.json` records every case's options, fixture hashes and runtime
source hashes. The replay script executes those options sequentially against each retained
`case/fixture`. It deliberately requires a separate output directory.

```bash
.venv/bin/python scripts/task007b/replay.py --output /private/tmp/apex-task007b-full-replay
# Or only specified cases:
.venv/bin/python scripts/task007b/replay.py --output /private/tmp/apex-task007b-pair --cases b0 b4_g1_w2
```

Early screen fixtures used general float reserialization with geometry differences no larger
than 1.4e-14 m. Each case retains its exact fixture; generator v2 preserves original geometry
CSV text exactly. The canonical Task 007A fixture was never changed. B0 preceded additive
support for the capped polynomial loader. Source hashes and `source_snapshot.zip` identify
versions; replay under current source preserves the controller mathematics, but measured
latency and nonlinear closed-loop trajectories are not guaranteed bitwise identical.

## Analysis, review images and regression

After benchmarks finish:

```bash
.venv/bin/python scripts/run_task007b.py analyze --output "$OUT"
.venv/bin/python scripts/run_task007b.py plots --output "$OUT" --cases b0 b4_g1_w2
.venv/bin/python -m pytest -q
.venv/bin/ruff check src scripts tests
.venv/bin/ruff format --check src scripts tests
```

To refresh the delivered full study, use its existing output directory for analysis and plots
only. With no `--cases`, plots read `selection.json`. Preserve that reviewed selection file
when regenerating the result tables:

```bash
.venv/bin/python scripts/run_task007b.py analyze
.venv/bin/python scripts/run_task007b.py plots
PYTHONPATH=scripts .venv/bin/python -c "from task007b.report import generate; generate('results/task007b')"
PYTHONPATH=scripts .venv/bin/python -c "from task007b.package import package; package('results/task007b')"
```

Packaging verifies retained Task 007A/006.4 results, canonical fixture bytes, each experiment
fixture, source files and archive integrity. Repackage only after all source, report and test-log
changes are finished. Timing distributions describe this Mac and are not exact CI assertions.
