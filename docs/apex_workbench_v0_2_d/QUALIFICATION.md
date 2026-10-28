# V0.2-D one-shot numerical qualification

**V0.2_QUALIFICATION_COMPLETE_PENDING_SCIENTIFIC_REVIEW.** Recorded 29 October 2026.

The single authorized campaign completed **17/17 distinct executions, 3,700 actual plant intervals
and 8.5 simulated seconds**, exit 0. There were no retries, substitute runs, supplementary grids or
extra trajectories. The verified `apex-vdl-qualification/1` record reports
`qualified_synthetic_comparisons`. All five cases pass numerical convergence and the sampled teaching
window; all four permitted comparisons pass yaw separation and are accepted by the production
comparison reader as **Qualified synthetic comparison — sampled model window; no physical validation**.

Reviewed source: `4897686e79c13757d5ef5b4373b44d4cab99b5bf`. Execution checkout/review delivery:
`6c6c169e483072c48866335aeb82439e24139920`, branch `codex/apex-workbench-v0-2-c`.
Unchanged accepted scientific contract: `0cc7e4f626311aec05977bd3beda40c346fa4214`.
This report records numerical qualification of the accepted finite synthetic protocol, pending
Primary scientific review. It is not formal Verification or physical validation.

## Five cases and four comparison outcomes

All three grids for each case retain the full 0.500 s horizon with completed worker outcomes, valid
evidence, no canonical failure, and zero sampled corridor violations. `E_r` is the nominal-versus-
quarter-grid maximum yaw-rate difference on shared nominal ticks; other channels are listed below.
The required pair signal was exactly **0.0001 rad/s** for every pair.

| Case | Grids complete | Numerics / sampled window | E_r [rad/s] | Peak pair abs(delta r) [rad/s] | Comparison outcome |
|---|---:|---|---:|---:|---|
| `VDL1_BASE` | 3/3 | grid-qualified / within window | 8.109698448471869e-07 | — | Common baseline |
| `VDL1_IZ_HIGH` | 3/3 | grid-qualified / within window | 3.8015363038046424e-07 | 0.008904428222327412 | Qualified synthetic comparison |
| `VDL1_STEER_HIGH` | 3/3 | grid-qualified / within window | 1.0135904908864513e-06 | 0.03336394365255693 | Qualified synthetic comparison |
| `VDL1_CF_HIGH` | 3/3 | grid-qualified / within window | 1.565783290177758e-06 | 0.010852414470119351 | Qualified synthetic comparison |
| `VDL1_CR_HIGH` | 3/3 | grid-qualified / within window | 9.219381430364271e-07 | 0.006275476007459452 | Qualified synthetic comparison |

No case or comparison was inconclusive under the accepted criteria. Per-case numerical status,
sampled-window status and per-pair excitation were evaluated separately. Individual immutable run
summaries still say numerics `not_qualified`; the separate verified qualification record supplies the
later assessment. No source-run summary or historical result was rewritten.

## Preflight and one-shot command

The checkout was clean. All 56 required source hashes matched the reviewed source; case, numerical
and validity documents matched the accepted contract. Installed package/Python/platform identities
matched the preparation environment. No measurement guards or conflicting workers were found;
46341808128 free bytes exceeded the 1 GiB floor, the execution lease was available,
and the approved output directory was absent. The one-shot ledger was written before invocation.

macOS process inspection required host permissions after the sandbox denied `sysctl`; no campaign
had started. An additional reporting assertion incorrectly required a nonempty `threadpoolctl` list.
The installed NumPy build uses Accelerate and the reviewed worker environment also records `[]`.
That reporting assumption was corrected without changing implementation, dependencies, native policy,
limits or scientific criteria. Accelerate native set/get reported SINGLE mode, set status 0 and mode 1.
Empty pool enumeration is an observation limit, not an exact active-BLAS-thread-count measurement.
Both diagnostic events are retained in `preflight_diagnostics.json`.

**Already executed once; shown for the record, not authorization to run again:**

```sh
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python \
  -m tools.apex_workbench.qualification_campaign execute \
  --output-dir results/apex_workbench_qualifications/v0_2_reviewed_20261029 \
  --reviewed-revision 4897686e79c13757d5ef5b4373b44d4cab99b5bf \
  --acknowledge-scientific-execution
```

The existing coordinator serialized the five cases on nominal/half/quarter grids, followed by the
fresh nominal BASE repeat and independent literal nominal BASE canonical-runner reference. No
implementation, case, tolerance, validity filter, frozen profile or historical evidence changed.

