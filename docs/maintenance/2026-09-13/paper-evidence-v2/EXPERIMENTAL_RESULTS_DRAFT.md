# Experimental evaluation

## Scope and evaluation protocol

This chapter evaluates an offline LiDAR SLAM system that uses frozen pretrained
RAP to estimate loop constraints for a KISS-ICP trajectory. The experiments
address three questions: whether the integrated system improves trajectory
accuracy over odometry, whether selected changes to registration and retrieval
produce consistent gains, and how RAP compares with conventional local
registration on identical candidate pairs. No task-level fine-tuning is performed.
The four sequences have already been used during system development; the results
therefore characterize this development cohort rather than an independent test
population. Checkpoint-specific training membership has not been established,
and training-domain novelty is not claimed.

Table 1 specifies the evaluated scan ranges. Each complete run starts from raw
scans and regenerates odometry, keyframes, retrieval, RAP measurements and pose
graph optimization. Source-frame IDs and input identities are persisted. Later
component comparisons reuse the explicitly bound frontends, avoiding changes in
odometry between methods. The POSS range is a segment of sequence 00, rather
than the entire sequence. [E1]

**Table 1. Evaluation ranges; endpoints are inclusive and stride is one.**

| Sequence | Source-frame range | Scans | Keyframes |
|---|---|---:|---:|
| POSS 00 | 3850–5268 | 1419 | 82 |
| KITTI 06 | 0–1100 | 1101 | 202 |
| KITTI 05 | 0–2760 | 2761 | 374 |
| KITTI 00 | 0–4540 | 4541 | 670 |

The default system uses keyframe thresholds of 6 m translation and 12 degrees
rotation and includes the last scan as a keyframe. Candidate retrieval combines
odometry proximity and Scan Context with a total budget of 12. Proximity uses a
15 m threshold and a minimum separation of 200 source frames. Scan Context uses
20 rings, 60 sectors, an 80 m radius, a shortlist of 10 and a distance threshold
of 0.25. Proximity candidates retain priority when the lists are merged. RAP
uses five sampling steps, one generation, a 0.4 m preprocessing voxel and a cap
of 4000 points per scan. A measurement is accepted when overlap is at least 0.7
and mean alignment distance is at most 2.5 m. The backend uses relative-floor
weighting and a Huber kernel, with loop non-maximum suppression disabled.
Deskew, the optional KITTI angular correction and odometry fallback are disabled.
Settings are fixed across sequences. [E2]

The primary outcome is LiDAR translation absolute pose error (APE) RMSE after
anchoring the estimated and reference trajectories independently at their first
poses. A separate rigidly aligned APE permits a global SE(3) fit without scale
correction. These measures answer different questions and are not interchangeable.
Segment translation drift is reported separately in the camera frame for KITTI,
using the calibration transform and corrected all-segment aggregation. POSS uses
a custom LiDAR-frame segment measure. Results are reported per sequence without
pooling these different drift conventions. These are local evaluations, not an
official benchmark submission. [E1, E2]

## Complete default-system results

Table 2 compares odometry with the complete default system. RAP loop constraints
reduce first-pose APE on all four sequences. The largest absolute reduction is
observed on POSS, from 8.257400 m to 1.822264 m. KITTI 00 retains a substantially
larger residual error than the other sequences, despite improving from
12.266655 m to 11.432935 m. Thus, the observed loop corrections improve global
trajectory accuracy but do not remove all accumulated error. [E1]

**Table 2. Default full-system results. APE is in metres; translation drift is
in percent. Drift is camera-frame for KITTI and LiDAR-frame for POSS.**

| Sequence | Accepted loops | Odom first APE | RAP first APE | RAP aligned APE | Odom drift | RAP drift |
|---|---:|---:|---:|---:|---:|---:|
| POSS | 4 | 8.257400 | 1.822264 | 0.666054 | 3.859185 | 1.961403 |
| KITTI 06 | 12 | 2.777067 | 2.446184 | 0.868971 | 0.643021 | 0.667058 |
| KITTI 05 | 12 | 5.193528 | 3.417117 | 1.129313 | 0.772150 | 0.703737 |
| KITTI 00 | 12 | 12.266655 | 11.432935 | 2.891543 | 0.904738 | 0.914171 |

The drift results qualify the APE improvements. Camera translation drift
increases on KITTI 06 and KITTI 00 after optimization. Global position error and
segment-relative motion error need not change in the same direction: an
optimization can improve the global trajectory while worsening some local
relative motions. The measurements support an improvement in the specified
global error measure, rather than a claim of improvement in every trajectory
metric.

