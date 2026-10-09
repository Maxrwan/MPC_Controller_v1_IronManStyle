# Task007D-D1 — committed-control-prefix predictor contract

Status: D1 capability and D2 opt-in runtime integration verified, 2026-10-09.
Architecture A remains the default. Architecture B is available through explicit
`AsyncConfig(committed_prefix_prediction=True)`. Architecture C is not implemented.
No packet, buffer, physical model, NMPC or production-default change.

## Interface and information boundary

The existing `ActuationPredictor.predict(state, time, duration, buffer, tracker)` accepts
one new keyword-only argument: `committed_prefix=None`. Omitting it, or explicitly
passing `None`, retains the legacy prediction arithmetic and endpoint convention.

`CommittedControlPrefix` is a frozen dataclass with these release-known fields:

| Field | Meaning |
|---|---|
| `release_time` | Simulated physical release timestamp; must equal `predict`'s `time`. |
| `applied_control` | Currently applied `[delta, a_cmd]`, in rad and m/s². |
| `last_application_time` | Most recent actual command-application time, at or before release. |
| `pending_control` | Optional already-computed requested command, before the application-time steering clamp. |
| `pending_application_time` | Its already-scheduled physical application time, at or after release; supplied together with the pending command. |

Timestamps are finite, nonnegative seconds. Input arrays/lists are copied into owned
immutable two-float tuples; subsequent caller edits cannot change the snapshot. Controls
must be finite canonical vectors and must lie within the tracker's existing actuator box.
The pending command is a commitment. Future TVLQR commands are **causal feedback forecasts**,
not known future actuator inputs.

The caller supplies the release-time measured state, release-active buffer and tracker.
Capture is defined at the existing planner-release phase: the current timestamp's due
applications and codriver release/skip have already been processed. A newly computed
zero-latency command may still be pending at that same timestamp. The next unprocessed
codriver tick is therefore strictly after release on the existing global tracker grid;
there is no second scheduler state or queue in the snapshot.

The predictor pins the active immutable packet at call entry in a private buffer and
clones the tracker. It never follows a later replacement of the caller's active packet.
No future solver duration, driver duration, latency trace, measured command history or
physical plant state is accepted or queried. The caller must not populate the snapshot
from information unavailable at release. The API cannot verify an external caller's
provenance claims. D2 supplies these fields directly from the runner's release context.

## Propagation and event ordering

The original prediction loop, symbolic bicycle, RK4 map, curvature sampling and stage
domain checks are reused. The NumPy physical plant remains separate. Maximum forecast
steps are 0.005 s, additionally split at pending application, codriver tick and target.
The snapshot's applied command takes precedence over the real tracker's `previous` value,
which may already contain a requested but unapplied command.

At each forecast event:

1. Apply a due release-known pending command first. Clip steering relative to the previously
   applied steering by `steering_rate * max(0, t - last_application_time)`, exactly the
   existing runtime application rule. Acceleration retains the requested value.
2. If at the target, return the predicted state and preceding applied command. A committed
   application exactly at the target is included, but it has no positive-duration influence
   on the state. Do not generate feedback at the target: trajectory handoff precedes the
   codriver release at that timestamp.
3. At a codriver tick strictly before the target, skip feedback if the known command is
   still pending. Increment the grid index; missed ticks never generate catch-up work.
4. Once no command is pending, forecast feedback using the cloned controller, predicted
   state and release-active trajectory. Assume ideal zero latency for these unknown future
   computations, preserving the established approximation. Apply the ordinary tracker box
   and per-period steering limits, then the elapsed-application steering clamp. Update the
   forecast's last-application time.
5. Propagate under the held applied command until the next event.

A known application coincident with a nonterminal codriver tick runs first, followed by
predicted feedback. The latter's instantaneous application has zero elapsed time, so it
cannot immediately change steering again, although its acceleration may differ. The
target convention returns before this new feedback. A known application due at release
is also processed for a zero-duration prediction.

The snapshot path uses integer-indexed global ticks, matching AsyncRunner. The legacy path
retains its original tick arithmetic. Existing 1e-10 s event comparisons and 1e-12 s loop
termination tolerance are retained; a pending timestamp strictly beyond the requested
target is never consumed. These numerical tolerances are not physical latency allowances.

