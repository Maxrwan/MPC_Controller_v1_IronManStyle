# Task007D-D0 — current timing pipeline audit

Completed 2026-10-09. Documentation-only inspection of the current working tree.
The controlling assignment is attachment `7093ac12-60ec-4403-9f25-c12a97640bc3/Pasted text.txt`.
No architecture B/C implementation, simulation, regression run or measured benchmark was performed.

**Finding:** APEX already predicts the future state by forecasting the active trajectory's
TVLQR feedback. It already delays early packets until their nominal start. These mechanisms
are not a complete committed actuator prefix or a fixed, grid-aligned handoff policy.

Statements labeled **Verified** describe inspected code. **Interpretation** and
**Recommendation** describe implications or future choices, not implemented behavior.
Source keys and line references below resolve through the absolute links in section 11.
All physical times and durations are seconds unless explicitly labeled ms.

## 1. Current architecture overview

**Verified.** The Task007C resumed worker composes a separate NumPy `DynamicBicycle` plant,
`TrajectoryPlanner`, `TrajectoryTracker` with default 100 Hz TVLQR feedback, and `AsyncRunner`
([RUN], lines 91–173). The planner uses the controller's independent CasADi model for its
future-state forecast and gain construction ([PL], 13–17). The physical plant never uses
the optimizer's returned states as its actual state.

The host executes preparation and codriver calls sequentially. It then advances simulated
physical time through their imposed availability intervals. This models continued motion
and control during computation; it is not an OS-thread implementation or a hardware
real-time scheduler ([A], 164–195, 279–432; [SPEC], 23–50).

The current stages are:

1. Sample the actual simulated state at a planner release; estimate total preparation delay.
2. Forecast the state and preceding command at release plus that estimate.
3. Solve NMPC from that forecast, validate the solution, construct a timestamped packet,
   and build the TVLQR gain schedule.
4. Schedule result readiness from measured or imposed preparation delay. Until acceptance,
   the active old trajectory remains authoritative for codriver reference sampling.
5. At readiness or the packet's later nominal start, attempt acceptance; trim late packets.
6. TVLQR samples the active trajectory on its fixed release grid. Its command becomes an
   applied plant input only after its own separately scheduled latency.

The new D0 assignment accepts **N=8, dt=0.1, H=0.8; Q=diag(4,4,1,200,200),
R=diag(25,1), W=diag(1,0.1), lambda_s=0, synthetic gamma=2.0** as the review candidate.
This is task context, not a configuration change made by this audit. The older handoff
still describes that choice as awaiting review ([HANDOFF], 22–36); it has not been rewritten.
The generic `MPCConfig` defaults are N=20/dt=0.05 ([NLP], 25–37), while the resumed-study
CLI defaults to N=4 and requires explicit candidate arguments ([CLI], 9–26). Neither
implicitly selects the complete D0 candidate. Production defaults remain unchanged.

## 2. Code-level timing diagram

For a nonstartup successful preparation, ignoring the stated numerical event tolerance:

```text
HOST EXECUTION (sequential; local perf_counter durations)
AsyncRunner.release at simulated t_r
  tracker.previous <- actually applied command
  estimate <- RollingDelay.estimate()
  TrajectoryPlanner.prepare(x(t_r), t_r, estimate, active buffer, tracker)
    ActuationPredictor.predict -> x_hat(t_r + estimate), u_hat_previous
    MPCController.compute_control
      preview -> warm-start/parameters -> IpoptSolver.solve -> validation
    construct nominal nodes at t_r + estimate + k*dt
    TVLQR.compute -> immutable packet with gains
    record planner_total_time
  tau_ready <- normal timing dispatch OR DiagnosticTiming
  pending <- (t_r + tau_ready, packet, event)

SIMULATED PHYSICAL EXECUTION (moving plant; held applied input between applications)
t_r ---------------- t_ready ------------------------- future events
   old trajectory + ongoing 100 Hz codriver while pending
                      |
                      +-- ready before nominal start -> waiting packet
                      |                                   |
                      +-- otherwise attempt handoff       +-- attempt at start
                                     |
                   accept only after validity/reserve/continuity checks
                                     |
                   active buffer changes (possibly between 10 ms ticks)
                                     |
                   next eligible codriver sample t_j = j*0.01
                                     |
                   sample state/reference -> compute/validate proposed input
                                     |
                   t_apply = t_j + tau_codriver -> application slew clamp
                                     |
                   new applied input drives subsequent plant RK4 steps
```

Sources: [A], 135–255, 279–421; [PL], 19–87; [CTRL], 62–174; [SOLVER], 33–82.
The diagram does not imply that `t_ready` must precede the prediction target. Either
ordering is possible. If accepted, the ordinary earliest acceptance time is
`max(t_release + physical_delay, original_packet.timestamps[0])`; rejection or termination
can mean no acceptance at all. Replacement of the single waiting slot is discussed below.

