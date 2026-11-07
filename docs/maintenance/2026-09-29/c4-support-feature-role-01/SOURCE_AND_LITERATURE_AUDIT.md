# C4 follow-up: existing context path and relevant prior art

Read-only audit after the sealed C4 result. No model modification,
inference, training or method selection occurred here.

## What the current RAP model already does

- F2's six ordered parts are `[i, i_support1, i_support2, j,
  j_support1, j_support2]`; pair pose decoding uses per-part fitted poses
  for parts0 and3. `rap_slam/structured_motion.py:7` builds one batch from
  all six point and feature arrays.
- `rectified_point_flow/flow_model/embedding.py:174` concatenates each
  32-D miniSpinNet feature with coordinate, current noisy coordinate and
  scale encodings, then projects to the transformer width. This is a
  direct input channel, consistent with C2's response.
- `rectified_point_flow/flow_model/layer.py:179-187` gives each of
  the12 DiT layers **part-wise attention** followed by **global attention
  across all parts**. Thus “add cross-part attention” by itself duplicates
  a capability already present. C4's support feature-to-pose responses are
  consistent with this existing mixing path; C4 does not localize which
  attention heads or layers caused them.
- `rap_slam/rap_backend.py:184` selects the largest part as the primary
  reference (`np.argmax(counts)`), which is part0 when parts0 and3 both
  contain2000 points. `rap_slam/structured_motion.py:12` marks only that
  primary part in `anchor_indices`. `point_cloud_dit.py:137` adds a learned
  binary reference/nonreference embedding. Accordingly part3, the
  **pairwise source anchor for evaluation**, shares the nonreference
  embedding class with four temporal supports. This is an interface fact,
  not proof that the model cannot distinguish those parts from geometry,
  point counts or attention. Any new source-anchor role encoding would
  require a separate adaptation question and matched control.
- The current flow model does not explicitly compute a cross-visit
  overlap probability or rigid-invariant pair/triplet relation before
  attention. That is a source observation, not evidence that adding
  either is necessary or sufficient. The geometric acceptance gate is
  downstream of generated poses.

## How others address related failures

[PREDATOR (CVPR2021)](https://openaccess.thecvf.com/content/CVPR2021/papers/Huang_Predator_Registration_of_3D_Point_Clouds_With_Low_Overlap_CVPR_2021_paper.pdf)
focuses cross-cloud attention and sampling on overlap and salient regions
to address low overlap. [GeoTransformer (CVPR2022)](https://openaccess.thecvf.com/content/CVPR2022/papers/Qin_Geometric_Transformer_for_Fast_and_Robust_Point_Cloud_Registration_CVPR_2022_paper.pdf)
uses rigid-invariant distance/angle relationships for correspondence
context. [SpinNet (CVPR2021)](https://openaccess.thecvf.com/content/CVPR2021/papers/Ao_SpinNet_Learning_a_General_Surface_Descriptor_for_3D_Point_Cloud_Registration_CVPR_2021_paper.pdf)
addresses local descriptor invariance. These are published solutions to
related registration problems; a plain overlap head, geometric attention
or new local descriptor is not a novel RAP-SLAM contribution by itself.

## Boundary for a constructive successor

C4's ordinary support-feature intervention changed flow but not material
pair pose, while several hard pairs changed pose and four00 positives
crossed strict labels with three losses. This favors a question about
**which context is reliable for hard candidate creation**, but supplies
no usable policy. A successor needs an explicit, GT-blind transformation
of available information, a same-point/noise/compute comparator, frozen
00/08 development safety and gain margins, and fresh confirmation if it
passes. It must explain what is different from published overlap and
geometric-context matching and from RAP's existing global attention.
No C5 protocol or training exists.
