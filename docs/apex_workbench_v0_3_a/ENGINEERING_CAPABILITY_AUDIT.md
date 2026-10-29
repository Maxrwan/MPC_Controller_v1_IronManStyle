# V0.3-A — engineering capability audit

**V0.3_ENGINEERING_MVP_DESIGN_COMPLETE_PENDING_REVIEW.** 29 October 2026.
V0.2 is accepted by Primary for its verified finite synthetic scope. This is a static source,
documentation and retained-file audit: no project module import, UI/server launch, test collection,
scientific calculation, simulation or benchmark. Previous execution evidence is explicitly inherited.
The product direction is an engineering workspace; learning is optional supporting material.

## Revision ledger

| ID | Exact audited identity | Authority / evidence |
|---|---|---|
| W | Workbench source `4897686e79c13757d5ef5b4373b44d4cab99b5bf`; accepted delivery/parent `0f74afb9121ee6834509e82f17153b539a59b828` | [Formal Verification](../reviews/apex_workbench_v0_2_e/VERIFICATION.md): historical **1,016 passes, 17 separately gated G2 skips**; [machine record](../reviews/apex_workbench_v0_2_e/verification_record.json). Source/evidence hashes checked statically here, not tests rerun. |
| Q | Contract `0cc7e4f626311aec05977bd3beda40c346fa4214`; qualification delivery `cd4da167166af63d758f715ede166a0e6a73b76a` | [Accepted finite results](../apex_workbench_v0_2_d/QUALIFICATION.md): five cases, four comparisons, 17 trajectories. Original qualification SHA-256 `f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8` unchanged. |
| P | `main` / `release/performance-synthetic-v1` at `48adbdf64d492592d15e23c917aca71fa58aa8a5`; verified scientific source `e603672b209985f11ed26b6f44d3949ffd5675c5` | [Primary E4 acceptance](../TASK007E4_PERFORMANCE_ACCEPTANCE.md), [overlay](../task007e/e4/primary_acceptance.json). Architecture A, variable availability, bounded synthetic profile. Fixed C70/C80 are not the default accepted architecture. |
| F | `research/efficiency` at `37b3f19a5d58f9a76cfd9dee5cb5bf4352edc980`; clock executable `c99b9dfdc981cb13ccd2e5ff53af98a3b568f70a` | [Clock report](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/37b3f19a5d58f9a76cfd9dee5cb5bf4352edc980/docs/task007f/profile1/clock_only_execution_report.md): one clock-only attempt; observer validity incomplete, allowance unresolved. No Phase B/controlled G2 acceptance. |
| C | `research/control-theory-ct1` at `265d02f479b7bb759baff9205156635f2da45887` | [L2B handoff](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/265d02f479b7bb759baff9205156635f2da45887/docs/ct1/ct1l/l2b_handoff.md): static-only implementation; independent review/L3 pending; whole-command 300 s timer gap unresolved. |
| S | `research/safety-s0` at `24cd70ca18b3efa56a9412d7cef9a86466091721` | [S1-A work evidence](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/24cd70ca18b3efa56a9412d7cef9a86466091721/docs/safety/s1a/implementation_work_evidence.json), [oracle review](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/24cd70ca18b3efa56a9412d7cef9a86466091721/docs/safety/s1a/oracle_completion_review.md). Unverified logical-authority candidate; no physical endpoint. |

Direct `git ls-remote --heads` matched these local heads. The Workbench, CT, Safety and detached
FC1 worktrees were clean at inspection. Research trees were read only, never checked out into or
merged with W. The new documentation branch is `codex/apex-workbench-v0-3-a-design`, from W's
accepted delivery. No previously proposed V0.3-B/C/D sequence is treated as binding.

## Actual capabilities

Labels: **V** available and verified within the cited scope; **U** implemented but unverified;
**R** research/development in progress; **N** planned or unsupported. A core capability is not
automatically a Workbench launch option. Current G1-instrumented runtime bytes differ from P;
W's functional passes do not replace P's exact scientific identity or F's missing observer gates.

