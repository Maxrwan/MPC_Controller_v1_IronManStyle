# Acceptance-metadata correction after the successful smoke

The sole genuine baseline 5 s smoke at source `3ccf294e28e2f213ef9d269333d2700f2ee37522` completed
with valid evidence / exit 0: 1,000 states, 500 controls, 50 packets, normal matching summary/worker result,
27.1881254 s supervisor runtime and 208,699,392-byte sampled peak RSS. Its exact end time is
`4.999999999999915`, native stop reason `duration`, coverage completed. No simulation was repeated.

The finalization metadata guard incorrectly required literal equality to 5. The canonical runner
already applies its accepted stopping rule; no scientific tolerance, clock or archive is changed.
The guard now requires the successful canonical duration outcome and exact agreement between the
retained raw end time and summary end time, preserving the original floating representation.

Only `lap/operational.py` changes among the 49 producers. Within that module, the existing changes
are confined to accepted authority validation and final installation; conditional worker-validation
functions and the authority prefix are AST-identical. The 48 other producers, 333 frozen scientific
files and 335 canonical/dependency files remain unchanged.

The smoke retains its original execution source/review/policy/claim and all 26 manifest artifacts.
A final accepted revision must have a new exact independent PASS explicitly declaring the old smoke
execution revision, final accepted revision, sole changed producer and acceptance-metadata-only
classification. Code verifies that declaration and all 48 unchanged producer hashes; broader changes,
missing declaration or altered review fail closed. Final acceptance separately binds the immutable
original conditional policy and both producer identities; it never reseals or relabels the smoke.
No old policy, claim, history slot, summary or execution evidence is rewritten.

All 38 metadata policy tests passed in 30.57 s, including native end-time roundoff and explicit source
compatibility/rejection cases. This is a correction iteration within the same narrow policy review,
not another numerical experiment, broad review or Verification. Correction review PASS at `5d88a54`
explicitly approved compatibility; final source/evidence checks passed and accepted-interactive was
installed, preserving both source identities. The normal smoke Replay/Analyze was observed; its
playback ended at the genuine 4.995 s last state with active packet 49 and nine nodes.
