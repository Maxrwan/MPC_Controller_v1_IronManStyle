# APEX Workbench V0.2 — Vehicle Dynamics Laboratory WORK

V0.2-C corrects the independent review findings and prepares the accepted numerical protocol.
See [closure, software tests and review stage](../../docs/apex_workbench_v0_2_c/WORK.md).
The campaign remains **pending separate execution authorization**. Preparing or printing its plan
does not qualify the lab or establish physical validity.

**WORK_COMPLETE_PENDING_REVIEW.** Adds the finite `dynamic_lab` adapter under the accepted
[V0.2-A2 contract](../../docs/apex_workbench_v0_2_a/PROPOSED_CASES.md) at
`0cc7e4f626311aec05977bd3beda40c346fa4214`. See the
[implementation evidence, focused tests and remaining gates](../../docs/apex_workbench_v0_2_b/WORK.md).
Numerical qualification has not run. Provisional sampled teaching filters do not validate vehicle
physics, numerical error bounds or actuator feasibility. The 17-trajectory campaign and formal
Verification require separate authorization.

Local engineering tooling: choose an existing experiment, edit supported inputs, predict,
run real APEX code, inspect retained results, and save your explanation. This workstream is
separately authorized from the earlier Workbench/VIS-2 deferral. It changes no canonical model,
controller, profile, scientific exporter, or historical evidence. Historical V0.1 delivery status:
**V0.1_VERIFIED_PENDING_USER_ACCEPTANCE**. Its functional Verification on
`77d018b11bbbfc39ab81d98c9bef70e90ab82725`: **855 passed, 17 separately gated G2 tests skipped**.
See the [final review](../../docs/reviews/apex_workbench_v0_1_stabilization/REVIEW.md) and
[Verification scope/limits](../../docs/reviews/apex_workbench_v0_1_stabilization/VERIFICATION.md).

R1–R6 corrective WORK uses record version 2. See [correction scope and evidence](CORRECTIONS.md).
The original [failed Engineering Review](../../docs/reviews/apex_workbench_v0_1/REVIEW.md)
remains preserved. The stabilized revision has passed separate-context technical review and
functional Verification; user/scientific acceptance remains separate.
The [delegated stabilization record](STABILIZATION.md) covers subsequent metadata/missing-evidence
corrections and their revision-specific review status.

## Setup and launch

On this configured Mac, double-click
[Launch_APEX_Workbench.command](../../Launch_APEX_Workbench.command) in the repository root.
It starts the local server and opens your default browser when ready. When starting a new server,
keep that Terminal window open; press **Control-C** there to stop it. The launcher works regardless
of Terminal's current folder and does not run an experiment automatically. A second double-click
reopens this project's already-running Workbench without starting another server. A listener
belonging to another application or checkout produces a clear port-conflict message.

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

- **Vehicle Dynamics Laboratory / prescribed open loop:** canonical `DynamicBicycle` with default
  linear axle tires/quasi-static loads, fixed existing track and canonical `SimulationRunner`.
  Select `VDL1_BASE`, `VDL1_IZ_HIGH`, `VDL1_STEER_HIGH`, `VDL1_CF_HIGH` or `VDL1_CR_HIGH`.
  Every case shows its full SI parameter snapshot, initial state and held-input schedule. All use
  [2,0,0,0,0,0], a_cmd=0, a steering step at 0.100 s, duration 0.500 s and plant/input period 0.005 s.
  The four treatments independently change Iz, steering amplitude, Cf or Cr. See
  [exact values/origins](../../docs/apex_workbench_v0_2_a/PROPOSED_CASES.md). There is no arbitrary
  parameter editor or mass family. The UI admits the nominal grid. The backend admits the accepted
  refinements only with explicit qualification purpose; software-test profiles are ineligible for
  scientific qualification evidence.
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

Lab comparisons allow BASE against one of the four treatments in either order. They show a
**Controlled candidate** only after checking full resolved snapshots, actual applied controls,
initial state, schemas/units, source identity, environment, geometry and evidence. Other verified
pairs are illustrative; corrupt/incomplete records are invalid. The UI never promotes completed
runs into a qualified synthetic comparison. Observed yaw separation is displayed with numerical
qualification still unavailable, even when it exceeds the provisional minimum signal floor.
After a separately authorized campaign, an optional qualification record can be selected. It is
revalidated against all referenced runs, source/environment and exact finite-case exports before
showing numerical case status and pair eligibility. Sampled interpretation, excitation and physical
validity stay separate; records are never silently attached to or written into old run evidence.

Lab state/control and canonical sample-diagnostic plots show actual retained yaw/lateral/longitudinal
response, steering/a_cmd, slip, lateral forces, axle loads, nominal/effective stiffness, utilization,
Frenet denominator, XY and sampled CG corridor flags. Terminal input/diagnostics are informational.
Configuration, execution, evidence, numerical qualification, model window, excitation and comparison
remain distinct. Missing observations are unavailable, never fabricated. The lab does not hold vx
constant when a_cmd=0 and introduces no steering actuator or feedback law.

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
Malformed request/status records are preserved and excluded with a warning. Selected completed records
are revalidated before metadata or plots appear. Missing manifest-listed files are integrity failures;
successful corrected runs also require their expected exports. Optional channels never produced by
an adapter remain unavailable. A failed run with no exports keeps its failure/error visible.
Unreadable lifecycle records block new admission until inspected; exclusion from UI selection does
not authorize another worker. No historical record is automatically repaired or deleted.

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
For `dynamic_lab`, the worker checks source/captured composition before and after execution, constructs
immutable canonical parameters and calls the canonical runner. Its raw CSVs precede diagnostic export;
`resolved_lab.json`, controls, diagnostics, telemetry units and summaries join the existing manifest.
Every required lab artifact is verified before scientific display, including a state-only plot.

The original experiment composes the actual `DynamicBicycle`, original tire/load components,
canonical RK4 integration, track geometry and (for Task005) scheduled LQR/PI plus
`SimulationRunner`. The controller's linear design stays separate from the nonlinear plant.
`lifecycle.py` owns the worker lease/identity checks; `storage.py` publishes records and verifies
selected artifacts; `comparison.py` classifies compatibility. Lab modules add the accepted finite
composition and sampled reporting, with no new simulation or analysis framework. The Workbench
contains no vehicle/tire/controller/integration/solver equations. Derived display
coordinates call the canonical Frenet API after execution. `plots.py` reads the retained CSVs;
no missing telemetry is invented. Learning notes then close the experiment loop without supplying
an AI explanation.

## Later work, requiring bounded review

- Numerical qualification of the accepted lab cases, refinement admission/retained qualification
  records and exact-SHA Engineering Review/Verification; no auto-qualification from WORK smoke runs.
- Further finite synthetic mass/initial/input cases after reviewed numerical contracts; no
  unrestricted slider ranges or invented parameter coupling.
- Explicit selection of existing kinematic and smooth combined-grip compositions; no hidden swap.
- Separately bounded NMPC/async adapters after their prerequisite gates, with zero/injected/measured
  latency, continuing plant motion, application staleness, fixed deadlines and failure retention.
- Exported comparison reports and curated learning experiments.
- Review/Verification of later implementation revisions. VIS package ingestion, VIS-2 unseen tracks,
  frozen Performance changes, Efficiency execution and physical vehicle identification remain separate.
