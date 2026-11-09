# APEX Pi compute benchmark v0

Exploratory computational benchmark, ready for Pi 4/5 hardware testing. No ROS,
hardware IO, motor control, tuning, physical Safety or real-time qualification.

Use **64-bit Raspberry Pi OS / Linux and 64-bit Docker** on both boards. Copy this
whole folder; no checkout, Git, display, external Planning package or Python install
is needed on the Pi. Build once and transfer the same image for the closest comparison.

## Build and run

From this folder, after Docker is installed and running:

```sh
docker buildx build --platform linux/arm64 --load -t apex-pi-compute:v0 .
./run.sh
```

The default is **three 2-second synthetic windows**, one fresh process per window.
The run is serial, with a 180-second wall-time cap per process including setup.
Each invocation creates a new `results/run-*` folder and never overwrites a run.
Exit 0 means all requested windows completed without controller failure/fallback;
exit 2 means failure/incompletion. Preserve both outcomes. There are no automatic retries.

Explicit bounded repetitions (1–5; same scenarios/settings, no tuning):

```sh
./run.sh --repetitions 3
```

Optional `--timeout-seconds 300` changes only the process watchdog (10–600 seconds).
`./run.sh --self-check` performs one real startup solve and one TVLQR update.
The Docker build already executes that check and fails if pinned ARM64 IPOPT is unusable.

## Copy the identical image to both Pis

On the build machine:

```sh
mkdir -p results
docker save apex-pi-compute:v0 | gzip > results/apex-pi-compute-v0-arm64.tar.gz
```

Copy this folder and that archive to each Pi (for example with a USB drive or `scp`).
On **each** Pi, from its copied folder:

```sh
gzip -dc results/apex-pi-compute-v0-arm64.tar.gz | docker load
./run.sh
```

The launcher records the Docker image ID in `host.txt`; require matching IDs for
the comparison. It disables container networking, makes the container filesystem
read-only and mounts only this folder's `results/` for writing. Docker access must
already work for the invoking user. Run one benchmark at a time on an otherwise
idle board; use the same cooling, power supply policy, OS, governor and repetition
count, and retain those details with the results. The script does not change them.

## Controller and scenarios

`source_manifest.json` binds every copied source/configuration file to exact Git
bytes at `48adbdf64d492592d15e23c917aca71fa58aa8a5`. Composition follows the
profile loader in producer `e577f2c00bde2092f6bd1bd403b72aa9ca10713a`;
the PRE-INT-W1 runtime/evidence driver is not invoked. Original manifest status text
is preserved as historical source content. The current Primary instruction supplies
authorization for this benchmark.

Architecture A; NMPC N=8, dt=0.1 s, RK4×4; combined-grip dynamic model; gamma-2
synthetic Grand Prix Planning reference; TVLQR at 100 Hz; original solver options,
costs and primal-shift warm start. Python **3.12.14**, CasADi **3.8.1**, NumPy
**2.5.3**, SciPy **1.18.1**, pandas **3.0.6**, PyYAML **6.0.3**, psutil **7.2.2**,
threadpoolctl **3.7.0**. `requirements.lock` is a hash-checked wheel-only subset of
the copied original `uv.lock`, including dateutil/six. No solver/version fallback.
The ARM64 Python base image is pinned by digest. Build needs registry/PyPI access;
running a loaded image is offline. Use one saved image to avoid rebuild differences.

`scenarios.json` freezes geometry-ranked, model-valid reference starts:

| Window | Track progress (m) | Track curvature (1/m) |
|---|---:|---:|
| Straight | 13.2468719495 | -0.0000051108 |
| High curvature | 23.8443695091 | -1.0928787490 |
| Curvature transition | 24.0943104893 | -0.8195433557 |

The file records selection rules, serialized row indices, gradients, full reference
channels, canonical six-state vectors and validation controls. A reference-valid
start does not guarantee successful optimization, closed-loop completion or a
dynamically realizable reference. Failures are retained without choosing easier starts.

## Timing and evidence

