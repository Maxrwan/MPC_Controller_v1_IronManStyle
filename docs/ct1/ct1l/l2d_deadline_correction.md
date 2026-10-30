# L2D shared monotonic deadline correction

**CODE ONLY — WORK_COMPLETE_PENDING_REVIEW. No execution authorization.**

At the first line of `cli.main`, record S with `time.monotonic()`, then create
one immutable `_AggregateDeadline(S, S+300)`. Parsing, source revision/hash checks,
Primary grant validation, resource preflight, supervisor setup, worker startup,
tests, analysis and finalization consume that original allocation. Supervisor
entry no longer establishes `begin=time.monotonic(); deadline=begin+300`.

```mermaid
flowchart LR
  E[External child Python launch: not timed by CLI] --> P[Python startup and imports]
  P --> C[CLI first timestamp S; D = S + 300]
  C --> V[Source checks and Primary grant]
  V --> R[Resource and ownership preflight]
  R --> U[Supervisor receives same deadline object]
  U --> W[Worker environment receives absolute D]
  W --> A[Existing tests and analysis poll D minus 5]
  A --> F[Flush, TERM/KILL, index within remaining D]
  F --> O[CLI final report sample, stdout and return]
```

The five-second reserve begins at D-5, independent of stage completion times.
It is never restarted. The <=1 s termination grace is `min(1,max(0,D-now))`;
final index hashing receives D. Supervisor resource observations and reported
elapsed wall time now use the original CLI start, including earlier preflight.
Monitor-gap timestamps are observations, not independent allocation clocks.
The worker's unchanged `CT1L_DEADLINE_MONOTONIC` contract receives exactly D;
`CT1L_CLI_START_MONOTONIC` additionally identifies S for retained metadata.

Changed interfaces (exact AST spellings in `l2d_change_manifest.json`):

- `check_execution_grant(..., *, deadline=None)`: CLI supplies the one deadline;
  the unchanged worker can still revalidate its Primary grant with three arguments.
  Omitting this optional argument does not create a clock or launch permission.
- `preflight_resources(..., *, deadline)`: deadline is required; checks and process
  inventory timeout consume remaining work time. Timeout is not collapsed into
  generic resource unavailability.
- `supervise_worker(..., *, deadline, inputs, grant_path)`: all three are required.
  Supervisor revalidates the exact Primary grant and command source/grant path
  before output creation/worker launch. A caller cannot enlarge the 300 s budget.
- `_AggregateDeadline` fixes a finite S/D pair with D=S+300. `_DeadlineExpired`
  preserves the checkpoint; `_preworker_evidence` serializes available failure
  facts; `_cli_result_exit_code` prevents zero-exit/missing-worker false success.
- `cli.main(argv=None)` retains its public signature.

Before every expensive CLI stage and after completion, check D-5. If source
validation fails, retain SOURCE_IDENTITY_FAILURE even if its elapsed check is
late; an otherwise valid but expired preflight becomes RESOURCE_CENSORED and
cannot launch a worker. Missing/invalid/revoked grants deny launch. Primary
validation is repeated at the supervisor boundary; deadline propagation cannot
substitute for authorization.

Early failures emit structured JSON on CLI stdout without creating an unauthenticated
output directory. If an already authenticated supervisor creates its fresh output
root but cannot create a worker, `preworker_failure.json` retains the available
failure facts there. Null RSS means NOT_OBSERVED, not a measured zero or a hard cap.
No-worker failures cannot return success; missing coverage cannot overwrite an
existing resource/source/environment failure into COMPLETE.

This is accounting and cooperative deadline propagation, not a certified hard
wall-time guarantee. Unmodified source verification/filesystem calls can block
between checkpoints; process reaping, stdout and final cleanup can overrun.
The CLI elapsed sample precedes stdout/return. The complete CLI envelope is from S
to actual return; that tail needs external observation. Python startup occurs
before S. The external launch-to-cleanup envelope is **UNRESOLVED**; L3 remains
**BLOCKED** pending the separately reviewable external ownership/deadline proposal.
No additional preflight allocation, fallback timeout or borrowed research budget exists.

Known cleanup/finalization I/O failures remain failed supervisor reports with explicit
incomplete diagnostics and retained files. A created child with an unavailable exit
status is labeled `worker_exit_status_NOT_OBSERVED`; CLI output retains
`worker_started=true` and a failure exit. It is not recast as a preworker failure.
A completed marker alone is not proof of final index/cleanup completion; the report
and incomplete diagnostics must be retained by the proposed external owner.

Without an RSS sample, marker/CLI diagnostics and finalization input carry null.
The unchanged integer-only scientific index schema cannot represent that missing
measurement, so any attempted scientific index fails closed and the partial files/
missing-index diagnostic remain. The unchanged internal SupervisorReport integer
slot retains zero only as a sentinel paired with `worker_RSS_NOT_OBSERVED`; CLI
serialization does not expose it as a measurement. No scientific schema is changed.

A missing final index cannot leave an otherwise COMPLETE result successful: it
becomes MISSING_COVERAGE while earlier failure classifications remain intact.
