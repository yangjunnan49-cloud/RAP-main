# RAP information path and domain-convention audit

Date: 2026-09-29. Status: **read-only source audit complete**. This is not a
registration experiment or a new efficacy result. The local identities and
limited checkpoint name check are in `source_identity_audit.json`; the script
is `scripts/maintenance/audit_rap_information_path.py`. No completed bank,
model, default, or Git state was changed.

## Question and evidence boundary

Trace what information the fixed F2 RAP-SLAM path actually supplies to RAP,
compare that path with the public RAP paper and local upstream demo, and
identify one testable input-convention difference. Separate source facts from
the paper's stated training recipe and from any causal explanation of F2.
The March 2026 [RAP v2 paper](https://arxiv.org/html/2512.01850v2) and
[official repository](https://github.com/PRBonn/RAP) were read on this date.
Those current descriptions cannot establish the training split, revision, or
intended preprocessing of the exact local 12-layer checkpoint.

## Information chain

| Stage | Local F2 path and prior evidence | Paper/upstream contrast and interpretation |
| --- | --- | --- |
| Pair and views | F2 freezes 00/08 observed-development pairs and six corrected scans per pair, split into three parts per visit. Corrected scans use the >=1.5 m range filter and +0.205 degree vertical correction. Temporal support is supplied as additional point-cloud parts; the model is not given the saved odometry motions as a separate condition. | The paper trains with varying view counts and assumes the inputs observe the same connected scene. Whether every F2 six-part set satisfies its training overlap-graph condition is not established by this audit. |
| Point selection | `rap_slam/rap_backend.py` voxel-downsamples at 0.4 m, removes statistical outliers, then samples a fixed per-scan cap with a seeded uniform random choice. F2 overrides the six caps to [2000,1000,1000,2000,1000,1000], totaling 8000. | Paper training KITTI scan/submap rows specify 0.25 m voxel size, coverage-proportional point counts and farthest-point sampling (FPS), with radius `20 * voxel_size` for MiniSpinNet patches. Local `demo.py` defaults to 0.25 m and FPS with adaptive allocation. Thus F2 is not a literal reproduction of the paper's point-selection convention. The difference is not a proven failure cause. |
| Local features | miniSpinNet extracts 32-D features after the F2 point cap, using those capped points as both keypoints and 5 m patch support. C0 safely loaded all 58 descriptor keys strictly; C1 found weak top-1 information on hard08 native-K4-unavailable positives; C2 showed the model responds to this channel. | Upstream `SampleProcessor` extracts features at FPS keypoints using the **pre-FPS voxel cloud** as patch support. The paper's KITTI 0.25 m voxel and `20 * voxel_size` imply the same 5 m metric radius, but a different support density and keypoint distribution. The paper says MiniSpinNet was pretrained on 3DMatch; that does not authenticate the local checkpoint's exact training history. |
| Canonicalization | The RAP-SLAM wrapper follows local `PointCloudDataset._transform` evaluation behavior: center the largest part, scale by `1.5 * max(abs(primary-centered coordinates))`, center each part, and use no evaluation-time random rotation. Earlier S0/C2 native outputs reproduced saved F2 generation exactly. | No mismatch was demonstrated at this stage. The paper's verbal normalization description is not a byte-level specification for this older local checkout. |
| Conditioning and flow | Local `PointCloudDiT` embeds normalized coordinates, the noisy state, scale and 32-D local descriptors; a learned embedding identifies anchor versus other points. Layers perform within-part and global attention; there is no distinct semantic tag for “temporal support”. C4 observed support-feature effects but no fixed-gate benefit. | The paper describes local-feature and coordinate conditioning with per-view/global attention. Existing C1/C2/C4 results refute an entirely absent feature channel but do not establish that it supplies reliable hard-loop information. |
| Weights and sampling | F2 uses `rap_model_12.ckpt`, 12-layer `rap_12` config, K4, rigidity forcing and five Euler steps. The checkpoint SHA-256 is `0c5b9f20ee4dfe2345c3cd47dd0632a3d807a3da69c7653900a755cd06564200`. | Paper v2 describes 10 attention blocks and 10 Euler steps. Local `demo.py` also defaults to 10 steps. S1 already tested 5→10 under fixed F2 inputs and failed its development gain/safety gates, so step count is not a pending rescue. A different model depth does not itself imply a broken checkpoint. |
| Decode and evaluation | F2 decodes rigid poses from generated endpoints, selects by raw rigidity among K4 and applies its common 4000-point geometric gate. F2 strict correctness is translation <=1 m and rotation <=5 degrees, on a deliberately difficult pair cohort. | The paper's KITTI pairwise table reports 555 pairs at translation <=2 m and rotation <=5 degrees. Its headline KITTI success cannot be directly compared with F2 strict recall or loop acceptance. |

Local source anchors: `E:/githouse/RAP-SLAM/rap_slam/rap_backend.py`,
`E:/githouse/RAP-SLAM/scripts/structured_motion_dev.py`,
`demo.py`, `dataset_process/extract_sample_features.py`,
`rectified_point_flow/data/dataset.py`,
`rectified_point_flow/flow_model/embedding.py`,
`rectified_point_flow/flow_model/point_cloud_dit.py`,
`config/model/flow_model/point_cloud_dit_12.yaml`, and
`config/RAP_inference.yaml`. Their hashes are sealed in the JSON record.

## Checkpoint and provenance limits

The local wrapper calls `load_checkpoint_for_module` without a strict override;
that utility defaults to `strict=False` and `weights_only=False`. Historical
F2/S0/C2 results show executable, exactly reproduced native trajectories,
but are not a strict key-and-shape proof. This audit did **not** execute
unrestricted deserialization. `torch.load(weights_only=True)` rejected the
checkpoint's OmegaConf `ListConfig`; no unrestricted fallback was used.
Instead, `zipfile` plus `pickletools` parsed serialized strings without
unpickling. All 344 state-dict names in a freshly instantiated local
12-layer model appear among checkpoint opcode strings, with layer indices
0–11. Serialized strings also include module paths, so this verifies name
presence only; it does not establish tensor values/shapes, strict loading,
training split, or provenance. The exact checkpoint identity matches the
F2-frozen SHA.

The [paper's data table](https://arxiv.org/html/2512.01850v2) includes KITTI
training examples and says KITTI 08–10 are excluded from its training set.
This applies to the reported paper recipe; the local 12-layer checkpoint's
membership is unresolved. The official repository still lists training
data curation code as unreleased. A public
[RAP issue](https://github.com/PRBonn/RAP/issues/2) reports poor registration
on one complex indoor scene despite success on other scenes; it contains no
verified remedy and is not evidence for the F2 cause.

## Decision and next bounded question

Decision: **INPUT_CONVENTION_DIFFERENCE_IDENTIFIED; CAUSE_UNTESTED**.
The most concrete unexplored boundary is keypoint construction and patch
support, before RAP generation. Do not change the backend default, promote
paper numbers as a baseline, or train an encoder based on this audit.

Next, prospectively freeze **one** matched point-selection information
preflight on the same F2 corrected scans and pair IDs. Compare F2's fixed
0.4 m/random-cap anchors with one explicit upstream-style 0.25 m/FPS
allocation, while holding the total point budget and 5 m MiniSpinNet radius
fixed or declaring any unavoidable inequality. Seal inputs and GT-blind
geometry/feature summaries before any evaluator labels. Measure source
coverage, patch support, cross-visit descriptor information and time/memory;
include unchanged F2 as the paired control and a separate validator. A
material information gain on hard08 missing-candidate positives would justify
a separately frozen RAP-generation test. It would not by itself establish a
new algorithmic contribution or authorize training. If it fails, stop this
exact convention route without a post-hoc voxel/FPS/point-count sweep.

E0 arm A's held-out-system improvement remains the positive engineering
transfer. All C/I and earlier negative stops and the manuscript pause persist.