## Componentwise convergence and contraction

Exactly the accepted shared nominal ticks were compared, with no interpolation. Only e_psi uses
the canonical wrapped angular difference. For every component: E <= 1e-5 in the listed SI unit and
d1 <= 0.5*d0 + 1e-12. All **30 component checks pass**. Ratios are shown only where both differences
exceed the accepted roundoff floor. The quarter grid is a numerical reference, not truth; these
observations do not prove global error bounds or a uniform RK4 order on switched spline-track runs.

| Case | Channel [SI unit] | d0 nominal/half | d1 half/quarter | E nominal/quarter | d0/d1 | Criteria |
|---|---|---:|---:|---:|---:|---|
| `VDL1_BASE` | vx [m/s] | 1.08225295392117e-09 | 6.262013130253763e-11 | 1.1448730852237077e-09 | 17.282827924656758 | PASS |
| `VDL1_BASE` | vy [m/s] | 8.228424212917279e-08 | 4.706070366733428e-09 | 8.699031249590622e-08 | 17.484702887323767 | PASS |
| `VDL1_BASE` | r [rad/s] | 7.670383230518052e-07 | 4.3931521795381734e-08 | 8.109698448471869e-07 | 17.459862342679862 | PASS |
| `VDL1_BASE` | e_psi [rad] | 1.854103404141938e-08 | 1.5959460419878724e-09 | 1.9602927281425764e-08 | 11.617582019455439 | PASS |
| `VDL1_BASE` | s_abs [m] | 1.0268441652527827e-10 | 2.1235069258551675e-11 | 1.1917455911003572e-10 | 4.8356054447020815 | PASS |
| `VDL1_BASE` | e_y [m] | 1.970732785294693e-09 | 1.5916720719211241e-10 | 2.1298999924868056e-09 | 12.381525190148299 | PASS |
| `VDL1_IZ_HIGH` | vx [m/s] | 7.771037147108473e-10 | 4.544453702237661e-11 | 8.225482517332239e-10 | 17.100046906148613 | PASS |
| `VDL1_IZ_HIGH` | vy [m/s] | 5.650594785220481e-08 | 3.2733146236932353e-09 | 5.977926247589804e-08 | 17.262608196351724 | PASS |
| `VDL1_IZ_HIGH` | r [rad/s] | 3.592743488406436e-07 | 2.087928153982066e-08 | 3.8015363038046424e-07 | 17.207217985707064 | PASS |
| `VDL1_IZ_HIGH` | e_psi [rad] | 9.935741562827616e-09 | 1.1298535440573687e-09 | 1.0513142800760988e-08 | 8.793831390879033 | PASS |
| `VDL1_IZ_HIGH` | s_abs [m] | 6.009265307582723e-11 | 2.1732282640130052e-11 | 6.657518980546229e-11 | 2.7651330544018555 | PASS |
| `VDL1_IZ_HIGH` | e_y [m] | 1.9409208684706414e-09 | 1.5987242085735431e-10 | 2.10054124094583e-09 | 12.140435842917661 | PASS |
| `VDL1_STEER_HIGH` | vx [m/s] | 1.6909917910368222e-09 | 9.78417347141658e-11 | 1.788833525750988e-09 | 17.282929375453886 | PASS |
| `VDL1_STEER_HIGH` | vy [m/s] | 1.0284513153428765e-07 | 5.8820298874662225e-09 | 1.0872716142175387e-07 | 17.48463260165273 | PASS |
| `VDL1_STEER_HIGH` | r [rad/s] | 9.58682399118671e-07 | 5.490809176778022e-08 | 1.0135904908864513e-06 | 17.459765368885407 | PASS |
| `VDL1_STEER_HIGH` | e_psi [rad] | 2.317431313514362e-08 | 1.8658603551102715e-09 | 2.4501558559819614e-08 | 12.420175535469818 | PASS |
| `VDL1_STEER_HIGH` | s_abs [m] | 2.199923576640117e-10 | 2.5070168163665585e-11 | 2.38117858764042e-10 | 8.77506509840044 | PASS |
| `VDL1_STEER_HIGH` | e_y [m] | 2.1292711344100823e-09 | 1.2375099903150222e-10 | 2.2419455042443914e-09 | 17.20609248470028 | PASS |
| `VDL1_CF_HIGH` | vx [m/s] | 1.8228605291881195e-09 | 1.0423084617627865e-10 | 1.927091375364398e-09 | 17.488685893475694 | PASS |
| `VDL1_CF_HIGH` | vy [m/s] | 1.5124871961640085e-07 | 8.529579861860093e-09 | 1.5977829947826094e-07 | 17.732259040413886 | PASS |
| `VDL1_CF_HIGH` | r [rad/s] | 1.482133763636151e-06 | 8.364952654160707e-08 | 1.565783290177758e-06 | 17.718376001792922 | PASS |
| `VDL1_CF_HIGH` | e_psi [rad] | 3.134144943572892e-08 | 2.257202424971183e-09 | 3.311042684472909e-08 | 13.88508584298949 | PASS |
| `VDL1_CF_HIGH` | s_abs [m] | 2.700357715212931e-10 | 2.5846769169390882e-11 | 2.8446767164069797e-10 | 10.447563861911368 | PASS |
| `VDL1_CF_HIGH` | e_y [m] | 2.0651888255063255e-09 | 1.534807142489214e-10 | 2.218669539755247e-09 | 13.4556894370254 | PASS |
| `VDL1_CR_HIGH` | vx [m/s] | 1.0818879125906733e-09 | 6.247713457696591e-11 | 1.1443650471676392e-09 | 17.31654180231153 | PASS |
| `VDL1_CR_HIGH` | vy [m/s] | 8.154977503439104e-08 | 4.6501528834161365e-09 | 8.619992791780717e-08 | 17.53700944440395 | PASS |
| `VDL1_CR_HIGH` | r [rad/s] | 8.721509211773171e-07 | 4.978722185911e-08 | 9.219381430364271e-07 | 17.51756552404886 | PASS |
| `VDL1_CR_HIGH` | e_psi [rad] | 2.0455907190353173e-08 | 1.6944947667241195e-09 | 2.1623518087210414e-08 | 12.071980151286946 | PASS |
| `VDL1_CR_HIGH` | s_abs [m] | 1.0260792215888159e-10 | 2.1184720644384925e-11 | 1.2181533559640911e-10 | 4.843487147236853 | PASS |
| `VDL1_CR_HIGH` | e_y [m] | 1.9742687762391853e-09 | 1.5389549357092136e-10 | 2.128147699731464e-09 | 12.828632797680728 | PASS |

