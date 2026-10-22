# S1-A — Bounded implementation authorization request

**PROPOSED — NOT IMPLEMENTED. WORK_COMPLETE_PENDING_REVIEW.**
This assignment prepares documents only. No reducer source, executable test, event/fault execution,
numerical import, solver, dynamics, endpoint, hardware or racing-runtime integration is created.

## Authority and exact basis

The owner supplied Primary's formal S1 acceptance with conditions, bound to
`9f0cbe0f0f48a1e2a62716957bbab79fe2b5b1b4`. The exact decision date was not supplied.
[Provenance](provenance.json) records that statement, attachment hash, exact S0 acceptance and
S1 source/hash bindings. Original accepted specifications, all 22 case designs and all 69 rows
remain byte-identical. Their historical pending/NOT_EXECUTED labels are not overwritten.
Acceptance of S1 is not acceptance of this proposed preparation package or authorization to code.

Preflight found clean `research/safety-s0` at the requested revision in the existing isolated
worktree; correct remote `Maxrwan/MPC_Controller_v1_IronManStyle`. Frozen Performance E4/main/tag
remain `48adbdf64d492592d15e23c917aca71fa58aa8a5`. Efficiency started at
`ff34bd36897c4ed00b850a2d0255132bdebac5fd` and independently advanced during temporary drafting
to documentation-only `83f360b2a96e8f6d9fe429d2cc2e5447da2f47c8`. Safety did not write that
checkout; its new documentation and unchanged runtime are preserved. No competing Safety branch
or automatic merge is created.

## Proposed activation decision

The [activation matrix](transition_activation_matrix.json) preserves every original S0 source state
and destination, explicit guard, authority effect, rejection, UNKNOWN consequence and source-edge
positive/rejection/boundary case link. ENABLED below means requested future implementation after
review, authorization and required passing coverage; nothing is currently enabled or implemented.

| Transition | S1-A proposal | Intended logical responsibility |
|---|---|---|
| T01 | ENABLED | Explicit armed admission into NORMAL. |
| T02 | ENABLED | Admissible NORMAL continuation enters WARNING. |
| T03 | ENABLED | Independently evidenced renewal/clearance returns WARNING to NORMAL. |
| T04 | DEFERRED/DISABLED | Recovery policy activation. |
| T05 | DEFERRED/DISABLED | Conservative deceleration activation. |
| T06 | ENABLED | Emergency/stop demand, immediate latch/revocation. |
| T07 | DEFERRED/DISABLED | Stop-policy activation/acknowledgement. |
| T08 | DEFERRED/DISABLED | STOPPING-to-confirmed-rest path. |
| T09 | ENABLED | Mandatory NO_VALID_POLICY closure. |
| T10 | DEFERRED/DISABLED | Emergency stop activation from NO_VALID_POLICY. |
| T11 | ENABLED | Supplied independent synthetic rest assertion; no grant or physical proof. |
| T12 | DEFERRED/DISABLED | Recovery/deceleration reentry into WARNING. |
| T13 | ENABLED | Authorized cleared-fault/new-session reset to DISARMED. |
| T14 | ENABLED | Loss of rest/hold confidence enters NO_VALID_POLICY. |

All nine state identifiers remain represented. RECOVERY, DECELERATING and STOPPING cannot gain
authority through a disabled edge, even with a SATISFIED toy assertion. Retained snapshots in those
states admit no permissive work; enabled T06/T09 escape and T14 rest-loss handling remain mandatory.
T06 records STOP_REQUESTED and then T09 in the same critical transaction when no enabled stop
policy exists. There is no invented braking controller or safe-zero output.

Each source-state edge maps to positive, rejection and boundary designs. A false no-policy guard
is unreachable in disabled active-policy states; the matrix explicitly uses wrong-source T14
dispatch/denial coverage rather than fabricating valid recovery/stop continuation. Reviewers must
approve this declared unreachable-case treatment. No unverified permissive behavior may be enabled.
State changes alone create no Permission: a separately checked phase4 request is always required.

## Exact proposed API and dependency boundary

[API contract](reducer_api_contract.json) specifies keyword-only immutable value constructors,
field types, pure function signatures, record/schema/source bindings, null/error behavior and
the maximum import surface. Native tuples and finite Decimal values preserve SI/canonical ordering;
the rational clock performs no vehicle propagation. IDs are explicit deterministic inputs/outputs.

The proposed runtime consists only of `src/apex/safety_authority/` with `records.py`, `codec.py`,
`time.py`, `ordering.py`, `policy.py`, `reducer.py` and explicit exports. Functions decode immutable
values, conservatively map time, validate half-open intervals, seal batches, reduce or reject a
batch and restore supplied logical persistence. No disk durability or independent enforcement is
claimed. S1-A may consume externally supplied endpoint/queue/rest observations; it never generates
an application, cancellation acknowledgement or simulated physical outcome.

