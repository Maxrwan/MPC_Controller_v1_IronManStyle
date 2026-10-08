# Task007C C3 controlled grid

Analyzed cells: 18/18. Grid analysis complete.

Single-lap screens retain the existing rolling start at s_abs=1m; their first lap-end time is a rolling segment, not a complete geometric lap. Comparisons share this start. Sustained confirmations report later complete laps separately.

Candidate C weights remain fixed. Only N changes; dt=0.1s, lambda0.

All comparisons use matched physical availability histories. Offline analysis can overlap these imposed-timing runs; their measured preparation wall times are not isolated compute benchmarks. Fresh measured repetitions remain a separate acceptance requirement.

| Gamma | History | N | Boundary samples | Solver failures | Slack max m | Clearance min m | Heading TV rad | Steering TV rad | Rate limit s | Beta p95 rad | Tracking ey RMS m | Lap s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.8 | fixed | 4 | 0 | 0 | 9.0918e-11 | 0.32641 | 9.6472 | 6.0848 | 5.49 | 0.093856 | 0.0012852 | 33.801 |
| 1.8 | fixed | 6 | 0 | 0 | 9.0918e-11 | 0.3311 | 8.0322 | 4.9165 | 4.01 | 0.080372 | 0.0011083 | 33.812 |
| 1.8 | fixed | 8 | 0 | 0 | 9.0918e-11 | 0.32831 | 7.5789 | 4.6057 | 3.43 | 0.078667 | 0.001068 | 33.773 |
| 1.8 | smooth | 4 | 0 | 0 | 9.0918e-11 | 0.32641 | 11.112 | 7.4795 | 3.36 | 0.09402 | 0.0013898 | 33.949 |
| 1.8 | smooth | 6 | 0 | 0 | 9.0918e-11 | 0.33138 | 8.0289 | 4.8691 | 1.99 | 0.080617 | 0.0010834 | 33.779 |
| 1.8 | smooth | 8 | 0 | 0 | 9.0918e-11 | 0.32743 | 7.542 | 4.6383 | 1.73 | 0.078804 | 0.0010286 | 33.766 |
| 2 | fixed | 4 | 0 | 0 | 9.0918e-11 | 0.32061 | 11.993 | 8.0008 | 8.56 | 0.14593 | 0.0015122 | 31.267 |
| 2 | fixed | 6 | 0 | 0 | 9.0919e-11 | 0.3246 | 9.3709 | 5.6601 | 5.37 | 0.11435 | 0.0013623 | 30.937 |
| 2 | fixed | 8 | 0 | 0 | 9.0918e-11 | 0.32917 | 8.0091 | 4.9598 | 4.35 | 0.10468 | 0.0012048 | 30.947 |
| 2 | smooth | 4 | 0 | 0 | 9.0918e-11 | 0.32057 | 11.214 | 7.342 | 3.7457 | 0.13605 | 0.0015219 | 31.202 |
| 2 | smooth | 6 | 0 | 0 | 9.0918e-11 | 0.3248 | 9.1283 | 5.6657 | 2.63 | 0.11166 | 0.0013307 | 30.86 |
| 2 | smooth | 8 | 0 | 0 | 9.0918e-11 | 0.32911 | 7.7536 | 4.7402 | 1.95 | 0.10455 | 0.0011991 | 30.927 |
| 2.1 | fixed | 4 | 0 | 0 | 9.0919e-11 | 0.31962 | 11.594 | 7.2668 | 7.72 | 0.15097 | 0.001608 | 30.819 |
| 2.1 | fixed | 6 | 0 | 0 | 9.0919e-11 | 0.32021 | 9.1724 | 5.7514 | 5.86 | 0.12544 | 0.001379 | 30.229 |
| 2.1 | fixed | 8 | 0 | 0 | 9.0916e-11 | 0.32617 | 9.9213 | 6.3963 | 6.236 | 0.12312 | 0.0014502 | 30.293 |
| 2.1 | smooth | 4 | 0 | 0 | 9.0917e-11 | 0.31947 | 10.899 | 6.8937 | 3.2958 | 0.14828 | 0.0015762 | 30.743 |
| 2.1 | smooth | 6 | 0 | 0 | 9.0918e-11 | 0.32061 | 8.2775 | 5.3052 | 2.4008 | 0.12248 | 0.0012823 | 30.21 |
| 2.1 | smooth | 8 | 0 | 0 | 9.0916e-11 | 0.3257 | 10.324 | 7.1581 | 3.6458 | 0.12847 | 0.0014585 | 30.313 |

## Deltas from matched baseline

Positive deltas mean a larger metric. These are separate diagnostics, not a combined score or an acceptance rule. A small lap-time gain never compensates for a safety failure.