All 40 attempted default-loop measurements are accepted and satisfy the recorded
pose-error label: translation error at most 5 m and rotation error at most
10 degrees relative to ground truth. This label is used for retrospective
evaluation, not for acceptance. It indicates neither negligible measurement bias
nor guaranteed benefit to the optimized trajectory. Since this RAP cohort has
no dangerous measurements, it cannot establish a dangerous-edge acceptance rate
or calibrate a statistical risk guarantee. [E1]

## Registration and retrieval ablations

Three bounded development experiments examine changes to the default system.
O1 refines each RAP transformation using fixed point-to-point ICP and recomputes
the acceptance diagnostics. O2 increases the candidate budget from 12 to 40,
regenerating measurements in both arms. O3 retains budget 12 but selects six
proximity candidates followed by up to six distinct Scan Context candidates;
unfilled slots are backfilled in a deterministic order. The frozen frontend,
geometric gate and backend remain fixed. Table 3 reports all sequences for each
policy; no per-sequence combination of winning policies is constructed. [E3]

**Table 3. First-pose LiDAR APE (m) for bounded ablations. The reference column
uses the O2 budget-12 replay; its agreement with the full runs is within
7 × 10⁻⁷ m.**

| Sequence | Reference | O1: RAP + ICP | O2: budget 40 | O3: source allocation |
|---|---:|---:|---:|---:|
| POSS | 1.822264 | 1.912266 | 1.822264 | 1.822264 |
| KITTI 06 | 2.446184 | 2.516788 | 2.558393 | 2.533434 |
| KITTI 05 | 3.417117 | 2.913561 | 3.487993 | 3.214084 |
| KITTI 00 | 11.432936 | 11.533925 | 10.931019 | 10.336943 |

O1 improves first-pose APE only on KITTI 05. O2 improves KITTI 00 but worsens
KITTI 06 and KITTI 05; POSS saturates at four candidates under both budgets.
All selected O2 candidates belong to the proximity lists. Increasing the budget
therefore does not, by itself, ensure participation by SC-only candidates.

O3 introduces four, four and six candidates outside the respective top-12
proximity lists on KITTI 06, 05 and 00. It improves first-pose APE on KITTI 05
and 00, worsens it on KITTI 06 and leaves POSS unchanged. Secondary outcomes
again differ. On KITTI 05, aligned APE increases from 1.129313 m to 1.168216 m
and camera translation drift increases from 0.703737% to 0.715824%, despite the
first-pose APE improvement. On KITTI 06, aligned APE and camera translation drift
improve to 0.862829 m and 0.663797%, respectively, despite first-pose APE worsening.
KITTI 00 improves all three reported measures under O3. [E3]

Each experiment used a predeclared practical screen requiring first-pose APE
improvement on at least three sequences, no regression exceeding 5%, and no
accepted dangerous edge. O3 additionally specified a numerical improvement
tolerance of 10⁻⁶ m. None passed. These screens guide engineering decisions;
they are not statistical significance tests. The default system is retained.

RAP sampling follows a shared random-number stream in candidate order. O3 changes
some common-pair measurements when their ordering changes. A post-hoc diagnostic
replaces those common-pair measurements with their exact reference measurements,
while retaining O3 measurements for new pairs. Its first-pose APE values are
1.822264, 2.535805, 3.213732 and 10.336943 m for POSS, KITTI 06, 05 and 00.
The directions of the O3 changes persist. This limits the explanation based on
common-pair sampling variation, but does not isolate sampling effects on new
pairs or constitute an additional prospective experiment. [E4]

A separate backend comparison uses identical fresh edges with fixed versus
relative-floor noise and with versus without Huber weighting. The largest
first-pose APE spread is approximately 0.00055 m, on POSS. This clean cohort
does not demonstrate a performance advantage from robust weighting. Relative-floor
and Huber weighting are consequently treated as backend engineering choices,
rather than independently validated robustness contributions. [E5]

## Matched registration comparison on the O3 cohort

The O3 candidate list is also held fixed for a comparison with point-to-point
ICP. Both ICP arms process every candidate using the same geometric preprocessing
and recomputed gate. One starts from the identity transform; the other starts
from the odometry relative pose. Open3D ICP uses a 2.5 m correspondence threshold,
100 iterations and relative fitness and RMSE tolerances of 10⁻⁶. RAP receives no
external relative-pose initialization. Odometry-initialized ICP has an additional
pose prior, so its results are reported separately. [E6]

