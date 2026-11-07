# Learned measurement readout: source/design audit only

Status: **DESIGN_ONLY**, not a training protocol or an experiment. Source and
filesystem metadata were inspected after PFG1's negative system result. No new
model inference, token extraction, label computation, learning or checkpoint
edit occurred. SOURCE_AUDIT records five source hashes and directory counts.

## Concrete overlooked interface

The local12-layer PointCloudDiT keeps512-dimensional per-input-row embeddings
after within-part and global attention. `return_transformer_features=True`
already exposes these before the final velocity MLP maps them to3 dimensions.
The sampler exports the last flow-call embeddings. With native five-step Euler
integration this is the input to the last integration step (nominal t=.2), not
an extra t=0 evaluation or the final clean coordinates. Exact runtime row/order,
RNG and native-output invariance still need a frozen extraction preflight.

C1 tested32-D local miniSpinNet descriptors. RAD1 tested final generated3-D
coordinates. Neither is a test of learning original-point correspondences from
these joint512-D embeddings. This is an untested source/interface, not evidence
that the tokens contain useful cross-view identity. The frozen transformer
contains no physical point-identity supervision guarantee; tokens can encode
anchor role, noise, coordinates and scene-specific shortcuts instead.

A candidate small readout would produce new measured-point correspondences,
then fit a pose on original measured points. It would not rank a sealed set of
failed poses. This distinction does not lift HL2's old support-selector stop,
RAD1's stopped decoder or the no-training boundary. A new supervised task,
data exposure and controls require a separate explicit scope.

## Practical sources and limits

Local KITTI00-10 scan directories, GT/calibration/timestamp file presence were
listed. Counts00/05/06/07/08/09/10=4541/2761/1101/1101/4071/1591/1201.
Presence/counts do not validate payloads, timestamps, labels or eligible pair
population. No image_2 directory exists in these observed sequence roots.
No MulRan/NCLT directory appears in the observed top-level dataset inventory;
other archives are uninspected, so this is not a claim that no copy can exist.
The local RAP checkpoint's pretraining membership remains unknown. Current
KITTI outcomes are historically exposed and are not new independent evidence.

Learned feature/correspondence pruning already has strong
[PointDSC prior art](https://openaccess.thecvf.com/content/CVPR2021/html/Bai_PointDSC_Robust_Point_Cloud_Registration_Using_Deep_Spatial_Consistency_CVPR_2021_paper.html).
Generative matching and virtual correspondences also have close
[Diff-Reg v2](https://arxiv.org/html/2503.04127v1) and
[VCR-Net](https://arxiv.org/abs/2011.14579) precedents. The
[RAP paper](https://arxiv.org/abs/2512.01850) supplies the joint generative
backbone. A small MLP on tokens is not automatically original. Novelty would
need a specific generative-readout construction and demonstrated information
beyond matched direct features and local encoding, with actual system benefit.

## Metric-first admission

Do not start training just because a source hook exists. Same-endpoint joint
GT replacement already gives limited ter opportunity. PFG1 now shows changing
directional geometry at those endpoints does not meet ter/ATE gates. First
complete the missing fixed-budget retrieval/measurement-placement opportunity
audit in PFG1 NEXT_ROUND_PLAN. It determines whether a better matching head on
the existing proposal distribution can plausibly address the target metrics,
or whether distinct coverage/local-motion information is required.

Only after a defensible system opportunity should a training annex select
dataset roles, physical query/site leakage rules, label quality/ambiguity,
architecture/loss/budget and independent confirmation before new outcomes.
Candidate controls: identical learned head/labels/solver on direct32-D
descriptors; matched local condition encodings without global generation;
row-destroyed joint tokens; native RAP. Compare original-point selected poses,
ordinary/confuser safety and complete online attempts, not descriptor recall
alone. Learned readout must beat the trained non-RAP control, not merely an
untrained descriptor matcher. A model-blind extraction preflight precedes
training. No head is implemented or trained in this turn.
