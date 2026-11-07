# Thesis results and evidence v2

Compiled after the experiments on 2026-09-13. This is a reporting consolidation, not a new preregistration. Keep the default offline system and the O3 source-balanced comparison separate. All four sequences are observed development data.

## Main default system: complete raw-scan reruns

| Sequence | Frames | Accepted loops | Odom first APE m | RAP first APE m | RAP aligned APE m | Odom translation drift % | RAP translation drift % |
|---|---:|---:|---:|---:|---:|---:|---:|
| poss | 1419 | 4 | 8.257400 | 1.822264 | 0.666054 | 3.859185 | 1.961403 |
| kitti06 | 1101 | 12 | 2.777067 | 2.446184 | 0.868971 | 0.643021 | 0.667058 |
| kitti05 | 2761 | 12 | 5.193528 | 3.417117 | 1.129313 | 0.772150 | 0.703737 |
| kitti00 | 4541 | 12 | 12.266655 | 11.432935 | 2.891543 | 0.904738 | 0.914171 |

The same fixed budget-12 RAP loop system improves first-pose APE over odometry on all four sequences. Camera translation drift worsens on KITTI 06 and 00. Thus global APE gains do not imply universal local drift gains. These full runs persist source-frame identities; legacy frontend assumptions are not used for this table.

## O3 fixed-budget source allocation: matched registrars

O3 allocates up to six proximity and six distinct SC candidates with deterministic backfill. Its 40 RAP attempts are all accepted. O3 failed the predeclared adoption screen and remains an experimental arm.

| Sequence | Method | Accepted / attempted | First APE m | Aligned APE m | Translation drift % | Rotation drift deg/100m |
|---|---|---:|---:|---:|---:|---:|
| poss | RAP | 4/4 | 1.822264 | 0.666054 | 1.961403 | 1.978396 |
| poss | ICP identity | 4/4 | 1.857711 | 0.658426 | 1.974556 | 1.973658 |
| poss | ICP odometry | 4/4 | 1.912702 | 0.676671 | 1.988490 | 1.977965 |
| kitti06 | RAP | 12/12 | 2.533434 | 0.862829 | 0.663797 | 0.315563 |
| kitti06 | ICP identity | 12/12 | 2.576697 | 0.856666 | 0.660728 | 0.314419 |
| kitti06 | ICP odometry | 12/12 | 2.581416 | 0.856060 | 0.660686 | 0.314323 |
| kitti05 | RAP | 12/12 | 3.214084 | 1.168216 | 0.715824 | 0.341193 |
| kitti05 | ICP identity | 9/12 | 3.179688 | 1.185694 | 0.698234 | 0.335186 |
| kitti05 | ICP odometry | 12/12 | 3.137198 | 1.157918 | 0.726223 | 0.346030 |
| kitti00 | RAP | 12/12 | 10.336943 | 2.109192 | 0.896651 | 0.384225 |
| kitti00 | ICP identity | 11/12 | 10.512414 | 2.107358 | 0.894535 | 0.384754 |
| kitti00 | ICP odometry | 12/12 | 10.567533 | 2.131840 | 0.902600 | 0.387940 |

Drift uses the KITTI camera frame; POSS uses a custom LiDAR-frame segment measure. Do not pool them or call POSS an official KITTI benchmark. First APE uses first-pose LiDAR alignment; rigidly aligned APE is distinct.

RAP has lower first-pose APE than either ICP arm on POSS, KITTI 06 and 00. Both ICP arms have lower first-pose APE on KITTI 05. Secondary metrics do not follow this ordering: for example, identity ICP has slightly lower aligned APE on POSS and KITTI 00, and both ICP arms have lower aligned APE and camera translation drift on KITTI 06.

Identity ICP accepts 36/40; its four dangerous measurements (three on KITTI 05, one on KITTI 00) are rejected. Odometry ICP accepts 40/40, all safe. All 80 attempts complete and all 76 accepted edges exactly reference their logged measurements. A safe label means pose error <= 5 m and <= 10 degrees, not negligible bias or guaranteed trajectory improvement.

These are fixed-gate system comparisons with potentially different accepted sets. Odometry ICP receives a pose prior; RAP and identity ICP receive no external relative-pose prior. Do not claim superiority over all classical/global registration, unseen domains or independent statistical risk guarantees. ICP registration-only times are not comparable to full RAP-stage wall times as a speed ratio.

## Interpretation for the thesis

The evidence supports a traceable offline integration of frozen pretrained RAP with KISS-ICP, candidate retrieval, geometric gating and graph optimization. No task-level fine-tuning is performed. The system improves global trajectory error on the four development sequences, while registration choice, candidate allocation and evaluation metric affect the result.

O1 ICP refinement, O2 increased budget and O3 source balancing each yield mixed outcomes and do not replace the default. The clean-cohort backend ablation was negligible, so robust weighting is an engineering choice rather than a demonstrated performance contribution. Do not choose the best method separately for each sequence and present that combination as one system.

## Evidence map

- Main full baseline: [report](../../2026-09-11/core-baseline-v1/REPORT.md) and its registry/source manifests.
- O1-O3: [synthesis](../OPTIMIZATION_SYNTHESIS.md), preserving secondary regressions.
- O3 matched comparison: [report](../o3-comparator-01/REPORT.md), per-attempt logs, source_manifest.json and association_validation.json.
- Candidate/measurement confounding: [common-edge-fixed diagnostic](../o3-common-fixed-01/REPORT.md); explicitly post-hoc.
- Earlier proximity-priority ICP comparison: [report](../../2026-09-11/comparator-01/REPORT.md); frozen legacy frontend scope, separate from O3.
- Runtime: full-run timing includes warmed reads/map export and clock-accounting limitations; no real-time claim.
- Deferred: independent backup, checkpoint training membership, optional statistical validation and unused ROS/Spires features.

Next deliverable: draft the thesis experimental-results section using these fixed tables and measured limitations. Do not launch further parameter sweeps merely to remove negative results. Any additional experiment needs a specific unresolved question.
