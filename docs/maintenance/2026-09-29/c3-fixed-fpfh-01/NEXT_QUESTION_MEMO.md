# After C3: where to look next (discussion, not a frozen experiment)

C3 rejects one fixed anchor-only FPFH information comparator. It does not
identify a cause for F2's missing hard08 candidates. The next research
question should concern **candidate creation with cross-scan context**, not
another local descriptor radius or an immediate encoder replacement.

The literature has encountered low-overlap, repetitive or locally
ambiguous point clouds. [PREDATOR (CVPR 2021)](https://openaccess.thecvf.com/content/CVPR2021/papers/Huang_Predator_Registration_of_3D_Point_Clouds_With_Low_Overlap_CVPR_2021_paper.pdf)
uses cross-cloud attention and overlap-aware/salient point emphasis.
[GeoTransformer (CVPR 2022)](https://openaccess.thecvf.com/content/CVPR2022/papers/Qin_Geometric_Transformer_for_Fast_and_Robust_Point_Cloud_Registration_CVPR_2022_paper.pdf)
uses rigid-invariant pairwise distances and triplet angles for geometric
context before correspondence estimation. These are primary examples of
solutions to similar ambiguity, **not** evidence that either mechanism is
novel or effective inside frozen RAP. [SpinNet (CVPR 2021)](https://openaccess.thecvf.com/content/CVPR2021/papers/Ao_SpinNet_Learning_a_General_Surface_Descriptor_for_3D_Point_Cloud_Registration_CVPR_2021_paper.pdf)
focuses on local invariant feature learning; C3 gives no reason to replace
RAP's existing miniSpinNet simply with another local descriptor.

One useful next diagnostic would isolate the role of RAP's four temporal
support parts in **creating** the anchor pose candidates, while keeping the
two anchors, exact noise and model fixed. Unlike C2's all-part destructive
shuffle, an anchor-versus-support feature intervention could localize which
context the model uses. Before any execution, choose fixed observed pairs,
define the intervention's null/control and a candidate-level effect margin,
freeze a validator and seal outputs before GT. A result would remain a
model-use mechanism finding, not a registration gain. A separate constructive
method and fresh confirmation would still be needed for a thesis innovation
claim. This is a proposal only; no C4 protocol, data or inference exists.

Do not infer from C1/C2/C3 that an overlap head, geometric transformer,
support-part perturbation, training or top-k matching will improve RAP-SLAM.
The master's-thesis contribution should continue to separate the measured
E0 system engineering transfer from unproven research mechanisms.
