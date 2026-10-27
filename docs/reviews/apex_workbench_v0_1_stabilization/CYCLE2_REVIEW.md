# Stabilization cycle 2 — independent-context technical review

**FAIL.** Reviewed exact `ca5c72fd255bd2b9511d891485087dc3174b9aea`.
Separate reviewer context: `stabilization_review`; no named external Secondary approval claimed.

Independent repeats closed S-R1/S-R2: malformed legacy status blocks admission while its real
legacy-command sentinel remains alive; a status replaced by `[]` before locked recovery becomes
quarantined/unknown. AppTest has explicit quarantine messages, zero exceptions/charts and preserves
the malformed bytes. A verified terminal supervisor conservatively blocks admission while alive;
the bounded probe admitted work after it exited without changing terminal-record bytes.

The root's additional genuine-copy receipt probe found a remaining C-R6 gap: deleting only the
manifest-listed `execution.json` rendered eight charts without any warning/error. This particular
probe was root-run, not independently repeated by the reviewer. The reviewer inspected the evidence
and agreed that it violates the explicit missing-manifest-listed-file invariant. No scientific
worker or historical record was modified by that probe.

| Area | Result |
|---|---|
| R1 | PASS |
| R2 | PASS |
| R3 | PASS |
| R4 | PASS |
| R5 | PASS WITH CONDITIONS — finalization mechanics pass; receipt consumption depends on R6 |
| R6 | FAIL — missing manifest-listed scientific receipt remains invisible |
| Launcher | PASS WITH CONDITIONS — unchanged source and applicable actual smoke |

Narrow required correction: before presenting a selected retained record, check that every
manifest-listed file is still present, while retaining selected-content hashing separately.
Add receipt deletion to the genuine-copy regression; no full-archive content read is needed.

Evidence: `results/apex_workbench_stabilization_20261028/independent-review-cycle2/` contains
`lifecycle-probe.json` and `followup-probe.json`; the root receipt observation is in
`root-receipt-probe/observation.json`. The complete 77-pass Workbench log/source identity was
inspected. The reviewer did not run a scientific suite or formal Verification.

Governance clarification: the reviewer found no sentence requiring an extra named/external human
authorization before already-delegated functional Verification. The user explicitly permits a
separate reviewer context and conditional Verification. That supplies authority after a technical
PASS; it does not claim named Secondary approval or Primary scientific acceptance. The general
rule that review is not automatic authorization still applies where explicit delegation is absent.
