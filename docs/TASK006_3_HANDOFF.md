# Task 006.3 handoff — asynchronous NMPC planner and 100 Hz TVLQR codriver

## Scope and status

Task 006.3 implementation and 21-condition experiment suite are complete. All 435 regression tests pass, along with
all 21 log audits and the final lint/format checks. Task 006.4 and Task 007 are
not implemented. The previous completed handoff is `TASK006_2_2_HANDOFF.md`.
Read `ASYNC_PLANNER_CODRIVER_SPEC.md`, `ASYNC_PLANNER_CODRIVER_RESULTS.md`, and ADRs 107–121.

Candidate C remains the frozen 10 Hz/N=4/0.4 s/four-RK4-substep planner with exact Hessian,
shifted primal warm start, IPOPT warm-start initialization and original Q/R/W/terminal cost.
Native Accelerate SINGLE is selected in fresh sequential workers before numerical imports.
The only prior production-file change is `src/apex/control/mpc/problem.py`: explicit tracker
margin, zero by default and 0.08 m per side in asynchronous cases. No NMPC retuning.

## Ownership and chronology

`src/apex/control/trajectory/` owns packet/buffer, TVLQR, prediction and planner adapter;
`src/apex/simulation/asynchronous.py` coordinates physical events. Planner owns nominal X/U
and gains; buffer owns active physical-time trajectory/reserve; codriver owns local correction;
independent NumPy plant owns physical state. Arrays are copied/read-only and predictor clones
tracker state. Linear X interpolation unwraps heading and retains absolute progress; U/K use ZOH.
Late prefixes and gains are trimmed. No trajectory extrapolation beyond the horizon endpoint.

The plant advances at <=5 ms while the old trajectory is tracked at 100 Hz. Planner preparation
is held unavailable until its physical completion. No overlapping solves; busy fixed releases
are counted separately from codriver misses. Measured runs include full planner and codriver
validation delay. Injected planner experiments use zero simulated codriver latency, but record
measured callback-over-period events. This is event emulation, not OS-concurrency validation.

Lateral error order [e_y,e_psi,vy,r], canonical indices [5,3,1,2]; delta=delta*−K e.
TVLQR linearizes the approved grip model's 10 ms RK4 map (two substeps), extracts A4x4/B4x1,
uses Q=diag(100,100,4,1), R=25, terminal DARE and finite-horizon Riccati on the planner side.
Longitudinal a=a*+1.0(vx*−vx); no integrator. Actuator/grip bounds and 1 rad/s steering slew
are enforced, including actual elapsed application time.

Rolling delay median: last 10 completions, initial 17 ms, clipped to [0,0.30] s. Forecast uses
approved symbolic dynamics and cloned local feedback. Future codriver execution is idealized;
an already in-flight command is not explicitly replayed. Errors are logged rather than hidden.

Startup gates motion and prepositions the first command before a synthetic 2 m/s rolling launch;
standstill is outside the approved dynamic model. Continuity limits in canonical order are
[0.5,0.5,1.0,0.20,0.75,0.15] SI. New plans need >=0.05 s reserve. Reserve categories:
healthy >=0.20 s; warning 0.05–0.20 s; critical >0–0.05 s; exhausted at zero.
Failed solves keep the active plan. Exhaustion latches Task 005 fallback only inside its 1–3 m/s,
in-track domain; otherwise stop. No automatic re-entry. Urgent replanning uses two samples
above 0.05 m lateral or 0.10 rad heading trajectory error and one pending request bit.

## Primary measured comparison

| Architecture | Lateral RMS mm | Heading RMS rad | Speed RMS m/s | Lap times s |
|---|---:|---:|---:|---|
| Synchronous Candidate C | 5.135 | 0.018230 | 0.030158 | 16.281 / 16.179 |
| Async nominal playback | 4.583 | 0.017694 | 0.029218 | 16.251 / 16.178 |
| Async TVLQR | 3.867 | 0.018083 | 0.030168 | 16.250 / 16.174 |

All primary runs: zero boundary violations, solver failures, fallback and planner misses;
async primary codriver misses zero. TVLQR effective rates 9.961/100.012 Hz. Whole-run startup,
margin and latency-accounting differences mean this is not a perfectly isolated tracker test.
Historical synchronous delay includes the backend only; async includes whole preparation.

## Robustness outcomes

| Planner delay ms | TVLQR lateral RMS mm | TVLQR outcome | Sync outcome |
|---:|---:|---|---|
| 0 | 3.549 | two laps | two laps |
| 25 | 3.443 | two laps | two laps |
| 60 | 4.206 | two laps | two laps |
| 100 | 3.641 | two laps | model-validity stop |
| 150 | 3.423 | two laps; 162 planner misses, zero codriver misses | model-validity stop |
| 250 | 15.371 | fallback at 0.517 s, then two laps | model-validity stop |
| 450 | 15.368 | fallback at 0.4 s, then two laps | model-validity stop |

250 ms: initial delay underestimate ages the replacement; next forecast exceeds remaining
active horizon. 450 ms: startup plan expires before the first replacement arrives. Do not
report either as successful continuous planned tracking. No retuning was used to hide the limit.

Isolated 150 ms plan 40 amid 25 ms delays: one planner miss, zero codriver misses, minimum
reserve 0.175 s, 25 ms below warning, no fallback. Isolated failed plan 40: old plan remained
active; next plan recovered, no fallback, minimum reserve 0.20 s.

Perturbation at 5 s: +0.08 m lateral, −0.04 rad heading. One urgent request in both feedback
and playback. Lateral RMS 7.232 versus 7.904 mm. Both reached physical centerline settling
(0.02 m/0.05 rad for one second) after 0.45 s; trajectory settling after 0.03 s partly reflects
reference replacement. Max feedback steering correction 0.04913 rad. No constraint violations.

