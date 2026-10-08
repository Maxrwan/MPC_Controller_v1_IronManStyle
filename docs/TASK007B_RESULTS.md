# Task007B measured results

Planning→APEX errors query the nominal package at every predicted node. APEX→vehicle errors use the active packet at physical release time. Node statistics weight nodes equally; local means/RMS use physical intervals. First lap is a rolling-launch transient. Timing is measured, not a hard real-time guarantee.

## Study cases

| case | gamma | lambda_s | laps | stop | solver_failures | planner_failures | global_fallback | boundary_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b0 | 1 | 0 | 58.635297, 59.011882, 59.013652 | target_laps | 0 | 0 | 0 | 0 |
| b1_g1.25 | 1.25 | 0 | 47.017272 | target_laps | 0 | 0 | 0 | 0 |
| b1_g1.5 | 1.5 | 0 | 39.722852 | target_laps | 0 | 0 | 0 | 0 |
| b1_g1.75 | 1.75 | 0 | 34.667222 | target_laps | 0 | 0 | 0 | 0 |
| b1_g2 | 2 | 0 | 31.448075 | target_laps | 0 | 0 | 0 | 0 |
| b1_g2.25 | 2.25 | 0 | 30.885035 | target_laps | 0 | 0 | 0 | 0 |
| b1_g2.5 | 2.5 | 0 | 30.325608 | target_laps | 0 | 0 | 0 | 0 |
| b2_w0.1 | 1 | 0.1 | 58.616627 | target_laps | 0 | 0 | 0 | 0 |
| b2_w0.25 | 1 | 0.25 | 58.592058 | target_laps | 0 | 0 | 0 | 0 |
| b2_w0.5 | 1 | 0.5 | 58.552186 | target_laps | 0 | 0 | 0 | 0 |
| b2_w1 | 1 | 1 | 58.517494 | target_laps | 0 | 0 | 0 | 0 |
| b2_w2 | 1 | 2 | 58.394572 | target_laps | 0 | 0 | 0 | 0 |
| b2_w4 | 1 | 4 | 58.212956 | target_laps | 0 | 0 | 0 | 0 |
| b2_w8 | 1 | 8 | 57.786473 | target_laps | 0 | 0 | 0 | 0 |
| b3_g2.5_w1 | 2.5 | 1 | 32.206657 | target_laps | 0 | 0 | 0 | 0 |
| b3_g2.5_w2 | 2.5 | 2 | 31.576227 | target_laps | 0 | 0 | 0 | 0 |
| b3_g2_w1 | 2 | 1 | 31.200155 | target_laps | 0 | 0 | 0 | 0 |
| b3_g2_w2 | 2 | 2 | 31.418612 | target_laps | 0 | 0 | 0 | 0 |
| b4_g1_w1 | 1 | 1 | 58.518637, 58.911665, 58.909154 | target_laps | 0 | 0 | 0 | 0 |
| b4_g1_w2 | 1 | 2 | 58.395693, 58.797833, 58.799993 | target_laps | 0 | 0 | 0 | 0 |
| b4_g2_w0 | 2 | 0 | 31.202251, 31.479313, 31.511372 | target_laps | 0 | 0 | 0 | 0 |
| b4_g2_w1 | 2 | 1 | 31.300569, 31.406680, 31.596719 | target_laps | 0 | 0 | 0 | 0 |
| b4_g2_w2 | 2 | 2 | 31.975886, 31.520096, 31.642861 | target_laps | 0 | 0 | 0 | 0 |
| support_injected_w2 | 1 | 2 | 58.278206 | target_laps | 0 | 0 | 0 | 0 |
| support_zero_w2 | 1 | 2 | 58.393582 | target_laps | 0 | 0 | 0 | 0 |

## Selection and interpretation

At gamma=1, lambda=2 gives comparable laps 58.797833/58.799993 s: mean 58.798913 s versus 59.012767 s at lambda=0, a 0.362% reduction. Both lap gains are positive. Lambda=1 gives only 0.173%, below the predeclared 0.2% threshold. Select the smallest screened qualifying weight, 2, only for this conservative synthetic case. Legacy default remains zero.

At gamma=2, mean complete laps are 31.495342 s (lambda=0), 31.501700 s (lambda=1), and 31.581479 s (lambda=2). The startup advantage of lambda=1 did not persist. Progress reward does not show a general high-demand advantage.

At gamma=2.5, lambda=1 is rejected for sustained planned lateral/heading oscillation and a slower lap; lambda=2 is rejected for 0.027471 m predicted slack and 0.060095 m physical clearance, below the unchanged 0.08 m margin. There was no physical boundary crossing or global fallback. These cases remain in every audit and comparison. Escalation stopped without retuning penalties, reference states, or TVLQR.

Planning-to-APEX deviations increase strongly with demand while vehicle-to-active-APEX errors remain much smaller. APEX backs away from requested speed. This supports feasibility adaptation, but the rejected oscillatory case is not graceful behavior. A codriver cannot correct the quality of a trajectory it is successfully tracking.

No near-singular coordinate-progress exploitation was demonstrated: inspect the denominator, physical path distance and heading jointly. Healthy denominator values do not excuse oscillation or margin slack. The experiment does not prove a unique cause; short horizon, frozen preview, geometric zero-vy nominal states, local nonlinear solutions and timing remain confounded.

The comparison is Pareto-style: lap benefit, nominal-intent departure, local tracking, constraint use and timing remain separate. Lambda=4/8 achieve larger startup gains but are larger than needed and lack high-demand confirmation. No combined score or claim of a globally optimal lambda is made. No group-multiplier sensitivity was needed because a safe conservative-case benefit exists.

Zero and 150 ms injected planner-latency supporting runs both finish without fallback or boundary violation. The injected case skips 291 planner deadlines with zero codriver misses. Measured runs remain primary; injected/zero lap times are not used to select the weight.

Future work should first review APEX trajectory quality and the frozen reference/preview approximation. Current evidence does not justify adaptive codriver switching. All observer signals are logged without constructing a difficulty index or controller policy.

Hairpin: at gamma=1, lambda=2 raises mean actual speed from 1.617 to 1.629 m/s. Planning-to-APEX lateral RMS is 17.49 mm while local lateral RMS is 0.769 mm. At gamma=2, the hairpin reaches about 95% peak front utilization in the tracking baseline. The larger nominal deviation is not equivalent to loss of local tracking.

Technical section: at gamma=2, lambda=2 increases Planning-to-APEX lateral RMS from 39.94 to 57.54 mm and local lateral RMS from 2.24 to 2.60 mm. It increases steering-rate-limit time from 2.45 to 3.94 s across the two comparable sector traversals and reduces mean speed from 4.180 to 4.140 m/s. This contributes to the absence of a complete-lap benefit.

Fast sweeper: the rejected gamma=2.5, lambda=1 screen has APEX heading total variation 6.329 rad versus 0.281 rad at lambda=0 in the same sector, and 2.35 s at the steering-rate limit versus zero. Local lateral RMS remains 3.15 mm despite planned lateral RMS deviation of 79.89 mm. Lambda=2 is not oscillatory in that same sector; its separate rejection is driven by margin slack elsewhere. Do not merge the two failure mechanisms.

Sideslip and reference approximation: peak actual |beta| is 0.129 rad in the conservative baseline, about 0.322 rad in the comparable gamma=2 tracking case and 0.490 rad in the rejected gamma=2.5, lambda=2 screen. Demand dependence is not monotonic at every ladder step. The frozen nominal 10 ms yaw-rate defect grows from 0.0231 to 0.1211 rad/s between gamma=1 and 2.5; mean stage vy cost rises from 0.0138 to 3.302 in their tracking cases. This exposes the geometric approximation but does not prove that vy_ref=0 alone prevents good behavior.

Computational cost: baseline versus selected conservative mean/p95 full planner preparation is 24.22/30.98 ms versus 23.56/30.39 ms; mean solver iterations are 7.795 versus 7.782. The gamma=2 baseline uses 11.106 iterations and 28.88/33.42 ms. Harder demand increases optimization effort, whereas adding the terminal reward is not intrinsically expensive. Measured tails vary by run and are not deterministic guarantees.

