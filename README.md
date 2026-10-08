# APEX / Defensive Racing AI

A simulation-first 1/10-scale autonomous racing research platform. **Task 004 implements
dynamic CG bicycle propagation with linear axle tires and provisional longitudinal load
transfer.** Kinematics remain available separately. Controllers and generic simulation
orchestration remain future work; physical vehicle parameters are not identified.
No ROS, Docker, Gymnasium, or RL framework is required.

## Development on macOS

Install uv if needed using `brew install uv`, then from this repository:

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked python -c "import apex, casadi; print(apex.__file__); print(casadi.__version__)"
```

`.python-version` selects Python 3.12; uv can provision it. `pyproject.toml` permits
Python 3.12–3.14. `uv run` uses the environment without shell activation.

## Layout

- `src/apex`: independent model, track, estimation, identification, planning,
  control, optimization, simulation, logging, and utility packages.
- `configs`: YAML templates; all generic vehicle physics values are intentionally null.
- `tests`: unit, model/track integration, and geometry/kinematic regression tests.
- `docs`: architecture, frozen conventions, roadmap, decisions, and engineering handoff.
- `scripts`, `notebooks`, `results`: future experiments, exploration, and generated output.

```python
from apex.config import load_vehicle_parameters
from apex.state import StateIndex, state_vector

vehicle = load_vehicle_parameters("configs/vehicles/generic_1_10_racecar.yaml")
state = state_vector([0, 0, 0, 0, 0, 0])
assert state[StateIndex.S_ABS] == 0
# vehicle.validate_for_simulation() raises: the template has no measured values.
```

Read [architecture](docs/APEX_ARCHITECTURE.md), [state definitions](docs/STATE_DEFINITIONS.md),
[coordinate conventions](docs/COORDINATE_FRAMES.md), [roadmap](docs/PROJECT_ROADMAP.md),
and [handoff](docs/CODEX_HANDOFF.md) before implementing the next phase.

## Track geometry

Read [TRACK_MODEL_SPEC.md](docs/TRACK_MODEL_SPEC.md) before supplying track data.
CSV input requires ordered x,y columns in metres. The first waypoint is progress zero;
widths are explicit, independent left/right half-widths.

```python
from apex.track import load_track_csv
from apex.coordinates.frenet import frenet_to_global, project_pose

# User-provided CSV and measured widths are required for a physical circuit.
# track = load_track_csv("track.csv", left_width=measured_left, right_width=measured_right)
```

Run the explicitly synthetic demonstration without opening a GUI:

```sh
uv run --locked python scripts/plot_track_geometry.py --save results/track_geometry.png
uv run --locked pytest -q -s tests/regression/test_geometry_accuracy.py
```

## Scripted kinematic demonstration

Read [KINEMATIC_BICYCLE_SPEC.md](docs/KINEMATIC_BICYCLE_SPEC.md). Only four state channels
are independently propagated; vy/r are reconstructed from vx and instantaneous steering.
All demo vehicle/track values are synthetic, NOT identified or representative of APEX.
The main generic vehicle template remains unpopulated.

```sh
uv run --locked python scripts/run_kinematic_demo.py
uv run --locked pytest -q -s tests/unit/test_kinematic.py tests/integration/test_kinematic_track.py tests/regression/test_kinematic_accuracy.py
```

The demo writes states.csv, summary.json and trajectory.png to results/kinematic_demo/.
Use --duration, --dt, --output-dir or --no-plot to change execution/output settings.
No feedback controller is used.

## Dynamic bicycle and comparison

Read [DYNAMIC_BICYCLE_SPEC.md](docs/DYNAMIC_BICYCLE_SPEC.md) and
[LINEAR_TIRE_SPEC.md](docs/LINEAR_TIRE_SPEC.md). The dynamic model propagates vy/r and
uses a_cmd=Fx/m, not the kinematic input interpretation. Linear forces are unsaturated;
mu is diagnostic only. All supplied dynamic vehicle values are explicitly synthetic.

```sh
uv run --locked python scripts/run_dynamic_bicycle_demo.py
uv run --locked python scripts/compare_bicycle_models.py
uv run --locked pytest -q -s tests/unit/test_dynamic_components.py tests/unit/test_dynamic_bicycle.py tests/integration/test_dynamic_track.py tests/regression/test_dynamic_accuracy.py
```

Results are saved under results/dynamic_demo/ and results/bicycle_comparison/ as CSV,
JSON summaries and headless plots. No feedback controller or automatic model switch exists.

## Autonomous baseline (Task 005)

Curvature feedforward + scheduled LQR + PI now controls the unchanged nonlinear dynamic
plant. Synthetic settings: 1–3 m/s, 100 Hz control / 200 Hz plant, perfect state feedback.
See [LQR baseline specification](docs/LQR_BASELINE_SPEC.md) for mathematics and limitations.

```sh
.venv/bin/pytest -q tests/unit/test_baseline.py tests/unit/test_runner.py tests/integration/test_baseline_tracking.py
XDG_CACHE_HOME=/private/tmp/apex-cache MPLCONFIGDIR=/private/tmp/apex-matplotlib .venv/bin/python scripts/run_lqr_baseline.py --suite
```

Results are in `results/lqr_baseline/`: per-case states.csv, controls.csv, summary.json
and baseline.png, plus suite_summary.json and linear_analysis.json. The suite includes
two laps on circle/oval at 1/2/3 m/s, all requested disturbances and a varying speed profile.
These are development benchmarks, not physical APEX validation or constrained-control guarantees.

## Constrained tracking NMPC and latency (Task 006)

Independent CasADi prediction + direct multiple shooting + IPOPT now runs against the
unchanged NumPy plant. Explicit zero/measured/injected timing modes keep the previous
command active while physical time advances during solving. Missed fixed releases and
application-state staleness are logged. See docs/NMPC_BASELINE_SPEC.md.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/check_mpc_parity.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 XDG_CACHE_HOME=/private/tmp/apex-cache MPLCONFIGDIR=/private/tmp/apex-matplotlib .venv/bin/python scripts/run_mpc_baseline.py --suite all
```