Startup is a separate gated case: prepare plan 0 at t=0 with estimate=0 and no forecast,
install it at t=0, and preposition its first nominal command before moving physics.
Measured startup work is retained but contributes no runtime availability delay or replay
entry ([A], 105–133; [PL], 27–30; [DT], 35–37).

## 3. Timestamp definitions and sources

`perf_counter()` supplies monotonic host wall-clock readings; only differences are retained
in these paths. `process_time()` supplies CPU durations, not physical event timestamps.
There is no mapping from an absolute host-clock epoch to a vehicle-clock epoch.

| Requested timestamp | Exact current meaning and source | Classification / retention |
|---|---|---|
| `t_measure` | Planner receives current `x` at `release()` time `t`. Packet `planner_sample_time` and `planner_release_time` are both that `time`; `source_sampled_state` is retained ([A], 169–171; [PL], 41–54, 77–86). | Simulated physical sample time; perfect state. No separate sensor acquisition, transport delay or estimator timestamp. |
| `t_release` | Fixed planner releases use `planner_index * planner_dt`, normally 0.1 s; idle urgent releases can occur outside this grid ([A], 364–372). | Simulated scheduled/actual launch time; `release_time` in plan events and `time` in releases. A skipped nominal release is a miss, not a new plan. |
| `t_prediction_target` | `time + estimate`; logged as `predicted_completion_time`, stored as `intended_handoff_time`, and used as original `timestamps[0]` ([PL], 40–47, 77–79). | Estimated future physical time. Neither measured solver finish nor a fixed application deadline. |
| `t_solver_start` | `IpoptSolver.solve`: local `start = perf_counter()` immediately before the backend call ([SOLVER], 33–43). Controller separately times its solver adapter ([CTRL], 96–98). | Host wall-clock reading, not exported as an absolute timestamp or scheduled physical event. No physical solver-start timestamp exists in the asynchronous packet/event schema. |
| `t_solver_finish` | Successful return is timed at `elapsed = perf_counter() - start` before adapter statistics/validation ([SOLVER], 44–69); exception branch also reports elapsed time. | Only backend `solve_time` duration is retained. Do not equate release + solve_time to packet readiness; prediction, preview, validation and gains also take time. |
| `t_packet_ready` | `completion = t + delay`; event `completion_time` and packet `actual_completion_time` receive it ([A], 172–193). | Scheduled simulated physical readiness. Default normal measured path uses `planner_total_time`; injected/zero/spike or diagnostic fixed/replay can override it. `completed` becomes true only when the event is processed. |
| `t_buffer_accept` | Successful `handoff(packet)` invokes `buffer.insert(packet,t)`; `handoffs` records `time`, `accepted`, and reason ([A], 135–162, 240–255; [PK], 191–201). | Actual simulated acceptance time, distinct from readiness. Startup insertion has no separate handoff row. No dedicated accepted-time field is written back into the original packet. |
| `t_packet_valid_from` | No field literally named `valid_from`. Sampling and insertion prohibit use before `timestamps[0]`; runner waits for it ([PK], 91–98, 196–200; [A], 250–255). | Existing implicit earliest-use boundary. Original start equals intended handoff; accepted late packet is trimmed so active `timestamps[0]` becomes acceptance time. `intended_handoff_time` stays unchanged. |
| `t_TVLQR_sample` | On a free codriver release, `tracker.update(x,buffer,t)` samples both state and active reference at `t`; row `time=t` ([A], 279–286, 324–325; [TR], 100–108). | Simulated release/sample time on the 10 ms grid. Busy ticks are skipped, not sampled later. |
| `t_command_ready` | Validated proposed command is available in host execution before scheduling `actuator_pending=(t+latency,proposed,row)` ([A], 313–362). | Local wall computation is retained as `total_time`; simulated ready time is scheduled as release + physical_latency. No separately logged ready event or extra actuator-transport stage. |
| `t_command_apply` | Due `actuator_pending` work applies at current `t`, with a second steering slew clamp; row gains `application_time`, `delta`, `a_cmd` ([A], 199–213). | Actual simulated application time; ordinarily equals scheduled command readiness within event tolerance. If termination intervenes, no applied row exists. |

**Verified wall-to-physical conversion.** Planner: [A], 62–69 and 172–180 chooses the
delay, then adds it to simulated release time. Codriver: [A], 356–362 chooses either
the full measured update duration (`codriver_delay=None`) or the configured duration,
then optionally replaces it with diagnostic timing. The study explicitly selects
`codriver_delay=None` for measured runs ([RUN], 147–153). The bare `AsyncConfig` default
is **0.0** for codriver delay, despite planner `latency_mode="measured"` ([A], 25–34).

