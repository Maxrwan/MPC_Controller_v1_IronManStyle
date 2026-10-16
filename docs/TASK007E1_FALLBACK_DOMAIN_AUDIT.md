# Task007E-1 — shared fallback domain and trajectory availability

**WORK_COMPLETE_PENDING_REVIEW.** Read-only technical audit of
`529459090021d06a869378e72e4abec6e7f00d3d`, following accepted
[E0 closure](TASK007E0_VIS1_CLOSURE.md). No controller, scheduler, model, fixture, exporter,
default or assertion changed. No tests, simulations, forecasts or timing replays were executed.

**Recommendation:** Architecture A may proceed to Engineering Review for **E-2 manifest
preparation as a bounded synthetic research baseline**, with the limitations below. This audit
does not establish a new invalid-model-propagation or packet-authority defect that blocks that
preparation. It does establish that trajectory availability and safe fallback recovery are not
guaranteed. No freeze, formal acceptance, hardware readiness or E-2/E-3 execution is implied.
C70 remains experimental for future Efficiency research.

The [fallback register](task007e/e1/fallback_domain_register.json) preserves conditions,
transitions, source/fixture hashes and retained observations. The
[safeguard matrix](task007e/e1/safeguard_verification_matrix.json) maps 20 safeguards to exact
source lines, existing tests, coverage limitations and future obligations.

## Implemented domain: admission is narrower than plant validity, not a recovery proof

The asynchronous runner constructs its own baseline controller, using the plant parameters,
the tracker steering-rate limit and a 10 ms period. Its default reference is the **centerline
at 2 m/s**, not the racing Planning line. The separate `MPCController.finalize_control` fallback
belongs to the synchronous application path; `TrajectoryPlanner.prepare` does not call it.
Do not count synchronous fallback tests as direct verification of asynchronous transitions.

| Condition / layer | Actual implementation | Limit of the claim |
|---|---|---|
| Fallback admission | At exhaustion: `1 <= vx <= 3` m/s and `-right_width <= e_y <= left_width`; same check before each idle fallback computation | Inclusive CG corridor only; no footprint or 0.08 m tracking-margin shrink |
| Finite state/input | Canonical six/two finite values; nonnegative s_abs | Admission expression itself does not enumerate these; controller/plant validators do |
| Baseline reference | Reference speed in [1,3]; default 2 m/s; finite curvature, positive actual speed for feedforward | No bound on curvature magnitude/slew, heading error, vy, r or beta for small-slip design validity |
| Lateral LQR | Static-load linear design; ZOH at 0.01 s; DARE gains at 1/2/3 m/s; interpolation, clamping scheduling speed only | Standalone baseline allows positive actual speed outside [1,3]; the runner supplies the domain gate |
| Longitudinal PI | Kp=1, Ki=0.5; conditional-integration anti-windup; finite inputs and positive dt | `a_cmd=Fx/m`, while `dvx/dt=a_cmd+r*vy`; command saturation alone does not bound the next speed |
| Commands | Baseline clips steering to ±0.4 rad and acceleration to [-3,+2] m/s²; runner clips to tracker/MPC grip/load-aware box | Synthetic limits, not identified actuator capability |
| Steering rate | Baseline nominal-step limit, then actual-application clamp at 1 rad/s using elapsed time since prior application | No actuator position/dynamics model; fallback internal state is not continuously synchronized to actuator motion |
| Physical model | vx in [0.5,6] m/s (1e-10 roundoff tolerance), finite states/forces, `1-kappa*e_y > 0.001`, axle loads >1e-9 N | Not the same as the fallback [1,3] admission rectangle or predictor denominator threshold 0.01 |
| Racing tires | Smooth combined grip, normal-load proportional allocation; reject `abs(Fx) > (1-1e-6)*mu*Fz`; lateral force uses smooth envelope | No LQR small-slip guarantee, sideslip cap, tire-identification claim or stability proof |

