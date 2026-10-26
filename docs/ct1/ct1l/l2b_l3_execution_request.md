# CT-1L L2B: separate L3 execution-authorization request

**DRAFT — NO EXECUTION AUTHORIZED. WORK_COMPLETE_PENDING_REVIEW.**

This request targets the exact Git commit containing this L2B package, whose literal
SHA is supplied in the final delivery handoff. Resolve it with
`git log -1 --format=%H -- docs/ct1/ct1l/l2b_l3_execution_request.md` and require
that it equals that reviewed delivery SHA and the future Primary grant's
`implementation_sha`. This follows the repository's no-circular-self-SHA rule;
a newer HEAD/descendant is not implicitly approved.

The machine-readable request is `l2b_l3_execution_plan.json`, including exact
source/evidence hashes, twelve unchanged candidate IDs, thirteen prerequisite
files and every AST-declared test-node selector (all parametrizations), locked
dependency identities, native controls, output ownership and failure policy.
`l2b_workload_plan.json` fixes the complete interval/normalization panel and workload
accounting before any numerical result. `l2b_failure_and_evidence_contract.json`
defines local/global stops and structured failure/missing-coverage events.

Future command, **only after separate Primary L3 authorization**:

```sh
CT1_ROOT=/Users/marwansaber/.codex/worktrees/control-theory-ct1/MPC_Controller_v1_IronManStyle
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$CT1_ROOT/scripts:$CT1_ROOT/src" \
  /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/.venv/bin/python \
  -B -m ct1.cli run \
  --repo-root "$CT1_ROOT" \
  --archive-root /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle \
  --assignment-root "$CT1_ROOT/docs/ct1/ct1l" \
  --grant <absolute-path-to-separately-approved-L3-grant.json> \
  --output "$CT1_ROOT/results/ct1/ct1l/<exact-reviewed-L2B-SHA>/<unique-run-id>"
```

Angle-bracket grant/SHA/run-id placeholders must be replaced by the separate
Primary decision; no executable grant file is created here. Do not execute this
request or the worker at L2B. The unchanged CLI authenticates grant SHA/test paths,
requires fresh output, performs resource/conflicting-owner checks and supervises
one fresh process. The worker establishes actual supported SINGLE before numerical
imports; environment variables alone are insufficient. Third-party pytest plugin
autoload is disabled; exact frozen tests run before candidate analysis. No model,
solver or research numerical function has been evaluated to prepare this request.

Proposed aggregate ceiling: **300 s**, with planning allocations **45 s initial
process/native/import/source setup + 75 s exact tests + 175 s analysis + 5 s
finalization**. These phase figures are not measured feasibility or separately
certified interrupt deadlines. Existing aggregate supervision stops new work at
295 s and permits at most 1 s termination grace inside the remaining allocation.
Unused CT1N/CT1R or other research allocations cannot be transferred.

Proposed guards remain 1 GiB sampled RSS, 1 GiB total new output, at least 2 GiB
initial free disk and a 1 GiB runtime free-disk floor. Logs, caches, temp files,
JUnit, science rows and monitoring share the output cap. Overshoot and monitoring
gaps must remain explicit; a sampled watcher is not a demonstrated hard memory cap.

At N=80 the bounded panel retains 16 intervals (including the full prefix scan),
4 normalization populations, at most **4,608 product records / 88,704 matrix
multiplications** over all candidates/subsystems/authority populations. It omits
3,224 of 3,240 arbitrary contiguous windows per population; these deliberate
omissions are separate from missing selected endpoints. Worst full-prefix growth
is anchored at the first available factor, not a maximum over all possible starts.

Complete runtime, RSS and output feasibility **cannot be established statically**.
Repeated source bindings, unchanged domain/derivative/gain qualification and all
prerequisite tests may exhaust the allocation. Historical binary/plugin identities
remain partly unknown. Primary must accept or separately qualify these limitations;
no favorable retry, cap increase, replacement point or silent gain substitution is
proposed. If hard per-phase enforcement or producer exception typing changes are
required, `guards.py`/other producers need separate source authorization.

Local scientific failure retains the exact original observation and blocks only its
dependent conclusions; independent candidates continue while common prerequisites
remain trusted. Source/environment/schema/native compromise, global resource limits
and unknown programming defects stop the run. All twelve candidate statuses, failed
comparisons, partial products, unknown coverage and missing selected endpoints must
be retained. Frozen Performance, Safety, Efficiency, SID, CT1N/R and optimization
remain outside this request.

Aggregate timer issue requiring separate source scope: unchanged `cli.py` performs
source/hash/resource preflight before `guards.supervise_worker` starts its 300 s
timer. The requested whole-command aggregate ceiling therefore remains unresolved.
The command above is a review proposal and **must not execute** until Primary and
Secondary resolve that gap. Proposed correction: start one monotonic deadline
before CLI preflight and propagate remaining time without resetting it. That would
require separately authorized `scripts/ct1/cli.py` and `scripts/ct1/guards.py` edits;
neither file was changed. No separate or borrowed preflight allocation is assumed.
