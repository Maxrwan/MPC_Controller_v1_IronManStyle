# Workbench V2 — bounded WORK delivery

**WORKBENCH_V2_LAP_WORK_COMPLETE_PENDING_PRIMARY_ACCEPTANCE.** Software source
`fdd494eb7ddf9b456b88cba243fbc704a4fd83c0`, branch `codex/workbench-v2-lap`, accepted V1 base
`511b0a884e0f8474760817620fcdef46e7860142`. [Primary authority](PRIMARY_WORK.md),
[machine record](work_record.json). The final delivery changes documentation only.

**Full-lap readiness is blocked at the reviewed resource preflight.** Corrected software received
independent PASS and one genuine10s baseline pilot completed/valid. Its conservative80s full-lap
projection requires551.42816CPU seconds, exceeding the declared480s CPU ceiling. No full-lap claim
or worker was created. No cap, projection rule, scientific source or consumed attempt was reset.
Primary's Section6 stop applies. No genuine full-lap time or numerical qualification is claimed.

## Delivered scope and launch

V2 provides Transient (unchanged accepted V1), Extended5/10/20s, and native Full Lap with an80s
simulation ceiling. Eight CostScales fields and the existing fixed disturbance are editable;
structural/physical configuration remains explicit in source. Saved drafts are versioned, exclusive
and unreviewed. The original V1 source/profile/policy/attempts/launcher remain byte-exact and usable.
V2 uses the same Streamlit/Plotly conventions, shared execution lease and accepted native renderer;
there is no new dependency, visual redesign, independent simulation engine or controller architecture.

From this configured branch checkout:

```sh
./Launch_APEX_Workbench_V2.command
```

Or double-click it in Finder; loopback8503. Keep Terminal open and use Control-C for owned shutdown.
The accepted V1 launcher remains `./Launch_APEX_Workbench.command` on8501. The existing approved
Python3.12.14/macOS Accelerate environment is reused. Both launchers resolve their own checkout,
without requiring a Codex-specific absolute launch command. An independently installed checkout
still needs the approved environment/runtime and explicit source/review/Primary-bound access files.
V2 remains reviewed-WORK gated: the pilot slot is consumed; Full Lap is blocked; repeatable V2 awaits
Primary acceptance. V1 retains its existing accepted-interactive policy.

## Scientific implementation and analysis

Frozen scientific source48adbdf64d492592d15e23c917aca71fa58aa8a5/333files is reused through the
existing import/dependency guard: Planning GP gamma2, dynamic bicycle/combined-grip tires,
Architecture A, NMPC N8/RK4x4 and TVLQR. Canonical dataclasses are reused. Only selected AsyncConfig
simulation duration changes; initial Planning state stays at s_abs1m. Native two-crossing termination
is retained. The first finish crossing is partial; native lap_times[1] alone measures a complete
boundary-to-same-boundary circuit. Incomplete observations remain incomplete; no endpoint state
is extrapolated. Controller equations, solver options, frozen configurations and thresholds are unchanged.

The original controlled availability pattern35/55/45/25ms and codriver5ms/prelaunch startup remain
fixed. Host solve/preparation durations and simulated availability/application clocks are separate.
Four equal-arc sectors use recorded length fractions0/.25/.5/.75/1 with identical comparison bounds.
Sector times follow the native progress-crossing convention on genuine integration segments; unobserved
entries/exits remain missing. Scientific summaries use every retained native observation. Spatial SVG
plots reduce only display points (maximum2000 per trace); native records are never replaced.

Metrics cover longitudinal speed, Planning racing-line/heading errors, yaw rate, held steering/a_cmd,
front/rear combined utilization, sampled boundary flags, slack/feasibility, solver failures/iterations/
preparation duration and scheduling events. Body accelerations derive from canonical derivative at
retained state/held command with explicit rotating-frame terms; they are synthetic model-derived SI
values. Missing slack remains missing. Genuine N8 prediction nodes match actual target timestamps
(1ns float-clock allowance only); absent target samples are not interpolated. Controlled comparison
requires equal non-cost source/environment/configuration/scheduling/initial conditions and equivalent
coverage. Differently weighted objective totals are not ranked; faster does not imply safer/robust.

## Recording and ownership

Native JSONL streams rotate at2MiB and flush observations. Complete native state/control/packet/plan/
handoff/release/miss/fallback/failure/lap chronology is retained. Partial plant/preparation/request
journals survive interrupted workers; native-final events absent after hard termination stay missing.
Full canonical histories remain bounded in native AsyncRunner memory; it is not rewritten. V2 avoids
a second in-memory plant-segment history and repeated full Jacobian recomputation. V1 local-linear
inspection remains available. Derived/native streams are chunked; manifest/status publish atomically.
Every listed artifact is verified, including unused journals. Missing/replaced/concurrently changed
bytes withdraw views. The V2 bridge binds each10s native window to its component identity/epoch,
resends one verified payload per presentation operation, and uses warm heartbeat-only updates.
Run identity/full evidence anchor and run-wide quarantine remain intact; V1 renderer files are unchanged.

| Profile | Sim ceiling | Wall | CPU | Sampled RSS | Sampled output | Single file |
|---|---:|---:|---:|---:|---:|---:|
| Extended |5/10/20s|180s|120s|768MiB|128MiB|4MiB|
| Full Lap |80s|600s|480s|768MiB|256MiB|4MiB|

