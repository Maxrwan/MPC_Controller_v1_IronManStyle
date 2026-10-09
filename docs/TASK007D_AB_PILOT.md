# Task007D-D3 — controlled prediction validation

## Protocol fixed before pilot execution

Synthetic simulation only. Begin at clean main b27c0465f3cb1a13ad20152c17bcfadb37c2a8c4.
Capture detached release state, active packet, applied and pending commands, estimated delay,
TVLQR config/bounds and vehicle parameters at the existing release phase. The optional
`AsyncRunner(..., release_observer=...)` defaults to None. It adds no events or RK4 splits.
Evaluate A and B offline with fresh private buffers/trackers, pinned to that release packet.
Only the actual architecture's original forecast controls NMPC. The other remains a shadow.
Physical histories from different active architectures are separate comparison strata.

Target = release + rolling estimated preparation delay. Signed residual = forecast minus
physical state in `[vx, vy, r, e_psi, s_abs, e_y]`; wrap only e_psi. Exact recorded events
use the existing 1e-10 s event tolerance (report actual timestamp offset). Otherwise replay
one partial step of the independent **existing NumPy plant** from the left recorded state
with its held command. Label this `reconstructed_rk4`, never independently sampled truth.
Verify the full bracket replay closes within 1e-10 per channel; report per-channel closure
and partial-step versus two-half-step differences. These are numerical consistency checks,
not bounds on true physical error. Never extrapolate beyond the last recorded event.
Missing targets and failed forecasts have null residuals and explicit exclusion counts.

Report readiness-minus-target only for processed readiness, accepted-handoff-minus-target
only for accepted packets, and retain the independent same-time handoff continuity residual.
Do not relabel the old readiness `prediction_error` as aligned error. Report per-state signed
mean, RMS and max absolute error; omit p95 for strata below 20 comparable releases. Percent
improvement = 100*(1-RMS_B/RMS_A); undefined when RMS_A is zero. No normalized aggregate.

Frozen Task007C candidate: N=8, dt=0.1, H=0.8, substeps=4, Q diag(4,4,1,200,200),
R diag(25,1), W diag(1,0.1), alpha_vy=alpha_r=1, lambda_s=0, tracker margin 0.08 m,
smooth combined grip, existing TVLQR, Ipopt defaults plus warm_start_init_point=yes, existing
primal warm-start policy. Read existing synthetic gamma 2.0 and, conditionally, gamma 1.8
packages unchanged. Initial progress 1 m and the existing reference-derived initial state.

Choose fixed planner 35 ms/codriver 15 ms for both architectures, exactly two simulated seconds
each. The deliberately nonzero driver delay exposes known pending work and busy grid ticks;
it is an imposed diagnostic schedule, not measured device performance. Normal urgent policy
stays enabled. Startup remains gated, first runtime delay estimate 17 ms, then existing rolling
median. Run sequential fresh Accelerate SINGLE workers. Host wall/CPU times are descriptive.
No tests or rendering overlap pilots. Check all MEASURED_ACTIVE guards and free disk >=1 GiB.

Run gamma2 A, inspect gate, then B, inspect gate. Only after this pair clears the gate run
one gamma 1.8 A/B pair. Stop continuation on boundary crossings, solver/preparation/model
failure, chronology/authority violation, unexplained exhaustion, forecast inconsistency,
or **any predicted slack above 1e-6 m** (conservatively stronger than persistent material slack).
Preserve all failures without tuning. Compare closed-loop metrics on the last common
recorded physical-time endpoint; do not align divergent planner launches by row index.

## Outcome

D3 complete, pending Engineering Orchestrator review. All four two-second runs reached the
duration limit and cleared the scientific gate. Architecture A remains the production default.
No Architecture C, full laps, measured repetitions or controller tuning were performed.

The 76 release contexts each yield a matched pair of forecasts: 19 per host architecture
and gamma. **All 76 have a known pending command**, with application 15 ms after release;
no-pending behavior is covered by unit tests, not this physical pilot. There are zero forecast
failures, excluded targets, solver/model failures, handoff rejections or chronology violations.
All 76 offline forecasts of the active architecture exactly reproduce the state and preceding
command actually passed to NMPC. This validates the captured release context, separately from
whether either forecast matches later simulated physics.

## Matched prediction accuracy

