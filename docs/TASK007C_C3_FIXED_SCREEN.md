# Task007C C3 fixed-timing screen

Interim result, 2026-10-08. All nine fixed-history cells completed without boundary, solver, planner or codriver deadline failures. Baseline costs, lambda0 and dt0.1s are held constant. No horizon is selected yet.

| Gamma | N | Lap s | Heading TV rad | Steering TV rad | Rate-limit s | Beta p95 rad | Clearance m | Tracking ey RMS m |
|---|---|---|---|---|---|---|---|---|
| 1.8 | 4 | 33.80143 | 9.64717 | 6.08478 | 5.49000 | 0.09386 | 0.32641 | 0.00129 |
| 1.8 | 6 | 33.81151 | 8.03219 | 4.91648 | 4.01000 | 0.08037 | 0.33110 | 0.00111 |
| 1.8 | 8 | 33.77281 | 7.57893 | 4.60573 | 3.43000 | 0.07867 | 0.32831 | 0.00107 |
| 2.0 | 4 | 31.26713 | 11.99287 | 8.00079 | 8.56000 | 0.14593 | 0.32061 | 0.00151 |
| 2.0 | 6 | 30.93697 | 9.37093 | 5.66012 | 5.37000 | 0.11435 | 0.32460 | 0.00136 |
| 2.0 | 8 | 30.94717 | 8.00906 | 4.95982 | 4.35000 | 0.10468 | 0.32917 | 0.00120 |
| 2.1 | 4 | 30.81883 | 11.59425 | 7.26682 | 7.72000 | 0.15097 | 0.31962 | 0.00161 |
| 2.1 | 6 | 30.22916 | 9.17239 | 5.75139 | 5.86000 | 0.12544 | 0.32021 | 0.00138 |
| 2.1 | 8 | 30.29302 | 9.92125 | 6.39631 | 6.23600 | 0.12312 | 0.32617 | 0.00145 |

N6 reduces heading and steering variation relative to N4 at every fixed-timing point. N8 further reduces these indicators at gamma1.8 and2.0, but gamma2.1 heading/steering variation and rate-limit time are worse than N6. The horizon benefit is therefore not monotonic. These imposed-timing results isolate formulation behavior; preparation times collected while offline analysis ran are not fair computational benchmarks.

Smooth, median and pathological E/F histories, isolated measured repetitions and compute costs remain necessary before choosing a horizon. The common first0.4s prediction prefix is exported separately to avoid comparing unequal horizon lengths as though they were equivalent. Accepted-packet realized-future errors include subsequent feedback and replanning and are not pure model error.

No production defaults, TVLQR settings, physical plant or timing architecture were changed.
