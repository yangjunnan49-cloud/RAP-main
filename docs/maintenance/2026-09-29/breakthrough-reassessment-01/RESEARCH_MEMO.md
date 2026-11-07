# Breakthrough reassessment after P0 and M1 (2026-09-29)

Status: research assessment and next-test proposal. No external comparator,
new RAP method, training, default change, or Git synchronization is frozen or
running. The owner's original-breakthrough requirement and manuscript pause
remain in force.

## What the local evidence actually says

The central failure is **candidate creation under cross-visit change**. On
the exact F2 observed-development KITTI 08 positives, 41/75 have no strict
pose among the four native generations. Of those 41, 37 have a best
generation within the 5-degree rotation limit but miss the 1-metre
translation limit; 26 have best translation error at most 2 m, while six
exceed 10 m. The strict condition is 1 m and 5 degrees. These strata do
not imply that one local translation correction will solve all cases.

The evidence argues against simply spending more computation on the same
representation: S1's 5-to-10-step change, D0 saved intermediate steps,
V0's fixed local translation grid, C5 support-feature masking, C6 earlier
donor transport, and P0's more paper-like 0.25 m/FPS/full-support input
all missed their prospective material gates. C1 found weak cross-visit
miniSpinNet top-1 information in the hard group. C2 established that RAP
uses the feature channel, but did not show that feature replacement would
improve registration. P0 improved geometric coverage without material
descriptor-information gain. I1 intensity and C3 anchor-only FPFH were
negative under their frozen information tests. These results constrain
the tested routes; they do not establish an impossibility theorem for RAP.

M1 tested one genuinely available but previously unused output path: each
native generation's six predicted part poses plus F2's saved within-visit
motions produce nine anchor-pair hypotheses. The GT-free bank of 36
hypotheses per pair was sealed before labels; independent validation passed
18,028 checks. On the 41 hard 08 positives, only four acquired a strict
support-derived pose and only two an interior pose. The frozen material
headroom rule required at least five and three respectively. Thus the
exact support-transport route stops. Its best-of-36 oracle changes 08
strict positive availability from 34/75 to 38/75, but supplies no
GT-blind selector or acceptance result. The 10 incorrect F2 accepts on 08
also mean pose availability and safety must be assessed separately.

Source records: [F2 report](../../2026-09-27/f2-postmortem-01/REPORT.md),
[mechanism memo](../../2026-09-28/NEXT_MECHANISM_MEMO.md),
[P0 report](../p0-point-selection-information-01/REPORT.md),
[M1 report](../m1-support-pose-hypotheses-01/REPORT.md).

## What other work changes, and what it does not license here

