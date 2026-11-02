# PRE-SID-R0-W1-C1 — provenance locator correction

**WORK_COMPLETE_PENDING_ENGINEERING_REVIEW**

Bounded documentation correction, 2026-11-02. Recovery remains **RECOVERY_INCOMPLETE**;
the proposed candidate remains **PROPOSED_NOT_ACCEPTED**. G01–G05 remain unchanged and open
under their existing dispositions. This WORK receipt does not approve the correction or
perform Engineering Review or Verification.

## Correction identity and lineage

- Existing branch: `codex/pre-sid-r0-w1-recovery`.
- Exact reviewed W1 correction base and sole C1 delivery parent: `6acd42ec10ec6835e90bc7af157713204899ae6c`.
- Frozen E4 scientific reference, unchanged: `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
- Original W1 delivery: [the exact reviewed commit](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/commit/6acd42ec10ec6835e90bc7af157713204899ae6c); its sole parent is E4.
- C1 delivery revision: the containing correction commit, with its exact SHA and GitHub URL
  supplied in the final delivery handoff after commit/push. In the C1 checkout,
  `git rev-parse HEAD^` must equal the W1 base above. No circular self-embedded SHA is used.

Original W1 identity/ancestry descriptions in the inventory, candidate, unchanged recovery
guide and historical report below continue to describe the original W1 commit `6acd42ec10ec6835e90bc7af157713204899ae6c`.
They do not assert that C1 directly parents E4. C1 descends through W1; E4 remains the
scientific source. The original guide is unchanged and remains interpreted in that W1
historical context. No release identity, tag or accepted status is assigned by C1.

## ER1 R1 disposition and bounded edits

ER1 reported 388 malformed locators among 728 digest-claim records. Individual JSON object
keys containing `/` had been split into path segments. C1 corrects those key tokens with
RFC 6901 encoding: escape `~` as `~0` first, then `/` as `~1`. For example,
`/source_sha256/src/apex/config.py` becomes `/source_sha256/src~1apex~1config.py`.

All 728 record references were inspected against their actual historical JSON structure:
Git-committed JSON was read at frozen E4, and the four original local ZIP-provenance JSON
files were read as accessible bytes. Whole-document references use the empty JSON Pointer.
The authoring reader reconstructed malformed paths from real dictionary keys and required
one unambiguous target; it did not rely on a regular-expression replacement. A separate
strict decoder then checked the written locators and their exact digest bindings.

- Corrected locators: **388**.
- Previously valid locators retained literally: **340**.
- Digest-claim locators required to resolve after writing: **728 / 728**.
- Intended SHA-256 values and complete resolved JSON target values: unchanged.
- Additional source-inventory record plus `/source_sha256` pointer: resolves to the
  unchanged 294-entry historical source map.
- The 31 distribution citations are unchanged plain references to `uv.lock` metadata,
  not JSON Pointer locators; no distribution bytes were fetched or installed.

Only locator strings changed in `recovery_inventory.json`; all other parsed inventory
fields remain identical to W1. Scientific/artifact/dependency identities, expected and
actual hashes, sizes, source attribution, availability classifications and G01–G05 are
unchanged. `freeze_candidate.json` changes only the inventory SHA-256 and byte-size binding.
`recovery_instructions.md` remains byte-identical.

Corrected inventory ordinary SHA-256: `96ebe7bb2dcad903ba25f693b311e946c8f48b42e69578127f2a592423b25185`.
Corrected inventory byte size: **1307491**.

## Static WORK validation and preservation

| Static WORK check | Result |
|---|---|
| Strict JSON parsing of both deliverables | PASS; duplicate members and nonstandard constants rejected |
| Separate strict pointer resolution against 16 actual historical JSON records | PASS: 728/728 digest-claim locators |
| Malformed locators corrected / originally valid locators preserved literally | 388 / 340; no unresolved locator |
| Changed-locator groups | 292 source-inventory, 62 VIS-verification and 34 parity references |
| Intended digests and complete resolved JSON target values | PASS: all 728 unchanged |
| Scope of inventory changes | PASS: only the 388 `digest_claims[].record` strings; all other fields unchanged |
| Additional structured source-inventory pointer | PASS: original 294-entry literal map |
| Scientific source byte identities | PASS: all 294 SHA-256 values at both original worker and frozen E4 |
| Candidate content bindings | PASS: all 17; only the inventory digest and size updated |
| Accepted classification and gap preservation | PASS: RECOVERY_INCOMPLETE, PROPOSED_NOT_ACCEPTED and G01–G05 unchanged |
| E4 source/tree preservation | PASS: all 827 original Git object/mode entries unchanged; no scientific-path diff |
| Other W1 file preservation | PASS: all 828 paths outside the three-file allowlist byte-identical, including the recovery guide |
| Original checkout preservation | PASS: 1,029 tracked-file hashes, HEAD and starting status unchanged |
| Accessible historical external evidence | PASS: all 204 selected file-content SHA-256 values unchanged |
| Historical results metadata | PASS: all 54,162 size/mtime pairs unchanged; this metadata is not whole-archive byte authentication |
| Existing refs before the authorized commit | PASS: unchanged; only the W1 documentation branch and corresponding remote ref advance for delivery |
| Changed paths and whitespace | PASS: exactly the three authorized files; `git diff --check` |
| Original W1 WORK history | PASS: preserved verbatim below this correction receipt |

The independent static reader does not import or reuse the authoring reader. It resolves
corrected pointers with a separate decoder and derives intended historical targets from
literal artifact keys in the actual JSON maps. For a group-level reference it verifies
the specific artifact-key binding, rather than merely finding the digest somewhere in a
record. Recorded source bytes, expected values, target objects and historical local JSON
bytes remain unchanged. These are WORK checks, not Engineering Review or Verification.

The only changed paths relative to W1 are:

- `docs/pre_sid/r0/recovery_inventory.json`
- `docs/pre_sid/r0/freeze_candidate.json`
- `docs/pre_sid/r0/WORK.md`

Temporary static-reader receipts live under `/private/tmp/apex-pre-sid-r0-w1-c1` and are
not new scientific evidence, independently qualified archives or required recovery inputs.
No source/test/configuration/dependency file, historical record, instruction, branch other
than the existing authorized documentation branch, or release tag is changed by C1.
No scientific execution, test collection/execution, simulation, numerical imports,
dependency installation, evidence regeneration, merges, SID or architecture work occurred.

## Continuing review boundary

R1 is corrected as a WORK proposal pending exact-revision Engineering Review. Review must
inspect all locator resolutions, unchanged intended values and candidate inventory binding,
the three-path diff, W1/E4 ancestry and preservation. Separate explicit authorization is
required for Verification or further WORK. G01–G05 are not closed by this correction.

Stop: **WORK_COMPLETE_PENDING_ENGINEERING_REVIEW**.

---

The original W1 WORK report follows verbatim as historical delivery context. Its source,
counts, checks, single-commit/direct-E4 relationship and delivery instructions concern the
original W1 revision, not the C1 correction revision.

# PRE-SID-R0-W1 WORK report

**WORK_COMPLETE_PENDING_ENGINEERING_REVIEW**
Recovery: **RECOVERY_INCOMPLETE**
Freeze candidate: **PROPOSED_NOT_ACCEPTED**

## Authorization and exact source identity

Documentation-only static recovery assessment under the user-supplied W1 request. No
Engineering Review, formal Verification, executable reproduction or new acceptance occurred.
Repository remote is `https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle.git`.
Branch: `codex/pre-sid-r0-w1-recovery` in the dedicated managed worktree
`/Users/marwansaber/.codex/worktrees/pre-sid-r0-w1/MPC_Controller_v1_IronManStyle`.

The documentation branch starts directly at frozen E4 `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
Its exact starting/sole delivery parent is E4, and starting tree is
`63c9165d7b5286240ee5d9e020978cfe0090a1b7`. E4's own parent is E3 delivery `ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9`.
The remote `release/performance-synthetic-v1` ref was checked and equals E4.
Local Git commit objects, ancestry, blob identities and selected ordinary SHA-256 values
were inspected; no cryptographic signature or independent source-authorship attestation is
claimed. The [inventory](recovery_inventory.json) records commit payload hashes separately
from ordinary artifact hashes and Git object IDs.

