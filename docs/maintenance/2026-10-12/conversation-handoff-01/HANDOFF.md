# Conversation handoff — RAP / RAP-SLAM

## Owner intent and current scope

The owner wants further metric improvement within the current RAP framework, with a defensible modest innovation and appropriate controls. The owner authorized successive bounded stages after primary-source research, then requested information synchronization before a new conversation: "做好信息同步工作，为防止上下文腐烂将开启新一轮对话". The current request is documentation/identity synchronization only, not another experiment, native training, Git synchronization or automatic creation of a new chat.

Originality was relaxed earlier: ordinary adaptation/geometry can be credited accurately, but new RAP-specific value, physical accuracy, independent generalization and system gain must be measured rather than assumed. Generic submap registration/refinement has prior art. The research corrected an older blanket IMU exclusion: official GLIM has a LiDAR-only mode; published inertial scores are not imported.

## State at the conversation boundary

| Layer | Latest evidence | Meaning |
|---|---|---|
|Complete system|2026-10-11 benchmark,36 runs|Still the latest full-system comparison; mixed RAP/KISS performance|
|Scan graph SGC0|Completed, NO_SAFE_MATERIAL_SCAN_GRAPH_SIGNAL|Retired exact graph/covariance-allocation rescue|
|Measured registration MGR0|Completed, NO_SAFE_MEASURED_REGISTRATION_HEADROOM|Retired exact single-scan GICP/initializer/selector rescue; no conditional graph|
|Physical/source diagnosis RPC0|Completed with validator repair|Broad09 conflict persists; cause/physical truth unresolved|
|Native comparison NOC4 attempt02|INCOMPLETE, replay mismatch/loss increase|P backward reproducibility prerequisite remains; zero retained fit updates|
|Causal context/submap and later residual|DESIGN_ONLY|No next runner/protocol freeze/feature extraction/solver/training/trajectory exists|

Scientific diagnostic completion does not imply a positive metric gate. A delivery seal is an artifact integrity statement, not proof of physical truth or completion of NOC4.

## Latest complete system result

Fixed sequences00/05/06/07/09/10, RAP-SLAM and KISS-SLAM, three separate process repetitions each:36 admitted complete runs. All-six means:

| Model | KITTI translation drift (%) | Aligned LiDAR ATE (m) |
|---|---:|---:|
|RAP-SLAM|0.447166761|1.091071657|
|KISS-SLAM|0.478613920|0.699688694|

Best actual global repetitions are RAP1/KISS3; never splice per-sequence bests. Tiny nonzero fixed-seed population standard deviations can round to zero; this is not fresh-noise/site robustness. Earlier GeoTransformer numbers are a controlled replacement from10-05, not these fresh complete repetitions. Two Windows observation gaps/null attached-launcher exit remain in this benchmark, despite full child peaks/exits. Original initial cap failures and prospective resource amendment remain distinct.

Exact paths from workspace root: `docs/meeting_20261011/benchmark/REPORT.md`, `attempt03/results.json`, `attempt03/validation.json`, `attempt03/trajectory_seal.json`, `RESOURCE_AUDIT.json`, `freeze.json`. The validation and trajectory seal are inside attempt03, not at benchmark root. No full-system metric is freshly replayed by this handoff.

## What this conversation established

**Review/research:** stage-review-01 verified bounded selected historical identities/arithmetic. metric-innovation-research-01 reviewed27 paper/concept entries plus6 implementation/metric entries from primary sources. Recommendations were measured graph/registration feasibility, then conditional frozen-RAP residual or changed observations. Read these to understand prior art and abandoned ideas, not to reopen old experiments.

**SGC0:**1155 frozen identities,147 delivery entries; complete original E0 A inputs for all six sequences(12296 scans,1800 keyframes,58 original loops). Native R/shared proper-SE3 keyframe B/nominal-strength-matched scan graph S. B/S ATE1.091071657→1.093276827m, ter.447166761→.446561289%, rer.138935217→.139008966deg/100m;4/61 tests fail. Independent Schur/derivative/covariance/metric checks pass,18 shared GTSAM replays exact, not an independent optimizer implementation. Smaller correction jumps are not material gain or calibrated uncertainty. No exact graph/weight allocation rescue.