**Timer boundary qualification.** `planner_total_time` encloses forecast, controller work,
packet construction and gain construction up to [PL], 69. The final duration-field packet
copy and returned event construction happen afterward (71–87). Study `RecordingPlanner`
bookkeeping also lies outside that timer ([RUN], 127–143). The measured codriver timer
ends before log-row construction and pending-event scheduling ([A], 322–362). In contrast,
an enabled `RecordingSolver` copies requests/results inside the controller call, so that
overhead contributes to planner duration ([CAP], 17–39). These are the actual boundaries
of the existing “full preparation/update” measurements, not total host-loop elapsed time.

## 4. Exact future-state prediction mechanism

**Verified: active-trajectory closed-loop forecast, initialized by the applied input.**
`TrajectoryPlanner` constructs `ActuationPredictor(controller.problem.model, track)`.
At release the runner resets `tracker.previous` to the actual applied `command` before
calling preparation ([A], 169–171). `predict` clones the tracker and starts from the
actual sampled six-state vector. The canonical ordering remains
`[vx, vy, r, e_psi, s_abs, e_y]`, with controls `[delta, a_cmd]`.

`RollingDelay` defaults to initial 0.017 s, median of the last ten observed durations,
clipped to [0,0.30] s ([PRED], 12–27). The observations are **physical readiness delays**
at processed planner completions, including failed preparations, not solver-only time
or accepted-handoff delay ([A], 215–229). Startup is not observed through this path.

The exact forecast loop is [PRED], 45–75:

1. Set `x = state_vector(state)`, `t = release`, `end = release + estimate`.
   Reject if there is no active packet or `end` exceeds its horizon by more than 1e-10 s.
2. Clone the tracker, including its previous applied command. Set the first forecast tick
   to `(floor((release + 1e-9)/tracker_dt) + 1) * tracker_dt`: the **next global codriver
   tick**, not a newly phased release-relative grid. Do not recompute feedback at release.
3. Until that tick, integrate under the currently applied command. At each forecast tick
   strictly before `end`, sample the existing active buffer and call the clone's `command`.
   A generic `forecast_command` hook exists, but `TrajectoryTracker` has no such hook;
   the fixed TVLQR path uses `local.command(x, *buffer.sample(t))`.
4. For each integration step choose `h=min(0.005, end-t, next_tick-t)` and curvature from
   the track at the predicted `s_abs` modulo track length. Hold that command and curvature
   through all four RK4 stages. Geometry is refreshed at the next forecast step.
5. Check finite states/domains at stages and endpoint; require vx in [0.5, maximum_speed]
   and Frenet denominator at least 0.01. Reject an invalid forecast or exhausted reference.
6. Return the endpoint state and the clone's last command. If the target is exactly a
   codriver tick, the loop ends without computing the command at that endpoint; returned
   input is the preceding held input. A zero duration returns the initial state/input.

The implemented RK4 map ([PRED], 33–42) is, with the same fixed `u,kappa` in each stage:

```text
a = f(x,u,kappa)
b = f(x + h*a/2,u,kappa)
c = f(x + h*b/2,u,kappa)
d = f(x + h*c,u,kappa)
x_next = x + h*(a + 2*b + 2*c + d)/6
```

Here `f` is the existing `SymbolicBicycle.derivative` ([SYM], 17–61), including its
configured smooth combined grip for this study. In particular, `vx_dot=a_cmd+r*vy`;
dynamic `a_cmd=Fx/m` is not kinematic `dvx/dt`. No physical parameters or equations are
introduced by this audit.

Forecast feedback uses the existing law ([TR], 84–98): heading error is wrapped;
`delta_desired = delta_nominal - K @ [e_y_error,e_psi_error,vy_error,r_error]` and
`a_desired = a_nominal - speed_kp*vx_error`. Box clipping precedes a steering clamp of
`steering_rate * tracker_dt` relative to the clone's last command. Reference states
interpolate linearly, while nominal controls and gains are held between their own nodes
([PK], 91–115). Gain times start at the packet's nominal start and are spaced by 0.01 s
([TR], 28–50); they need not coincide with the global codriver release grid.

The forecast state is the NLP's constrained initial state; the forecast preceding command
is the first input-increment/rate reference ([PL], 34–36; [CTRL], 67–98; [NLP], 80–84,
131–142, 227–228). The forecast interval is **outside** the new NMPC decision horizon.
There are no serialized prefix commands or prefix-equality constraints in this formulation.

**Verified limitations, consistent with [SPEC], 132–149:** the predictor receives no
`actuator_pending`, `last_application`, codriver busy state or timing trace. Future forecast
commands apply ideally at their ticks. It does not replay an already computed in-flight
command, model future codriver latency/skipped ticks, apply the runtime elapsed-application
slew clamp, or account for a waiting packet's future takeover. The active buffer is read
throughout the synchronous forecast; its arrays are immutable but it is not serialized as
a separate commitment snapshot. Even a same-time codriver update made just before planner
release is not used until physically applied: release resets `tracker.previous` to `command`.

