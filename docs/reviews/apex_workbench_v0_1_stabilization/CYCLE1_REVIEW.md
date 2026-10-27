# Stabilization cycle 1 — independent-context technical review

**FAIL.** Reviewed exact `aeedf18e0df9b40ef7294ba15fc73e19b0d5884b`.
Reviewer: separate `stabilization_review` agent context with no implementing conversation history.
This is advisory technical review, not designated external Secondary/Primary approval.

| Area | Result |
|---|---|
| R1 lifecycle | FAIL — malformed legacy-status metadata can hide a live owner from admission |
| R2 publication/readers | FAIL — the in-lock status reread can raise AttributeError after replacement |
| R3 notes | PASS |
| R4 comparison | PASS |
| R5 finalization | PASS |
| R6 retained ingestion | PASS |
| Launcher | PASS WITH CONDITIONS — source/syntax and applicable smoke evidence inspected |

**S-R1:** A real disposable sleeping process used the legacy worker command contract. A status with
`state=running`, its live PID and malformed `evidence_state={}` was excluded by UI validation.
Admission then skipped the same invalid record before checking ownership and reached the review's
provenance interception marker. A readable-status control correctly rejected admission while the
same sentinel remained alive. The marker prevented publication or an actual second scientific worker.
Required correction: separate lifecycle ownership inspection from UI/evidence-field validity and
fail closed when an identifiable record's lifecycle cannot be read safely.

**S-R2:** A controlled interleaving returned a valid running status to `status_for()`, then replaced
the retained status with `[]` before `_reconcile_locked()` reread raw JSON. Both direct invocation
and AppTest raised `AttributeError: 'list' object has no attribute 'get'`. Required correction:
validate the status again inside the execution lock and quarantine malformed replacement data.

Independent passing probes: nine malformed/missing request/status variants; ten missing-artifact
cases including LQR controls and required JSON; genuine retained plots/controlled duration comparison;
optional never-produced dynamic controls; source/log hashes, numerical environment, applicable
218-plus-two test results and retained dynamic/LQR byte parity. Missing required exports produced
zero charts and invalid comparisons. Missing manifest-listed stdout/stderr produced explicit errors
while other verified selected telemetry remained usable.

The reviewer verified reconstructed first-run test source against its recorded hash: only the two
failing test bodies changed before their affected rerun. That supports reuse of 218 passes but does
not cover the newly reproduced lifecycle failures. No full regression/Verification or new scientific
campaign ran. The reviewer left the candidate and tracked working tree unchanged.

Raw independent evidence remains under
`results/apex_workbench_stabilization_20261028/independent-review/`:
`lifecycle-probe.json`, `lifecycle_probe.py`, `retained-probe.json`, `retained_probe.py`,
and `audit.json`. The next corrective revision must receive
its own exact-SHA review; this failed result remains historical.
