# Task007D-D1 — committed-control-prefix predictor contract

Status: implemented and verified in isolation, 2026-10-09. Architecture B/C are not
activated. No AsyncRunner, planner, packet, buffer, physical model or NMPC changes.

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
provenance claims; D1 does not wire it into the runtime.

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

Architecture B may later pass the snapshot with the existing estimated duration.
Architecture C may later pass `scheduled_target - release_time` through the same `duration`
argument. D1 neither chooses that target nor implements fixed handoffs. D2 should capture
these fields atomically from the existing release context behind an explicit opt-in path,
without exposing future measured timing to the predictor or changing default behavior.
Do not activate that integration before review.

## Focused verification

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
Runtime ordering reference: [AsyncRunner](/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/simulation/asynchronous.py:197), unchanged.