`prediction_error` compares the forecast **target-time** state against actual state at
**readiness**, so it includes target/readiness time mismatch. Handoff errors instead compare
the actual state with the candidate reference sampled at the same acceptance-attempt time
([A], 137–159, 218–227). Neither diagnostic alone isolates model error from timing/control error.

## 5. Packet and buffer authority rules

**Verified.** Host construction does not grant authority. Before readiness a packet may be
in the result log and `pending`, but only `buffer.active` supplies the codriver reference.
Success requires controller validation of solver output, bounds and NLP constraints
([CTRL], 127–169), followed by valid packet/gain preparation ([PL], 38–72).

On processed completion, the runner observes the delay and then ([A], 215–255):

- Rejects a returned packet if fallback is already latched.
- Rejects one with less than 0.05 s remaining horizon reserve.
- Places an early packet into the single `waiting` slot until its original `timestamps[0]`.
- Otherwise attempts handoff immediately at the current physical event time.

At handoff the runner compares actual state against the candidate at that same time, wrapping
heading error. Absolute limits are `[0.5 m/s, 0.5 m/s, 1 rad/s, 0.20 rad, 0.75 m, 0.15 m]`
in canonical order. Exceeding any gives `handoff_mismatch`; otherwise the independent plant
validates the nominal state/control before insertion ([A], 135–162). These are existing
synthetic thresholds, not new guarantees.

`TrajectoryBuffer.insert` requires the validity flag, an ID newer than the active ID,
time at/after actual completion and first timestamp (1e-10 s tolerance), and at least
0.05 s reserve. It immediately replaces `active` with `packet.trim(time)` ([PK], 191–201).
There is no explicit age-from-measurement limit beyond these gates. A stale ID is rejected;
a late but otherwise admissible packet is trimmed, not re-solved, re-forecast or shifted
to a new horizon. Original `intended_handoff_time` and `predicted_handoff_state` are retained.
No field literally named `valid_from` exists, but the earliest timestamp already enforces
that aspect of validity. The metadata does not independently enforce equality of intended
handoff and first timestamp; the standard planner constructs them equal ([PK], 70–81;
[PL], 40–47).

Acceptance is not quantized to the codriver grid and does not itself change the actuator
command. It affects a later eligible `tracker.update`, possibly on the same timestamp
when acceptance precedes a coincident tick. Already pending codriver work is neither
cancelled nor recomputed; it can apply a command sampled from the previous plan after
the buffer has changed ([A], 199–213, 240–255, 279–286).

While preparation fails or a packet waits/is rejected, the existing valid packet remains
active. Reserve is `max(0,horizon_end-time)`: healthy >=0.20 s, warning >=0.05 s, critical
below 0.05 s, exhausted <=1e-10 s ([PK], 176–205). Critical reserve alone does not trigger
urgent replanning. An active packet may be used below the new-packet acceptance reserve
threshold until exhaustion. Packet endpoint sampling is allowed for validation, but the
buffer refuses tracking at its exhausted endpoint.

On exhaustion, the runner enters the existing baseline fallback only when vx is in
[1,3] m/s and lateral position is within the actual track widths; otherwise it stops with
`exhausted_outside_baseline_domain`. It rechecks fallback validity on updates and rejects
newly completed planner packets after fallback has latched ([A], 230–239, 265–299).
It does not synthesize a new trajectory or extrapolate the old one. An in-flight actuator
command is not explicitly cleared at fallback entry. This is the existing scheduler
behavior, not a verified real-vehicle recovery policy.

The runner holds one pending preparation and one completed future-dated packet. Waiting
does not mark the planner busy: another launch is allowed while `waiting` exists. Completion
can overwrite that slot, and every handoff attempt clears it ([A], 135–167, 250–255,
364–372). There is no multi-packet commitment queue or explicit supersession log. The
predictor sees only the currently active packet, not the waiting slot. These distinctions
matter when specifying a future commitment policy; D0 did not exercise those edge cases.

## 6. TVLQR and physical-command chronology

**Verified tie order** in each physical event-loop pass ([A], 197–377):

1. Apply due codriver work and update the actual held command.
2. Process due planner completion, and attempt any now-eligible waiting handoff.
3. Apply an explicitly configured state disturbance; check trajectory exhaustion/fallback.
4. Process the codriver tick. If busy, record a codriver miss and increment its grid index.
   If free, sample state and active reference, compute feedback, and validate the command.
5. Process the nominal planner release; if busy, record a planner miss. Otherwise launch
   in trajectory mode. An idle urgent request can launch when there is no nominal release.
6. If newly scheduled work has zero duration, repeat at the same physical timestamp before
   logging/integrating. Grid indices already advanced, so no duplicate tick is created.

