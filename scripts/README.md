# Geometry visualization

`plot_track_geometry.py` plots centerline, independent left/right boundaries, and left
normals. Without --csv it uses a clearly synthetic radius-5-m circle with demonstration
half-widths 0.6/0.9 m. It does not choose physical track dimensions for the project.

```sh
uv run --locked python scripts/plot_track_geometry.py --save results/track_geometry.png
uv run --locked python scripts/plot_track_geometry.py --csv /path/to/track.csv --left-width 0.6 --right-width 0.9 --save results/user_track.png
```

The second command's widths are examples: substitute measured/approved values.
`--save` selects Matplotlib's Agg backend. Omit it only when an interactive plot is desired.

## Scripted kinematic propagation

`run_kinematic_demo.py` uses the clearly labelled synthetic vehicle YAML and a synthetic
closed circle. Steering is fixed and acceleration is a predetermined function of time.
It never feeds state error back into the commands. Defaults: 10 s duration, dt=0.01 s.
Writes states.csv, summary.json and trajectory.png under results/kinematic_demo/.
Use --no-plot to omit the figure; plotting always uses a headless backend.

## Task 004 dynamic scripts

run_dynamic_bicycle_demo.py produces a synthetic 10 s cornering/acceleration/braking
sequence at dt=0.005 s. Controls are predetermined. --duration, --dt, --output-dir and
--no-plot configure the run. Default outputs: results/dynamic_demo/{states.csv,summary.json,
dynamic_demo.png}. Rows log the state and command applied starting at that timestamp;
final-row commands are informational because no following interval is simulated.

compare_bicycle_models.py runs a fixed 4 s low-slip comparison from identical initial
states and inputs (delta=0.02 rad, a_cmd=0). It shares synthetic scenario helpers with the
dynamic demo script. Outputs: results/bicycle_comparison/{dynamic.csv,kinematic.csv,
summary.json,comparison.png}. Input semantics and lateral physics differ; equality is not expected.

`run_lqr_baseline.py --suite` runs Task 005 nonlinear-plant closed-loop validation and saves
per-case CSVs, summaries and eight-panel headless plots under results/lqr_baseline.
Use `--track circle|oval --speed 2 --laps 2` for a single case; `--no-plots` skips plotting.
The duration defaults to an 80-second safety cap. All cases use synthetic geometry/parameters.

Task 006: check_mpc_parity.py verifies independent symbolic/NumPy equations and RK4.
run_mpc_baseline.py supports --suite zero|latency|comparisons|disturbances|speeds|all,
--mode zero|injected|measured, --latency-ms, and --plots-only. Set writable Matplotlib cache
and single-thread BLAS/OpenMP as in the handoff for reproducible development conditions.
Each result includes independent plant, applied-control, solver-event and prediction logs.

## Task006.1

- analyze_tire_model.py: fixed-load force-slip/utilization and load-transfer tables.
- compare_tire_models.py: scripted vehicle comparisons and radius-demand snapshots.
- check_grip_parity.py: independent NumPy/CasADi force, derivative and RK4 parity.
- run_grip_regression.py --case all: circle/oval, combined disturbance,45ms latency,
  then timing/evaluation/sparsity report. --case timing reuses saved runs for reporting.
- run_mpc_baseline.py now defaults to matched smooth-grip models and results/mpc_grip;
  --tire-model linear explicitly restores reference physics. Do not overwrite archived
  Task006 output when comparing timing. --tire-config accepts a model-selection YAML.
- audit_mpc_results.py --output results/mpc_grip audits physical clocks and grip utilization.

All timings are host dependent; no Task006.2 optimization is implemented.