**MGR0:**1567 frozen identities,344 delivery entries; all58 original admitted loops/232 GICP outputs complete. Open3D0.19 CPU, fixed80 iterations/2.5m, RAP/identity/KISS/FPFH-FGR initializers; W geometry versus J RAP three-candidate maximum-refinement-budget bundles, not equal total pipeline cost. N/RI/W/J mean relative translation.908734233/.905946369/.905800583/.905902878m; rotation.215742686/.185353040/.185788792/.185817210deg. RI rotation improves14.0861%, translation only.3068%; joint nonworse23/58 versus required44.4/46 engineering tests and2/14 RAP initializer-increment tests fail. All support/sequence/harm guards pass. No conditional graph or new trajectory scores.09 translation conflict persists. Retain original endpoint0 prefreeze failure, CPU/CUDA API failure, source-snapshot supplement, amendments and validate_bank Windows exit/late-host gap. Independent support/metrics and selected shared solver replays are not an independent GICP implementation. Stop exact radius/epsilon/normal/point-count/FGR/initializer/selector/iteration/gate rescue.

**RPC0:**1910 original frozen identities;13-entry separate validator amendment;122 original delivery entries plus a separately sealed count-notation note. Fixed first admitted00(2429,3373),09(0,1574). Eleven raw scans/1380000 returns;45056 deterministic source-ID selections, complete rejection reasons, RAW/.205deg representations with identical IDs and16 fixed sensor-coordinate return strata. Fifteen revisit pairs(9 sequence00,6 sequence09), seven adjacent controls(4 sequence00,3 sequence09);09 unavailable -1 explicitly excluded, future controls diagnostic/noncausal. No fit/selector/model/optimizer/graph.

All current00/09 filename/path/ID/time/row bindings and coordinate direction/transfer checks pass.09 all6/6 revisit pairs retain median G-minus-W nearest-distance contrast2.464157098m RAW/2.462758691m CORRECTED;144/144 eligible pair/direction strata retain>=.5m gap. These are repeated partitions over five scans, not144 independent scenes.00 contrast is.149803628/.149845836m, zero>=.5m pair/eligible-stratum gaps. Immediate median t/R disagreement:00 .017664765m/.061745796deg;09 .026015501m/.102169634deg. Fixed intrinsic correction(max point shift.285322694m) obeys every NN bound and does not remove the broad09 conflict. G-minus-N09 vector[-.556973826,2.043355467,-3.064252584]m in LiDAR0 axes has z/norm82.2632%; that axis is not independently authenticated gravity or a vertical-drift diagnosis.

All1949696 logical directed-distance records independently validate,1703936 unique brute cdist records and30 exact-transform aliases. Nearest distance max3.55271e-15; matrices7.26364e-14. First validator stopped at local-envelope1.59471e-8>unchanged1e-8 tolerance: independent scalar-angle extraction omitted SciPy1.15.2's orthogonalization of rounded matrices. Failed source/receipts retained; independent polar-eigendecomposition repair separately frozen,14-matrix prerequisite/full attempt02 pass. Original corpus/poses/results/gates unchanged; no fixed-pose evaluation or corpus rerun.

Nine supervised children(eight success,one retained validation failure),108.281916375s payload/RSS120557568bytes, GPU0;900s/2GiB/256MiB scientific-child/new-dossier bounds pass. All9 Windows exits/child peaks and zero new logging gaps/retries. Ordinary setup RSS is not fully captured; imports/WSL startup/design/final bookkeeping excluded from payload timing, ru_maxrss includes imports. Old MGR/NOC/system gaps remain. Approval usage-limit service nonexecution was retained; identical scoped retry following owner continuation passed normal review, no bypass. RPC0's new INCOMPLETE marker alone closed.

## Physical and native gaps that must survive handoff

