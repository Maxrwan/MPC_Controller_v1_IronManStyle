# F-C1 — clock-only execution authorization request

**PROPOSED_NOT_EXECUTED. WORK_COMPLETE_PENDING_REVIEW.** Recorded 26 October 2026.
Primary's human-supplied decision authorizes this **documentation package only**. It accepts
G1 as the basis for this request; it does not authorize the probe. Exact decision date was
not supplied. No clock probe, selected-interpreter identity process, psutil import, timer
sampling, test/collection, numerical import, simulation or benchmark ran in this task.

This package creates exactly the five requested clock_only documents. G1 code/tests,
historical records, dependencies and global handoff/roadmap/decisions stay unchanged;
the task-specific five-path instruction takes precedence over the standing shared-document
update convention. This file is the scoped handoff and the execution request, not approval.

[Protocol and literal argv](clock_only_protocol.json),
[environment and actual resource behavior](clock_only_environment_and_resources.json),
[evidence/interpretation](clock_only_evidence_manifest.json),
[static validation/preservation](clock_only_static_validation.json).

## Exact source pin and future setup

The reviewed executable revision is **c99b9dfdc981cb13ccd2e5ff53af98a3b568f70a**, not the later documentation commit.
All ten G1 runtime/test hashes match that revision and the accepted G1 static record;
the unchanged startup helper hash is recorded too. The recorder API/clock catalog were
inspected by AST without imports. Current Efficiency HEAD was clean at this SHA.
The delivery commit containing this package supplies its own SHA in the final message;
it cannot silently become the execution SHA.

Propose a **new detached worktree**, not a second attachment to research/efficiency:

```sh
git -C /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle worktree add --detach /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle_FC1_c99b9df c99b9dfdc981cb13ccd2e5ff53af98a3b568f70a
```

This command was not run. Its resolved destination is `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle_FC1_c99b9df`. After separate approval,
require it to be absent, create it, verify clean HEAD equals the reviewed SHA, rehash all
listed G1 source/contract/profile bytes, and leave current Efficiency/Safety/CT-1 checkouts
untouched. Reject dirty, wrong-HEAD, symlink or unexpected source paths. Do not reset an
existing checkout or delete/reuse an old evidence directory.

Future setup also creates `/private/tmp/apex-fc1-parent-deps-c99b9df-001` containing **only the 18 individually hashed psutil
package/distribution files** listed in the environment record, copied byte-for-byte
from the inspected psutil 7.2.2 installation. No installer, executable setup, editable
package, .pth, symlink, pyc or dependency resolution. Verify the exact copied file set.
Create a fresh empty `/private/tmp/apex-fc1-pycache-c99b9df-001`. Neither path exists/was created during preparation.

The output parent `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/task007f/profile1` must exist with at least 2 GiB free, while the output
`/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/task007f/profile1/fc1-clock-c99b9df-001` must remain absent for the launcher's exclusive mkdir. Create only the fresh
supervisor envelope `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/task007f/profile1/fc1-clock-c99b9df-001-envelope` beforehand. These are resolved reserved path proposals,
not claims that setup or execution happened. If any reserved destination exists at the
future gate, stop for a revised path/request; no automatic rerun or next numbered slot.

## Complete proposed invocation — DO NOT RUN without narrow approval

Working directory: `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle_FC1_c99b9df`.
Interpreter: `/Users/marwansaber/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12` (base CPython, not the mutable project .venv).

```sh
cd /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle_FC1_c99b9df && \
/usr/bin/env \
  -i \
  PATH=/usr/bin:/bin:/usr/sbin:/sbin \
  LANG=C \
  LC_ALL=C \
  PYTHONNOUSERSITE=1 \
  PYTHONSAFEPATH=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPYCACHEPREFIX=/private/tmp/apex-fc1-pycache-c99b9df-001 \
  PYTHONHASHSEED=0 \
  PYTHONVERBOSE=1 \
  PYTHONPATH=/private/tmp/apex-fc1-parent-deps-c99b9df-001 \
  /Users/marwansaber/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12 \
  -S \
  /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle_FC1_c99b9df/scripts/task007f/profile1/run_phase_a.py \
  --efficiency-instrumentation \
  profile1-v1 \
  --fixture \
  clock_probe \
  --source-root \
  /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle_FC1_c99b9df \
  --reviewed-revision \
  c99b9dfdc981cb13ccd2e5ff53af98a3b568f70a \
  --output \
  /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/task007f/profile1/fc1-clock-c99b9df-001 \
  > /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/task007f/profile1/fc1-clock-c99b9df-001-envelope/parent_console.log 2>&1
```

