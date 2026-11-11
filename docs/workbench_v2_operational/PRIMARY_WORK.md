# PRIMARY APEX — WORKBENCH V2 FINAL OPERATIONAL ACCEPTANCE

**Decision: AUTHORIZE BOUNDED FINALIZATION AND CONDITIONAL ACCEPTED-INTERACTIVE ACTIVATION**

Repository: `Maxrwan/MPC_Controller_v1_IronManStyle`

Branch: `codex/workbench-v2-ui`

Latest delivery: `9ef4bf9265892eff6fc4bee6e91a7494cbf86e48`

Corrected recovery source: `f7c4e188c296f77dfbc7aa56e830d0315bf346a0`

Frozen scientific source: `48adbdf64d492592d15e23c917aca71fa58aa8a5`

## OBJECTIVE

Finalize APEX Workbench V2 as a fully operational, repeatable, user-controlled synthetic NMPC experimentation laboratory.

The user must be able to launch Workbench, configure NMPC weights, select an experiment duration, execute genuine simulations, replay them, analyze results and compare configurations without obtaining separate Codex authorization for each experiment.

**This is the final operationalization task. Complete development, focused validation, policy transition and normal-launch testing in one assignment.**

Do not stop merely because the old one-time pilot and full-lap slots are consumed. They are historical research authorizations, not appropriate limits for accepted interactive laboratory use.

Do not reset those slots or modify their records.

## 1. Primary acceptance decision

Primary APEX accepts the reviewed V2 presentation and read-only recovery implementation for synthetic experimentation.

Existing evidence includes:

- Operational V1 Scratch.
- Completed and valid genuine 10-second V2 baseline pilot.
- Native full-lap observation of 31.1719003976093 seconds.
- Original full-lap Workbench lifecycle failed during postprocessing, with retained valid evidence.
- Corrected NumPy lap validation and verified read-only recovery.
- Independent focused integrity PASS for recovery.
- Preserved frozen scientific sources and historical experiments.

The recovered full lap is **not** a completed Workbench execution and must never be relabeled as one.

The application may nevertheless be accepted for bounded exploratory execution based on the existing successful pilot, corrected software and additional focused acceptance checks below.

Do not require a second completed full lap as a precondition for operational acceptance.

## 2. Enable accepted-interactive V2

Inspect:

- `tools/apex_workbench/lap/config.py`
- `tools/apex_workbench/lap/admission.py`
- `tools/apex_workbench/lap/execution.py`
- `tools/apex_workbench/lap/ui_views.py`
- Existing V2 access, review and Primary authorization records.

Implement and activate a source-bound `accepted-interactive` policy after the final focused review and smoke test pass.

This policy must authorize ordinary user-triggered experiments using the existing approved finite V2 profiles.

Preserve:

- All historical consumed attempts.
- Original pilot and full-lap run directories.
- The full-lap failed status and valid original evidence.
- Existing source/review/authority bindings.
- The original historical policy as an immutable retained record.
- Worker identity, source isolation and execution lease protections.

Create the necessary new explicit acceptance record tied to the final reviewed implementation.

This prompt constitutes Primary's conditional authorization to install that record after the required checks pass. No separate approval turn is needed for that exact bounded transition.

Do not pretend the original failed run succeeded or silently convert the old one-shot policy by resetting its attempt counters.

## 3. Supported experiments

Enable repeated manual execution of:

**Transient**
- Existing V1 2-second Scratch mode, unchanged.

**Extended V2**
- 5 simulated seconds.
- 10 simulated seconds.
- 20 simulated seconds.

**Full Lap V2**
- Existing native two-crossing completion rule.
- Existing 80-second maximum simulation duration.
- Same-phase full-circuit lap timing.

All modes must support the existing approved eight CostScales fields.

Preserve the existing fixed disturbance selector.

Support baseline and user-edited weight configurations using the current versioned configuration system.

Do not introduce new controller parameters, vehicle physics, custom track generation, automatic sweeps, arbitrary simulation duration or new disturbance scenarios.

## 4. Preserve finite resource limits

Use the existing V2 resource profiles.

