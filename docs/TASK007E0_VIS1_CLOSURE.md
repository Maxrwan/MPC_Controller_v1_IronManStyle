# Task007E-0 — VIS-1 scientific closure and verification applicability

**WORK_COMPLETE_PENDING_REVIEW — documentation/evidence audit, 2026-10-16.** Primary APEX
has directed closure of the VIS-1 experimental campaign with its scientific stop preserved.
This closes experimental execution; it neither certifies the evidence nor accepts/freezes
APEX Performance. Architecture A remains the intended **synthetic** Performance configuration.
C70 remains an experimental candidate for future Efficiency research, without authorization
to optimize or investigate it here. Production defaults are unchanged.

Audit baseline: `d55f203aac1a04be598ebce4c38be51a4883e0ba`. Only this report, the two
[audit records](task007e/e0/evidence_matrix.json), [applicability matrix](task007e/e0/verification_applicability.json),
handoff prepend and ADR-163 are delivered. No tests, forecasts, solver/physical workers,
integrator calls, new exports, figure rendering or experimental reruns were executed.

## Complete case disposition

| Authorized long case | Worker / pipeline | Physical end (s) | Crossings / complete laps | Complete-lap time (s) |
|---|---|---:|---:|---:|
| controlled_A | exit 0; complete; adapter valid | 62.235 | 2 / 1 | 31.171900 |
| controlled_C70 | exit 0; complete; adapter valid | 62.075 | 2 / 1 | 31.172038 |
| measured_A_1 | exit 0; complete; adapter valid | 62.285 | 2 / 1 | 31.317756 |
| measured_C70_1 | exit 1; scientific stop; incomplete export | 48.670 | 1 / 0 | **not observed** |
| measured_C70_2 | not executed after campaign stop | — | — | — |
| measured_A_2 | not executed after campaign stop | — | — | — |

These statuses reconcile with original raw histories, recorded RK4 endpoints, exit records and
the committed [VIS-1L summary](task007d/vis/vis1l/summary.json). No failed worker is counted as
a successful pipeline. The rolling start is at s_abs=1 m on the 154.76345492731022 m circuit;
the first seam crossing is an initial partial traversal. Only the next traversal is a full lap.
Crossing times are linear-progress reconstructions inside recorded integration brackets.
The controlled C70-minus-A difference, **0.000137869 s**, is below the 5 ms crossing brackets
and establishes no performance advantage.

The [85 retained run/lap/sector rows](task007d/vis/vis1l/lap_sector_metrics.csv) include partials.
Measured C70's second-straight observation ends after 1.471642 s at exhaustion; its later
technical and return sectors are unobserved. Neither that sector nor the lap is completed.
Common-time comparisons remain bounded by 62.075 s for the controlled pair and 48.670 s for
the measured pair. On the controlled common-time window, applied steering total variation
is 17.389398 rad for A and 13.735874 rad for C70, as retained in the
[common-coverage table](task007d/vis/vis1l/common_coverage_metrics.csv). This is a control-quality
observation, not a demonstrated racing gain or a measured reliability conclusion.

## Reconstructed C70 exhaustion

The retained measured C70 history contains **485 runtime releases, 455 accepted handoffs,
30 missed fixed deadlines, 22 misses followed by later accepted recovery and eight terminal
misses without observed replacement**. There is one planner-busy miss and no codriver-busy tick.
These are distinct event counts. Startup plan 0 is separate.

Packet 477 released at 47.800 s, became ready at 47.868902625 s and was accepted at 47.870 s.
Its nominal horizon expired at **48.670 s**. Packets 478–485 missed deadlines 47.970,
48.070, …, 48.670 s. Packets 478–484 completed and were discarded after their deadlines;
none appears in accepted authority, physical-state packet IDs or control requests.
TVLQR and physical propagation continued using packet 477 until exhaustion.

Packet 485's host preparation duration is 72.029625 ms, giving a **scheduled** completion
48.672029625 s, beyond observed coverage. Its actual readiness/discard remain null and
`completed=false`. The analysis's `resolved=485, censored=0` concerns fixed-deadline outcomes;
one physical completion is censored. All 30 misses and their recovery/null fields remain in
[misses.csv](task007d/vis/vis1l/misses.csv); exact terminal cycles are also in the new evidence matrix.

The final reserve-event sample at 48.665 s is approximately 0.005 s. The **recorded terminal
RK4 endpoint** at 48.670 s has zero reserve. This endpoint is native evidence, not display
interpolation. The historical event-based minimum is retained without treating it as reserve
remaining at termination.