Native threading is configured through Accelerate set/get, not environment variables alone. Its exact active-thread count is unavailable through this API. Recorded CPU/wall preparation ratios near one support single-core execution; the earlier isolated threading study remains the detailed backend/thread-behavior evidence. Peak RSS is process memory, not isolated solver allocation.

Validation: all 500 regression tests pass, including an end-to-end progress-export test with injected skipped deadlines and an independent physical-command/packet audit. The full study retains all 25 cases. No adaptive codriver, observer-driven mode selection, global Planning optimizer, or new vehicle physics was implemented.

Machine-readable decisions and case membership: `results/task007b/selection.json`.

## Adaptation versus local tracking

| case | plan_ey_rms | plan_epsi_rms | plan_v_rms | plan_v_mean | local_ey_rms | local_ey_max | local_heading_rms | beta_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b0 | 0.00578725 | 0.0130768 | 0.145798 | 0.00985935 | 0.000408394 | 0.0051051 | 0.00300822 | 0.129203 |
| b1_g1.25 | 0.0113498 | 0.0209179 | 0.213883 | -0.00431368 | 0.000886381 | 0.00716143 | 0.0067986 | 0.0836859 |
| b1_g1.5 | 0.0202042 | 0.0389825 | 0.288481 | -0.0556046 | 0.00115889 | 0.00850264 | 0.00914812 | 0.0676401 |
| b1_g1.75 | 0.0188121 | 0.0477762 | 0.37563 | -0.142837 | 0.00122936 | 0.0100716 | 0.00991086 | 0.154475 |
| b1_g2 | 0.0337138 | 0.0723256 | 0.541462 | -0.307885 | 0.0016599 | 0.00909214 | 0.014004 | 0.323995 |
| b1_g2.25 | 0.0709034 | 0.115982 | 0.696057 | -0.52688 | 0.00232561 | 0.0113808 | 0.0166416 | 0.401791 |
| b1_g2.5 | 0.0711434 | 0.118612 | 0.83367 | -0.628394 | 0.0022656 | 0.0133911 | 0.017528 | 0.394342 |
| b2_w0.1 | 0.00568486 | 0.0129846 | 0.145651 | 0.0107613 | 0.000376991 | 0.00466417 | 0.0027176 | 0.127384 |
| b2_w0.25 | 0.00577713 | 0.0130595 | 0.145889 | 0.0117805 | 0.00039084 | 0.00463325 | 0.00281892 | 0.127683 |
| b2_w0.5 | 0.0059109 | 0.0131493 | 0.146102 | 0.0132349 | 0.000405295 | 0.00515753 | 0.00294138 | 0.127909 |
| b2_w1 | 0.00580405 | 0.0130236 | 0.146294 | 0.0148557 | 0.000388875 | 0.00449994 | 0.00285186 | 0.12831 |
| b2_w2 | 0.0060096 | 0.0130857 | 0.14734 | 0.019823 | 0.000410812 | 0.00519163 | 0.00300314 | 0.128414 |
| b2_w4 | 0.00593602 | 0.0128351 | 0.14905 | 0.0278639 | 0.000385963 | 0.00446443 | 0.00280504 | 0.126701 |
| b2_w8 | 0.00633453 | 0.0127859 | 0.154808 | 0.0458844 | 0.00041166 | 0.00490774 | 0.00301939 | 0.122352 |
| b3_g2.5_w1 | 0.0890586 | 0.146575 | 1.03758 | -0.887048 | 0.00317599 | 0.0185971 | 0.0265168 | 0.393669 |
| b3_g2.5_w2 | 0.0912286 | 0.158918 | 1.14985 | -0.826701 | 0.00268771 | 0.0132561 | 0.0211691 | 0.489986 |
| b3_g2_w1 | 0.0286161 | 0.0646467 | 0.507589 | -0.279653 | 0.00145815 | 0.00993261 | 0.0118967 | 0.321033 |
| b3_g2_w2 | 0.0345378 | 0.0728163 | 0.561087 | -0.308786 | 0.00172867 | 0.00931306 | 0.014814 | 0.323605 |
| b4_g1_w1 | 0.00587615 | 0.0130734 | 0.146337 | 0.0144277 | 0.000406713 | 0.0052499 | 0.00289662 | 0.125458 |
| b4_g1_w2 | 0.00598618 | 0.01305 | 0.147171 | 0.0189624 | 0.000413411 | 0.00523927 | 0.00298715 | 0.128535 |
| b4_g2_w0 | 0.0288837 | 0.0647147 | 0.519537 | -0.294211 | 0.00142822 | 0.00930459 | 0.010983 | 0.322121 |
| b4_g2_w1 | 0.0297536 | 0.066315 | 0.517263 | -0.293675 | 0.00154502 | 0.0101236 | 0.0127496 | 0.322966 |
| b4_g2_w2 | 0.0343805 | 0.0696347 | 0.546615 | -0.305537 | 0.00154917 | 0.0103578 | 0.0125445 | 0.316142 |
| support_injected_w2 | 0.0067809 | 0.0130803 | 0.161652 | 0.0212657 | 0.000783714 | 0.0132476 | 0.00480027 | 0.119459 |
| support_zero_w2 | 0.00598451 | 0.0129728 | 0.148847 | 0.0196756 | 0.000407285 | 0.0049686 | 0.00297748 | 0.124411 |

## Constraint and coordinate audit

| case | front_max | rear_max | clearance_min | slack_max | predicted_denominator_min | predicted_heading_max | progress_per_physical_distance | steering_TV | acceleration_TV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b0 | 0.390641 | 0.311037 | 0.334938 | 9.09187e-11 | 0.7775 | 0.26743 | 1.00525 | 13.9087 | 53.3342 |
| b1_g1.25 | 0.642758 | 0.585538 | 0.316698 | 9.09182e-11 | 0.797597 | 0.319476 | 1.00528 | 6.54865 | 26.9988 |
| b1_g1.5 | 0.82448 | 0.815634 | 0.306823 | 9.09176e-11 | 0.791241 | 0.386877 | 1.00522 | 7.48229 | 44.3081 |
| b1_g1.75 | 0.919324 | 0.924553 | 0.313332 | 9.09184e-11 | 0.783401 | 0.358711 | 1.0056 | 7.32541 | 50.5362 |
| b1_g2 | 0.949599 | 0.979452 | 0.307991 | 9.09183e-11 | 0.783255 | 0.400168 | 1.00426 | 10.4578 | 77.8966 |
| b1_g2.25 | 0.934732 | 0.973463 | 0.101332 | 9.09185e-11 | 0.731069 | 0.733462 | 1.0029 | 13.3337 | 118.996 |
| b1_g2.5 | 0.928309 | 0.97583 | 0.138994 | 9.09161e-11 | 0.737225 | 0.740881 | 1.00196 | 13.366 | 112.299 |
| b2_w0.1 | 0.381388 | 0.305492 | 0.334949 | 9.09181e-11 | 0.791897 | 0.264079 | 1.00531 | 4.6089 | 17.8917 |
| b2_w0.25 | 0.37876 | 0.306033 | 0.334959 | 9.09183e-11 | 0.786702 | 0.26432 | 1.00532 | 4.62162 | 18.0197 |
| b2_w0.5 | 0.383347 | 0.306503 | 0.335018 | 9.09185e-11 | 0.778221 | 0.264799 | 1.00532 | 4.65522 | 17.9864 |
| b2_w1 | 0.383156 | 0.306098 | 0.335024 | 9.09184e-11 | 0.784655 | 0.265582 | 1.00532 | 4.62199 | 17.5257 |
| b2_w2 | 0.387134 | 0.308454 | 0.335026 | 9.09186e-11 | 0.778697 | 0.266814 | 1.00532 | 4.71477 | 17.8326 |
| b2_w4 | 0.384979 | 0.312914 | 0.335028 | 9.09185e-11 | 0.788872 | 0.263209 | 1.00531 | 4.61521 | 16.9632 |
| b2_w8 | 0.394166 | 0.329036 | 0.335047 | 9.09186e-11 | 0.788913 | 0.265285 | 1.00532 | 4.68219 | 17.8612 |
| b3_g2.5_w1 | 0.923486 | 0.97575 | 0.134605 | 9.09169e-11 | 0.683339 | 0.738769 | 0.996403 | 24.4437 | 233.324 |
| b3_g2.5_w2 | 0.956075 | 0.989793 | 0.0600955 | 0.0274713 | 0.757548 | 0.977958 | 0.999312 | 18.418 | 171.224 |
| b3_g2_w1 | 0.953989 | 0.978395 | 0.320564 | 9.09186e-11 | 0.798168 | 0.398276 | 1.00484 | 9.09249 | 67.7942 |
| b3_g2_w2 | 0.951259 | 0.978646 | 0.2994 | 9.09185e-11 | 0.772464 | 0.399726 | 1.00415 | 11.6416 | 85.8594 |
| b4_g1_w1 | 0.389594 | 0.308356 | 0.334966 | 9.09186e-11 | 0.776243 | 0.265543 | 1.00525 | 13.9398 | 52.444 |
| b4_g1_w2 | 0.389418 | 0.307936 | 0.335024 | 9.09187e-11 | 0.778699 | 0.266871 | 1.00525 | 14.2324 | 53.4214 |
| b4_g2_w0 | 0.957753 | 0.977645 | 0.312322 | 9.09186e-11 | 0.769427 | 0.396998 | 1.0049 | 26.1087 | 201.611 |
| b4_g2_w1 | 0.954572 | 0.978458 | 0.320157 | 9.09185e-11 | 0.789545 | 0.398569 | 1.00466 | 29.3473 | 215.905 |
| b4_g2_w2 | 0.952659 | 0.979118 | 0.255594 | 9.09186e-11 | 0.775628 | 0.479851 | 1.00368 | 33.9403 | 262.143 |
| support_injected_w2 | 0.410386 | 0.339689 | 0.33465 | 9.09185e-11 | 0.793585 | 0.257116 | 1.00532 | 5.22329 | 28.1884 |
| support_zero_w2 | 0.380457 | 0.315313 | 0.334927 | 9.0918e-11 | 0.780502 | 0.265432 | 1.00533 | 5.45003 | 45.9347 |