**Documentation delivery revision:** the containing W1 documentation commit, whose exact SHA,
branch and GitHub commit URL are supplied after commit/push in the final delivery handoff.
Resolve it in the clean delivery checkout with `git rev-parse HEAD` and confirm
`git rev-parse HEAD^` equals E4. Its SHA cannot be embedded in its own contents. E4 remains
the frozen scientific source/acceptance identity; the W1 SHA identifies the overlay only.
Any future accepted R0 release identity is unassigned. No release/tag was created.

## Changed-file inventory

Only these four new documentation paths are authorized and delivered:

- `docs/pre_sid/r0/recovery_inventory.json`
- `docs/pre_sid/r0/recovery_instructions.md`
- `docs/pre_sid/r0/freeze_candidate.json`
- `docs/pre_sid/r0/WORK.md`

The exact W1 allowlist overrides the general handoff-update convention: this file is the
W1 handoff, and `docs/CODEX_HANDOFF.md` and `docs/DECISIONS.md` remain untouched. No architecture,
scientific source, test, fixture, configuration, dependency, evidence or assertion changed.

## Recovery finding and authenticated material

The static documentation overlay is complete for review; independent recovery remains incomplete.
565 selected committed artifacts were inventoried with exact source/path/blob identity,
ordinary SHA-256, byte size and E4 byte-equality checks. All 294 original scientific source
entries match both the original worker `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae` and E4.
All four retained long-case input source maps match those 294 entries. The later three
offline report/test files are distinguished at `d55f203aac1a04be598ebce4c38be51a4883e0ba`.

