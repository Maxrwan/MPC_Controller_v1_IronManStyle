# APEX Workbench V0.1 Engineering Review

**Decision: FAIL. Status: ENGINEERING_REVIEW_COMPLETE_PENDING_DECISION.**
Reviewed revision: **`a0b4a98b14f53469735ca4dd9f7a93a7b0651860`** on
`codex/apex-workbench-v0-1`. This is an Engineering Review recommendation, not formal
Verification, Primary acceptance or permission to begin V0.2.

The scientific adapters are legitimate, but supervisor loss breaks execution ownership and
leaves unreconciled evidence. Concurrent publication, comparison eligibility and artifact
integrity have additional reproduced defects. Correct these in a separately authorized task
and review the new revision before proceeding to Verification.

## Revision, scope and review authority

The original working tree was clean at `a8e96ee95b99088bafb8ef2cb7a4d13f76c7905f`.
Relative to the requested pin, that descendant only adds `Launch_APEX_Workbench.command` and
changes the README/handoff. The launcher is **outside this review**. All implementation,
tests, requirements and canonical scientific source match the pin. The original pinned
README/handoff were read from Git/an isolated detached local clone; all eight entries in the
delivery's tool-source manifest match. Tests confirmed imports from the pinned clone, not
from the later working checkout. The clone has an untracked tooling-only .venv symlink to the reused environment; its tracked
contents match the pin. No dependency installation or implementation modification occurred.

Inspected AGENTS, verification workflow/test guide, handoff, ADR-169, roadmap/deferral records,
all Workbench source/tests/docs, Task004/005 entry points, dynamic/linear-tire/LQR specifications,
canonical state/coordinates/track sampling, baseline diagnostics and runner/metrics. Review
artifacts are the only repository additions; the handoff is prepended without rewriting history.

This is a fresh source audit and bounded adversarial review in the same Codex chat that authored
the implementation. It is **not personnel-independent Secondary approval**. Governance assigns
the subsequent decision to the user/Engineering Orchestrator and Primary; no additional local
reviewer/branch requirement was found. That external decision remains outstanding.

## Findings and smallest required corrections

| ID | Priority | Finding | Required disposition |
|---|---|---|---|
| R1 | P1, blocking | Supervisor death releases the lock while the worker survives; cancellation/status recovery is absent | Bind execution ownership to worker lifetime and reconcile abnormal exits before accepting another run |
| R2 | P2 | A retained request becomes visible before status publication | Publish a complete initial record before listing it; tolerate incomplete records |
| R3 | P2 | New note files are visible before JSON is complete | Atomically publish exclusive note versions; tolerate interrupted writes |
| R4 | P2 | Comparison eligibility checks only adapter and completed status | Validate a scientific compatibility fingerprint or label the overlay illustrative/ineligible |
| R5 | P2 | Manifest failure follows publication of a clean completed status | Keep scientific outcome and evidence validity separate; publish final evidence state transactionally |
| R6 | P2 | Retained CSVs are plotted without checking their recorded hashes | Verify required artifacts on ingestion and visibly reject/mark altered or unverified records |

