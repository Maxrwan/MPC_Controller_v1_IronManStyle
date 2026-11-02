# PRE-SID-R0-W1 recovery instructions

Status: **RECOVERY_INCOMPLETE**. Proposed R0: **PROPOSED_NOT_ACCEPTED**.
W1 is documentation-only static provenance work. It demonstrates artifact inspection and
selected byte authentication. It demonstrates neither recovered execution environment,
successful executable reproduction nor new scientific acceptance. All execution commands
below are historical quotations, unexecuted in W1 and subject to separate authorization.
The [inventory](recovery_inventory.json) gives per-file digests, byte sizes, literal locations,
source revisions, evidence roles, accessibility and unresolved provenance.

## 1. Recover immutable Git source

Obtain `Maxrwan/MPC_Controller_v1_IronManStyle` and the complete necessary Git history.
A future recipient can use these static Git commands after acquiring a checkout:

```sh
git cat-file -e 48adbdf64d492592d15e23c917aca71fa58aa8a5^{commit}
git show --no-patch --format='%H %P %T' 48adbdf64d492592d15e23c917aca71fa58aa8a5
git show e603672b209985f11ed26b6f44d3949ffd5675c5:configs/performance/apex_performance_synthetic_v1.json | shasum -a 256
```

The E4 parent must be `ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9`; its tree must be
`63c9165d7b5286240ee5d9e020978cfe0090a1b7`. The manifest hash must be
`5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
Git SHA-1 identities are distinct from ordinary file SHA-256 digests. Resolve the R0 overlay
from the exact documentation commit in its delivery handoff; confirm the sole parent is E4.
No future `main` contents, mutable branch name, Git tag or release designation substitutes
for these full identities. The remote release ref matched E4 in W1; an independent full
fetch/checkout remains a future recipient's action.

Use the following separate source roles. They are not interchangeable:

| Role | Exact Git revision |
|---|---|
| Frozen E4 acceptance/source snapshot | `48adbdf64d492592d15e23c917aca71fa58aa8a5` |
| Original VIS scientific worker | `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae` |
| Frozen executable ancestor | `c6990572045e61ee443dc715de9e8c44396e5b41` |
| Later offline report tools | `d55f203aac1a04be598ebce4c38be51a4883e0ba` |
| E2 manifest / exact E3 tested source | `e603672b209985f11ed26b6f44d3949ffd5675c5` |
| E3 verification delivery | `ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9` |
| W1 documentation overlay | Containing delivery commit; exact SHA in final handoff |
| Future accepted R0 release | Unassigned; no release/tag created |

Authenticate all 294 literal `/source_sha256` entries in
`docs/task007d/vis/vis1l/evidence/controlled_A/summary.json` against both worker and E4
source bytes. The three later report/test files are separately inventoried at their report
revision. Preserve the complete E4 tree, tests, dependency files and configuration; do not
replace source with contents from an older source ZIP. The four original Planning constituents
under `configs/planning/synthetic_grand_prix_v1/` are retained, including the base reference
whose hash is bound by the accepted gamma2 Planning manifest. No fixture regeneration is needed
for static recovery.

## 2. Recover the environment separately

Use the hash-bound `uv.lock` and `pyproject.toml`, not current package defaults. Their hashes are
`8cf85868a456415a898643dbb226d146b0b90e5c98982136cf2abf2465fa16ec` and
`c8ea69a3a486c9794b6cf88ac26566211c6f1bb7b7286d86dbaa36a191353d41` respectively.
The recorded execution environment is Python 3.12.14, macOS 26.5.1 arm64, Clang 22.1.3;
NumPy 2.5.3, SciPy 1.18.1, CasADi 3.8.1, pandas 3.0.6, pytest 9.1.1,
psutil 7.2.2 and threadpoolctl 3.7.0. Additional locked packages are listed in the inventory.
`.python-version` says `3.12`; that is not an exact historical interpreter binary identity.

Historical environment setup documented in [README](../../../README.md) and
[Task007A reproduction](../../TASK007A_REPRODUCTION.md):

```sh
uv sync --locked
```

This installation was **not run in W1**. First resolve the exact target interpreter/OS and
validate selected wheel bytes against their lock SHA-256 and size. The inventory records
compatible-looking lock distribution candidates as **unaccessed**, not downloaded or available.
No exact historical uv version or Hatchling build identity was recovered; Hatchling is a
build-system version range and is not a package pin in this lock. No historical IPOPT/plugin/
linear-solver build fingerprint was recorded. The locked CasADi distribution is not proof
of that independent binary identity. Historical environment equivalence remains unresolved;
any new environment qualification requires review and separate execution authorization.

Native policy is a fresh sequential SINGLE process: remove competing backend variables,
set `VECLIB_MAXIMUM_THREADS=1`, `PYTHONHASHSEED=0` and `PYTHONPATH=scripts:src`, then
call the existing `configure_accelerate(1)` before numerical imports. Preserve deterministic
single-thread operation and inspect actual backend/process observations during any later
authorized execution. Recorded [1] process-thread samples and an empty threadpool inventory
do not establish continuously active BLAS thread counts or embedded timing qualification.
Do not launch tests, analysis or rendering concurrently with any measured worker.

## 3. Recover existing evidence bytes

The original accessible evidence root observed in W1 was
`/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle`.
It is a local observation, not a portable download location. The new documentation worktree
does not contain those ignored result folders. Use the inventory's literal external locations
relative to that original checkout and arrange an authorized transfer to a future independent
recipient. Preserve these groups, including their negative records:

- `results/task007d/vis/vis1r_c699057/`: prerequisite/export/frozen-matrix gates, recovered
  parity A/C70 packages, controlled A/C70, measured A and partial measured C70 histories.
- `results/task007d/vis/vis1_execution/parity_A/`: seven original failed-pipeline records.
- `results/task007e/e3/formal_e603672/`: full suite log/XML, invocation, exit, thread
  observations, historical wrapper and hash-indexed audit/check records.
- Local CX verification logs required by the committed prerequisite provenance.
- The committed E0–E4 records, compact VIS evidence, input configurations, report tables,
  original failed test log/XML and figures. Git compact records do not contain all raw files.

For each transferred external file, recompute ordinary SHA-256 and byte size and compare both
with the inventory and its named historical committed digest record. W1 authenticated 196
external files against committed historical hash bindings without a mismatch; four older
source ZIPs and their four local provenance files are accessible but not fully authenticated
historically. The ZIP SHA-256/size observations are recorded separately from Git identities.
No off-host archive URL, total archive SHA-256/size or independent retrieval test was supplied.
Do not infer availability from a stored path or previous hash. An immutable archive/transfer
and independent retrieval authentication remain R0-G01 prerequisites.

The four successful/failed long-case input inventories each match the original 294-entry
map. Failed C70 source attribution rests on campaign preflight and its preserved input map;
there is no direct final worker-summary SHA. Do not invent capture or binary provenance.

## 4. Apply the accepted configuration without changing it

Read the complete manifest at E2/E4, the per-case preserved input configurations and the
worker setup at its original source revision. The manifest is an audit record and is **not
automatically loaded by the runtime**. Do not invent a `--profile` argument or a new loader.
The historical strict launcher has only its documented case/root interface and fixes its
scientific configuration in existing source.

The accepted profile remains Architecture A, original predictor and variable availability;
N8, dt=0.1 s, H=0.8 s, four RK4 substeps, original Q/R/W/scales, lambda_s=0,
exact gamma2 Planning package, full control sequence, terminal/IPOPT/warm-start policy,
100 Hz TVLQR, original synthetic plant/tires and validity rules. Preserve canonical
`[vx,vy,r,e_psi,s_abs,e_y]`, `[delta,a_cmd]`, SI and dynamic `a_cmd=Fx/m`.
The exact vehicle and all five gamma2 Planning hashes are in the inventory and acceptance
record. Do not replace unknown physical parameters with synthetic ones as measured APEX data.

Historical manifest flags `frozen=false`, `formal_verification_pending=true` and
`primary_acceptance_pending=true` remain unchanged. E3 records historical verification;
E4 separately records Primary acceptance. W1 adds no new acceptance and changes no flags.
The 35/55/45/25 ms replay, imposed 5 ms codriver delay, rolling start, two seam crossings
and 80 s cap are evaluation conditions, not promoted controller defaults.

## 5. Historical execution/validation entry points: quotation only

The following exact worker transcripts come from
[VIS-1L reproduction](../../TASK007D_VIS1L_REPRODUCTION.md):

```sh
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case controlled_A
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case controlled_C70
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case measured_A_1
PYTHONPATH=scripts:src .venv/bin/python scripts/run_task007dvis.py \
  --root results/task007d/vis/vis1r_c699057 --case measured_C70_1