**Table 4. O3 matched comparison: first-pose APE (m), with accepted/attempted
counts in parentheses.**

| Sequence | RAP | ICP: identity | ICP: odometry |
|---|---:|---:|---:|
| POSS | 1.822264 (4/4) | 1.857711 (4/4) | 1.912702 (4/4) |
| KITTI 06 | 2.533434 (12/12) | 2.576697 (12/12) | 2.581416 (12/12) |
| KITTI 05 | 3.214084 (12/12) | 3.179688 (9/12) | 3.137198 (12/12) |
| KITTI 00 | 10.336943 (12/12) | 10.512414 (11/12) | 10.567533 (12/12) |

RAP has lower first-pose APE than both ICP arms on three sequences. On KITTI 05,
both ICP arms yield lower first-pose APE. The comparison therefore does not
establish universal superiority of RAP, even within this small cohort. It also
does not compare RAP against global classical registration methods.

The secondary metrics further qualify this result. On KITTI 06, identity- and
odometry-initialized ICP achieve aligned APE of 0.856666 m and 0.856060 m,
respectively, compared with RAP's 0.862829 m. Their camera translation drift is
also lower: 0.660728% and 0.660686%, compared with 0.663797%. Identity ICP has
slightly lower aligned APE than RAP on POSS and KITTI 00 as well. Complete
secondary results are retained in the accompanying evidence tables. [E7]

All 80 ICP attempts complete. Identity ICP accepts 36 of 40 measurements and
rejects four dangerous results: three on KITTI 05 and one on KITTI 00.
Odometry-initialized ICP accepts all 40, all labeled safe. This demonstrates
successful rejection of those particular failures, not a population-level
guarantee. Because methods can accept different edge sets, Table 4 compares
fixed-gate SLAM systems, rather than registration accuracy alone.

## Execution cost, traceability and limitations

The full pipelines record wall times of 137.63 s on POSS, 99.61 s on KITTI 06,
166.79 s on KITTI 05 and 267.98 s on KITTI 00. These are single-run observations
on the recorded Windows/WSL2 workstation with an RTX 5070. They include map
export and input reads warmed by preflight hashing. Some stage totals differ
from monotonic subprocess duration, so precise throughput or cold-start claims
are not supported. O2 increases KITTI loop-verification time from approximately
17–18 s to 56–57 s. ICP-only registration timings exclude preprocessing and
cannot be divided into full RAP-stage times to claim a speed ratio. [E1, E3]

The evidence chain links accepted edges to the exact logged measurements and
source scans. The O3 comparator independently checks candidate order, initial
transforms, source IDs, labels, gates and all 76 accepted edge associations, and
recomputes metrics from saved trajectories. Such checks support traceability
and bounded reproducibility; they do not substitute for an independent evaluation
cohort. No formal confidence intervals or calibrated coverage claims are drawn
from these correlated, previously observed sequences. [E6]

The experiments support an offline integration of frozen pretrained registration
with odometry, retrieval, geometric gating and graph optimization. They show
consistent default-system improvements in first-pose APE over odometry, together
with sequence-dependent and metric-dependent tradeoffs in alternative policies.
They do not establish unseen-domain generalization, universal superiority over
ICP, a benefit from every accepted loop, or real-time deployment performance.
Unused online ROS, Spires and multiway/statistical variants remain outside this
chapter's validated core.

## Evidence references for manuscript integration

These local references identify measured artifacts; they are not substitutes for
the final bibliography's method and dataset citations.

- [E1: Full-run baseline and registry](../../2026-09-11/core-baseline-v1/REPORT.md).
- [E2: Fixed full-frontend protocol](../../2026-09-11/FULL_FRONTEND_PROTOCOL.md) and [source ranges](../../2026-09-11/FULL_CORE_COMPLETION_PROTOCOL.md).
- [E3: O1–O3 synthesis](../OPTIMIZATION_SYNTHESIS.md), with links to individual protocols and outputs.
- [E4: Fixed-common-edge diagnostic](../o3-common-fixed-01/REPORT.md).
- [E5: Controlled backend comparison](../../2026-09-11/backend-ablation-01/REPORT.md).
- [E6: O3 comparator](../o3-comparator-01/REPORT.md) and [protocol](../O3_COMPARATOR_PROTOCOL.md).
- [E7: Complete reporting tables](RESULTS.md).