| Gamma | History | N | Delta Heading TV rad | Delta Steering TV rad | Delta Rate limit s | Delta Beta p95 rad | Delta Clearance min m | Delta Tracking ey RMS m | Delta Lap s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.8 | fixed | 6 | -1.615 | -1.1683 | -1.48 | -0.013485 | 0.0046846 | -0.00017691 | 0.010079 |
| 1.8 | fixed | 8 | -2.0682 | -1.4791 | -2.06 | -0.01519 | 0.0018995 | -0.0002172 | -0.028615 |
| 1.8 | smooth | 6 | -3.0835 | -2.6105 | -1.37 | -0.013403 | 0.0049701 | -0.00030643 | -0.16936 |
| 1.8 | smooth | 8 | -3.5704 | -2.8413 | -1.63 | -0.015216 | 0.0010162 | -0.00036119 | -0.18221 |
| 2 | fixed | 6 | -2.6219 | -2.3407 | -3.19 | -0.031585 | 0.0039934 | -0.00014987 | -0.33016 |
| 2 | fixed | 8 | -3.9838 | -3.041 | -4.21 | -0.041253 | 0.0085624 | -0.00030732 | -0.31996 |
| 2 | smooth | 6 | -2.0859 | -1.6763 | -1.1157 | -0.024395 | 0.0042368 | -0.00019119 | -0.34251 |
| 2 | smooth | 8 | -3.4606 | -2.6018 | -1.7957 | -0.031506 | 0.0085423 | -0.0003228 | -0.27484 |
| 2.1 | fixed | 6 | -2.4219 | -1.5154 | -1.86 | -0.02553 | 0.00059195 | -0.000229 | -0.58967 |
| 2.1 | fixed | 8 | -1.673 | -0.87051 | -1.484 | -0.027844 | 0.0065469 | -0.00015788 | -0.52581 |
| 2.1 | smooth | 6 | -2.6217 | -1.5886 | -0.89499 | -0.025805 | 0.0011396 | -0.00029395 | -0.5327 |
| 2.1 | smooth | 8 | -0.5755 | 0.26434 | 0.35001 | -0.019816 | 0.0062318 | -0.00011772 | -0.42965 |

## Timing-history spread

Absolute fixed-versus-smooth differences below describe these two retained histories only. They do not estimate a population distribution.

| Gamma | N | Abs spread Heading TV rad | Abs spread Steering TV rad | Abs spread Rate limit s | Abs spread Beta p95 rad | Abs spread Clearance min m | Abs spread Tracking ey RMS m | Abs spread Lap s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.8 | 4 | 1.4653 | 1.3948 | 2.13 | 0.00016391 | 2.0314e-06 | 0.00010461 | 0.14713 |
| 1.8 | 6 | 0.0032612 | 0.047427 | 2.02 | 0.00024569 | 0.0002835 | 2.492e-05 | 0.032309 |
| 1.8 | 8 | 0.036915 | 0.032548 | 1.7 | 0.00013758 | 0.00088533 | 3.9388e-05 | 0.0064615 |
| 2 | 4 | 0.77864 | 0.65876 | 4.8143 | 0.0098791 | 4.0084e-05 | 9.7088e-06 | 0.064879 |
| 2 | 6 | 0.2426 | 0.005603 | 2.74 | 0.0026889 | 0.00020332 | 3.1618e-05 | 0.077228 |
| 2 | 8 | 0.25549 | 0.2196 | 2.4 | 0.00013257 | 6.0099e-05 | 5.7626e-06 | 0.01976 |
| 2.1 | 4 | 0.69506 | 0.37309 | 4.4242 | 0.0026844 | 0.00014753 | 3.1817e-05 | 0.075873 |
| 2.1 | 6 | 0.89487 | 0.44621 | 3.4592 | 0.0029593 | 0.00040015 | 9.677e-05 | 0.018911 |
| 2.1 | 8 | 0.40244 | 0.76176 | 2.5902 | 0.005344 | 0.00046264 | 8.346e-06 | 0.020281 |

## Comparable prediction prefix

Accepted packets only. State predictions use their first0.4s in all cases. Steering TV spans the four corresponding held input nodes (three differences). Full-horizon variation is exported separately with duration normalization.

| Gamma | History | N | First0.4s heading TV | First0.4s steering TV | First0.4s reversals | Iterations mean | Planner misses | Codriver misses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.8 | fixed | 4 | 0.092776 | 0.050559 | 0.70118 | 9.7929 | 0 | 0 |
| 1.8 | fixed | 6 | 0.06738 | 0.03444 | 0.52367 | 10.311 | 0 | 0 |
| 1.8 | fixed | 8 | 0.067228 | 0.032684 | 0.35799 | 10.516 | 0 | 0 |
| 1.8 | smooth | 4 | 0.10388 | 0.058494 | 0.70588 | 9.9617 | 0 | 0 |
| 1.8 | smooth | 6 | 0.067556 | 0.034192 | 0.53846 | 10.329 | 0 | 0 |
| 1.8 | smooth | 8 | 0.067259 | 0.032609 | 0.36391 | 10.51 | 0 | 0 |
| 2 | fixed | 4 | 0.11591 | 0.064935 | 0.88179 | 11.304 | 0 | 0 |
| 2 | fixed | 6 | 0.087009 | 0.043698 | 0.61613 | 11.877 | 0 | 0 |
| 2 | fixed | 8 | 0.076777 | 0.038804 | 0.41935 | 12.175 | 0 | 0 |
| 2 | smooth | 4 | 0.11544 | 0.064379 | 0.83974 | 11.231 | 0 | 0 |
| 2 | smooth | 6 | 0.08283 | 0.044147 | 0.58576 | 11.906 | 0 | 0 |
| 2 | smooth | 8 | 0.074877 | 0.03655 | 0.43366 | 12.104 | 0 | 0 |
| 2.1 | fixed | 4 | 0.12265 | 0.066166 | 0.81494 | 11.526 | 0 | 0 |
| 2.1 | fixed | 6 | 0.083498 | 0.043531 | 0.61589 | 12.281 | 0 | 0 |
| 2.1 | fixed | 8 | 0.092833 | 0.049169 | 0.49505 | 12.834 | 0 | 0 |
| 2.1 | smooth | 4 | 0.12054 | 0.064342 | 0.84091 | 11.485 | 0 | 0 |
| 2.1 | smooth | 6 | 0.076546 | 0.038864 | 0.5596 | 12.195 | 0 | 0 |
| 2.1 | smooth | 8 | 0.09438 | 0.050802 | 0.53135 | 12.868 | 0 | 0 |

No production selection is made by this generated report. Retain physical failures, finite-trace censoring and the later representative/measured outcomes in the final review.
