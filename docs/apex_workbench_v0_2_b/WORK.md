# Vehicle Dynamics Laboratory — V0.2-B implementation WORK

**WORK_COMPLETE_PENDING_REVIEW.** 28 October 2026. Accepted scientific/design basis:
`0cc7e4f626311aec05977bd3beda40c346fa4214`. Branch `codex/apex-workbench-v0-2-b`.
The containing implementation commit is the delivery revision; its exact SHA/URL is reported after
push. This is neither Engineering Review approval nor formal Verification/numerical qualification.
The [machine record](work_record.json) binds source identities, commands, logs and parity hashes.

## Implemented behavior

The existing one-click launcher opens the Workbench with an additional **Vehicle Dynamics Laboratory**
selection. Choose `VDL1_BASE`, `VDL1_IZ_HIGH`, `VDL1_STEER_HIGH`, `VDL1_CF_HIGH` or `VDL1_CR_HIGH`,
inspect the complete SI snapshot/seed/schedule, enter a prediction and run the canonical plant.
All five full snapshots match the accepted finite contract. No editable range or mass case is added.

The lab constructs immutable canonical VehicleParameters, DynamicBicycle, LinearAxleTire and
QuasiStaticLongitudinalLoadTransfer, with the actual existing synthetic track injected into both
runner and geometry export. SimulationRunner supplies 100 held-input RK4 intervals, 101 state rows
and 100 control rows for the accepted 0.500 s nominal profile. The provider changes steering at tick20;
the terminal command is informational. There is no new dynamics/integration loop, feedback controller,
equilibrium reconstruction, clamping or physical coupling law in tooling.

The plots consume retained state/control/sample-diagnostic CSVs: yaw/lateral/longitudinal response,
steering/a_cmd, slip, lateral forces, loads, nominal/effective axle stiffness, utilization, Frenet
denominator, sampled CG corridor information and canonical XY. Lab CSV parsing preserves float
round trips. Source/effective configuration, origins, complete initial tuple/schedule, contract and
criteria versions, numerical environment, outcome/receipt and artifact hashes remain inspectable.

All required lab artifacts are hashed before scientific display. Schema/units, full snapshot, seed,
ticks/applied controls, row coverage, summary consistency and numerical/source identity are checked.
Corruption/missing evidence blocks even state-only graphs. Separate execution, evidence, numerical,
sampled interpretation, excitation and comparison categories remain visible. Sampled filters retain
the accepted provisional values; no physical validation or numerical-error guarantee is claimed.

BASE versus exactly one treatment, in either order, can become a **controlled candidate** after
verified exact metadata/input/source/environment/geometry checks. Other known pairs are illustrative;
failed/incomplete/unknown/corrupt records are invalid. No completed run, large yaw difference or
manually asserted qualification label can promote a record to a qualified synthetic comparison.

The shared lease/identity/guard/cancellation/recovery, atomic publication, immutable outcome receipt,
manifest commit, native SINGLE setup and resource/disk/measurement protections are retained. Raw
runner CSVs precede diagnostic export, handled failures retain partials without invented terminal
samples, export failures remain failures, and completed execution remains separate from evidence
validity. The original dynamic-demo/LQR entry-point paths/defaults/exports remain intact.

## Fresh focused software evidence

All numerical invocations used the existing isolated Workbench Python environment and the documented
Accelerate SINGLE bootstrap before numerical imports. Commands/logs are retained locally under
`results/apex_workbench_v02b_work_20261028/`; logs are ignored artifacts, with hashes in the committed
machine record. No result below is inherited from V0.1 or counted twice as a distinct assertion.

| Invocation | Result and disposition |
|---|---|
| Initial new lab tests, `lab-tests.log` | 44 passed, 2 failed. Retained failures exposed pandas decimal parsing precision and a test dropdown selected by position. Corrected exact lab float parsing and label-based test selection. |
| Combined focused suite, `focused-tests.log` | 297 passed, 1 failed; no setup errors. Included 46 then-current lab tests, all 78 existing Workbench tests and 174 selected canonical tests. The one legacy UI failure caught two extra lab charts appearing in legacy comparisons. Scoped them to lab comparisons. |
| Final affected tests, `affected-tests.log` | **50 passed, zero failures/errors**: all 49 final lab tests plus the failed legacy comparison/quarantine UI regression. Adds incomplete-environment rejection and a real laboratory form submission. |
| Static final checks | Ruff check/format, Git whitespace, documentation links and preservation checks pass. No scientific source/configuration or accepted numerical criterion changed. |

