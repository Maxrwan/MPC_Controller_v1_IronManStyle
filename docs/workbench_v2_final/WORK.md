# V2 final replay and full-lap WORK

Starting delivery `e45059cb0fff41a8610761e83bdd69c4a2dff1e2`, branch `codex/workbench-v2-ui`.
Primary accepted the presentation foundation at `b1cc8b3d7b306a56adf99a63d8dc689c13856114` and
[authorized these corrections and one conditional full-lap attempt](PRIMARY_WORK.md).
Frozen scientific source remains `48adbdf64d492592d15e23c917aca71fa58aa8a5`.

**Independent Engineering Review PASS** for `740a268a2d2c6b92a67a45456292a3b2cafb2479`;
[report](../reviews/workbench_v2_final/iteration_1/REVIEW.md). Independent105pass/1deselected,
2,847 JS checks and8,005 additional assertions; counts remain separate. No correction requested.
All review/test/UI/helper activity has ended. No new scientific execution has started.

## Implemented scope

- Whole circuit / recording window retain their meaning; Follow Vehicle smoothly translates the
  camera and Follow Prediction frames only the genuinely available active packet. Display-camera
  smoothing never changes positions, telemetry, timestamps, packet identity or measurements.
- An illustrative wheel replaces the tire glyphs. Actual applied front delta remains the latest
  application event, with native held initialization before the first event. Radians/degrees display
  the front command; visual wheel rotation is `ratio × delta`, default12:1. The optional nominal is
  the native tracker nominal belonging to the applied request. Ratio is client-only, explicitly
  passenger-car-style illustration, never steering-column/RC-servo calibration or a command change.
- The Prediction Microscope renders all9 retained N8 state nodes and8 native control intervals;
  terminal node8 has no invented command. Selection enlarges numerical state/control/error details;
  all-node/selected-node labels and optional heading radians are available without pausing live
  active-packet updates. Historical inspection remains labelled and has no active authority.
- Derived reference nodes call the **original** pinned `PlanningReference.sample` at each predicted
  unwrapped progress, then canonical `frenet_to_global` and `wrap_angle`. Errors are exactly
  `e_y - e_y_ref` and `wrap(e_psi - e_psi_ref)`. Reference, lateral connectors and world-heading
  glyphs are derived presentation data, not retained NMPC preview, actual-future prediction residuals,
  physical measurements or new scientific validation. Missing reference stays unavailable.
- A source-isolated read-only geometry process reuses the expensive canonical reference construction.
  It imports no controller/plant/simulation/CasADi modules. Existing import/hash guards and complete
  approved dependency checks remain. Captured inputs plus helper hash key a bounded immutable cache;
  runtime hashes are checked before projection/cache use and after new calculations. Parent birth
  ownership, timeout and exit cleanup protect the helper; it has no execution lease or solve path.
- One next native window is prefetched read-only. Full evidence checks surround preparation and
  publication; current/next transport remains bounded. At the boundary, playback waits for a verified
  window and resumes at the identical overlapping native timestamp and prior rate. No simulated
  time is added while waiting. This is automatic continuation, not a gapless/network-time guarantee.

## Resource and admission correction

Only Full Lap's wall/CPU values change: **900s /720s**. Extended, V1,768MiB RSS,256MiB full-lap output,
4MiB single-file,80s simulated ceiling, two-crossing termination and frozen mathematics stay fixed.
The conservative original pilot projection remains: wall588.889137s, CPU551.42816s,
RSS270,616,848bytes, output112,568,912bytes. It now fits the authorized Full Lap limits.

A narrowly checked retained-profile path admits the exact historical profile **for reading only**
when the entire current profile differs solely by those two authorized cap fields. The original
pilot request/profile/manifest/producer hashes remain unchanged; new execution strictly requires
current profile identity. No old request is rewritten or resumed. Comparison classification is not relaxed.