Gamma 2.0, **A-controlled physical history**, n=19 (all pending); errors are in canonical SI units.
B is a shadow here, so both columns score against exactly the same future physical trajectory.


| State | A mean | A RMS | A max abs | B mean | B RMS | B max abs | RMS reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| vx (m/s) | 0.000240166 | 0.000450335 | 0.00107017 | 5.9245e-05 | 0.000320262 | 0.00120274 | 28.88% |
| vy (m/s) | -0.000171498 | 0.0016741 | 0.00223257 | -8.95724e-05 | 0.00139387 | 0.00173618 | 16.74% |
| r (rad/s) | -0.00404741 | 0.0478599 | 0.0596039 | -0.00156383 | 0.0253375 | 0.0314216 | 47.06% |
| e_psi (rad) | -5.43317e-05 | 0.000468874 | 0.00062649 | -2.86211e-05 | 0.000144768 | 0.00023856 | 69.12% |
| s_abs (m) | 6.82293e-06 | 9.3633e-06 | 1.94522e-05 | 1.61012e-06 | 4.01362e-06 | 1.08381e-05 | 57.13% |
| e_y (m) | -4.80597e-06 | 4.06925e-05 | 5.61292e-05 | -2.64548e-06 | 1.24101e-05 | 2.15556e-05 | 69.50% |

The independent **B-controlled history** gives consistent RMS reductions. Lower-demand gamma 1.8
also improves every per-state RMS. These strata are kept separate; they are not 76 independent
replications and launch indices are not used to pair different closed-loop histories.

| Host physical history | vx RMS reduction | vy | r | e_psi | s_abs | e_y |
|---|---:|---:|---:|---:|---:|---:|
| gamma2_B | 28.08% | 17.14% | 47.18% | 69.11% | 56.90% | 69.48% |
| gamma 1.8_A | 30.90% | 25.36% | 47.33% | 69.04% | 61.00% | 69.86% |
| gamma 1.8_B | 30.43% | 25.35% | 47.34% | 69.07% | 60.90% | 69.88% |

Complete signed mean/RMS/max/p95-null values for **every state in every stratum** are in
[accuracy.csv](task007d/d3/accuracy.csv); individual residuals and timestamps are in
[release_scores.csv](task007d/d3/release_scores.csv). P95 is intentionally not estimated
from 19 releases. Relative improvement refers to RMS, not every individual error: in the
primary A-host history B's maximum vx error rises from 0.00107017 to 0.00120274 m/s.

## Closed-loop pilot, common observed time 0–1.995 s

Both pairs have identical planner release times, delay estimates, accepted IDs/timestamps and
400 recorded physical events. Every run simulated 2 s; the unchanged runner does not log the
terminal step endpoint, so physical comparisons conservatively end at 1.995 s. No run is
truncated against a longer comparator. Clearance and crossings below refer to recorded
vehicle-center positions, not continuous-time body-footprint certification.

| Gamma / active architecture | Progress reached (m) | Min center clearance (m) | Steering TV (rad) | Global heading TV (rad) | e_y tracking RMS (m) | e_psi tracking RMS (rad) |
|---|---:|---:|---:|---:|---:|---:|
| gamma2_A | 12.20427 | 0.2466621 | 0.943432 | 1.78859 | 0.003607407 | 0.03572488 |
| gamma2_B | 12.20777 | 0.2479049 | 0.9320446 | 1.785702 | 0.003486185 | 0.03396975 |
| gamma 1.8_A | 11.10312 | 0.2510738 | 0.9310274 | 1.649717 | 0.003501601 | 0.03497554 |
| gamma 1.8_B | 11.10478 | 0.2513748 | 0.9248121 | 1.651669 | 0.003361254 | 0.03342006 |

Every run: zero recorded boundary crossings; zero solver/model failures; maximum predicted
slack below 9.1e-11 m (zero plans above 1e-6 m); zero handoff rejections; 19 accepted runtime packets;
zero planner busy misses; 100 codriver busy grid misses and 100 applied jobs exceeding the 10 ms
period, as expected from the imposed 15 ms latency; minimum trajectory reserve 0.67 s. There is
no exhaustion or fallback. These imposed misses are not measured host deadline failures.
Subtract 0.08 m from center clearance for the unchanged tracking-margin clearance. Heading TV
uses wrapped increments of track tangent plus e_psi; Frenet heading TV is reported separately.
APEX-to-vehicle tracking uses codriver sampling residuals against the active packet, not the
offline Planning line; the compact summary retains RMS/max for all six states.