One reviewed parent invocation may spawn one clock child via its internal --_worker flag.
Do not pass that flag yourself. No --clock-allowance is supplied, no numerical fixture,
no parallel execution, retry or continuation. Setup, identity/origin/process checks and
the literal one-shot command all require the separate execution/setup approval.

## Environment and module separation

Static file inspection observes macOS 26.5.1 build 25F80, Darwin 25.5.0, arm64; the
installed base header says CPython 3.12.14. This is not a runtime version/origin check.
The executable SHA256 is `2d96eb826dc74db4fcd5da6dde045a6fa145e292e07e69d1bdd1a19fa90ffc22`; libpython/header/BUILD and all psutil Python/native
files/metadata are pinned in the environment record. psutil 7.2.2 is read from METADATA,
not imported. Current shared .venv has an editable APEX .pth and startup hooks; using it
would expose a mutable source path. It is only the source of vetted dependency file
copies, never the interpreter or import path in the proposed command.

Before an approved attempt, reverify OS/architecture, interpreter version/prefix/origins,
source/contract/profile hashes, dependency copies and base site startup files. Drift
requires revised approval, not silent substitution. The explicit env -i removes inherited
virtualenv/Python/DYLD contamination; -S disables parent site processing. The launcher
adds pinned scripts and the parent imports only the isolated copied psutil plus standard
library and pinned threading_study.config. The latter imports ctypes but environment(1)
only sets environment values: it does not call Accelerate control APIs.

The child is started using sys.executable **without inheriting -S**. It therefore needs
an independently inspected clean base site prefix, PYTHONNOUSERSITE=1, PYTHONSAFEPATH=1,
empty cache-prefix isolation and no startup customizations. Its PYTHONPATH is overwritten
by G1 to the pinned scripts:src:scripts. It does not inherit copied psutil or the shared
venv path. Worker routing returns to _clock_worker before configure_accelerate, numerical
construction, threadpoolctl, NumPy/SciPy/CasADi/APEX control/simulation imports.

Retain proposed PYTHONVERBOSE origin trails in worker.log and parent_console.log, then
audit every loaded origin: base stdlib/frozen builtins, pinned recorder/launcher/scripts,
and parent-only copied psutil. Reject any current mutable/Safety/CT-1 source or numerical
backend import. This trace is additional disclosed observation cost, not invisible or
zero overhead. G1 has no structured final module-origin manifest/import sandbox: verbose
logs and path/hash/startup preflight support review, not an infallibility guarantee. If
hard origin enforcement is required, stop and request a separately authorized source
correction with a newly reviewed execution SHA. No launcher correction is made here.

The child also invokes local Git subprocesses for source checks/diff identity. “Stdlib-only
child” excludes third-party Python dependencies, not the pinned recorder or external Git.
It does not mean every dynamic native library/thread is controlled. No BLAS API is called
on this path; VECLIB_MAXIMUM_THREADS=1 and one worker are not native-thread-control proof.

## Population and interpretation

Intended: one auxiliary clock call, 1000 clock_empty spans then 1000 clock_parent/clock_child
pairs, **3000 span occurrences**. If fully reached: 6002 wall and 6002 process-CPU endpoints,
12004 clock reads total, with wall before CPU in every pair. Child occurrence is 1 under
each distinct parent; standalone/parent occurrences are each 1..1000. These are static
count derivations, not observed results. Raw endpoints, nulls, faults and signed residuals
must be retained. Default caps (64 calls/8192 spans/depth 8/16 MiB sidecar) accommodate the
intended slot count arithmetically; this is not a measured memory/export-success claim.

Clock metadata reports nominal implementation/resolution only. Inclusive/exclusive
reconciliation retains signed differences and subtracts complete immediate children;
partial coverage is unknown. No minimum duration, constant correction or allowance is
invented. With no allowance, reconciliation normally stays unresolved and a fault-free
sealed observer remains **incomplete**. The clock branch can return zero nevertheless;
this means neither observer scientific validity nor numerical-controller acceptance.
raw_not_returned=true and null simulated fields are intentional: no physical population
exists. Host interruption/missing tail is incomplete, never proof of physical safe stopping.

## Actual supervision and unresolved guarantees

The proposal is one invocation, one exclusive output, a **30-second sampled child interval**,
1 GiB observed direct-child RSS, 1 GiB observed logical output, 2 GiB initially free and
1 GiB remaining. The monitor performs work then sleeps 0.1 s, so samples are approximately
100 ms plus inspection/scheduler cost. No execution measurements were collected here.

The timer starts before log open/Popen but after parent imports/guards/setup. On a sampled
limit exceedance, parent sends SIGTERM to the direct child, waits up to two seconds, then
SIGKILL and an unbounded wait. finally can also terminate/wait/kill. Grace, scheduling,
export and cleanup can extend total wall time beyond 30 seconds; **neither a hard 30-second
nor 32-second total bound is provided**. There is no new session/process-group signaling,
descendant aggregation, hard kernel memory limit, parent RSS limit or total-parent deadline.
Git helper descendants are possible. These gaps require explicit review; request separately
authorized corrections if stronger guarantees are mandatory.

