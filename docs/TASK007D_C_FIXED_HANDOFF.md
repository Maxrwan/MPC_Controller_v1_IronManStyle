# Task007D-C — fixed-handoff contract audit (C0 blocked)

**Status: BLOCKED at the C0 urgent-release alignment gate.** Baseline/main:
`3564bb394c7f49cf430d6f0f976bea153a5da822`. The working tree was clean at entry and origin
was verified as `Maxrwan/MPC_Controller_v1_IronManStyle`. No runtime implementation was made.
The authorized C0 audit found an incompatible set of timing requirements on the unchanged
scheduler, reproduced with the existing isolated straight planner and real NumPy plant.
C1, C2, C3, ECDF selection and the nine racing-result figures were not executed.

## Verified current architecture

Inspected source at the baseline: `simulation/asynchronous.py`, `diagnostic_timing.py`,
`control/trajectory/packet.py`, `planner.py`, `prediction.py`, `tracker.py`, plus the existing
chronology, diagnostic-timing, predictor/tracker and default-fingerprint tests.

The host computes a preparation synchronously, then models its physical availability with one
`pending=(completion, packet, event)` tuple. Physical propagation and codriver updates continue
during that imposed/measured interval. This is a simulated asynchronous chronology, not an OS
cancellation or parallel-solver facility. One completed future-dated packet may occupy `waiting`;
it is not a queue. Waiting alone does not mark the planner busy or block a new release.

The event loop's total phase ordering is:

1. Apply an already-due requested actuator command, using elapsed time since last actual
   application for the steering-rate clamp. Its recorded plan ID is the packet sampled when
   the request was computed, even if later application follows a new handoff.
2. Complete due planner work; clear `pending`; log readiness-state mismatch/reserve; observe
   physical delay in the rolling estimator; reject fallback-latched/insufficient-reserve work,
   put an early packet into `waiting`, or attempt immediate handoff.
3. Attempt a waiting packet when its first nominal timestamp is due.
4. Apply an approved disturbance; evaluate exhaustion and the existing fallback latch/domain.
5. Consume a busy codriver tick, or compute a new command from the current active packet and
   schedule its application. Two consecutive excessive tracking errors may latch urgent work.
6. Process a nominal planner tick (busy miss or release). Otherwise, **release latched urgent
   work immediately whenever pending is empty**, including an off-grid completion event.
7. Continue at the same timestamp for zero-duration completion/application. Otherwise record
   state/reserve, diagnose the plant and propagate to the next event.

The next physical event is the minimum of `t+plant_dt`, next codriver/planner grid, duration,
planner readiness, actuator application, waiting nominal start, packet expiry and disturbance.
Readiness can therefore introduce an RK4 partition even without an authority change. No change
to that partitioning, ordering or numerical tolerance (1e-10 s for events) was made.

Startup prepares packet 0 before physical launch, sets its physical completion to zero and
prepositions the first command while launch is gated. Runtime nominal releases begin at 0.1 s.
The rolling estimator initially returns 17 ms, then the median of at most ten observed physical
preparation delays, clipped to [0, 0.30] s. Observation occurs at completion, not release.
The legacy A predictor clones its tracker and advances the existing nonlinear RK4 prediction;
its duration is the release-time estimated delay. It never reads future measured readiness.
The real planner builds nominal nodes at `release + estimate + j*NMPC_dt`.

The buffer rejects invalid, stale (plan ID <= active), not-yet-available and insufficient-reserve
packets. Minimum handoff reserve is 0.05 s; warning is <0.20 s, critical <0.05 s and exhausted
<=1e-10 s. Acceptance trims a late nominal trajectory to acceptance time, not a shifted NMPC
grid. Existing handoff continuity limits are [0.5,0.5,1.0,0.20,0.75,0.15] in canonical SI order,
with wrapped heading residual, plus physical/model validation. Exhaustion can latch the baseline
fallback only in its documented speed/lateral domain. These rules are untouched.

## Required fixed contract, not implemented

The requested research mode would set one finite positive 10 ms-aligned offset T_h<=100 ms,
with legacy defaults unchanged and A as its only predictor. At each actual release t_r, both
forecast target and original nominal start must equal `valid_from=t_r+T_h`. Readiness must not
shift that original timeline. Early results wait; exact-deadline readiness precedes acceptance;
late results miss at the deadline and remain permanently ineligible. A still-running late solve
must remain pending and block releases until real physical completion; no cancellation or overlap.

Required simultaneous-event ordering would retain actuator application first, then preparation
completion/eligibility, fixed acceptance or miss, disturbance/validity, codriver sampling,
nominal/urgent release, and physical propagation. A prior command survives acceptance unchanged.
These are the assignment's requirements, not claims of implemented behavior or passing C tests.

