# User/Primary APEX — V0.3-D formal acceptance

- **Recorded:** 30 October 2026
- **Decision:** `V0.3_D_ACCEPTED_WITHIN_VERIFIED_SCOPE`
- **Authority:** The user's explicit formal acceptance in this chat
- **Exact accepted implementation:** `c5f3db6852af8f8ffccf4e5e9e6f11d01fa861b4`
- **Engineering Review delivery:** `49f7eb98fcec6fac5869371f70dc2e7d2daf7dff`
- **Formal Verification delivery:** `af9311ed19e41045aa16dd1029d7191f8eae9c45`
- **Branch:** `codex/apex-workbench-v0-3-d`

## Accepted software scope

Accept V0.3-D within its independently reviewed and verified software scope: the single
source-bound historical P/VIS-1R `controlled_A` inspector, native sector/event/diagnostic
presentation, source-linked local HTML generation/reopening and the existing oval LQR/PI shortcut,
with preservation of the accepted Workbench execution, evidence and scientific foundations.
This does not expand supported archive profiles or establish physical/controller qualification.

The [independent review](iteration_1/REVIEW.md) passed at the exact implementation.
The single [formal Verification](VERIFICATION.md), [machine evidence](verification_record.json),
reports **1,089 passed, 17 separately gated G2 skips, zero failures/errors**. These are the retained
Verification results, not newly executed tests in this acceptance-recording task. Scientific
evidence preservation remains as recorded; historical failures and reviewer corrections remain intact.

## Observations retained without expanded implications

- **Embedded-browser automatic download:** not confirmed within the bounded 10-second observation.
  The native Codex save-dialog inspection was tool-restricted. The historical 1,558.497-second
  browser-tool delay retains an unknown unique cause. Neither observation establishes an application
  processing delay, successful automatic download, fixed browser defect or latency guarantee.
  **Local HTML generation and reopening are verified and accepted.**
- **Launcher termination:** safe owned cleanup is verified and accepted. Targeted supervisor SIGINT
  returned 0; terminal Ctrl-C terminated the foreground shell by SIGINT(2), released the port and
  left no owned survivor. The earlier tool-reported exit 1 remains retained without a proven unique
  cause. Numeric exit status and terminal/process-group signal termination remain distinct; no
  application failure, leak, universal exit-code rule or hard-real-time guarantee is inferred.

## Gates and next preparation

RBT-S/N/V, component numerical budgets, future G/P controller execution, new scientific experiments,
frozen research and hardware work remain separately gated. RBT-0.1 remains unimplemented and
unexecuted. Existing qualification does not transfer to a new scenario or controller adapter.

The user authorizes **preparing the next bounded engineering assignment** for read-only C0/
asynchronous controller-availability failure inspection from original retained evidence. The
[prepared task](../../apex_workbench_v0_3_d/NEXT_C0_TASK.md) requires a separate producer/archive
contract audit and independent review before conditional implementation using existing Workbench
infrastructure. Preparation is not execution of that task or approval of a new archive contract.

No new racing simulation, scientific campaign, application change, test run or formal Verification
repeat is part of this documentation delivery. Stop after acceptance recording and task preparation.
