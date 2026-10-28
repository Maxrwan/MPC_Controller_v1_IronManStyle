# Proposed separately authorized numerical qualification

**PROPOSAL ONLY — NOT EXECUTED.** Prepared 29 October 2026. The V0.2-C assignment authorizes
software preparation and independent review, not this command's execution. A separate instruction
from the user/Engineering Orchestrator is required. This is not formal Verification or physical
validation.

Reviewed source: `4897686e79c13757d5ef5b4373b44d4cab99b5bf`, branch
`codex/apex-workbench-v0-2-c`. Run from the repository root with the existing Workbench environment:

```sh
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python \
  -m tools.apex_workbench.qualification_campaign execute \
  --output-dir results/apex_workbench_qualifications/v0_2_reviewed_20261029 \
  --reviewed-revision 4897686e79c13757d5ef5b4373b44d4cab99b5bf \
  --acknowledge-scientific-execution
```

The output directory was absent at delivery. It must remain fresh: the command refuses an existing
directory. The acknowledgement flag records the operator's intent; it does not supply human approval
on its own. Documentation-only descendants are permissible when every required source file still
matches the reviewed source commit. Any scientific/qualification implementation change requires a
new exact-revision review before execution.

The fixed scope is 17 serialized executions: five accepted cases on 5/2.5/1.25 ms grids, one additional
nominal BASE repeat in a fresh worker and one independently composed nominal BASE canonical reference.
Each runs 0.500 s with the 0.100 s steering onset: 3,700 plant intervals and 8.5 simulated seconds in
aggregate. There are no extra grids, sweeps, retries, tuning, controller or hardware experiments.
Existing locks, source checks, native controls, resource limits and disk/measurement preflight remain.

Source-run outcomes, verified retained evidence, component convergence, sampled interpretation,
pair excitation and family qualification remain separate. Retain every negative/partial outcome.
An execution failure stops the coordinator; a criteria failure produces a retained negative
assessment. Do not alter thresholds, substitute favorable runs or turn fixture calculations into
real evidence. A completed campaign may still be unqualified. The quarter grid is a numerical
reference and the physical-validity status remains `not_established`.

The real positive publication/applicability path, scientific convergence, repeatability and signal
sufficiency have deliberately not been demonstrated by this preparation task. They must be assessed
from the separately authorized execution's actual evidence. Formal Verification remains a later,
separately authorized gate.
