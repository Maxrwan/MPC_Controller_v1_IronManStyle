# Task 007A reproduction

Run from the project root. Preserve published results by choosing a fresh output directory.
The generator is offline-only. Generation/validation must complete before launching simulation.
Timing workers run sequentially with native Accelerate SINGLE, without concurrent tests/plots.

```sh
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle
uv sync --locked
export MPLCONFIGDIR=/private/tmp/apex-mpl

# Deterministic track construction and reference generation from documented track_source.json
.venv/bin/python scripts/run_task007a.py generate
# Strict schema, geometry, margin, domain, grip and actuator validation
.venv/bin/python scripts/run_task007a.py validate

OUT=/private/tmp/apex-task007a-reproduction
# Primary: first partial/transient lap, then two full comparable laps
.venv/bin/python scripts/run_task007a.py run --mode measured --laps 3 --duration 300 --output "$OUT"
# Supporting chronology checks; not primary measured performance claims
.venv/bin/python scripts/run_task007a.py run --mode zero --laps 1 --duration 100 --output "$OUT"
.venv/bin/python scripts/run_task007a.py run --mode injected --laps 1 --duration 100 --output "$OUT"
# Figures, lap/sector/difficulty metrics and physical chronology audits
.venv/bin/python scripts/run_task007a.py analyze --output "$OUT"
# Regression and style after timing experiments finish
.venv/bin/python -m pytest -q
.venv/bin/ruff check src scripts tests
.venv/bin/ruff format --check src scripts tests
```

`--fixture` can point to replacement Planning files plus the matching track_source.json. Schema,
track hash and all validation requirements must pass; runtime does not regenerate or repair it.
The injected check uses 60 ms planner delay and zero simulated codriver latency. The measured
primary applies both measured planner and measured codriver delay while physics continues.
`generate` reproduces CSV/manifest bytes deterministically; validation writes its separate report.
Runtime no-overwrite guards protect completed case summaries. Timing varies with host scheduling.
