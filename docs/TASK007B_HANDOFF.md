# APEX handoff — Task 007B complete

Date: 2026-10-03. Complete only Task 007B. Task 007A was explicitly accepted by the user.
No next-task implementation is authorized. The completed Task 007A handoff is preserved in
`docs/TASK007A_HANDOFF.md`.

## Outcome

Optional terminal progress is implemented with default lambda=0. The selected experimental
setting is **gamma=1, lambda=2**, limited to the conservative synthetic reference. Complete
comparable lap times are 58.797833/58.799993 s, versus 59.011882/59.013652 s at lambda=0:
mean improvement **0.3623865%**. Lambda=1 gives only 0.1734506%, below the predeclared 0.2%
meaningful-benefit threshold. Both selected lap gains are positive. No combined score was used.

At gamma=2, complete-lap means are 31.495342 s (lambda=0), 31.501700 s (lambda=1) and
31.581479 s (lambda=2). Do not generalize the conservative-case selection to aggressive demand.
At gamma=2.5, lambda=1 causes sustained planned oscillation and a slower screen; lambda=2
uses 0.027471 m predicted margin slack with 0.060095 m minimum physical clearance. Both are
rejected, retained, and documented. Escalation stopped without changing any frozen mathematics.
No physical boundary crossing, model-domain failure, solver failure or global fallback occurred
in the 25 retained cases. This does not make the rejected behavior acceptable.

## Frozen architecture and implementation

Planning owns offline global line and speed. The accepted geometry and original fixture remain
unchanged. Separate packages scale speed by gamma=1,1.25,1.5,1.75,2,2.25,2.5 with the explicit
6 m/s cap. Capped cubic/constant pieces are serialized offline; runtime does not repair them.
Task 007B advisory feasibility still rejects hard schema/geometry/domain invalidity.

APEX remains always active at 10 Hz: Candidate C N4, dt=0.1 s, four RK4 substeps, exact Hessian,
warm start, native SINGLE. TVLQR 100 Hz, longitudinal gain 1, steering rate 1 rad/s, margin
0.08 m, Q/R/W, terminal/slack costs, plant and prediction equations remain frozen.

J = J_existing - lambda*(s_N-s_0)/(6*4*0.1), using unwrapped s_abs and no new decision variable.
Runtime edits are limited to four existing files: MPC cost grouping, problem reward/components,
controller diagnostics, and Planning loader policy; one new polynomial-loader file is added.
No simulation, plant, TVLQR or solver-backend code changed. No dependencies were added.

## Evidence and interpretation

Selected case: local lateral RMS/p95/max 0.413/0.763/5.239 mm; Planning-to-APEX lateral RMS
5.986 mm. Minimum physical clearance 0.335024 m; maximum predicted slack 9.09e-11 m;
maximum solver primal infeasibility 3.50e-8. Peak front/rear utilization 0.389418/0.307936.
Minimum predicted Frenet denominator 0.778699; progress/physical-distance ratio 1.005254.
No demonstrated near-singular coordinate gaming. Oscillation and margin slack still reject
high-demand progress cases even though their denominators remain healthy.

Selected planner preparation mean/p95/max 23.563/30.387/38.864 ms; codriver
0.840/1.178/3.254 ms. CPU demand 0.3194 core-seconds per physical second, peak RSS 411893760
bytes. Zero planner/codriver misses and minimum reserve 0.277116 s. Baseline had two planner
and one codriver miss. These are measured observations, not deterministic timing guarantees.

Supporting zero and 150 ms injected planner-delay runs completed. Injected case skips 291
planner deadlines while codriver misses remain zero; minimum reserve 0.067 s, no fallback.
Physics continues during planner/codriver computation and previous commands are held correctly.

Nominal-state and preview approximations remain frozen. Increasing demand exposes larger
Planning-to-APEX deviations, sideslip and nominal yaw defects; the evidence does not isolate
vy_ref=0 as the sole cause. TVLQR often tracks the undesirable APEX trajectory accurately.
Review planner/reference quality before proposing an adaptive codriver. No difficulty index,
supervisor, reference-state redesign or next-task feature was implemented.

## Verification and artifacts

- Full regression: **500 passed in 662.93 s** (`results/task007b/regression.log`).
- Ruff check and format: pass, 173 Python files formatted (`results/task007b/lint.log`).
- Independent chronology audit: **25 cases passed** (`results/task007b/verification.json`).
- Telemetry errors independently match physical state minus available packet within 1e-8.
- Objective component accounting and independent stage-channel attribution verified.
- Six 3900x7050 telemetry dashboards and a 3600x3300 comparison were generated and visually
  checked, with sideslip/aggression and high-demand oscillation figures retained.
- Original Task 007A fixture/results and Task 006.4 results are hash-verified by packaging.

Primary files:
`docs/TASK007B_PROGRESS_SEEKING_RACING.md`, `docs/TASK007B_RESULTS.md`,
`docs/TASK007B_REPRODUCTION.md`, `results/task007b/selection.json`, `study_manifest.json`,
`frozen_costs.json`, `pareto_metrics.csv`, `timing_distributions.csv`, `provenance.json`,
`source_snapshot.zip`. Every case retains raw states, commands, events, predictions, packet
history, exact input fixture, telemetry, per-node deviations, objective groups and analysis.
ADRs 140–146 record ownership, validity policy, errors, progress default and scoped selection.

## Reproduction and limitations

See `docs/TASK007B_REPRODUCTION.md`. Benchmarks must be sequential fresh SINGLE workers with
no concurrent tests, rendering or bulk analysis. Use fresh output directories; completed cases
are protected. `scripts/task007b/replay.py` reuses retained fixtures and explicit options.
Early float-rewritten fixture geometry differed by at most 1.4e-14 m; generator v2 preserves
original non-speed text. Per-case hashes preserve this provenance and B0's earlier loader source.

Synthetic physics, perfect state, one circuit and limited comparable laps are not an identified
APEX vehicle operating envelope. Startup screens and complete laps are distinguished. Hardware
latency is nondeterministic. Native set/get confirms SINGLE; exact active-thread count is not
available from Accelerate's API, and CPU/wall evidence is retained. No Pi/ROS deployment.
