# Task007E-3 — formal synthetic Performance verification

**VERIFIED_AWAITING_ACCEPTANCE. Recommendation B — recommend freeze with documented
nonblocking synthetic limitations.** This verifies the bounded Architecture A research
candidate; it does not freeze or accept the profile, certify hardware, or accept the incomplete
VIS scientific package. Primary APEX retains that decision.

Exact reviewed/tested revision: `e603672b209985f11ed26b6f44d3949ffd5675c5` on `main`.
The worktree was clean and all 819 tracked files remained byte-identical through numerical,
manifest and evidence verification. This delivery adds verification documentation only.
Its containing commit identifies delivery; it is not relabeled as the scientific worker.

[Verification record](task007e/e3/verification.json),
[recommendation](task007e/e3/freeze_recommendation.json), and
[limitations/safeguard register](task007e/e3/remaining_limitations.json) contain exact hashes,
applicability decisions and local log references. The
[proposed manifest](../configs/performance/apex_performance_synthetic_v1.json), schema
`apex-performance-profile/1.0.0`, is unchanged, including `frozen=false`,
`formal_verification_pending=true` and `primary_acceptance_pending=true`. This separate
verification record reports the completed E3 gate without changing reviewed proposal metadata.

## Current full regression

| Scope | Result |
|---|---|
| Full `tests/`, one invocation | **750 passed; 0 failed, errors or skipped** |
| Composition | 716 unit, 31 integration, 3 regression |
| Pytest summary duration | 633.76 s |
| JUnit duration / wrapper wall time | 633.651 s / 634.995 s; distinct timer boundaries |
| VIS cases within that same suite | 30 export + 11 long-report tests; not additional executions |
| Native configuration | Accelerate ceiling 1, set status 0, mode 1; initialized before numerical imports |
| Process observations | One process thread before/after pytest and at every recorded test boundary |

Complete output, all-test durations, JUnit, exit/invocation records and thread observations are
retained in ignored `results/task007e/e3/formal_e603672/`; their SHA256 values are committed in
[verification.json](task007e/e3/verification.json). No full-suite repeat occurred. Established
integration/regression fixtures ran under the explicit E3 authorization; no new scientific
worker, full-lap campaign, measured experiment or counterfactual replay ran.

The suite covers mathematical/model validity, tire parity, NMPC/solver constraints and warm
starts, prediction/latency, TVLQR/buffers, asynchronous chronology/authority, fixed-handoff
compatibility, native threading, diagnostic noninterference and VIS coverage/export behavior.
Module counts and specific E1 safeguard node matches are recorded. The slowest tests were the
existing NMPC oval/circle integrations (72.265/68.128 s including their test fixture timing),
aggressive-reference scaling (58.357 s) and baseline oval/circle at 1 m/s (49.932/43.914 s).
These are verification durations, not solver benchmark results.

Preflight found no measurement guard or competing scientific worker; disk was 7,579,922,432
bytes free and available memory 1,507,016,704 bytes on an 8 GiB host. Ordinary desktop processes
remained visible in the saved inventory. Python 3.12.14, macOS 26.5.1 arm64, NumPy 2.5.3,
SciPy 1.18.1, CasADi 3.8.1, pandas 3.0.6, pytest 9.1.1, psutil 7.2.2 and threadpoolctl 3.7.0
match retained numerical provenance. Process sampling does not establish continuous active
BLAS thread counts; explicit threading-test subprocess configurations remain separate.

## Manifest and implementation identity

The unchanged [E2 validator](../scripts/task007e2/validate_manifest.py) passed freshly:
294 source hashes, 31 evidence references, schema/status/type checks and ten deliberately
corrupted inputs rejected. Its `audited_source_revision` labels the historical E2 preparation
base `835eefb`; E3 separately records the exact current invocation at `e603672`. No numerical
constructor or solver was needed for this audit.

Independent inspection of the worker, implementation and retained configurations confirmed:

| Identity | Verified value/semantics |
|---|---|
| Coordinates/vehicle | Canonical `[vx,vy,r,e_psi,s_abs,e_y]`, `[delta,a_cmd]`, SI; `a_cmd=Fx/m`; synthetic 2 kg vehicle, separate NumPy plant/CasADi prediction, matched smooth combined-grip tires |
| Formulation | N8, dt=0.1 s, four RK4 substeps, H=0.8 s; full eight-stage two-input sequence, 88 decision values |
| Objective | Q=diag(4,4,1,200,200), R=diag(25,1), W=diag(1,0.1); lateral scale 2, other scales/alpha_vy/alpha_r 1, lambda_s=0; no dt scaling of increment penalty |
| Terminal | Existing 100 Hz DARE schedule at 1/2/3 m/s, clamped/interpolated P plus speed-error weight 4; no terminal set or new terminal scaling |
| Solver | Existing explicit IPOPT options and finite/infeasibility checks; shifted primal states/controls/slacks, duplicated last columns, replaced first state, no supplied dual warm start |
| Architecture A | Original predictor to release + rolling estimate; initial 17 ms, last-ten median capped at 300 ms; variable handoff, one pending solve, causal acceptance/reserve/continuity checks |
| Tracking/limits | TVLQR 100 Hz, proportional speed correction kp=1; steering ±0.4 rad, application slew 1 rad/s, acceleration [-3,2] m/s²; existing soft 0.08 m corridor margin and slack semantics |
| Reference/native | Exact synthetic gamma2 Planning package and vehicle/lock hashes; native SINGLE policy; controller properties separated from imposed VIS timing and lap protocol |

