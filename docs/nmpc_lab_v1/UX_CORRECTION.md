# NMPC Lab V1 — playback and user-acceptance correction

**NMPC_LAB_V1_UX_READY_PENDING_PRIMARY_USER_ACCEPTANCE.** 10 November 2026. Branch `codex/nmpc-lab-v1`, base
`a7cdc334d76f42ce589e217cd3fb9a7543744b9b`. Exact implementation `447cc1e60c064062c75f879c3c67e611a84cff31`
received focused independent **PASS**, with no unresolved blocking finding.
[Review](../reviews/nmpc_lab_v1/ux/REVIEW.md), [record](../reviews/nmpc_lab_v1/ux/review_record.json).
This containing delivery changes documentation only. This is presentation/read-only replay WORK only.
The scientific worker and three completed af3956 executions remain unchanged; the three slots
stay consumed and repeatable Scratch execution is not enabled.

The old fragment advanced5ms every400ms:0.0125×, or80× slow before Plotly/table rebuilds.
The replacement is a small self-hosted Streamlit component using elapsed browser time and Canvas2D.
It is a recorded-data viewer, with no model, optimizer, controller or scientific scheduler. The
read-only Bench35f6fa5 (`web/app.mjs`, `engine.mjs`, `canvas.mjs`) supplied interaction/cadence ideas;
no N=4 model, vendor runtime or scientific interpolation/metrics were imported.

Play/pause, restart, previous/next native sample, native-index timeline and0.25/0.5/1/2× rates
operate in the browser. Rendering is capped at30fps, readouts10Hz and optional plots5Hz. Actual
cadence is measured, not guaranteed. Canonical global positions may interpolate for the marker
only; known instantaneous kicks are held then jump. State readouts, commands, packet IDs, metrics
and solver nodes remain native. Applied commands use their original application clocks and ZOH
display; requests remain separately timestamped. No missing events or endpoint state are filled.

The default horizon follows the recorded native active ID/mode, with actual completion, validity
and horizon coverage checked. Manual historical inspection is visibly separate and does not
confer authority. Terminal node8 has no command. Current state/held command appear beside the
vehicle; tracking plots and scheduling/solver diagnostics are on demand. Existing Analyze remains
native-sample scientific postprocessing, unaffected by display interpolation. Repetitive Scratch
warning banners become `Synthetic research mode · Not physically qualified`; real errors and
historical M5-A/C0 restrictions remain visible.

One presentation operation parses verified buffers and builds a reduced display payload. After its
acknowledgement the browser retains it; Python sends epoch/validity/nonce heartbeats, not the whole
recording every animation frame. Captured hashes are checked before and after each1s heartbeat.
A changed/unavailable member unmounts the component and latches quarantine until explicit reopen.
The browser clears its payload after4.5s without validation. This is a bounded display freshness
policy, not instantaneous tamper detection or a real-time scientific guarantee. Navigation removes
the component; hidden pages pause, and recording end stops without extrapolation.

Focused software:18passes/0failures/errors/skips in6.10s, no scientific imports/subprocess execution
except read-only Git/platform metadata. Separate JS fixture checks:11passed, including native
authority, command clocks, interpolation exclusions and an animation-frame timestamp preceding
the Play event. That last case initially backdated the wall anchor (.02s instead of.01s); the
regression and negative observation are retained. Earlier harness guard/bare-fragment failures,
the temporary-container mount issue and identical-heartbeat elision remain recorded separately.
No broad suite, numerical experiment or formal Verification was run.

Final real-browser measurements on exact447cc1e over the retained1.995s sample window:

| Speed | Ideal wall s | Observed wall s | Deviation ms |
|---|---:|---:|---:|
|0.25×|7.9800|7.9882|+8.2|
|0.5×|3.9900|3.9926|+2.6|
|1×|1.9950|2.0081|+13.1|
|2×|0.9975|0.9992|+1.7|

Each speed was observed once on the final clock. The two-second run plays in approximately two
wall seconds at1×; the unrecorded endpoint is not invented. Paint counts23/46/89/180 and maximum
50.6ms gap describe this local browser only. Payload load stayed1 across heartbeats. Initial
four-speed measurements before the first-frame anchor fix remain separate historical observations.

Actual browser checks confirmed native steps0↔.005s, seek0.200s/index40 and1.995s/index399, pause,
restart/end, active packet0 versus manually inspected future packet10, and terminal node8/NULL
command. A switch during playback starts the selected baseline paused at zero and resets the
historical selection. Navigation to Analyze removes the iframe. Visible position/horizon captures
at native0 and.800s match the source, with packet8 active at.800s.

A disposable copy's same-size/restored-mtime byte change removed replay. Restoring bytes did not
clear the latch; explicit reopen started paused at zero. Stopping its validation service cleared
browser data/image under the4.5s lease/250ms poll policy; Streamlit's connection modal initially
obscured the cleared view and was dismissed for inspection. Detection latency was not qualified.
Both owned servers/tabs are closed, ports8517/8518 refuse connection, the shared lease is free and
no owned scientific worker remains. Evidence/logs are under
`results/apex_workbench_nmpc_lab_v1/ux_correction_20261109/`.

Separate independent evidence:11 Python tests passed in4.881s,11 pure JS checks passed, and a
three-recording audit checked1200 native states/600 request/application rows and input immutability.
Parent18passes are not added to those counts. A changed legacy display-fixture test also passed
separately in2.17s using retained source-bound configuration metadata, without another native probe.
Reviewer setup/path/assertion negatives and the parent's initial M5-link-root audit mistake are
retained; corrected checks pass. No scientific execution or formal Verification occurred.

All6393 protected regular files,324 historical links, primary56/345/25/4 groups, originalC0 and333
frozen runtime members match. Scientific/worker/profile/analysis/scheduling differences from the
UX base are empty. Original8ee2 renderer findings/captures/review remain unchanged. All three
genuine execution references remainaf3956, with unchanged access policy and no remaining allowance.

Remaining UX limits: reopening starts paused at the first sample; navigating back to Inspect uses
its existing catalog selection/default, without position persistence. Background/hidden pages pause;
browser scheduling can reduce frame cadence. Canvas2D and timings were checked in the local embedded
browser, not qualified across platforms. Detailed local native diagnostics remain descriptive,
not physical validation, controller real-time guarantees or nonlinear/hybrid stability proofs.
Raw ignored evidence remains local; published hashes do not create off-host artifact retrieval.

Next: Primary user acceptance of exact447cc1e within this bounded UX/software scope. Repeatable
Scratch execution remains disabled. Stop at
`NMPC_LAB_V1_UX_READY_PENDING_PRIMARY_USER_ACCEPTANCE`. No numerical experiment, automatic acceptance,
exporter, ROS2, Docker, hardware, expansive Verification or unrelated stage is authorized.