| Capability | Class / actual interface | Scope and Workbench availability |
|---|---|---|
| Dynamic plant, track and integration | **V**, [DynamicBicycle](../../src/apex/models/vehicle/dynamic_bicycle.py), [VehicleParameters](../../src/apex/models/vehicle/parameters.py), [runner](../../src/apex/simulation/runner.py), [RK4](../../src/apex/models/integration.py) | Independent six-state dynamics, injected track/tire/load model. W's demo and five-case lab use canonical code. Synthetic parameters; forward-speed/domain guards, no standstill or physical validation. |
| Linear and alternative grip tires | **V**, [linear](../../src/apex/models/tire/linear.py), [smooth combined grip](../../src/apex/models/tire/grip.py), [allocation](../../src/apex/models/vehicle/force_allocation.py), symbolic prediction | Distinct compositions, not interchangeable widgets. Linear law is unsaturated and mu diagnostic; smooth grip needs explicit longitudinal allocation/validity and matched prediction. W has no tire selector and Q covers only its prescribed linear composition. |
| Scheduled LQR/PI baseline | **V**, [ScheduledLQR](../../src/apex/control/baseline/lqr.py), [BaselineController](../../src/apex/control/baseline/controller.py), [SpeedPI](../../src/apex/control/baseline/speed.py) | Four-state lateral design at 1/2/3 m/s, interpolated gain, separate nonlinear plant and PI. W launches `run_lqr_baseline.run_case`, fixed 200/100 Hz, supported config only. This is **not TVLQR**. |
| LQR engineering analysis | **V** equations/tests; retained export needs source binding, [linear_analysis](../../scripts/run_lqr_baseline.py), [metrics](../../src/apex/simulation/metrics.py) | Nodal gains/poles/controllability and interpolated spectral-radius study already implemented. Run-bound gain/reference/saturation channels exist. `results/lqr_baseline/linear_analysis.json` exists but is not a Workbench-manifest-bound artifact; do not infer its source version from its filename. |
| NMPC and solver diagnostics | **V** for documented regression/profile scope, [MPCProblem](../../src/apex/control/mpc/problem.py), [MPCController](../../src/apex/control/mpc/controller.py), [IpoptSolver](../../src/apex/optimization/solvers/ipopt.py) | Separate NumPy plant and CasADi prediction; backend protocol plus IPOPT adapter; objective/components, status, primal infeasibility, iterations, timing. W cannot launch it. Solver success is not global optimality; arbitrary controller/tire/profile combinations are not qualified. |
| Trajectory TVLQR/tracker | **V** scoped runtime/tests and P, [TVLQR / TrajectoryTracker](../../src/apex/control/trajectory/tracker.py), [packets/buffer](../../src/apex/control/trajectory/packet.py) | Packet-dependent 10 ms discrete Jacobians/Riccati gains, terminal DARE, separate longitudinal P, command/rate limits. Saved X/reference/U/K and errors exist in archives. W has no execution or archive adapter. |
| Variable asynchronous planner/tracker | **V** scoped P and regressions, [AsyncRunner](../../src/apex/simulation/asynchronous.py), [planner](../../src/apex/control/trajectory/planner.py), [timing](../../src/apex/simulation/timing.py) | Physics advances during preparation; actual availability, staleness, skips, reserve/fallback and separate planner/codriver misses. Event simulation is not OS/hardware concurrency certification. No W adapter. |
| Fixed handoffs | **V** for bounded opt-in research verification, [FixedHandoffs](../../src/apex/simulation/fixed_handoff.py), [contract](../TASK007D_C_FIXED_HANDOFF.md), [CX verification](../TASK007D_CX_VERIFICATION.md) | Explicit deadlines, waiting/late discard and urgent-grid chronology. Default remains variable Architecture A; no automatic promotion of C70/C80. Recorded fixtures available for investigation/replay. |
| CT-1 / CT-1L analysis | **U**, research C's `scripts/ct1/{analytic,rk4,linear_systems,riccati,closed_loop}.py` | Implemented map/derivative, SVD/PBH, original-gain, finite-product/defect machinery; L2B tests and numerical analysis unexecuted. No numerical rank/stability result or completed L3 claimed. CT-1N/R trials remain proposals. |
| Efficiency / profiling | **R**, F; current optional recorder branches in planner/tracker/solver | Mechanistic clock evidence exists; G1 implementation remains unqualified for controlled profiling. No approved observer-cost allowance, cost correction, speedup or full profiling qualification. Existing full-runtime timings and sampled resources remain descriptive. |
| Safety S0/S1 | **R**, S's `src/apex/safety_authority/` | S0 architecture acceptance is not physical validation; S1-A is an implemented but unverified pure logical candidate, with pending oracle/review/execution gates and no implemented endpoint. Do not import it into W or expose command/arming controls. |
| Perception-to-Control / physical monitoring | **N** as an integrated capability in audited refs | Canonical [state](../../src/apex/state.py) is a simulation/control vector, not a sensor wire schema. S references pending Perception v0.3 producer/clock/frame/uncertainty contracts; no accepted physical producer/adapter is present here. External departmental work is outside this audit. |
| Estimation, identification, opponents, tactics, energy/LMPC | **N** for practical W use | Package placeholders or design references are not implementations. No invented measurement model, identified tire data, defensive-racing logic, ROS or hardware capability. |