The resulting distinct coverage is **49 lab +78 existing Workbench +174 canonical =301 focused
test cases**, covered across those invocations; there was no single 301-pass invocation. The remaining
77 Workbench and 174 canonical passes remain applicable: subsequent changes only tightened lab
evidence validation and restored the legacy comparison UI; all affected lab/UI checks were rerun.
Existing suites were not repeated solely for a cleaner count. Prior failed logs and raw attempts remain.

The canonical selection was `tests/unit/test_config.py`, `test_state.py`, `test_dynamic_components.py`,
`test_dynamic_bicycle.py`, `test_frenet.py`, `test_runner.py`, `test_baseline.py` and
`tests/regression/test_dynamic_accuracy.py`. These are software/model correctness fixtures, not the
new case family's scientific qualification. Existing original dynamic/LQR byte-parity, owned-worker
parity, SIGKILL lease/recovery/cancellation, failure/evidence, publication and legacy comparison tests
ran freshly. Core tests/fixtures themselves were not modified.

All five cases received literal full-snapshot/component/initial-state propagation checks and
independent analytical force/body-derivative checks at the shared state. Unit scheduling checked all
three accepted grids **without propagating a model**. Actual nominal nonlinear WORK smoke trajectories
used BASE and STEER_HIGH, plus an independent nominal canonical-runner reference. Injected failures
and deliberately damaged/rebound copies are software test fixtures, never physical results or
repairs of real/historical records. No full-path result for the other three treatments is claimed.

## Independent canonical-runner parity

`test_canonical_runner_and_diagnostic_byte_parity` independently loads the canonical synthetic YAML,
constructs DynamicBicycle/track/SimulationRunner and uses a literal test-only input provider. It does
not use the adapter's resolver/provider for expected trajectories. Every state/control/diagnostic row
matches exactly, and canonical XY is checked for each exported sample.

| Artifact | Equal adapter/direct SHA-256 |
|---|---|
| states.csv | `43e9945f2c458ce80dd3f234da6b3c2b4639c760c8c4ddd6321bae5e5c9ec389` |
| controls.csv | `139c0767e1ba41ae44a3a45fdd7c609d6c57b604812556e38b1fcea29c4c6577` |
| diagnostics.csv | `55730ba2c41350e8e34685e815f178e92805b5168f896d483e361e22bc0e0463` |

Artifacts live under `affected-tests/test_canonical_runner_and_diag0/` in the local evidence root;
`parity.json` records their identities. This proves adapter/direct-runner agreement for the nominal
software fixture; it is not an independent ODE accuracy proof or physical validation.

## Preservation and remaining gates

Before/after hashes cover all 910 preexisting tracked files; changes are restricted to authorized
tooling/docs. Canonical source, original scripts/core tests, configuration/dependency files, launcher,
accepted contract documents and historical review records are unchanged. Of 19,101 preexisting result
files, 19,100 retain size/mtime; only `results/.DS_Store` filesystem-view metadata changed during the
task and is left as observed. No scientific result changed. This is not a content rehash/backup.
The preexisting local browser
server was observed, left running and was not treated as a task-owned smoke server.

No genuinely unresolved scientific decision was discovered. Existing accepted values and provisional
criteria stand. Remaining work requires separate authorization:

- Independent Engineering Review of the exact implementation revision and retained negative evidence.
- The planned three-grid/17-trajectory qualification, repeatability and excitation/window assessment,
  followed by versioned qualification-record association. This WORK admits only nominal lab runs;
  refinement execution admission and qualification ingestion/evaluation remain deferred to that stage.
- Formal exact-SHA complete applicable Verification and subsequent acceptance. No full-suite run,
  timing benchmark, new parameter sweep, NMPC/async/other controller, hardware or frozen research
  campaign occurred. Software smoke runs are not the qualification campaign.

**Stop: WORK_COMPLETE_PENDING_REVIEW.**
