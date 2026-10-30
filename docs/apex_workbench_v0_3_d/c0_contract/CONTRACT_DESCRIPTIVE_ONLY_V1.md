# C0 original155 — descriptive-only inspection contract v1

**Contract identifier:** `c0-original155-descriptive-only/1` (contemporary proposed inspection contract; **not** an original producer schema).
**Admission/profile:** `descriptive_only / source_unverified`.
**Disposition:** **DRAFT — INDEPENDENT CONTRACT REVIEW PENDING.** No implementation, adapter admission, qualification, scientific execution or approval is implied.
**Authority:** Primary APEX's conditional amendment to Section A; audit revision `acf34015157d237a979fd11263982be6b82c523c` (30 October 2026).

This document is the narrower successor to the original [blocked contract](CONTRACT.md). The original [Section A audit](AUDIT.md) and [contemporary inventory](evidence_inventory.json) remain historical evidence, unchanged. **G1 capture-time producer/source provenance remains OPEN**; this contract does not resolve it or promote a final-delivery reference revision into a capture identity.

## 1. Exactly admitted bytes and authority

Only the following *existing local artifact* can be admitted as a **record of literal JSON content**:

| Attribute | Exact requirement |
|---|---|
| Path | `results/task007d/c/amended/c0_export/original155.json` |
| Byte count | **152,600** |
| SHA-256 | `2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5` |
| Origin confidence | **Exact known retained bytes**; **capture source/configuration/environment/receipt unverified** |
| Archive scope | Exactly one file/profile; no wildcard, directory traversal, arbitrary upload, alternate fixture or automatic version detection |
| Original format | Historical unversioned JSON; no embedded producer schema, capture revision, environment, source manifest or execution UUID |

The known checksum establishes identity of retained bytes *only*. The amended-C reference delivery `44e0471680bb22ea1ee790173d1f2481a905f386`, its static source inventory, neighboring pilot, and later preservation records are **context/reference evidence only**, not capture-source authority. No current-source import or "equivalent" record is allowed.

The contemporary Section A inventory describes observed keys, shapes and nullability; it is *not* a backdated producer manifest. Any external contract or code revision used for presentation must be labeled contemporary and cannot confer historical source validity. No synthetic run, controller, optimizer or capture-environment identity is assigned.

## 2. Evidence hierarchy and UI/export labeling

Every admissible value in a view, tooltip, table, plot, report, figure, exported file and copied summary must preserve the following classification:

| Layer | Permissible statement | Impermissible promotion |
|---|---|---|
| **L0 — literal recorded** | `fallbacks[0]` contains a recorded reason string `"trajectory_exhausted"` and a timestamp token `0.400` (if those exact source lexemes are present); `fixed_handoffs[0].status = "missed"` | "APEX failed because the accepted solver/controller did X" |
| **L1 — contemporary structural audit** | "The pinned record contains 120 `states` rows and 60 `controls` rows; Section A found no duplicate members or nonfinite numbers" | "A verified historical controller generated those samples" |
| **L2 — later source/reference interpretation** | "Reference code describes `a_cmd` as `Fx/m` and the nominal vector ordering as `[vx,vy,r,e_psi,s_abs,e_y]`; applicability at original capture is **unverified**" | Source-qualified SI physical measurements, control semantics or computational performance |
| **Unknown** | Capture source/config/backend/environment/receipt, physical truth, world XY, terminal state, causal cross-stream tie order and actual optimizer activity are unavailable/unknown | Fill, reconstruct, interpolate, infer or certify |

**Required persistent banner**, including any standalone exported HTML: **"DESCRIPTIVE ONLY · SOURCE UNVERIFIED — exact retained JSON; capture-time producer, configuration and environment unknown. Plots show recorded numbers, not qualified scientific/controller-performance evidence."**

For each plot axis or derived display label, mark whether the unit/frame is **literal within the artifact**, **reference-derived and unverified**, or **not declared**. The reference's units are **not embedded source-bound metadata**. Present the raw field name and original numeric token as authoritative; optional SI annotations must read `[reference interpretation — unverified for capture]`. No unqualified "physical time [s]", "measured yaw [rad/s]", "optimizer latency", "true controller fallback" or similar labels. A literal control field called `latency` is still only a recorded value; its original meaning is not authenticated.

Do not repackage descriptive rows as a current verified Workbench execution, `apex-run/0.1.0`, Performance P/VIS, V0.2 Q, historical amended-C source verification, controller acceptance or numerical qualification.

## 3. Payload shape, original ordering, missingness and coverage

Treat the exact original root (18 observed keys) and field/type/optional/null inventories in [evidence_inventory.json](evidence_inventory.json) as the **proposed contemporary parsing constraints**, not as proof of a historic schema.

