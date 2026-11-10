# Workbench V2 UI — independent Engineering Review, iteration 1

**PASS WITH CONDITIONS** for exact candidate `cfe1b44081be4acb5ba606063819a7c138dfdd75`
on `codex/workbench-v2-ui`. This is a focused Engineering Review of presentation and UX,
not formal Verification, Primary acceptance, or scientific execution authorization.

Base delivery: `afa85389ccdb532816702f0ab5d3a4a49e54918f`. Reviewed preceding implementation:
`fdd494eb7ddf9b456b88cba243fbc704a4fd83c0`. Frozen science:
`48adbdf64d492592d15e23c917aca71fa58aa8a5`. Initial tree was clean; branch, HEAD and
`Maxrwan/MPC_Controller_v1_IronManStyle` remote were checked directly. Fresh reviewer context
was used; primary test counts were not treated as independent proof.

## Findings and conditions

**V2UI-ER1-01 / P2 — preserve missing observations as gaps in Analyze traces.**
`tools/apex_workbench/lap/ui_views.py:345` removes rows with an unavailable selected value
before reduction and emits a `mode="lines"` trace. Reproduce without any scientific runtime:
call `plot` with `[{"time":0,"value":1},{"time":1,"value":null},{"time":2,"value":3}]`
and inspect the figure passed to `theme.chart`. Its x/y arrays are `[0,2]` / `[1,3]`;
the line bridges the unavailable observation. This matters for optional solver/iteration and
other missing channels even though numerical metric missingness remains intact. Retain explicit
gaps through display reduction and add a focused check that the reduced trace cannot connect
across missing rows. Submit the resulting exact commit for focused re-review.

**V2UI-ER1-02 / evidence note — refresh the candidate display projection with traceable hashes.**
The supplied `results/apex_workbench_v2_ui/pilot_display.json` matches current states, controls,
packets, geometry, reference and coverage exactly, but has `meta.sectors=[]`; the candidate adapter
now supplies four explicitly incomplete sector records. No complete sector or scientific value
differs. Identify the older export as an earlier display projection and retain its hash when a
fresh read-only candidate export is added. This is an evidence applicability condition, not a
historical scientific-artifact defect.

No other blocking defect was found in this focused scope. Conditions above require an exact-revision
follow-up; this review must not be relabelled as a review of a later implementation.

## Independently checked behavior

- Front steering uses the latest actual `application_time` event, then the initial native held
  angle before any application; the tracker nominal stays separate and optional. The 0.125 s
  retained application is `0.020027495934949978` rad, with nominal `-0.003984999314297534` rad
  from request time 0.12 s. These are retained values, not hardware measurements.
- Native instruments remain held at recorded samples. Only XY marker position interpolates,
  holding across a documented kick. Active identity requires native trajectory mode, the recorded
  plan ID, valid packet, reached completion and horizon coverage. Manual/future packet inspection
  stays explicitly historical and does not change authority or applied steering.
- Track phase, complete-lap count, last complete native interval and first-circuit sectors use
  distinct clocks. The partial launch crossing is excluded. Progress seek selects a genuine
  sample and rejects nonmonotone progress. SI labels separate Fx/m from derived body acceleration.
- Native windows overlap by one sample, preserve observations and stop at the selected boundary.
  The 4,096-state, 512-packet and 8 MiB limits reject unsupported payloads. Playback remains
  browser timed; no per-frame Python transmission or new scientific resampling was introduced.
- Pre/post-render artifact checking, one-second rechecks, heartbeat loss clearing and the run-wide
  quarantine latch remain. Renderer/window identity participates in the epoch. No checksum cache
  or evidence-policy relaxation was found. V2 source admission remains stale and disabled.
- Comparison reuses original eligibility functions and complete native metrics; noncontrolled
  conditions remain labelled, and differently weighted raw objectives are not ranked.
- The Transient form produces the exact original V1 schema and validators; its accepted V1 policy,
  capture, execution lease, source/environment checks and worker remain unchanged. Navigation
  alone performs no probe or run. Its available two-second V1 route does not admit extended/full-lap
  V2 work: switching back to Extended still fails the V2 source gate. New UI files are bound in the
  V2 inventory; the V1 inventory is intentionally the original V1 execution contract, not a claim
  that the new UI is part of the old reviewed V1 presentation. No execution button was pressed.