## UI/architecture findings and evidence assets

Actual [UI](../../tools/apex_workbench/app.py), [plots](../../tools/apex_workbench/plots.py),
[configuration](../../tools/apex_workbench/configuration.py), [storage](../../tools/apex_workbench/storage.py),
[jobs](../../tools/apex_workbench/jobs.py) and [qualification](../../tools/apex_workbench/qualification.py)
were inspected. It has Experiment / Compare runs / Capabilities, four result tabs, optional prediction,
append-only notes, three execution adapters and exactly two selected comparison runs. No file import,
playback cursor, multi-plot time synchronization or live vehicle-monitoring path exists. Plotly figures
exist; explicit reproducible figure export is not an accepted workflow. The ZIP is explicitly labeled
as potentially including unverified evidence, not a certified export bundle.

**D1:** hard-coded `V0.2 WORK` / “qualification has not been performed” text is stale after Q/E;
actual immutable run summaries correctly remain separate from selected qualification. **D2:** discovery
only scans `results/apex_workbench`; the accepted 17 Q runs are elsewhere, although its optional
qualification record selector can find their qualification. **D3:** [source inventory](../../tools/apex_workbench/lab_sources.py)
includes `app.py` and `plots.py`; changing these invalidates current-source applicability. Do not
silently relax that enforcement. **D4:** C's general handoff still describes L0/no code; the later
L2B handoff and actual source are authoritative for this audit. No research handoff was edited.

Reusable assets: Q lives under `results/apex_workbench_qualifications/v0_2_reviewed_20261029/`;
its published references bind BASE, IZ_HIGH, STEER_HIGH, CF_HIGH and CR_HIGH. Accepted synthetic C0
failure fixture: `results/task007d/c/amended/c0_export/original155.json`. A separate preliminary
`results/asynchronous_planner_tracker_preliminary/serialization_failure_250ms/` retains CSV/packets
but lacks summary: its log shows a JSON serialization TypeError, not evidence of an IPOPT failure.
Neither archive is silently upgraded into a Workbench run or qualified comparison.

Static evidence/snapshot/asset index: `results/apex_workbench_v03a_audit_20261029/`.
The [gaps](MVP_SCOPE_AND_GAPS.md), [analysis backlog](CONTROL_ANALYSIS_BACKLOG.md),
[roadmap](MVP_ROADMAP.md), [acceptance scenarios](ACCEPTANCE_SCENARIOS.md) and
[next task](DECISIONS_AND_NEXT_TASK.md) share this revision ledger. No critical discrepancy in W's
accepted numerical results was found; D1–D4 are presentation/discovery/research-status constraints.