In both pairs the first forecast split is at release 0.1 s, and both accept plan 1 at 0.135 s.
The codriver samples it at 0.14 s; the first applied acceleration difference is at 0.155 s
(steering and physical states still coincide). The first recorded state difference is
at 0.160 s. Thus the difference follows accepted new-packet authority. Full preceding handoff
and command events are retained in [summary.json](task007d/d3/summary.json).

## Reconstruction and timing distinctions

For each run 18 targets match recorded events and the first target 0.117 s is reconstructed
inside the unchanged 0.115–0.120 s held-command interval. Full bracket replay closure is zero
in all channels. Across four cases, maximum absolute partial-step/two-half-step differences,
in canonical order, are:
`[3.73035e-13, 3.25840e-11, 4.23609e-11, 3.38618e-12, 3.33955e-13, 1.04267e-12]`.
This is negligible against the reported residuals but is not a rigorous integration-error
bound or independent physical measurement. Exact-event timestamp offsets are at most
6.67e-16s. The truth reconstruction reuses the approved plant and its stage curvature
refresh; the predictor keeps its original held-curvature policy.

Readiness-minus-target and accepted-handoff-minus-target are each +0.018 s for the first
release, then zero for 18 releases per run. They happen to coincide in this chosen history;
the implementation and early-readiness unit fixture distinguish them. No accepted-handoff
time is assigned to rejected/unaccepted packets. Existing handoff continuity compares the
candidate nominal state and actual state at the *same* handoff instant; it is separate from
both forecast target scoring and the old misaligned readiness `prediction_error`.

| Gamma / architecture | Same-time handoff vx RMS | vy RMS | r RMS | e_psi RMS | s_abs RMS | e_y RMS |
|---|---:|---:|---:|---:|---:|---:|
| gamma2_A | 0.00107655 | 0.00764757 | 0.0558831 | 0.00247151 | 0.000153714 | 4.06749e-05 |
| gamma2_B | 0.00094887 | 0.00769329 | 0.0370016 | 0.00241382 | 0.000151401 | 1.28636e-05 |
| gamma 1.8_A | 0.000760622 | 0.00550077 | 0.0545747 | 0.00210852 | 0.00013497 | 4.44457e-05 |
| gamma 1.8_B | 0.000658199 | 0.00544428 | 0.0335759 | 0.00204062 | 0.000133038 | 2.13594e-05 |

## Failures, limits and interpretation

An initial gamma 1.8 launch referenced the Task007B fixture directory and failed before
loading the plant. The correct existing package is
`configs/planning/task007c_resume/gamma_1p800`; only this path was corrected. The failed
`results/task007d/d3/gamma1p8_A/worker.log` is retained and reproduced in the compact summary.
The successful retry has a separate directory. No unfavorable physical case was removed.

