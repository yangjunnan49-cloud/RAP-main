# RAP / RAP-SLAM stage review — 2026-10-12

Status: **BOUNDED_READ_ONLY_STAGE_REVIEW_COMPLETE**.
Owner request: read AGENTS.md, investigate the project in depth, and provide a stage summary.

The project has a reproducible complete SLAM pipeline, a substantial frontend engineering improvement, and several validated diagnostic signals. It does not yet have a demonstrated additional RAP mechanism that produces a safe system improvement. The latest complete system evidence is the 2026-10-11 fixed-pipeline repetition study; the latest native adaptation comparison remains an incomplete, audited prerequisite stop. These two statuses coexist.

This review reads code and existing evidence, verifies identities, and recounts stored scalar statistics. It performs no new model load, feature extraction, native forward/backward, optimizer call, trajectory experiment, physical-reference validation, or production change.

## 1. Project structure and actual operating path

| Location | Responsibility | Current state |
|---|---|---|
| RAP-main | Pretrained registration model, local runtime adaptation, maintenance evidence and handoff | HEAD 4055d929c594b0033aafc6eed339c910369eef55; branch codex/meeting-20260930 |
| RAP-SLAM | Dataset loading, odometry, loop retrieval/verification, pose graph and research helpers | HEAD 6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6; branch codex/e0-f1-20260926 |
| RAP-SLAM-report | Historical thesis and presentation material | Separate artifact area; no root Git repository recorded |
| Datasets | Raw scans, official poses, calibration and timestamps | Existing inputs; no acquisition in this review |

Both Git HEADs remain the original recorded commits. RAP-main has two tracked dirty files (.gitignore and AGENTS.md); RAP-SLAM has nine. Considerable maintenance and research work also lives in untracked files. A HEAD alone therefore does not reproduce the executed system: the source snapshots, configuration and input manifests identify the actual work. The current RAP-SLAM dirty set was read through WSL Git with optional index locking disabled; the Windows Git status path could not inspect that work tree. No Git configuration, commit or synchronization changed.

The working pipeline is:

`LiDAR scans → preprocessing / KISS-ICP → keyframes → proximity + Scan Context → RAP relative-pose verification → GTSAM PGO → dense trajectory / evaluation`.

RAP estimates loop constraints; KISS-ICP supplies the local motion backbone. Native RAP has not replaced odometry. Optional N-way, confidence, conformal and live/ROS branches are separate protocols and are not validated core defaults simply because their code exists.

Source anchors: [backend](../../../../../RAP-SLAM/rap_slam/rap_backend.py), [pipeline](../../../../../RAP-SLAM/scripts/run_pipeline.py), [graph](../../../../../RAP-SLAM/rap_slam/pose_graph.py), [data loader](../../../../../RAP-SLAM/rap_slam/real_dataset.py).

### Native registration details

The local model uses a 12-layer DiT, 512-dimensional hidden tokens, eight heads, and 32-dimensional miniSpinNet descriptors. Each layer has within-part and global attention. The final velocity MLP runs in float32; attention uses the configured lower precision. The local attention implementation uses PyTorch attention rather than an external FlashAttention import. These are local source facts, not a claim that this checkout reproduces every published model version.

The SLAM backend downsamples at 0.4m, removes statistical outliers, caps each scan at 4000 points, and extracts descriptors with 5m support. Normalization retains per-part centres and a common scale. Starting from Gaussian coordinates, five Euler calls use tau = 1, .8, .6, .4, .2:

`clean estimate = current coordinates − tau × predicted velocity`.

The sampler fits each estimated clean part rigidly back to its measured input and uses that rigid estimate plus the original noise for the next state. Final relative pose is obtained from the last raw clean estimate by per-part rigid fitting, metric restoration, and `inverse(T_a) × T_b`. The anchor is tagged, rather than hard-clamped by the Euler sampler. Common output frame freedom makes relative poses, metric scale restoration and proper rotations essential.

The actual complete-system configuration uses K=1, five steps, candidate cap12, NMS0, overlap >=0.7 and mean distance <=2.5m, with relfloor/Huber graph treatment. Historical F2 instead uses K4 and six parts; its candidate counts do not describe this online pipeline. The latest actual manifest has Scan Context shortlist10; the older AGENTS narrative mentioning12 should not override the run manifest. Model-group sampling defaults also differ from the explicit backend overrides.