The exact00/09 directories lack22 predefined OXTS/scan start-end/raw-calibration/labels/receipt paths. This is a scoped absence, not a machine-wide search. XYZI exposes no actual per-return times under the current schema; production deskew=false path passes zero point times. Upstream motion compensation/calibration/rectification/extraction provenance, trigger synchronization, reference physical accuracy, dynamics/surface identity,09 cause and checkpoint/site membership remain unresolved. Provider format documentation, algebra, rank, low NN residual and label disagreement cannot certify physical truth. Keep official reference and every original edge/sequence; no GT selector/corrected reference/09 deletion.

NOC4 attempt02 status is AUDITED_NATIVE_PREFLIGHT_STOP_WITH_REPLAY_MISMATCH; decision PROBE_LOSS_INCREASE_AND_P_REPLAY_MISMATCH. Four restored optimizer probes,0 retained updates/fits/comparison traces. Initial parameters/outputs exact, full V replay exact, P gradients/updates/endpoints mismatch; original and replay objectives increase. No unique cache/precision/curvature/overshoot/runtime cause established. Stop exact rate/step/scale/noise/init/gate rescue. Bounded P backward reproducibility with upstream/per-parameter checks precedes native adapter updates. Both original and attempt02 INCOMPLETE markers stay. NOC3 positive rigid numerical control does not establish native learnability or physical/generalization/system gain.

A separate frozen-feature head is not automatically blocked by native backward, but requires its own exact frozen extraction/derivative/functional-step checks; native backward repair must never be assumed. Earlier PFG/shared-plane/CV/MF/RLP/NOC/LC stops and all immutable seals remain in AGENTS and their original dossiers. Read the relevant original scope before any related path is considered; do not repeat retired constructions to avoid a negative result.

## Recommended next distinct step — not yet executed

Read RPC0 NEXT_ROUND_PLAN for the current recommendation: causal observation-context/submap feasibility around original frontend/frozen RAP, with fixed support/work and strong geometry controls. Historical research questions are drafts; the ATE-primary/ter-safety choice used in SGC0 does not automatically freeze gates/resources for a future context study.

When the owner requests next-stage execution, resolve a concrete prospective scope/resources/gates before payload, then proceed within that authorization without repeating already granted permissions. This information-sync request does not itself authorize a next experimental runner/freeze or training.

Use only earlier/current endpoint frames, one fixed prospective history length and point policy; align by original frontend poses with independent direction/common-gauge/no-op/source-ID tests. Boundary endpoint0 retains available history and complete-population membership; never borrow future scans or move anchors. Required contrasts: original single scan, same-total-return-count single-scan density control, causal context at matched total returns, full context with extra work separately counted. No radius/normal/selector/FGR sweeps, favorable windows or GT-based selection. Seal complete predictions before reference and preserve all failures/fallback/support/accepted-rejected records. Accumulation brings odometry/dynamic/aliasing errors and does not certify a better physical measurement.

Only if context shows safe measured headroom should a bounded frozen-RAP metric SE3 residual/context head follow, with target/cache-free exact extraction, its own derivatives, equal-active-capacity direct/separated-context/joint heads, strong geometry and equal-work controls. Generic fitting/submaps are prior art; modest innovation must be tied to measured incremental RAP value. Complete trajectories/reserved-session confirmation are conditional later stages, not current authorization. Exposed KITTI roles are development; new dataset names do not prove exclusion from pretraining.

Independent physical evidence is a separate possible branch only if authenticated drive mapping/archive identities/original OXTS/start-end timestamps/calibration/rectification/deskew lineage become available. No acquisition/install or inferred corrected reference by this handoff. Do not spend another round on unchanged local physical/offset/patch sweeps.

## Source map and execution hygiene

Workspace Windows `E:\githouse\RAP-main`; sibling `E:\githouse\RAP-SLAM` remains read-only. WSL equivalents `/mnt/e/githouse/RAP-main`, `/mnt/e/githouse/RAP-SLAM`; data `/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset`. New isolated algorithm helpers for authorized stages are under main `scripts/maintenance`; current production is in sibling.