## Physical-time performance

| case | progress_mps | terminal_progress_mps | above_ref_s | below_ref_s | excess_m | shortfall_m | rate_limit_s | reserve_min | planner_misses | codriver_misses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b0 | 2.62248 | 2.5158 | 39 | 79.0257 | 6.40971 | 5.23581 | 1.98 | 0.198535 | 2 | 1 |
| b1_g1.25 | 3.27037 | 3.08085 | 14.86 | 32.15 | 3.45403 | 3.62358 | 2.02 | 0.247862 | 0 | 2 |
| b1_g1.5 | 3.87091 | 3.61511 | 10.16 | 29.5531 | 3.12234 | 5.30482 | 2.68 | 0.277391 | 0 | 0 |
| b1_g1.75 | 4.43543 | 4.10265 | 7.59 | 27.07 | 2.53104 | 7.47103 | 2.66 | 0.243448 | 0 | 0 |
| b1_g2 | 4.88947 | 4.51145 | 4.89 | 26.55 | 1.78264 | 11.6484 | 4.09 | 0.273691 | 0 | 0 |
| b1_g2.25 | 4.9786 | 4.77021 | 1.32 | 29.5558 | 0.278625 | 16.7836 | 5.56 | 0.268892 | 0 | 0 |
| b1_g2.5 | 5.07044 | 4.90859 | 0.78 | 29.5358 | 0.195008 | 19.588 | 5.55 | 0.268052 | 0 | 0 |
| b2_w0.1 | 2.62321 | 2.5158 | 19.39 | 39.22 | 3.19063 | 2.56673 | 0.79 | 0.277528 | 0 | 0 |
| b2_w0.25 | 2.62431 | 2.51589 | 21.1 | 37.4757 | 3.21275 | 2.53673 | 0.82 | 0.277219 | 0 | 0 |
| b2_w0.5 | 2.6261 | 2.5182 | 22.37 | 36.1757 | 3.25063 | 2.4874 | 0.86 | 0.277739 | 0 | 0 |
| b2_w1 | 2.62765 | 2.51957 | 23.62 | 34.89 | 3.2841 | 2.42033 | 0.77 | 0.27743 | 0 | 0 |
| b2_w2 | 2.63319 | 2.52294 | 27.86 | 30.5257 | 3.41644 | 2.26553 | 0.9 | 0.277593 | 0 | 0 |
| b2_w4 | 2.6414 | 2.53206 | 34.43 | 23.7757 | 3.67212 | 2.05132 | 1.01 | 0.277414 | 0 | 0 |
| b2_w8 | 2.66089 | 2.5486 | 37.7 | 20.08 | 4.33455 | 1.67491 | 0.93 | 0.277422 | 0 | 0 |
| b3_g2.5_w1 | 4.77427 | 4.92058 | 0.4 | 31.8 | 0.133563 | 29.8268 | 12.26 | 0.249114 | 0 | 0 |
| b3_g2.5_w2 | 4.8696 | 4.15465 | 0.63 | 30.94 | 0.149139 | 26.8424 | 8.87 | 0.266464 | 0 | 0 |
| b3_g2_w1 | 4.92829 | 4.51305 | 5 | 26.1907 | 1.83234 | 10.6348 | 3.31073 | 0.272949 | 0 | 0 |
| b3_g2_w2 | 4.89406 | 4.48508 | 5.34 | 26.07 | 1.86899 | 11.7571 | 4.92 | 0.272953 | 0 | 0 |
| b4_g1_w1 | 2.62727 | 2.52035 | 47.56 | 70.25 | 6.59056 | 4.89727 | 1.79 | 0.237237 | 0 | 6 |
| b4_g1_w2 | 2.63243 | 2.52308 | 55.89 | 61.7057 | 6.83068 | 4.59892 | 1.83 | 0.277116 | 0 | 0 |
| b4_g2_w0 | 4.91853 | 4.51142 | 10.26 | 52.7258 | 3.63155 | 22.486 | 5.45 | 0.255564 | 0 | 0 |
| b4_g2_w1 | 4.91275 | 4.50903 | 10.08 | 52.9158 | 3.6495 | 22.4922 | 7.24 | 0.272633 | 0 | 0 |
| b4_g2_w2 | 4.86964 | 4.499 | 10.66 | 52.5 | 3.71026 | 23.4383 | 7.36 | 0.273655 | 0 | 0 |
| support_injected_w2 | 2.63844 | 2.52528 | 25.95 | 32.32 | 3.81245 | 2.5867 | 2.18 | 0.067 | 291 | 0 |
| support_zero_w2 | 2.63323 | 2.52378 | 27.51 | 30.875 | 3.45339 | 2.31921 | 1.78 | 0.283 | 0 | 0 |

## Computation (milliseconds; excludes startup in official timing summaries)