## Native-grid sampled interpretation

All retained native samples, including onset and informational terminal diagnostics, were assessed.
Slip ranges below are signed alpha_f/alpha_r minima and maxima [rad]; U_f/U_r are peak synthetic
lateral utilization [dimensionless]. Full extrema and their times are retained in each referenced
run summary and the machine report. Every D minimum is 1.0, every sampled corridor-violation count
is zero, and every native horizon is complete. No continuous-time corridor/physical guarantee follows.

| Case/grid | alpha_f range [rad] | alpha_r range [rad] | max U_f [1] | max U_r [1] | Sampled window |
|---|---|---|---:|---:|---|
| `VDL1_BASE/nominal` | 0.0 to 0.02 | -0.0 to 0.005927830642624526 | 0.09174311926605504 | 0.027191883681763878 | Within |
| `VDL1_BASE/half` | 0.0 to 0.02 | -0.0 to 0.005927830643296654 | 0.09174311926605504 | 0.027191883684847033 | Within |
| `VDL1_BASE/quarter` | 0.0 to 0.02 | -0.0 to 0.005927830643342578 | 0.09174311926605504 | 0.027191883685057698 | Within |
| `VDL1_IZ_HIGH/nominal` | 0.0 to 0.02 | -0.0 to 0.005927253888951358 | 0.09174311926605504 | 0.027189238022712652 | Within |
| `VDL1_IZ_HIGH/half` | 0.0 to 0.02 | -0.0 to 0.005927253897388948 | 0.09174311926605504 | 0.027189238061417195 | Within |
| `VDL1_IZ_HIGH/quarter` | 0.0 to 0.02 | -0.0 to 0.005927253897894235 | 0.09174311926605504 | 0.027189238063735018 | Within |
| `VDL1_STEER_HIGH/nominal` | 0.0 to 0.025 | -0.0 to 0.007411417144265123 | 0.1146788990825688 | 0.03399732634984001 | Within |
| `VDL1_STEER_HIGH/half` | 0.0 to 0.025 | -0.0 to 0.0074114171419459324 | 0.1146788990825688 | 0.03399732633920152 | Within |
| `VDL1_STEER_HIGH/quarter` | 0.0 to 0.025 | -0.0 to 0.0074114171418194884 | 0.1146788990825688 | 0.03399732633862151 | Within |
| `VDL1_CF_HIGH/nominal` | 0.0 to 0.02 | -0.0 to 0.006236157145667227 | 0.11009174311926606 | 0.028606225438840494 | Within |
| `VDL1_CF_HIGH/half` | 0.0 to 0.02 | -0.0 to 0.006236157142557985 | 0.11009174311926606 | 0.028606225424577914 | Within |
| `VDL1_CF_HIGH/quarter` | 0.0 to 0.02 | -0.0 to 0.006236157142389621 | 0.11009174311926606 | 0.0286062254238056 | Within |
| `VDL1_CR_HIGH/nominal` | 0.0 to 0.02 | -0.0 to 0.0047078495959367835 | 0.09174311926605504 | 0.02591476841800064 | Within |
| `VDL1_CR_HIGH/half` | 0.0 to 0.02 | -0.0 to 0.0047078495933262675 | 0.09174311926605504 | 0.025914768403630828 | Within |
| `VDL1_CR_HIGH/quarter` | 0.0 to 0.02 | -0.0 to 0.004707849593175068 | 0.09174311926605504 | 0.02591476840279854 | Within |

