# C0 Section A — producer/archive audit and unresolved gaps

**C0_ARCHIVE_CONTRACT_BLOCKED_PENDING_DECISION.** 30 October 2026.
Authorized base: `f80a105d9ab3c1fcf5e28e97a0876fcb422c1c60`, branch
`codex/apex-workbench-v0-3-d`. Section A only; documentation delivery.
[Blocked contract draft](CONTRACT.md), [evidence/source/type inventory](evidence_inventory.json).

## Decision and established evidence

The original `original155.json` bytes are intact and structurally inspectable. Their provenance
is **not sufficiently bound to the exact capture-time producer** to admit the requested source-bound
Workbench profile. Do not infer that matching reference code or a later verification ran this file.
No independent contract review, import, parser implementation or adapter work occurred.

- Exact artifact: 152,600 bytes, SHA256 `2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5`.
  This matches the prior MVP anchor. Strict standard-library parsing found no duplicate members or
  nonfinite values. The compact original155 summaries agree with the corresponding raw fields.
- A documented immutable producer/reference pathway is available at amended-C delivery
  `44e0471680bb22ea1ee790173d1f2481a905f386`. All 16 declared final source hashes in its verification
  record match Git. A conservative 69-file local static-import reference set (including vehicle
  YAML) was inventoried by AST inspection without imports. It is not a capture manifest.
- Native data include 120 state/reserve rows, 60 controls, three plans/packets, two missed fixed
  commitments, three planner-busy skips and one fallback. Last state0.595/control 0.590 s precede
  declared end 0.600 s. `test_success` is an injected planner status; `failure=null` does not make
  controller availability successful. Missing acceptance/use/authority times stay null.
- The draft records clocks, per-collection identity/order, status meanings, units/frame declarations
  from reference source, missingness, mode-dependent fallback diagnostics and fail-closed rules.
  No new telemetry/event/score is computed. Reference sampling and test gains are distinguished
  from physical observations, optimizer results or a computed TVLQR design.

## Why the source-binding gate fails

| Gap | Direct evidence and consequence |
|---|---|
| G1 — capture producer binding, **blocking** |The raw file has no schema/source/configuration/environment envelope; its directory contains only original155, recovery35 and summary JSON. The reference exporter writes the raw result directly without adding those identities. The known hash authenticates the retained bytes, not their complete capture source. The 16-file final-delivery inventory binds final code but names no original155 capture. |
| G1 — nearby sources cannot be substituted |Neighboring `C1_steady/summary.json` records baseline Git `c56e509…` plus runtime source hashes: asynchronous `38b6e352…` and fixed_handoff `84c60758…`. Final 44e reference hashes are `7d14395a…` and `8f0bc766…`. Reproduction documentation explicitly describes post-pilot urgent-bookkeeping changes. This proves source ambiguity in the work period, **not** which variant C0 used. C0 has urgent demand, so borrowing a no-urgent C1 compatibility argument is unsound. |
| G1 — later preservation/authority is narrower |CX's reviewed source manifest binds later code; its retained before-snapshot lists original155 size/mtime, not a capture source map. The exact raw-byte hash first appears in V0.3-A commit `03055a183be0f5d3691714103588d5b263748128`; the f80 task records it again. These identify known retained bytes, not a retroactive execution-source receipt. |
| G2 — capture environment/receipt, unresolved |No amended-C0 environment/package/backend/command/process receipt was located. Reference code requests Accelerate SINGLE but records no native result in this export. Host computation fields are not evidence of the environment or physical timing. This blocks reproduction/performance claims; no new measurement is authorized. |
| G3 — intentional channel limits, not a repair task |No native XY/serialized geometry or actual optimizer telemetry; no native terminal 0.600 s state. Reference fallback rows use self-reference/zero error placeholders. Keep unavailable/mode-specific, without reconstruction or perfect-tracking/safety claims. |

The older `docs/task007d/c/c0_summary.json` has source/environment metadata but describes the
**different original blocked variable-handoff case**, duration 0.8 s and off-grid urgent release.
It cannot supply missing provenance for this amended fixed-handoff 0.6 s file. Original failure
and amended resolution remain distinct; neither record was edited.

Search/audit scope: the exact C0 export directory, original/amended C documents and compact records,
producer/test-fixture/serializer sources at 44e, neighboring pilot source receipt, CX formal source
and raw-metadata inventory, V0.3-A byte anchor and Git history. File mtimes were treated only as
hints; they are not source authority. No claim is made that an unavailable record cannot exist elsewhere.

## Minimum next decision

First seek an **existing** capture-time source inventory/snapshot or equivalent authoritative record
that links the exact artifact to producer, test fixtures, serializer and dependency/configuration
identities, including any dirty changes. A final commit SHA alone is insufficient unless its relation
to the capture is established. Preserve and independently review any supplied binding; do not rerun
or regenerate the fixture as a substitute for historical provenance.

If such evidence is unavailable, Primary may separately decide whether to authorize a narrower
**known-bytes/descriptive-only** profile with source/environment explicitly unverified and no
source-verified scientific presentation or qualification. That is a changed admission scope, not a
repair of historical provenance, and requires a revised contract and independent review. This audit
makes no such decision. RBT-S/N/V, future G/P execution and all scientific campaigns remain gated.

## Execution and preservation scope

Only standard-library JSON/hash/AST inspection and read-only Git commands were used. No scientific
or project module was imported; no fixture, exporter, planner, plant, worker, Workbench, numerical
test, simulation or campaign ran. Earlier tests are historical evidence, not fresh passes here.
The inventory and draft are contemporary audit documents, not manufactured historical manifests.
Audit scripts/logs and before/after preservation evidence are retained under
`results/apex_workbench_c0_contract_20261030/`; original files remain in place.

**Stop: C0_ARCHIVE_CONTRACT_BLOCKED_PENDING_DECISION.**