## Validation and limitations

Unavailable, future-dated, invalid or exhausted release trajectories fail explicitly;
targets beyond the active horizon fail under the existing horizon tolerance. No trajectory
is extrapolated or switched. Existing finite-state, speed and Frenet-denominator checks
remain; the snapshot path additionally checks initial and just-applied states/commands
through the same symbolic map with zero duration, including zero-duration requests.

This is not a replay of the future physical world. Unknown future computation delay,
busy ticks, disturbances, new packets, fallback and planner availability are not invented.
Only the one already-known pending command suppresses feedback ticks. No packet-authority
decision, predictor correction from future truth or prefix constraint inside NMPC is added.
The tested controller is the frozen TVLQR path; optional local-MPC controller behavior is
outside this task. Predictor curvature remains held within each RK4 step as before;
the physical plant refreshes it at derivative stages. No general plant/forecast identity
or hard-real-time guarantee is claimed.

Architecture B now passes the snapshot with the existing estimated duration.
Architecture C may later pass `scheduled_target - release_time` through the same `duration`
argument, but D2 does not choose a fixed target or implement its scheduling/authority policy.

## D2 runtime integration

`AsyncConfig.committed_prefix_prediction` defaults to `False` and requires a Python `bool`;
integers, strings, `None` and NumPy booleans are rejected. Disabled runs call the original
planner interface and legacy predictor path. Enabled runs check that `planner.prepare`
accepts the `committed_prefix` keyword before startup; an incompatible signature raises
an explicit `TypeError`. Wrappers accepting `**kwargs` remain responsible for forwarding
the snapshot; the standard `TrajectoryPlanner` does so.

The shared `AsyncRunner.run.release` function captures the immutable snapshot for both
normal and urgent releases. Capture occurs after the current event pass's due actuator
application, planner/waiting handoff, disturbance/fallback handling and codriver tick/skip.
It reads only `t`, applied `command`, `last_application` and the optional
`actuator_pending=(scheduled_time, requested_command, telemetry_row)`. The requested
command is copied without premature application clamping. A new zero-latency command
created on the current tick remains pending with `scheduled_time == t`; the predictor
handles that case without changing the runtime's same-time continuation.

`TrajectoryPlanner.prepare(..., *, startup=False, committed_prefix=None)` forwards the
snapshot only for a nonstartup prediction. Without it, the old positional predictor call
is used. The target stays `release_time + estimated_delay`, independent of the actual
future preparation duration or imposed readiness delay. Startup still uses the unpredicted
initial state, zero estimate and gated prepositioning, with no snapshot argument.

Only the forecast inputs change under B. Planner/codriver periods, event ordering, plant
RK4 partitions, readiness scheduling, waiting, late trimming, continuity/reserve checks and
fallback rules are unchanged. A packet becomes authoritative only through the existing
buffer acceptance path. Different forecast states can change later optimized packets and
their physical consequences; B is not a promise of equal A/B trajectories or better racing.

### Planner event telemetry

| Field | Meaning |
|---|---|
| `prediction_architecture` | Runner configuration: `A` or `B`, including startup. |
| `prediction_mode` | Actual standard-planner path: `startup`, `legacy`, or `committed_prefix`. |
| `release_time`, `predicted_completion_time` | Existing release and estimated target timestamps. The latter is a forecast target, not measured completion. |
| `release_command_pending` | A release-known command is pending, even if its scheduled time equals release. Logged in A too, without affecting A prediction. Startup is false. |
| `pending_application_time` | That command's scheduled time, or null. Startup is null. |
| `predicted_state` | Existing forecast initial state passed to NMPC. On forecast failure the legacy source-state placeholder remains; inspect preparation status and the following field. |
| `predicted_previous_control` | Forecast preceding applied command passed to NMPC; null if forecasting did not produce it. Startup records its unchanged preceding input. |
| `completion_time`, `physical_delay`, `planner_total_time` | Existing readiness and preparation timing; accepted handoff stays in the separate handoff log. |

The existing completion `prediction_error` still compares actual state **at readiness**
with predicted state **at the estimated target**. It is not an aligned handoff prediction
error. Same-time candidate-reference mismatch remains in `handoffs`. Telemetry additions
are diagnostic only and occur outside the recorded preparation total; added Python work
can still change host timing, so parity checks use imposed physical delays.