Actual compute measurements are separate from synthetic simulation time. The
unchanged asynchronous runner uses measured preparation and tracker+validation
durations as **synthetic availability intervals**. Held-input plant integration
continues through those intervals, at steps ≤5 ms, while valid TVLQR authority is
available; planner busy ticks, command staleness and skipped tracker ticks are
retained in `raw_simulation.json`. This serial discrete-event harness is not
concurrent onboard execution or a wall-clock paced simulator. There is no injected
actuator, sensor, network or ROS delay. Startup is measured separately before
synthetic motion, with the existing prepositioned-command convention.

- `summary.json`, `timing_summary.csv`: count, mean, median, p95, p99, maximum and
  strict `>` exceedance proportions for 100 ms planning and 10 ms tracking. Separate
  startup/recurring and cold/warm populations. Linear interpolated empirical quantiles.
  TVLQR update, command validation and total validated/applied trajectory-control
  timings are separate populations; the latter contains only requests applied
  before the window ends. Consult pending-at-end and failures for censored requests.
- Each window's `plans.json` / `plans.csv`: release and plan IDs, source progress,
  IPOPT duration/iterations/status/infeasibility, slack, warm-start flag, prediction,
  gains and full preparation timing. Raw solver statistics survive gain/packet failure.
  Solver success, controller validation and packet preparation are distinct. Slack
  is null when the original controller cannot provide an accepted solution.
- `tracker.json` / `tracker.csv`: actual TVLQR updates, distinct from the runner's
  command-validation timing. Predictor-clone updates are not mixed into this population.
- `raw_simulation.json`: existing states, controls, releases, handoffs, misses,
  fallback, failures, stop reason, pending-at-end status. `plant_steps.json` records
  plant-step timings separately. Full-loop time also includes geometry, diagnostics
  and in-memory recorder work; it is not controller time.
- `run_configuration.json`, `resolved_configuration.json`: source and harness hashes,
  scenario/configuration snapshots and machine identity. Worker summaries separate
  numerical construction, loop wall time, process CPU time and plant-step time.
- `resource_samples.json`, `supervisor.json`: external 20 ms sampling of worker RSS,
  per-thread CPU counters, process thread counts and readable sysfs temperatures.
  Peak **sampled** memory can miss short peaks. A separate supervisor process performs
  sampling; its CPU time is reported separately from worker/child CPU time.
- `host.txt`: host model/CPU/OS, governor, initial temperatures, image ID and
  `vcgencmd measure_temp/get_throttled` before/after when installed and permitted.
  Missing telemetry is unknown. Container kernel/CPU identity can differ from the host
  on Docker Desktop; only measurements on an actual Pi describe that board.
- `progress.jsonl` / `worker.log`: incremental preparation boundaries and outcomes.
  A timeout/crash retains partial evidence and reports an incomplete case; missing
  calls are never fabricated. `RUNNING` without `FINISHED` marks supervisor interruption.

One numerical thread is requested **before imports in fresh processes**, with
supported threadpoolctl limits also applied. Loaded backend identities and thread
pool counts are recorded before/after; a detected pool count other than one fails
the window. Per-thread CPU observations describe sampled activity, not exact
instantaneous parallelism. Environment variables alone are not execution evidence.
Lightweight in-memory wrappers surround unchanged methods; file logging, monitoring,
plant integration and setup are outside solve and tracker timers. The preparation
timer includes a small solver-statistics copy. Wrapper time and native timer time
are both retained; instrumentation is not claimed to have zero overhead.

Sampled maxima are **not WCET**. Exceedance proportions are descriptive and do not
establish guaranteed real-time performance, physical Safety or deployment readiness.

## Validation and limits

See `VALIDATION.md` for executed checks and retained local outcomes. Pi 4/5 access is
required to establish board timings, memory/thermal/throttling behavior and CPU/thread
observations on those boards. No Pi timings are supplied by this package.

Focused packaging/evidence tests (no scientific Verification campaign):

```sh
docker run --rm --platform linux/arm64 --entrypoint python apex-pi-compute:v0 -m unittest -v test_package
```

**STOP: PI COMPUTATIONAL BENCHMARK PACKAGE READY FOR HARDWARE TESTING.**