Extended:
- Maximum wall time: 180 seconds.
- Maximum CPU: 120 seconds.
- Maximum sampled RSS: 768 MiB.
- Maximum output: 128 MiB.
- Maximum individual file: 4 MiB.

Full Lap:
- Maximum wall time: 900 seconds.
- Maximum CPU: 720 seconds.
- Maximum sampled RSS: 768 MiB.
- Maximum output: 256 MiB.
- Maximum individual file: 4 MiB.

Keep the existing 80-second simulation ceiling and native lap-crossing rules.

V1 limits remain unchanged.

Every genuine execution must retain source/environment verification, exclusive execution ownership, resource monitoring, cancellation and evidence publication.

No simultaneous scientific workers or implicit automatic retries.

## 5. Replace one-shot research admission with practical laboratory admission

Separate two concepts:

**Historical authorization**
The original pilot/full-lap attempt limits and their immutable consumption history.

**Accepted laboratory execution**
A persistent, source-bound permission to run validated configurations manually within finite approved limits.

An accepted interactive experiment should not consume or modify historical one-shot slots.

Instead, every new experiment must receive its own unique run identity, captured configuration, source identity, resource profile, execution outcome and retained evidence.

Do not weaken the current scientific source verification.

Ensure accepted-interactive admission remains bound to the final independently reviewed implementation and explicitly recorded Primary acceptance.

Do not create unnecessary per-experiment research reviews or administrative approvals.

## 6. Resource admission before full laps

The historical full-lap driver had an additional host-capacity gate, while the general V2 worker uses its own runtime limits.

Ensure normal interactive Full Lap execution has a fresh, appropriate host-capacity check before launching the worker.

Retain the existing conservative memory and disk safeguards unless a focused technical justification demonstrates a correction is necessary.

The historical full-lap RAM floor was greater than 1,610,612,736 bytes of available memory.

Ensure the UI can report:

- Sufficient host resources.
- Insufficient available memory.
- Insufficient disk capacity.
- Existing active scientific worker.
- Source/authorization mismatch.

Do not block legitimate runs merely because the user's own Workbench UI is running or a legitimate read-only reference viewer exists.

Distinguish harmless presentation processes from conflicting scientific compute processes.

Check resources once per explicit launch request rather than polling repeatedly until a favorable reading is obtained.

A failed preflight should not create a scientific execution or consume a historical slot.

## 7. Operational interface

The user workflow must be:

**Configure → Run → Replay → Analyze → Compare**

On Configure:

- Select Transient, Extended or Full Lap.
- Select 5/10/20 seconds in Extended mode.
- Edit approved cost multipliers.
- Choose the approved disturbance selector.
- Save a versioned experimental configuration.

On Run:

- Show the selected configuration.
- Show the applicable resource limits.
- Show genuine source-bound execution readiness.
- Provide an enabled Run Experiment button for valid supported configurations.
- Explain actionable resource or policy blockers.
- Start only when the user explicitly clicks Run.

On Replay:

- Open the newly completed experiment.
- Preserve the existing polished V2 interface.
- Retain follow cameras, steering wheel, prediction microscope, active-packet tracking and verified window continuation.

On Analyze and Compare:

- Show metrics from genuine retained observations.
- Permit comparisons of baseline versus modified-weight runs.
- Distinguish complete and incomplete coverage.
- Preserve scientific condition-matching requirements.
- Keep recovered failed-run data descriptive, not qualified or officially completed.

No new visual redesign is requested.

## 8. Postprocessing and failed-run behavior

Ensure the previous NumPy scalar failure is fixed in genuine worker execution, not only in the read-only recovery path.

A successfully executed native lap with valid terminal postprocessing should produce the required normal summary, worker result, status and manifest.

Do not fabricate summaries for the original failed historical run.

If a new run fails during simulation, postprocessing, resource monitoring or cancellation:

- Retain the genuine outcome.
- Preserve available evidence.
- Provide a clear user-visible reason.
- Allow normal read-only inspection where evidence is valid and complete enough.
- Permit later explicitly user-triggered experiments under the accepted interactive policy.

