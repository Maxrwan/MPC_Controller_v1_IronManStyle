# Minimum implementation and regression sequence

**Design only; not an implementation authorization.** Start only after scientific review of the
[five decisions](README.md#scientific-decisions-requiring-review) and a separately scoped instruction.
Canonical science, frozen profiles, V0.1 behavior and old evidence stay protected at every stage.

## Proposed stages

| Stage | Small deliverable | Necessary focused checks / exit evidence |
|---|---|---|
| B1 — Model configuration adapter | Strict lab schema/contract and immutable base-plus-override factory; fixed linear/load/track composition; complete effective provenance | Literal approved valid/invalid values for every exposed field; reject unknown/null/bool/nonfinite/coercible-string inputs, unsupported fields and inconsistent geometry. Call canonical readiness/constructor checks; verify originals/fixtures unchanged. No full parameter sweep. |
| B2 — Initial state and input schedule | Explicit full state, independent vx/vy/r overrides, tick-aligned ZOH constant/step provider; existing SimulationRunner; actual state/control/diagnostic/geometry exports | Independently construct the canonical model/runner as oracle; inspect applied inputs and every timestamp, first/terminal rows, failed/domain/partial outputs, no hidden pose or control reconstruction. Retain existing worker/import-order/lifecycle/resource protections. Register the adapter only when this vertical path genuinely works. |
| B3 — Sensitivity visualization | Existing Plotly raw-time overlays with allowlisted real r/vy/vx, slip, force/load and nominal/effective-stiffness channels; explicit units/source/coverage | CSV-to-plot value checks; missing/corrupt every required new artifact visibly quarantines; optional channels unavailable, never fabricated. No fitting, new solver or frontend rewrite. |
| B4 — Controlled comparison and learning | Lab-only one-factor treatment contract and metadata diff; existing prediction/observation/explanation workflow | Same-profile intended factor controlled; extra physical/input/state/time changes illustrative or invalid as specified. Unknown schema/units/failed coverage and tampering invalid. Historical V0.1 eligibility/notes remain unchanged. Serial manual two-run comparisons suffice; no sweep scheduler. |
| B5 — Engineering Review / Verification | Exact committed candidate, independent review of construction/semantics/results, then explicitly authorized complete applicable acceptance gate | Focused new tests and V0.1 regressions pass before review. Review is not automatic execution authority. At Verification, run the complete required set on that exact revision; preserve skipped independent scientific gates and classify software/parity/evidence separately from physical validity. Stop for acceptance. |

These stages are small reviewable increments of one lab, not five independently advertised unfinished
features. No user should be offered a working vehicle-property editor that cannot yet run, retain
and explain its actual effects. No broad architecture/plugin framework is required.

## Future source scope to propose with the implementation assignment

Indicative tool-local paths only; **none is created/edited by V0.2-A**:

- New `tools/apex_workbench/lab_configuration.py`, `dynamic_lab.py` and narrow test files under
  `tools/apex_workbench/tests/` for construction/schedule/export/comparison.
- Minimal explicit branches in `configuration.py`, `worker.py`, `jobs.py`, `storage.py`,
  `comparison.py`, `plots.py`, `app.py` and their documentation. Existing two-adapter fallthrough
  paths must become explicit before a third adapter is registered.
- No edits to `src/`, original experiment scripts, core tests/fixtures/dependencies, configuration
  YAML, accepted profiles or historical results are required by the recommended composition.
- A reusable original-demo function extraction, if required by a stricter cross-profile byte-parity
  decision, needs its own scientific-entry-point allowlist/review. It is not silently included here.
- No launcher change is indicated by this audit; retain the accepted one-click path and protections.

## Minimal test plan, without unnecessary campaigns

1. **Static/contract checks after code is separately authorized:** keep canonical order/units,
   explicit field allowlists, immutable base/config snapshots, lazy numerical imports after native
   controls, no force/kinematic/integration equations in tooling and no unused UI parameters.
2. **Factory/schedule units:** canonical P validation plus reviewed fixture expectations independent
   of adapter normalization; coupled geometry; initial vector provenance; event ordering/grid/limits;
   each fixed/overridden/derived value; identical reset/repeat behavior. Do not populate the expected
   result by calling the adapter under test.
3. **One short real path per supported profile and approved parameter case family:** direct canonical
   runner versus adapter, not an invented plant. Compare actual initial state, applied controls,
   sample times, states and exported diagnostics. The legacy demo/LQR paths keep their original
   exact byte-parity checks, including original partial-step behavior for dynamic compatibility.
4. **Focused nonlinear/domain checks:** existing low-speed, maximum-speed, command, load, Frenet,
   evaluated-stage and integration contracts. Add only override-specific acceptance/convergence cases
   needed for approved inertia/stiffness/initial/input combinations. Do not infer continuous-time
   boundary enforcement from sampled/RK-stage checks. No tuning or new large campaign.
5. **All Workbench regressions:** R1 supervisor SIGKILL/worker lease/legacy malformed owner/recovery,
   cancellation and limits, two-reader publication, notes atomicity, comparison, failed evidence,
   required/manifest-listed deletion (including receipt/owners), changed-byte cache invalidation,
   malformed selected metadata and real UI execution. Test new nested metadata under the same paths.
6. **Relevant canonical tests, when applicable:** `test_config.py`, `test_state.py`,
   `test_dynamic_components.py`, `test_dynamic_bicycle.py`, `test_frenet.py`, `test_runner.py`;
   retain `test_baseline.py` and the original LQR parity because V0.1 must stay intact. Existing
   `test_dynamic_track.py`/`test_dynamic_accuracy.py` are the established geometry/accuracy anchors.
   Tire-specific tests are needed only if their separately approved adapter/composition changes.
7. **Formal gate after exact-SHA review/authorization:** the repository complete acceptance set is
   `tests/`, with all `tools/apex_workbench/tests/` added outside default pytest testpaths. Use the
   documented native bootstrap, fresh outputs, serialized work, measurement guards and disk floor.
   Do not enable frozen Profile1 G2 or other separately gated research merely to remove skips.

Run successful unchanged suites once where their source/dependencies/assertions/environment apply.
If a bounded fix changes a dependency, rerun failed/affected checks, then broaden only for unresolved
risk or an explicit gate. Save exact SHA/diff/source identity, commands, exit status and full logs.
Do not reuse V0.1 pass counts as if they were V0.2 execution; review any proposed result reuse.

## Acceptance and stop rules

- Existing V0.1 defaults, adapter routes, outputs and legacy comparison classifications remain
  unchanged; new lab defaults have their own explicit profile, not an undocumented compatibility claim.
- No scientific source/configuration/profile/history changes; no hidden parameter coupling, equilibrium
  solve, speed regulation, force clipping, low-speed blending or substituted tire model.
- Complete, inspectable effective provenance and actual sampled data; failures/partials/unknowns and
  evidence validity stay separate. Never repair a damaged historical record to get a passing view.
- The three learning experiments run only approved cases; numerical success is not physical acceptance.
- Any new parameter semantics, validity/coupling assumption, required canonical/interface change or
  unsupported tire/control capability returns to scientific review before implementation.

V0.2-A ends at **V0.2_DESIGN_COMPLETE_PENDING_SCIENTIFIC_REVIEW**. There is no automatic transition
to B1, no numerical prototype run, and no reopened Performance/Efficiency/Safety/VIS/NMPC/async/hardware work.
