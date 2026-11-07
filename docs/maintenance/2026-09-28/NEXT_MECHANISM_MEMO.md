# Post-F2 candidate-creation direction (2026-09-28)

## Evidence and decision

There is **positive system engineering evidence**: frozen E0 arm A transferred
against O on complete KITTI07/09/10 in E0-H1 (mean camera ter 0.959528 to
0.505615%, mean aligned LiDAR ATE 1.217655 to 0.721480 m). This is not a
new RAP algorithmic signal, fully unseen-domain claim, or across-the-board
win over same-data KISS-SLAM. F2 S and E1 remain negative under their rules.

The fixed R0 local ICP, G0 equal-2000-point KISS-Matcher and G1 full-scan
KISS-Matcher each recovered **zero** of the 41 KITTI08 positives without a
strict native K4 candidate. G1 used ~120k points per scan and produced 20/75
strict positives on08 versus RAP N/R4's30/75; all G1 successes were already
native successes. G0's 2000-point result was especially under-supported
(199/200 pairs had <5 final inliers), so the full-scan test is the more
informative external component comparator. None evaluated a common executable
gate or graph outcome. Do not integrate KISS-Matcher as a supposed rescue.

In the saved F2 oracle rows, 37/41 native K4-unavailable 08 positives fail
only translation (>1m, rotation <=5deg); 4 fail both and 0 fail rotation
alone. The best-of-K4 oracle translation error is <=2m for 26/41, >10m for
6/41. This is **post-hoc observed-development diagnosis**. It does not make
the oracle executable, identify the physical cause, imply a learnable
correction, or license a threshold change. It does justify studying whether
a translation-focused intervention can alter *generation* before the final
pose fit; fixed after-the-fact ICP did not.

## One bounded next question

Investigate a **visibility-aware cross-view geometric guidance term during
RAP's flow sampling**. The question is whether a fixed, GT-free consistency
signal on the predicted clean endpoints can steer pose *creation* in partial
overlap, including pairs for which native K4 has no strict candidate. It
must retain native scan-specific conditioning and point budget; it must not
reuse F2's hard within-visit projection, pool supports, change acceptance
thresholds, initialize from cross-visit GT/odometry, or merely rerank saved
generations. The candidate is a hypothesis, not a selected method or claimed
novel contribution.

Source feasibility is the immediate gate. RAP's published inference already
has multiview and rigidity forcing, and the local `flow_sampler` computes a
raw clean endpoint at each Euler step (`x_0_hat=x_t-v*t`) before rigid
projection. `sample_rectified_flow` currently runs under
`@torch.inference_mode()`, so gradient guidance would require an isolated
implementation and bounded numerical/memory checks; a gradient through
that decorated call cannot simply be assumed. The released README still
lists training code/data curation as unavailable, so a new training campaign
is not an immediate low-cost continuation. R0 demonstrated that final-pose
point-to-point ICP does not solve this development deficit; any new guidance
must have a mechanism-level control against that baseline.

Before any GPU efficacy screen, specify one exact differentiable or closed-
form visibility-aware energy, its scale/step placement and an engineering
preflight on fixed saved pairs with no outcome selection. Audit closest work
in geometric guidance, overlap-aware registration and RAP itself; visibility,
feature matching, diffusion/flow guidance and rigid projection are prior art.
If this cannot be made stable and independent of GT with a bounded budget,
stop it at feasibility. If it passes, freeze a full 00/08 development
protocol with native N, F2 S/P, R0 ICP and G1 full-scan external controls,
fixed costs and exact gates. A positive development result would still need
fresh confirmation and system impact. Do not treat a favorable oracle or
saved-energy correlation as efficacy.

## Primary-source boundary

- [RAP paper](https://arxiv.org/abs/2512.01850) and local
  `rectified_point_flow/{sampler,modeling}.py`: native multiview, rigidity,
  flow endpoint and current inference-mode constraints.
- [GeoTransformer paper](https://openaccess.thecvf.com/content/CVPR2022/papers/Qin_Geometric_Transformer_for_Fast_and_Robust_Point_Cloud_Registration_CVPR_2022_paper.pdf): established cross-cloud geometric feature consistency.
- [KISS-Matcher paper](https://arxiv.org/abs/2409.15615) and
  [official implementation](https://github.com/MIT-SPARK/KISS-Matcher):
  established global geometric matching comparator.

This is a focused source screen, not exhaustive novelty clearance. No new
GPU mechanism, training, production edit or Git sync occurred in this memo.
