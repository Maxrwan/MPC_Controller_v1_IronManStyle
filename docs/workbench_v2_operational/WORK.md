# V2 accepted-interactive operational delivery

**WORKBENCH_V2_ACCEPTED_INTERACTIVE_OPERATIONAL**

Branch `codex/workbench-v2-ui`. Accepted implementation:
`5d88a5478109d5ce93207170ceec60938a87e793`. Final documentation-only delivery SHA is supplied
in the Git handoff. [Primary authorization](PRIMARY_WORK.md), [user guide](USER_GUIDE.md),
[machine evidence](work_record.json). Frozen science remains
`48adbdf64d492592d15e23c917aca71fa58aa8a5`.

The source-bound **accepted-interactive policy is installed and operational**. Ordinary explicit
user clicks may run existing finite profiles and edit the approved eight CostScales/fixed disturbance
without another research authorization. Historical one-shot counters are retained, not reused.

## Enabled scope and launch

| Selection | Simulated recording | Existing limits |
|---|---|---|
| Transient | V1 2 s, unchanged | Original V1 profile/policy |
| Extended | 5 / 10 / 20 s | wall 180 s, CPU 120 s, RSS 768 MiB, output 128 MiB, file 4 MiB |
| Full Lap | Two native crossings; 80 s ceiling | wall 900 s, CPU 720 s, RSS 768 MiB, output 256 MiB, file 4 MiB |

Double-click `Launch_APEX_Workbench_V2.command` in this configured checkout or run
`./Launch_APEX_Workbench_V2.command`; loopback `http://127.0.0.1:8503`. No manual acceptance JSON,
internal policy script or dependency installation is needed. The launcher resolves its own checkout.
Configure → Run → Replay → Analyze → Compare; save a versioned experimental draft as needed.
Source/review/Primary, shared lease, environment isolation, finite resources, cancellation and atomic
publication remain enforced for every experiment. No automatic retries or background sweeps.

Full Lap checks host capacity once per explicit launch under the lease: available RAM and free disk
must each exceed 1,610,612,736 bytes, preserving the historical conservative reserves. Extended retains
its 1 GiB disk floor and fixed runtime caps. UI/reference viewers are harmless; scientific/test/benchmark
workers or active/unverified measurement guards block. A failed preflight creates no run or historical
claim. UI reports source/ownership readiness and actionable launch failures. Host memory sufficiency
is not guaranteed; free capacity and trigger a new launch yourself if needed.

## Sole genuine smoke and reviewed correction

One baseline Extended 5 s run was triggered through the normal UI after initial independent PASS at
`3ccf294e28e2f213ef9d269333d2700f2ee37522`:
`2026-11-11T160708.594424_0000_fe073e9a35714216accf3f91cc7cadae`.

- **Completed / valid evidence / exit 0**, normal matching summary and worker result; all 26 members valid.
- 1,000 native states, 500 controls, 50 packets/preparations, 49 handoffs/releases; no planner/codriver
  misses or fallbacks. Native stop `duration`; no model/control failure.
- Actual retained end `4.999999999999915`, last native sample 4.995 s; canonical duration semantics preserved.
- Supervisor wall 27.1881254 s; worker CPU 23.010227 s; sampled peak RSS 208,699,392 bytes.

A metadata-only finalization guard incorrectly expected literal 5.0. It was corrected to accept the
canonical successful duration outcome and exact raw/summary endpoint agreement. No scientific
threshold, timestamp or archive byte was changed. [Correction](FINALIZATION_CORRECTION.md).
Only `operational.py` differs among 49 producers; 48 other producers and conditional worker validation
are unchanged. The [same review's correction iteration](../reviews/workbench_v2_operational/correction_1/INTEGRITY_REVIEW.md)
passed at final 5d88a54 and explicitly approved that compatibility. The accepted record separately
binds the final source/review and immutable original smoke source/policy/review/claim. It does not
relabel the smoke as execution of the later metadata revision. **No second smoke or Full Lap ran.**

## Focused checks and actual UI

Root combined focused run: 169 passed / 2 harness failures, 75.15 s. Both affected checks re-passed
separately: 2 passed in 38.02 s after supplying the required parent VECLIB ceiling and updating rejection
wording; production logic did not change for those harness fixes. This is not one clean 171-pass invocation.
Final correction policy module: 38 passed in 30.57 s. Initial independent selection: 15 passed in 10.58 s;
correction selection: 5 passed in 0.34 s. Counts remain separate; negatives/logs/JUnit are retained.

Four canonical configuration compositions, including edited lateral cost 3.0, were checked with
solver creation, AsyncRunner.run and plant steps forbidden; actual Accelerate SINGLE confirmed.
Other software checks covered all finite modes, invalid inputs, source/review/authority/history/
smoke mutation, capacity floors and single observation, no-run preflight failure, shared-lease
contention, cancellation/resource guards, later manual admission after failure and failed-native reads.
No broad formal Verification or scientific campaign occurred.

Actual normal launcher startup from `/private/tmp`, owned reuse and clean shutdown passed. Browser
confirmed enabled Run for 5/10/20 s and Full Lap, unchanged Transient, edited-weight admission, and
saved `interactive_v2_demo_20261111_extended_5s_v1.json` with lateral 3.0. No Run was clicked after
smoke. Its normal Replay played through active packet 49/nine nodes; Analyze opened genuine metrics.
Playback advanced 4.995 simulated seconds in 2.500 display-wall seconds at 2×; display timing only.
Compare opened genuine 5 s/10 s recordings and correctly classified differing coverage/conditions as
noncontrolled. Matched-condition weight eligibility is software-tested; no treatment run was added.

## Acceptance, preservation and limits

Live policy SHA `4738fe6d5d19eeddf432e4a6c5513510be5ce93994464280fb6ddca1a8fa6d39`;
Primary accepted-authority SHA `e276d41f81c4f9859d7339800c1cc9f0ecbe8f1cdd4367225284a54a76266430`;
final review SHA `9499e5b5b150f12b59dacdba212db841a59444df233466e371bd76a8d326fd47`.
The original policy `f9a0304f…` is retained exactly as immutable `access_historical.json`. Both historical
used IDs and one-attempt counters remain unchanged; ordinary runs never write them. Every new run
captures its own unique ID/configuration/producer/host/limits/outcome/evidence.

All 811 historical file hashes/65 links rechecked: sole old-file change is the authorized live policy.
All 333 frozen runtime and 335 canonical/dependency files unchanged; V1 source/profile/policy,
renderers/clock, native scientific worker/profile and launchers preserved. Original full-lap 39-member
archive remains failed / valid evidence / exit 2 with absent summary/result and valid read-only recovery. Nothing
was repaired into success. New failed operational evidence stays descriptive; valid complete-enough
observations remain inspectable without poisoning later explicit admission. Controlled comparisons
still require completed / valid evidence / exit 0, matching conditions/coverage and no recovery.

All owned server/helper/worker activity ended; port 8503 is closed. The policy persists for the next normal
launch. Experiments remain synthetic, experimental and unqualified; no physical, hard real-time or
numerical qualification claim. Cold reference initialization/verified-window pauses remain possible.
Local retained artifacts are not off-host backup. No ROS/exporter, Docker, new scenario, tuning sweep
or later research stage was implemented. No operational blocker remains in the approved scope.
