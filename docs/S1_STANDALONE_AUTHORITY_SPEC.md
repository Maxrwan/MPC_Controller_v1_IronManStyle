# S1 — Standalone Synthetic Safety/Authority Supervisor Specification

**WORK_COMPLETE_PENDING_REVIEW — documentation and specification only.**
No supervisor, endpoint, test fixture, fault injector or adapter is implemented or executed here.
Primary approved the staged strategy and bounded scenario basis, subject to review; S1 acceptance
and implementation authorization remain pending.

## 1. Authority, immutable sources and accepted claim

The [separate S0 acceptance overlay](safety/s0/primary_acceptance.json) records Primary's scientific
architecture acceptance of exact S0 delivery `3747e0d9a7e834a5df34c4b089a5292c0a749fa4`.
The acceptance date is unknown and is recorded as null with reason. Neither today's date nor the
S0 commit date is substituted. Original [S0](S0_SHARED_SAFETY_SPEC.md), its WORK statuses, registers,
structural-check evidence and all nineteen NOT_EXECUTED scenario records remain unchanged.

Accepted architecture separates controller feasibility, accepted valid trajectory authority and
permission for actual application. It retains explicit operating/recovery/deceleration/stop domains,
conservative uncertainty, feasibility-based response selection, causal freshness and intervention,
application/hold checks, epochs, cancellation acknowledgement, critical latching, controlled reentry
and NO_VALID_POLICY. Architecture acceptance does not numerically establish any physical domain,
residual-risk budget, response time or physical guarantee.

