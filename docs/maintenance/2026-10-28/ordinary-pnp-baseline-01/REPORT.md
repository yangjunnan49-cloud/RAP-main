# PR1 ordinary source-depth PnP:17/200 numerical camera poses

Complete200-pair inference/evaluation/audit is finished.17/200 outputs (all00 original positives),183 explicit no-evidence.00=17/100;08=0/100. All50 confusers remain without output.176 cases have fewer than8 unique input depth hypotheses; five further00 cases have insufficient independently verified native-inlier support, and both08>=8-hypothesis cases fail native PnP. All cases/denominators remain.

| Quantity | Complete result |
|---|---:|
| Pose coverage |17/200 (8.5%)|
| Rotation mean /median,17 outputs |0.623331734 /0.498693179 degrees|
| Translation mean /median,17 outputs |0.664157493 /0.647724825 supplied metres|
| Direction mean /median,17 outputs |11.979501330 /4.444280644 degrees|
| R<=5deg andt_error<=2m,all200 denominator |17/200|
| R<=10deg andt_error<=5m,all200 denominator |17/200|
| R<=5deg anddirection<=15deg,all200 |14/200|
| R<=10deg anddirection<=30deg,all200 |15/200|

These are supplied-reference exposed-cohort engineering measurements. The17 output errors do not describe the183 missing outputs, and no universal accuracy/safety guarantee follows from all17 satisfying the descriptive bin. Full200 rows and15 complete summary groups are under evaluate. Do not promote the per-output error means into complete-cohort or population accuracy.

## New quantity and limits

Unlike ER1's scale-free camera5DoF, PR1 uses source3D depth hypotheses to estimate camera_i->camera_j rotation and translation in supplied raw-LiDAR coordinate units. This is numerical metric-camera6DoF estimation, not physical-scale authentication, corrected-LiDAR rigid equivalence, RAP/native-N metric comparability or a system/manuscript contribution. SD1 assignments remain fixed2px nearest-projection/z-buffer hypotheses, not verified texture/point/target identities; timing/occlusion/extraction/calibration/cohort independence is not added. Original raw points/suppliedTr/archiveP0 are unchanged. Old point-dependent0.205-degree correction has no assumed constant conjugation.

## Prospective implementation and controls

All source/input/fixture/parameters/resources were frozen before any measured PnP. Exactly one estimator:SOLVEPNP_EPNP RANSAC1000iterations/confidence0.999/2px/seedSHA('PR1:'+key), no LM/model/fit/seed/threshold rescue. Native inliers are independently reprojected and require positive target depth,<=2px residual and>=8 support. The installedOpenCV5.0.0 EPNP flag is1, confirmed directly; do not substitute values recalled from another version.

All23 pre-measured controls passed: actual API, first solver call after strict I/O gate, clean/nonplanar direction/inverse/metric scaling, exact fixed outliers, deterministic outputs, ranks0/1/2/3, planar/duplicate/collinear/2D/nonfinite/invalidK fallbacks, support/positive depth, zero/unit direction, cold NPZ and reference-binding denial. The rank tests run before real data here; they do not retroactively repair SD1's omitted prospective rank test. No failed PR1 child/retry or settings change occurred. The copied launcher console prefix 'VB1' identifies this PR1 folder's receipt, not a reversal of original VB1's failure.

All200 prediction records/evidence were sealed2026-10-28 12:47:07.8857930UTC; reference-read begin is12:47:33.895155UTC. Prediction's exact Python read allowlist contains only200 sealed source hypothesis files and two archive calibration files. No reference/labels/outcome values; native APIs receive arrays only. This is source-reviewed Python I/O separation, not OS security isolation.

Independent audit passes all200 masks/order and complete summaries,1129 scalar projection checks (max pixel delta2.2737367544323206e-13,zero threshold-boundary ambiguities),200 Decimal60 relative reference solves and independent scalar rotation/translation/direction errors. Max Q/R/t/direction differences are8.5265128291212022e-14/4.6629367034256575e-15/2.55351295663786e-14/2.3590018827235326e-12. No prediction replay was used in audit.

Resource audit:inclusive948.164127/3600s including preparation/closure, child host walls3.2537946s, max lifetime peak47562752bytes,new dossier939554/16777216bytes before small closure additions. All four stages passed fresh12GiB/2s gates, their60/180/120/120s limits, exit0 and reaping. No live owned worker remains. No installation/network/WSL/GPU/Torch/model/training/existing-environment/default/production/Git writes/outreach/scheduler/goal-status action.

Next saved-output categorical comparison must keep all200 IDs and the frame/task distinctions. If any future point-cloud initializer uses these17 camera poses, first establish raw LiDAR<->camera/public normalization action explicitly. Do not infer a constant transform for the old point-dependent correction or automatic RAP benefit. No new model experiment is admitted by this closeout. ResearchUNRESOLVED/manuscriptPAUSED; SR1/HFIT0/all older failures/caps/source restrictions unchanged.