Only the named standard-library imports are permitted. No NumPy/SciPy/CasADi, controller/plant/
simulation imports, real clock, threads, random IDs, networking, MCU/device calls or dependency
changes. No existing `apex` initializer or unrelated module is edited.

## Ordering resolutions that require review

[Event precedence resolution](event_precedence_resolution.json) proposes exact integer-time,
sealed-batch admission, causal/producer ordering, microsteps, boundary traversal, fault closure,
session/epoch barriers and denial ordering. The original contract is not silently redefined.

| Proposed amendment | Decision requested |
|---|---|
| PC01 | Admit producer sequences before phase sorting and persist exact event identities. |
| PC02 | Explicit requested interval for old-command reauthorization. |
| PC03 | Explicit WARNING_CLEAR and exact prepared/new-session barrier binding. |
| PC04 | Per-event traces separate from historical compound-row summaries. |
| PC05 | Separate event and command-operation ledgers for replay/idempotency. |
| PC06 | Critical closure and one epoch bump per current-session batch; controlled restart. |
| PC07 | Exact crossed-boundary traversal and inclusive freshness-limit handling. |
| PC08 | Typed synthetic role/mapping/uncertainty assumptions; no real authentication claim. |
| PC09 | Explicit proposed PermissionRequest identity/supersession fields. |
| PC10 | Invalid-input handling cannot discard separately known critical facts. |

These are concrete candidate resolutions, all pending Engineering/Primary review. Proposed wire
version `apex-s1-authority/0.2.0` and Python API `apex-s1a-python/0.1.0` must not be presented as
adopted replacements for accepted 0.1.0. No accepted file is rewritten and no runtime decoder exists.

Known revocation/expiry/critical invalidity wins over new grants. Undelivered host revocation does
not become endpoint enforcement. A healthy same-tick estimate cannot clear a critical latch.
Exact duplicate receipt replays history only; a later permission attempt rechecks current guards.
Unknown/censored acknowledgements and physically held input remain explicit, never a false stop.

## Independent oracle package

[Oracle expansion](independent_oracle_expansion.json) retains the original six-scenario/22-case/
69-row basis and audits each row with its immutable hash. Five endpoint-stage cases remain deferred.
Compound rows, reauthorization intervals, exact permission identities, persistence and reset
contexts have explicit materialization findings. No row is rewritten merely to make a test pass.

The added source-edge and protocol cases reference complete immutable Configuration and Snapshot
records by JSON pointer and SHA-256. They define exact input records/ticks, expected final logical
projection and transition path, decision/reasons, permission/session/epoch/latch changes, retained
unknowns, forbidden outcomes and trace identity constraints. All inputs are labelled toy assumptions;
zero/rest fixture values are record data, never an assertion of physical braking or valid dynamics.

Before execution, independent reviewers must approve literal per-event expected traces and
boundary/internal IDs, including the original compound-row materializations. Future expectations
must not call reducer guard/order/transition/ID helpers or be regenerated from implementation output.
The document builder expands authored data templates only; it executes no transition or oracle.

## Exact future file scope and separate gates

[Scope and gates](implementation_scope_and_gates.json) lists every proposed source, test and fixture
path, role, oracle source and focused command. The dedicated future tests cover records, time,
ordering, transitions, identity, restart and reviewed literal cases. The four JSON fixture files
are future materializations, not created as executable test assets by this assignment.

The proposed isolated pytest command disables unrelated plugins/conftest imports; it is text here
and is not run. No numerical suite or controller/plant simulation is authorized by pure S1-A work.
Controller integration would later require the repository's full causal latency/physics gates.

1. Engineering/Primary review of this package, activation set, proposed amendments and oracle plan.
2. Separate explicit Primary authorization for the named reducer/test/fixture creation only.
3. Engineering Review of the exact implementation and independently materialized oracle revision.
4. Separate explicit authorization for the named deterministic focused checks.
5. WORK evidence/review, with complete passed/failed/censored outcomes and exact source/fixture hashes.
6. Formal verification and scientific acceptance only under their own later instruction.

A later assignment can explicitly combine bounded creation and execution permissions only by naming
both scopes and satisfying their entry gates. No implication or status automatically grants either.
S1-B/S1-C, endpoint execution, integration, physical controller changes and hardware remain excluded.

## Ready-for-review disposition and remaining decisions

This is a ready-to-review bounded code authorization request, **not permission to implement**.
Outstanding decisions are the eight-enabled/six-disabled activation set, unreachable-negative-guard
treatment, PC01-PC10/version adoption, and independently reviewed literal per-event materializations.
No new numerical envelope, real freshness threshold, recovery basin or physical controller is proposed.
Approximately50ms remains an unvalidated Perception hypothesis. Hardware HW01–HW10, physical response
guarantees and archive restoration/coverage qualification remain separate obligations.

[Validation](validation.json) records scoped documentation/structure/schema/reference/source-hash
and preservation checks only. Commit/push this documentation on research/safety-s0, verify the
remote SHA and stop at **WORK_COMPLETE_PENDING_REVIEW** for Secondary Engineering Review.