| case | solve_mean | solve_p95 | planner_mean | planner_p95 | planner_max | codriver_mean | codriver_p95 | codriver_max | core_seconds_per_s | peak_RSS_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b0 | 11.5571 | 14.4049 | 24.2209 | 30.978 | 117.404 | 0.853571 | 1.18311 | 13.1162 | 0.325798 | 295747584 |
| b1_g1.25 | 11.436 | 16.5922 | 24.4336 | 34.1849 | 78.3999 | 0.871077 | 1.17988 | 11.7042 | 0.327212 | 198213632 |
| b1_g1.5 | 12.3373 | 15.5309 | 24.7039 | 30.5124 | 37.9801 | 0.837856 | 1.16207 | 2.37 | 0.330567 | 247037952 |
| b1_g1.75 | 13.5391 | 16.1822 | 26.631 | 31.5032 | 82.9461 | 0.841849 | 1.16988 | 6.80875 | 0.348407 | 204898304 |
| b1_g2 | 15.7183 | 19.9175 | 28.826 | 33.5787 | 35.5897 | 0.84184 | 1.17689 | 7.04742 | 0.371726 | 206143488 |
| b1_g2.25 | 16.1502 | 19.9997 | 29.1102 | 33.3661 | 38.8031 | 0.82943 | 1.06418 | 2.26879 | 0.373208 | 267042816 |
| b1_g2.5 | 16.5828 | 20.0995 | 29.6068 | 34.3002 | 38.6047 | 0.828822 | 1.06451 | 2.27621 | 0.378691 | 214646784 |
| b2_w0.1 | 11.2524 | 14.0699 | 23.5075 | 30.4633 | 37.706 | 0.83682 | 1.17704 | 2.28046 | 0.318605 | 272121856 |
| b2_w0.25 | 11.1942 | 13.9369 | 23.4769 | 30.4454 | 38.5015 | 0.843182 | 1.12272 | 2.31508 | 0.318691 | 265355264 |
| b2_w0.5 | 11.2271 | 14.1157 | 23.3337 | 30.3863 | 41.3636 | 0.828452 | 1.16764 | 2.52221 | 0.315873 | 224493568 |
| b2_w1 | 11.3147 | 14.0909 | 23.5875 | 30.2496 | 37.6163 | 0.843685 | 1.17536 | 3.04733 | 0.319906 | 207536128 |
| b2_w2 | 11.2841 | 14.0324 | 23.5943 | 30.4606 | 38.055 | 0.84507 | 1.18268 | 3.60067 | 0.319775 | 213188608 |
| b2_w4 | 11.1466 | 13.9784 | 23.4751 | 30.75 | 38.5805 | 0.847072 | 1.20265 | 2.32646 | 0.319337 | 268976128 |
| b2_w8 | 11.1584 | 13.953 | 23.5943 | 30.5051 | 39.3464 | 0.854488 | 1.12304 | 2.53108 | 0.320905 | 276856832 |
| b3_g2.5_w1 | 17.358 | 20.7556 | 31.0582 | 35.2752 | 79.4005 | 0.840742 | 1.07558 | 3.78242 | 0.394055 | 208437248 |
| b3_g2.5_w2 | 17.0239 | 20.5262 | 30.6412 | 34.8038 | 40.6802 | 0.84477 | 1.08417 | 2.31354 | 0.389811 | 206356480 |
| b3_g2_w1 | 15.7869 | 19.7172 | 29.351 | 33.8307 | 40.9673 | 0.866179 | 1.19967 | 3.07588 | 0.379698 | 226689024 |
| b3_g2_w2 | 15.9934 | 20.3331 | 29.3897 | 33.5425 | 37.7641 | 0.849645 | 1.13263 | 2.35658 | 0.378422 | 212451328 |
| b4_g1_w1 | 11.4982 | 14.285 | 23.9893 | 30.9358 | 85.361 | 0.852627 | 1.18633 | 53.7476 | 0.324194 | 308772864 |
| b4_g1_w2 | 11.2485 | 14.1138 | 23.5633 | 30.3873 | 38.8645 | 0.840102 | 1.17759 | 3.25396 | 0.319411 | 411893760 |
| b4_g2_w0 | 15.6266 | 19.2733 | 28.877 | 33.4248 | 71.7995 | 0.846613 | 1.15242 | 8.3615 | 0.37249 | 317014016 |
| b4_g2_w1 | 15.7715 | 19.7642 | 29.122 | 33.5362 | 51.5111 | 0.851315 | 1.15885 | 9.86346 | 0.37587 | 282820608 |
| b4_g2_w2 | 15.5702 | 19.8771 | 28.4031 | 32.7031 | 41.2022 | 0.829984 | 1.07713 | 2.32471 | 0.366873 | 310542336 |
| support_injected_w2 | 11.5089 | 14.4194 | 45.1618 | 58.8531 | 79.784 | 0.863901 | 1.16675 | 11.2149 | 0.311491 | 210731008 |
| support_zero_w2 | 11.3769 | 14.204 | 19.3902 | 23.4499 | 26.6384 | 0.854915 | 1.19167 | 19.0577 | 0.278563 | 272662528 |

## Objective component distributions (mean / p95 absolute / maximum absolute)

### b0

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00167611 | 0.00705231 | 0.030595 |
| input_reference | 0.129495 | 0.464002 | 2.78646 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09181e-06 |
| slack_quadratic | 8.26555e-15 | 8.26556e-15 | 8.2661e-15 |
| state_tracking | 0.526496 | 2.50274 | 7.77127 |
| terminal_tracking | 0.208565 | 1.00797 | 3.59682 |
| total | 0.866241 | 4.11581 | 13.285 |

### b1_g1.25

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00468002 | 0.0266626 | 0.0864143 |
| input_reference | 0.270855 | 1.18363 | 2.88178 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.09148e-06 | 9.09151e-06 | 9.0918e-06 |
| slack_quadratic | 8.26551e-15 | 8.26556e-15 | 8.26608e-15 |
| state_tracking | 1.30983 | 5.61179 | 14.6945 |
| terminal_tracking | 0.400891 | 1.57704 | 7.5159 |
| total | 1.98626 | 8.86265 | 24.3721 |

### b1_g1.5

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0141633 | 0.0781319 | 0.409649 |
| input_reference | 0.563041 | 2.19555 | 7.07013 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.09149e-06 | 9.09152e-06 | 9.09171e-06 |
| slack_quadratic | 8.26552e-15 | 8.26557e-15 | 8.26592e-15 |
| state_tracking | 3.39123 | 12.3461 | 45.2946 |
| terminal_tracking | 1.13547 | 3.58518 | 33.3043 |
| total | 5.10391 | 19.2001 | 76.7485 |

### b1_g1.75

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0223606 | 0.0671309 | 0.74702 |
| input_reference | 0.859332 | 3.12588 | 11.9801 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.0915e-06 | 9.09168e-06 | 9.09178e-06 |
| slack_quadratic | 8.26554e-15 | 8.26586e-15 | 8.26605e-15 |
| state_tracking | 5.34926 | 15.7384 | 42.618 |
| terminal_tracking | 1.57633 | 4.33801 | 24.1343 |
| total | 7.8073 | 22.9228 | 56.1635 |

### b1_g2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.052162 | 0.25533 | 0.999926 |
| input_reference | 1.7175 | 6.63404 | 12.6851 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.09142e-06 | 9.09151e-06 | 9.09182e-06 |
| slack_quadratic | 8.26538e-15 | 8.26556e-15 | 8.26612e-15 |
| state_tracking | 12.9376 | 39.9702 | 67.6671 |
| terminal_tracking | 4.47744 | 13.9617 | 74.3782 |
| total | 19.1847 | 60.25 | 132.708 |

### b1_g2.25

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.226541 | 1.4041 | 5.01934 |
| input_reference | 3.18437 | 14.4339 | 28.0201 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.09139e-06 | 9.09151e-06 | 9.09185e-06 |
| slack_quadratic | 8.26534e-15 | 8.26556e-15 | 8.26617e-15 |
| state_tracking | 29.6741 | 99.8495 | 410.122 |
| terminal_tracking | 24.633 | 112.471 | 844.949 |
| total | 57.718 | 239.733 | 1072.2 |

### b1_g2.5

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.22369 | 1.30976 | 4.78473 |
| input_reference | 3.48771 | 17.0695 | 28.0051 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.09138e-06 | 9.09151e-06 | 9.09157e-06 |
| slack_quadratic | 8.26531e-15 | 8.26556e-15 | 8.26567e-15 |
| state_tracking | 34.2697 | 125.825 | 443.185 |
| terminal_tracking | 22.0633 | 102.338 | 666.019 |
| total | 60.0444 | 225.227 | 911.059 |

### b2_w0.1

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00166686 | 0.00639798 | 0.0305741 |
| input_reference | 0.129497 | 0.464679 | 2.68522 |
| progress_reward | -0.0437214 | 0.0501809 | 0.0512383 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09179e-06 |
| slack_quadratic | 8.26556e-15 | 8.26556e-15 | 8.26607e-15 |
| state_tracking | 0.525124 | 2.44789 | 7.79396 |
| terminal_tracking | 0.207854 | 0.956038 | 3.46308 |
| total | 0.82043 | 3.93169 | 13.2688 |

### b2_w0.25

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00168671 | 0.0063839 | 0.0305878 |
| input_reference | 0.129936 | 0.467002 | 2.6827 |
| progress_reward | -0.109354 | 0.125493 | 0.128124 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09181e-06 |
| slack_quadratic | 8.26555e-15 | 8.26556e-15 | 8.2661e-15 |
| state_tracking | 0.529022 | 2.51965 | 7.81619 |
| terminal_tracking | 0.209242 | 0.993772 | 3.45593 |
| total | 0.760543 | 3.92274 | 13.2396 |