Thus exact completion/release ties free the resource **before** a new release in this
asynchronous path. The old synchronous runner's `run_timed` has busy-first tie ordering
([SYNC], 74–75, 135); it is not the Task007C worker path and must not supply this audit's
chronology by analogy. A just-computed zero-latency command is applied on the subsequent
same-time pass, after the planner release in the first pass.

The codriver uses global `tracker_index*tracker_dt` deadlines from t=0. A pending command
causes skipped fixed ticks rather than a catch-up solve. The old physical command remains
held during that latency, even though the tracker has computed a new requested command.
The applied steering is clipped again relative to the old applied steering by
`steering_rate * (current_application_time - last_application_time)` ([A], 199–213).
This second clip can change the request. It is not a continuous actuator dynamics model.
Command validation occurs at computation/sample state; subsequent physical diagnostics
use the actual current state and applied command ([A], 313–324, 378, 421).

Control rows retain the plan ID/reference/error at **sample time**, the requested command,
computation duration, physical latency, application time and final applied command
([A], 324–362, 211–212). There is no dedicated application-state vector in each control
row; physical state histories support alignment. Unapplied work at termination is not
exported as a completed control row; runner output exposes planner `pending_at_end`,
not the full final actuator-pending record ([A], 437–454).

Urgent requests use two consecutive codriver observations with |ey error|>0.05 m or
|heading error|>0.10 rad, retain one pending bit, and do not create concurrent planner
work ([PRED], 78–92; [A], 287–290, 364–372). Urgent releases are not themselves guaranteed
to be on the 100 ms grid and must be considered separately by a future grid policy.

## 7. Event-grid and RK4 implications

**Verified.** The next plant interval ends at the minimum future candidate among
`t+plant_dt`, next codriver tick, next planner release, duration limit, pending planner
readiness, pending command application, waiting packet start, active horizon end, and
configured disturbance time ([A], 403–421). Candidate/event comparisons use 1e-10 s
tolerances. `plant_dt` is constrained to at most 0.005 s ([A], 45–60).

`DynamicBicycle.step(x,command,next_time-t)` executes one classical RK4 step with held
control, validates all derivative stages and the final state, and wraps final heading
([PLANT], 237–268; [RK], 10–18). Physical curvature is sampled at each derivative stage's
progress ([PLANT], 188–190). This differs from the predictor's curvature hold within
each at-most-5-ms forecast step, and from the NMPC shooting intervals' stage-preview
curvature hold ([SYM], 63–83).

Readiness therefore partitions plant RK4 **even if the packet is rejected or waits**, and
waiting eligibility creates a further boundary. The asynchronous cap is `t+plant_dt`, not
an independent `plant_tick*plant_dt` grid: a fractional event can shift subsequent capped
steps until another fixed event reanchors them. Changes in ready/application times can
alter integration partitions even when no immediate nontrivial command change occurs.

**Interpretation.** Timing-history sensitivity in this simulator contains both control
chronology and numerical partition effects. Neither D0 nor the existing Task007C-R
evidence isolates every continuous-time causal contribution ([CR-SPEC], 87–98;
[CR-RESULTS], 263–267). Adding fixed buffer handoffs alone would not remove ready-time
RK4 boundaries while readiness remains a scheduler candidate. Any future decision to
decouple integration from availability is a separate explicit semantic change.

## 8. Existing deterministic timing/replay capabilities

**Verified reusable code, not newly executed evidence:**

| Component | Current capability and limit |
|---|---|
| `AsyncConfig.delay` ([A], 62–69) | Normal measured, injected, zero and a selected-plan spike. Planner normal measured availability uses preparation duration, not just IPOPT. |
| `DiagnosticTiming` ([DT], 11–47) | Optional fixed or per-launch replay sequences for planner and codriver availability. Nonnegative finite values; fixed mode has one duration per channel; one-event planner perturbation returns a new schedule. |
| `AsyncRunner(..., timing=...)` ([A], 75–85, 172–176, 356–362, 433–434) | Imposes physical availability while still computing/timing the actual controller. Explicit `diagnostic_trace_exhausted` stop. No default-path timing substitution when absent. |
| `task007cr.audit.audit` ([TRACE], 13–44) | Extracts logged planner `physical_delay` and applied-control `physical_latency`, checks release/completion and release/application differences, and preserves round-trip floats. Existing function also writes historical manifests; it was read, not invoked in D0. |
| Study workers ([CR-RUN], 126–152; [RUN], 145–173) | Compose unchanged plant/controller/tracker with fixed/replay timing and optional single-event perturbation. Existing CLI fixed defaults are planner35 ms/codriver1 ms ([CLI], 15–20). |
| `RecordingSolver`, `reconstruct` ([CAP], 17–79) | Captures exact NLP initial guess, parameters, prior solution, returned solution, graph, bounds and options. Capture cost lies inside preparation; file output is separate. This is numerical solver replay, distinct from closed-loop timing replay. |
| `task007cr.compare.pair` ([COMPARE], 55–95) | Compares physical channels on identical grids or common timestamps without interpolating states; compares requested/applied controls and accepted handoff times. Existing comparison tolerances and prefix coverage must remain visible. |

