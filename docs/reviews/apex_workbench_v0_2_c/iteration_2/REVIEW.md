# V0.2-C independent Engineering Review — iteration 2

**PASS — V0.2_QUALIFICATION_READY_PENDING_EXECUTION_AUTHORIZATION.** Reviewed exact source `4897686e79c13757d5ef5b4373b44d4cab99b5bf`, branch `codex/apex-workbench-v0-2-c`. Prior candidate: `a6917a00c2ac48e69d3a28ca4e7c9fbf6d964052`. Unchanged scientific contract: `0cc7e4f626311aec05977bd3beda40c346fa4214`. Recorded 29 October 2026.

Q1 is closed by the bounded evidence correction. The accepted C1–C3 corrections, refinement admission, literal numerical calculations, fixed campaign and conservative qualification consumption are ready for a separately authorized qualification execution. This is an independent software Engineering Review pass, not independent human approval, formal Verification, numerical qualification or physical validation. No campaign is authorized or executed by this report.

## Independence and scope

The same separate reviewer context that found Q1 inspected the corrected exact Git revision and its complete diff. The reviewer did not implement the correction or modify repository files/Git state. Root's reported pass counts were checked as retained evidence and not substituted for reviewer reproduction. The first failed review and its reproduction document were byte-compared with the preserved repository copies and remain unchanged.

Only `qualification.py` changes production behavior between the candidates: the new retained execution-identity gate and its recorded identities. Added tests and delivery/review documentation make up the remaining diff. No canonical model, original experiment script, state/coordinate contract, physical case value, accepted numerical threshold, V0.1 entry point, frozen profile or accepted A2 contract changed in this correction. Applicable iteration-1 inspection and 99-test reader/calculation evidence remain scoped prior evidence; unchanged C1–C3 behavior was not redundantly rerun.

## Q1 closure and nearby checks

`tools/apex_workbench/qualification.py` now calls `distinct_executions()` after binding all source runs and validating each protocol slot, before scientific identity/calculation. It consumes verified `worker.json`, requires a nonempty string run ID, worker role, positive integer PID and finite positive birth time, and independently rejects duplicate run IDs, worker PID/birth pairs and manifest hashes. Source paths remain separately distinct. A copied original cannot serve as a fresh baseline repeat. The qualification document records the captured per-slot execution identities.

The production reader recomputes the complete qualification document from its source references before accepting it. The added `source_executions` therefore participates in the existing document equality/checksum and reference invalidation checks. Worker identity is retained evidence: an archived worker need not remain alive; PID reuse with a distinct birth time is permitted. Ordinary copied data remains inspectable without counting as a separate execution. This correction does not claim authentication against arbitrary wholesale fabrication of all records.

Fresh independent evidence:

| Check | Result |
|---|---|
| Focused `test_qualification.py`, with real-worker fixture replaced by disposable copies of retained corrected-WORK records | **40 passed**, exit 0, 0.38 s; no new workers or model trajectories |
| Exact unchanged directory copy | Bound as inspectable data, then rejected as duplicate execution |
| Full evaluator admission probe with duplicate run ID | Rejected before calculation |
| Full evaluator admission probe with duplicate worker PID/birth identity | Rejected before calculation |
| Full evaluator admission probe with duplicate manifest hash | Rejected before calculation |
| Literal unique 17-execution metadata | Reaches a deliberately raised calculation sentinel |
| Literal PID reuse with different birth time | Reaches the sentinel; valid distinct identity is retained |
| Existing altered/nonplotted artifacts, source/environment differences, source-run manifest epoch change, fixture-purpose rejection and literal numerical criteria tests | Passed within the 40-test focused run |

The independent evaluator probes use explicitly mocked bound-source loading and scientific identity only to isolate admission; they retain the actual slot validation and new identity gate. They stop at `calculate`, never complete the calculation, and create no qualification document. No fixture has scientific evidence authority. Exact scripts, logs and results are under `/private/tmp/apex-v02c-independent-review-2/` and summarized in `REPRODUCTION.md` and `review_record.json`.

## Final closure and readiness

| Requirement | Decision |
|---|---|
| C1 complete versioned actual source inventory at admission/consumption | Closed; iteration-1 evidence remains applicable |
| C2 applied-input and shared track/geometry aliases | Closed; iteration-1 evidence remains applicable |
| C3 independent integration coverage/process outcome/evidence/comparison meanings | Closed; iteration-1 evidence remains applicable |
| Accepted nominal/half/quarter profile admission and integer ticks | Prepared; no scientific refinement campaign executed |
| Accepted component errors/contraction/yaw separation/native sampled filters | Prepared and fixture-tested; no threshold amendment |
| Source/environment/artifact binding, publication/applicability/invalidation | Prepared; Q1 execution uniqueness now closed |
| Fixed 17-slot scope, serialized ownership/resource/native/disk/measurement safeguards, no automatic retry | Prepared; no execution launched |
| Canonical/V0.1/scientific preservation | Maintained at the reviewed correction; prior parity/lifecycle evidence remains scoped WORK evidence |

**No remaining blocking finding was found in this scoped review.** No further corrective iteration is required. The next task may execute the accepted fixed 17-trajectory protocol only after separate execution authorization, against this reviewed source identity with a fresh evidence directory. A later documentation-only delivery may retain this source review if all required code hashes remain identical; any relevant code/config/dependency change requires an applicability assessment and affected re-review.

Scientific limitations remain explicit: unmeasured synthetic parameters, unsaturated linear tires, provisional loads, ideal instantaneous steering, sampled interpretation filters and a quarter-grid numerical reference. A future passing campaign establishes only the accepted finite synthetic numerical/comparison qualification. It does not establish physical truth, a real-vehicle envelope, continuous-time safety, actuator feasibility, hard real-time performance or controller capability. Failed, weak, partial and inconclusive future evidence must remain retained without favorable reruns or tuning.
