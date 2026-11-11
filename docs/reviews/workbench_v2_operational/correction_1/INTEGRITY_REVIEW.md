# V2 operational acceptance correction 1

**PASS** for `5d88a5478109d5ce93207170ceec60938a87e793`, against the original reviewed
and executed source `3ccf294e28e2f213ef9d269333d2700f2ee37522`. No blocking findings in
this bounded correction iteration of the same execution-policy/source-preservation review.
The initial review files remain byte-for-byte unchanged.

Independently compared all 49 current producers with both Git revisions. Only
`tools/apex_workbench/lap/operational.py` differs; the other 48 producers are identical.
An independent AST comparison confirms only existing `authority` and `activate` changed,
with `smoke_source_compatibility` added. All other existing functions, the conditional
authority prefix, and module imports/constants are AST-identical. The accepted-authority
branch and final installation metadata account for the production changes. No worker,
configuration, capacity, clock, scientific stopping rule or tolerance changed. All 335
canonical/dependency files and 333 frozen runtime files remain exact.

The sole genuine smoke remains the original run
`2026-11-11T160708.594424_0000_fe073e9a35714216accf3f91cc7cadae`, executed at `3ccf294…`.
Read-only ingestion verifies all 26 manifest artifacts and the pinned manifest
`f06539ea720ba0d25a49abffd7d07632e30558e7c3edc0f2a06fa65c648d5202`.
Status is completed/valid/exit 0, with 1,000 states, 500 controls and 50 packets. Summary
and worker result match; native stop reason is duration, failure is absent, coverage is
completed, and raw/summary endpoints agree exactly at `4.999999999999915`. This is a
successful canonical duration run; the former literal endpoint-equals-5 predicate was
an acceptance-metadata defect. This correction does not round or rewrite its data.

The final accepted policy must bind this final revision and a new exact independent PASS
containing the explicit compatibility declaration in this review's JSON. The new helper
rejects absent/mutated review permission, different producer membership, or changes outside
the single permitted metadata module. Final authority separately retains and hashes the
original conditional policy, checks the original claim/execution revision and producer map,
matches that policy to the captured admission, verifies genuine smoke success, exact endpoint
agreement and normal summary/worker result, then validates before publishing the live policy.
The old execution is not relabeled with the new accepted revision. The unchanged conditional
validation still prevents another smoke attempt.

The live policy is still the spent reviewed-smoke record, identical to retained
`policy_smoke.json`, SHA-256 `e8b98bc788c660c8c42d9d8337b205fea64f67eddd7a3d48cadfc002576002f8`.
The original historical policy remains retained at its exact `f9a0304…` hash. Of the original
811 file inventory, 810 files are unchanged; its sole difference is the previously authorized
live-policy transition, whose original bytes are retained. All 65 historical symlink targets
are unchanged, and original failed full-lap evidence/outcome remains intact. All 26
hash-referenced correction WORK artifacts match their recorded hashes and sizes.

My correction checks: **5 passed, 0 failures/errors/skips, 0.34 s**, selecting only
`test_post_smoke_compatibility_is_explicit_and_acceptance_only` and its five parameter cases.
They validate the allowed metadata-only difference and rejection of missing permission,
execution changes, producer membership changes and altered review bytes. No installer runs
in this selection. A fail-closed scientific-import guard remained active; no controller,
model, simulation or CasADi module was imported. No helper started; the test process exited.
The retained root correction suite is separately verified as 38 passed in 30.57 s; it is
not my execution and is not combined with my counts or the initial review counts.

This PASS explicitly declares the original smoke scientifically unchanged and compatible
with the final acceptance metadata revision. It permits final source/evidence checks and the
already conditionally authorized activation using the existing successful smoke. **No
second genuine numerical attempt is permitted by this review.** No production installer,
activation, worker/start/probe, solver, plant/simulator execution, archive rewrite, commit or
push occurred during this correction review. Scientific acceptance and physical/realtime
qualification remain outside scope.
