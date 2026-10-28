# V0.2-C corrective WORK and qualification preparation

Candidate status: **WORK_COMPLETE_PENDING_REVIEW**. Recorded 29 October 2026.
Base/review delivery `4bac7b49f623c13ee90ab7ff79376f3f5ca6b4ec`; reviewed implementation
`895ecddf55754e94d5dbf53d5aca01f91f013a05`; unchanged scientific contract
`0cc7e4f626311aec05977bd3beda40c346fa4214`. Branch `codex/apex-workbench-v0-2-c`.
An exact committed candidate receives separate-context Engineering Review before readiness is
reported. No scientific qualification campaign or formal Verification is authorized here.

## C1–C3 closure

| Finding | Correction | Focused evidence |
|---|---|---|
| C1 source identity | `apex-dynamic-lab-sources/1` names56 actual required dependencies: model, runner/state/units, RK4, Frenet/angles, tire/load components, track/import closure, native controls, lab construction/export/readers and qualification code. Admission captures from the existing source ledger and rejects missing identities; consumption checks exact inventory/version/ledger consistency. No missing value is filled from the current checkout. | Every inventory entry is individually removed in tests; runner omitted on both rebound records is invalid. Static canonical-import closure is checked. Known complete differing inventories remain illustrative for ordinary comparison. |
| C2 aliases | Exact finite float64 equality for copies of the same canonical sample/input; no new physical tolerance. Cross-check a_cmd against actual input, diagnostic track_s/curvature against state, and state track_s/curvature/widths against new canonical per-sample `track_samples.csv`. Nominal Cf/Cr must match the captured effective parameters. | Rebound contradictory command, geometry, width and nominal-stiffness fixtures are rejected even with rederived summaries. Producer exports call the actual injected track, not interpolated plotting geometry. Readers add no force/dynamics equations. |
| C3 coverage/outcome | Completed implies successful full integration coverage; cancelled/interrupted/failed outcomes may retain full coverage without becoming successful or comparable. Genuine partials remain inspectable. Semantic quarantine preserves raw evidence/log access. | Cancelled/interrupted/failed full-output copies remain inspectable and invalid for comparison. Partial and fabricated-coverage tests, plus a real Streamlit retained-cancellation view, pass. These are bounded software fixtures, not a claimed live cancellation race. |

The new lab adapter version is0.2.1 and lab telemetry schema is2. Older lab records lacking the
versioned inventory are preserved and ineligible rather than silently upgraded. V0.1 request,
provenance, original entry points and scientific exports retain their existing behavior. Original
review documents, failed logs and historical artifacts remain unchanged.

## Prepared fixed protocol

Normal UI admission remains nominal-only. The explicit qualification context admits exactly the
accepted5/2.5/1.25 ms grids, with onset ticks20/40/80 and terminal steps100/200/400. All cases keep
onset0.100 s, duration0.500 s, the accepted seed/parameters and canonical runner/RK4. A separate
`software_test` context cannot supply scientific qualification evidence.

`qualification_campaign plan` prints the fixed17-slot scope without starting workers: five cases
times three grids, one additional nominal BASE repeat and one independently assembled nominal BASE
canonical reference. Total3,700 intervals,8.5 simulated seconds. Future execution requires explicit
acknowledgement and an exact reviewed source SHA; every required current file is compared with that
Git revision before each existing bounded worker. All workers are serialized under the existing
lease/resource/native/disk/measurement safeguards. Any failed/interrupted execution stops the
campaign with retained status/data and no automatic retry, tuning or favorable substitution.

The reference uses literal accepted parameters, independent canonical track/runner construction and
a literal20-zero/80-step provider, not the lab constructor/input-provider implementation. It shares
only canonical result export. The ordinary independent nominal parity test still constructs expected
CSV/diagnostic/XY data separately, and remains required.

The evaluator:

- Verifies17 distinct source-run manifests, every referenced artifact byte, exact case/grid/role,
  purpose, source inventory, numerical environment, geometry and schema. Shared artifacts are not
  duplicated into invented trajectories; each original execution stays bound to its own manifest.
- Uses shared nominal ticks only, without interpolation; wraps only e_psi using the canonical angle
  function. Evaluates every accepted per-channel error/contraction criterion and all native sampled
  slip/utilization/corridor/coverage criteria. It preserves all differences/extrema and failures.
- Separates per-case numerical convergence, sampled interpretation and each pair's yaw excitation;
  an unrelated weak treatment does not rewrite another pair's numerical status. Family and pair
  decisions remain distinct. Exact BASE repeat/reference scientific CSV equality is required.
- Publishes a versioned immutable qualification document and final checksum commit only from
  verified real qualification-purpose runs. Mathematical fixture results always identify themselves
  as calculations without evidence authority. Test-only/interactive data cannot be promoted.
- Revalidates referenced bytes/manifest anchors and the qualification document on consumption;
  changed evidence, source inventory, current scientific code or environment invalidates application.
  Selected nominal runs must match the qualified finite case's actual scientific exports exactly;
  that is an applicability identity check, not an additional numerical-error tolerance.

Individual run summaries remain immutable and unqualified at export. A later externally selected
verified qualification record supplies the separate numerical/comparison assessment. It never
establishes physical validity, hard real-time behavior or unsupported controller capability.

## Focused tests and current limits

Raw local evidence: `results/apex_workbench_v02c_work_20261029/`.

| Invocation | Result |
|---|---|
| `focused-1.log`, all Workbench tests |224 passed, including existing V0.1 original/worker parity and lifecycle/integrity regressions |
| `affected-1.log`, lab/closure/evaluator after record-consumption hardening |149 passed |
| `affected-2.log`, per-axis assessment tests |148 passed,1 failed: an insufficient-excitation fixture changed only nominal yaw, unintentionally introducing a grid discrepancy. The evaluator correctly rejected numerical qualification. |
| `literal-fix.log` |1 passed after making that mathematical fixture's zero response consistent across all grids; no production criterion or scientific case changed |

Successful unchanged tests are not repeated merely to combine counts. All attempts/logs remain.
One BASE/half functional rate/export smoke was explicitly marked software-test-only and is rejected
as scientific qualification input. Nominal BASE/STEER smokes, canonical parity and software fault
fixtures remain software evidence. No all-case/all-grid numerical campaign, repeatability acceptance,
real qualification record, full-suite Verification, new scientific values or canonical edits occurred.

The committed candidate's source identity, focused logs and independent review outcome will be
recorded in the final handoff. The final proposed execution command will name the exact reviewed
source SHA and a fresh results directory; it must not run before separate execution authorization.
