# Separately reviewable external process-envelope proposal

**PROPOSAL ONLY. UNRESOLVED. L3 BLOCKED. No supervisor script is created/executed.**

The current correction owns S/D from first CLI entry. A complete child-command
measurement starts earlier: immediately before an external owner launches that
child Python process, and ends only after process-group termination/reaping and
required cleanup/log retention. Python startup/imports precede S. CLI report
serialization/stdout/return and OS cleanup can follow the last internal timestamp.
Thus no strict external 300 s guarantee follows from the allowed source correction.

Propose a separately authorized trusted external owner already active before child
launch. It must establish one authoritative start T0 and D=T0+300, bind ownership
PID/job ID, exact reviewed SHA, Primary grant, output reservation and same-host
monotonic identity, then launch one child process group. A future reviewed handoff
must make child CLI/supervisor/worker use that SAME D, recording CLI entry S only as
an observation. Do not independently start child S+300 as another allocation.
The present CLI does not accept such an unreviewed handoff. Adding it and an
external launcher requires a new exact source allowlist and Primary review.

The external owner must independently record launch, observed CLI/worker start,
D-5 no-new-work/flush, TERM/KILL, process-group state, reaping, output/log retention
and cleanup completion on one clock. Proposed grace stays <=1 s within D; it is not
extra time. Refuse competing measurement owners and preserve their markers. Bind
all parent/child logs/temp/caches/indexes to the same 1 GiB reservation and 2 GiB initial/
1 GiB runtime disk policy. A parent-owned allocation/log directory may contain a
still-absent fresh grant-bound child output subdirectory; do not precreate the child
run root and thereby bypass its fresh-output authorization check.

External sampling must cover the chosen parent/child memory/output population and
report gaps/overshoot rather than a hard RSS claim. Never hide Python startup or
cleanup cost and never borrow CT1N/R or another research allocation. Capture CLI
stdout/stderr even when preflight fails before creating a worker directory; preserve
those failure records with their authorization/source state, not fabricated science.

A hard launch-to-cleanup bound remains UNRESOLVED even with a watchdog proposal:
OS scheduling, blocking calls, uninterruptible cleanup and reap latency need an
explicit reviewed policy and independent qualification. No benchmark/probe is run
here. Smallest next correction: separately authorize the external owner plus
single-deadline handoff and define/qualify its measured boundary/cleanup behavior.
Only a later Primary decision may permit execution. This document grants none.
