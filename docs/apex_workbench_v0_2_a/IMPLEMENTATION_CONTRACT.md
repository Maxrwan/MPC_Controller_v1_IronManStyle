# V0.2-A2 — Proposed implementation and acceptance contract

**Documentation only. Implementation and execution are not authorized.** User-approved D1–D5 are
recorded in [the index](README.md#scientific-decisions-requiring-review). Primary acceptance of the
[remaining numerical decisions](DECISION_SUMMARY.md) and a separately scoped V0.2-B assignment are
required before code. Reuse [ADAPTER_DESIGN.md](ADAPTER_DESIGN.md) and the
[existing implementation stages](IMPLEMENTATION_PLAN.md); this document narrows their first release.

## Small versioned request and fixed construction

Proposed identifiers: adapter `dynamic_lab`, case contract `apex-vdl-linear-cases-v1`, runner profile
`apex-vdl-rk4-zoh-v1`. They become usable/immutable only after acceptance; no case is approved merely
because it has an ID. Register exactly the five [case IDs/full snapshots](PROPOSED_CASES.md).
The first user flow selects a named case and sees every resolved value. No arbitrary numeric
editor, continuous range, mass family, pose edit or sweep engine is part of this minimum release.
D1/D3 permit later finite extensions; those need numerical case qualification, not policy reopening.

The bounded request contains the contract/runner versions, case ID, declared experiment/treatment
key and existing learning note. Normal UI requests use only `nominal`; `half`/`quarter` grid IDs are
explicit qualification requests, accepted only under that authorized workload. Resolve the complete
parameter/state/schedule snapshot from the versioned registry; record it with the request and check
it again in the worker. Reject unknown keys/versions/cases and any conflicting supplied snapshot.
Do not accept arbitrary file paths, injected components, expressions or user Python.

Resolved schedule representation (nominal grid example; amplitude depends only on case):

```json
{
  "duration_ticks": 100,
  "dt_plant_s": 0.005,
  "dt_input_ticks": 1,
  "segments": [
    {"start_tick": 0, "delta_rad": 0.0, "a_cmd_m_per_s2": 0.0},
    {"start_tick": 20, "delta_rad": 0.020, "a_cmd_m_per_s2": 0.0}
  ]
}
```

This is a documentation example, not an executable configuration created by A2. Refinement changes
onset/duration ticks as [specified](NUMERICAL_CONTRACT.md#minimal-future-convergence-qualification),
not physical event times. A one-segment constant schedule is the degenerate grammar case; the first
scientific registry uses only these two-segment steps. No additional constant-input trajectory is
needed to qualify the four questions.

After strict type/finite/schema checks, use canonical `VehicleParameters` plus immutable replace,
`validate_for_dynamic()`, canonical state/control constructors and the default DynamicBicycle
linear/no-allocator/quasi-static load composition. Fixed track is the existing demo `synthetic_track()`
factory, without invoking its `main()`. Use SimulationRunner/RunConfig with the reviewed clock and
an integer-tick prescribed-input provider implementing the existing controller protocol.
All canonical equations, state order/units, limits, geometry checks and guards remain unchanged.
There is no controller prediction model in this open-loop adapter; existing LQR/PI/TVLQR are untouched.

No scientific source change is currently necessary. A need to change canonical equations/interfaces,
frozen YAML, model semantics or the fixed composition returns to review before implementation.
Do not create an adapter-specific dynamics/integration loop or derive missing vehicle dimensions.

## Telemetry and provenance

Use `RunResult.write_csv()` for actual `states.csv` and `controls.csv`. Require a versioned telemetry
contract recording exact columns, names, SI units, row timing, terminal-input meaning and provenance
for derived channels. Required numeric scientific observations:

- `time`, all six canonical states, actual `delta/a_cmd`, lap_index/track_s, curvature, left/right
  widths and `boundary_violation`, from the canonical runner rows.
- Canonical `diagnostics.csv` at each retained sample: alpha_f/r, fyf/fyr, fzf/fzr and static loads,
  cf/cr and cf_eff/cr_eff, fx_total, a_cmd, mu, front/rear lateral utilization and Frenet denominator.
  Recompute through the same immutable model's `diagnostics(x,u)` after raw export, with no further
  integration. These are model-derived diagnostics, not sensor measurements or internal-stage logs.
- Canonical geometry and trajectory XY exports from the **actual injected track**. Current channels
  suffice for all four comparisons. Do not fabricate measured yaw acceleration; derivative oracles
  are future tests, not an extra user telemetry promise.

Required artifacts extend the existing adapter-scoped set with `experiment/controls.csv`,
`experiment/diagnostics.csv` and `experiment/resolved_lab.json`; retain summary, states, geometry,
trajectory XY, telemetry contract, worker result, numerical environment, request/receipt/owner records,
logs and existing manifest. `resolved_lab.json` records full base/effective parameters (including
nulls), exact base YAML path/bytes hash, override key/old/new/origin, full initial tuple and its
origin, composition/track/guard identities, schedule/grid/versions and synthetic labeling.
Summary records runner stop/failure, intended/retained coverage, diagnostic extrema with timestamps
and the separate validity axes. Numerical qualification is **not** inferred by the worker from one
successful run; it references an explicit future qualification record with source/environment and
all grid-run manifest hashes. Associate it only with exact matching cases/profile/source/environment;
changed contents invalidate applicability. New run evidence must still pass its own integrity checks.

Record the existing Git revision, relevant scientific **and lab-provider/factory/export/validation**
source hashes, dependency/native runtime controls, numerical environment and actual applied controls.
Case ID or base YAML alone is insufficient proof of the effective model. Labels/ranges/derived
summaries must identify source rows and coverage, including terminal informational controls.

## Ownership, integrity and controlled comparisons

Reuse the verified V0.1 worker-owned execution lease, supervisor-death/cancellation recovery,
PID/birth/full-command/run-path identity checks, atomic request/status and note publication, exclusive
outcome receipt, final manifest anchor, hash-on-consumption/quarantine and stale-status reconciliation.
Preserve resource/disk/measurement-guard preflights and native controls before numerical imports.
Run serial existing jobs; no new worker pool. Launcher convenience confers no bypass or new limits.
Register explicit lab dispatch/validation/artifact/geometry branches; current otherwise-LQR fallthrough
must not receive a new adapter. Preserve V0.1 requests, defaults, exports and comparison semantics.

For a lab controlled candidate, compare the actual resolved snapshots and applied schedules, with
identical accepted contract/profile, numerical source/environment, base, tire/load/allocation,
track geometry, guards, initial tuple, grid/horizon/terminal rules, telemetry schemas and all fields
except exactly the declared treatment. The only permitted first pairs are BASE versus each of
IZ_HIGH, STEER_HIGH, CF_HIGH and CR_HIGH. For steering, one post-step amplitude is the treatment;
the resulting repeated control rows are its applications, not independent factors. Case IDs,
override-origin descriptions and run IDs differ as metadata; they may not conceal extra scientific
differences. Compare exact resolved values, never rounded plot labels or just an allowlisted hash.

Compatibility and [full qualification](VALIDITY_CONTRACT.md) are separate decisions. A changed dt
pair is a numerical refinement comparison, not a physical single-factor comparison. Missing evidence
is invalid; known multi-factor or cross-adapter overlays are illustrative. Keep existing V0.1 behavior
and historical classifications; do not retroactively promote/reseal old runs or ignore all vehicle
fields to enable a lab comparison. No full regression/NMPC/async/hardware campaign is authorized here.

## Minimum future tests and independent oracles

**Plan only — none run or collected in A2.** Implement focused tests after scoped authorization,
then run the qualification only when its execution is authorized. Reuse outputs rather than launch
duplicate trajectories; the [17-trajectory budget](NUMERICAL_CONTRACT.md#minimal-future-convergence-qualification)
covers scientific lab runs, not the existing regression suite.

| Check | Minimal meaningful evidence / independent oracle |
|---|---|
| Parameter propagation/construction | All five resolved snapshots against literal accepted table; exactly one allowed treatment; base immutable; canonical actual model parameters/component classes/guards agree. Reject altered fixed fields, unknown/null/bool/string/nonfinite inputs, conflicting snapshots and unsupported cases. No adapter-generated expected snapshots. |
| Immediate mathematics | Call canonical derivative/diagnostics at shared valid body state and compare body force/moment values with the analytical table, including CR_HIGH initially unchanged. Explicit new fixture tolerance proposal: absolute 1e-12 in each quantity's own SI unit. Preserve existing component/model mathematical tests; no golden trajectories generated by the adapter. |
| Input ticks/exports | Literal expected controls per integer tick for all three grids; onset previous/new interval, initial/terminal rows/counts, held input across stages. Include constant-provider grammar, invalid/duplicate/off-grid/terminal events and reset/immutability checks; a recording model may check scheduling but cannot qualify physical dynamics. |
| Canonical-runner parity | One nominal baseline independently constructed with canonical parameters/model/track/runner and a literal test-only schedule, avoiding adapter normalization/provider. Compare every time/state/control row and canonical sample diagnostic, byte equality where export schema matches. Reuse the nominal adapter output. Propagation and analytical tests cover all treatments without four duplicate reference trajectories. |
| Repeatability | One additional nominal adapter baseline in a fresh serialized worker, exact scientific CSV equality under identical recorded numerical environment. No wall-time equality assertion. |
| Numerical/experiment qualification | Five cases × three grids; componentwise convergence, native sampled validity filters and four yaw-signal comparisons as proposed. Retain all failed/weak/partial outcomes. No automatic retries/tuning/extra grids. |
| Evidence/lifecycle/classification | Extend real V0.1 regression paths to new nested metadata/artifacts; deletion/corruption of every required/manifest-listed file blocks scientific display. Test completed/evidence-failed, handled runner failure, cancellation/SIGKILL lease recovery, atomic publication, stale status, additional-factor rejection and qualification/source mismatch. Exercise real workers where ownership/integrity behavior is asserted, not only mocked outcomes. |
| V0.1 preservation | Existing [Workbench tests](../../tools/apex_workbench/tests/test_workbench.py) and [correction tests](../../tools/apex_workbench/tests/test_corrections.py), original dynamic/LQR byte parity, and applicable focused canonical config/state/dynamic/component/Frenet/runner/baseline, dynamic track and accuracy tests. Use [the focused guide](../CODEX_TEST_GUIDE.md). Prior counts are historical, not new evidence. |

Implementation WORK and Engineering Review precede separately authorized exact-SHA Verification.
The complete applicable suite belongs to that later gate per [workflow](../CODEX_VERIFICATION_WORKFLOW.md),
with frozen research skips retained. Scientific approval of numerical proposals does not itself run
or implement anything; no automatic V0.2-B transition occurs at this delivery.
