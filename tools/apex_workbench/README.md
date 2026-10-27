# APEX Workbench V0.1

Local engineering tooling: choose an existing experiment, edit supported inputs, predict,
run real APEX code, inspect retained results, and save your explanation. This workstream is
separately authorized from the earlier Workbench/VIS-2 deferral. It changes no canonical model,
controller, profile, scientific exporter, or historical evidence. Delivery status:
**WORK_COMPLETE_PENDING_REVIEW**, not formal verification or scientific acceptance.

## Setup and launch

From the repository root, using Python 3.12 and the existing core environment:

```sh
.venv/bin/python -m venv tools/apex_workbench/.venv
uv pip freeze --python .venv/bin/python | rg -v '^-e ' > /tmp/apex-workbench-pins.txt
uv pip install --python tools/apex_workbench/.venv/bin/python -e . \
  -r tools/apex_workbench/requirements.txt --constraint /tmp/apex-workbench-pins.txt
tools/apex_workbench/.venv/bin/python -m streamlit run tools/apex_workbench/app.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true \
  --browser.gatherUsageStats false
```

Open <http://127.0.0.1:8501>. The pins preserve the installed scientific dependency versions;
Workbench dependencies live in its ignored `.venv`, outside the core environment. If dependencies
are already installed, only the last command is needed. `uv` cache/network access must be available.
Install pytest in this tool environment to run the focused tests. See [validation](VALIDATION.md)
for the exact checked environment and evidence. No cloud deployment or authentication is included;
keep the server bound to loopback.

## Supported experiments

- **Dynamic bicycle / open loop:** the unmodified Task004 CLI `main()`; duration and RK4 timestep.
  The original synthetic vehicle, track, initial state, steering and acceleration schedule remain fixed.
- **LQR/PI / tracking:** the unmodified Task005 `run_case()`; duration, circle/oval track,
  initial/reference speed, initial lateral error and heading error. Duration-only termination,
  fixed 200 Hz plant / 100 Hz control, original weights/gains and PI constants.

The [capability matrix](CAPABILITY_MATRIX.md) records sources, SI units, bounds, validation,
provenance and deferred features. Every bound beyond an existing mathematical contract is labeled
as a conservative UI/resource safeguard. These ranges are not certified physical validity domains.
Parameters are synthetic, never measured or identified APEX data. Linear tires remain unsaturated;
`mu` is diagnostic. Dynamic `a_cmd` means `Fx/m`, not generally `dvx/dt`.

## Use

1. Select an experiment in the sidebar and enter supported inputs with units.
2. Write **My prediction**, then press **Run experiment**.
3. Inspect status, XY trajectory, states, actual/reference channels where available, and controls.
4. Read metadata, summaries, stdout/stderr and numerical environment in **Evidence & logs**.
5. Save **My observation** and **My explanation** in **Learning notes**.
6. Select retained runs later, download a ZIP, or overlay two completed runs of the same adapter
   in **Compare runs**. Overlays use raw elapsed simulation time without interpolation.

Failed, timed-out and cancelled runs stay visible. A `completed` execution means the original
entry point returned successfully; review boundary violations, model failures and summary criteria
separately. Short runs may have null settled metrics. The dynamic demo does not export boundary
violation flags or reference states. Solver status/computation times, application staleness,
latency/deadlines and optimizer constraints are unavailable here and are explicitly labeled so.
Host wall runtime is process overhead plus computation, not modeled control delay.

## Execution and evidence

Every run exclusively reserves `results/apex_workbench/<UTC timestamp>_<random id>/` before launch.
Original experiment outputs live in `experiment/`; preexisting output directories are rejected.
The request records source/effective configuration, notes, adapter/version/entry point, model,
controller, full synthetic vehicle YAML, timing mode, Git revision/branch/status/diff hash,
source hashes, Python and package versions. Worker environment controls and loaded native pool
inspection are retained separately. Final artifact SHA256/size manifest links the produced files.
Observations/explanations are append-only note versions; the original prediction is preserved.
Do not manually edit run evidence or delete the execution lock file while workers are running.

The supervisor persists independently of browser reruns/closure. Cancellation terminates only its
own scientific worker process group; partial files and logs remain. One inherited `flock` per
checkout serializes Workbench runs across sessions and application instances. Repository
`MEASURED_ACTIVE` / `D3_ACTIVE` guards and a 1 GiB disk floor are checked before launch. This lock
cannot serialize unrelated direct experiment launches: do not start external measurements while
Workbench runs. These are synthetic functional simulations, not timing benchmarks.

Limits: 60 s wall supervision, 30 s soft / 31 s hard kernel CPU, 16 MiB kernel per-file limit,
512 MiB sampled worker RSS and 64 MiB sampled output budget. RSS/output/thread observations at
100 ms are soft samples, not exact peak bounds. Single native thread controls are configured
before numerical imports; macOS uses the existing Accelerate API. Loaded pools and sampled
process thread counts are recorded; environment values or thread counts do not prove parallel
numerical execution. Unexpected supervisor/host termination is not hardware watchdog protection.
No standstill braking, collision safety or real-time certification is implied.

## Engineering Understanding Notes

`app.py` submits only the selected adapter's allowlisted values. `configuration.py` rejects
unknown, nonfinite or out-of-range values and invalid LQR step multiples. `jobs.py` reserves an
exclusive run directory, captures source identity, holds the execution lock, and starts a fresh
supervisor/worker with explicit argument arrays and no shell interpolation. `worker.py` applies
resource/native controls and calls the original Task004 CLI or Task005 function.

The original experiment composes the actual `DynamicBicycle`, original tire/load components,
canonical RK4 integration, track geometry and (for Task005) scheduled LQR/PI plus
`SimulationRunner`. The controller's linear design stays separate from the nonlinear plant.
The Workbench contains no vehicle/tire/controller/integration/solver equations. Derived display
coordinates call the canonical Frenet API after execution. `plots.py` reads the retained CSVs;
no missing telemetry is invented. Learning notes then close the experiment loop without supplying
an AI explanation.

## Later work, requiring bounded review

- A model-composition adapter for synthetic vehicle/initial/input overrides, with original-API
  parity and coupled parameter validation (including wheelbase consistency).
- Explicit selection of existing kinematic and smooth combined-grip compositions; no hidden swap.
- Separately bounded NMPC/async adapters after their prerequisite gates, with zero/injected/measured
  latency, continuing plant motion, application staleness, fixed deadlines and failure retention.
- Comparison eligibility by track, source identity, timing and model as well as adapter; exported
  comparison reports and curated learning experiments.
- Formal verification of the reviewed delivery revision. VIS package ingestion, VIS-2 unseen tracks,
  frozen Performance changes, Efficiency execution and physical vehicle identification remain separate.
