# Workbench V2 — extended and full-lap WORK

**WORK_READY_PENDING_INDEPENDENT_REVIEW.** Base `511b0a884e0f8474760817620fcdef46e7860142`,
branch `codex/workbench-v2-lap`. [Primary authority](PRIMARY_WORK.md).
No genuine extended/full-lap execution has occurred at this candidate stage.

The accepted V1 producer files, entrypoint, launcher, profile, access policy and all historical
attempts remain unchanged. V2 is a small composition/presentation package under
`tools/apex_workbench/lap/`, served by `Launch_APEX_Workbench_V2.command` on loopback8503.
The same Streamlit/Plotly conventions, V1 transient editor/inspection/Control Analysis/comparison,
existing native replay component and shared execution lease are reused. The V1 launcher remains
the normal accepted V1 path on8501. Separate entrypoint avoids changing V1's source-hashed producers.
No new dependency, visual redesign, standalone simulation engine or scientific source change.

## Scientific composition and clocks

The verified333-file48adbdf runtime and original import/dependency guard remain the scientific
implementation. Native `resolve`, CostScales/MPCConfig, Planning gamma2 GP, dynamic bicycle,
combined-grip tires, N8/RK4x4 NMPC, Architecture A and TVLQR are reused. Only AsyncConfig duration
is selected as5/10/20s or finite80s full-lap ceiling. Its existing native two-crossing stop is retained.
Initial state remains the original Planning state at s_abs1m. No speed regulation, initial-state
reconstruction, controller equations, solver options, geometry or scientific thresholds change.

Controlled availability remains the exact original replay: planner pattern35/55/45/25ms, codriver5ms,
prelaunch startup. Host solver/preparation durations are descriptive, separate from simulated packet
availability. New preparation/plant/tracker observers only serialize return values and pass through
the original result. No full packet Jacobian recomputation is made in V2; V1 retains that inspection.

Native AsyncRunner first crosses the next multiple of track length L. From1m this is a partial
launch interval, never a full lap. Its second crossing completes L metres between consistent phase0
boundaries. V2 reports native lap_times[1], excludes lap_times[0], retains both crossings and all
native stop/failure fields. Reaching80s or a resource limit without that interval is incomplete.
The native crossing-time linear progress interpolation is retained; it does not create telemetry.
Duration modes also preserve the native two-crossing stop; early native termination is explicit.

## Independent execution profile and retained data

V1's global60s wall/30s CPU limits are unchanged. V2's versioned profile separately declares:

| Mode | Sim ceiling | Wall | CPU | Sampled RSS | Sampled total output | Single file |
|---|---:|---:|---:|---:|---:|---:|
| Extended |5/10/20s|180s|120s|768MiB|128MiB|4MiB|
| Full Lap |80s|600s|480s|768MiB|256MiB|4MiB|

These are exploratory software safeguards, not scientific/real-time guarantees. The worker inherits
the same V1 lease, verifies inode/identity, retains it until exit, and monitors supervisor birth/command,
cancel request, wall/RSS/output. CPU/file limits are set before numerical imports. Supervisor uses
separate verified process roles and leaves a live uncertain worker's inherited lease authoritative.
Stale states reconcile only under the shared lease, with interrupted evidence retained.

Before acceptance, independent PASS/Git/current-producer/Primary hash binding permits one baseline10s
pilot and one conditional baseline full-lap attempt. The slot is consumed before probe/execution;
failure is retained and no automatic retry exists. Full lap additionally requires the exact valid pilot
manifest, declared resource extrapolation fitting fixed caps, and a separately retained host-capacity
preflight. Later repeatable user-triggered operation requires an explicit versioned Primary acceptance
of the reviewed revision; no per-experiment review bureaucracy or automated sweeps are added.

Compact native JSONL streams rotate at2MiB and flush each observation. Native states/commands/
packets/plans/handoffs/releases/misses/fallbacks/failure/lap arrays retain exact native timestamps.
Plant segments and preparation/request journals survive an interrupted process without retaining
a second in-memory plant-segment history. Partial journals are not a completed scheduler history:
missing native-final events after a hard kill remain missing. Full native histories are still bounded
in AsyncRunner memory; it is not rewritten. Final native and derived streams are chunked, with atomic
manifest/status publication. All listed artifacts are verified, including unused journals; changed,
missing or concurrently replaced evidence withdraws views. Original bytes are never repaired.

The native replay component receives a selected10s window of real samples. Full scientific metrics
always use all retained data; spatial plots show at most2000genuine points per trace. No resampled
scientific states, invented terminal sample or interpolated prediction error. Repeated validation
heartbeats preserve the existing browser fail-closed lease/quarantine behavior.

## Analysis definitions

Four identical equal-arc sectors use phase fractions0/.25/.5/.75/1 of the recorded canonical length.
Sector time is native integration-segment progress crossing time on the complete post-launch circuit;
an unobserved entry/exit remains incomplete. Speed, Planning racing-line/heading error, yaw rate,
held steering/a_cmd, front/rear combined utilization, sampled boundary violations, slack/feasibility,
solver status/iterations/preparation duration and scheduling events use actual native records.
Body accelerations derive from canonical DynamicBicycle.derivative at retained state/held command,
with rotating-frame terms explicitly separated; these are model-derived SI values, not measurements.

Selected native N8 prediction nodes are associated with actual samples at their target timestamps
(1ns float-clock matching only). Missing target samples stay absent. Completion and handoff clocks
remain explicit; nominal versus realized divergence is not causal controller validation.
Controlled weight comparison requires identical source/environment/resolved non-cost conditions,
scheduling, initial state and equivalent coverage. Full laps compare complete same-phase circuits;
incomplete/different coverage is noncontrolled. Differently weighted objective totals are not ranked.
There is no new score; faster does not establish safer or more robust.

## Focused evidence and pending gate

Final focused invocation: **40passed,0failures/errors/skips,31.86s**. Earlier37-pass intermediate
invocation is retained separately and is not added to the final count. Tests cover strict finite modes,
partial-first crossing, chunk roundtrip/limits/no-overwrite, one-shot/source/authority/Git rejection,
future explicit acceptance without history reset, complete/missing/replaced evidence, controlled
comparison classification, target-clock missingness, UI, V1 byte preservation, shared-lease contention,
and real metadata-only supervisor-SIGKILL/cancel/output-abort helpers. The latter exercise the actual
monitor and inherited lease with real PID birth/command identity; production command-prefix startup
validation is separately inspected, not claimed as a full genuine-worker stress campaign.

One fresh no-solve process composed three configurations through original native dataclasses:
controller config/initial state unchanged, only declared duration differs. Optimizer construction/solve,
AsyncRunner.run and DynamicBicycle.step were blocked. There were zero genuine scientific runs.
Ruff and launcher shell syntax pass. Full regression/formal Verification is not authorized here.
Logs/JUnit/software fixtures: `results/apex_workbench_v2_lap/software/`.

Preservation anchor:12,546historical files/508links across existing Scratch/M5 roots, including frozen
runtime and V1 policy. Before genuine execution: independent exact-candidate Engineering Review PASS.
Then at most one10s pilot; only a successful, valid, resource-supporting pilot permits one full lap.
No retry, new scenario, frozen research, controller architecture change, exporter or hardware work.
Final stop: `WORKBENCH_V2_LAP_WORK_COMPLETE_PENDING_PRIMARY_ACCEPTANCE`.
