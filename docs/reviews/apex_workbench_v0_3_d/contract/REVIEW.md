# V0.3-D independent archive-contract review

**Decision: PASS for bounded implementation of the stated single archive profile.**
30 October 2026. Separate reviewer context; no adapter existed when reviewed. Base
`7da7100fe624481e6066390d503abea5b4292b4d`, branch `codex/apex-workbench-v0-3-d`.
Reviewed [contract](../../../apex_workbench_v0_3_d/ARCHIVE_CONTRACT.md) SHA256
`ac870a008180e33e59bb6259644865c48215bde3b229e29ce56f02a976916f22`.
This is a preimplementation semantic/integrity review, not implementation correctness,
new scientific qualification, formal Verification or final user acceptance.

| Contract area | Independent evidence and disposition |
|---|---|
| Producer/source identity | Scientific and export revisions both `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae`; all **294** manifest scientific source hashes independently match immutable historical Git blobs. Current runtime source is not substituted. PASS. |
| Trust chain | All four contract SHA256 anchors match retained bytes. P/E4 acceptance is limited to original Architecture A synthetic scope. VIS inventory binds all **25** original case files; all sizes/hashes match. All **15** scientific-manifest artifacts match; manifest self-seal matches the externally bound manifest. PASS. |
| Clocks and controls | First state is native time0/s_abs1; first control computation0/application0.005 s. First cycle release0.1, ready/accept0.135 s. Distinct application/computation/host clocks are required and correctly specified. `a_cmd=Fx/m` is retained. PASS. |
| Events and solver meaning | First event is native `command_computed`, controls source row0/phase5; within-phase order is explicitly missing. A `preparation_ready` payload contains actual `status=Solve_Succeeded`; cycle `status=accepted` is a different concept. Frozen producer code confirms partial order and existing payload provenance. PASS. |
| Missingness and reconstructed fields | Manifest declares unavailable unapplied tail/independent world truth, row missing reasons, native state/endpoints, producer-reconstructed XY/reference/authority intervals. Contract preserves these distinctions and does not rerun exporter functions. PASS. |
| Geometry and sector selection | Hashed fixture has original nine named sector starts, length154.76345492731022 m, SI/left-positive/CCW conventions and gamma2. Native-progress half-open filtering preserves original rows/run identity. Controls/events/cycles remain explicitly full-run because they lack native progress. No inferred crossing/event/score is needed. PASS. |
| Coverage and historical status | Original native end62.23500000000001 s; target-laps termination, two crossings, initial partial plus one complete lap, intended80 s. Existing reconstructed crossing metadata remains historical metadata. Original ingestion-pending flag is preserved separately from P acceptance and new software review. PASS. |
| Containment and scope | Fixed single-case discovery, pinned inventory, operation-local verified bytes plus final rehash, unsafe/missing/changed evidence quarantine and no execution/lifecycle/qualification path are technically sufficient. Final implementation must demonstrate these properties; contract approval does not demonstrate them. PASS. |

Independent read-only checks used Python standard-library `hashlib`, `json`, `csv` and
`subprocess.run(['git','show', revision+':'+path])`; no scientific module imports, simulations,
exporter invocation, pytest, numerical campaign or original-data writes. CSV counts independently
read: states12,448; controls6,223; cycles622; events14,310; planning3,097. All matched the original
manifest. All **11** exporter source hashes also independently match historical Git blobs.
Reviewed `scripts/task007dvis/{interface,export}.py`, actual manifest/fixture/native rows,
E4 acceptance and Performance profile evidence. No mismatch or material contract gap found.

Implementation clarification: sector-filtered traces must use native sample markers or explicit
gaps so plotting does not connect disjoint visits across omitted portions of the run. Retain the
unfiltered whole-track reference as context and label producer-reconstructed position separately.
This follows the stated no-interpolation/native-view contract; it does not change scientific
definitions or require a new parameter decision.

Remaining limits: only controlled_A is approved by this contract; G and incomplete C70 are not
ingestion targets. Its five observed event kinds are command computed/applied, preparation ready,
handoff accepted and releases; this successful P case demonstrates no recorded fallback or
controller-failure episode. Primary's broader C0/failure-inspection M4 goal remains incomplete;
the explicit D brief's preference for a complete accepted P archive is satisfied within its bounded
scope. No unapproved failure archive is selected or repaired. Exact future runtime/profile choices
and rolling-response experiment approval
remain pending. Immutable historical source identity is demonstrated, not hardware/physical
validity or hard real-time behavior. Final exact-source independent Engineering Review and focused
negative/invalidation/UI checks remain required before a V0.3-D engineering delivery claim.