| Work | Mechanism relevant to this failure | Boundary for this project |
| --- | --- | --- |
| [GeoTransformer](https://github.com/qinzheng93/GeoTransformer) | Rigid-invariant distance/angle context builds cross-view correspondences; official KITTI code and checkpoint are offered. | A strong external registration comparator, not a RAP gain. Its reported KITTI result uses its own pairs and evaluation. |
| [UGP](https://github.com/peakpang/UGP) | Outdoor-focused intra-frame features, progressive self-attention and BEV cues target generalization and scene ambiguity. | Interesting comparator, but the published setup and old PyTorch/CUDA dependencies need feasibility and training-split checks before use. |
| [Regor](https://openaccess.thecvf.com/content/CVPR2025/papers/Zhao_Progressive_Correspondence_Regenerator_for_Robust_3D_Registration_CVPR_2025_paper.pdf) | Regenerates correspondences under very weak initial matches instead of only rejecting outliers. | Makes a generic RAP-seeded correspondence-regeneration idea non-novel without a distinct tested mechanism. |
| [Quatro++](https://quatro-plusplus.github.io/) | Uses ground segmentation and robust global registration for sparse/degenerate outdoor loop geometry. | Ground removal or a robust estimator alone is established prior art. |
| [BEV-LIO(LC)](https://arxiv.org/abs/2502.19242) | BEV matches produce a coarse loop transform before ICP and graph integration. | BEV coarse-to-fine alone is established prior art. |

Their headline registration recalls are not comparable to F2's exact
200-pair observed-development cohort, positive/confuser composition, and
strict 1 m/5-degree test. Reproducing one model on the same pairs is a
measurement, not a new method claim.

Feasibility is a real gate. GeoTransformer's official KITTI release lists
pretrained weights, but its tested stack is Python 3.8, PyTorch 1.7.1,
CUDA 11.1 and Open3D 0.11.2; the local RTX 5070 RAP environment uses
PyTorch 2.7/CUDA 12.8. Therefore the release is **not yet known runnable**
here. A clean compatibility audit and isolated execution path are needed;
do not modify the working RAP environment or treat a ported model as an
exact reproduction without checks. The released weight's training-set
membership must also be verified from primary material rather than
inferred from community benchmark conventions.

## Priority decision: calibrate the ceiling with one external method

First audit and, if feasible, run **one** released outdoor checkpoint on
the exact F2 200 pairs, favoring GeoTransformer because its public repo
explicitly provides a KITTI checkpoint and test path. Verify the weight
identity and train/test split, dependencies, input frame convention and
pose direction before freezing the protocol. Freeze exact source files,
checkpoint hash, pairs, input preprocessing, computation cap, output
schema, validator and stop margins before any pair output. Seal every
GT-free predicted pose, confidence and runtime before using the F2 GT
evaluator. Report strict 1 m/5-degree outcomes separately for 00/08,
ordinary/low-overlap/ambiguous/confuser, and especially the 41 hard 08
native-K4-unavailable positives. Count new strict candidates, false
acceptance under a separately frozen common gate, and per-pair resource
cost. Preserve the model's own output rather than tuning it to F2 labels.

Use the result as a branch point:

1. If a strong independent matcher has material hard-08 recovery, inspect
   its GT-blind correspondence coverage and translation residuals. This
   would show that cross-visit structure survives in the raw data and
   locate a concrete information path RAP does not exploit. Only then
   freeze a distinct RAP-side candidate mechanism with matched direct-
   matcher and same-compute controls.
2. If it also fails, inspect overlap, structural aliasing and GT/frame
   consistency on the failed cohort before training or integrating a new
   module. A negative external comparison would not prove impossibility,
   but would lower the priority of another local RAP refinement.
3. If the official checkpoint is infeasible or its training membership
   cannot be authenticated, record that fact and make a separate decision
   about another comparator. Do not silently substitute checkpoints,
   pairs, thresholds or preprocessing.

The comparator is not an independently held-out claim: these 200 pairs
have already been used for development diagnosis. Its purpose is mechanism
calibration and fair same-cohort comparison.

## Conditional candidate direction, not yet a protocol

The strongest design hypothesis is a **rotation-conditioned, structural
translation proposal**. RAP's near-correct rotation on 37/41 hard 08
pairs suggests testing whether cross-visit evidence can identify one or
several translation modes over a range wider than V0's fixed +/-1 m grid.
A causal short submap on each visit could stabilize persistent ground,
facade and vertical structure; a spatial correlation or correspondence
stage could propose translation modes, which RAP could refine or score.
The preliminary information question is whether such modes exist in
GT-blind structural evidence, not whether a GT-selected mode is correct.

This idea overlaps Quatro++, BEV loop registration, geometric feature
matching, and Regor. Its novelty cannot be asserted from a component
list. Any original contribution would need a demonstrably distinct
interaction with RAP's generative hypotheses or an evidence-backed way
to construct and rank modes under dynamic/repetitive scene changes. It
must beat the direct external matcher and same-input/compute structural
baseline on strict candidate creation, keep 00 and confuser safety, and
survive a later independent cohort. If the external calibration gives no
cross-visit signal, do not build this module merely because it sounds
plausible.

## Research discipline

Keep a hierarchy of claims: information signal, candidate oracle,
GT-blind selection, accepted loop, and graph improvement are different
outcomes. No source paper's score transfers across our cohort or strict
threshold. Freeze each new test and an independent validator before
output; seal generated banks before GT. Preserve completed banks and
negative decisions. No margin relaxation, method sweep, checkpoint
shopping or production edit to rescue a failed result. Originality must
be argued against the cited primary methods only after a measured gain.
