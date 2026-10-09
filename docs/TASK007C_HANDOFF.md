# APEX handoff — Task 007C stopped at mandatory reproduction gate

> Historical gate-stop record. Task007C-R subsequently passed; resumed C1–C4 results are in [TASK007C_RESUMED_RESULTS.md](TASK007C_RESUMED_RESULTS.md), with current status in [CODEX_HANDOFF.md](CODEX_HANDOFF.md).

Task007B is accepted. The Task007C source brief is
`/Users/marwansaber/.codex/attachments/f3aef931-588b-4af1-be06-3450fc5a54cf/Pasted text.txt`.
Prior completed handoff: `docs/TASK007B_HANDOFF.md`.

All six measured anchors and one additional unchanged repetition each of E/F have finished.
No measured benchmark is running. C1–C4 must NOT start: the user's prerequisite says
“Do not continue if the rejected oscillatory cases cannot be reproduced.”

E original sweeper heading TV 6.328775 rad and rate-limit time 2.35 s; first/repeat
TV 0.280870/0.282400 rad and rate-limit time 0/0 s. F original predicted slack
0.0274713 m and minimum physical clearance 0.0600955 m; first/repeat slack about
9.09e-11 m and clearance 0.109151/0.095736 m. Both attempts fail to reproduce these
specific rejected behaviors. This does not establish that the high-demand cases are safe.

No Task007C runtime/controller/plant/TVLQR changes. Baseline preservation verified before work:
259 Task007B source files, 675 artifacts. Final checks are in `anchor_provenance.json`.
E/F match original runtime, fixtures, configuration, native settings and startup states/controls.
A's original early B0 predates the additive speed-polynomial loader, explicitly documented in
Task007B provenance; this inherited source difference must remain disclosed. B–F match exactly.
Measured latency traces differ; causation remains unresolved, not proven to be timing alone.

Task007C additions are offline metrics, anchor/repeat drivers, comparison/sector plots, provenance
checks, five arithmetic tests and documentation. All eight cases pass physical-time chronology
checks (`results/task007c/verification.json`) and telemetry completeness checks
(`export_verification.json`). Full project regression: **505 passed in 653.71 s**; whole-repository
Ruff check and formatting of the new files pass. No tests or numerical analysis ran concurrently
with measured anchors. All processes have finished.

Offline analysis and metric exports cover all eight cases. Figures: eight full-trend anchor
reviews, eight sideslip relationship plots, one anchor comparison, six E/F sector zooms and
one extra F long-straight zoom (24 PNG files). The latter exposes the original F slack peak
at progress 13.584 m before the hairpin. All paths: `results/task007c/ARTIFACT_INDEX.md`.
These are anchor reviews, not the unexecuted C1–C4 experimental dashboards or maps.
Final gate decision: `results/task007c/reproduction_gate.json`.

Read `docs/TASK007C_RESULTS.md` and `docs/TASK007C_REPRODUCTION.md` for outcomes/commands.
ADRs147–152 record the authorized protocol and stop decision. The current source and result
hashes are retained in `results/task007c/provenance.json` with `source_snapshot.zip`.

Recommended next step: obtain an agreed controlled reproducibility protocol, potentially
recorded-latency replay alongside measured repeats, before revisiting the gate. This is only
a recommendation; no replay mechanism or additional study has been implemented. Do not
claim timing alone caused the mismatch, Task007C is complete, or Task007D is ready. Do not
change TVLQR, Planning, plant, alpha weights, terminal DARE, horizon or progress scheduling.
No subagents authorized. The brief requires a 48-section final handoff.
