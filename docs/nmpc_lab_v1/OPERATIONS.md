# NMPC Lab V1 — acceptance and operational finalization

**PRIMARY_ACCEPTED_FINALIZATION_PENDING_FOCUSED_REVIEW.** 10 November 2026. Branch
`codex/nmpc-lab-v1`, starting delivery `6e2d3b7009b637a8f67ec49b326a29c32bff2aa0`.
[Primary decision](PRIMARY_ACCEPTANCE.md), [acceptance record](acceptance_record.json).
The laboratory/UX source remains accepted447cc1e; only checkout-environment resolution in the
launcher, an ignore rule and deterministic test fixtures change. No scientific implementation changes.

The old WORK policy correctly rejected current source: its panel hash was25f8b7…, while accepted
447cc1e has ea0820…. All other14 producer hashes are identical. Each current producer was compared
with exact Git447cc1e. The original Engineering Review8ee2 and UX Review447cc1e PASS records were
matched to their original Git-delivery bytes and copied unchanged into the local acceptance bundle.
Primary's hashed acceptance record binds both reviews, frozen48adbdf, executionaf3956, the current
15-producer map, original case/used identities and resource limits. The existing access parser is
unchanged: current files must match the policy and exact reviewed Git source, final UX review and
explicit Primary-record hashes. No verification is skipped or weakened.

The existing policy alone transitioned to `accepted-interactive`. Its exact predecessor628a6199…
is retained in `results/apex_workbench_nmpc_lab_v1/operational_20261110/previous_access.json`.
All three historical consumed IDs, cases and original grant remain unchanged. Ordinary explicit
user-triggered runs may use the existing eight costs/fixed disturbance/current2s GP gamma2 profile.
They remain experimental/unqualified; no frozen Performance configuration is overwritten. There
is no sweep, background runner, automatic retry, new scenario, exporter or deployment work.

The normal `Launch_APEX_Workbench.command` is checkout-relative. This configured checkout shares
the existing approved tool environment using a local ignored directory symlink. The launcher
resolves that directory, retaining its venv interpreter instead of resolving the binary to bare
Python. This preserves the original environment identity. No dependencies were installed/changed.
Launch it from the accepted branch checkout:

```sh
./Launch_APEX_Workbench.command
```

Or double-click the file in Finder. Open <http://127.0.0.1:8501>. Keep its Terminal open; Control-C
stops the owned server. A second launch reuses that checkout's server. Other checkouts/branches are
not silently selected. A different checkout needs its own correctly provisioned acceptance/runtime
files and approved environment; copying arbitrary approval files is not setup.

Focused software:42passes,0failures/errors/skips,9.71s. Scientific imports, workers and probes were
blocked; only read-only metadata and disposable Git fixtures were permitted. Tests cover repeatable
admission without changing historical consumption, tampered/missing acceptance/review/source/Git
rejection, bounded configuration, standard navigation/comparison and versioned drafts. The old
disabled-gate test now explicitly models an unaccepted fixture instead of relying on production
remaining unaccepted. A strict preparation audit caught that planned test-only delta before any
policy write; it is recorded separately from runtime/source equivalence. Test formatting records
were finalized before review; predecessor prepared bytes remain retained.

The actual normal launcher started from `/private/tmp`, served loopback8501 from this checkout
using the canonical approved venv, and a second invocation reused its owned listener. Interpreter
and10 installed dependency RECORD trees match the frozen approved numerical environment.

Next: focused independent exact-candidate operational review. Only following PASS may the agent
make the single authorized baseline2s smoke attempt, through interactive admission, with no retry.
No broad Verification campaign is authorized. Logs, policy transition/provenance and preservation
anchors are under `results/apex_workbench_nmpc_lab_v1/operational_20261110/`.

On completion stop at `NMPC_LAB_V1_ACCEPTED_FOR_SYNTHETIC_EXPERIMENTATION`.
