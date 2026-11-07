# MGR0 physical GICP measurement study — 2026-10-12

**VALIDATED_MEASUREMENT_COMPARISON_COMPLETE_WITH_PREFREEZE_AND_SUPERVISION_REPAIR.** Decision **NO_SAFE_MEASURED_REGISTRATION_HEADROOM**. All58 original admitted-loop measurements completed and independently validated. The engineering conjunction and RAP-initializer increment both fail; conditional full-trajectory graph execution is not admitted and was not performed. Retire this exact GICP/FPFH-FGR/selector family without parameter, point, radius, initialization, threshold or favourable-case rescue.

## Result

Errors below are relative loop-pose errors against the existing calibrated reference, not new full-system ATE. No new RAP/descriptor inference or learned head was used. N is native RAP, RI is RAP-initialized physical GICP, W is the three-candidate geometry bundle and J replaces its identity initializer with RAP under the same maximum refinement budget.

| Arm | Mean translation m | Mean rotation deg | q90 translation m | q90 rotation deg | Joint nonworse vs N |
|---|---:|---:|---:|---:|---:|
| N | .908734233 | .215742686 | 3.798729703 | .290275139 | reference |
| RI | .905946369 | .185353040 | 3.834718073 | .283337220 | 23/58 |
| W | .905800583 | .185788792 | 3.835792293 | .283337221 | 23/58 |
| J | .905902878 | .185817210 | 3.835792293 | .283337220 | 23/58 |

RI improves mean rotation14.0861%, but mean translation only .3068% (2.78786mm), versus the frozen10% requirement. J improves mean rotation13.8709% and translation .3116%; joint nonworse is23/58 versus required44. Translation q90 slightly worsens. Four of46 engineering checks fail (translation improvement and joint44 for RI/J); all support, sequence mean, q90 allowance and absolute per-edge harm safeguards pass. Maximum RI translation/rotation harm .095618m/.095971deg; J .095618m/.096383deg. This is a failed material/joint conjunction with real partial rotation improvement, not catastrophic sequence harm or zero effect.

J also fails two of14 initializer-increment checks: mean translation is .102295mm worse than W and rotation .000028418deg worse; required translation gain>=5% and nonworse rotation are absent. Other increment safety checks pass. Classical geometry accounts for the available improvement here; selecting RI in24 cases does not itself demonstrate incremental RAP value.

| Sequence | N/RI/W/J mean t m | N/RI/W/J mean R deg |
|---|---|---|
| 00 | .824481 / .814961 / .815046 / .815076 | .209287 / .152990 / .156636 / .156737 |
| 05 | .135770 / .122640 / .122411 / .122414 | .315839 / .307220 / .305302 / .305324 |
| 06 | .073857 / .062368 / .062329 / .062389 | .107452 / .093516 / .093299 / .093533 |
| 07 | .139058 / .128129 / .127875 / .127879 | .215971 / .184665 / .184783 / .184801 |
| 09 | 3.862860 / 3.900771 / 3.900450 / 3.900928 | .233049 / .188978 / .189551 / .189267 |

The large09 reference discrepancy persists across native and all measured initializers. Its translation mean worsens while rotation improves. This does not prove the official reference wrong, certify the measured pose physically correct, identify a unique timing/calibration/dynamics cause, or license excluding09. Other exposed sequences show conditional gains but do not override the frozen all58 gate. No new trajectory/system score is claimed.

## What actually ran

The owner explicitly requested the next round and continuation.1567 identities froze after the recorded prefreeze boundary amendment, including all147 SGC0 deliveries, previous preserved artifacts, scientific sources, package versions, installed CPU binary/entry source, original raw/cache/reference identities. The installed Open3D0.19 CPU route uses process-local hidden CUDA visibility; no persistent configuration/install/restart. Tagged upstream source/API links are in SETUP_RECORD; binary identity does not prove bit-identical compilation from the online source.

The prescribed index0 pilot00/05/06 passed GT-free support after independent synthetic gates.81 measured endpoint caches (324000 points) and81 neighbouring whole-scan holdouts (324000 points) were bound. All six original pilot endpoints reprocess byte-exactly (coordinate max0). Independent brute-force neighbour/PCA reconstruction reproduces all81 normal/covariance caches, max covariance delta0. Independent raw equations on six holdout scans differ by <=2.38419e-7m; shared Open3D voxel/outlier/cap implementation remains. No full independent raw processing claim for every scan. Frame0 endpoints07/09 use frame1 holdouts under the prospective amendment; all other endpoints use their predecessor.

