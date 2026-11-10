# NMPC Lab V1 — acceptance and operational finalization

**NMPC_LAB_V1_ACCEPTED_FOR_SYNTHETIC_EXPERIMENTATION.** 10 November 2026. Branch
`codex/nmpc-lab-v1`, starting delivery `6e2d3b7009b637a8f67ec49b326a29c32bff2aa0`.
[Primary decision](PRIMARY_ACCEPTANCE.md), [acceptance record](acceptance_record.json).
Operational candidate `480933c655991917f69dafaa40fb58419758a8c9` received focused independent
**PASS**, with no blocking findings. [Review](../reviews/nmpc_lab_v1/operational/REVIEW.md),
[review record](../reviews/nmpc_lab_v1/operational/review_record.json),
[final evidence record](operations_record.json). The laboratory/UX source remains accepted447cc1e;
only checkout-environment resolution in the
launcher, an ignore rule and deterministic test fixtures change. No scientific implementation changes.

The old WORK policy correctly rejected current source: its panel hash was25f8b7…, while accepted
447cc1e has ea0820…. All other14 producer hashes are identical. Each current producer was compared
with exact Git447cc1e. The original Engineering Review8ee2 and UX Review447cc1e PASS records were
matched to their original Git-delivery bytes and copied unchanged into the local acceptance bundle.
Primary's hashed acceptance record binds both reviews, frozen48adbdf, executionaf3956, the current
15-producer map, original case/used identities and resource limits. The existing access parser is
unchanged: current files must match the policy and exact reviewed Git source, final UX review and
explicit Primary-record hashes. No verification is skipped or weakened.

The existing policy alone transitioned to `accepted-interactive`. Its exact predecessor628a6199…
is retained in `results/apex_workbench_nmpc_lab_v1/operational_20261110/previous_access.json`.
All three historical consumed IDs, cases and original grant remain unchanged. Ordinary explicit
user-triggered runs may use the existing eight costs/fixed disturbance/current2s GP gamma2 profile.
They remain experimental/unqualified; no frozen Performance configuration is overwritten. There
is no sweep, background runner, automatic retry, new scenario, exporter or deployment work.

The normal `Launch_APEX_Workbench.command` is checkout-relative. This configured checkout shares
the existing approved tool environment using a local ignored directory symlink. The launcher
resolves that directory, retaining its venv interpreter instead of resolving the binary to bare
Python. This preserves the original environment identity. No dependencies were installed/changed.
Launch it from the accepted branch checkout:

```sh
./Launch_APEX_Workbench.command
```

Or double-click the file in Finder. Open <http://127.0.0.1:8501>. Keep its Terminal open; Control-C
stops the owned server. A second launch reuses that checkout's server. Other checkouts/branches are
not silently selected. A different checkout needs its own correctly provisioned acceptance/runtime
files and approved environment; copying arbitrary approval files is not setup.

Focused software:42passes,0failures/errors/skips,9.71s. Scientific imports, workers and probes were
blocked; only read-only metadata and disposable Git fixtures were permitted. Tests cover repeatable
admission without changing historical consumption, tampered/missing acceptance/review/source/Git
rejection, bounded configuration, standard navigation/comparison and versioned drafts. The old
disabled-gate test now explicitly models an unaccepted fixture instead of relying on production
remaining unaccepted. A strict preparation audit caught that planned test-only delta before any
policy write; it is recorded separately from runtime/source equivalence. Test formatting records
were finalized before review; predecessor prepared bytes remain retained.

The actual normal launcher started from `/private/tmp`, served loopback8501 from this checkout
using the canonical approved venv, and a second invocation reused its owned listener. Interpreter
and10 installed dependency RECORD trees match the frozen approved numerical environment.

The independent reviewer separately ran15guarded checks:15passed,0failures/errors/skips,8.74s.
These are separate from the parent42-pass invocation. Review confirmed both original review copies,
all15producers against447cc1e, policy/Git fail-closed behavior,333frozen runtime files and the retained
history. All review work terminated before the smoke. The immutable pre-attempt claim pins the
exact480933c candidate and independent review digest
`f7fa51d586dd4013471abc37303813f42970f61e69f49ad8d68a3630718fd3af`.

**One genuine attempt, no retry:** the actual browser's Run Scratch experiment button admitted
`20261110T113507881268Z_abbb79f98d324399a2070740ba4b95d3`, with accepted baseline costs, no
disturbance and fixed2s GP gamma2 profile. It completed with valid evidence and returncode0:
400native state samples,200controls, duration termination and no recorded failure. Supervisor
runtime18.7401s, sampled peak RSS209,862,656bytes, sampled peak worker threads4. Accelerate's actual
native control reports SINGLE/status0; sampled process threads are a different population.
Existing60s wall/30s CPU/512MiB sampled RSS/64MiB sampled output/16MiB file limits remain unchanged.
The source/environment identity and every committed artifact were checked by the production reader.
No second scientific attempt, parameter sweep or broad formal Verification was performed.

Actual browser acceptance: eight-field editor and baseline reset; enabled interactive admission;
saved `operational_baseline_20261110_v1.json`; new completed/valid run reopened in Inspect; native
playback; Control Analysis with genuine tracking/command/solver/grip diagnostics; and new baseline
versus retained lateral1 comparison labelled **controlled / experimental, unqualified**. Production
comparison also admitted the new/original baseline pair with no configuration differences.
One1× playback observation:1.995retained simulated seconds in2.0113wall seconds,46painted frames,
maximum painted-frame gap50.1ms. This is display timing, not a real-time or general latency guarantee.
The400sample window ends at1.995s; no2s endpoint state is invented.

The post-attempt audit rechecked11,135historical files/500links: only the authorized access.json
transition differs. All3old attempts/case/grant identities, original reviews, negative evidence,
333frozen runtime files and source/profile/dependencies remain preserved. The interactive attempt
did not change access.json or consume/reset historical WORK entries. Its genuine raw evidence and
hash manifest remain local under the original run directory; Git documentation is not an off-host
evidence backup.

The normal launcher was started again from `/private/tmp`, reused its owned server on a second
invocation (exit0), and stopped with Control-C. The server, worker and supervisor terminated,
loopback8501 refused connection, and the execution lease was free. This tool-PTY shutdown route
returned exit1 despite verified owned cleanup; this observation has no broader platform implication.
The discovery selector may retain its pre-refresh queued metadata while verified run details show
completed/valid; Refresh catalog refreshes discovery. Playback/navigation behavior remains the
accepted UX behavior.

Preparation negatives are retained: the planned test-only source delta was caught before transition;
an initial browser connection found the previous tool server closed, followed by a normal relaunch;
one metadata-only preflight approval review timed out before execution and its permitted retry
succeeded. A frame-locator Play click failed without action; the native accessibility click worked.
None caused an extra scientific attempt or an integrity bypass.

Logs, JUnit, exact commands, policy transition, exclusive claim, raw run audit and cleanup records
are under `results/apex_workbench_nmpc_lab_v1/operational_20261110/`. A fresh independent checkout
needs the supported environment, exact frozen runtime and explicitly provisioned source/review/
Primary-bound access records; arbitrary approval-file copying is not an installation procedure.
On this configured accepted checkout, use the normal command above or double-click the launcher.
The primary checkout's unrelated active branch was left untouched.

Final recommendation: use V1 for explicitly triggered, bounded synthetic experimentation within
the accepted profile. Results remain unqualified; physical, real-time, deployment and broader
scientific claims remain unsupported. ROS2, exporter, Docker, new scenarios and campaigns remain
outside scope. No remaining blocking operational finding.
