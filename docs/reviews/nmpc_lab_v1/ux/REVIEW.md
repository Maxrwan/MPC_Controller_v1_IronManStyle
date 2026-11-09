# NMPC Lab V1 playback correction — independent Engineering Review

**PASS. No unresolved blocking finding. Primary user acceptance remains required.**
Exact candidate: `447cc1e60c064062c75f879c3c67e611a84cff31`, branch `codex/nmpc-lab-v1`.
Scope: presentation and read-only retained playback. This is one focused Engineering Review,
with no formal Verification or new scientific execution.

The old renderer advanced one 5 ms sample per 400 ms refresh: 0.0125× before figure overhead.
The replacement uses browser elapsed time and a small Canvas2D component. Its acknowledged
payload stays in the browser; nonce heartbeats validate captured hashes before and after each
one-second presentation boundary. The Bench at `35f6fa579adc574d73ea834786e53667eddcb585`
is a clean, byte-matched read-only interaction reference; no model or controller was imported.

Native seek/step and end clamping are correct. Only marker XY interpolates; the actual 0.5 s
kick holds then jumps. State values, packet IDs, solver nodes, requests and applications remain
native. Application lookup uses application clocks and requested lookup uses request clocks.
The default horizon follows the native active ID/mode with completion, validity and coverage
checks. Historical inspection is explicitly separate; terminal node 8 has no command.
Existing Control Analysis and eight-cost configuration remain intact. The restrained synthetic
caption preserves qualification limits, actual failures and historical-view restrictions.

Final-source browser pacing, one observation per speed over the actual 1.995 s native window:

| Speed | Expected wall [s] | Observed wall [s] | Difference [ms] |
|---|---:|---:|---:|
| 0.25× | 7.9800 | 7.9882 | +8.2 |
| 0.5× | 3.9900 | 3.9926 | +2.6 |
| 1× | 1.9950 | 2.0081 | +13.1 |
| 2× | 0.9975 | 0.9992 | +1.7 |

The retained two-second run therefore plays in approximately two wall seconds at 1×, without
inventing the missing endpoint state. Final timing observed 23–180 painted frames per segment,
maximum gap 50.6 ms, and one payload load across heartbeats. Earlier four-speed measurements
precede the first-frame anchor correction and remain historical. These are local display
observations, not browser cadence or real-time guarantees.

Reviewer inspection of `viewer_final.jpg` and `viewer_sample160.jpg` confirms visible track,
position marker and prediction/reference, with a changed marker position at native 0.800 s;
the matching AX record identifies active packet 8. Browser records support pause, restart,
native forward/backward, interior/end seek, historical future-packet inspection without
authority, and terminal NULL command. Run switching clears old playback/selection and starts
the new recording paused at zero. Navigation to Analyze removes the iframe. Returning to
Inspect uses the catalog default paused at zero; selection/position persistence is not claimed.

Disposable-copy mutation, including unchanged byte count/restored mtime, removes the iframe.
Restoring bytes does not clear the quarantine latch; explicit reopen starts paused at zero.
Stopping the owned fixture service eventually clears the browser payload/image; the configured
4.5 s lease is checked every 250 ms and depends on browser scheduling. The connection modal
initially obscured inspection; the preserved follow-up AX confirms clearance after dismissal.
No exact detection-latency guarantee follows. Both temporary browser services/tabs are closed;
the parent cleanup record reports refused ports, no owned scientific worker and a free lease.

Independent checks: **11 Python retained-data/presentation tests passed in 4.881 s**, zero
failures/errors/skips and zero scientific imports; **11 pure JS fixtures passed** separately.
An additional retained-data audit rebuilt all three exact-source payloads and checked 1,200
native states, 600 request/application rows, native authority, kick interpolation exclusions,
end clamping and input immutability. Older display fixtures omit only the added packet
diagnostics metadata; all other values match. Parent 18-pass software evidence is separate; a further retained existing-UI fixture passed
once in 2.17 s using captured configuration metadata, with no new probe or scientific import.
Reviewer harness setup/assertion negatives are retained and distinguished from product defects.

All 6,393 snapshot files, 324 historical M5-A links and eight old renderer capture/DOM files
match. Primary 56/345/25/4 maps and original C0 bytes match. The 333-file runtime independently
matches exact scientific Git source `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
UX-base-to-candidate scientific-prefix and worker/profile/analysis/scheduling diffs are empty;
eight older checkout differences from scientific source are preexisting and are recorded.
Access policy SHA-256 remains `628a61998231be7d45be3591236d6debbe8e67ca6d083a86ae874f2786c58f8e`:
all three genuine attempts at `af3956fc2dc8c1a88051e87e2eae66010490a2fb` remain consumed.
Repeatable execution is disabled; no probe, solve, plant step, simulation, gate reset or reseal ran.

This supports `NMPC_LAB_V1_UX_READY_PENDING_PRIMARY_USER_ACCEPTANCE`. It grants no numerical
execution, scientific/physical acceptance, real-time qualification, formal Verification or later
Workbench stage. Raw ignored evidence remains local. `review_record.json` binds the evidence;
all paths in that record are repository-relative for exact-copy publication.
