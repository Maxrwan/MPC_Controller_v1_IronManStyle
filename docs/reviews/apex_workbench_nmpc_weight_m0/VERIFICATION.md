# M5-A formal software Verification — BLOCKED

**NMPC_WEIGHT_LAB_M0_VERIFICATION_BLOCKED_PENDING_PRIMARY_DECISION.** 3 November 2026.
Exact reviewed implementation: `96be0969703f0675060208843c9920bca2187e3e`.
Tested checkout: documentation-only delivery `d4315b74f643238fd6b6a49f8922fda3351188da`,
branch `codex/m5a-nmpc-weight-m0`. This containing delivery is documentation only.
[Machine record](verification_record.json). No implementation/test repair or new experiment occurred.

## Blocking evidence finding V1

The production read-only `nmpc_weight_lab.verify_gate()` fails at lines 345–347 with
`ValueError: Software gate evidence changed`, before any formal regression is launched.
The affected required file is:

`results/apex_workbench_nmpc_weights/authorizations/primary-r1-r2-20261102/exploratory_software_probe.json`

- Expected SHA-256: `dac35d357e64ef0e30702650ddef2b130503fab643315170cbfb80c4a53acb3e`.
- Observed SHA-256: `443c09d57db08eefeef2ae9ebc35d83767845b3161bbe4d461b90b23dcb237a4`.
- The mismatch was already present in this Verification's initial snapshot, before harness creation.
- Gate `19217b49b7b49129e565078a6fdfaccc27bad8878f42c87a5c56fb8bb1fde857` and authority
  `47ce382539021089742e59fa799227f531b761f2117bce4bd30095d3e8f4fbca` remain unchanged.
  The other four gate-referenced evidence files match their hashes.

An existing original probe wrapper retains stdout which, rendered **in memory** in the original
storage format, exactly hashes to the expected probe identity. Comparison establishes equal decoded
values/types and a different `/imports` dictionary member order (first difference at index149:
`numpy.ma.core` versus `numpy.rec`). No numbers, timestamps or native values were repaired.
The current report also matches a separately retained fresh-probe wrapper. These facts do not
identify who or what wrote the authority file. Both versions/wrappers and the unchanged gate/authority
were copied into the fresh failure-evidence directory; the authority file was not restored/resealed.
The correct fail-closed guard does not make this unsatisfied byte-identity prerequisite a PASS.

Static source inspection identifies a concrete write collision: `nmpc_weight_panels.py:23` uses
that authority filename as the configuration-preview destination, and lines34–37 run a fresh
no-solve probe and write the preview without exclusive publication. This can overwrite gate-bound
evidence. It is a reachable source path, not attribution of the observed writer; no live overwrite
was attempted during Verification.

## Executed and unexecuted scope

**Formal regression invocations: zero.** No pytest collection, JUnit, selected-case execution,
passes, failures, skips or deselections were generated. The intended selection and unexecuted
controlled-process harness are retained, but are not test results. Existing G2 enabling variables
were absent and gates were not changed; do not count the historical17 skips as fresh skips.
The earlier73 WORK passes and independent reviews remain historical evidence, not new Verification.

Exact failed command argv, environment, stdin body, exit2 and traceback are retained under
`results/apex_workbench_nmpc_weights/verification_20261103/` as
`blocked_gate_reproduction_command.json`, `blocked_gate_reproduction_stdin.py` and
`blocked_gate_reproduction.log`. A preliminary harness TypeError (omitted runtime argument) and
an unexecuted approval-service usage-limit rejection are separately retained; neither is the
blocking product/evidence finding. The approval-service issue was resolved through the same
approval path, without bypassing it.

The checkout is a clean documentation-only descendant of the exact reviewed source: all eight
producer hashes match its Git blobs. The333 frozen runtime files match source
`48adbdf64d492592d15e23c917aca71fa58aa8a5`, and actual installed dependency identities match the
approved gate environment (Python3.12.14/macOS26.5.1). No new numerical backend/thread or timing
qualification is claimed. R1/R2 behavioral checks, lifecycle/resource fixtures and Workbench/P/C0
regression remain unexecuted after the mandatory stop. Full native semantic Verification is incomplete.

## Existing native data and retrieval limits

Both native raw JSON files were actually read locally. Their raw and manifest hashes still match
the delivered inventory:

| Retained case | Raw SHA-256 | Manifest SHA-256 |
|---|---|---|
| Nominal `20261103T092919578650Z_8db96af73edb48afa17b8d608c9cb7a9` | `e81b5df5e10164eed1feccc3217292718391f1c0eb89d123cfb70e3b47a13263` | `bc4f53a95fcae849e11537eb7c25f9b9d1480be4be8f2f88e33d212f283f0933` |
| Exploratory `20261103T092919578903Z_67d4ffe6c44b4628adc58505ca43b50c` | `95c3a927ac3203c1a4316a89257fc3f86cf754daac789ec07245c3450bcae792` | `dc74308fa3fd16edfd600ab1bf1b31c4b56df2070284a8936d7c5b6a78fe6f31` |

Absolute paths, sizes, observed status and retrieval details are in the machine record. These
are ignored local records on this host. A committed SHA inventory is **not an independently
retrievable raw archive**; off-host persistence/retrieval has not been established. The hash
mismatch in the separate preflight evidence is not evidence of changed native trajectories or
controller failure. No scenario was rerun and no physical/statistical improvement is inferred.
Objective contributions retain their post-solve expression-accounting classification, not native
IPOPT iteration instrumentation; this incomplete Verification makes no new accounting acceptance.

All3283 regular M0 files and191 symlinks present at the start, including the observed mismatching
file, original failed attempt/claims/BLOCKED and historical reviews, remain unchanged by this task.
This proves preservation since this Verification began, not that the preexisting mismatch was valid.
Source/tests, scientific equations/configurations/dependencies, retained runs and consumed claims
were not modified. No R0, SID, Safety, Efficiency, ROS2, hardware or later feature work occurred.

## Required next decision

Primary should authorize bounded corrective WORK to separate mutable preview output from immutable
authority evidence, with a regression proving that Validate configuration cannot alter sealed gate
files. Preserve this failure and its observed file. Primary must decide whether exact-byte evidence
recovery from the authenticated original wrapper or an independently reviewed append-only
reconciliation is appropriate; do not silently restore the file, accept reordered bytes, reseal the
gate or regenerate an experiment during Verification. Any changed implementation needs independent
Engineering Review, then an explicit decision on fresh bounded formal Verification.

No merge, final acceptance, new scientific experiment or automatic next stage is authorized.