The manifest SHA256 remains
`5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
The exact `uv.lock`, `pyproject.toml`, vehicle and all five Planning constituent hashes remain
bound in the manifest and rechecked. No dependency installation or update occurred.

Scientific VIS worker: `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae`; frozen executable ancestor:
`c6990572045e61ee443dc715de9e8c44396e5b41`. Their scoped executable diff is empty.
All 294 retained scientific files and three later offline report/test files match. The offline
report revision is `d55f203aac1a04be598ebce4c38be51a4883e0ba`; E2 adds only its proposed
manifest/validator and documentation to that scientific lineage. The reviewed E3 target is a
profile/documentation descendant, not a newly run scientific worker.

The independently recorded IPOPT plugin/linear-solver build identity remains **unavailable**.
Locked CasADi distribution metadata, explicit options and current numerical passes support
same-host reproducibility; they do not establish independent backend binary identity across
machines or portable timing equivalence. No historical build identity was inferred from current
defaults. Mac timing is not embedded hard-real-time certification.

## Retained scientific evidence

| Authorized VIS long case | Disposition | Complete lap, s | Worker/package |
|---|---|---:|---|
| controlled_A | Two crossings, one complete lap | 31.171900398 | Exit 0; valid |
| controlled_C70 | Two crossings, one complete lap | 31.172038266 | Exit 0; valid |
| measured_A_1 | Two crossings, one complete lap | 31.317755779 | Exit 0; valid |
| measured_C70_1 | Censored at 48.670 s; one crossing | — | Exit 1; incomplete |
| measured_C70_2 | Not executed after stop | — | No worker |
| measured_A_2 | Not executed after stop | — | No worker |

Fresh read-only checks reconciled all four raw histories, recorded RK4 segment continuity and
terminal endpoints, release contexts, chronology, accepted authority and stop reasons. Three
long packages, two recovered parity packages and four small contract fixtures passed the existing
adapter validator. This does not assert Workbench ingestion acceptance.

The two successful A runs retain no boundary crossing, material slack, solver failure, chronology
issue or fallback. Controlled/measured A minimum recorded center clearance is
0.328795505/0.329423745 m and minimum reserve 0.667000/0.565170813 s. Maximum predicted slack
is approximately 9.092e-11 m, below the unchanged 1e-6 m scientific gate. Retained causal forecast
matches are 622/622 and 620/620; native process observations are [1]. Measured A preparation
mean/p95/max is 57.629/70.253/193.324 ms. These remain observations of a particular host history.

All **85** run/lap/sector metric windows recomputed exactly from retained native state exports;
all 73 sector-window boundaries matched recorded coverage. The 85-row lap/sector table and
8-row common-coverage table reproduced byte-for-byte, and both paired comparisons matched.
Cycle/miss CSV counts are 2347/30, matching raw releases and misses. Seven previous numerical
reproduction files remain byte-identical. Eight retained PNGs match recorded hashes, sizes and
valid dimensions; prior rendered review is reused without redraw. Tracking, smoothness and
physical metric definitions remain native-sample/left-held weighting with wrapped headings.

The first rolling-start crossing is partial. Complete-lap times use linear progress inside
recorded RK4 brackets, not new independently sampled crossing events. The controlled difference
of approximately 0.138 ms is below the 5 ms crossing brackets and demonstrates no racing
advantage. Common-time/progress comparisons remain separate from unequal whole-run totals.
Own-reference tracking is not equivalent to racing performance; no visualization interpolation
contributes to scientific extrema or acceptance metrics.

### C70 failure remains represented

The raw audit confirms **485 releases, 455 accepted handoffs, 30 fixed deadline misses**:
22 followed by accepted recovery and eight terminal misses (478–485). Packet 477 was accepted
at 47.870 s and expired at 48.670 s. Packets 478–484 completed late and never activated;
packet 485's completion at scheduled 48.672029625 s lies beyond observed coverage, so actual
completion/discard remains null rather than invented. No late packet authority appeared in
state or applied-command history.

The last sampled reserve event at 48.665 s is approximately 0.005 s; the recorded terminal RK4
endpoint has zero reserve and vx=**5.960492971116675 m/s**. Fallback admission is invalid and
the runner stops `exhausted_outside_baseline_domain` before invoking baseline control.
The earlier VIS prose used the preceding sample's 5.960447591 m/s; the existing E0 erratum
remains applicable and no historical file was rewritten. No omitted recorded boundary crossing,
material slack, solver failure or chronology violation was found. Host-runtime causes of the
late-computation cluster remain hypotheses, not conclusions from timestamps alone.

Raw states, segments, 485 release contexts and analysis remain preserved. The nested NumPy
boolean serialization error occurred afterward during offline export. The final manifest,
packets/planning completion and normal summary are missing. Failed-worker sampled native-thread
observations, forecast-match result and wall/CPU/RSS summary are unavailable and remain null.
The current expected-exception test documents the defect; it does **not** demonstrate a working
export. No repair, replacement or package re-finalization occurred.

This is **nonblocking for the bounded Architecture A candidate**, because its two supporting
long-run pipelines are complete, source/configuration-bound and revalidated. It **blocks a
claim of complete formal VIS scientific-package acceptance**. The failed run supports its
recorded exhaustion/chronology conclusions, not a measured C70 full lap or complete runtime
observation set.

## Fallback and safety classification

The [20-row safeguard applicability register](task007e/e3/remaining_limitations.json) maps
E1 findings to exact source and freshly passed test node IDs. No new controller/test repair or
additional fallback scenario was necessary or executed.

| Class | Disposition |
|---|---|
| A — verified existing behavior | Finite/model/RK4 checks; actuator clamps; LQR/PI component behavior; packet availability/staleness/reserve/continuity checks; failed-preparation isolation; busy/urgent chronology; pending old-command provenance; fixed late-result exclusion. Verification applies to the asserted conditions only. |
| B — nonblocking synthetic limitations | Restricted sampled fallback admission, no guaranteed recovery/availability, incomplete async delayed-fallback coverage, no continuous swept-body safety, no standstill braking or hardware watchdog, narrow evidence coverage and incomplete C70 export. |
| C — concrete correctness blocker | None newly demonstrated by this exact-revision verification. |

Fallback admission and each idle fallback computation require **1 <= vx <= 3 m/s** and the
vehicle center inside the corridor. These are not a verified nonlinear basin of recovery.
Due actuator applications occur before the fallback checks. There is no separate baseline-domain
recheck at every delayed application; held-state/control diagnostics and RK4 guards check physical
propagation, not continuous membership in the baseline admission rectangle. Synchronous
application-state rejection tests do not close asynchronous delayed fallback-transition coverage.
Old pending-command/fallback, busy-tick, domain-edge, late/waiting and fallback telemetry
combinations still require separately reviewed coverage.

Reserve warnings/critical categories do not initiate rescue. A can theoretically exhaust through
sustained delay, preparation/prediction failure or repeated rejection, although this was not
observed in its retained VIS runs. Ordinary completed laps do not validate fallback recovery.
A synthetic loop stop is not hardware emergency braking. Center clearance is not swept-body
collision certification; vehicle dimensions, identification and state/actuator uncertainty are
outside the demonstrated model.

## Applicability, preservation and remaining gates

Historical CX **709** passes at `935e98b` remain evidence for unchanged components; they were not
substituted for this fresh **750**-test run or added to its count. All 168 CX core/fixture hashes
and 18 local verification-log hashes match. Original VIS prerequisite revisions evolved before
c699057; recovered parity, not the failed original pipeline, supplies short-run acceptance.
The two recovered runs each retain 19 exact historical C3 comparison groups and 19 forecast
matches. No forecast or scientific replay was rerun in E3. Existing 30 VIS export and 11 long
report assertions passed freshly inside the full suite; the original historical test-setup and
export failures remain retained. The applicability matrix is embedded in verification.json.

Full raw archives are available locally under ignored `results/`; GitHub retains compact
summaries, inventories, tables and figures. Fresh full-content checks cover 90 long-run files,
54 recovered-parity files, seven original failed-parity files, 40 compact artifacts and the
source/fixture/log inventories (groups overlap and are not summed as unique files).
Before authored documentation, all 819 tracked SHA256 values and 11,617 historical result
size/mtime pairs remained unchanged. Metadata preservation is **not** a whole-archive content
rehash. Final scoped preservation/link/JSON/whitespace checks are recorded with this delivery.
Historical reports, negative results and the proposed profile remain unchanged.

No required bounded E3 numerical/manifest/evidence check remains deferred. What remains is:

- Engineering handoff and **Primary scientific acceptance**, with any manifest status/freeze
  change separately authorized. Recommendation B is advice, not an executed freeze.
- Separate incomplete-export remediation/acceptance and Workbench importer tests before broader
  complete-VIS/interface acceptance; no missing failed-worker observations may be invented.
- The manifest's unchanged `apex-prehardware-gates/1.0.0` HW01–HW07: identify the physical system
  and uncertainty; establish recovery/safe stop; application-time/held-input validity; independent
  watchdog and fault handling; swept-body/stopping-distance safety; target hardware timing/fault
  tests; and missing asynchronous fallback-transition tests. None is implemented by E3.
- Separate authorization for any hardware, unseen-track, Efficiency or other future work.

## Commands and evidence retrieval

Executed once from exact reviewed source, after resource/guard checks:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONHASHSEED=0 PYTHONPATH=scripts:src \
  .venv/bin/python results/task007e/e3/formal_e603672/run_verification.py \
  > results/task007e/e3/formal_e603672/full_suite.log 2>&1
```