Planner replay index is `plan_id-1`, excluding startup. Codriver replay uses `len(controls)`
when a free launch occurs; because only one command can be pending and the next cannot
launch until it is applied, that is the next launch index during continued execution.
Skipped planner/codriver releases consume no entry ([DT], 35–40; [A], 279–282, 360–370).
Stored release-time arrays in extracted traces are provenance, not a forced event schedule:
workers inject the delay arrays and let the scheduler determine actual releases.

Finite traces have no padding, cycling or extrapolated tail. Historical codriver traces
contain applied rows, so they cannot reconstruct an unexported final in-flight command
([TRACE], 58–62). A transferred trace can cover only a censored prefix. Startup stays gated;
the rolling estimator still observes imposed readiness delays; buffer rules still apply.
Fixed35 ms availability is **not** an implemented fixed-handoff Architecture C: early
packets still wait for their estimated start, late packets can be accepted later, and
35 ms is not aligned with the 10 ms codriver grid.

Existing tests read for contract coverage: [TEST-T], 89–128, 173–184, 213–218;
[TEST-A], 57–139; [TEST-D], 28–71, 111–131. They cover forecast feedback/clone isolation,
buffer validity, physical movement under busy planning, separate misses, early waiting,
fixed/replay dispatch and trace exhaustion. They were **not rerun** in D0. Historical
repeatability outcomes in [CR-HANDOFF], 18–40 are prior evidence, not fresh verification.
Fresh worker single-thread configuration precedes numerical imports in [RUN], 28–30,
53–62; future measured runs must retain serialized execution and actual backend checks.

## 9. Architecture B implementation gap

**Verified overlap:** if B means “propagate the current state along the accepted APEX
trajectory using predicted TVLQR until a future target,” that mechanism is already
implemented by `ActuationPredictor`. Adding a second predictor under a new name would
not establish a materially different architecture. The old trajectory already remains
active while a result is pending, and the new NLP already begins at a future predicted state.

**Interpretation: potentially material differences requiring specification.** A strict
committed prefix could additionally mean one or more of the following; none should be
inferred as authorized mathematics:

- An explicit immutable description of what remains authoritative until a selected
  handoff, including an existing waiting packet and its supersession policy.
- Replay of the known in-flight command and scheduled application, starting from actual
  applied input and last application time, then a defined assumption about future
  codriver latency, missed ticks and application-time slew clipping.
- A prefix of fixed actuator inputs, or a frozen feedback policy with state-dependent
  commands. These are different commitments: future actual TVLQR commands are not known
  at planner release because they depend on future physical states.
- Locking prefix inputs inside the new NLP instead of forecasting outside its horizon.
  The current parameter vector contains one prior command, not a command sequence, and
  its only initial equality fixes the forecast state ([NLP], 80–84, 131–151, 227–228).
  Adding a constrained prefix would change the formulation and cannot be silently
  reconciled with frozen mathematics/horizon semantics.

Thus a predictor/commitment chronology improvement may be materially different, but the
name “committed-prefix prediction” alone does not define it. Reuse the existing model,
tracker clone, buffer sampling and RK4 forecast. Specify the additional guaranteed
information and authority interval before changing any code or claiming a B improvement.

## 10. Architecture C implementation gap

**Verified overlap:** earliest timestamp gating, one waiting slot, immutable packets,
time-based interpolation, late trimming and a separate high-rate command scheduler exist.
A new `valid_from` spelling alone would not create fixed future handoffs.

**Interpretation: changes needed for a materially fixed handoff policy:**

1. Define the future grid-aligned commitment time from actual release, including urgent
   off-grid releases. Examples 30/40/50 ms in [RESUME], 53–59 are documented future choices,
   not a selected rule. An offset plus an off-grid release is not automatically grid aligned.
2. Make the predictor target, packet start/intended handoff and authority commitment agree
   with that chosen time. Current target is a rolling median estimate, not a fixed offset.
3. Keep readiness and authorization-to-take-over distinct. Early readiness can reuse waiting;
   late readiness needs an explicit policy (drop, next approved grid, retain old plan, etc.).
   Current late trimming accepts at variable readiness when otherwise valid, so it does
   not enforce a fixed deadline. Exact deadline-tie ordering must be specified.
4. Define waiting-slot supersession, active-plan reserve coverage, fallback behavior, and
   whether planner busy and handoff waiting are separate states. Avoid silently converting
   the current single-slot behavior into a queue.
