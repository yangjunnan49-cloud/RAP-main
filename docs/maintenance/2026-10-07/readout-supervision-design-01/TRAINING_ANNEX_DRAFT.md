# RLP1 proposed scope: frozen RAP, small measured-point readout

**REVIEWABLE DRAFT, NOT AUTHORIZED OR EXPERIMENT-FROZEN.** The proposed next
authorization is for an isolated exploratory readout pilot, including its
mandatory engineering/weak-label preflight and one fixed-budget three-arm fit.
RAP and miniSpin weights remain frozen; no fine-tuning/retraining of either.
No production/default/manuscript change, acquisition/install or Git sync.
No head, labels, independent-context bank or training code exists today.
Implement and freeze runner/algorithm/validator/source/roles/settings before
any new outputs. Do not silently promote this design annex to an executed study.

## Question and measured output

Does a small common readout recover original measured-point correspondences
and coupled local SE3 from joint flow tokens better than equally trained direct
features and a cross-view-separated frozen-network control? It creates a new
measurement on the original points; it does not rank old failed poses or decode
final generated3-D coordinates. Generic feature matching/pose fitting has strong
prior art. The proposed contribution is an experimentally conditional use of
joint generative representation for local measured motion, not "512 dimensions"
or a generic MLP by itself.
[SuperGlue, unmatched assignments](https://arxiv.org/abs/1911.11763),
[GeoTransformer, contextual registration](https://arxiv.org/abs/2202.06688).

## Data / non-leakage / fixed opportunity

Use DATA_ROLES and the exact204-window draft, prospectively finalized in the
new experiment freeze.144 fitting windows00-05,12 development06,48 evaluation
07-10. No errors/overlap/GT motions choose the indices. Preserve1000 native
processed points per scan,32-D descriptors, original preprocess and shared
native normalization. No density/step/timestep/window/noise search. Every
window retains original three scans; all pairs(0,1),(0,2),(1,2) train the same
head. Primary measured motion is source scan1 to target scan0.

Use the original LMF1 seed rule for every window: first4 bytes of
SHA256('LMF1|sequence|t') interpreted little-endian. Draw one native3000x3 noise
tensor/window with that seed; same measured inputs/noise in all token arms.
There is no new noise selection or rescue of an old pose/response arm.
All old sealed inputs remain untouched.
No spatial/chronological site independence or checkpoint exclusion is assumed.
The new head holds out07-10 sequences from its fit, but these sequences have
historical native/diagnostic exposure. This is exploratory transfer only.

## Mandatory prerequisite, before fitting anything

Prepare a separately frozen four-window preflight at the same count-selected
TR0 rows00/05/06/07,t200. J must exactly reproduce their sealed native raw/state/
pose/token outputs. I uses the controlled grouping below, repeats exactly and
keeps all measured-input/noise/role bindings. Independently reconstruct both
groupings, all five flow inputs/times, row metadata, native RNG vector draws
and Horn poses. Confirm a perturbation in another scan cannot affect I's
unperturbed scan outputs/tokens: add1 to the third part's initial noise only,
hold conditions/descriptors/scale/roles fixed, and check parts0/1 exactly.
Independently test this only as a disclosed
engineering control, never a confidence/accuracy signal. No model edits.

Seal the complete GT-free inputs/token bank and validate source bindings before
reading new pose labels for that stage. Then a separate weak-label preflight
checks camera/LiDAR conversion, direction, counts, nearest-set masks, third-
view support and original-point solver on synthetic exact/ambiguous/dynamic/
unmatched/rank1/planar controls plus the four fixed real windows. Brute-force
geometry and independent quaternion reconstruction validate the runner, not
the physical correctness of supplied GT. Do not call synthetic dynamic controls
real dynamic annotations. At least20 supported positive rows in each direction
of each of the three scan pairs/window; otherwise stop before fitting. No window
replacement, threshold/density/seed rescue. Do not infer calibrated label noise.

## Exact three-arm construction to freeze

J: native five-step joint three-part batch; last-call t=.2 float32 tokens.

I: same tensor rows,cond,features,initial noise,scale and anchor mask, but three
one-part examples: points_per_part=[[1000],[1000],[1000]], batch cuts
[0,1000,2000,3000], scales=[s,s,s]. Part cuts stay identical. Anchor bits retain
original roles; do not make all parts anchors or renormalize separately.
Embedding expands the same scale per row; every adaptive-LN timestep equals
the original t. Part attention/pointwise operations and per-part rigidification
retain the original point sets, while global attention cannot cross scans.
All five I integration states are generated under this separated grouping,
not a final masked pass on J's already jointly conditioned state. The sampler
preparation draws one unused length3 CUDA vector versus J's length1; verify
the actual source-defined RNG transition, not three separate draws. No extra
t0 call. Source supports this grouping; runtime feasibility is not yet tested.
I is a causal context-removal ablation and may be outside the pretrained
one-part distribution, not a competitive optimized standalone odometry method.
Its runtime independence must pass; its empirical weakness alone does not
establish generalizable generative originality. J/I both process3000 rows/five
flow calls, but their attention work differs and total cost must be reported.

D: native32-D descriptors, not an untrained nearest-feature matcher. All arms
also receive identical common measured inputs: normalized conditionxyz3,
original noisexyz3,anchorbit1,log(scale)1 and nominal lastt1. Never give D/I J's
generated coordinates, native pose, match labels or final joint flow input.

Normalize D's32 feature values or I/J's512 values to row unit norm (epsilon1e-8),
zero-pad D feature channel to512 and concatenate common9 channels. No GT/PCA
projection fit. Same trainable521->128 SiLU->64 unit-normalized projector and
128->1 overlap logit, plus scalar dustbin logit. Nominal75202 parameters in
each arm; D has61440 structurally inactive first-layer weights from padding,
so its effective parameter count13762 differs. Report this, do not claim equal
effective capacity. I and J have identical dimensions/active head capacity,
which is the primary test of joint context. No head cross-attention or additional
learned backbone; I/J backbone stays eval/no_grad with original weight hashes.

## Weak correspondence labels, ambiguity and motion

Let C be LiDAR->camera calibration and G_i be camera-to-world pose. LiDAR
sourceb->targeta relative T_ab=C^-1 G_a^-1 G_b C. Use general inverse for
rounded serialized matrices, keep official values, and make no physical GT repair.
Convert observed points using the original KITTI205 convention, disclosed.
For this new exploratory readout's angular metric/motion loss only, map the
rounded GT rotation to its nearest proper SO3 via polar SVD; keep its original
translation and store both raw transform and numerical mapping. Independently
validate this convention on rounded/identity/reflection fixtures. Do not rewrite
official GT files, old local metrics or the native-system evaluator. This is
a declared new readout scoring convention, not evidence that GT is physically
more accurate or that historical measurements should change.

For each pair/direction use all retained original points: GT-transported distance
<=.30m forms a set of admissible positive rows, not one hard nearest point.
A row must also have a point within.60m in the third scan under the same GT
reference to be supervised. If pair minimum>=.60m and third-view support holds,
use the unmatched dustbin. Ignore .30-.60m, no third-view support, or nonfinite
inputs; never force them into matches. Multiple positives remain a set; no
error-based sample exclusion. These are processed-resolution weak geometric
labels, not identified raw returns or verified static/dynamic point identity.
Third-view support can be consistently wrong; the blind spot is retained.

Scores are normalized embedding dot products/temperature.10. Row and reverse
column softmax each include a dustbin with scalar alpha minus the row overlap
logit. Set-positive loss=-log(total probability on admissible rows); unmatched
loss=-log(dustbin probability), symmetric over directions and three pairs.
Average positive and unmatched class terms separately when present, then
average their present terms, so nonoverlap abundance cannot dominate. Ignore
rows contribute no loss. Log all class/ignored counts and supervision coverage.

After100 correspondence-only warmup updates, use loss=L_corr+.05 L_motion.
For motion, W_ij=p_row(i,j)*p_reverse(j,i)*sigmoid(overlap_i)*sigmoid(overlap_j).
Weighted proper SVD fits original source points to target points using every
W_ij, paired centroids and the same R,t. Huber(delta1) translation residual
scaled by.20m and Frobenius rotation residual scaled by sqrt(2)*.2deg in
radians provide a weak coupled SE3 loss, averaged over three pairs. Guard the
proper-rotation Horn top-eigenvalue relative gap>1e-6 and positive finite mass;
skip only this auxiliary motion term on a degenerate soft fit, report counts.
No regularizing pseudo-correspondences or identity pose replacement. Synthetic
gradient/rigid-unique checks must pass before fitting; nonfinite loss/gradient
stops and preserves the run. Pose supervision is weak because local GT noise
is unresolved; it does not claim sub-centimetre physical accuracy.

## Fixed fitting / pose inference / resource scope

Fit D,I,J independently with the same initialized head for each seed
20261007/20261008/20261009. AdamW,lr1e-3,weight_decay1e-4,1000 updates,
batch1 window, gradient clip1. Cyclic hash-shuffled fitting-window order fixed
per seed. No GT augmentation, noise regeneration, LR/architecture/epoch search,
validation-based early stopping or best-seed/epoch selection. Final1000-step
checkpoint is the only evaluated checkpoint. Development06 is diagnostic and
does not choose settings. Backbone/descriptor checksums unchanged after fit.

At inference, keep mutual row/column argmax real matches only when each side
probability>=.05, discard dustbin winners, weight by W. Require>=20 matches;
fit original points by proper SVD, perform two fixed.60m residual trims/refits,
and require relative proper-objective eigen gap>1e-6 each time. No native pose
initialization, GT gate or candidate ranking. Same solver in all three arms.
Any missing/invalid output remains a failure in the full denominator. Primary
pilot comparison needs complete valid48-window outputs in all arms; otherwise
report COVERAGE_INCONCLUSIVE rather than remove windows or rescue parameters.

Precompute one float32 I/J bank shared by all fits; measured inputs/descriptors
cache shared. Raw token arrays204*2*3000*512*4=2506752000 bytes before compression;
new study artifacts cap4GiB, RSS4GiB, allocated GPU3GiB. Extraction stage<=20min,
each1000-update fit<=5min, all compute stages combined<=60min. Include neural/
descriptor/readout/solver/validation work and rejected outputs; equal row count
is not equal attention work. No cache quantization or density reduction to meet
a failed cap. Stop on cap/source/control/label/numerical failure, preserve files
and freeze; any repair requires a disclosed separately frozen amendment.

For full RLP1 label generation, complete204 GT-free bank/source seal precedes
its labels. The earlier four-window weak-label preflight is separately sealed
and disclosed as label exposure; its outcomes cannot change this manifest or
the fitting/scoring settings. Supervised full labels then
freeze/seal separately; only144 fit labels can enter gradient updates. Export
all final48-window predictions before evaluator error computation. Independent
validator checks labels/solver/weights/splits/counts and all metrics, using
Horn/brute force rather than runner copies. Preflight4windows can overlap draft
fit/development/evaluation only as disclosed engineering exposure; no preflight
GT/model error selects the final204 indices.

## Frozen proposed gates and permitted conclusions

Use per-window median prediction error across the three fixed seeds, never
best seed; seeds do not create144 independent evaluation cases. Report all
seed-level errors. For J vs both I and D on all48 primary windows, require:
median paired translation gain>=.005m AND median J translation<=90% control;
median paired rotation gain>=.01deg AND median J rotation<=90% control; at least
60% positive signs for each quantity/control. Each07/08/09/10 mean regression
<=.005m translation and<=.02deg rotation. All conjunctions prospectively frozen.
These are exploratory engineering gates, not calibrated significance tests.

System readiness additionally needs J to beat the same1000-point geometric
G3 control (paired translation>=.005m,rotation>=.01deg), and the saved KISS
motion at the same endpoints on07/09/10 (36 windows) in both translation and
rotation: paired median gains>=.002m/ .005deg and cohort medians<=90% KISS.
KISS uses a denser map; report work, do not call it density-matched.06 KISS is
diagnostic. No saved full08 KISS source is established, so make no08 KISS claim
or new KISS run in this pilot. Native R3 is a disclosed negative reference.

If J beats I/D but not KISS/G3, record a readout signal without a useful local
motion gain and do not advance to trajectory. If the joint-context gates fail,
stop this fixed construction, no feature/time/noise/window/gate rescue. If all
pass, a new separately frozen native-system protocol is still required; no
trajectory/default promotion is included in this authorization. It must test
full-system ter AND aligned ATE, rotation/sequence safety and total inference
cost, preserve old loop comparisons and account for GT-free rejects. Local
feature gains cannot be reported as measured system gains or thesis originality.