### b2_w0.5

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00171218 | 0.00687859 | 0.0306608 |
| input_reference | 0.130362 | 0.471993 | 2.69023 |
| progress_reward | -0.218847 | 0.251116 | 0.25634 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09183e-06 |
| slack_quadratic | 8.26555e-15 | 8.26556e-15 | 8.26614e-15 |
| state_tracking | 0.533848 | 2.54565 | 7.86382 |
| terminal_tracking | 0.21096 | 1.03757 | 3.44046 |
| total | 0.658045 | 4.00742 | 13.1466 |

### b2_w1

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0016762 | 0.00685897 | 0.0308174 |
| input_reference | 0.129912 | 0.461771 | 2.72617 |
| progress_reward | -0.437952 | 0.502613 | 0.51307 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09178e-06 |
| slack_quadratic | 8.26556e-15 | 8.26556e-15 | 8.26605e-15 |
| state_tracking | 0.529624 | 2.6225 | 7.95467 |
| terminal_tracking | 0.209112 | 0.97905 | 3.43795 |
| total | 0.43238 | 3.88164 | 12.8643 |

### b2_w2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00171399 | 0.00705528 | 0.0309407 |
| input_reference | 0.130651 | 0.475564 | 2.80103 |
| progress_reward | -0.877764 | 1.00629 | 1.02773 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09181e-06 |
| slack_quadratic | 8.26555e-15 | 8.26556e-15 | 8.2661e-15 |
| state_tracking | 0.538044 | 2.53843 | 7.80291 |
| terminal_tracking | 0.21121 | 1.05691 | 3.52885 |
| total | 0.00386423 | 3.64674 | 12.7407 |

### b2_w4

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00167443 | 0.00646612 | 0.0288279 |
| input_reference | 0.130176 | 0.470145 | 2.76156 |
| progress_reward | -1.76092 | 2.01931 | 2.06164 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09183e-06 |
| slack_quadratic | 8.26556e-15 | 8.26556e-15 | 8.26614e-15 |
| state_tracking | 0.538066 | 2.59282 | 7.76802 |
| terminal_tracking | 0.208872 | 0.998776 | 3.56135 |
| total | -0.882127 | 2.87546 | 12.4504 |

### b2_w8

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00170701 | 0.00627618 | 0.0283742 |
| input_reference | 0.131441 | 0.475626 | 2.63064 |
| progress_reward | -3.54773 | 4.06299 | 4.14806 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.0918e-06 |
| slack_quadratic | 8.26556e-15 | 8.26556e-15 | 8.26609e-15 |
| state_tracking | 0.567452 | 2.86279 | 8.23171 |
| terminal_tracking | 0.213241 | 1.04366 | 3.43104 |
| total | -2.63389 | 4.05072 | 11.8807 |

### b3_g2.5_w1

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.44884 | 1.82722 | 4.80103 |
| input_reference | 6.08128 | 19.0369 | 30.0083 |
| progress_reward | -0.800661 | 0.96113 | 0.994671 |
| slack_linear | 9.09137e-06 | 9.09151e-06 | 9.09168e-06 |
| slack_quadratic | 8.2653e-15 | 8.26556e-15 | 8.26587e-15 |
| state_tracking | 53.1755 | 138.341 | 441.87 |
| terminal_tracking | 31.7143 | 115.482 | 680.775 |
| total | 90.6192 | 235.338 | 926.312 |

### b3_g2.5_w2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.306073 | 1.72722 | 5.037 |
| input_reference | 4.68477 | 17.1344 | 33.9269 |
| progress_reward | -1.62923 | 1.98042 | 1.98994 |
| slack_linear | 2.92767 | 9.09151e-06 | 274.713 |
| slack_quadratic | 0.599951 | 8.26556e-15 | 75.4672 |
| state_tracking | 57.9143 | 243.434 | 702.138 |
| terminal_tracking | 46.3826 | 196.126 | 943.175 |
| total | 111.186 | 597.475 | 1673.18 |

### b3_g2_w1

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0370017 | 0.122181 | 0.734067 |
| input_reference | 1.47744 | 5.51335 | 12.8697 |
| progress_reward | -0.821018 | 0.986355 | 0.992568 |
| slack_linear | 9.09143e-06 | 9.09151e-06 | 9.09179e-06 |
| slack_quadratic | 8.26541e-15 | 8.26556e-15 | 8.26606e-15 |
| state_tracking | 10.6194 | 27.6844 | 70.9629 |
| terminal_tracking | 3.53137 | 8.05921 | 85.7815 |
| total | 14.8442 | 39.7592 | 146.888 |

### b3_g2_w2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0605748 | 0.240226 | 1.3633 |
| input_reference | 1.89191 | 7.58056 | 19.4461 |
| progress_reward | -1.63191 | 1.97349 | 1.98651 |
| slack_linear | 9.0914e-06 | 9.09151e-06 | 9.09183e-06 |
| slack_quadratic | 8.26536e-15 | 8.26556e-15 | 8.26614e-15 |
| state_tracking | 13.4085 | 44.9774 | 81.3812 |
| terminal_tracking | 4.89866 | 20.4454 | 85.6996 |
| total | 18.6277 | 70.2115 | 161.33 |

### b4_g1_w1

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00169038 | 0.00694025 | 0.0308396 |
| input_reference | 0.130025 | 0.475193 | 2.728 |
| progress_reward | -0.437926 | 0.502642 | 0.513081 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09183e-06 |
| slack_quadratic | 8.26556e-15 | 8.26556e-15 | 8.26614e-15 |
| state_tracking | 0.531311 | 2.58954 | 7.95441 |
| terminal_tracking | 0.209633 | 1.04131 | 3.52327 |
| total | 0.434742 | 3.79669 | 13.0653 |

### b4_g1_w2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00170565 | 0.00704492 | 0.0309279 |
| input_reference | 0.130413 | 0.474328 | 2.79993 |
| progress_reward | -0.877559 | 1.0063 | 1.02773 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09181e-06 |
| slack_quadratic | 8.26556e-15 | 8.26556e-15 | 8.2661e-15 |
| state_tracking | 0.536362 | 2.55336 | 7.79525 |
| terminal_tracking | 0.210674 | 1.06043 | 3.52819 |
| total | 0.00160456 | 3.68279 | 12.7539 |

### b4_g2_w0

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0395907 | 0.146691 | 1.31841 |
| input_reference | 1.53826 | 6.05949 | 13.0396 |
| progress_reward | 0 | 0 | 0 |
| slack_linear | 9.09143e-06 | 9.09151e-06 | 9.09184e-06 |
| slack_quadratic | 8.26541e-15 | 8.26556e-15 | 8.26615e-15 |
| state_tracking | 11.0686 | 35.4275 | 70.5312 |
| terminal_tracking | 3.86055 | 8.93556 | 85.3722 |
| total | 16.507 | 49.9254 | 145.785 |

### b4_g2_w1

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0405008 | 0.145839 | 0.811293 |
| input_reference | 1.55169 | 5.89308 | 12.8645 |
| progress_reward | -0.819045 | 0.985359 | 0.992568 |
| slack_linear | 9.09141e-06 | 9.09151e-06 | 9.09178e-06 |
| slack_quadratic | 8.26538e-15 | 8.26556e-15 | 8.26605e-15 |
| state_tracking | 11.2768 | 32.7901 | 70.961 |
| terminal_tracking | 3.68785 | 8.8862 | 85.689 |
| total | 15.7378 | 47.2311 | 146.765 |

### b4_g2_w2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.0700683 | 0.370997 | 1.78421 |
| input_reference | 2.06378 | 8.43378 | 24.2172 |
| progress_reward | -1.62507 | 1.96999 | 1.98652 |
| slack_linear | 9.0914e-06 | 9.09151e-06 | 9.09184e-06 |
| slack_quadratic | 8.26536e-15 | 8.26556e-15 | 8.26615e-15 |
| state_tracking | 14.6399 | 53.9656 | 119.258 |
| terminal_tracking | 5.48707 | 21.1713 | 120.626 |
| total | 20.6357 | 84.4936 | 242.278 |