**R1 — reproduced with the real worker.** After the supervisor received SIGKILL, its worker
remained alive, the execution lock was available, a second request reached Popen, and a
cancellation marker did not stop the orphan. The second Popen was intercepted, so a second
scientific worker did not execute. The original record remained `running` without a manifest.
The orphan was manually terminated by the review harness. CPU/per-file kernel limits still
inherit; wall/RSS/output supervision is lost by code inspection. The probe did not wait beyond
60 s or claim unlimited CPU. Preserve an explicit interrupted/unknown outcome and verified
process ownership; never convert an orphan or stale record to successful completion.
Sources: [parent lock/launch](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/jobs.py#L137-L175),
[separate worker session and supervision](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/jobs.py#L234-L274).

**R2 — reproduced at the publication boundary.** A harness scheduling barrier after request
publication but before initial status publication caused a second AppTest session to raise
FileNotFoundError. The writer completed once released. This can also leave a permanently
unreadable record if interrupted in that window. Sources:
[publication order](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/jobs.py#L163-L164),
[unguarded status read](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/app.py#L142-L167).

**R3 — reproduced with two interleaved readers/writers.** The note filename existed while its
writer was paused before json.dump. The same read_json API used by the UI raised JSONDecodeError;
the note was valid after the writer finished. Exclusive filenames preserve previous notes but
do not provide atomic visibility. Prediction bytes remained unchanged. Sources:
[note publication](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/jobs.py#L195-L203),
[latest-note reader](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/app.py#L243-L246).

**R4 — reproduced with clearly labeled review-only fixtures.** Records with the same adapter
but conflicting track, source revision/hash, vehicle YAML, controller and timing metadata produced
three overlay charts without a warning. The config panel exposes the track difference; the other
provenance differences are not compared. These fixtures make no scientific run claim. Source:
[eligibility branch](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/app.py#L106-L130).

**R5 — reproduced with an injected hash-read error.** A tiny real worker completed, then the
harness raised OSError during final manifest construction. The supervisor propagated the error,
but status remained `completed`, error null, with no artifacts.json. This does not invalidate
the worker's numerical result; it leaves evidence validity unreported. Source:
[terminal publication before hashing](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/jobs.py#L282-L308).

**R6 — reproduced on disposable copied telemetry.** After a fixture's states.csv hash was
recorded, its first vx sample was changed to 123.456. Its checksum differed, yet that value
was plotted and comparison still displayed no integrity warning. Historical outputs were
not edited. Source:
[CSV ingestion](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/a0b4a98b14f53469735ca4dd9f7a93a7b0651860/tools/apex_workbench/plots.py#L9-L11).

## Verified behavior and scientific limits

- Dynamic execution calls original Task004 main(); LQR execution calls original Task005 run_case().
  No dynamics, tire, integration, controller or solver equations are duplicated in the adapter.
- Duration/dt reach the dynamic CLI. Duration, track, initial/reference speed, ey and epsi reach
  the LQR function. Strict keys, finite numbers, domain/UI bounds and LQR tick multiples are
  enforced; unsupported parameters are not editable. Fixed vehicle/controller/tire composition
  is explicit. The UI safeguards are not physical validity envelopes.
- Canonical SI channels/order, dynamic a_cmd=Fx/m, held-input timing, original LQR references and
  Frenet conversion are preserved. XY is derived through the canonical API; plots read CSVs.
- Both original-entry-point parity checks passed again, including states/summary and LQR controls.
  These short deterministic cases establish adapter consistency, not integration convergence,
  nonlinear stability, linear-tire physical validity, full-lap completion or vehicle safety.
- Normal lock/cancellation/timeout/failure retention, exclusive output and the real UI run test
  passed. Ordinary invalid workers retain logs/error states. Exceptional recovery has the defects above.
- Prediction/configuration are retained with the request; normal observation/explanation saves
  create separate exclusive versions. Synthetic/perfect-state assumptions, derived XY and unavailable
  solver/latency metrics are labeled. No generated learner explanation is supplied. Process
  completion is explicitly distinguished from scientific acceptance.

## Comparison validity

| Classification | Minimum interpretation |
|---|---|
| Directly comparable | Matching scientific source/composition, track geometry, vehicle/controller definitions, timing assumptions, schema/units and relevant environment; intentional varied parameters identified; data integrity checked and outcome coverage explicit |
| Qualitatively illustrative only | Different tracks, multiple changed factors, or known compatible revisions without a controlled equivalence argument; display those differences and make no causal ranking |
| Invalid for scientific comparison | Unknown/incompatible coordinate or unit contracts, unverified/corrupt artifacts, unreported source/model/timing changes, or missing outcome/coverage provenance |

Use a small compatibility fingerprint over scientific source hashes, model/tire/vehicle/controller
composition, track geometry, timing and schema/units, plus the explicitly varied inputs. A
documentation-only Git revision difference need not forbid comparison when scientific identity
matches. Preserve failed/censored/negative records with their labels; do not replace them with
favorable runs. No expanded comparison system was implemented.

## Evidence, uncertainty and recommendation

**Fresh bounded tests: 85 passed** (17 Workbench + 68 selected Frenet/baseline/runner tests),
zero failures/skips, at the exact pin. All five review probes completed and reproduced the
six findings; their zero exit codes mean the expected defects were observed, not that the
implementation passed those scenarios. See [reproduction](REPRODUCTION.md),
[machine-readable evidence](evidence.json) and [review-only harness](review_probes.py).
Full local logs/fixtures are under `results/apex_workbench_review_20261027/`.

Environment: Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.6, matplotlib 3.11.2,
Streamlit 1.66.1, Plotly 6.9.0, psutil 7.2.2, threadpoolctl 3.7.0, pytest 9.1.1; existing
macOS Accelerate SINGLE bootstrap. This is functional evidence, not a latency benchmark.

Preservation checks retain every original tracked file outside the authorized handoff, all
11,775 original result-file size/mtime records, and the pinned clone's tracked source. This is
not a full historical-result content rehash or backup.

Full integration/regression, CPU/file/RSS/output exhaustion stress, broader input/convergence
coverage, cross-platform behavior and external reviewer independence remain unverified. No NMPC,
async planner, measured-latency, VIS-2, Efficiency, hardware work or feature correction ran.

**Do not accept V0.1 or advance to V0.2 on this result.** Authorize a bounded correction task
for R1–R6, preserve this failed review/evidence, review the corrected SHA, then explicitly
select the formal Verification gate and its complete applicable acceptance/regression set.
The external Engineering/Primary decision remains required.
