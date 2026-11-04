# W1 local nominal-control interface

**Corrective WORK checkpoint — independent Engineering Review pending.**
Primary APEX's 2026-11-04 dispatch authorizes corrections and conditionally authorizes a fresh
replacement G0/G1/2 s smoke sequence after independent PASS on the clean committed producer.
The original failed G0 remains consumed. No replacement run has occurred at this checkpoint.

WORK implementation; not formal Verification or physical Safety acceptance.
Scientific source: `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
Approved specification: `63d56fc366de7464e1c71a4f831c87ec03d31a2f`.

`apex.preintegration.session.ControlSession` owns injected components and local lifecycle.
`profile.compose(root, admission=...)` composes the unchanged accepted N8/0.1 s/four-substep,
gamma2, combined-grip, original A predictor and TVLQR configuration. Solver factory injection
is separate. `bootstrap` requires a fresh Python 3.12.14 process with `-P -S`, hash seed zero,
unchanged source/dependencies and the supported Accelerate SINGLE setting. It inspects installed
RECORD hashes before any numerical import and bypasses editable `.pth` processing. No dependency
installation or source-tree substitution is performed.

Canonical SI state: `[vx,vy,r,e_psi,s_abs,e_y]`; command: `[delta,a_cmd]`.
Dynamic `a_cmd=Fx_total/m`, not measured `dvx/dt`. Progress stays nonnegative and unwrapped;
only geometry lookup wraps. Headings and lateral conventions are unchanged.

`Feedback(sample_id,time,state,clock='local-simulation')` owns a tuple copy. A decision or check
requires the exact same simulation-time value as capture, explicit clock identity, monotonic
time and sample identity. Identical sample reuse at the same instant is supported; stale,
future, missing, conflicting or replayed feedback inhibits until reset. This provides no
physical freshness allowance, sensor-quality assertion or uncertainty policy.

Operations: `prepare(...,plan_id,applied,startup)` returns a prepared token plus native diagnostic
record; `complete(token,feedback,now)` resolves and offers it; `offer_waiting` admits only when its
nominal start arrives; `propose(feedback,now,applied)` calls the original tracker;
`check_application(proposal,feedback,now,applied,last_application)` checks the original source and
current state and uses the existing elapsed steering clamp. `observe_applied` records only a
caller assertion. `reset` requires fresh independently owned components/session, inhibits if construction fails,
and invalidates all old tokens;
`close` leaves no output. Instances are single-owner; callers supply actual preceding applied
input and scheduling. The API never steps a plant or makes blocking preparation concurrent.

Only `VALID_NOMINAL` has a command. Inhibition is `command=None`, with explicit reason(s).
The optimized previous-command placeholder and legacy baseline fallback are never advertised
as new nominal authority. No zero/brake/hold response or physical permission is manufactured.
A rejected replacement can leave the prior unexpired packet usable. Pending proposals retain
original provenance across handoff; expiry at application denies them. Application checks are
single-use. Reentry after invalid authoritative feedback requires explicit fresh reset/startup.

`local.LocalAdapters` delegates preparation/tracking to this boundary while the existing
`AsyncRunner` retains its only buffer and event scheduler. Predictor clones are detached native
trackers. Native planner timing remains the original availability input; separate boundary
envelopes expose overhead. Legacy simulator application rows do not prove enforcement of this
new application-check API. Mock-endpoint tests check that operation before invoking the endpoint;
there is no new external endpoint adapter here. No-nominal/fallback during genuine local smoke
is incomplete, not a qualified recovery.

Fresh execution, after admission and software gates, uses the existing admitted virtualenv:

```sh
env -u PYTHONPATH -u PYTHONHOME PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 \
  /path/to/admitted/.venv/bin/python -P -S scripts/preintegration/launch.py \
  --case conditional-sequence --output results/preintegration/w1/replacement-UNIQUE
```

The replacement claims use the fresh source-bound ledger under
`results/preintegration/w1/correction-20261104T160319Z/`. A software gate must bind the
clean committed producer, runtime hashes and independent PASS report. Predecessors additionally
require a normal-exit witness bound to their result/index/ledger plus an in-memory grant
from the same live sequence driver after all final bookkeeping. Stored receipts alone do not
grant admission. Run all three conditionally in one invocation; do not resume a terminated
driver or execute a standalone G1/smoke. Case process groups include supervisor and descendants;
a surviving descendant fails cleanup. The original ledger
under `work-20261103T123702Z-532aa226` is preserved and never reset or reused. Existing output
or consumed case claims reject; this command is not permission to rerun. Each worker has 60 s
launch-through-cleanup wall, 30 s process-tree CPU, 2 GiB sampled RSS, 128 MiB output and at least
1 GiB disk admission. Parent resource sampling and worker CPU limit retain their observation
limits. Raw records, faults, exits, actual import/binary hashes and checksums precede any complete
claim. A final JSON index is required. Raw local paths are not independently qualified backups.

External integration still must negotiate frames/transforms, delayed feedback, clocks, worker
completion while world physics continues, command transport/application/hold-on-inhibition,
reset ownership and logging. S1-A, recovery/stop policy, physical uncertainty, watchdogs,
continuous collision safety, actual onboard timing and physical actuation remain deferred.
