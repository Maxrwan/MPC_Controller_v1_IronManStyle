# Workbench V2 UI — focused independent re-review, iteration 2

**PASS** for exact correction candidate `b1cc8b3d7b306a56adf99a63d8dc689c13856114`
on `codex/workbench-v2-ui`. Both iteration 1 conditions are closed. No additional actionable
finding was identified in this bounded correction review. This is Engineering Review of the UI,
not formal Verification, Primary acceptance or new scientific execution authority.

The tree was initially clean and HEAD was checked directly. The exact source delta from
`cfe1b44081be4acb5ba606063819a7c138dfdd75` is the new `ui_data.trace` helper, its use by
`ui_views.plot`, and four regression cases. Other changes are documentation. Native replay JS,
payload construction, validators, admission, execution, comparison, scientific source and retained
evidence are unchanged. The original [iteration 1 review](../iteration_1/REVIEW.md) and machine
record retain their exact earlier hashes.

## Condition disposition

**V2UI-ER1-01 — CLOSED.** Missing/nonfinite values or clocks now produce explicit `None` plot
breaks; Plotly receives `connectgaps=False`. The helper inspects every original row for missingness
before reducing genuine points, so an unselected missing row still breaks the displayed segment.
It preserves source data, first/last selected observations, at most 2,000 genuine points and a
conservative bound of 3,999 array entries including break markers. A `None` is a display break,
not a fabricated measurement. Full-record metric calculation is unaffected.

**V2UI-ER1-02 — CLOSED.** Both projection files remain, with independently verified hashes:

| Local display projection | SHA-256 |
|---|---|
| `results/apex_workbench_v2_ui/pilot_display.json` | `55491133b658448eb16e839f216aa692390c05542939f05871812675159d9401` |
| `results/apex_workbench_v2_ui/pilot_display_cfe1b44.json` | `928def66422d70292c740a51105d232efd00576a3fa291585fe264d349a6ce91` |

`display_projection_reconciliation.json` binds those exact bytes. States, controls, packets,
geometry, reference, coverage and other metadata are identical; only four incomplete sector
records replace the earlier empty metadata list. The refreshed projection also equals a fresh
read-only payload from the exact correction candidate. Its `cfe1b44` filename remains accurate
because the correction changes trace preparation only. No scientific artifact was modified.

## Independent correction checks

```text
PYTHONDONTWRITEBYTECODE=1 tools/apex_workbench/.venv/bin/python3.12 -B -m pytest -q tools/apex_workbench/tests/test_lap_ui.py -k 'optional_plot_missing_values or reduction_preserves_unsampled_missingness' --basetemp=/private/tmp/apex-v2-ui-rereview.QEFC0J/pytest --junitxml=/private/tmp/apex-v2-ui-rereview.QEFC0J/pytest.xml
```

**4 passed, 17 intentionally deselected, 0 failures/skips, 2.00 s.** Separately, reviewer-authored
checks passed **27,309 assertions across 144 scalar display fixtures** plus projection/source
applicability checks: clean, missing/nonfinite, entirely missing and unselected missing rows;
multiple reduction bounds; genuine-point identity; bounded arrays; no line spanning an unavailable
source row; input preservation; and invalid-bound rejection. No controller, plant or simulation
module was imported. V2 admission was rechecked and still rejects the stale source binding.

All 43 producer hashes match the corrected work record. All 15 copied iteration 1 raw artifacts
match their original recorded bytes/hashes. Unchanged iteration 1 native-clock, packet, quarantine,
Transient/V1 guard, comparison, transport and preservation evidence remains applicable after the
exact dependency diff above; it is inherited evidence, not a fresh run. The primary's separate
87-pass invocation was inspected but is not counted as this review's execution. Counts are not combined.

Raw scripts, logs and hashes are indexed in `review_record.json`; new raw files are under
`/private/tmp/apex-v2-ui-rereview.QEFC0J/`. No failed correction attempt occurred. No broad unchanged
suite or new browser check was run. The earlier unavailable IAB surface remains a platform limit;
the desktop/mobile flow observations remain the supplied primary evidence listed in iteration 1.

Only these two iteration 2 documentation files were written by the reviewer. No implementation,
historical evidence, policy or claim was changed; no run, probe, simulation, campaign, numerical
acceptance or hardware work ran. The manual replay-window boundary, absent genuine full lap/V2
treatment pair, blocked full-lap resource gate, stale V2 source policy and unqualified synthetic
status remain. Next decision: Primary user acceptance of the reviewed UI. This PASS does not
authorize policy resealing, another pilot/full lap, resource changes or any follow-on stage.