The largest absolute slip is 0.025 rad (accepted cutoff 0.050 rad). The largest lateral utilization
is 0.1146788990825688 (accepted cutoff 1). Linear tire forces remain unsaturated; these values do
not establish real grip or a measured vehicle envelope. a_cmd=0 did not impose constant speed:
the largest nominal vx was 2.000638702491741 m/s in STEER_HIGH, from the common 2 m/s seed.

## Analytical expectations versus observed responses

The analytical expectations remain those of the accepted experiment design: at a shared state
and force, Iz scales yaw acceleration inversely; steering changes front slip/force; separate Cf/Cr
changes affect their respective axle forces and moment contributions. They are not universal claims
about later peaks, equilibrium, handling balance or stability. No derivative oracle or new model
experiment was executed during this campaign.

Observed nominal retained samples:

| Treatment | Time of peak separation [s] | Signed treatment minus BASE r there [rad/s] | Treatment r at 0.500 s [rad/s] |
|---|---:|---:|---:|
| `VDL1_IZ_HIGH` | 0.125 | -0.008904428222327412 | 0.13336505295289638 |
| `VDL1_STEER_HIGH` | 0.5 | 0.03336394365255693 | 0.16672938403813242 |
| `VDL1_CF_HIGH` | 0.13 | 0.010852414470119351 | 0.14029982760399706 |
| `VDL1_CR_HIGH` | 0.5 | -0.006275476007459452 | 0.12708996437811604 |

BASE ends at r=0.1333654403855755 rad/s. The inertia treatment is distinguishable in its transient
despite nearly equal terminal yaw rates. Higher steering and Cf produce positive recorded separations
at their peak-separation samples; Cr produces a distinguishable negative separation after rear slip
develops. All four are resolvable in this finite synthetic experiment. This does not establish a
general damping, settling, understeer/oversteer, stability or real-vehicle trend.

## Repeatability, reference, integrity and resource observations

The repeat and independent reference each match BASE nominal byte-for-byte for all three required
scientific CSVs. Their distinct run IDs, worker PID/birth identities and manifest hashes were verified.

| Export | BASE/repeat/reference SHA-256 |
|---|---|
| `experiment/states.csv` | `43e9945f2c458ce80dd3f234da6b3c2b4639c760c8c4ddd6321bae5e5c9ec389` |
| `experiment/controls.csv` | `139c0767e1ba41ae44a3a45fdd7c609d6c57b604812556e38b1fcea29c4c6577` |
| `experiment/diagnostics.csv` | `55730ba2c41350e8e34685e815f178e92805b5168f896d483e361e22bc0e0463` |

The production qualification reader verified the committed record, re-evaluated all referenced
manifests/artifacts and criteria, and checked current source identity. The production comparison
reader accepted each of the four nominal pairs with this qualification record. No fixtures supplied
scientific evidence. Qualification SHA-256:
`f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`.

