# Task007C representative-history review

Gamma2 is complete across fixed, smooth, median, pathological E and pathological F. This is a deliberately selected five-history diagnostic set; ranges below are descriptive and are not population confidence intervals. Gamma2.1/2.2 recorded-history validation is complete (see their separate history reports). Gamma2 measured repetitions are complete and gamma2.2 measured repetitions are active; final acceptance remains pending.

The five formulations are compared on the same observed progress interval, approximately1–145.94m. Native endpoints differ slightly and are disclosed in the JSON. Whole-record safety failures are included even if outside that prefix. Each single screen starts at s_abs=1m, so its first counted lap end closes a rolling segment.

| alpha_vy | N | Lambda | Histories | Records reaching first lap end | Whole-record boundary samples | Common epsi TV range rad | Common steering TV range rad | Tracking ey RMS range m |
|---|---|---|---|---|---|---|---|---|
| 1 | 4 | 0 | 5 | 3 | 0 | 10.278–28.651 | 6.925–19.662 | 0.0014735–0.0027508 |
| 1 | 6 | 0 | 5 | 4 | 0 | 8.2144–8.4953 | 5.2636–5.5597 | 0.0012838–0.0013505 |
| 1 | 8 | 0 | 5 | 4 | 0 | 6.9156–7.4964 | 4.4024–5.0444 | 0.0011108–0.0012211 |
| 0.5 | 4 | 0 | 5 | 2 | 59 | 9.8404–31.083 | 6.2788–20.235 | 0.0014609–0.0029653 |
| 1 | 4 | 4 | 5 | 2 | 100 | 9.6204–28.686 | 6.0233–18.557 | 0.0014267–0.0027574 |

## Rejected initial candidates

Half-vy N4/lambda0 fails pathological E in the fast sweeper:59 boundary samples, max ey0.583446m, clearance−0.033446m and slack0.111458m. Active nominal ey reaches0.581448m and local position error stays below0.010m around the excursion. The F replay is also censored but adds no boundary crossing. Do not take this ablation into measured finalist repetitions.

Baseline-weight N4/lambda4 fails pathological F in the return complex:100 boundary samples, max abs ey0.637804m, clearance−0.087804m and slack0.162558m. Nominal abs ey reaches0.631948m; local ey error remains below0.010m near the excursion. No solver or deadline failure caused either boundary event. Reject this static-progress candidate; its favorable fixed/smooth gamma2 results are insufficient.

Exact reviewed failures are hash-bound in `reviewed_failures.json`; individual review JSONs retain event windows, progress, local errors and the independent-continuation decision. Original records are not deleted or rewritten.

## Remaining horizon candidates

N6 and N8 retain baseline dynamic-state weights and lambda0. Both complete the E/F rolling screens safely, while the median history ends after30.45s before the gamma2 lap end. The two codriver misses in median remain recorded. N6/N8 are still candidates, not accepted production configurations: higher-demand histories, exact deterministic repeats, zero/injected support and sustained two-complete-lap confirmations are now complete. See `TASK007C_SUSTAINED_CONFIRMATION.md` for nonuniform sustained smoothness and `TASK007C_MEASURED_RESULTS.md` for measured outcome distributions as they are analyzed.

No adaptive progress gate is supported. The new failures strengthen the need to judge timing robustness and softened-track slack before lap speed, and to distinguish an unsafe APEX path from local vehicle tracking error.

Exact per-history and all-history tables: `TASK007C_G2_HISTORY_RESULTS.md`. Shared-prefix evidence: `results/task007c_resume/g2_all_histories_common_progress.json`.