The policy installer requires a new exact independent PASS, current/Git producer equality and
unchanged historical review/Primary/pilot provenance. It copies the exact previous policy, binds
new authority to reviewed source/current profile/Primary brief, preserves the consumed pilot and
unused full slot, and permits only that new full-lap slot. Every subsequent WORK admission verifies
prior-policy bytes and preserved history. Current UI uses the live budget/admission rather than the
old480s historical decision as a permanent blocker. A pending acceptance proposal explicitly cannot
activate accepted-interactive execution.

The once-only driver requires no previous claim or spent full slot, fresh source and complete
approved-environment checks **before** claim/consumption, unchanged shared lease/worker ownership,
and the original full-lap host floors: more than2×768MiB available RAM;1GiB+2×256MiB free disk;
no competing benchmarks/UI/reference processes or active measurement guards. No pilot-only reserve
relaxation, capacity polling for a favorable sample, source bypass or numerical retry is introduced.

## Focused evidence

Raw evidence: `results/apex_workbench_v2_final/`; exact commands/hashes in `work_record.json`.
Final focused invocation: **105 passed,1 deliberately deselected,0 failures/skips,29.09s**. It covers
new display/admission, prior V2 lifecycle/cancel/source-integrity tests, UI and original replay.
The unchanged native configuration-composition subprocess was deliberately not rerun. No broad
scientific Verification, qualification campaign or extra optimizer/plant experiment occurred.
Pure JS:2,847 display assertions over scalar fixtures and genuine pilot states/packets.

Retained negative attempts: initial read-only projection rejected a symlink-spelled interpreter
identity; resolving the existing venv root fixed the path without bypassing environment checks.
The first focused test invocation had99 passes/4 fixture-registration setup errors; those harness
imports were corrected. Separate intermediate103 and104 pass invocations are not added to105.
An initial cold read-only projection measured12.945s: bootstrap2.757s, canonical geometry8.012s,
node projection1.731s. Geometry reuse and bounded prefetch address repeated initialization; initial
cold construction remains noticeable and has a visible preparation spinner.

Actual IAB1440×1100 /390×844 observations: four camera views, actual/nominal wheel and12→6→12
visual ratio,9 nodes/8 controls, terminal absence, degrees/radians, live node selection without pause,
active handoffs, historical packet99 at0.125s retaining authority packet0 and applied0.0200274959rad.
Genuine pilot replay advanced9.87s in9.8863wall s at1×;219 painted frames/max233.3ms gap during
tool-controlled inspection. Do not infer hard frame-rate or real-time guarantees from this sample.
A labelled two-window transport fixture (repeated retained samples, shifted clocks, not a scientific
trajectory/archive) automatically continued; its second window advanced9.995fixture s in5.0033wall s
at2×,113frames/max50.1ms gap. Both payload loads and the epoch change were observed; no simulated
time accrued in the verified boundary pause. A removed required file in a **disposable copy** withdrew
the iframe and displayed quarantine while the original archive hash remained unchanged.

## Remaining gate and limitations

Independent review of the exact committed source passed before live admission and the single
baseline Full Lap attempt. During this WORK phase the historical production access policy remains
unchanged/stale. No claim is reset, no pilot repeated, no full lap yet claimed, and no repeatable
V2 policy installed. Cold reference initialization can take about13s; boundary pauses are possible.
The camera is a display aid; heading-glyph lengths and wheel ratio are illustrative. Planning reference
reconstruction does not fabricate native optimizer preview. Browser viewport emulation is not a
physical-mobile or accessibility certification. Local logs/screenshots are not off-host archival backup.

After PASS: terminate review/tests/UI/helpers; install the explicitly bound WORK policy; take one
host/source preflight and attempt the baseline full lap once. Preserve the genuine outcome. Only if
completed/valid/exit0 with one full native circuit, prepare a pending source-bound acceptance proposal;
do not install it. Final stop: `WORKBENCH_V2_FINAL_READY_FOR_PRIMARY_ACCEPTANCE`.