| Need | Exact workspace-relative entry |
|---|---|
|Current newest diagnostic|docs/maintenance/2026-10-12/reference-physical-consistency-01/{REPORT,PROTOCOL,OWNER_SCOPE,NEXT_ROUND_PLAN,AMENDMENT_01,EXECUTION_NOTE}.md; STATUS/CHECKS/validation/RESOURCE_AUDIT/FINAL_IDENTITY_CHECK/DELIVERY_SEAL.json|
|Count-notation clarification|docs/maintenance/2026-10-12/reference-physical-consistency-delivery-note-01/{REPORT.md,CHECKS.json,DELIVERY_SEAL.json}|
|Current source/graph/registration history|docs/maintenance/2026-10-12/{scan-level-graph-feasibility-01,measured-gicp-registration-01}|
|Review/primary research|docs/maintenance/2026-10-12/{stage-review-01,metric-innovation-research-01}|
|Prior broad temporal/geometry checks|docs/maintenance/2026-10-05/{temporal-identity-audit-01,online-geometry-consistency-01}|
|Native stop|docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02; parent original dossier and markers|
|Original E0 input bindings|docs/maintenance/2026-09-26/e0-frontend-01/full-{00,05,06}-A;2026-09-27/e0-heldout-01/full-{07,09,10}-A|
|Original measured input caches|docs/maintenance/2026-10-05/online-geotransformer-01/input-bank|
|Current durable supervisor|scripts/maintenance/invoke_mgr_supervised_wsl.ps1|
|Completed RPC0 source|scripts/maintenance/{reference_physical_consistency.py,validate_reference_physical.py,reference_physical_validation_attempt02.py,close_reference_physical.ps1}; original snapshot/amendment in dossier|
|Daily record/final prior check|docs/maintenance/2026-10-12/PHASE_RECORD.md;RPC0_FINAL_HANDOFF_CHECK.json|

Observed existing WSL runtime: Ubuntu-24.04 root Python `/root/miniconda3/envs/rap-inference/bin/python`, frozen NumPy1.26.4/SciPy1.15.2/GTSAM4.2/Open3D0.19.0. No current neural runtime revalidation or environment change. For a later authorized CPU Open3D process, set process-local CUDA_VISIBLE_DEVICES empty before its first import; importing default CUDA then CPU binding caused the retained MGR setup failure. No install/restart is implied. Use -B and recorded single-thread environment for prospective jobs; preserve exclusive output directories and every failed/attempted payload. Repaired supervisor records host/child exits/peaks and uses12GiB launch/4GiB observed headroom guards; these are not future lifetime guarantees. Never mutate the old supervisor/source/output/gates to hide failure. New isolated amendment with frozen source/output route is required for a real implementation repair.

Windows sibling Git HEAD/branch reads work but status can report "must be run in a work tree". Read-only WSL Git succeeds; use that for actual status comparison instead of changing Git config/worktree. Quote-safe standalone standard-library bookkeeping helpers avoid nested shell/Python escaping failures. No script should be rerun unchanged against an existing immutable stage directory. No scientific job is pending in current status; this sync does not perform a live process census.

## Repository and preservation boundary

| Repository | Original HEAD | Branch | Original tracked dirty set |
|---|---|---|---|
|main|4055d929c594b0033aafc6eed339c910369eef55|codex/meeting-20260930|.gitignore, AGENTS.md|
|sibling|6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6|codex/e0-f1-20260926|loop_closure.py, odometry.py, pose_graph.py, rap_backend.py, real_dataset.py under rap_slam; build_s1_features.py, eval_map_consistency.py, eval_paper_metrics.py, run_pipeline.py under scripts|

Preserve all existing untracked work. Only isolated new main maintenance helpers/docs and mutable AGENTS/daily handoffs are changed. No production/default/backbone/manuscript/official reference/model/config/checkpoint/acquisition/install/process restart/commit/Git sync. The information-sync audit hashes selected sealed artifacts, current benchmark bindings and repository identities only; it does not replay numerical/raw/neural/optimizer/trajectory work or certify unknown physical/site evidence. CHECKS/IDENTITY_CHECKS/DELIVERY_SEAL make the handoff reviewable.