Float32 rigid-fit products are protected by the cooperating registration precision scope, which restores the incoming process policy. This addresses the recorded TF32/SO(3) problem; it is neither full-fp32 neural execution nor a guarantee against unrelated callers changing PyTorch's global policy.

## 2. Latest complete system result

The [2026-10-11 benchmark](../../../meeting_20261011/benchmark/REPORT.md) completes six sequences, two fixed systems and three separate process repetitions: 36 admitted runs. It includes frontend, loop processing and backend. Original failed attempts remain separate. New resource limits were declared before the new 36-run set; the earlier cap failure was not reclassified.

The values below are arithmetic means over sequences and repetitions. ter is official-style KITTI camera segment translation drift; ATE is SE(3)-aligned LiDAR position RMSE. They measure different error properties and must remain separately visible.

| Cohort | RAP-SLAM ter (%) | KISS-SLAM ter (%) | RAP-SLAM ATE (m) | KISS-SLAM ATE (m) |
|---|---:|---:|---:|---:|
| 00/05/06 | 0.388718 | 0.472672 | 1.460663 | 0.635296 |
| 07/09/10 | 0.505615 | 0.484556 | 0.721480 | 0.764081 |
| All six | 0.447167 | 0.478614 | 1.091072 | 0.699689 |

RAP has lower ter on00/05; KISS has lower ter on06/07/09/10. RAP has lower ATE only on09. The exposed-transfer mean ATE advantage is driven by09. The larger00/05 ATE deficits dominate the all-six comparison. This supports competitive, mixed system performance rather than general superiority or component-level causal attribution.

The documented best actual complete repetition is RAP1 and KISS3, selected globally on all-six mean ter with ATE tie-breaking. It must not be replaced by a table assembled from each sequence's best run. Means above use all repetitions. RAP's all-six population standard deviations are about8.32e-13 percentage points for ter and6.40e-12m for ATE; they round to zero in the meeting table but are not mathematically zero. Fixed-seed process reproducibility does not establish fresh-noise or population robustness.

The existing independent validator reconstructed44388 segment records with maximum ATE/segment discrepancies6.33e-14/2.18e-14. This review rehashes source/trajectory bindings and independently recounts scalar means, population standard deviations and actual repetition choices. It does not rerun that trajectory evaluator. GeoTransformer numbers in meeting material come from the older controlled online matcher swap, not these new end-to-end repetitions.

Child resource peaks/exits are captured. Windows supervision has two retained observation gaps and an unavailable attached-launcher exit code. These do not erase the complete child records, and they do prevent a claim of uninterrupted host supervision. No recorded experiment timing is promoted to production latency here.

## 3. What the experimental history has established

| Stage | Validated finding | Remaining boundary |
|---|---|---|
| M0–M3 maintenance | Preserved outputs; repaired rotation precision, frame identity and metric accounting; rebuilt measurement logging | Statistical calibration, independent backup and unused live/Spires coverage remain incomplete |
| E0 frontend correction | 0.205deg vertical correction reduces development full-system mean ter0.761655→0.388718%; exposed-system transfer0.959528→0.505615% | Established engineering gain; cannot be credited to a new RAP mechanism |
| F2 / candidate diagnostics | On hard08,41/75 positives have no strict-correct native K4 candidate;4/75 are selector misses | Candidate creation is a larger observed category; this does not uniquely diagnose its cause |
| Feature / step / support / decoder studies | RAP uses descriptors and context, but the fixed constructive alternatives fail their material/safety screens | Model responsiveness and oracle availability do not imply executable registration or graph improvement |
| Native local-motion screen | Three-scan RAP median t0.094945m versus KISS0.018766m; same-point three-scan geometry also defeats its full improvement gate | Current sparse native layout is unsuitable for replacing local odometry; no general impossibility claim |
| RLP2 learned readout | Joint tokens beat separated tokens, but the full comparison against descriptors fails and practical controls are substantially better | Median joint t0.888431m versus same-point geometry0.097115m and matched KISS0.022371m; no trajectory stage |
| Map / revisit refinement | Some translation/ATE gains, accompanied by rotation or case safety failures | Residual reduction is not a dependable accuracy gate in these cases |
| NOC0 / NOC1 | Tiny native adaptation can fit one fixed noise; fresh-noise mean gains exist | Only1/4 fresh-noise cells passes the complete gate; no stable conjunction or scene transfer |
| NOC2 / NOC3 | Affine control stops near20mm; fixed-anchor rigid control fits and scaled conditioning improves | Positive numerical control, rather than demonstrated neural/system convergence |
| NOC4 attempt02 | Runtime reaches native probes; both one-step objectives increase; P cache/full backward differs | Scientific comparison INCOMPLETE; zero fitted updates and zero comparison prediction traces |