Frozen Performance release/tag and main remain at `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
The immutable Efficiency F0 reference remains `eaa0a3398515a21f30a850de59a0b44c775fad4d`.
During temporary Safety drafting, independent Efficiency advanced to documentation-only
`ff34bd36897c4ed00b850a2d0255132bdebac5fd`. Safety did not write that checkout or create that
commit. This concurrent change is retained and separately recorded in validation; its runtime,
configuration, tests and dependencies remain unchanged.
No merge, racing-runtime change, dependency/test/source change or hardware work is authorized.
[Provenance](safety/s1/provenance.json) records exact S0 artifact hashes and immutable scientific
references. Historical E3 verification is not a pass for the unimplemented Safety layer.

The first component is a pure deterministic authority reducer independent of CasADi/IPOPT,
the racing controller, vehicle propagation, real clocks/transport/MCUs and unvalidated recovery or
braking policies. Synthetic protocol verification can eventually succeed without a braking system;
its accepted claim must then concern only demonstrated logical/synthetic protocol properties.

## 2. Three separately reviewed stages

| Stage | Proposed responsibility | Explicit boundary |
|---|---|---|
| S1-A | Pure reducer over Configuration, Snapshot and Event; logical decisions, leases, fault state and independent transition assertions. | No endpoint application. External fixture acknowledgements/rest evidence are labelled assumptions. |
| S1-B | Synthetic endpoint with separate local state, command lifecycle, cancellation, commit and acknowledgement behavior. | Only SIMULATED_APPLIED/SIMULATED_CANCELLED; no physical feedback or dynamics. |
| S1-C | Separately scoped extended scenarios, pending producer adapters and integration verification. | Each integration/experiment needs new authorization; no automatic controller merge. |

The [stage plan](safety/s1/staged_implementation_plan.json) and [review gates](safety/s1/review_gates.json)
require review between A and B, and separate scope/authorization for C. A review status alone never
authorizes another stage. WORK → ENGINEERING REVIEW → explicitly authorized VERIFICATION →
PRIMARY SCIENTIFIC ACCEPTANCE remains the governing sequence.

## 3. Exact proposed data boundary

[Interface contract](safety/s1/interface_contract.json) contains closed JSON Schema 2020-12 design
definitions for Configuration, ClockStamp, Estimate, Uncertainty, Evidence, Proposal, Packet,
Command, Permission, Cancellation, EndpointObservation, BarrierAck, Snapshot, EndpointSnapshot,
Event and Trace. Barrier installation acknowledgement is distinct from application feedback.
Required fields, null handling and extra-field rejection are explicit. These are proposed schemas,
not implemented runtime validators. Semantic rules and independent checks remain necessary.

Canonical SI state is `[vx,vy,r,e_psi,s_abs,e_y]` in `[m/s,m/s,rad/s,rad,m,m]`; control is
`[delta,a_cmd]` in `[rad,m/s²]`. Dynamic a_cmd remains Fx_total/m. S1 propagates no state and
converts no requested value into a physical actuator setting. Model/plant/controller boundaries stay
unchanged; even the toy state and control values in scenario tables are not vehicle identification.

Proposal readiness never grants authority. Packet acceptance requires explicit causal acceptance
evidence. A logical Permission binds command, original controller/packet, original generation epoch,
current permission epoch, policy/context evidence and a bounded interval. Reauthorization creates
a distinct permission, keeps original source identity and cannot extend original packet expiry.
Command submission, first grant request and explicit REAUTHORIZE are different operations.
Exact duplicate operations replay their prior outcome and cannot issue a second grant.

Evidence has three outcomes: SATISFIED, VIOLATED, UNKNOWN. All S1 fixture evidence is explicitly
SYNTHETIC_ASSUMPTION, bound to the current context and validity interval. Unknown mandatory evidence
denies dependent permission. No physical recovery/deceleration/stop or degraded continuation is
available by default; labelled positive fixture tokens prove only logical handling of an assertion.

## 4. Deterministic time, ordering and information

Control time is a nondecreasing integer tick with a configured exact rational period in SI seconds.
Keep source SI packet timestamps and mapped conservative tick bounds; do not derive authority from
N, scalar dt or optimizer horizon. Off-grid source times map outward. Unknown mappings deny dependent
authority, and clock reset changes clock/session identity. No invented hardware clock tolerance.

Packet/permission intervals are half-open `[start,end)`. Require application upper bound strictly
before end, latest application before end, and permitted hold no later than end. Check estimate age
at application and across hold using earliest plausible capture. Unknown freshness bound denies new
nominal authority. Required causal comparisons use conservative bounds, never future plant truth.
ADVANCE visits crossed lease/evidence/freshness boundaries even when no new command arrives.

[State/event invariants](safety/s1/state_and_event_invariants.json) defines phases and tie-breaks.
Each externally scheduled timestamp batch is sealed before evaluation. Known expiry, emergency,
invalid evidence and delivered revocation/cancellation precede permissive work. Positive observations,
barriers and acceptance are incorporated before grant evaluation; endpoint commit is later.
Within a phase, producer identity, sequence and event identity determine order. Causal outputs
cannot be backdated; newly found critical faults update the deny gate before any remaining commit.

Planned handoff may consume a matching same-batch acknowledged epoch barrier. If that barrier is
still unknown after positive-evidence processing, and no separately eligible bounded continuation
or response exists, take T09 before permissions/commits. Critical faults are acted on immediately.
No planned transition window silently authorizes a held physical input.

S1-A returns logical decisions and traces only. APPLICATION_CHECK never records application.
S1-B has a separate EndpointSnapshot and rechecks locally received session/epoch, cancellation,
lease, estimate/health and synthetic prior-input/constraint evidence immediately before commit.
An endpoint cannot know a host revocation until it is delivered. Host request, endpoint installation,
acknowledgement and commit timestamps remain distinct. A globally instantaneous revocation claim
would be false under delayed delivery.

## 5. State machine, unknowns and critical latches

All nine S0 states and T01–T14 are retained, with exact source/destination lists and additional
explicit guards in the invariant register:

| State | S1 interpretation |
|---|---|
| DISARMED | No nominal grant; explicit arming, eligible evidence and reset/session barrier required. |
| NORMAL | Current nominal authority/evidence admissible; each grant/application/hold remains conditional. |
| WARNING | Existing authority continues only if admissible; reviewed renewal/response evidence required. |
| RECOVERY | Named separately eligible recovery assertion and selection evidence; no assumed LQR basin. |
| DECELERATING | Named eligible joint policy and destination/transfer assertion; no invented braking law. |
| STOP_REQUESTED | Latched demand/request; not application or achieved rest. |
| STOPPING | Named stop assertion plus matching endpoint activation observation; not a send acknowledgement. |
| STOPPED_LATCHED | Independent rest/holding assertion; S1 fixture assertion carries no physical proof. |
| NO_VALID_POLICY | Required knowledge or eligible continuation/response unavailable; revoke unsupported grants and report the unresolved hazard. |

Emergency takes precedence. If stop eligibility is unknown, log T06 then T09 in one transaction;
no permissive action occurs between them. Rejected input does not erase a prior held value.
Unobserved application/cancellation and censored outcomes remain null with a reason. Sending
cancellation, simulation termination, a zero request, power removal or missing motion feedback
never proves stopping. No universal safe-zero, maximum-braking or power-disconnection response exists.

Fault latches and command identity history are part of explicit Snapshot input/output. Pure restart
checks retained snapshots; it does not prove disk or power-failure durability. Missing/corrupt
persistence denies arming and takes T09. Fresh estimates alone never clear critical faults.
The initial logical reentry route is T11 (independent synthetic rest assertion), T13 (authorized
clearance/reset and old-session queue invalidation), then T01 (new-session admission and explicit arm).
There is no direct NO_VALID_POLICY/STOPPED_LATCHED-to-NORMAL shortcut. T12 positive recovery reentry
still needs separately reviewed terminal, dwell/hysteresis and transition evidence.

## 6. First six scenario specifications and independent oracles

[Initial scenario oracles](safety/s1/initial_scenario_oracles.json) gives independent initial profiles,
named inputs, exact toy ticks, state paths, grants/rejections, reason codes and pass/fail assertions.
The tables are design documents; materializing executable Event fixtures requires the S1-A gate.
Every case is independent. Toy millisecond ticks and the toy age bound are arbitrary protocol data,
not intervention budgets, real publication latency or a certified Perception threshold.

| S0 scenario | Initial design claim | Deferred scope |
|---|---|---|
| V01 | Proposal gives no reserve; expiry boundary rejects authority/commit and explicitly records no-policy. | High/low-speed dynamics, reachability and physical response. |
| V05 | Missing/invalid/degraded/stale state, map/frame/clock/uncertainty failure denies new nominal grants; healthy input does not clear latch. | Estimator validation and validated degraded continuation. |
| V06 | Delayed/reordered/conflicting/duplicate command handling and later endpoint at-most-once behavior. | Real transport, slew and actuator behavior. |
| V07 | Old-source reauthorization requires a new current-epoch grant; unknown barrier/cancellation cannot be inferred. | Physical policy handovers and cancellation bounds. |
| V15 subset | Same-tick critical fault priority; cancellation at/before/after commit; undelivered revocation and delayed observation. | All T01–T14 positive cases, full collision cross-product, clocks/queues and hardware arbitration. |
| V19 subset | No-policy latch, restart retention, rejected reset, explicit synthetic rest/reset/arm path and old-session rejection. | Physical emergency/standstill/rest loss, durable storage, T12 terminal/dwell and full fault combinations. |

None is executed or accepted as full S0 scenario verification. The immutable wider V01–V19 register
remains the verification authority; all physical and unselected assertions remain deferred.

Expected outcome tables must be reviewed independently before implementation runs. A future oracle
must not call the reducer/endpoint or reuse its guard, sort, interval or transition helpers to
generate expectations. Check interval inequalities, unique grant/commit identities, immutable sources,
phase order, session/epoch and latch paths independently. Never regenerate golden traces from the
system under test. Preserve complete inputs, expected and actual traces, exact source/config hashes,
failures, unknowns and censored outcomes. Changing expectations requires reviewed rationale.

## 7. Pending Perception v0.3 adapter

No adopted v0.3 implementation is claimed. The pending adapter preserves capture/publication/receipt
timestamps and clock sessions/mappings, age, measured publication latency, state covariance or
bounded-error interpretation, DEGRADED quality, map identity, frame consistency and missing inputs.
Publication latency and receipt/transport latency are different observations. Invalid chronology
or an unavailable measurement stays explicit; receive time never freshens an old capture.

Covariance alone is not conservative reachable containment. A versioned interpretation/calibration
must justify any eligibility assertion. DEGRADED/stale state denies new nominal racing authority;
continued existing behavior needs a separately validated continuation policy, never an implicit
healthy fallback. The suggested approximately 50 ms age is an **unvalidated integration hypothesis**,
not an adopted default or certified safety limit. Its numerical review remains pending.

## 8. Coordination, unresolved decisions and release boundaries

Safety consumes actual timestamps, acceptance/health and endpoint evidence. It assumes no stage
count, uniform grid, solver completion policy or variable/fixed handoff. FIXED acceptance keeps
ready-at-deadline eligibility and rejects late completion; a missed deadline does not cancel a
running solve. Accepted trajectory authority is distinct from packet sampling tolerance.

Any later adapter must review differences from frozen application-before-fallback ordering and
old pending-command preservation. The proposed stricter epoch/half-open lease contract is isolated;
it does not silently revise TrajectoryPacket, historical readers, the scheduler or Performance.
Supervision overhead has no inherited timing equivalence with accepted Performance/F0.

The review-gate register lists every current blocker and all ten unresolved HW01–HW10 topics:
geometry/inertia, tire/grip, steering/motor/braking, sensing, clock/execution, communications,
watchdog/e-stop independence, power fail-state, swept environment geometry and low-speed/rest.
Physical domains, uncertainty/risk interpretation, intervention/freshness/watchdog budgets,
actuator response, rest/holding and reentry dwell remain unestablished. Current dynamic vx minimum
0.5 m/s excludes standstill; baseline LQR/PI is not a validated high-speed rescue controller.
These block physical claims, while synthetic-only protocol work may later be separately authorized.

The owner reports two external-drive ZIP copies with SHA-256 records. This delivery performs no
archive restore or coverage qualification and makes no new backup claim.

## 9. Current checks and next gate

[Documentation schemas](safety/s1/documentation_schemas.json), [provenance](safety/s1/provenance.json)
and [validation record](safety/s1/validation.json) describe static JSON/schema/reference/source-hash,
Markdown, Git-scope and preservation checks only. They are neither a running protocol oracle nor
scientific verification. No tests/collection, numerical imports, solver, simulation, fault injection,
benchmark or hardware work is run. Full numerical regression is intentionally unexecuted for this
documentation-only assignment; no inherited pass is claimed for S1.

Commit/push documentation only on research/safety-s0, verify remote delivery, and stop at
**WORK_COMPLETE_PENDING_REVIEW** for Engineering Review. S0 acceptance and strategy approval do
not constitute S1 acceptance, code authorization or automatic S1-B/S1-C progression.