V1's60s/30s limits remain unchanged. V2 inherits the same lease until worker exit, verifies lease
inode/process birth/command/run identity, and monitors supervisor loss/cancel/wall/RSS/output.
CPU/file limits precede numerical imports. Stale states reconcile under the lease with interrupted
evidence retained. These safeguards and extrapolations are exploratory limits, not hard real-time
or guaranteed memory bounds. Admission binds Primary authority, exact current/Git producer bytes
and independent PASS; slots consume before probe/execution and no automatic numerical retry exists.

## Independent review and tests

Original19aff134a797da755c1ee985e892f2b6bcc5b80c received [BLOCKED](../reviews/workbench_v2_lap/iteration_1/REVIEW.md).
R1 required terminal completed/valid/exit0 pilot evidence; R2 fixed acknowledged stale replay windows;
R3 retained missing failed-solve slack without sector crashes. Invalid/duplicate drafts are contained
without overwriting saved bytes. Original failed report/source/reproductions are preserved.

Corrected exactfdd494e received [independent PASS](../reviews/workbench_v2_lap/iteration_2/REVIEW.md)
with **56passed,0failures/errors/skips,34.41s**, plus separate adversarial metadata/transport checks.
[Review record](../reviews/workbench_v2_lap/iteration_2/review_record.json) SHA256
`9ed0de16c1d1d13fec06a84a934fc81a0fd9a2d58d117f5eea6cc000a249e79c`.
Parent affected correction selection17passed/39deselected0.92s; earlier parent40 and intermediate37,
and independent iteration1's40, are separate historical invocations and are not added to56.
Tests exercise finite modes, lap partiality, chunks, source/authority/Git/once-only gates, changed/
missing evidence, target-clock missingness, comparisons, V1 preservation, UI and real metadata-only
supervisor-loss/cancel/output/lease helpers. Guarded native configuration composition blocks solver,
runner and plant execution. All reviewer activity terminated before the genuine pilot.
No broad regression/formal Verification or frozen research campaign was performed.

## Genuine pilot and resource stop

One genuine baseline attempt: `2026-11-10T145233.755880_0000_f46cc76634dd4322b1720f37eb96442b`.
Production admission/worker/consumer retained completed/valid evidence, exit0:10.0s native duration,
2000states,1000applied-control rows,100plans/packets,99handoffs/releases,0failed preparations,
0misses/fallbacks/codriver misses and0sampled boundary violations. No scientific retry occurred.
The native sample window ends9.995s; no full circuit was completed and lap time remains unavailable.
Supervisor wall36.805571s, pre-finalization worker CPU34.46426s, sampled peak RSS216,514,560bytes.
Accelerate actual control reports SINGLE/status0; this is not an exact total-thread guarantee.
Source/environment and artifact integrity passed the production consumer.

Two initial **metadata-only** capacity checks failed before any claim/run/consumption. The extra
2x-worker-cap headroom floor belonged to the ignored task harness, not the reviewed profile.
An [independent memo](../reviews/workbench_v2_lap/host_preflight/MEMO.md) supported a pilot-only
768MiB allowance+512MiB host reserve while preserving all worker/full-lap gates. Fresh pilot capacity
was1,652,654,080available bytes,22GB disk, no conflicting processes and66inactive external guards.
Original failed checks/scripts/inputs and memo are retained; no accepted source was changed.

The unchanged production budget then rejected the full lap:

| Projection (2 x 80/10 pilot scaling) | Value | Declared ceiling |
|---|---:|---:|
| Wall |588.889137s|600s|
| CPU |**551.42816s**|**480s**|
| RSS estimate |270,616,848bytes|805,306,368bytes|
| Output estimate |112,568,912bytes|268,435,456bytes|

These are extrapolations, not measured full-lap values. Resource rejection occurred before a full-lap
host/claim/worker stage. The full-lap slot remains unused. Full Lap's actual browser Run button is
disabled by this gate. No second pilot, resource-limit increase, revised projection or campaign followed.

## Functional observations, preservation and next decision

Actual launch from/private/tmp, owned reuse and shutdown pass. The genuine pilot reopened in V2
with racing metrics/predictions/native replay;1x playback observed9.995native seconds in10.0071wall
seconds (223painted frames,max gap50.4ms), display timing only. Full-lap status accurately remains
incomplete. Multi-window replay and V2 controlled-treatment classifications have software-fixture
coverage; no genuine >10s or modified-weight V2 comparison was executed under this authorization.
The accepted V1 transient editor/analysis/comparison paths remain available.

Final audit:12,546historical files/508links across retained Scratch/M5 roots unchanged;333frozen
runtime files and32V2 producer identities match reviewed Git. V1 policy/attempts/launcher/renderers
are unchanged. Canonical source/configuration/dependency prefixes are unchanged. Server/worker/
supervisor are stopped,8503closed, common lease free; temporary in-app tabs closed. Raw results/logs
remain local/ignored: Git report hashes do not establish off-host archival retrieval.

Primary should review a bounded resource-plan correction before authorizing any full-lap execution.
Unconditional full-lap acceptance is not recommended from this evidence. The reviewed software and
successful10s exploratory path are delivered; full-lap empirical readiness remains blocked. No
automatic V2 acceptance/repeatable enabling, new scenarios/physics/controllers, sweeps, ROS2,
exporter, hardware, qualification or later-stage work follows.
