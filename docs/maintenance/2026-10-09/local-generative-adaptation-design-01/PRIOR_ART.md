# Bounded primary-source comparison

Accessed: 2026-10-09. This is a targeted mechanism review, not exhaustive
novelty clearance and not proof of universal non-originality. No external
implementation, checkpoint, dataset or dependency was acquired/reproduced.

| Primary source | Relevant established mechanism | Consequence for the current draft |
|---|---|---|
| [RAP v2](https://arxiv.org/html/2512.01850v2), sections3.2/3.3 andB.3 | Conditional point-velocity learning, per-view rigidity feedback with original noise, generated-position pose recovery | The native output contract, rigid sampling and ordinary flow objective are existing RAP. |
| [RPF v2](https://arxiv.org/html/2506.05282v2), sections3.2/3.3 | Euclidean point flow, conditional velocity loss and per-part pose recovery | Point generation with known within-part row binding is not a new correspondence mechanism. |
| [RPF authors' training instructions](https://github.com/GradientSpaces/Rectified-Point-Flow#training-and-finetuning) | Explicit checkpoint-based flow-model fine-tuning | Adaptation from pretrained generative weights is already an offered workflow. |
| [LoRA](https://arxiv.org/abs/2106.09685) | Frozen pretrained weights plus trainable low-rank updates | Low-rank modules are an implementation choice, not the new registration contribution. The paper is not a guarantee of LiDAR effectiveness or memory. |
| [DiffusionReg authors](https://github.com/Jiang-HB/DiffusionReg), [NeurIPS2023 paper](https://papers.nips.cc/paper_files/paper/2023/file/43069caa6776eac8bca4bfd74d4a476d-Paper-Conference.pdf) | Generative registration on SE3 with progressive pose denoising | Moving the learning target into rigid motion does not by itself establish a new generative-registration idea. Object-pose results do not establish our local-LiDAR accuracy. |
| [DiffLO, CVPR2025](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_DiffLO_Semantic-Aware_LiDAR_Odometry_with_Diffusion-Based_Refinement_CVPR_2025_paper.html) | Semantic distillation and diffusion-based pose refinement for LiDAR odometry | Generative local odometry and semantic conditioning have direct task-level prior art. We make no reproduction or performance-equivalence claim. |
| [Diff-Reg v2](https://arxiv.org/html/2503.04127v1) | Diffusion in matching-matrix space and rigid-pose fitting from weights | A new matching head or matching-space generation does not reopen the stopped RLP2/RAD1 construction as original work. |
| [Viewpoint-Aware ICP authors](https://github.com/HMCL-UNIST/ViewpointAwareICP/blob/main/README.md) | Visibility scoring in coarse/fine point-cloud registration for loop closure | Visibility/free-space suggestions need a precise new mechanism and sensor contract; visibility scoring itself cannot be claimed new. |

The bounded review did not locate a direct publication with the exact proposed
LoRA block selection and auxiliary relative-pose loss. Absence of that exact
configuration is not affirmative evidence of an original algorithm.

The current G-versus-F contrast tests a supervised objective change. It does
not identify a new independent observation source, prove physical alias
correctness, or isolate joint generative context as the cause of improvement.
Therefore the present draft does not meet the owner's originality admission
condition. Empirical engineering usefulness would still need the full controls
and practical safety conjunction, and would remain a separate claim.

Prior stops were checked against the preserved local reports/plans: native
R3/LMF1, shared-identity D1, final-raw decoder RAD1, directional FDI, geometric
shape PFG1, retrieval placement LC0 and weak/frozen readouts RLP1/RLP2. None is
reopened through a new label or incidental implementation change.
