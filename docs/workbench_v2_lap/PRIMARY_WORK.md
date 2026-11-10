# PRIMARY APEX — WORKBENCH V2: EXTENDED AND FULL-LAP NMPC EXPERIMENTATION

**Decision: AUTHORIZE BOUNDED DEVELOPMENT**

Repository: `Maxrwan/MPC_Controller_v1_IronManStyle`

Accepted V1 baseline: `511b0a884e0f8474760817620fcdef46e7860142`

Create a new isolated development branch, `codex/workbench-v2-lap`, from this baseline.

## Objective

Expand APEX Workbench from 2-second NMPC transient experiments into meaningful extended and full-lap racing experiments using the genuine frozen NMPC/TVLQR controller.

Retain the existing operational NMPC Lab V1 unchanged and usable.

## 1. Experiment modes

Support:

- **Transient:** Existing accepted 2-second Scratch experiments.
- **Extended:** Bounded 5-, 10- and 20-second experiments.
- **Full Lap:** Run until a complete circuit is traversed, or until a declared maximum simulation duration is reached.

Use the existing synthetic Grand Prix track, Planning reference, dynamic bicycle model, combined-grip tires, Architecture A, NMPC N=8 and TVLQR.

No new control equations, solver algorithms or vehicle physics.

Reuse the native `AsyncRunner` and its actual lap-crossing mechanism.

Define lap completion correctly: the measured lap must represent traversal of one complete track circumference from a consistent spatial phase. The existing `s_abs=1 m` starting state must not make an incomplete first crossing appear to be a full lap.

Record incomplete attempts accurately.

## 2. Separate bounded execution profile

Do not simply enlarge the accepted V1 profile or globally weaken the current 60-second worker limit.

Create an independent, source-isolated long-run profile with explicit simulation-duration, wall-time, CPU, memory and output ceilings.

Preserve the accepted V1 access policy, scientific source, historical attempts and existing execution lease.

Use a clear versioned configuration identifying duration/termination mode, controller costs, track, reference, initial conditions and scheduling assumptions.

Avoid unnecessary approval bureaucracy for ordinary user-triggered runs after V2 acceptance.

## 3. Efficient long-run recording

Inspect current memory usage, per-step journals, raw output size, full Jacobian logging and playback payload construction.

Implement the smallest sufficient improvements needed for longer runs.

Preserve genuine state, command, packet, optimizer, handoff, failure and lap-crossing chronology.

Avoid redundant full histories and expensive display regeneration.

Use chunked or compact retained files where appropriate, maintaining integrity and exact native timestamps.

Scientific metrics must use genuine recorded values. Display decimation must never replace retained scientific observations.

## 4. Racing-performance analysis

Add analysis of:

- Actual completed lap time.
- Vehicle speed versus track progress.
- Racing-line tracking error versus track progress.
- Heading error and yaw-rate behavior.
- Steering and longitudinal command evolution.
- Longitudinal and lateral acceleration where derivable from the accepted model/records.
- Front/rear combined-grip utilization.
- Track-boundary violations.
- Feasibility, slack and solver failures.
- NMPC iterations and preparation times across track regions.
- Packet handoffs, missed releases and fallback activity.
- Selected genuine NMPC predictions versus actual vehicle evolution at correctly associated timestamps.

Use a small number of clearly defined spatial sectors, with identical track-progress boundaries across compared experiments.

Include time-based views when helpful.

Do not introduce a new racing-performance score.

## 5. Comparisons

Support baseline versus modified weights over equivalent experimental conditions.

Report actual lap/sector time, tracking error, steering effort, grip utilization, feasibility and solver behavior.

Label runs with different starting conditions, coverage or scheduling assumptions as noncontrolled comparisons.

Do not compare differently weighted raw NMPC objective totals as a performance ranking.

A faster lap is not automatically a safer or more robust lap.

## 6. Numerical authorization

Complete software tests and an independent Engineering Review before genuine extended execution.

After review, authorize at most:

1. One explicitly bounded 10-second pilot.
2. One genuine full-lap baseline attempt, conditional on successful preflight and a declared finite resource budget supported by the pilot and host capacity.

No automatic retries or campaign.

If the full-lap execution would require unsupported resource limits or modifications to frozen scientific mathematics, stop and report the blocker rather than bypassing safeguards.

Retain incomplete runs and their failure reasons.

## 7. Acceptance

Deliver:

- Working extended-run selection.
- Full-lap termination and accurate lap-time reporting.
- Scientific racing-performance metrics.
- Existing short-response analysis preserved.
- Efficient replay-ready retained data.
- Source and historical evidence preservation.
- Focused independent Engineering Review.

Do not perform the visual redesign in this task.

Stop at:

`WORKBENCH_V2_LAP_WORK_COMPLETE_PENDING_PRIMARY_ACCEPTANCE`

**Priority: Genuine full-lap scientific usefulness without expanding the controller architecture.**