The retained hashed wrapper calls `configure_accelerate(1)` before numerical/pytest imports,
then `pytest.main` with `-vv -x tests --durations=0 --durations-min=0` and the recorded
`--junitxml` path; repository pytest options add `-ra` to the effective arguments. Its plugin samples process counts at test boundaries without modifying tests.
A repository-only equivalent uses the documented bootstrap in
[CODEX_TEST_GUIDE.md](CODEX_TEST_GUIDE.md) with those same pytest arguments. Do not repeat the
successful suite merely because this delivery changes documentation.

Fresh manifest and scoped lint commands:

```sh
.venv/bin/python scripts/task007e2/validate_manifest.py \
  --output results/task007e/e3/formal_e603672/manifest_validation.json
.venv/bin/ruff check scripts/task007e2/validate_manifest.py
.venv/bin/ruff format --check scripts/task007e2/validate_manifest.py
git diff --check
```

Read-only audit readers and complete logs are hash-indexed in verification.json. They call the
existing coverage, chronology, adapter-validation and metric helpers on saved records, without
solving or propagating a plant. The [VIS reproduction guide](TASK007D_VIS1L_REPRODUCTION.md)
documents source files and optional offline report reproduction into a fresh directory; its
historical worker commands are not renewed execution authorization. No further project phase
is authorized by this report.