```

These ran historically at the scientific worker revision, in order, with exit codes 0,0,0,1;
the campaign stopped. They are not runnable recovery steps over archived folders. The launcher
refuses an existing case folder, requires its root below `results/task007d/vis`, compares
literal current source hashes with `prerequisites.json` and `export_validation.json`, requires
all prior cases (including parity A/C70) to have successful summaries, and preserves measurement
and disk gates. E2/report additions change the enumerated source set, so launching from E4
or the overlay does not silently recreate the historical worker gate identity.
The later measured cases remain unexecuted. No guards, gates, failed outputs or historical
source maps may be bypassed, fabricated or edited. New roots, prerequisite creation, exact
case scope and budgets require a separately reviewed executable-recovery plan. W1 supplies
no fabricated missing arguments or purported fresh launch command.

Historical E3 full regression command from
[E3 verification](../../TASK007E3_PERFORMANCE_VERIFICATION.md):

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONHASHSEED=0 PYTHONPATH=scripts:src \
  .venv/bin/python results/task007e/e3/formal_e603672/run_verification.py \
  > results/task007e/e3/formal_e603672/full_suite.log 2>&1
```

The original authenticated wrapper is external evidence, not a committed executable source.
It asserts clean exact `e603672b209985f11ed26b6f44d3949ffd5675c5` HEAD, initializes SINGLE,
imports pytest and writes fixed paths. **Do not run it from the E4/R0 checkout or overwrite
its retained outputs.** Its historical effective pytest arguments are `-ra -vv -x tests
--durations=0 --durations-min=0 --junitxml=results/task007e/e3/formal_e603672/full_suite.xml`.
A future verification plan must resolve isolated exact-source checkout, recovered wrapper
placement and fresh log paths before execution; any adapted harness has new provenance.
The 750 passes are historical evidence only; W1 neither ran nor independently revalidated them.