### support_injected_w2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00248671 | 0.0117423 | 0.0412525 |
| input_reference | 0.149097 | 0.575207 | 3.06693 |
| progress_reward | -0.879396 | 1.00552 | 1.02727 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09182e-06 |
| slack_quadratic | 8.26555e-15 | 8.26556e-15 | 8.26612e-15 |
| state_tracking | 0.620795 | 3.02518 | 9.06802 |
| terminal_tracking | 0.228478 | 1.07551 | 3.6769 |
| total | 0.12147 | 4.20111 | 15.178 |

### support_zero_w2

| component | mean | p95_abs | max_abs |
| --- | --- | --- | --- |
| input_increment | 0.00170562 | 0.00654877 | 0.0305375 |
| input_reference | 0.132035 | 0.470801 | 2.71583 |
| progress_reward | -0.877778 | 1.00647 | 1.02764 |
| slack_linear | 9.09151e-06 | 9.09151e-06 | 9.09178e-06 |
| slack_quadratic | 8.26556e-15 | 8.26556e-15 | 8.26605e-15 |
| state_tracking | 0.542334 | 2.57802 | 7.95847 |
| terminal_tracking | 0.210652 | 1.02394 | 3.43231 |
| total | 0.00895769 | 3.51109 | 13.1826 |

## Selected-case sectors

### b0

| sector | plan_ey_rms | plan_v_rms | local_ey_rms | speed_mean | steer_max | rate_limit_s | acceleration_max | braking_min | longitudinal_util_max | front_max | rear_max | ay_max | planner_mean | codriver_mean | reserve_min | progress_cost_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long_straight | 0.00363092 | 0.179279 | 0.000305414 | 2.79083 | 0.229629 | 0.09 | 0.282168 | -0.794776 | 0.264925 | 0.163303 | 0.159908 | 1.52827 | 0.0231672 | 0.000810538 | 0.233294 | 0 |
| hairpin | 0.016858 | 0.232933 | 0.000745784 | 1.61715 | 0.939596 | 0.94 | 0.305986 | -1.13343 | 0.377811 | 0.352145 | 0.305072 | 3.13861 | 0.0277749 | 0.000845941 | 0.296998 | 0 |
| acceleration_zone | 0.00409273 | 0.197178 | 0.000253901 | 2.22957 | 0.121916 | 0 | 0.350216 | -0.0550566 | 0.175108 | 0.0984143 | 0.0968696 | 0.916096 | 0.0253422 | 0.000839659 | 0.30491 | 0 |
| medium_corner | 0.0039333 | 0.159443 | 0.000348877 | 2.38693 | 0.324206 | 0.07 | 0.3415 | -0.382457 | 0.17075 | 0.22256 | 0.213777 | 2.07651 | 0.0265121 | 0.000859111 | 0.205869 | 0 |
| fast_sweeper | 0.000758981 | 0.0457358 | 8.80983e-05 | 2.97414 | 0.11189 | 0 | 0.263016 | -0.202378 | 0.131508 | 0.131209 | 0.13088 | 1.28426 | 0.0216801 | 0.0007479 | 0.301065 | 0 |
| direction_change | 0.00152251 | 0.149393 | 0.000168577 | 2.77128 | 0.23699 | 0.01 | 0.301835 | -0.478025 | 0.159342 | 0.21645 | 0.207026 | 2.01434 | 0.0228912 | 0.000836028 | 0.302341 | 0 |
| second_straight | 0.000641783 | 0.0828505 | 7.18895e-05 | 2.96686 | 0.201461 | 0 | 0.0170804 | -0.425493 | 0.141831 | 0.198363 | 0.194751 | 1.89639 | 0.0225485 | 0.000831552 | 0.302195 | 0 |
| technical_section | 0.00706565 | 0.161966 | 0.000611677 | 2.29793 | 0.814256 | 0.78 | 0.346911 | -0.669012 | 0.223004 | 0.363492 | 0.311037 | 3.22883 | 0.0271232 | 0.000971146 | 0.201491 | 0 |
| return_complex | 0.00243592 | 0.118443 | 0.000406282 | 2.76078 | 0.256851 | 0.09 | 0.282377 | -0.458887 | 0.152962 | 0.2279 | 0.20546 | 2.08142 | 0.023158 | 0.000853784 | 0.301775 | 0 |

### b3_g2.5_w1

| sector | plan_ey_rms | plan_v_rms | local_ey_rms | speed_mean | steer_max | rate_limit_s | acceleration_max | braking_min | longitudinal_util_max | front_max | rear_max | ay_max | planner_mean | codriver_mean | reserve_min | progress_cost_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long_straight | 0.154743 | 1.4933 | 0.00446332 | 4.56742 | 0.783521 | 2.16 | 2 | -3 | 1 | 0.923486 | 0.975735 | 9.08896 | 0.0306979 | 0.000795689 | 0.27 | -0.751633 |
| hairpin | 0.105359 | 0.769739 | 0.00251969 | 2.98536 | 0.966379 | 1.17 | 2 | -3 | 1 | 0.828322 | 0.851383 | 7.82785 | 0.0288737 | 0.000833875 | 0.29729 | -0.508549 |
| acceleration_zone | 0.0469348 | 1.15516 | 0.00345265 | 4.66605 | 0.4657 | 0.41 | 2 | -0.922312 | 1 | 0.810321 | 0.833941 | 7.70027 | 0.0346496 | 0.000836191 | 0.258515 | -0.795474 |
| medium_corner | 0.0798194 | 1.20318 | 0.00291928 | 4.53691 | 0.633771 | 0.99 | 2 | -3 | 1 | 0.861327 | 0.921673 | 8.51324 | 0.0312663 | 0.000856523 | 0.300671 | -0.777717 |
| fast_sweeper | 0.0798923 | 1.06008 | 0.00314574 | 4.95504 | 0.601045 | 2.35 | 2 | -3 | 1 | 0.838995 | 0.887403 | 8.17892 | 0.0306443 | 0.000748667 | 0.298706 | -0.834432 |
| direction_change | 0.0964094 | 1.08587 | 0.00377486 | 4.8626 | 0.593495 | 1.53 | 2 | -3 | 1 | 0.866169 | 0.926159 | 8.5555 | 0.0315031 | 0.000837132 | 0.300534 | -0.823232 |
| second_straight | 0.0879858 | 0.725752 | 0.00362192 | 5.30308 | 0.606964 | 1.5 | 2 | -3 | 1 | 0.875415 | 0.941522 | 8.66713 | 0.0326247 | 0.0008246 | 0.301089 | -0.889065 |
| technical_section | 0.0581141 | 1.04909 | 0.00272202 | 4.50148 | 0.6544 | 1.68 | 2 | -3 | 1 | 0.858981 | 0.899279 | 8.17971 | 0.0309061 | 0.000949281 | 0.298185 | -0.762206 |
| return_complex | 0.0253448 | 0.583223 | 0.00177965 | 5.44303 | 0.399932 | 0.47 | 1.22698 | -0.764054 | 0.613489 | 0.84138 | 0.865754 | 7.97471 | 0.0304329 | 0.000856914 | 0.298258 | -0.917482 |

### b3_g2.5_w2

