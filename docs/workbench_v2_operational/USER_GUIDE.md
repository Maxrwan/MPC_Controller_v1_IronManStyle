# Using the accepted V2 laboratory

Double-click `Launch_APEX_Workbench_V2.command` in this configured checkout, or run
`./Launch_APEX_Workbench_V2.command`. Open `http://127.0.0.1:8503` if needed. Keep its Terminal
open; Control-C stops only its owned server. The launcher resolves its own checkout and existing
Workbench environment; it installs no software or authorization files.

1. **Configure:** choose Transient (existing V1,2s), Extended (5/10/20s), or Full Lap (two native
   crossings,80s maximum). Edit the eight cost multipliers and optional fixed disturbance. Save
   a versioned draft with a distinct configuration ID/version; frozen Performance is never overwritten.
2. **Run:** review the selected weights, duration and resource limits. Run starts only on your click.
   Source/authorization mismatch or another worker blocks execution. Full Lap checks available
   RAM and disk once for that launch: each must exceed1,610,612,736bytes. The UI and read-only
   reference viewer may remain open. Free resources and click again yourself if a preflight fails;
   there is no automatic retry or queue. Available host memory is not guaranteed.
3. **Replay:** select a retained recording or the newly started run. Refresh active status as needed;
   cancellation retains its outcome. Completed data opens the existing cameras, actual steering,
   active packets, nine-node prediction microscope and verified native-window continuation.
4. **Analyze:** inspect tracking, actuation/grip, solver/events, predictions and recorded lap/sectors.
   Overview metrics cover the full native recording; recovered circuit-specific metrics are labelled.
5. **Compare:** choose two V2 runs. Use the same duration/scenario/initial state/scheduling/source for
   baseline-versus-weight comparisons. Different coverage or conditions is noncontrolled; raw objective
   totals with different weights do not rank controller performance.

Every experiment has its own ID, captured configuration/source/environment, finite resource profile,
outcome and evidence. Manual experiments do not consume historical pilot/full-lap research slots.
Failed/cancelled/incomplete executions remain recorded; valid complete-enough observations can be
inspected read-only and never become completed or qualified merely through recovery. The original
failed Full Lap remains explicitly descriptive. Synthetic experiments are unqualified; no physical
or real-time guarantee is implied. A failed ordinary experiment does not require a new research
authorization for your next manual run, provided source/policy identity and resource gates still pass.
