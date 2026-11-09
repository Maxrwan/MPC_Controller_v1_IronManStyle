# NMPC Lab V1 — playback and user-acceptance correction

**WORK_COMPLETE_PENDING_REVIEW.** 9 November 2026. Branch `codex/nmpc-lab-v1`, base
`a7cdc334d76f42ce589e217cd3fb9a7543744b9b`. The containing implementation is the candidate for
one focused independent Engineering Review. This is presentation/read-only replay WORK only.
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

Browser validation and final independent disposition are being recorded in
`results/apex_workbench_nmpc_lab_v1/ux_correction_20261109/`. The initial four-speed measurements
precede the first-frame monotonic-anchor fix; they are retained and will not be presented as fresh
final-source results. Original8ee2 blank-WebGL/SVG evidence and reviews remain unchanged.

Next: finish focused real-browser acceptance, review the exact final source and publish the bounded
handoff. Stop at `NMPC_LAB_V1_UX_READY_PENDING_PRIMARY_USER_ACCEPTANCE` after success. No numerical
execution, acceptance, exporter, ROS2, Docker, hardware or unrelated Workbench work follows.
