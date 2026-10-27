# APEX Workbench V0.1

Local engineering tooling: choose an existing experiment, edit supported inputs, predict,
run real APEX code, inspect retained results, and save your explanation. This workstream is
separately authorized from the earlier Workbench/VIS-2 deferral. It changes no canonical model,
controller, profile, scientific exporter, or historical evidence. Delivery status:
**WORK_COMPLETE_PENDING_REVIEW**, not formal verification or scientific acceptance.

R1–R6 corrective WORK uses record version 2. See [correction scope and evidence](CORRECTIONS.md).
The original [failed Engineering Review](../../docs/reviews/apex_workbench_v0_1/REVIEW.md)
remains preserved; the corrected revision still requires a new Engineering Review.

## Setup and launch

On this configured Mac, double-click
[Launch_APEX_Workbench.command](../../Launch_APEX_Workbench.command) in the repository root.
It starts the local server and opens your default browser when ready. Keep the Terminal window
open while using Workbench; press **Control-C** there to stop it. The launcher works regardless
of Terminal's current folder and does not run an experiment automatically.

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
   in **Compare runs**. Eligibility is controlled, illustrative, or invalid. Scientific source,
   composition, geometry, timing, numerical environment and telemetry contracts are compared;
   varied inputs and differences are shown. Documentation-only Git revision differences do not
   exclude an otherwise controlled comparison. Overlays use raw time without interpolation.

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
inspection are retained separately. The immutable execution receipt records the scientific outcome.
Status records evidence validity separately and commits the manifest hash only after all stable
artifacts have been hashed. A hash/finalization failure is visible as `evidence_failed`, even
when scientific execution completed. Interrupted finalization is reconciled conservatively.
Observations/explanations are append-only note versions; the original prediction is preserved.
Do not manually edit run evidence or delete the execution lock file while workers are running.

The supervisor persists independently of browser reruns/closure. The scientific worker also
inherits the checkout execution lock and runs its own guard. Supervisor loss, cancellation,
wall/RSS/output limits and monitoring faults are checked by that guard; it stops its own process
without signalling a stored PID. Supervisor termination actions verify worker birth time, full
command, role and run path through psutil. A second worker cannot start while the first retains
the lease, including when the supervisor has been killed. Stale corrected records are reconciled
under the same lock; interrupted/uncertain outcomes are never promoted to success.

Initial request/status publish together through a hidden staging directory. Notes publish complete
exclusive versions; malformed historical notes are retained and skipped with a warning. Required
artifact hashes are checked before plots or comparison. Only selected files are read, using a
bounded cache keyed by expected hash, inode, size, mtime and ctime; changed data is quarantined.
Historical records are not repaired in place. Legacy runs need their original valid artifact hashes
for individual plots and lack the new comparison contract, so cannot claim a controlled comparison.

Repository `MEASURED_ACTIVE` / `D3_ACTIVE` guards and a 1 GiB disk floor are checked before launch.
The Workbench lease cannot serialize unrelated direct experiment launches: do not start external
measurements while Workbench runs. These are functional simulations, not timing benchmarks.

Limits: 60 s wall supervision, 30 s soft / 31 s hard kernel CPU, 16 MiB kernel per-file limit,
512 MiB sampled worker RSS and 64 MiB sampled output budget. RSS/output/thread observations at
100 ms (supervisor) / 50 ms (worker guard) are soft samples, not exact peak bounds. Single native thread controls are configured
before numerical imports; macOS uses the existing Accelerate API. Loaded pools and sampled
process thread counts are recorded; environment values or thread counts do not prove parallel
numerical execution. The worker guard depends on Python/OS scheduling: SIGSTOP pauses it too, while the inherited
lock still prevents overlapping runs. Host/OS failure is not hardware watchdog protection.
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
`lifecycle.py` owns the worker lease/identity checks; `storage.py` publishes records and verifies
selected artifacts; `comparison.py` classifies compatibility. These modules add no scientific
composition or analysis framework. The Workbench contains no vehicle/tire/controller/integration/solver equations. Derived display
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