GICP supplies explicit positive anisotropic point shape matrices, rematches at2.5m and caps80 iterations per candidate. Covariance shapes are not calibrated sensor uncertainty. FPFH/FGR supplies a genuinely independent classical initialization, without learned descriptors or GT. GI/GK/GF versus RI/GK/GF have equal candidate counts/max refinement budget, not equal total full-pipeline work: RAP was previously generated, actual convergence/timing differ. Shared candidates and cached processing must not be double counted as new executions.

All58 RI outputs are supported, all232 RI/GI/GK/GF refinement outputs complete, no FGR failure or W/J fallback. W selector counts GI11/GK25/GF22; J selects RI24/GK15/GF19. These selectors use only censored symmetric fit-support distance and physical support; holdouts and reference labels are excluded. Pilot predictions are reused byte-exactly in the complete bank, without extra scientific fits. The complete59-file prediction bank seals before numerical reference access. Whole-scan diagnostics use fixed KISS local motion and remain correlated proxies, not independent physical truth.

Synthetic known-transform forward/reverse/common-frame recovery errors<=3.01842e-16. Independent full covariance-objective gradient FD relative2.51496e-10 and frozen-weight residual Jacobian max5.72464e-9 pass. Single-plane structural rank3, nondegenerate rank6, disjoint support rejection and periodic high-support/full-rank different basins are retained. Open3D uses conditional GN with weights frozen inside a step; we do not call its update the full rotation-dependent covariance derivative or interpret returned Euclidean inlier RMSE as the diagnostic GICP objective. Low residual and rank6 alone are not accuracy gates.

The independent full validator reconstructs all supports/costs/selectors/holdout responses; selected three-case shared-library replays at pilot and full-validation stages have all nine pose arrays max delta0. Reference metrics58 pairs and all engineering/increment gates independently reproduce, max scalar delta1.07442e-13. These solver replays share the installed implementation; there is no independently implemented GICP/FGR nonlinear solver. No new learned/native gradient, head/cache extraction, full trajectory or physical reference validation.

## Failures, resources and preservation

The initial API-only mixed CPU/CUDA binding import failed before numerical registration; setup ru_maxrss was not captured. One automatic-approval usage-limit error executed nothing and later retry succeeded through normal approval. Preserve these setup gaps.

The first supervised prefreeze census stopped on an assumed strictly positive endpoint. AMENDMENT_01 retains original sources/protocol/failure/logs and declares the endpoint0 successor rule before any numerical payload. Flat snapshot basenames then collide with preserved prefreeze copies; original snapshots remain and separately hashed frozen_current_sources/SOURCE_SNAPSHOT_SUPPLEMENT identify the actual frozen current helpers. Neither historical science nor a numerical result/gate was repaired.

During validate_bank the original Windows supervisor failed at atomic host-pointer File.Move. Native validation continued successfully, with full57.549269004s/RSS367276032bytes captured. Windows child exit and later host observations for that stage are unknown. AMENDMENT_02 freezes a distinct logging helper for subsequent evaluation/validation; old source/logs/gap remain. The first logging-helper text-replacement setup and incomplete metadata attempt also remain (LOGGING_REPAIR_SETUP_NOTE and both amendment freezes). These bookkeeping failures launched no numerical evaluation. No old gap is backfilled and no duplicate full validation was executed as a rescue.

Twelve supervised child attempts include the failed prefreeze and eleven successful stages. Combined child payload339.845608401s, peak full-process RSS492589056bytes (~.459GiB);1800s/4GiB/512MiB bounds pass, with all attempted child wall/RSS receipts. Eleven Windows exit records exist for twelve children; one known supervision gap prevents an all-attempt/gap-free Windows claim. API/metadata setup full RSS remains unknown and is outside these child figures. Whole dossier before final reports/seal about90.51MiB; RESOURCE_AUDIT records closing size. CPU payload only, no project model/checkpoint/RAP/descriptor forward or neural optimizer calls. This is a stored-observation offline measurement cost, not full production latency.

Original repositories' HEADs/branches and two/nine tracked dirty sets, current model/config/checkpoint sources, SGC0 and older delivered artifacts/stops/seals/failures remain. No production/default/backbone/manuscript/reference edit, new loop admission, install, global process/configuration change, commit or Git sync. NOC4 stays INCOMPLETE/P replay prerequisite.

## Next judgment

The tested local refinement is feasible and partially improves rotation, but it does not provide the declared joint metric headroom or isolate a RAP increment. Do not turn this into a production/default change or a new mechanism claim. Next DESIGN_ONLY priority is a bounded source/reference/physical-consistency diagnosis of the existing large09 discrepancy, with00 included as a fixed contrasting case. It must retain official metrics and avoid oracle replacement/edge selection. After that, choose a genuinely new observation/context or bounded frozen-feature residual task with strong geometry controls; neither route is executed or newly frozen here. See NEXT_ROUND_PLAN.md.