**Reporting erratum, without rewriting history:** [VIS-1L prose](TASK007D_VIS1L_RESULTS.md)
labels 5.960447591 m/s as the endpoint speed; that value belongs to the 48.665 s runtime row.
The actual 48.670 s endpoint in the saved segments/native CSV is **5.960492971 m/s**.
Both exceed the existing exhaustion fallback check's 1–3 m/s domain, which also requires
corridor containment ([existing implementation](../src/apex/simulation/asynchronous.py)).
The recorded fallback event has `valid_domain=false`; termination is
`exhausted_outside_baseline_domain`, not operation of a valid baseline fallback.
The timestamp correction changes no data, gate or scientific conclusion.

No omitted boundary crossing, material slack, solver failure or chronology violation was found
in the recorded data. All four raw histories have zero such counts, no reported model-domain
failure, and maximum predicted slack around 9.092e-11 m, below the unchanged 1e-6 m gate.
Measured C70 minimum native center clearance is 0.329202 m. These observations do not waive
reserve exhaustion or certify continuous swept-body/hardware safety.

Temporal clustering of preparation tails explains the recorded lack of timely replacements;
it does **not** identify the underlying host-runtime cause. No claim about thermal state,
OS scheduling, CPU contention or solver pathology is established by this audit.

## Export failure is a separate defect

The unchanged worker saves raw.json, segments.json, all 485 release contexts and analysis.json
before exporting. The [retained traceback](task007d/vis/vis1l/evidence/measured_C70_1/worker.log)
then records a nested NumPy boolean failing the CSV JSON-cell `json.dumps` path. The earlier
standalone JSON correction does not cover that path. The existing expected-exception test
documents the defect; it is not a passing failed-package export gate.

The error occurred **after physical exhaustion** and is not its cause. The final summary,
manifest, packets/planning completion and complete event stream are absent. Available native
CSV rows match raw states and the terminal segment exactly, but the partial directory is
not a valid apex-run package. No package was repaired, finalized or relabeled here.

The failed worker's exact forecast-match count, actual sampled thread-count list and wall/CPU/RSS
summary are unavailable. Its configuration requests SINGLE; no actual observation is borrowed
from another worker. Successful workers retain process-count observations [1] and exact forecast
counts 622/622, 620/620 and 620/620. Workbench ingestion remains separately pending even for
the three adapter-valid packages. These gaps limit completeness, not the directly retained
physical-stop/authority reconstruction; acceptance of those limitations requires review.

## Source, configuration and evidence identity

| Evidence boundary | Exact revision / applicability |
|---|---|
| CX scientific revision formally tested | `935e98b7af6c2fda8458551f1fbcbddb3bf8932d` |
| CX verification documentation | `f072052cd4481df6d987deb6d8d721f1b1b99cb2` |
| Frozen VIS executable and recovery tests/workers | `c6990572045e61ee443dc715de9e8c44396e5b41` |
| VIS-1L scientific execution and in-worker export | `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae` |
| Later offline long-report/figure tools and delivery | `d55f203aac1a04be598ebce4c38be51a4883e0ba` |

Fresh content checks match the existing **168-path CX core/fixture manifest, 294-path VIS
inventory, three later report/test hashes, five Planning artifacts and vehicle hash**.
Frozen executable→worker has no executable difference. CX→VIS has only 16 added VIS
adapter/report/test files; all earlier controller, solver, predictor, scheduler, vehicle/tire,
integration, configuration, dependency and test files are unchanged. Successful summaries
directly record the worker SHA. The failed worker's attribution instead rests on campaign
preflight and its saved input/source inventory; no separate summary SHA survived.

The [preflight](task007d/vis/vis1l/evidence/vis1l_preflight.json) and per-case input configurations
preserve synthetic_grand_prix_v1/gamma2, N8/dt0.1/H0.8, Q=diag(4,4,1,200,200), R=diag(25,1),
W=diag(1,0.1), lambda_s=0, alpha_vy=alpha_r=1, predictor A, unchanged TVLQR100 Hz, tires,
IPOPT/warm starts and 0.08 m synthetic margin. Controlled readiness repeats 35/55/45/25 ms;
measured readiness uses complete host preparation duration. All impose 5 ms codriver delay.
A retains variable targets; C70 uses 70 ms. Consequently this is not a scheduler-only comparison.

All **2,347** runtime preparation rows and outliers remain. Measured A has 620 samples,
mean/p95/max 57.629/70.253/193.324 ms; measured C70 has 485,
58.812/70.371/117.222 ms. Startup is separate. Controlled host costs are descriptive and do
not determine their imposed readiness. One correlated, censored measured pair does not
establish a deadline reliability distribution or embedded hard-real-time performance.