RSS is sampled and fast peaks can be missed; a short child can finish with zero samples.
Output uses recursive logical st_size under the worker directory, can transiently double
count hard links, and excludes envelope logs/dependency/worktree setup. Disk free is the
output volume's sampled statvfs availability, not a reserved quota. Poll completion stops
monitoring before final parent_exit/cleanup writes. Parent/descendants and post-child or
outside-directory growth are not bounded by those sampled limits. Non-NoSuchProcess
monitor/storage errors may escape and omit parent_exit. Preserve all logs regardless.

Automatic guards scan only the pinned launcher's ROOT/results and seven known workload
substrings, excluding self/immediate parent. They do not scan all other worktrees or
atomically reserve the machine, and process checks are not repeated during the monitor.
Before the attempt, the authorized supervisor must inspect active computational processes
and original/pinned/Safety/CT-1 result guards, establish an exclusive reservation, record
owner PID plus command/start identity, and stop on ambiguity. Absence was **not verified
live** by this documentation task and must be re-established at execution time.

Parent publishes MEASURED_ACTIVE owner_pid/fixture in the fresh output; the child checks
it against its parent PID. Normal finally removes only the owner-matching readable guard
after direct child cleanup. Startup errors before try, kill, corrupt guard or storage
failure can leave guard/partials behind. Do not delete or overwrite unknown guards.
External supervisory reservation/logging is required; current code alone does not provide
global isolation or a hard resource guarantee. No broader ten-minute G2 budget is enforced.

## Evidence, incomplete outcomes and review

The evidence manifest enumerates clock_metadata.json, raw preparation_sidecar.json (or
retained .partial), sidecar_export.json, clock_probe_counts.json, parent_exit.json,
worker.log and residual guards/other partials. The supervisor envelope adds actual identity,
source/dependency hashes, guard/process reservation, parent origin log and a post-attempt
review. Neither these future evidence files nor their measurements exist from this task.
The clock route does not emit the numerical worker's raw/provenance/allowance files or its
sidecar_export_failure handler. An early exception can leave no count/export/failure record;
absence is incomplete evidence. Verify actual artifacts and hashes, never assume a manifest
entry was produced. Preserve every unsuccessful attempt and its only output directory.

Mechanics review requires identity/origin/resource evidence, actual count/tree/sequence
checks, raw integer/nondecreasing endpoints and available halves, no fault/open tail for a
full mechanics candidate, independent signed accounting and export/file-hash checks.
Unknown/missing data, timeout, overflow, clock error, import contamination or export failure
blocks clean-mechanics status. Coarse equal clock values/zero intervals remain raw; no
clock tolerance is supplied. No failed attempt is discarded, repaired into success or
replaced by a favorable run. No raw clock observation is called NMPC profiling, speedup,
full software latency or a physical stopping result.

**Narrow decision requested, not yet granted:** approve the stated setup/identity/import
checks and exactly this one pinned clock-only invocation, accepting the explicitly sampled
resource/direct-child/origin-audit limitations, or require separately authorized corrections
and review their new execution SHA first. After the single attempt, stop for Engineering
and Primary review of all raw/partial results. Do not derive/approve an allowance or unlock
the other 43 proposed G2 workers. Later G2 must reconcile worker identities/order, aggregate
ten-minute budget, B0/B1/B2 parity, separate observer costs, deadlines/readiness and full
warm-state limitations. Phase B remains independently blocked; no reconstruction or tuning.

## Preservation and delivery

Static AST/hash/schema/argument/reference/Git audits only. All 857 original tracked files
remain byte-identical; original 11,646 results files retain size/mtime metadata (not a full
raw rehash or backup). The exact five created paths are the only repository changes.
Main/release remain E4 48adbdf64d492592d15e23c917aca71fa58aa8a5; annotated tag object 76d9eaa65af02efb0263916adc75d5247a0e778f
still peels to E4; manifest SHA256 5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf
matches. Remote freeze rules remain active without bypass actors. Safety/CT-1 stay independent
at observed 6392092d68c1e2dd75120fbd87c32714e530e44e / 3898704102e7570bcaff9b1654b7b345db1f9b6f;
no checkout, ref, environment, launcher or test was changed by this task. No main merge.

**NO CLOCK PROBE, TESTS, PROFILING OR BENCHMARKS EXECUTED.**
Exit: **WORK_COMPLETE_PENDING_REVIEW**, awaiting a separate narrow execution decision.
