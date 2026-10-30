# Primary APEX — V0.3-C Formal Acceptance

**Recorded:** 30 October 2026  
**Decision:** `V0.3_C_ACCEPTED_WITHIN_VERIFIED_SCOPE`  
**Authority:** Explicit user instruction to Primary APEX after independent Engineering Review and formal Verification  
**Workstream/branch:** `codex/apex-workbench-v0-3-c`  
**Exact verified implementation:** `34f98a4894e457900d2fae3b2fd09ead4f5ba5a0`  
**Prior clean documentation-only delivery:** `6d3a368dc7bb7e6f029f70eda6603b475e09c1ca`

## Evidence reviewed

- Independent N1 Engineering Review: `docs/reviews/apex_workbench_v0_3_c/responsiveness/iteration_1/REVIEW.md` — **PASS** at the exact implementation, with no material finding remaining within its bounded scope.
- Formal Verification: `docs/reviews/apex_workbench_v0_3_c/RESPONSIVENESS.md` and `responsiveness_record.json` — **one complete suite**, **1,069 passed**, **17 separately gated G2 skips**, **zero failures/errors**, exit 0; split 777 repository plus 292 Workbench passes. These are reported retained results, not independently rerun by Primary.
- Original Workbench scientific dependencies (56 files), all 345 retained qualification files and accepted scenario documents are reported unchanged; original reviewed behavioral hashes and original negative/failure evidence remain preserved. Historical results metadata audits are **not** full content rehashes.
- The current source has accepted Home/Run/Inspect/Compare, three existing canonical experiment adapters, native-time recorded replay of supported Workbench evidence, 2–4-run pairwise comparison, read-only archives, evidence/quarantine behavior, original qualification consumer, launcher ownership and legacy compatibility.
- Historical 89.886 s Q-selection outlier and earlier failed AppTest/reviewer attempts remain preserved. Their unique cause is unknown. The corrected candidate passed the original deadlines and independent bounded responsiveness gate; this acceptance does **not** certify latency tails, real-time responsiveness, macOS portability or hardware suitability.

## Accepted scope and limits

**ACCEPT** corrected V0.3-C as a local, verified **software engineering workspace** and as an interface to the previously accepted **finite synthetic** V0.1/V0.2 experiments/evidence, under exactly their original source, qualification and numerical limitations.

Current playback is read-only and tied to verified existing Workbench software profiles. It does not reconstruct missing telemetry, interpolate unrecorded states, provide generic external import, guarantee physical sensor compatibility, or authorize live actuator/arming/Safety commands. NMPC/TVLQR/asynchronous racing execution is **not** a newly qualified Workbench adapter. The 17 G2 skips are not passes or authorization for those workers. This acceptance does not independently accept V0.3-B under a separate user gate, and does not imply completion of the full Engineering MVP M4.

## Racing scenario boundary — separate

The proposed S1/S2/S3 decisions in `docs/apex_workbench_v0_3_c/SCIENTIFIC_DECISIONS.md` remain **PENDING PRIMARY SCIENTIFIC REVIEW**. The existing oval LQR/PI option remains usable under its original scope. GP historical profile G, immutable Performance profile P, new rolling-response family and other proposed racing scenarios have **no new executable or qualification authorization** from this acceptance. Do not conflate G and P, silently migrate frozen source identities, or treat illustrative overlays as controlled causal comparisons.

## Authorized next stage — V0.3-D (M4)

**Proceed with bounded V0.3-D engineering development planning and subsequent scoped WORK** toward the already documented M4 goals: (1) inspect a specifically contracted retained C0/asynchronous *software* controller-failure archive without modifying it; (2) improve source-linked engineering figure/HTML/evidence export using supported verified records.

Before implementing a new recorded archive profile, define and independently review the exact producer/source/schema, timebase, unit/frame, missingness, event/command identity, historical partial/failure interpretation and provenance requirements. Ordinary presentation/export implementation may proceed under a bounded Codex assignment without changing accepted scientific definitions. No new science/metric/threshold, controller, simulator, solver, replay-derived event, racing adapter, numerical campaign, hardware integration or Safety authority is authorized.

Apply the existing `WORK → Engineering Review → Verification` process. Preserve frozen main/Performance, current V0.3-C accepted source/evidence and independent research branches. Stop at the relevant review gate before scientific scenario execution or claiming new qualification.

**Primary disposition:** `V0.3_C_ACCEPTED_WITHIN_VERIFIED_SCOPE`. **S1/S2/S3 remain separate and pending.** **V0.3-D is the next bounded engineering stage, not an implicit approval of new scientific execution.**