## Error, reserve and compute evidence

TVLQR trajectory error RMS/p95/max:
- lateral: 0.450/0.510/6.389 mm;
- heading: 0.003539/0.006137/0.036937 rad;
- vy: 0.001886/0.003547/0.029025 m/s;
- yaw rate: 0.026263/0.048367/0.321262 rad/s.

Disturbance max lateral trajectory error 79.996 mm nearly consumes the provisional 80 mm
margin. Nominal data are conservative; there is no robust-invariant safety guarantee.
Measured reserve min/mean/p95: 0.25546/0.34904/0.39442 s; zero time below warning/critical.
Measured accepted handoff max lateral mismatch 0.391 mm, heading 0.01121 rad;
max nominal steering/acceleration jumps 0.09524 rad/0.11715 m/s². Actual steering slew <=1 rad/s.
Completion prediction lateral RMS 0.205 mm, progress RMS 6.985 mm; p95 absolute delay error
4.117 ms. All six components are in separate prediction/handoff CSVs.

Planner total mean/p50/p95/p99/max: 40.877/40.087/44.593/53.972/74.282 ms.
Average solver/preview/forecast/gains: 21.046/4.623/8.931/5.574 ms.
Codriver full mean/p50/p95/p99/max: 1.040/0.969/1.187/1.337/7.058 ms.
Interpolation/feedback kernel mean 0.0635 ms; full time includes command validation.
CPU-core-s/s: planner 0.40713 + codriver 0.10369 = 0.51082. Excludes simulated plant, logging,
transport and OS contention. No Raspberry Pi utilization claim. RSS includes imports/NLP/logs;
numeric packet arrays alone are 2080 bytes, including 1280 bytes of gains, excluding metadata.

Primary measured run had no 10 ms callback exceedances. Injected cases recorded 46: isolated
failure 3, playback disturbance 1, and 250/450 ms fallback cases 34/8. Their physical codriver
latency was deliberately zero, so zero simulated misses do not imply a hard deadline guarantee.
Fallback costs include the existing Task 005 controller and require deployment timing work.
Across all 13 async cases max front/rear tire utilization 0.499994/0.398708, no boundary or model
failure. Synchronous high-delay failures and boundary excursions are retained in the tables.

## Validation and reproducibility

36 focused tests passed, including chronology on the approved plant, NumPy/symbolic Jacobian
consistency, packet/interpolation/heading/progress, rate limits, prediction, failure/exhaustion,
urgent policy, startup gating and gain-failure discard. All 13 async and 8 sync log audits passed.
Full regression: 435 passed in 483.73 s. Final Ruff lint/format passed (169 Python files).
158 scientific plots cover all 14 requested types; primary/error/tire/latency/spike plots reviewed.

Final evidence: `results/asynchronous_planner_tracker/README.md` indexes CSV/JSON/plots,
configuration, Task 006.4 handoff, audits, source archive and provenance. Preliminary data and
partial failed serialization output are archived separately and excluded. A NumPy-bool JSON
writer fix split final benchmark writer hashes after case 13; physical/control source was
identical. Afterwards, the planner exception path was fixed to discard a partial packet on
failed gains. No final benchmark had a gain failure; the only preparation failure was an
unavailable forecast. Original source snapshot and exact revisions are retained.

Power observation: AC source reported but battery 16% discharging; thermal/performance-warning
APIs unavailable. Do not claim a thermally controlled or fully charged benchmark session.

## Next task boundary

Task 006.4 should replace ONLY lateral TVLQR correction with small linear MPC, preserving
Candidate C, packet/buffer, longitudinal P control, actuator limits, fallback and experiments.
Use 4 lateral states/1 steering input, A4x4/B4x1 at 100 Hz, 10 ms full-update deadline.
First replay identical saved packets and availability times; then compare closed-loop replanning,
where differing actual states naturally yield differing plans. Measure full replacement cost.
`results/asynchronous_planner_tracker/task0064_handoff.json` exports dimensions, costs, limits,
all packet sources and measured host budget. No implementation of Task 006.4 is included.

## Commands

Run from `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle`.
Set writable caches and use fresh names/output directories; run timing cases sequentially.

```sh
export MPLCONFIGDIR=/private/tmp/apex-matplotlib
export XDG_CACHE_HOME=/private/tmp/apex-cache
RUNROOT=$(mktemp -d /private/tmp/apex-async-replay.XXXXXX)
.venv/bin/python scripts/run_async_planner_tracker.py run --name sync --architecture sync --output "$RUNROOT"
.venv/bin/python scripts/run_async_planner_tracker.py run --name playback --architecture open_loop --output "$RUNROOT"
.venv/bin/python scripts/run_async_planner_tracker.py run --name codriver --output "$RUNROOT"
.venv/bin/python scripts/run_async_planner_tracker.py suite --output "$RUNROOT/suite"
.venv/bin/python scripts/run_async_planner_tracker.py run --name spike --mode injected --delay .025 --spike --output "$RUNROOT"
.venv/bin/python scripts/run_async_planner_tracker.py run --name disturbance --mode injected --delay .025 --disturbance --output "$RUNROOT"
.venv/bin/python scripts/run_async_planner_tracker.py run --name failed_plan --mode injected --delay .025 --failure --output "$RUNROOT"
.venv/bin/pytest -q
.venv/bin/python scripts/run_async_planner_tracker.py audit
.venv/bin/python scripts/run_async_planner_tracker.py analyze
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```
