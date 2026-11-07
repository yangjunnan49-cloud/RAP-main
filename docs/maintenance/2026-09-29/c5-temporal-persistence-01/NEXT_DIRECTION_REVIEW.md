# After C5: candidate-creation direction review

This is a read-only synthesis, not C6 protocol or novelty clearance.

The measurable problem remains absent correct native K4 candidates on
41/75 hard08 positives in F2. C1 found weak miniSpinNet top-1 anchor
information there; C2 showed RAP uses those features; C3's fixed FPFH
alternative was weaker; C4 isolated heterogeneous support-feature effects;
C5's GT-blind same-visit persistence mask recovered0/6 fixed hard08
positives and caused one00 loss. G0/G1 external global matchers, V0 fixed
sensor-ray search, D0 saved transient poses, S1 ten steps and R0 local ICP
also did not recover a safe, prospective mechanism. Repeating descriptor
radius, support mask, step count or post-hoc score searches is unsupported.

Published work already treats related problems. [PREDATOR](https://openaccess.thecvf.com/content/CVPR2021/papers/Huang_Predator_Registration_of_3D_Point_Clouds_With_Low_Overlap_CVPR_2021_paper.pdf)
targets low-overlap regions; [GeoTransformer](https://openaccess.thecvf.com/content/CVPR2022/papers/Qin_Geometric_Transformer_for_Fast_and_Robust_Point_Cloud_Registration_CVPR_2022_paper.pdf)
uses rigid-invariant geometric relations; [Rectified Point Flow](https://proceedings.neurips.cc/paper_files/paper/2025/file/f72599679c20c6e59878c075706132f1-Paper-Conference.pdf)
already generates multi-part registered clouds with local feature and
global-attention conditioning. Recent [Source-Guided Flow Matching](https://proceedings.iclr.cc/paper_files/paper/2026/hash/adedc33539eafdf3d2c14a5e0032db6e-Abstract-Conference.html)
changes a flow model's source distribution without retraining; this is
a general generative-model analogy, not a point-registration result or
an originality claim for RAP-SLAM.

A next research proposal should state how it creates poses the native
sampler misses, why its input signal is available without GT, what is
different from those published approaches and RAP's existing multi-part
attention, and which matched comparator would falsify it. The F2
positive-metric system reference remains E0 arm A's engineering transfer;
no recent feature/context intervention establishes an algorithmic gain.
Until a distinct mechanism meets those requirements, do not spend GPU
time on another local parameter variant or write a stronger thesis claim.