A failed ordinary Scratch experiment must not permanently lock the whole laboratory or require a new authorization campaign.

No automatic retries.

## 9. Focused final validation

Use existing tests and add only focused coverage needed for the accepted-interactive transition.

Verify:

1. Valid 5-, 10- and 20-second configurations are admitted.
2. Full Lap is admitted when resources and source checks pass.
3. Invalid duration, unsupported configuration and malformed weights are rejected.
4. User-edited costs survive capture and worker configuration.
5. Source changes invalidate execution authorization.
6. Previous consumed slots remain unchanged.
7. The original failed full-lap evidence remains unchanged and replayable.
8. Per-run resource ceilings are enforced.
9. Shared execution ownership prevents concurrent scientific workers.
10. Cancellation and failed-run handling preserve evidence.
11. Run/Replay/Analyze/Compare work together.
12. The accepted source is the exact reviewed Git revision.
13. Launch and shutdown behave correctly from the intended checkout.

Conduct one narrowly scoped independent integrity review of the **execution-policy transition and source preservation**.

Do not reopen vehicle dynamics, NMPC theory or the entire Workbench review campaign.

No broad formal Verification is required for this exploratory laboratory.

## 10. One genuine lightweight smoke test

After focused software validation and review PASS, authorize at most one genuine 5-second baseline V2 smoke run to verify the normal accepted execution path.

No additional full-lap execution or 10/20-second campaign during this assignment.

Check:

- Real worker and genuine NMPC execution.
- Valid completed lifecycle.
- Valid manifest and summary.
- Correct state/control/packet recording.
- Correct replay and analysis.
- No unintended changes to historical records.

No automatic retry.

If this smoke test fails, retain evidence, correct in-scope software defects where feasible and stop without activating accepted-interactive if the failure remains unresolved.

After a successful smoke and final source identity checks, install the accepted-interactive policy and demonstrate that the normal UI admits all supported experiment modes without consuming another historical slot.

Use metadata-only or validation-only tests to confirm subsequent run admission. Do not start additional numerical experiments.

## 11. Launch and documentation

Ensure the user can simply double-click:

`Launch_APEX_Workbench_V2.command`

from the accepted configured checkout.

Provide concise user instructions covering:

- Choosing an experiment.
- Changing weights.
- Running 5/10/20 seconds.
- Running Full Lap.
- Interpreting the resource readiness message.
- Finding previous runs.
- Comparing results.
- Recognizing failed versus completed experiments.

Do not require the user to manually install an authorization JSON or run internal Python policy scripts after delivery.

The accepted-interactive transition must already be operational when Codex reports completion.

Do not invent a guarantee that host memory will always be sufficient for a full lap.

## 12. Authorization boundaries

Do not change:

- Frozen NMPC or TVLQR mathematics.
- Vehicle dynamics or tire physics.
- Planning reference or track.
- Scientific scheduling assumptions.
- Accepted V1 source/profile/policy.
- Original full-lap failed lifecycle.
- Retained evidence or historical authorization records.

Do not implement automated tuning, batch sweeps, ROS 2, Docker, System Identification or unrelated features.

## 13. Completion criteria

This assignment is finished only when:

- V2 is `accepted-interactive`.
- The final source, review and acceptance records match.
- Repeated 5/10/20-second user-triggered experiments are enabled.
- Repeated Full Lap user-triggered experiments are enabled subject to fresh host-capacity checks.
- At least one new, lightweight genuine run has demonstrated the normal interactive execution path.
- Replay, Analyze and Compare work.
- Historical evidence and consumed slots remain intact.
- The ordinary V2 launcher works.

Deliver:

- Exact final Git revision.
- Focused review and test results.
- Smoke-test observation.
- Accepted-interactive policy confirmation.
- UI readiness for all four V2 experiment selections.
- Launch instructions and remaining limitations.

Stop at:

`WORKBENCH_V2_ACCEPTED_INTERACTIVE_OPERATIONAL`

If a genuine blocker prevents these conditions, report that blocker explicitly rather than claiming completion.

**This is the final Workbench V2 operationalization assignment. The priority is to make experimentation routinely usable, not to expand the development project.**