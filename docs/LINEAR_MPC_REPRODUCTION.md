# Task 006.4 reproduction

Run from `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle`.
The existing results are immutable inputs; choose a fresh output directory for experiments.
All timing experiments must run sequentially without tests, analysis or other CPU work.
The script starts a fresh native-SINGLE worker per case. Explicit N=8 selects the studied MPC;
the initial library/CLI default is N=5. Runtime timing varies by machine and load.

```sh
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle
uv sync --locked
export MPLCONFIGDIR=/private/tmp/apex-mpl
OUT=/private/tmp/apex-0064-reproduction

# Fresh measured TVLQR baseline
.venv/bin/python scripts/run_linear_mpc_codriver.py run --controller tvlqr --name baseline --output "$OUT"
# All horizons and paired TVLQR replay, same saved Task006.3 packets
.venv/bin/python scripts/run_linear_mpc_codriver.py horizons --output "$OUT"
# Selected packet replay (separate name from horizon sweep)
.venv/bin/python scripts/run_linear_mpc_codriver.py run --phase replay --horizon 8 --name selected_replay --output "$OUT"
# Full measured closed loop, disturbance and constraint stress
.venv/bin/python scripts/run_linear_mpc_codriver.py run --horizon 8 --name selected_closed --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py run --horizon 8 --scenario disturbance --name selected_disturbance --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py run --horizon 8 --scenario stress --name selected_stress --output "$OUT"
# Both controllers: nominal, disturbance, stress, QP failure, 60/100/150ms and spike
.venv/bin/python scripts/run_linear_mpc_codriver.py comparisons --horizon 8 --output "$OUT"
# Standalone long-tail and local-failure reproductions
.venv/bin/python scripts/run_linear_mpc_codriver.py run --horizon 8 --scenario spike --mode injected --delay .025 --zero-codriver --name selected_spike --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py run --horizon 8 --scenario qp_failure --name selected_failure --output "$OUT"
# Limited W/LTI study
.venv/bin/python scripts/run_linear_mpc_codriver.py run --phase replay --horizon 8 --weight .5 --name replay_N8_W05 --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py run --phase replay --horizon 8 --weight 1 --name replay_N8_W1 --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py run --phase replay --horizon 8 --weight 2 --name replay_N8_W2 --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py run --phase replay --horizon 8 --model lti --name replay_N8_LTI --output "$OUT"
# Fixed-input timing then independent prediction parity
.venv/bin/python scripts/run_linear_mpc_codriver.py benchmark --horizon 8 --name timing_benchmark --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py parity --horizon 8 --name model_parity --output "$OUT"
# Export selected settings before generating N8 workload summaries
cp results/linear_mpc_codriver/selected_configuration.json "$OUT/selected_configuration.json"
# Audits, plots and tables after timing experiments
.venv/bin/python scripts/run_linear_mpc_codriver.py audit --output "$OUT"
.venv/bin/python scripts/run_linear_mpc_codriver.py analyze --output "$OUT"
# Regression, lint and formatting (after timing)
.venv/bin/python -m pytest -q
.venv/bin/ruff check src scripts tests
.venv/bin/ruff format --check src scripts tests
```

`analyze` regenerates `docs/LINEAR_MPC_CODRIVER_RESULTS.md` from the chosen output and
writes plots/CSV/JSON there. To restore the published results document, rerun analysis with
`--output results/linear_mpc_codriver`. Auditing/analysis do not overwrite per-case raw logs.
For a historical source reproduction, the measured implementation is preserved under
`results/linear_mpc_codriver/benchmark_sources/`; final source has one additional nonfinite
residual rejection guard. Fresh host timing is never expected to reproduce byte-for-byte.