Other existing historical entry points, also unexecuted in W1:

```sh
.venv/bin/python scripts/task007e2/validate_manifest.py \
  --output results/task007e/e3/formal_e603672/manifest_validation.json
```

```sh
XDG_CACHE_HOME=/tmp/apex-vis1l-cache MPLCONFIGDIR=/tmp/apex-vis1l-mpl \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_module("task007dvis.long_report", run_name="__main__")' \
  --source results/task007d/vis/vis1r_c699057 \
  --output results/task007d/vis/vis1r_c699057/new_offline_review
```

The first is historical static manifest validation; it also inspects environment metadata.
The second performs numerical/figure analysis of saved data and is outside W1. Its original
report source revision is separate from the worker. New report outputs require a fresh
nonexistent directory; no case folder may be repaired. Recover historical audit readers as
bytes, inspect their imports and paths, and obtain separate permission before executing them.

## 6. Inspect positive and negative outputs

Static recovery should locate/authenticate, without recomputing scientific metrics:

| Evidence | Historical disposition to retain |
|---|---|
| controlled_A | Complete pipeline, two crossings, one complete lap; 31.1719003976093 s |
| measured_A_1 | Complete pipeline, two crossings, one complete lap; 31.31775577928828 s |
| controlled_C70 | Comparison only; complete pipeline; 31.172038266215967 s |
| measured_C70_1 | Exit 1; censored at 48.670 s; no complete lap; 30 fixed misses, eight terminal |
| measured_C70_2 / measured_A_2 | NOT_EXECUTED_CAMPAIGN_STOP; no outputs expected |
| Original parity A pipeline | Failed history preserved; recovered parity is separate evidence |
| Initial VIS1L focused run | Original test-container failure preserved beside later correction |
| E3 suite | Historical 750 passed, 0 failed/errors/skipped; not rerun in W1 |

Failed C70 stopped `exhausted_outside_baseline_domain` at its recorded terminal state, followed
by the separate nested NumPy-boolean export defect. Its raw/native state, segments, release
contexts, analysis, exit and worker log survive. `summary.json`, `scientific/manifest.json`,
`scientific/packets.json` and `scientific/planning.csv` are absent; no complete package or
measured full lap may be inferred. Direct summary revision, native-thread observations,
forecast-match result and wall/CPU/RSS summary remain unavailable. Scheduled future completion
is not an observed completion. An expected-exception export test is not a working-export pass.

The original rolling-start crossing is partial, and lap crossings retain their RK4 brackets.
The controlled A/C70 difference is below the 5 ms brackets; it does not demonstrate a racing
advantage. Preserve native versus derived metrics, left-held weighting, common versus unequal
whole-run windows, null values, censored records and rejected cases. Do not regenerate missing
scientific evidence or reinterpret record hashes as capture-provenance proof.

## 7. Keep the four recovery/acceptance stages separate

1. **Static artifact recovery:** the W1 inventory authenticates selected existing bytes and
   identifies gaps. All essential static materials must also be independently retrievable
   before RECOVERY_CANDIDATE_COMPLETE is warranted. Current classification is incomplete.
2. **Environment recovery:** exact historical binary provenance remains unresolved; locked
   dependencies and version strings alone do not establish it. No environment was installed.
3. **Executable reproduction:** a separately authorized, isolated plan must run existing
   entry points with honest new provenance and preserved stop gates. W1 demonstrates none.
4. **Scientific acceptance/release:** independent Engineering Review and explicitly authorized
   Verification precede any new Primary R0 acceptance/release decision. W1 is unaccepted.

Existing accepted scope is a bounded synthetic research baseline on the recorded track,
vehicle, latency histories and host conditions. It supplies no guaranteed recovery/availability,
standstill braking, independent watchdog, continuous swept-body/collision safety, unseen-track
generalization or embedded real-time claim. Restricted fallback admission is not a verified
nonlinear recovery basin. No physical readiness, integrated Safety qualification, ROS 2
qualification or measured embedded real-time operation is established. Preserve E3/E4 technical
limitations and HW01–HW07. R0-G01–G05 in the inventory identify consequences and minimum future
actions. Stop at WORK_COMPLETE_PENDING_ENGINEERING_REVIEW.