| Group | Observed retained information | Descriptive-only rule |
|---|---|---|
| `states`, `reserves` | 120 rows each, first through last recorded `time` values 0 through 0.595 | Show literal state/reserve fields, original indices and exact recorded time tokens. No invented 0.600 state or inferred actuator/sensor/ground-truth stream |
| `controls` | 60 rows, time 0 through 0.590, recorded computation/application/latency fields | Separate fields and preserve original row identities. Coincident times/zero latencies in this record are *observations*, not a general system clock contract |
| `plans`, `packets` | Three each; `plans[].status="test_success"`; packet 0 lacks `valid_from` | Show raw plan/packet fields as test-fixture-like records; do not label an IPOPT result or reconstruct omitted validity/authority times |
| `fixed_handoffs` | Two `"missed"` records, with null acceptance/use fields | Display deadline, readiness, late-discard and null fields distinctly; null is not zero, failure, or a time to be estimated |
| `urgent_demands` | One `"fallback"` record | Display its literal trigger/idle/release/busy/grid fields and missing acceptance; no inferred authority sequence |
| `triggers`, `releases`, `misses`, `fallbacks` | Original arrays and their own source order | `misses` includes planner-busy skips distinct from fixed-hand-off missed records; do not merge event categories into one causal timeline |
| `handoffs`, `lap_times`, `codriver_misses` | Empty arrays | "No rows recorded in this collection"; do not assert absence of an event in a real system |
| `failure`, `stop_reason`, `end_time`, `pending_at_end` | `null`, `"duration"`, `0.600`, `false` | Recorded disposition only; `failure=null` does not establish controller availability, successful optimization or scientific validity |

Maintain the exact JSON array order, JSON pointers (`/collection/index/field`), original numeric lexemes (including trailing zeros or extended float representations where present), integer versus real token forms, text, booleans, nulls and **field absence**. Never normalize absent to null, null to zero, zero to missing, empty to not-applicable, or round recorded timestamps in authoritative display/export. A parsed numeric plot may position a marker, but must retain the exact source lexeme and pointer for user inspection and export; no reserialized float may masquerade as the original token.

Allow differing startup/runtime packet/plan field sets **only as actually declared in the pinned observed-shape inventory**. For packet 0, `valid_from` is absent, not `null`; other fields and empty curvature previews retain their original shapes/meaninglessness. Preserve `states`, `controls` and `reserves` independent end coverage; the declared `end_time` is not a native terminal state.

## 4. Recorded chronology without causal reconstruction

A literal-row chronology table may display the following **exact field contents** side by side with their original collection/index/field and source order; decimal display must preserve tokens from the original JSON:

- Fixed handoffs: recorded targets `0.170`, `0.330`; readiness/late discard `0.255`, `0.41500000000000004`.
- Urgent demand: trigger `0.160`, idle `0.255`, release `0.260`; busy/grid waits separately recorded (e.g. `0.095` and `0.0050000000000000044`).
- Planner-busy nominal skip rows `0.200`, `0.300`, `0.400` are distinct from fixed deadline missed rows.
- Fallback entry `0.400` with literal reason `"trajectory_exhausted"` and `valid_domain=true` **as recorded**; no claim of safety, verified model domain, recovery, optimization failure or physical effectiveness.
- The record ends by declaration at `0.600`; last retained state/reserve is `0.595`, last control `0.590`. No final new state, command, acceptance or feedback row can be invented.

Any combined chronology is a **visual index of per-collection records**, not an authoritative total order. Preserve original per-array order and explicit ties/unknown interstream ordering. Time tokens are raw fields; a `[reference-source seconds, unverified]` annotation is permitted but not a capture-authenticated measurement unit. Do not derive new event classes, interpolation, nearest-neighbor matching, held inputs, elapsed response time, causality, reliability/failure rates or comparison scores.

For fallback, reference code may explain `baseline_fallback` nominal/reference self-substitution and zeroed error/correction fields; label that explanation reference-derived, unverified. The recorded zeros **must not** be used to assert perfect trajectory tracking. `plan_id=0` does not by itself identify original command authority.

## 5. Planner and timing labels

`test_success` is a **literal status string**. The later reference fixture describes an injected `StraightPlanner`, NOT an IPOPT solver result. Display: "recorded status `test_success`; reference source suggests an injected test planner, capture implementation unverified." Do not print `optimizer succeeded`, `MPC converged` or `controller accepted`.

The record's `planner_total_time=0.017`, `planner_cpu_time=0.017` and packet timing fields are **not qualified measured optimizer performance**. Later reference source describes injected constants (including `0.010` packet solve duration). Present them under raw recorded values and a reference-derived "fixture-imposed timing; not a measured optimizer benchmark" note. Do not convert host timing names into measured physical latency or combine them into end-to-end compute time.

`fixed_handoffs` missed targets, `urgent_demands` fallback, and `misses` busy skips are distinct JSON records; `t_accept=null`, missing `first_TVLQR_use`, missing trigger-to-authority fields and unavailable controller acceptance must remain explicit. No shared-controller availability statistic may be inferred.

## 6. Permitted views, prohibited claims and exports