5. Define what “handoff” guarantees: buffer reference authority at a tick, or actual actuator
   command application. Fixed buffer acceptance alone leaves codriver delay, skipped ticks
   and old in-flight command application variable. Do not imply a fixed actuator deadline
   without separately specifying it.
6. Decide explicitly whether raw readiness should still split physical integration; preserve
   the existing behavior unless a separately reviewed numerical scheduling change is required.

The buffer's first timestamp can support an earliest-use boundary, but an explicit committed
handoff/expiry contract and logs may be useful to distinguish planned handoff, readiness,
acceptance, first new-plan sample and first new-plan application. This is a design
recommendation, not a decision to change the packet schema. No C policy was implemented.

## 11. Relevant source files and functions

Line references identify the inspected working tree, not a claimed clean Git revision.
All links resolve under the current repository root.

| Key | File / principal functions and lines |
|---|---|
| A | [asynchronous.py][A] — `AsyncConfig` 18–69; `AsyncRunner` 72–454; nested `handoff` 135–162 and `release` 164–195; event loop 197–432. |
| PL | [planner.py][PL] — `TrajectoryPlanner.prepare` 19–87; forecast/model composition 13–17. |
| PRED | [prediction.py][PRED] — `RollingDelay` 12–27; `ActuationPredictor` 30–75; `UrgentReplan` 78–92. |
| PK | [packet.py][PK] — `TrajectoryPacket` 10–164; `sample` 91–115; `trim` 131–157; `TrajectoryBuffer` 167–206. |
| TR | [tracker.py][TR] — `TVLQR.compute` 28–50; `TrackerConfig` 53–66; clone/command/update 77–119. |
| CTRL | [controller.py][CTRL] — `MPCController.compute_control` 62–170; `_finish_timing` 172–174; `make_mpc` 221–235. |
| NLP | [problem.py][NLP] — defaults 25–37; initial equality/stage constraints 80–153; parameter packing 227–228. |
| SOLVER | [ipopt.py][SOLVER] — `IpoptSolver.solve` 33–82. |
| SYM | [symbolic_model.py][SYM] — `SymbolicBicycle` derivative/domain 17–61; `rk4` 63–83. |
| PLANT / RK | [dynamic_bicycle.py][PLANT] — geometry 188–190, `derivative`/`step` 237–268; [integration.py][RK] — `rk4_step` 10–18. |
| DT / SYNC | [diagnostic_timing.py][DT] — `DiagnosticTiming` 11–47; [timing.py][SYNC] — separate synchronous `run_timed` 40–209. |
| RUN / CLI | [resumed worker run.py][RUN] — `dispatch` 12–50, composition 91–173; [run_task007c_resume.py][CLI] — explicit CLI defaults 9–26. |
| CR-RUN / TRACE | [Task007C-R run.py][CR-RUN] — timing injection 126–152; [audit.py][TRACE] — `audit` timing extraction 13–44. |
| CAP / COMPARE | [snapshot.py][CAP] — `RecordingSolver` 11–69, `reconstruct` 72–79; [compare.py][COMPARE] — `pair` 55 onward. |
| TEST-A / TEST-T / TEST-D | [test_async_chronology.py][TEST-A], [test_trajectory_tracker.py][TEST-T], [test_diagnostic_timing.py][TEST-D] — existing contracts cited in section 8, inspected only. |

Documentation cross-checks: [AGENTS.md][RULES]; [CODEX_HANDOFF.md][HANDOFF], 1–36, 95–100;
[PROJECT_ROADMAP.md][ROADMAP], 12–18, 45–47; [ASYNC_PLANNER_CODRIVER_SPEC.md][SPEC], 23–185;
[TASK007C_HANDOFF.md][C-HANDOFF], 1–3 (historical gate);
[TASK007C_R_REPRODUCIBILITY.md][CR-SPEC], 8–24, 80–98;
[TASK007C_R_HANDOFF.md][CR-HANDOFF], 6–15, 74–81;
[TASK007C_R_RESULTS.md][CR-RESULTS], 47–60, 263–275;
[TASK007C_RESUMPTION.md][RESUME], 11–38, 53–75;
[TASK007C_RESUMED_RESULTS.md][C-RESULTS], 258–277, 371–400.

## 12. Known ambiguities and unresolved questions

**Observed discrepancies / qualifications:**

- The older handoff/roadmap records stop-for-review; the new D0 assignment supplies candidate
  acceptance and authorizes this audit only. This chronological difference is disclosed;
  old documents, defaults and evidence were not rewritten.
- The phrase “committed-prefix prediction” risks duplicating existing feedback forecasting.
  The complete Task007D scientific brief is referenced by D0 but was not included as a
  separate full B/C specification in this assignment or found as a Task007D repository
  document during the scoped file inventory. D0's B/C descriptions and prior document-only
  proposals do not settle the implementation choices in sections 9–10.