Sources: [E0](../../2026-09-26/e0-frontend-01/REPORT.md), [transfer](../../2026-09-27/e0-heldout-01/REPORT.md), [F2 diagnosis](../../2026-09-27/f2-postmortem-01/REPORT.md), [local motion](../../2026-10-05/local-motion-screen-01/REPORT.md), [RLP2](../../2026-10-08/motion-supervised-readout-01/REPORT.md).

The important outcome of the negative screens is narrower than “RAP does not work.” They retire specific frozen constructions, prevent repeated retrospective rescue, and clarify which success criterion has not been met. No stopped route is reopened by this review.

## 4. Map objective versus reference conflict

CV2 locks every B rotation exactly and refines only second-visit translation. Cases00/06 improve;05 ATE and endpoint translation worsen6.334%/18.559%. Mean ATE gain4.107817% misses5%, and05 violates safety. All three holdout surface residuals nevertheless improve. Thus a lower training or held-out plane residual does not certify a better reference pose. Six-DOF refinement improves both R/t on06, so a universal rotation lock is also unsupported.

MF0 then rebuilds the same three revisits' complete B-formed and reference-formed memberships. All22055 candidate voxels and84 cost records are independently reconstructed. Every training set still prefers B, including reference-formed sets and shared-row diagnostics. Merely forming groups at B is insufficient to explain the conflict. The06 reference-formed holdout exception, where reference RMS is0.221mm lower, remains visible.

This narrows an explanation without verifying physical surface identity or establishing that official GT is wrong. Internal motion shape, association/aliasing, dynamics, scanning/timing/calibration and reference limitations remain unresolved. The shared-plane objective stays stopped pending independent physical evidence; more optimizer steps or a residual-based selector is unjustified.

The earlier09 online discrepancy is related evidence uncertainty, not a proven common cause: RAP/Geo median overlap81.34%/78.51% versus official relative pose2.5% on the observed inputs. Available frame/time/calibration and local geometry checks narrow gross conventions but do not settle physical truth. It neither invalidates hard08 labels nor permits replacing official metrics.

Sources: [CV2](../../2026-10-09/rotation-protected-map-pilot-01/REPORT.md), [MF0](../../2026-10-10/membership-formation-diagnosis-01/REPORT.md), [09 diagnostic](../../2026-10-05/online-geometry-consistency-01/REPORT.md).

## 5. The positive control and current native bottleneck

NOC3 optimizes12 metric rigid variables with a fixed identity anchor in CPU float64. All four RAW/SCALED × DIRECT/DECODE conditions pass5mm/.05deg and numerical validity. Scaling reduces the identity Hessian condition number205.067699→1.001903 and accepted optimization work12 iterations/14 closures→4/6. DIRECT and SVD-decoded paths agree for this smooth rigid family. This proves that the known-transform objective and rigid control can be made numerically feasible. It changes family, gauge, precision and optimizer relative to NOC2 and therefore does not uniquely isolate the old failure or certify conditioning of443904 neural parameters.

NOC4 restores identical original443904 trainables for velocity V and relative-pose P probes. Only the last two layers' rank8 global QKV/output adapters and the final velocity MLP are trainable; the rest remains frozen. Backward multipliers V1024/P1/1024 are divided out before AdamW, and are not loss weights. A starts inactive because B=0; finite active B/MLP gradients and parameter motion are observed.

| Arm / path | Loss before | Loss after | Reproducibility |
|---|---:|---:|---|
| V cache/full | 7.210630e-6 | 9.050254e-4 | Saved gradients, optimizer, parameters and outputs match exactly |
| P cache | 198.489161 | 384.974440 | Differs from full backward/update |
| P full | 198.489161 | 385.364910 | Initial parameters and pre-update output match cache |