B meaningfully reduces target-state RMS in this pending-heavy synthetic interval: approximately
47% in yaw rate and 69% in heading/lateral offset across both gammas and both physical histories.
Absolute residuals and the higher worst vx error must accompany these percentages. Closed-loop
changes are small, with slightly better RMS tracking/clearance/variation in this pilot, but some
individual channels worsen (e.g. gamma 2 B's peak progress tracking error and vy handoff RMS).
This is evidence for **a wider bounded A/B validation**, not for a production default switch,
long-lap performance, physical validation, hard-real-time behavior or Raspberry Pi timing.

Only one imposed delay pair, one start position and a short shared interval were exercised.
Future unknown driver latency, skipped ticks and future packet changes remain absent from
both causal forecasts as documented in D1/D2. No future physical truth or actual future solver
duration enters either forecast. Snapshot copies are read-only and detached; the callback is
a trusted diagnostic collector, not a sandbox for arbitrary user code. Capture overhead can
alter host durations; invariance claims concern imposed timing, not measured runs.

Recommended next bounded assignment: review D3, then authorize a small predefined matrix of
short A/B intervals with lower/zero driver delay and varied planner estimates, including
no-pending/urgent releases. Keep matched shadows and the same stop gates. Do not add fixed
handoffs or tune weights to compensate. No such next assignment was executed here.

## Verification and evidence preservation

**116 focused tests passed in 7.40 s**, comprising 15 new diagnostic cases and 101 existing
D1/D2/chronology/tracker/timing cases. Ruff check and format check passed on all 8 scoped
Python files. Tests cover exact capture-on/off physical states, commands, accepted handoffs,
solver guesses/parameters and every RK4 interval; retained pre-D2 default-A fingerprints;
same-context shadows, controller nonmutation, future-information exclusion, angular wrapping,
analytical held-acceleration reconstruction, missing/exhausted trajectory, pending/no-pending,
readiness versus handoff, repeated forecasts, unequal coverage and explicit stop gates.
Existing tests/tolerances were not changed. New straight-plant assertions use 1e-12 absolute
and zero relative tolerance for float accumulation; 1e-10 s is the existing event tolerance.
Closure tolerance 1e-10 per channel only rejects inconsistent recorded brackets; it is not
used to loosen physical/controller checks. No measured-duration equality is asserted.
Fresh workers verified Accelerate SINGLE through BLASGetThreading, observed one OS process
thread at preparation entry/exit, and CPU/wall ratios 0.9935–0.9991 over physical execution.
Runtime wall duration was 3.27–3.42 s per case and is descriptive only. These samples do not prove
absence of every transient thread, and environment variables alone are not the evidence.
No isolated measurement marker/worker was active before tests/pilots; disk had at least 1.7 GiB
free (the launcher requires 1 GiB). No tests/rendering overlapped pilot execution.

Raw new evidence is retained under `results/task007d/d3` (~4.8MiB), ignored by Git. The compact
review bundle (~125KiB) is under `docs/task007d/d3`: summary, accuracy, release scores and
source hashes. It records fixture/vehicle/source/raw-file hashes and source base commit.
Gamma2 ran before the gamma 1.8 fixture-path fix; source hashes retain that distinction.
The later report-export script is postprocessing only. An independent export into a fresh
scratch directory reproduced all four compact artifacts byte-for-byte. Preservation audit:
394 other preexisting Git files are SHA-256-identical; only the authorized runner and
three existing documentation files changed. All 10,852 preexisting result files retain their
sizes and modification timestamps (a metadata check, not a fresh bulk content hash).
No prior B/C/C-R evidence was overwritten.

## Reproduction

Run from the repository root with its existing environment; confirm no measured campaign
is active first. Choose **fresh** result and export directories; commands reject overwrite.
Execute one pilot at a time, inspect its `summary.json.stop_gate`, and stop if nonempty or
if the worker fails. The following are the successful case commands with fresh names:

```sh
.venv/bin/python scripts/run_task007d_pilot.py --architecture A --gamma 2.0 --output results/task007d/d3_repro/gamma2_A
.venv/bin/python scripts/run_task007d_pilot.py --architecture B --gamma 2.0 --output results/task007d/d3_repro/gamma2_B
.venv/bin/python scripts/run_task007d_pilot.py --architecture A --gamma 1.8 --output results/task007d/d3_repro/gamma1p8_A
.venv/bin/python scripts/run_task007d_pilot.py --architecture B --gamma 1.8 --output results/task007d/d3_repro/gamma1p8_B
VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/run_task007d_report.py --input results/task007d/d3_repro --output results/task007d/d3_repro_compact
```

Workers configure the existing native policy before numerical imports. The report command
only analyzes saved evidence. Focused regression command (after all pilots have exited):

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python - <<'PYTEST'
from threading_study.config import configure_accelerate
configure_accelerate(1)
import pytest
raise SystemExit(pytest.main(['-q',
    'tests/unit/test_prediction_diagnostics.py',
    'tests/unit/test_committed_prefix.py',
    'tests/unit/test_committed_prefix_runtime.py',
    'tests/unit/test_async_chronology.py',
    'tests/unit/test_trajectory_tracker.py',
    'tests/unit/test_diagnostic_timing.py']))
PYTEST
.venv/bin/ruff check src/apex/simulation/asynchronous.py src/apex/simulation/prediction_capture.py scripts/task007d scripts/run_task007d_pilot.py scripts/run_task007d_report.py tests/unit/test_prediction_diagnostics.py
.venv/bin/ruff format --check src/apex/simulation/asynchronous.py src/apex/simulation/prediction_capture.py scripts/task007d scripts/run_task007d_pilot.py scripts/run_task007d_report.py tests/unit/test_prediction_diagnostics.py
```
