# C1: fixed KITTI descriptor-information audit

Frozen before descriptor generation. C0 found the miniSpinNet checkpoint
loads completely; C1 asks whether its actual F2 input features distinguish
cross-visit KITTI anchor points. This is an information diagnostic, not a
RAP output, registration score, method selection, or independent test.

## Inputs and separation

Use the exact saved-order F2 observed-development KITTI00 and08 cohorts,
100 pairs each, including 25 pairs per original stratum. No replacements,
new data, new inference, training, parameter search or production edit.
Regenerate all six F2 corrected scans with the unchanged >=1.5m KITTI
filter, 0.205deg vertical correction, voxel0.4, outlier20/2.5, cap
[2000,1000,1000,2000,1000,1000], fixed preprocessing seed42 and frozen
miniSpinNet. Instantiate the same backend preprocessing method without
its unused flow model; load miniSpinNet with safe `weights_only=True` and
`strict=True`. Assert every 8000-point concatenation, counts, normalized
condition, centers and scale exactly equals the original F2 inputs.npz.
Save each part's 32-D features, feature norms and source identities. Assert
all values finite and every point norm>1e-8, so no partial all-zero fallback.
The runner must not load GT or parse evaluator decisions. Hash-freeze this
protocol, runner, separate validator, model/feature/preprocessing sources,
weight files, exact F2 inputs, all 796 referenced raw scans and evaluator
GT/label identities before generating descriptors. Seal the full feature
bank by SHA256 before evaluator-only analysis.

## Fixed evaluator

The target anchor is part0 (KITTI frame i), source anchor part3 (frame j).
Use the same pose convention as F2, T_ij=inv(GT_i)@GT_j, to map source
points into target coordinates. For each source point, define geometric
eligibility if its nearest target point is <=1.0m under T_ij. Use
`scipy.spatial.cKDTree` in float64. Normalize each descriptor independently
to unit L2 and take the target descriptor with smallest Euclidean distance
(lowest index if an exact tie). A top-1 match is correct if that target
point is <=1.0m from the transformed source point. Report separately the
eligible fraction of all 2000 source points, and the fraction of eligible
points with correct top-1 match. Pairs with zero eligible points have null
conditional recall, not zero. Also report unconditional correct top-1
fraction over all 2000 source points.

Control: 16 fixed target-descriptor-to-coordinate permutations per pair.
For control k, seed SHA256(`C1|pair|k`) converted to a uint64 and use
NumPy PCG64 permutation. Keep the same descriptor nearest-neighbor
indices and permute only the target coordinate association. Thus the
descriptor distribution and geometry are identical while point-feature
assignment is broken. Report each pair's mean control recall across16
permutations, paired true-minus-control difference, and full pair-level
results. Do not optimize a descriptor threshold or radius.

Stratify by 00/08, F2 confuser/ambiguous/low-overlap/ordinary, and native
N K4 oracle candidate availability as determined by evaluator-only GT.
For the primary 08 positives lacking a strict N K4 candidate, report
pair-level median and mean conditional recall, median/mean shuffled
control, median/mean paired difference, median eligibility and eligible
pair count. Show the same summaries for 00 unavailable and both available
groups. The pair is the analysis unit; points within a scan are not
independent samples. No cross-sequence pooling or point-level p-values.

Prospective interpretation: `FEATURE_INFORMATION_PRESENT` only if at
least20 of the41 known 08 native-unavailable positive pairs each have
>=10% eligible source points and the median true-minus-control
conditional recall across those adequately covered pairs is >=0.10.
If fewer than20 qualify, `INCONCLUSIVE_CORRESPONDENCE_SUPPORT`; otherwise
failure is `NO_FEATURE_INFORMATION_SIGNAL`. This is an exploratory
information margin, not a significance test. A positive result permits
only a separately frozen model-use intervention; a negative result
motivates an input/domain audit. Neither licenses training, a default
change, or a thesis performance claim.

## Engineering and validation

Caps: <=30min bank wall, <=12GiB peak allocated GPU memory, <=1GiB new
artifacts. Preserve request-local RNG and precision state. On any partial
bank leave INCOMPLETE and do not analyze. Independent validator rehashes
freeze, bank and source, checks all200 feature artifacts and exact F2
point identities, independently recomputes the correspondence metrics on
the full200 pairs and16 controls, verifies group arithmetic and decision.
No rerun/overwrite of completed earlier experiments or Git sync.