**Permitted, if later implemented under separate WORK:** a fixed-record metadata/limitations summary; literal raw JSON browser; per-collection row tables with original JSON pointers/order; simple record-value plots with uncertainty labels; side-by-side chronologically ordered *descriptive* markers, preserving ties; visible missingness coverage/flags; on-demand **reference-only explanatory glossary**; source-linked offline export that repeats all caveats and exact tokens/pointers. There is no current adapter, new replay engine, verified physics/geometry plot, controller Run button or scientific comparison.

**Prohibited:** source-verified labels; validated dynamics/vehicle performance/physical measurements; "NMPC optimized" or solver efficiency; numerical convergence/qualification; inference of control law, controller acceptance/fallback safety, causal sequence, tracking success, or intervention outcome; new state/controls/XY/corridor/reference geometry reconstruction; GP/P overlay, VDL controlled comparison, new scientific metric or qualification threshold. No historical capture envelope may be generated or backdated.

## 7. Future admission, currentness, quarantine — contract, not implementation

Any later admission must follow all of these, in order:

1. Use a fixed allowlisted path only; reject symlinks, escaping paths, alternate roots, duplicates, arbitrary JSON uploads and unlisted archives. Confirm exact 152,600 byte size and SHA-256 of the original file **before parsing**; no "resealing" altered bytes or falling back to another file.
2. Strict JSON shape validation against the *observed inventory* and exact root contract: reject duplicate object keys, nonstandard NaN/Infinity, nonfinite numeric values, wrong field types, booleans in numeric positions, altered array counts, nested dimensions, unexpected fields, invalid IDs/indices, unexpected null or missing where the pinned profile doesn't allow them. Preserve valid conditional field absence and nullity precisely. Parse bounded bytes and enforce bounded rendering/export; do not invoke project producer/importer code.
3. Bind each rendered item to `(original SHA-256, JSON pointer, original array index, literal numeric lexeme)` where applicable. Display `source_unverified` and unresolved G1 visibly throughout. The contemporary contract/authority record has an explicit version/identity; modifying it requires review, not an automatic confidence upgrade.
4. Use operation-local verified raw bytes and derivations only. Before publishing and again after serialization/download preparation, verify original file and applicable external contract/authority identities; if anything differs or becomes unavailable, clear/withhold **all scientific-looking figures, eligibility/status labels and export**, with an explicit quarantine notice. No permissive stale cache, metadata-only invalidation, source binding repair or replay fallback.
5. Never call a controller, scientific model, simulator, optimizer, worker lifecycle, exporter producer, reconciler, cancellation path, actuator or Safety authority. Never write original archive files, hashes, logs or historical receipts.

**Failure labels:** `descriptive_record_valid_source_unverified` is a *presentation validity* classification only, not a scientific/evidence qualification; `descriptive_record_quarantined` for altered/unsupported/missing bytes; `descriptive_contract_unreviewed` until review. Do not reuse `qualified_synthetic_comparison`, `accepted P` or any controller-performance status.

## 8. Static acceptance examples (normative, not executed)

| Input / attempted statement | Required descriptive outcome |
|---|---|
| Correct bytes and `fixed_handoffs[0].t_accept = null` | Show **null**, source path and JSON pointer; "acceptance time unavailable in record", not a zero-time acceptance |
| `plans[1].status = "test_success"` | Show exact string; warn **reference test planner; no verified optimizer success** |
| `fallbacks[0]` records `trajectory_exhausted` at `0.400`, `valid_domain=true` | Show literal fields, provenance banner; **no authenticated source, successful recovery or physical safety** |
| `packets[0]` omits `valid_from` | Show **absent**; do not infer null, time zero or immediate packet authority |
| User requests world XY or a terminal state at `0.600` | Show **unavailable**, do not reconstruct geometry, resample or extrapolate |
| `states` shown with `[m/s, rad/s]` | Only if clearly marked **reference-derived SI/frame interpretation, unverified for capture**; raw field/vector remains primary |
| Report prints `IPOPT solved in 0.017 s` | **Reject**; the named timing is not an authenticated optimizer measurement |
| Data changed, even if same size/mtime or JSON is re-sealed | **Quarantine** on SHA mismatch; no plots, accepted labels or export |
| Unsupported second archive, unknown producer or schema | **Reject**; no generic import and no fallback to reference source |

## 9. Review gate and stop

An independent reviewer must inspect this contract against the *unchanged* Section A audit/draft/inventory and original pinned source evidence, independently assess its meaning and misattribution risks, and issue exact-revision **PASS / PASS WITH CONDITIONS / BLOCKED** with retained findings. The reviewer must not infer historical provenance or treat a clean static contract as software Verification.

**This document authorizes no implementation even after PASS.** Separate Primary bounded WORK authorization is mandatory before a parser/adapter or tests. G1 remains OPEN. No RBT, GP/G/P execution, NMPC, Performance/Efficiency/CT/Safety, physical telemetry or hardware work is in scope.

**Stop at `C0_DESCRIPTIVE_CONTRACT_SUBMITTED_PENDING_INDEPENDENT_REVIEW`**, or `C0_DESCRIPTIVE_CONTRACT_BLOCKED_PENDING_DECISION` if independently found misleading.