Results: results/mpc_baseline. Measured timing depends on host/load; deterministic injected
latency is the reproducible timing benchmark. No racing objective or latency compensation.

## Task 006.1 — smooth combined grip

Racing-development experiments now select matched NumPy/CasADi bounded axle tire forces,
with explicit normal-load proportional longitudinal allocation. Linear tires remain a
selectable reference. See [grip specification](docs/GRIP_LIMITED_TIRE_SPEC.md) and
[handoff](docs/CODEX_HANDOFF.md). Physical parameters remain synthetic/unknown as labeled.

```sh
.venv/bin/python scripts/analyze_tire_model.py
.venv/bin/python scripts/compare_tire_models.py
.venv/bin/python scripts/check_grip_parity.py
.venv/bin/python scripts/run_grip_regression.py --case all
```

New results use `results/tire_model` and `results/mpc_grip`, preserving Task006 logs.
Task006.2 synchronous NMPC characterization is complete; see
[parameter study](docs/NMPC_PARAMETER_STUDY.md),
[measured tables](docs/NMPC_PARAMETER_STUDY_RESULTS.md) and
[selected configurations](results/mpc_parameter_study/selected_candidates.json).

## Task 006.3 — asynchronous planner and 100 Hz codriver

Candidate C now supplies timestamped trajectories to an independent TVLQR/P codriver.
The physical plant keeps moving under high-rate feedback while the next plan is computed.
See the [architecture specification](docs/ASYNC_PLANNER_CODRIVER_SPEC.md),
[measured results](docs/ASYNC_PLANNER_CODRIVER_RESULTS.md), and
[experiment artifacts](results/asynchronous_planner_tracker).

```sh
.venv/bin/python scripts/run_async_planner_tracker.py run --name my_async_run
.venv/bin/python scripts/run_async_planner_tracker.py suite --output /private/tmp/apex-async-new
.venv/bin/python scripts/run_async_planner_tracker.py audit
.venv/bin/python scripts/run_async_planner_tracker.py analyze
```

Run timing experiments sequentially, without tests or analysis competing for CPU.
Use fresh names/output directories: existing measurements are retained.
Task 006.4 is complete: 26 cases compare small lateral MPC with TVLQR; retain TVLQR.
See [study](docs/LINEAR_MPC_CODRIVER_STUDY.md), [results](docs/LINEAR_MPC_CODRIVER_RESULTS.md)
and [reproduction commands](docs/LINEAR_MPC_REPRODUCTION.md).
Task 007B adds optional terminal progress; adaptive codriver switching remains deferred.

## Task 007A — offline racing-reference integration

Planning owns the offline racing line and velocity profile. A separate temporary synthetic
generator creates the Grand Prix fixture under `configs/planning/synthetic_grand_prix_v1`.
Runtime APEX loads and validates that serialized reference, remains active at 10 Hz and supplies
the unchanged 100 Hz TVLQR codriver. No adaptive switching or near-limit tuning is included.
See [interface specification](docs/TASK007A_RACING_REFERENCE_INTERFACE.md).

## Task 007B — progress seeking and aggressive nominal references

The offline line remains unchanged. Separate packages scale only nominal speed, while APEX
may adapt the request through its existing constrained dynamics. Progress reward defaults to
zero. The study selects lambda=2 only for the conservative gamma=1 experiment; aggressive
progress cases expose oscillation and margin-slack limitations. TVLQR remains unchanged.

See the [study specification](docs/TASK007B_PROGRESS_SEEKING_RACING.md),
[measured results](docs/TASK007B_RESULTS.md), [reproduction](docs/TASK007B_REPRODUCTION.md),
and [review artifacts](results/task007b).
