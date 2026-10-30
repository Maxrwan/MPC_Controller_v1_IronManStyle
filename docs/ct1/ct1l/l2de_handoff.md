# L2D deadline correction and L2E static resource review handoff

**WORK_COMPLETE_PENDING_REVIEW. L3 BLOCKED. No numerical work or tests executed.**

Base `265d02f479b7bb759baff9205156635f2da45887`, branch
`research/control-theory-ct1`. Exact delivery SHA is the containing pushed commit,
reported after commit. Only cli.py, guards.py and the three approved test files are
modified; new narrowly scoped review documents are listed in l2d_change_manifest.json.
Every other CT1 file, original evidence, worker, mathematical threshold and L2B
selection policy stays unchanged.

One immutable first-CLI-origin deadline now covers preflight, grant/resource checks,
supervisor setup, startup, existing worker/tests/analysis and finalization. Expired
preflight refuses launch; Primary authorization is revalidated at the supervisor;
no-worker or zero-exit failures cannot become success. Source failure identity and
available preworker evidence are retained. Five-second reserve and <=1 s grace share
the original deadline; no stage restarts it. New clock/process doubles extend the
same 59 selectors across 13 files, without executing them or requiring numerical
libraries for basic deadline logic.

CLI-monotonic accounting does not prove external process-launch-to-cleanup timing.
Python startup precedes CLI entry and return/reap/cleanup can follow its last sample.
External envelope is UNRESOLVED and L3 BLOCKED. The separate external-owner proposal
is documentation only; no supervisor script is created/executed.

Static output review uses actual schemas, producers, 395 fixed source bindings and
the unchanged 15,807-row planning population. It separates exact identity-byte/
cardinality counts from variable strings, logs/temp/index overhead and hypothetical
serialization assumptions. A deterministic whole-run byte maximum cannot be justified;
1 GiB output exceedance risk is material. 300 s feasibility is UNKNOWN, without invented
throughput, compression or test duration. Any future scientific/logging reduction is
proposed only; worker/evidence/schema/workload files are not modified.

Exact environment/archive readiness classifications, revised NOT AUTHORIZED L3
command, independent regression inventory and static/preservation results are the
companion documents. Provisional 45 + 75 + 175 + 5 s allocations and sampled resource
limitations remain. Next: Secondary Engineering Review, then separate Primary L3
scientific decision with remaining blockers explicitly resolved or accepted.

Permitted static audit: 31 Python sources parsed/compiled without evaluation; exact
API propagation, closed diagnostic-schema fields, 27 strict JSON documents, workload
arithmetic, Ruff lint/format and whitespace checks passed. Rechecked 305 frozen source
and 90 accepted archive content hashes; all 52,758 historical result size/mtime
entries were preserved. Unrelated concurrent primary-checkout/ref changes are recorded
in l2de_static_validation.json and were not changed by this task. These observations
are source/metadata checks, not runtime behavior or scientific verification.

| Prerequisite | Review classification | Remaining gate |
| --- | --- | --- |
| Interpreter/venv binary and configuration files | Statically verified | Runtime ABI, executable and module origins |
| Locked NumPy, SciPy, CasADi, psutil, pytest, threadpoolctl and PyYAML versions | Declarations statically verified | Installed metadata/import/backend checks |
| Native SINGLE initialization and CPU/thread behavior | Runtime verification required | Fresh-process controls plus observed mode/CPU/thread evidence |
| E3/E4, source hashes, 12 original candidate/packet/gain bindings | Statically verified | Exact reviewed implementation grant and runtime revalidation |
| 90 accepted archive files | Content hashes statically verified | Runtime availability/readability, without substitutions |
| 59 declared selectors in 13 files | Statically verified | All test behavior unexecuted |
| Fresh output ownership and concurrent measurement guards | Runtime verification required | Exact grant-bound fresh allocation and conflict refusal |
| CLI deadline propagation | Source structure statically verified | Literal regressions remain unexecuted; blocking/tail costs unqualified |
| Sampled RSS/output/disk enforcement | Unresolved as a hard guarantee | Gaps, overshoot and shared external/child accounting |
| External Python launch through cleanup within 300 s | Unresolved | Separately reviewed external owner and single-deadline handoff |

The complete matrix with exact file paths, hashes, versions, archive inventory and
original candidate identities is l2e_environment_archive_readiness.json. External
supervision and any logging/schema/selection reduction remain proposals only.