| sector | plan_ey_rms | plan_v_rms | local_ey_rms | speed_mean | steer_max | rate_limit_s | acceleration_max | braking_min | longitudinal_util_max | front_max | rear_max | ay_max | planner_mean | codriver_mean | reserve_min | progress_cost_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long_straight | 0.200289 | 2.1219 | 0.00445927 | 4.15407 | 1 | 2.37 | 2 | -3 | 1 | 0.956075 | 0.989791 | 9.32562 | 0.0305682 | 0.00079386 | 0.27 | -1.35587 |
| hairpin | 0.0537689 | 0.673731 | 0.00220216 | 3.13312 | 0.998635 | 0.99 | 2 | -3 | 1 | 0.930226 | 0.939793 | 8.9667 | 0.0285486 | 0.000837136 | 0.298295 | -1.10042 |
| acceleration_zone | 0.0322642 | 1.00828 | 0.00115604 | 4.86483 | 0.134925 | 0.01 | 1.84326 | 0.557728 | 0.921631 | 0.400467 | 0.384144 | 3.73268 | 0.0275732 | 0.00083983 | 0.307376 | -1.66179 |
| medium_corner | 0.0262376 | 0.742855 | 0.0014847 | 5.02396 | 0.360419 | 0.21 | 1.35237 | -0.85383 | 0.676187 | 0.794812 | 0.816435 | 7.78154 | 0.0283163 | 0.000850138 | 0.307346 | -1.7194 |
| fast_sweeper | 0.0190584 | 0.351509 | 0.000336111 | 5.64785 | 0.122778 | 0 | 0.478978 | 0.227806 | 0.239489 | 0.466107 | 0.458268 | 4.4931 | 0.0286896 | 0.000747514 | 0.308322 | -1.89722 |
| direction_change | 0.0162976 | 0.389834 | 0.00117328 | 5.59839 | 0.273502 | 0.14 | 0.883187 | -0.391504 | 0.441594 | 0.737661 | 0.759094 | 7.28965 | 0.0297613 | 0.00083486 | 0.299543 | -1.87908 |
| second_straight | 0.0135609 | 0.152125 | 0.000511983 | 5.87072 | 0.232555 | 0.02 | 0.281794 | -0.370863 | 0.140897 | 0.769108 | 0.751249 | 7.43566 | 0.0330552 | 0.000837116 | 0.299721 | -1.9586 |
| technical_section | 0.0774126 | 1.34467 | 0.00294998 | 4.30415 | 0.823181 | 2.1 | 2 | -3 | 1 | 0.900198 | 0.954945 | 8.61726 | 0.0317226 | 0.000959289 | 0.293329 | -1.45476 |
| return_complex | 0.0564253 | 0.905759 | 0.00307284 | 5.0971 | 0.577752 | 3.03 | 2 | -3 | 1 | 0.843672 | 0.928754 | 8.49345 | 0.0320999 | 0.000852466 | 0.300605 | -1.72656 |

### b4_g1_w2

| sector | plan_ey_rms | plan_v_rms | local_ey_rms | speed_mean | steer_max | rate_limit_s | acceleration_max | braking_min | longitudinal_util_max | front_max | rear_max | ay_max | planner_mean | codriver_mean | reserve_min | progress_cost_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long_straight | 0.00350186 | 0.179733 | 0.000301296 | 2.79916 | 0.229725 | 0.09 | 0.284289 | -0.768222 | 0.256074 | 0.163763 | 0.160034 | 1.5448 | 0.0222202 | 0.000785546 | 0.301091 | -0.927923 |
| hairpin | 0.0174928 | 0.240972 | 0.000769109 | 1.62857 | 0.92802 | 0.82 | 0.304575 | -1.1182 | 0.372734 | 0.349056 | 0.306685 | 3.09118 | 0.0270635 | 0.000823786 | 0.295703 | -0.569956 |
| acceleration_zone | 0.00391497 | 0.188797 | 0.000256121 | 2.23886 | 0.121944 | 0 | 0.350865 | -0.0528145 | 0.175433 | 0.0990259 | 0.0975288 | 0.921917 | 0.0247059 | 0.000827497 | 0.304133 | -0.751602 |
| medium_corner | 0.00394386 | 0.157045 | 0.000333614 | 2.3964 | 0.320159 | 0.04 | 0.340665 | -0.380218 | 0.170332 | 0.225122 | 0.21355 | 2.07875 | 0.0238719 | 0.000841878 | 0.303246 | -0.816959 |
| fast_sweeper | 0.000769003 | 0.04285 | 8.91821e-05 | 2.98294 | 0.111605 | 0 | 0.255032 | -0.169644 | 0.127516 | 0.132109 | 0.131396 | 1.28906 | 0.0211902 | 0.000738372 | 0.30071 | -0.996715 |
| direction_change | 0.00151902 | 0.147894 | 0.00017356 | 2.77987 | 0.237303 | 0.04 | 0.302197 | -0.479056 | 0.159685 | 0.214258 | 0.211523 | 2.04165 | 0.0224808 | 0.0008249 | 0.301846 | -0.928246 |
| second_straight | 0.000613631 | 0.0848934 | 7.14386e-05 | 2.97601 | 0.203016 | 0 | 0.0162725 | -0.425844 | 0.141948 | 0.201265 | 0.197199 | 1.92078 | 0.0219548 | 0.000815539 | 0.301523 | -0.989595 |
| technical_section | 0.00738407 | 0.165584 | 0.000618401 | 2.3068 | 0.812724 | 0.73 | 0.345625 | -0.656684 | 0.218895 | 0.361802 | 0.304906 | 3.21799 | 0.0260583 | 0.000955805 | 0.29548 | -0.774294 |
| return_complex | 0.00247874 | 0.119093 | 0.000413259 | 2.76972 | 0.254127 | 0.11 | 0.283864 | -0.459815 | 0.153272 | 0.220857 | 0.209953 | 2.09402 | 0.0225294 | 0.000836606 | 0.301223 | -0.928194 |

### b4_g2_w0

| sector | plan_ey_rms | plan_v_rms | local_ey_rms | speed_mean | steer_max | rate_limit_s | acceleration_max | braking_min | longitudinal_util_max | front_max | rear_max | ay_max | planner_mean | codriver_mean | reserve_min | progress_cost_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long_straight | 0.00930338 | 0.579197 | 0.00101681 | 5.44198 | 0.328158 | 0.36 | 1.19091 | -2.3609 | 0.786967 | 0.743465 | 0.772825 | 7.10012 | 0.029846 | 0.000800049 | 0.257363 | 0 |
| hairpin | 0.0684526 | 0.571259 | 0.00223339 | 2.85018 | 0.879456 | 1.71 | 1.45362 | -3 | 1 | 0.952071 | 0.976243 | 9.22773 | 0.0281997 | 0.000831837 | 0.29755 | 0 |
| acceleration_zone | 0.0195545 | 0.750839 | 0.000870417 | 4.11693 | 0.134253 | 0.02 | 1.24119 | 0.0259521 | 0.620594 | 0.312675 | 0.299906 | 2.86897 | 0.0259926 | 0.000861257 | 0.295149 | 0 |
| medium_corner | 0.0152832 | 0.548606 | 0.00115317 | 4.42369 | 0.356868 | 0.2 | 1.29571 | -0.783225 | 0.647853 | 0.690456 | 0.685807 | 6.6497 | 0.0263758 | 0.000852342 | 0.305021 | 0 |
| fast_sweeper | 0.0188887 | 0.419198 | 0.00032759 | 5.59444 | 0.12741 | 0.01 | 0.9397 | -0.293151 | 0.46985 | 0.462638 | 0.45174 | 4.45833 | 0.0285997 | 0.000744557 | 0.298575 | 0 |
| direction_change | 0.0123686 | 0.458917 | 0.000937187 | 5.27981 | 0.255317 | 0.17 | 0.856674 | -1.18993 | 0.428337 | 0.69847 | 0.709789 | 6.73022 | 0.0285063 | 0.000838572 | 0.297228 | 0 |
| second_straight | 0.0111325 | 0.199228 | 0.000449342 | 5.80534 | 0.200218 | 0.06 | 0.330073 | -1.11673 | 0.372245 | 0.693028 | 0.700686 | 6.7563 | 0.0318949 | 0.000824 | 0.299619 | 0 |
| technical_section | 0.0399428 | 0.623845 | 0.0022431 | 4.17972 | 0.759544 | 2.45 | 2 | -2.61096 | 1 | 0.876351 | 0.910343 | 8.26581 | 0.0290167 | 0.00096937 | 0.29787 | 0 |
| return_complex | 0.0183093 | 0.477895 | 0.00132025 | 5.14953 | 0.323236 | 0.47 | 1.11427 | -1.10816 | 0.557133 | 0.713478 | 0.71253 | 6.87566 | 0.0281633 | 0.000846564 | 0.29789 | 0 |

### b4_g2_w2