Loss magnitudes across V/P have different definitions; compare before/after within an arm. P differs at7268 gradient values(max0.375),4329 updated parameters(max0.000199999246) and8997 output coordinates(max0.000820875168). Differences appear in B gradient groups while MLP group norms match. Four actual restored optimizer calls occurred; no probe update was retained. Neither planned400-update fit nor72-trace comparison occurred.

Negative gradient dot actual update coexists with increased observed loss. A1e-4 coordinate bound yields total parameter movements about0.0603/0.0650 and cannot guarantee finite functional descent. Selected output-weight finite differences do not check the complete parameter-direction derivative. Current evidence does not uniquely establish cache error, fp16 nondeterminism, curvature or overshoot. The failed byte-equality validator stays failed; the later CPU artifact audit is a separate bounded audit rather than its repair.

The 10-10 runtime recovery is historical validated engineering evidence: targeted overlay restart releases17.772GiB observed host commit; three target-free native checks complete, two with full Windows supervision. It does not make NOC4 successful or guarantee current/future host headroom. This review performed only read-only WSL repository/source checks, no fresh neural runtime verification.

Sources: [NOC3](../../2026-10-10/rigid-control-conditioning-01/REPORT.md), [NOC4](../../2026-10-10/native-conditioned-comparison-01/attempt-02/REPORT.md), [runtime recovery](../../2026-10-10/wsl-runtime-recovery-01/REPORT.md).

## 6. Stage judgment and next priority

The engineering baseline and evidence chain are substantially stronger than the early project state. Further research must cross three separate gaps: reliable neural backward/update behavior, an observation objective that predicts useful pose changes, and a gain that survives practical controls and system safety. Completing another artifact seal alone crosses none of these scientific gaps.

The immediate native next step remains **DESIGN_ONLY**: separately scope repeated full-forward P backward checks on immutable inputs, then cached/full comparisons, retaining upstream output gradients and every trainable tensor. Whole parameter-direction checks and functional step policy come only after reproducibility is understood. No new protocol freeze or neural execution is introduced here. This is not permission to rescue the stopped pilot by changing its rate, scales, seed, initialization or gate.

The shared-plane line requires independent physical observation evidence before further refinement. For future system proposals, declare which metric is primary before outcomes and keep the other metric's safety/tradeoff visible. ATE and ter can disagree even with lower residuals and improved pair scores. Existing competitive ter is a thesis asset, while weak development ATE and the unproven additional RAP benefit remain the central result gaps.

The owner's10-09 relaxation permits useful conventional geometry and ordinary adaptation to be proposed; older blanket originality exclusions are historical. It does not amend negative decisions or authorize a new experiment from this summary request. Original mechanism, physical accuracy, calibrated confidence and independent generalization remain unestablished. Exact local checkpoint training/site membership is still unknown, and fixed-seed repetitions are not new independent scenes.

## 7. Checks and document continuity

[CHECKS.json](CHECKS.json) and [IDENTITY_CHECKS.json](IDENTITY_CHECKS.json) record this review. Fourteen delivery dossiers match:103/188/53/5/37/40/60/86/35/42/37/42/39/56 entries. Benchmark71 source identities and144 trajectory/binding entries match. All204 NOC4 attempt02 freeze identities match, including two WSL optimizer sources hashed separately without Python imports. Across overlapping checks there are1278 identity references and1107 distinct verified files;1105 local files total675952923 bytes. The stored36-run means, population standard deviations, repetition grid, frame counts, child completion fields and repetition choices match. NOC4 INCOMPLETE, four probes and zero fit updates remain intact.

The initial review helper stopped while treating a Linux-only path as a Windows-relative path, before emitting review results. It was corrected to consume the separate observed WSL hash receipt. Historical scientific code, outcomes, thresholds and seals were not changed. Review timing is not a new scientific resource certification.

This is not an all-history/raw-data/model/optimizer replay. Existing validator findings are cited as historical validation, distinguished from the fresh identity and scalar-arithmetic checks above. Old missing resource/supervision intervals, failure snapshots and negative decisions remain.

AGENTS.md's newest scientific entry was dated10-10 and did not mention the10-11 meeting benchmark; the current entry now links this summary and that separate result. Historical entries and sealed handoff snapshots are preserved. RAP-SLAM README still presents older07-20 conclusions and should be read as history rather than the current phase authority. No README, production/default/backbone/manuscript, official reference, installation, process configuration or Git history was edited.