All 17 worker environments report the same numerical identity and Accelerate SINGLE control.
Recorded worker wall times range from 1.6144078329998592 to 3.1449892910004564 s;
peak sampled RSS is 84754432 bytes and sampled worker threads peak at 2.
These are descriptive supervisor samples, not exact CPU/native-thread counts or hard-real-time
claims. Existing 60 s wall, 30 s CPU, 512 MiB sampled RSS, 64 MiB output and 16 MiB single-file limits
were unchanged. Kernel CPU/file limits were exercised in preflight. All recorded campaign workers
and supervisors have terminated, and the execution lease is released.

## Exact evidence locations and preservation

Resolve the following repository-relative paths under:
`/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle`.

- Campaign: `results/apex_workbench_qualifications/v0_2_reviewed_20261029/`.
- Published record: `results/apex_workbench_qualifications/v0_2_reviewed_20261029/qualification/qualification.json`
  and final checksum `commit.json` in the same folder.
- Original command/stdout/stderr/exit and preflight/audit records:
  `results/apex_workbench_v02d_reporting_20261029/`.
- [Machine execution report](execution_record.json): exact source/environment identities, all 17
  run/worker identities and manifest hashes, full-precision required metrics, consumption checks,
  report-artifact hashes and preservation limits. It is a report, not replacement qualification data.

Each directory below contains its immutable `artifacts.json`, `request.json`, `worker.json`,
`execution.json`, `numerical_environment.json` and `experiment/summary.json` plus actual CSV exports.
All are bound by the machine report and published qualification references.

| Slot | Run directory under campaign `runs/` |
|---|---|
| `VDL1_BASE/nominal` | `20261028T222835751293Z_021826cdd430404a809b24cc72a306df` |
| `VDL1_BASE/half` | `20261028T222838959075Z_b7c3b95d529a4d078daae45f4ba1d079` |
| `VDL1_BASE/quarter` | `20261028T222842428580Z_7f47b6423e67458593573687411eaa47` |
| `VDL1_IZ_HIGH/nominal` | `20261028T222846828499Z_4d209985d28d4e9ba778e9befb606a77` |
| `VDL1_IZ_HIGH/half` | `20261028T222849748573Z_e85cb100b6364e83846bdcfc61c5ff15` |
| `VDL1_IZ_HIGH/quarter` | `20261028T222853191579Z_1a974f4c10f748b092b349f082954f87` |
| `VDL1_STEER_HIGH/nominal` | `20261028T222857599970Z_a0ec2bc0f1c44e6088e48e8a936dae96` |
| `VDL1_STEER_HIGH/half` | `20261028T222900652163Z_65820774f09d4a0c9956e873e0cfcc11` |
| `VDL1_STEER_HIGH/quarter` | `20261028T222904258223Z_fe4529986deb45a68f5974f9748f441c` |
| `VDL1_CF_HIGH/nominal` | `20261028T222908631528Z_e848f1103e284fdd84a628ab08f6ebd1` |
| `VDL1_CF_HIGH/half` | `20261028T222911617766Z_719928896faf431d985f5304d1fb4c0b` |
| `VDL1_CF_HIGH/quarter` | `20261028T222915042417Z_9efc755020574f9cb0a05132b02b7104` |
| `VDL1_CR_HIGH/nominal` | `20261028T222919465430Z_c8169a8a05004229aeb9fb7a7bcb9053` |
| `VDL1_CR_HIGH/half` | `20261028T222922489893Z_07114372786245f1b3b004faacfd7a92` |
| `VDL1_CR_HIGH/quarter` | `20261028T222925955930Z_829b9563f35a4ec4b51f66879bbb7657` |
| `repeat` | `20261028T222930399552Z_aea9dc071d4945f78dd9fb4430cd3d85` |
| `reference` | `20261028T222933272417Z_339ebd5ccbf7439f828ed62d48fa6fca` |

All 951 preexisting tracked files remained byte-identical after execution, before reporting.
All 27782 preexisting result files retain size/mtime and remain present. This is
not a full historical content rehash or backup claim. Only this report, its machine reporting record
and the current handoff are delivery changes. Generated measurements, qualification records and
run artifacts remain in ignored `results/` and are not added to Git.

No formal Verification, V0.3, further scientific execution, model change, threshold change, physical
qualification, controller work or hardware activity occurred. The next gate is **Primary scientific
review of this retained one-shot result**. Formal Verification needs a separate authorization.

**Stop: V0.2_QUALIFICATION_COMPLETE_PENDING_SCIENTIFIC_REVIEW.**
