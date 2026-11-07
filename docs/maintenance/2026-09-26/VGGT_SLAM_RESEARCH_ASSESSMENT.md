# RAP-SLAM research assessment inspired by VGGT-SLAM

2026-09-26. Discussion only; no experiment or production change.

## Owner intent

HC-V1 served the weekly Sunday group meeting. The owner now asks to return to
the research mainline, improve capability and examine lessons from VGGT-SLAM,
the original inspiration for building a SLAM system around RAP.

## Sources inspected

- VGGT-SLAM 1.0 paper, explicit arXiv v2:
  https://arxiv.org/html/2505.12549v2
- Official 1.0 implementation, inspected solver and README:
  https://github.com/MIT-SPARK/VGGT-SLAM/tree/version1.0
  https://raw.githubusercontent.com/MIT-SPARK/VGGT-SLAM/version1.0/vggt_slam/solver.py
- VGGT-SLAM 2.0 paper, explicit arXiv v1:
  https://arxiv.org/html/2601.19887v1
- Official repository distinguishes main (2.0) from version1.0:
  https://github.com/MIT-SPARK/VGGT-SLAM
- RAP paper: https://arxiv.org/html/2512.01850v1
- Local HC-V1 report, frozen research memo and current pair-registration path
  in RAP-SLAM/rap_slam/{loop_closure,rap_backend}.py.

This is a focused reading, not a complete source audit or novelty search.

## Literature observations

VGGT-SLAM 1.0 incrementally aligns overlapping model-generated submaps and uses
SL(4) optimization to accommodate projective ambiguity from uncalibrated images.
Its results must be interpreted by calibration setting: TUM ATE is 0.053 m for
its SL(4) arm, versus 0.060 m for uncalibrated MASt3R-SLAM and 0.030 m for the
calibrated MASt3R-SLAM row. It does not establish universal metric dominance.
The inspected solver adds retrieved historical images to the current image
batch before model inference, providing a concrete example of joint conditioning.

VGGT-SLAM 2.0 addresses initial high-dimensional drift and planar degeneracy
through constraints on shared frames and a keyframe-level graph. It also studies
model attention for retrieval verification. These mechanisms are specific to
VGGT and cannot be presumed effective in RAP.

RAP already provides multi-view registration and rigidity-forcing sampling;
its paper already demonstrates map merging and related robotics applications.
It assumes a common scene and acknowledges inference speed limitations at
automotive LiDAR rates. Native multi-view use or map merging alone is not a new
contribution for this project.

## Assessment and proposals (not measured conclusions)

HC-V1 establishes an end-to-end gap, not a causal attribution to RAP or to a
particular front-end parameter. E0 can separate engineering configuration gains
from research gains. Its limited arms should remain prospective; old baseline
artifacts remain canonical until a successor is explicitly frozen.

Our default RAP use is pairwise loop measurement. A more model-centered system
would exploit structured multiple observations where local odometry is reliable
but cross-visit alignment is uncertain. The existing F1 proposal is a bounded
test of that idea: preserve six scan parts and constrain within-visit motion
during clean-endpoint generation, with final-only/native/pooled controls.
This is distinct from the stopped pooled-context route but remains unproven.
Unlike identical shared images, estimated LiDAR motion is not an exact identity;
constraint bias and motion sensitivity must be tested.

Retain SE(3) for metric LiDAR. No evidence supports importing SL(4) deformation
variables. Retain a fast local front-end initially; greater RAP involvement
should follow demonstrated value rather than replacing tracking on principle.
If multi-view measurements eventually enter a graph, account for dependence
between measurements from one generation and reused odometry; do not count all
derived pairwise edges as independent evidence.

Attention diagnostics are an unselected alternative, not permission to restart
failed selectors or search layers/thresholds on observed outcomes. Likewise,
submap integration is a conditional architectural destination, not implemented
work. First establish incremental registration value over strong same-input
comparators, then evaluate graph impact, trajectory, map quality and cost.

Useful evidence needs both competitive standard-sequence performance and
predeclared challenging conditions such as weak initial alignment. Do not replace
unfavorable KITTI results with favorable demonstrations or claim unseen RAP
training domains without tracing checkpoint membership.

## Next boundary

Recommend E0 engineering alignment and the existing F1 research preflight in
bounded sequence, without a broad rewrite. This discussion does not approve E0
execution, freeze a new protocol or establish a positive research result.
The existing F1 preparation authorization remains; all prior negative decisions
and manuscript pause persist.