## Independent checks and preservation

Approved Python: `tools/apex_workbench/.venv/bin/python3.12`, Python 3.12.14. Command:

```text
PYTHONDONTWRITEBYTECODE=1 tools/apex_workbench/.venv/bin/python3.12 -B -m pytest -q tools/apex_workbench/tests/test_lap_ui.py tools/apex_workbench/tests/test_lap_v2.py tools/apex_workbench/tests/test_scratch_replay.py -k 'not source_isolated_configuration' --basetemp=/private/tmp/apex-v2-ui-review.uRcNnd/pytest --junitxml=/private/tmp/apex-v2-ui-review.uRcNnd/pytest.xml
```

**83 passed, 1 deliberately deselected, 0 failures/skips, 8.99 s.** The unchanged native
composition probe was not imported/executed by this selection. Separately, 11 reviewer-authored
UI/admission/payload checks passed with run/probe entry points replaced by forbidden sentinels;
no controller, plant or simulation modules were imported. Independently authored JS checks passed
**56,027 assertions at 8,000 retained native/request/application clocks**, using linear-search
oracles plus display-only discontinuity/lap/sector/progress/rate fixtures. Counts are not combined.

After the checks, an independent read-only audit reproduced preservation of **13,279 files and
573 links**, with no additions, deletions or changes in the retained V1/M5/V2 roots; all **333**
cached scientific dependencies, **334** canonical source/config/dependency files, V1 producers and
the V2 execution core matched their pinned sources. All **43** current producer hashes matched
the candidate's work record; HEAD remained the exact candidate above.

Temporary raw logs/scripts/hashes are indexed by `review_record.json`. Two harness/environment
attempts are retained: an initially overstrict whole-payload equality check exposed the incomplete
sector projection difference above; the initial JS command found no `node` on PATH and was then
run with the discovered bundled Node executable. Neither was a product/scientific retry.

## Visual flow inspected from supplied evidence

The primary's screenshots were opened and inspected directly, with provenance retained as primary
evidence. The reviewer's IAB surface returned `Browser is not available: iab`; no independent live
capture or fallback-browser run is claimed. Files below are under the local ignored
`results/apex_workbench_v2_ui/screenshots/after/` directory, not an off-host backup.

| Step | Screen / supplied capture | General health |
|---|---|---|
| 1 | Configure — `04-configure-desktop.jpg` | Clear eight-field form, fixed-profile context and draft/run distinction. |
| 2 | Run — `05-run-gate.jpg` | Source/resource failure visible; V2 button disabled. |
| 3 | Replay — `01-replay-desktop.jpg`, `02-replay-mobile.jpg`, `03-instruments-mobile.jpg` | Track/instrument hierarchy, native/application labels and mobile reflow are readable. |
| 4 | Analyze — `06-analyze-desktop.jpg` | SI/native metric labels are clear; missing-trace finding above remains. |
| 5 | Compare — `07-compare-desktop.jpg` | Selected recordings and experimental/unqualified eligibility are visible; no winner score. |
| 6 | Bounded transport — `08-long-transport-fixture.jpg` | Explicit software-fixture label and selected-window coverage; no scientific lap claim. |
| 7 | Heartbeat loss — `09-heartbeat-quarantine.jpg` | Cleared replay and visible recheck failure beneath the connection error. |

Labels, focus styles, native controls and text readouts support accessibility, but screenshot/source
inspection does not establish keyboard, screen-reader, zoom or WCAG compliance. No genuine full lap
or V2 treatment pair exists; complete-lap/sector semantics have only bounded software fixtures here.
No controller/probe execution, simulation, campaign, numerical acceptance, broad suite, policy reseal,
claim reset, deployment, Docker or hardware work ran. The 551.42816 s CPU projection versus the
unchanged 480 s cap remains blocked. Stop at Engineering Review; Primary UI acceptance and any
future execution authority remain separate.