| sector | plan_ey_rms | plan_v_rms | local_ey_rms | speed_mean | steer_max | rate_limit_s | acceleration_max | braking_min | longitudinal_util_max | front_max | rear_max | ay_max | planner_mean | codriver_mean | reserve_min | progress_cost_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long_straight | 0.00890094 | 0.6185 | 0.00100602 | 5.38969 | 0.362653 | 0.35 | 1.81086 | -2.29618 | 0.905432 | 0.737886 | 0.767691 | 7.04611 | 0.0288855 | 0.000784997 | 0.298509 | -1.79313 |
| hairpin | 0.068136 | 0.585573 | 0.00217372 | 2.86609 | 0.83737 | 1.72 | 1.30727 | -3 | 1 | 0.939593 | 0.974358 | 9.20159 | 0.0275038 | 0.000816253 | 0.297371 | -0.974005 |
| acceleration_zone | 0.0201938 | 0.741601 | 0.000869832 | 4.1226 | 0.133808 | 0.02 | 1.25917 | 0.0104425 | 0.629584 | 0.313714 | 0.30111 | 2.86008 | 0.0246371 | 0.000821001 | 0.303632 | -1.40198 |
| medium_corner | 0.0147956 | 0.54169 | 0.0011479 | 4.43036 | 0.370316 | 0.28 | 1.30148 | -0.786161 | 0.650742 | 0.693607 | 0.683154 | 6.54266 | 0.0249462 | 0.000834229 | 0.304103 | -1.52044 |
| fast_sweeper | 0.0188676 | 0.41282 | 0.000332536 | 5.60206 | 0.125316 | 0.01 | 0.933877 | -0.329718 | 0.466939 | 0.459648 | 0.451113 | 4.45104 | 0.0279429 | 0.00073354 | 0.305723 | -1.88259 |
| direction_change | 0.0123069 | 0.457076 | 0.000964188 | 5.28674 | 0.24222 | 0.2 | 0.854882 | -1.1832 | 0.427441 | 0.695907 | 0.705115 | 6.74579 | 0.0277123 | 0.000820153 | 0.30648 | -1.77286 |
| second_straight | 0.0108444 | 0.185331 | 0.000438774 | 5.81448 | 0.194423 | 0.03 | 0.332761 | -1.13944 | 0.379814 | 0.691679 | 0.701981 | 6.79926 | 0.0313652 | 0.000811608 | 0.298934 | -1.93388 |
| technical_section | 0.0575432 | 0.708439 | 0.00259977 | 4.14031 | 0.774437 | 3.94 | 2 | -3 | 1 | 0.881068 | 0.89708 | 8.43076 | 0.0291369 | 0.000943731 | 0.29114 | -1.39264 |
| return_complex | 0.0185611 | 0.482355 | 0.00137604 | 5.14946 | 0.417957 | 0.81 | 1.18189 | -1.12748 | 0.590945 | 0.745499 | 0.735023 | 6.93582 | 0.0276591 | 0.000833092 | 0.297293 | -1.73251 |

## Frozen nominal-state defect,10ms, independent plant

| case | vx | vy | r | e_psi | s_abs | e_y |
| --- | --- | --- | --- | --- | --- | --- |
| b0 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b1_g1.25 | 0.00958395 | 0.0352557 | 0.033869 | 0.000212932 | 6.84424e-05 | 0.000182251 |
| b1_g1.5 | 0.0139158 | 0.0267742 | 0.0468784 | 0.000302947 | 0.000101867 | 0.000139432 |
| b1_g1.75 | 0.0191612 | 0.0331196 | 0.0621098 | 0.0004091 | 0.000141179 | 0.000168406 |
| b1_g2 | 0.02507 | 0.0468463 | 0.0795592 | 0.000531431 | 0.0001863 | 0.000237817 |
| b1_g2.25 | 0.0304843 | 0.058864 | 0.0992219 | 0.000669972 | 0.000237153 | 0.000296422 |
| b1_g2.5 | 0.0376493 | 0.0727504 | 0.121094 | 0.000824735 | 0.000293659 | 0.000366132 |
| b2_w0.1 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b2_w0.25 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b2_w0.5 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b2_w1 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b2_w2 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b2_w4 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b2_w8 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b3_g2.5_w1 | 0.0376493 | 0.0727504 | 0.121094 | 0.000824735 | 0.000293659 | 0.000366132 |
| b3_g2.5_w2 | 0.0376493 | 0.0727504 | 0.121094 | 0.000824735 | 0.000293659 | 0.000366132 |
| b3_g2_w1 | 0.02507 | 0.0468463 | 0.0795592 | 0.000531431 | 0.0001863 | 0.000237817 |
| b3_g2_w2 | 0.02507 | 0.0468463 | 0.0795592 | 0.000531431 | 0.0001863 | 0.000237817 |
| b4_g1_w1 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b4_g1_w2 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| b4_g2_w0 | 0.02507 | 0.0468463 | 0.0795592 | 0.000531431 | 0.0001863 | 0.000237817 |
| b4_g2_w1 | 0.02507 | 0.0468463 | 0.0795592 | 0.000531431 | 0.0001863 | 0.000237817 |
| b4_g2_w2 | 0.02507 | 0.0468463 | 0.0795592 | 0.000531431 | 0.0001863 | 0.000237817 |
| support_injected_w2 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |
| support_zero_w2 | 0.00619002 | 0.0414639 | 0.0230794 | 0.000140428 | 4.09869e-05 | 0.000214848 |

## Mean stage tracking cost by frozen state channel

| case | vx | vy | r | e_psi | e_y |
| --- | --- | --- | --- | --- | --- |
| b0 | 0.310217 | 0.0137802 | 0.0261088 | 0.159731 | 0.0166595 |
| b1_g1.25 | 0.670766 | 0.0382774 | 0.126348 | 0.390106 | 0.0843317 |
| b1_g1.5 | 1.22066 | 0.183062 | 0.306157 | 1.37125 | 0.310101 |
| b1_g1.75 | 2.0689 | 0.606193 | 0.297351 | 2.10756 | 0.26926 |
| b1_g2 | 4.50442 | 1.57138 | 0.899116 | 5.01311 | 0.94959 |
| b1_g2.25 | 7.75786 | 2.97389 | 2.22933 | 12.4865 | 4.22654 |
| b1_g2.5 | 11.3617 | 3.3016 | 2.45257 | 13.086 | 4.06784 |
| b2_w0.1 | 0.30981 | 0.013921 | 0.0260277 | 0.159084 | 0.016281 |
| b2_w0.25 | 0.310834 | 0.0139345 | 0.026525 | 0.160778 | 0.0169506 |
| b2_w0.5 | 0.311997 | 0.0139266 | 0.0271873 | 0.162774 | 0.0179633 |
| b2_w1 | 0.312645 | 0.0139177 | 0.0265546 | 0.159371 | 0.0171363 |
| b2_w2 | 0.31712 | 0.0139176 | 0.0279147 | 0.160523 | 0.0185689 |
| b2_w4 | 0.324145 | 0.0138943 | 0.0279995 | 0.154414 | 0.0176136 |
| b2_w8 | 0.350693 | 0.0138655 | 0.0310927 | 0.151682 | 0.0201183 |
| b3_g2.5_w1 | 17.6223 | 3.86124 | 5.15468 | 19.9576 | 6.57969 |
| b3_g2.5_w2 | 21.4019 | 3.43102 | 3.80639 | 22.5447 | 6.73034 |
| b3_g2_w1 | 3.8825 | 1.56935 | 0.525577 | 3.97958 | 0.66235 |
| b3_g2_w2 | 4.88615 | 1.60695 | 0.878459 | 5.04675 | 0.990178 |
| b4_g1_w1 | 0.312689 | 0.0138788 | 0.0269028 | 0.160374 | 0.0174664 |
| b4_g1_w2 | 0.31653 | 0.0138601 | 0.0277309 | 0.159807 | 0.0184341 |
| b4_g2_w0 | 4.03935 | 1.55012 | 0.55097 | 4.1515 | 0.776617 |
| b4_g2_w1 | 4.10593 | 1.58025 | 0.644768 | 4.21888 | 0.726937 |
| b4_g2_w2 | 5.2814 | 1.6028 | 1.01453 | 5.46047 | 1.28067 |
| support_injected_w2 | 0.389707 | 0.0132287 | 0.0350069 | 0.159438 | 0.0234148 |
| support_zero_w2 | 0.324325 | 0.013825 | 0.0278363 | 0.158272 | 0.0180745 |

No reference-state redesign or codriver switching was performed. Residuals diagnose the geometric approximation; they are not accepted-solver constraint violations.