### Packet metadata and serialization audit

`intended_handoff_time` is currently a forecast/intention timestamp. `timestamps[0]` provides an
implicit earliest nominal availability; `actual_completion_time` provides readiness. The buffer
does not enforce an exact deadline from `intended_handoff_time`, and historical late acceptance
is legitimate. Reinterpreting old packets as fixed commitments would break prior semantics.

A future explicit `valid_from` should distinguish an opted-in fixed commitment from that historical
intention. If an optional appended field is chosen, absent/None must retain legacy behavior;
old serialized dictionaries must still load without it. Because `as_dict()` currently exports
all dataclass fields via `vars`, merely adding a None field would change default serialization
and frozen fingerprints. A reviewed implementation must preserve legacy output keys (for example,
by emitting the new field only for explicit fixed packets), while retaining the original intended
handoff meaning. Fixed packets would require original nominal start, intention and valid_from to
agree; late-result eligibility must also survive readiness. No field or serializer was changed.
One-slot waiting supersession and fallback interaction still need the C0 tests after the blocking
urgent policy is resolved. This audit does not silently turn waiting into a scheduler queue.

## Reproduced semantic conflict

The existing test fixture uses a synthetic straight chart, constant nominal vx=2 m/s, 0.4 s
packet horizon, real dynamic bicycle plant, normal TVLQR tracker, zero codriver delay and the
unmodified urgent policy. It is a scheduler fixture, **not the N8/gamma2 racing candidate**.
Preparation delay is injected at 155 ms; approved disturbance occurs at 150 ms with the existing
0.08 m lateral / -0.04 rad heading perturbation. Duration is 0.8 s. No optimizer is invoked.

| Event | Physical time | Meaning |
|---|---:|---|
| Packet 1 release | 0.100 s | Planner becomes pending |
| Disturbance | 0.150 s | Existing approved test perturbation |
| Urgent request latched | 0.160 s | Planner still busy |
| Nominal planner miss | 0.200 s | No overlapping launch |
| Packet 1 completion | 0.255 s | Existing pending work clears |
| Urgent packet 2 release | 0.255 s | Immediate same-event urgent launch |
| Hypothetical exact +70 ms target | 0.325 s | Not on global 10 ms grid |

Code mechanism: readiness clears pending at `asynchronous.py:271–285`; the urgent release branch
at `asynchronous.py:427–428` has no grid predicate. This is existing, intentional variable-mode
behavior, not a discovered defect to repair without authorization. Old authority, codriver updates
and physical motion continue while the planner is busy. No solver overlap or fallback is observed.
The physical/command chronology reproduces exactly when the fixture is repeated. In the
requested 70 ms fixed contract, packet 1 would miss at 0.170 s but must remain busy until
0.255 s. Its late discard would still leave the latched urgent request eligible immediately,
with the startup packet still unexpired. Thus preserving busy/miss rules does not remove
the conflict merely by discarding the late packet.

For grid period g=0.010 s and eligible offset T_h=n*g,
`(t_r+T_h) mod g = t_r mod g`. Here t_r=0.255 s leaves a 0.005 s phase error for **every**
eligible offset 10–100 ms. It exceeds the event tolerance by orders of magnitude. A free planner
can also release urgent work on-grid (a second fixture gives 0.050 s); that does not remove the
busy-completion counterexample. The task explicitly requires longer overruns to be tested in C0.

It is impossible to preserve all three simultaneously in this observed case:

- Existing immediate urgent release at completion.
- Exact fixed offset from that actual release.
- Acceptance on the global 10 ms codriver grid.

The assignment's section 6 explicitly says to stop and report this conflict. Rejecting all
such urgent work, disabling urgent operation, rounding takeover or delaying release would each
introduce an unapproved policy change. No such workaround was implemented.

## Review decision needed

Engineering Orchestrator must decide which contract may change. The most direct candidate for
review is to **queue a latched urgent request until the next global codriver tick in fixed mode
only**, while preserving planner-busy behavior until completion. Then the actual release is
grid-aligned and `valid_from=t_release+T_h` can remain exact. This changes urgent responsiveness
by up to one tick and requires explicit approval; it has not been implemented or selected.
Alternatively the exact-offset or global-grid requirement must be revised. Variable-mode
behavior must remain unchanged in any approved follow-up.

A stays default; B remains experimental; P0/P1a/P1b were not selected. C remains an authorized
opt-in research scheduling proposal, **not an implemented mode in this blocked delivery**.
Production defaults remain unchanged. No System Identification, LMPC, adaptive codriver,
opponent handling, energy optimization or final profile freezing has begun.
