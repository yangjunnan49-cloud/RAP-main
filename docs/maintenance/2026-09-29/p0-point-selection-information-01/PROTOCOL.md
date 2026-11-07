# P0 full point-selection information audit

Frozen before full-pair output. Use all 200 exact saved-order F2
observed-development pairs: 100 KITTI 00 and 100 KITTI 08. P0-02 passed
its fixed four-pair engineering preflight; its code supplies the exact
0.25 m voxel, outlier, fixed-count batched FPS, full pre-outlier voxel
miniSpinNet support, 5 m radius and scoped per-pair NumPy seed. The six
counts remain `[2000,1000,1000,2000,1000,1000]`, equal to F2's 8,000
input points. This is fixed-count upstream-inspired input, not the RAP
paper's adaptive allocation. The F2 points and C1 features are the paired
control and stay immutable. No RAP generation, gate, training or default
change occurs.

## Bank and separation

Before any new output, hash-freeze this protocol, runner, independent
validator, P0-02 source and validation, relevant RAP/miniSpinNet sources,
checkpoint, all 200 F2 inputs, all 200 C1 feature artifacts, 796 referenced
corrected raw scan identities, evaluator-only GT and F2 label files and C1
pair metrics. The bank runner can hash GT/label files but cannot parse
them. Generate and SHA-seal the complete 200-pair P0 points/features and
per-part support counts first. No partial bank can be evaluated. Keep
`INCOMPLETE` on failure. Caps: 30 minutes bank wall, 12 GiB peak allocated
GPU memory, 1 GiB new point/feature artifacts. Stop on shortage, bad
feature, source mismatch or resource excess without replacing pairs.

## Fixed evaluator

Only after the full bank seal, use F2's GT relative transform
`inv(GT_i) @ GT_j` to map source part 3 to target part 0. For each arm,
the 2,000 source anchors are geometrically eligible if their nearest
target anchor lies within 1.0 m. L2-normalize descriptors and choose
Euclidean top-1 target descriptor (lowest index on an exact tie). Correct
means selected target point lies within 1.0 m of the transformed source.
Conditional recall is correct/eligible; zero eligible gives null. Report
eligible fraction and unconditional correct fraction separately. The
control is C1's same 16 target-descriptor-to-coordinate permutations:
PCG64 seed from the first eight bytes of SHA256(`C1|pair|k`), preserving
the descriptor nearest-neighbour indices. Pair information equals true
conditional recall minus mean shuffled-control recall. Check recomputed
F2/C1 metrics against its sealed `pairs.json` within 1e-12.

The primary fixed group is the 41 KITTI 08 positive pairs with no strict
native F2 N/K4 candidate. Common adequacy requires both arms to have
at least 10% eligible source anchors. Material information signal requires
at least 20 common-adequate pairs, median pairwise
`P0_information - F2_information` >=0.10 (10 percentage points) and at
least two thirds of those pairwise differences strictly positive. If
fewer than 20 pairs qualify, decide `INCONCLUSIVE_COMMON_SUPPORT`.
For safety, each sequence's 25 ordinary pairs must have at least 20 with
nonzero eligibility in both arms, and median P0 minus F2 information on
that common set must be >=-0.05. Insufficient ordinary support is also
inconclusive. Otherwise a failed gain or guard is
`NO_MATERIAL_INFORMATION_SIGNAL`; passing all is
`MATERIAL_INFORMATION_SIGNAL`. No threshold is tuned to the outputs.

Report for 00 and 08, native-K4 available/unavailable and each F2 stratum:
pair count, both-arm eligible fractions, adequate counts, conditional
recall/control/information medians, and paired information/coverage changes.
Report the 41 hard08 primary pairs, common-adequate subset, positive-sign
count and ordinary guards explicitly. These are pair-level observed-
development diagnostics, not significance tests or pose/loop recall.

## Validation and interpretation

The separate validator rehashes freeze and full bank, checks every point,
feature and source identity and all pair metrics/controls, independently
recomputes cohort arithmetic and decision, and exactly regenerates the
first two preflight pairs per sequence using the frozen P0-02 path. Only a
material information signal licenses designing a separately frozen RAP
generation comparison with unchanged K4 noise, weights, steps, selector
and gate. A negative result retires this exact input convention without a
voxel, seed, radius, count or gate sweep. P0 jointly changes voxel size,
keypoints and descriptor support, so it cannot identify a single cause.
No evaluator GT access before the bank seal, paper-number comparison,
manuscript claim, production edit or Git sync.