- Nominal start is an implicit validity boundary, not a hard fixed handoff deadline; there
  are no separate exported absolute solver start/finish or command-ready timestamps.
- Predictor causality omits known pending commands, waiting takeovers and nonideal future
  codriver timing. This is documented existing behavior, not evidence of a new bug or an
  authorized correction. Which omissions B must address remains an orchestrator decision.
- Existing one-slot waiting behavior does not define a general commitment/supersession
  policy. Fallback rejection is explicit in the pending-completion branch; `handoff()` itself
  has no independent mode guard. The standard forecast checks horizon coverage, but D0 did
  not prove every possible waiting/fallback overlap unreachable for injected planners.
- “Full” timers exclude the specific post-timer bookkeeping described in section 3.
  Exact future benchmark boundaries should be settled without relabeling prior evidence.
- Fixed acceptance would not by itself fix actuator timing or remove integration-partition
  dependence. No stronger deterministic/safety conclusion follows from this source audit.

**Questions for the next assignment, not blockers to D0:** define the committed object
(trajectory policy versus actuator sequence), commitment interval, handoff meaning, late
result policy, urgent-release alignment, pending-command treatment and future driver-delay
assumption. Confirm whether prediction remains outside the frozen N=8 horizon and whether
the rolling estimator remains diagnostic or still selects any target. No choices have
been silently made here.

## 13. Recommendation for the next bounded implementation subtask

**Recommendation only:** the Engineering Orchestrator should first resolve the B/C contract
questions above and issue one bounded assignment. A suitable first implementation task,
once explicitly authorized, is an opt-in prediction/commitment interface that reuses
`ActuationPredictor` and makes the chosen release-time applied/pending-command information
explicit, while preserving the current default path. Its scope must state whether it only
captures that information or changes forecast chronology; these are different deliverables.
Do not combine that task with fixed-handoff scheduling, NLP prefix constraints or benchmarking.

Recommended later verification for that bounded task: focused deterministic cases for a
pending command, coincident/just-before/just-after ticks, target at a tick, skipped codriver
deadlines, exhausted reserve, and unchanged default-path replay. Reuse the existing
zero/injected/measured dispatch contracts and Task007C-R replay mechanisms; wall-clock
measurements must not become exact CI assertions. These tests were not added or run in D0.

D0 verification passed: this document is readable, contains all 13 required sections,
and its 32 source-link targets and anchor line numbers resolve. The new-file Git diff
was inspected and its whitespace check produced no diagnostics. Before/after SHA-256
comparison preserved all 394 existing Git-listed tracked and nonignored untracked files:
zero existing files changed or disappeared; this document was the sole addition. The
initial 24 preexisting Git-status entries were preserved. This is not a fresh bulk audit
of ignored experiment archives; no evidence-writing script was invoked. No handoff,
decision log, roadmap, Python source or production default was edited.
**D0 stops here; no next phase is executed.**

[A]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/simulation/asynchronous.py:18
[PL]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/trajectory/planner.py:13
[PRED]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/trajectory/prediction.py:12
[PK]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/trajectory/packet.py:10
[TR]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/trajectory/tracker.py:18
[CTRL]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/mpc/controller.py:62
[NLP]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/mpc/problem.py:25
[SOLVER]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/optimization/solvers/ipopt.py:33
[SYM]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/control/mpc/symbolic_model.py:12
[PLANT]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/models/vehicle/dynamic_bicycle.py:188
[RK]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/models/integration.py:10
[DT]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/simulation/diagnostic_timing.py:11
[SYNC]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/src/apex/simulation/timing.py:40
[RUN]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/scripts/task007c_resume/run.py:12
[CLI]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/scripts/run_task007c_resume.py:9
[CR-RUN]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/scripts/task007cr/run.py:126
[TRACE]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/scripts/task007cr/audit.py:13
[CAP]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/scripts/task007cr/snapshot.py:11
[COMPARE]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/scripts/task007cr/compare.py:55
[TEST-A]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tests/unit/test_async_chronology.py:57
[TEST-T]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tests/unit/test_trajectory_tracker.py:89
[TEST-D]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tests/unit/test_diagnostic_timing.py:28
[RULES]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/AGENTS.md:1
[HANDOFF]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/CODEX_HANDOFF.md:1
[ROADMAP]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/PROJECT_ROADMAP.md:1
[SPEC]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/ASYNC_PLANNER_CODRIVER_SPEC.md:23
[C-HANDOFF]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/TASK007C_HANDOFF.md:1
[CR-SPEC]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/TASK007C_R_REPRODUCIBILITY.md:8
[CR-HANDOFF]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/TASK007C_R_HANDOFF.md:6
[CR-RESULTS]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/TASK007C_R_RESULTS.md:47
[RESUME]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/TASK007C_RESUMPTION.md:11
[C-RESULTS]: /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/docs/TASK007C_RESUMED_RESULTS.md:258