Source: [runner construction](../src/apex/simulation/asynchronous.py#L123),
[admission and command validation](../src/apex/simulation/asynchronous.py#L373),
[baseline controller](../src/apex/control/baseline/controller.py#L59),
[LQR](../src/apex/control/baseline/lqr.py#L27),
[references](../src/apex/control/baseline/references.py#L17),
[PI](../src/apex/control/baseline/speed.py#L34),
[plant validation](../src/apex/models/vehicle/dynamic_bicycle.py#L127),
[grip](../src/apex/models/tire/grip.py#L32) and
[MPC input bounds](../src/apex/control/mpc/problem.py#L173).

The 1–3 m/s/corridor guard is **not sufficient to certify recovery throughout that set**.
Independent checks reject explicitly invalid model states/commands, but no controlled-invariant
set, nonlinear recovery envelope or safe stopping trajectory is computed. Curvature-dependent
feedforward may saturate; arbitrary heading/lateral/yaw states can satisfy the entry rectangle
without satisfying the controller's approximation assumptions. Forward Frenet progress is not
guaranteed merely by positive vx. The documented static-stiffness/small-slip approximation
neglects reference derivatives, load variation and higher-order coupling; frozen linear poles
do not establish nonlinear or time-varying stability. See [baseline specification](LQR_BASELINE_SPEC.md).

During codriver-busy ticks, no new PI update occurs. Each eventual computation uses nominal
0.01 s, not total elapsed busy time. The PI aims at 2 m/s; it is not emergency braking to rest.
The physical model itself rejects sufficiently low speed and contains no standstill transition.

## Physical event order and availability state machine

At each physical timestamp the existing order is:

1. Apply an already-due actuator request, with elapsed-time steering clamp and original source ID.
2. Resolve planner completion; observe its physical delay. A may accept, wait or reject; C records readiness.
3. Process A's waiting nominal start, then C's due fixed acceptance/miss.
4. Apply an authorized disturbance, then check exhaustion and fallback eligibility.
5. Skip a busy codriver tick or compute the next trajectory/fallback request and validate it.
6. Service the nominal planner opportunity first; otherwise an eligible latched urgent request.
7. Continue zero-duration events at the same timestamp, or validate the held pair, record and propagate.

This follows [the event loop](../src/apex/simulation/asynchronous.py#L284), not a proposed scheduler.

| State / event | Condition | Existing transition/action |
|---|---|---|
| Startup | Initial preparation fails | `startup_failed`; no physical/control rows; vehicle not launched |
| Healthy reserve | R >= 0.20 s | Normal tracker and planner schedule |
| Warning | 0.05 <= R < 0.20 s | Log warning; **no** automatic reserve-triggered action |
| Critical | 1e-10 < R < 0.05 s | Existing packet remains usable; no extrapolation or automatic braking |
| New packet | Ready, nominal timeline reached | Continuity/model/buffer checks; accept only with >=0.05 s reserve; rejection preserves old authority |
| A early readiness | Completion precedes nominal start | Store one waiting packet; hold old authority until the nominal start; readiness is not acceptance |
| Planner busy | Nominal or urgent demand arrives | Log nominal miss / retain urgent latch; no overlap or cancellation; physics and available codriver continue |
| Failed preparation | Solver, prediction or gain validation fails | No new packet; pending preparation resolves without a replacement |
| C deadline | Packet not ready at fixed target | Record miss; solve remains busy until completion; late result never activates |
| Exhaustion | R <=1e-10 after due handoffs | Check speed/corridor eligibility before any new trajectory sampling |
| Ineligible at entry | Eligibility false | Record `valid_domain=false`; `exhausted_outside_baseline_domain`; break before baseline computation/next propagation |
| Eligible entry | Eligibility true | Latch `baseline_fallback`; initialize previous steering from applied command; retain pending actuator work |
| Fallback execution | Idle codriver tick due | Recheck eligibility; compute baseline, clip, plant-validate and schedule request |
| Fallback invalidity | Tick-time speed/corridor check fails | `fallback_outside_validity_domain`; stop without that new baseline request |
| Fallback latched | Later planner result / release opportunity | Reject late result as `fallback_latched`; no new planning or automatic return to trajectory mode |
| Model/input failure | Current pair, RK4 stage or final state invalid | Catch `ModelValidationError`/`ValueError`; `model_or_control_validity_failure`; no invalid returned RK4 state committed |

R is `max(0, horizon_end_time-t)`; missing buffer also has zero reserve. These are the
actual [buffer thresholds and guards](../src/apex/control/trajectory/packet.py#L180).
The **new-packet** 50 ms requirement does not prohibit continued use of an already-active
critical packet. Expiry is explicitly included in the next-event candidates.
`TrajectoryPacket.sample` allows the terminal point for evaluation; `TrajectoryBuffer.sample`
rejects exhausted authority, including that endpoint. Offline endpoint references therefore do
not prove executable authority at zero reserve.

Buffer acceptance checks valid flag, newer ID, availability, fixed eligibility where applicable
and remaining reserve. It trusts the producer's validation contract: the controller independently
checks solver result shape/finiteness, nonlinear residuals and bounds; the planner creates a
packet only after success and finite gain preparation. Handoff additionally checks wrapped
canonical mismatch limits [0.5,0.5,1,0.20,0.75,0.15] and nominal plant diagnostics. These limits
are synthetic continuity tolerances, not a safety tube. See
[planner failure handling](../src/apex/control/trajectory/planner.py#L37) and
[solver-output validation](../src/apex/control/mpc/controller.py#L127).

## Pending commands and what “validated” means

Commands requested from the old packet may apply after a new handoff or fallback entry. The
application record retains the request's original plan ID/mode; it is not reassigned to the new
packet. This is committed held-command physics, not a fresh sample of expired packet authority.
No pending command is erased at exhaustion. A busy codriver delays fallback computation too.

The candidate is checked against the plant at generation. At application the runner assigns
the rate-clamped command and appends its application record **before** subsequent current-pair
diagnostics. Before motion, diagnostics validate the held pair; RK4 checks every stage and final
state. An application record at a terminal timestamp alone does not prove a subsequent physical
interval or successful current-state validation. An invalid exhaustion gate can stop between
the application phase and propagation. This distinction must survive hardware-interface design.

There is **no separate application-time baseline [1,3]/corridor gate**, nor continuous membership
check during holds. The implementation can retain a command while leaving that admission
rectangle between computations, as long as the wider physical-model checks pass. Consequently
“fallback always remains within [1,3] and in track” is unsupported. No new counterfactual was
executed, and this audit does not relabel this sampled policy as a demonstrated invalid-model
propagation. If continuous membership is required for a later claimed profile, this implementation
does not establish it and requires separate review/design/testing.

The synchronous [application-state test](../tests/unit/test_mpc.py#L254) explicitly checks a
speed-domain crossing during solver latency; it does **not** exercise this asynchronous delayed
fallback path. Direct tests of pending requests across fallback entry and subsequent domain exit
remain missing. Existing [old-command handoff tests](../tests/unit/test_fixed_handoff_scheduler.py#L127)
support provenance/ordering across handoff, not a broader recovery guarantee.

Fallback telemetry uses `mode=baseline_fallback`, retains the last packet ID, and fills
reference=current state/error=zeros. Those placeholders are **not APEX tracking performance**.
The VIS offline gate flags any fallback as trajectory exhaustion. Core trajectory-mode boundary
checks are flags; the VIS scientific campaign checks occur after the worker returns, not as a
continuous emergency-stop supervisor. See [runtime logging](../src/apex/simulation/asynchronous.py#L418),
[VIS analysis](../scripts/task007dvis/analysis.py#L15) and
[worker chronology](../scripts/task007dvis/worker.py#L91).

## Architecture A: demonstrated behavior versus permitted failure mechanisms

Retained controlled A completed its full lap in 31.171900 s: 622 runtime releases, 621 accepted
handoffs and no fallback; the final preparation was outside observed completion coverage.
Measured A completed in 31.317756 s: 620 releases/accepted handoffs, two planner-busy misses,
no fallback and maximum observed preparation 193.324 ms. These successful records do not prove
availability under all delays. Fixed-deadline misses are not an A metric.

Unlike C70, A may accept a late result if it remains available, has enough reserve and passes
validation. Nevertheless sustained delays, busy releases, failed solves, failed prediction/gains,
repeated mismatch/model/stale/reserve rejection, or simply no valid replacement before expiry
can remove trajectory authority. There is no guarantee or upper bound on solver completion.

The rolling estimate starts at 17 ms, uses a ten-completion median and caps its **estimate** at
300 ms; it does not cap computation duration. Predictor A forecasts only within the active horizon,
clones the tracker and rejects unsupported predicted states; failure yields no replacement.
It retains its ideal future-codriver timing approximation. Urgent replanning needs two consecutive
tracking-error samples above 0.05 m lateral or 0.10 rad heading, not low reserve. One latch waits
while busy; a persistent unbroken error episode does not create unlimited fresh requests.
A can release off-grid when eligible; C waits for an eligible global 10 ms tick. See
[predictor/estimator](../src/apex/control/trajectory/prediction.py#L50) and
[urgent handling](../src/apex/control/trajectory/prediction.py#L188).

Prior [isolated chronology evidence](../tests/unit/test_async_chronology.py#L79) demonstrates
fallback at 0.4 s with a 450 ms injected planner delay, a 400 ms straight-fixture horizon and
2 m/s state. It is not an N8/gamma2 racing A failure. No new A exhaustion run, replay or timing
history was created. Racing-speed A exhaustion and broad delayed-fallback transitions remain
unsupported experimental conditions.

## C70's recorded stop uses the shared gate correctly

Fresh read-only reconciliation confirms **485 releases, 455 accepted handoffs, 30 fixed misses,
22 later recoveries and eight consecutive terminal misses**. Packet 477 accepted at 47.870 s
expires at 48.670 s. Last reserve-event sample at 48.665 s is 0.005 s; the native terminal RK4
endpoint is **zero reserve and vx=5.960492971 m/s**. This incorporates E0's timestamp erratum.

The guard is false. Source breaks before setting baseline mode or invoking its controller;
all recorded state/control modes are trajectory, with no baseline-mode record. Stop reason is
`exhausted_outside_baseline_domain`. Packets 478–484 never activate; packet 485's actual completion
and discard remain null, beyond coverage. There is no recorded post-stop physical propagation.

The later NumPy-boolean CSV serialization error is an existing research-tool defect. Raw,
segments, contexts and analysis survive, but the complete package and normal summary do not.
It is not the cause of exhaustion and was not repaired. No absent native-thread or forecast
observations are invented. See [original results](TASK007D_VIS1L_RESULTS.md),
[reproduction/provenance](TASK007D_VIS1L_REPRODUCTION.md) and
[E0 evidence](task007e/e0/evidence_matrix.json). Host-runtime root cause remains undetermined.

## Safeguard classification and verification applicability

| Classification | Relevant examples | Evidence boundary |
|---|---|---|
| Implemented and supported | Buffer no-extrapolation/stale/reserve checks; failed-plan isolation; busy chronology; actuator/model guards; LQR/PI equations | Exact source and existing focused assertions; retained four VIS traces |
| Implemented, insufficiently tested | Delayed fallback application/domain exit; fallback latch combinations; fallback telemetry interpretation | Synchronous tests and handoff tests must not be overgeneralized to async fallback |
| Documented assumption, not enforced envelope | Small-slip/static-load LQR, bounded reference variation, perfect-state recovery suitability | No full nonlinear invariant region or curvature/slip admission bounds |
| Absent or deferred | Reserve-triggered rescue, guaranteed availability, continuous corridor/swept-body safety, braking to rest, watchdog/cancellation/reentry policy | No such capability inferred from a simulator stop |
| Not applicable to present synthetic execution | Sensor/transport/hardware faults and real actuator enforcement | Mandatory before hardware; their absence prevents hardware-readiness claims |

The safeguard matrix supplies individual source/test references and separates the known exporter
defect from runtime correctness. No newly demonstrated incorrect packet activation, expired-buffer
sampling or invalid-model state propagation was found. This is a bounded audit finding, not proof
that all possible faults are excluded.

**Reused, not rerun:** 284 relevant cases in 13 baseline, chronology, buffer, model, tire, MPC,
latency and baseline-integration modules are a subset of the prior CX **709-pass** suite at
`935e98b7af6c2fda8458551f1fbcbddb3bf8932d` (597.59 s). Original JUnit status/node IDs and hash
were checked. Selected test contents, core/config/dependency tree and fixture hashes are unchanged.
Baseline two-lap integration tests use circle/oval fixtures with the linear tire plant; the
straight asynchronous fallback test uses racing tires. Neither proves racing-circuit fallback
coverage. Later VIS test evidence remains separately inherited from E0, not added to a new count.

Fresh audit checks matched 168 CX core/fixture hashes, 294 VIS source hashes, three later report
hashes and five Planning fixture hashes; directly used raw/segment/analysis/configuration/exit
files match retained manifests. Scientific workers remain revision
`8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae`, executable-identical to `c699057`; later reports are
`d55f203`. Python3.12.14/macOS26.5.1 arm64, NumPy2.5.3, SciPy1.18.1 and CasADi3.8.1 match the
recorded environment. No numerical package import or model evaluation was needed for this audit.

Local audit scripts/logs are ignored under `results/task007e/e1/5294590_audit/`; hashes and
source lines are committed in the register. JSON/reference/source-preservation checks and
`git diff --check` apply only to these documentation changes. Full numerical/formal verification
was not run. Existing broad formal evidence does not automatically verify later VIS export code.

## Freeze-readiness and mandatory later obligations

| Dimension | Technical disposition |
|---|---|
| Synthetic reproducibility | Existing A profile is a defensible candidate for exact manifest preparation with stated fixtures, timing and stop semantics |
| Simulation correctness | No new demonstrated blocker within audited scope; do not claim continuous admission-domain enforcement or complete fallback-transition coverage |
| Solver/timing robustness | Not guaranteed; finite reserve can exhaust and high-speed fallback is unavailable |
| Physical safety | Not established; no invariant/swept-body proof, independent supervisor or safe-stop mechanism |
| Hardware deployment | Not ready; synthetic/unidentified parameters and Mac timing are inadequate certification |

Before hardware, separately specify and verify: an identified vehicle/tire/actuator and estimator
uncertainty model; recovery or safe-stop behavior across the intended operating envelope;
application-time freshness/domain and held-input reachability checks; pending-command ownership
at expiry/fallback; independent watchdog and braking-to-standstill capability; continuous
swept-body/obstacle clearance and stopping distances; hardware timing/communications/worker-fault
handling. Tests must include domain edges, delayed requests, busy ticks, simultaneous expiry,
repeated preparation/rejection failures, fallback entry/exit and honest missing/fallback metrics.
These are requirements for later review, not implementations authorized here.

For the synthetic Performance decision, E-2 must bind the exact configuration and explicitly
exclude guaranteed fallback recovery, continuous safe operation after authority loss, hardware
safety and unseen-track generalization. E-3 must verify its reviewed revision and assess the
remaining transition/export gaps and accepted limitations. Primary APEX retains final acceptance.
No additional architecture decision is made; ADR-163's closure and deferrals remain in force.
**Stop after E-1 for Engineering Review.**