## D1 focused verification (retained)

No active measured campaign marker or numerical experiment process was found before
verification. Tests ran in a fresh process with the existing Accelerate SINGLE configuration;
no full laps or measured benchmarks ran.

**85 passed in 1.91 s:** 37 new cases plus the existing trajectory-tracker, asynchronous
chronology and diagnostic-timing suites. Ruff check and format check passed on the two
changed Python files. Existing tests and their tolerances were not edited.

The new tests cover exact pre-D1 output parity with both omitted/None snapshots; held
physics before/after a pending event; a target before the event; steering limits and busy
ticks; release/tick/target ties; agreement with unchanged AsyncRunner on four short targets;
immutable owned inputs, caller nonmutation, repeatability, release-packet pinning,
forbidden future plant/solver/timing access, and invalid snapshot/state/trajectory rejection.
Legacy fixtures use exact array equality. New analytic and independent NumPy/CasADi
comparisons use absolute 1e-12 with rtol=0 for floating-point accumulation and heading-wrap
roundoff in short straight-track fixtures. Scalar steering checks use 1e-15 absolute
tolerance. Neither is a wall-clock assertion or an enlarged existing tolerance.

Scope verification preserved 392 other Git-listed files by SHA-256, including the runtime
scheduler, planner, packet/buffer, models and existing tests. The prior handoff and decision
log text remain verbatim beneath the D1 additions. All 8,740 files in the existing B/C/C-R
and resumed result directories had modification timestamps predating D1; those archives
were not rewritten or subjected to a new bulk content-hash audit. The D1 diff contains only
the predictor, new tests, this contract, handoff and required ADR-157.

Implementation: [prediction.py](/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/trajectory/prediction.py:14).
Tests: [test_committed_prefix.py](/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tests/unit/test_committed_prefix.py:1).
Prior baseline: [D0 audit](/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/TASK007D_CURRENT_TIMING_AUDIT.md:1), retained as the pre-D1 record.
Runtime ordering reference: [AsyncRunner](/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/simulation/asynchronous.py:236); the event-loop ordering remains unchanged in D2.

## D2 focused verification

Started from clean main `4a7026eac13e2a5d976a0dfb2a6756dfa5de6afb`, matching GitHub main.
No active measurement marker or numerical experiment process was present. A fresh
Accelerate SINGLE process ran only the five relevant suites: committed-prefix runtime,
D1 prefix, trajectory tracker, asynchronous chronology and diagnostic timing.
**101 tests passed in 4.51 s**, including 16 new D2 cases and all 85 prior focused cases.
Scoped Ruff check/format passed. No full laps, measured repetitions or historical result
exports ran. The straight synthetic 2 m/s fixtures use N8/dt0.1 and frozen review weights;
they are not gamma2 racing validation.

Pre-edit channel fingerprints retained in the runtime tests match both default and
explicitly disabled A exactly: states, requested/applied commands and their timestamps,
handoffs/IDs, releases, misses, reserve, triggers/fallbacks, termination, predicted inputs,
and every solver initial guess and parameter vector. Wall/CPU timing, the wall-based
deadline-exceeded diagnostic, and additive telemetry are excluded from that numerical
comparison. The golden fingerprints document this backend's deterministic baseline;
they are not a cross-platform bitwise guarantee or wall-clock CI threshold.

Other cases verify actual snapshot capture/forwarding, applied/requested distinction,
completed and newly zero-latency command ordering, urgent capture, immutable copies,
future-readiness independence, a direct expected D1 prediction, exact B repeatability,
unchanged startup inputs, and unchanged early-wait/late-accept policies. Existing tests
also retain zero/injected/measured dispatch, busy deadlines and moving-plant checks.
New timestamp assertions allow only the existing 1e-10 s event tolerance; physical and
solver parity use exact equality. No existing tolerance was enlarged.
All 16 D2 cases also passed after explicitly tightening their timestamp assertions to
that absolute tolerance with zero relative tolerance.

Runtime tests: [test_committed_prefix_runtime.py](/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tests/unit/test_committed_prefix_runtime.py:1).
No D3, fixed-handoff architecture or timing campaign is authorized by this result.