E2 manifest and E3 exact tested source: `e603672b209985f11ed26b6f44d3949ffd5675c5`.
E3 delivery: `ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9`. Frozen executable ancestor:
`c6990572045e61ee443dc715de9e8c44396e5b41`. E4 acceptance is a separate subsequent record;
none is relabeled as the R0 overlay or a future accepted release.

Manifest SHA-256: `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
Dependency lock: `8cf85868a456415a898643dbb226d146b0b90e5c98982136cf2abf2465fa16ec`.
Project metadata: `c8ea69a3a486c9794b6cf88ac26566211c6f1bb7b7286d86dbaa36a191353d41`.
Vehicle, all five accepted gamma2 Planning constituents and the four original Planning
constituents are separately identified and hashed. No runtime profile is newly loaded.
Historical pending/frozen proposal flags remain literal; existing E3/E4 status overlays
remain authoritative for their respective historical decisions.

Of 210 selected external file locations, **196 are available and authenticated against
committed historical digests**, **8 are available but not fully authenticated**, and
**6 are missing historical outputs**. Actual SHA-256 and verified byte size were obtained
for all 204 accessible files (418,956,735 bytes); no digest/size mismatch was found.
This is a selected-byte audit, not a hash of the entire 11 GiB results tree. The eight
partially authenticated files are original A/B/C/CR source ZIPs and their local provenance
records. ZIP bytes match their local expected digests; independent historical binding of
those local provenance records remains unresolved. Git object SHA-1 values were never
substituted for file SHA-256 values. Selected remote dependency distribution candidates
were recorded from the lock only; no distribution bytes were fetched or qualified.

The required current local raw/verification files selected by the committed bindings are
accessible. The absence of a durable independent retrieval route is a different gap; no
manifest path, local existence or old digest was treated as independent retrieval proof.

## Outstanding gaps and consequences

| Gap | Deficiency and consequence | Minimum future action |
|---|---|---|
| R0-G01 | Local raw histories, exports, launcher gates and E3 logs lack a qualified independent retrieval route. Git-only recovery is incomplete. | Authorize archival transfer of existing bytes; record archive/per-file SHA-256 and sizes, custodian/location, and independent retrieval authentication. |
| R0-G02 | Historical Python/OS/Accelerate, IPOPT/linear-solver and uv/build-tool provenance is incomplete; lock distributions are unaccessed. Exact environment recovery is unestablished. | Retrieve genuine historical records or explicitly review an alternative target/provenance boundary; separately authorize environment qualification without changing the lock. |
| R0-G03 | Failed measured C70 lacks summary/manifest/packets/planning completion and runtime observations; later A/C70 cases were not run. Complete VIS or measured C70-lap claims are unsupported. | Preserve nulls, failure and absence. Recover only genuine existing records; no reconstruction or favorable rerun. |
| R0-G04 | Four historical source ZIPs depend on local unanchored provenance digests. | Retain this limitation or obtain independent historical binding; exact Git source remains authoritative. |
| R0-G05 | Historical launchers require source-bound prerequisites/order/fresh outputs, and the E3 wrapper asserts clean exact E2 HEAD with fixed paths. | Review a separate exact-source, isolated, fresh-output executable-recovery plan before authorization. |

The six missing files are the two unexecuted-case summaries plus measured C70's
`summary.json`, `scientific/manifest.json`, `scientific/packets.json` and
`scientific/planning.csv` under `results/task007d/vis/vis1r_c699057/`.
Their absences are preserved historical limitations, not newly lost required A records.
Failed C70 remains censored at 48.670 s, with 30 fixed misses, eight terminal misses,
no complete measured lap and subsequent export failure. Worker-native-thread/forecast-match/
wall/CPU/RSS observations remain unavailable. Source attribution remains campaign/input-bound,
without an invented direct final-summary revision.

The accepted scope remains bounded synthetic Architecture A. Existing E3/E4 technical
limitations and HW01–HW07 survive, including incomplete asynchronous fallback-transition
coverage, restricted fallback admission, no guaranteed recovery/standstill braking/watchdog/
swept-body safety, synthetic vehicle/tire parameters and no embedded timing certification.
Physical readiness, integrated Safety, ROS 2 and measured embedded real-time qualification
are not established. Historical E3 **750 passed, 0 failed/errors/skipped** is retained
execution evidence only; W1 did not execute or scientifically revalidate it.

## Static checks and preservation

The W1 tools read Git objects, text/JSON, existing artifact bytes and file metadata using
standard-library-only helpers located outside the repository. No project module, numerical
library, existing historical validation command or audit reader was imported/executed.
Static JSON parsing, reference/hash/size comparisons and documentation checks are WORK
checks; they are not independent Engineering Review or formal Verification.

Static check results are recorded below before the sole delivery commit.

| Static WORK check | Result |
|---|---|
| Strict JSON, duplicate-key/nonfinite-value rejection and explicit null/status checks | PASS: both JSON deliverables |
| Per-artifact inventory consistency | PASS: 565 committed, 210 external, 31 unaccessed distribution and 5 unverified environment/archive rows |
| Candidate content-hash/size bindings | PASS: 17 references |
| Markdown local links and fences | PASS: 6 links; fences paired |
| Historical execution/installation/validation quotations | PASS: 5 command blocks compared verbatim to frozen reports; unexecuted |
| E4 preservation | PASS: all 827 preexisting tracked files retain their original SHA-256; executable/config/test diff empty |
| Original checkout preservation | PASS: branch, HEAD, clean status and all 1,027 tracked-file SHA-256 values unchanged |
| Historical results preservation | PASS: all 53,522 file size/mtime pairs unchanged; selected 204 accessible external files content-hashed separately |
| Changed-file allowlist / existing refs | PASS: exactly the four allowed new paths; preexisting branches/tags unchanged |
| Authored-file whitespace | PASS; two Markdown trailing spaces removed before delivery |
| Numerical/project imports and test executions | 0; all historical reader/validation commands remained unexecuted |

These results apply to the E4 base plus these four authored file contents, associated with
the containing delivery commit after staging. JSON/reference/source checks found no content
mismatch. Documentation-check setup corrections separated two quotations for literal block
comparison and accounted for Git no-index diff exit semantics; no scientific evidence changed.

The original checkout stays on `codex/apex-workbench-c0-descriptive-adapter` at
`dd0ff721ac88456f0111e1fc3eaf22d984e83250`; its 1027 tracked-file hashes and starting
clean status are preservation baselines. The E4 worktree baseline covers all 827 tracked
files. The 53,522 historical result-file size/mtime pairs are
also compared; this metadata comparison is not a whole-results content rehash. Existing
refs/tags are preserved; only this new documentation branch and its pushed remote ref may
be added. Transient static audit snapshots live under `/private/tmp/apex-pre-sid-r0-w1-audit`
and are not durable published recovery evidence; the committed inventory retains selected
artifact hashes/sizes and exact Git reference bindings.

No simulations, solver calls, benchmarks, tests (including collection), numerical imports,
dependency installation/upgrades, evidence repair/regeneration, SID, merge, release/tag,
independent Engineering Review or Verification ran.

## Independent Engineering Review and subsequent prerequisites

Engineering Review must inspect the exact delivered documentation SHA and its sole E4
parent, four-path diff and full E4 preservation; assess the inventory's authentic versus
local-only versus missing/unverified categories; check historical command fidelity and
source/environment separation; accept or correct the incomplete classification and each
gap disposition; and confirm no release/physical/Safety/ROS/timing claim is implied.
The proposed freeze candidate remains PROPOSED_NOT_ACCEPTED throughout review.

Any subsequent Verification requires separate explicit authorization, an exact reviewed
revision/scope and evidence-preservation plan. Close or explicitly disposition essential
static retrieval/environment gaps first. Pure documentation Verification must stay static;
independent executable reproduction requires its own separately approved experiment/harness
scope, qualified environment, original source checkouts, prerequisite gates, fresh output
paths, budgets and stop conditions. No unchanged historical numerical suite needs repeating
merely to validate this overlay. A pushed WORK result is not acceptance or permission to run.

## Separate executable-recovery proposal — unexecuted

First recover and independently authenticate existing evidence without executing scientific
code. If executable recovery is still needed, separately authorize an isolated environment
qualification and existing-entry-point reproduction plan: exact E3 test/source and VIS worker
checkouts, honest environment/binary uncertainty, fresh new evidence destinations, source-bound
prerequisites and sequential SINGLE execution, physics/latency/deadline semantics preserved,
negative/censored outcomes retained and scientific stop gates enforced. Review the historical
wrapper's fixed paths and HEAD assertion before any adaptation; an adapted harness receives
new provenance. Offline analysis, full regression and any worker rerun are separate execution
choices, not work performed or authorized by W1. Do not reconstruct missing scientific records.

Stop: **WORK_COMPLETE_PENDING_ENGINEERING_REVIEW**.