GitHub retains compact tables, eight figures, configurations, three summaries, failure evidence
and manifests. Full raw/segments/release histories and scientific packages remain **ignored
local evidence** under `results/task007d/vis/vis1r_c699057/`. Original failed parity remains
under `results/task007d/vis/vis1_execution/parity_A/`. Compact GitHub evidence cannot substitute
for these archives. Keep them before any future cleanup.

## Verification applicability and checks actually performed

The [machine-readable matrix](task007e/e0/verification_applicability.json) separates eight groups,
original revisions, logs, dependency identity, reuse decisions and outstanding checks:

- **CX formal:** 709 prior passes, 597.59 s. The 226 focused cases are a subset. Applicable to
  unchanged components; predates all VIS additions and is not formal VIS verification.
- **VIS prerequisites/recovery:** 410 initial passes contained 384 unaffected cases and 26
  evolving adapter cases. Recovery ran 30 source-bound adapter tests; 384 inherited + 30 gives
  414 applicable prerequisites. Both complete 2 s workers retain 19 exact C3 groups and 19
  forecast matches each. Original incomplete parity is not retroactively accepted.
- **VIS-1L:** 41 unique final focused passes. Initial invocation had 40 passes and one new-test
  container-setup failure; the 11 report cases passed after the documented dtype correction.
  The recheck and 30 prior adapter cases overlap. No cumulative distinct-test total is claimed.

E0 performed read-only content checks of **90 long-run files, 54 recovery-parity files,
seven original failed-parity files, 40 compact artifacts and 18 CX log/artifact files**;
these sets are not claimed disjoint. It parsed historical JUnit/log hashes and test overlap,
revalidated three complete long packages, two parity packages and four contract fixtures,
checked four native traces/segment continuity/chronologies, recomputed lap coverage and miss
recovery, and reconciled CSV counts and preparation extrema. Seven existing numerical
reproduction copies remain byte-identical; all eight figure hashes match. Nothing was redrawn.

Two local audit-reader setup failures were retained: treating variable-mode deadline misses
as zero instead of null, and assuming a timing object where measured mode records null.
Only the disposable reader was corrected. These are not experiment/test regressions and did
not change repository code, assertions or evidence. Logs/scripts are under
`results/task007e/e0/d55f203_audit/`, with hashes in the audit matrix.

Environment: macOS26.5.1 arm64, Python3.12.14, NumPy2.5.3, SciPy1.18.1, CasADi3.8.1,
pytest9.1.1, pandas3.0.6. Recorded numerical versions match prior VIS prerequisites.
Measurement guards were absent before offline checks. Documentation/JSON/reference checks,
`git diff --check`, source scope and preservation checks complete this documentation-only WORK.
No pytest or numerical regression was run. Historical numerical passes are inherited, not new.

Before/after preservation checks cover all 807 initially tracked files (only handoff prepend
and decision append authorized) and 11,591 preexisting result-file size/mtime pairs. The latter
is **metadata preservation**, not independent full-content hashing of the whole archive.
Specific content rehashes are listed above. Historical reports and standalone Primary documents
are untouched; this report explicitly records the speed erratum instead of editing old evidence.

## Remaining obligations and next review boundary

The measured A/C70 comparison is incomplete: one measured A lap, one censored C70 history and
two unexecuted cases. One circuit establishes no unseen-track generalization. The synthetic
vehicle is not physically identified hardware, center clearance is not swept-body safety,
and the existing shared fallback has a restricted validity domain.

Separately authorized **formal VIS/Performance verification** must target an exact reviewed
revision, run its required current regression and acceptance checks, audit mathematical,
chronology, physical-validity and analysis/export coverage, and disposition the failed package
and missing observations explicitly. CX's full-suite pass does not cover newer VIS code.
An exporter repair would require separate review, source-bound tests and new artifact provenance;
it cannot recover unrecorded runtime observations by assumption.

Recommended **007E-1 boundary**, without starting it: audit the existing shared fallback's
documented/implemented entry, validity and termination conditions against retained evidence,
identify unsupported operating regions and required acceptance tests, and return findings for
review. Do not expand its domain, redesign it, retune controllers or launch racing runs under
that audit recommendation. E-2 must separately bind the exact intended Performance profile,
source/dependencies, fixture/vehicle, constraints, timing/native policy and validity/claim limits.
E-3 formal verification and Primary acceptance remain subsequent gates.

Hardware/safety gates, Efficiency research and Workbench ingestion remain independent stages.
No Performance freeze, unseen-track run, new controller feature or next-stage execution follows
from VIS-1 closure. **Stop here for Engineering Review.**
