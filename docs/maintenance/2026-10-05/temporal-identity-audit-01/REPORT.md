# Bounded identity, calibration and temporal-control audit

Decision: **LOCAL_09_CONSISTENT_CROSS_VISIT_DISCREPANCY**. Independent validation passed. This closes the planned local audit; it does not resolve the physical truth of the cross-visit discrepancy.

The protocol and 415 identities were frozen before construction of a new GT-free bank. All 98 previous endpoints reproduce exactly. The bank contains 265 distinct 4,000-point scans (1,060,000 points) and 190 directed endpoint-to-offset controls at fixed -10/+10 frames. Positive offsets are diagnostic and noncausal. The bank was sealed before evaluator pose computation. No neural inference or graph optimization ran.

## What the checks establish

For all six saved E0 sequences, full absolute scan paths and consecutive filename indices agree with the source manifests. Their timestamps equal the complete available `times.txt` arrays and are strictly increasing. Scan, manifest and GT row counts agree. An independent reconstruction verifies the LiDAR convention `Tr^-1 * camera_pose * Tr`, relative transform direction, and every new geometric distance. Available-file inventory did not provide independent raw OXTS/trigger archives; actual sensor synchronization and archive provenance therefore remain unverified.

| Sequence | Local controls | Median absolute mean-distance difference, GT vs odom (m) | Median absolute overlap difference (pp) | Median pose translation disagreement (m) | Rotation (deg) |
|---|---:|---:|---:|---:|---:|
| 00 | 34 | 0.006875 | 0.1250 | 0.115897 | 0.101114 |
| 05 | 46 | 0.002806 | 0.0875 | 0.062637 | 0.086246 |
| 06 | 47 | 0.001353 | 0.0875 | 0.082679 | 0.045412 |
| 07 | 18 | 0.001794 | 0.1125 | 0.057562 | 0.122584 |
| 09 | 13 | 0.004655 | 0.0500 | 0.107995 | 0.115788 |
| 10 | 32 | 0.003721 | 0.1000 | 0.074308 | 0.140958 |

09 passes all four frozen local-agreement gates: distance <=0.10 m, overlap <=5 pp, translation <=0.20 m and rotation <=1 deg. Across the 12 earlier 09 revisit attempts, the median absolute z component divided by translation-error norm is 0.812687, passing the predeclared 0.80 directional flag. These components are in the reference endpoint's LiDAR axes; they are not a measurement of world vertical drift. There are nontrivial other components as well.

This narrows gross frame-index and calibration-convention explanations. Local agreement can coexist with accumulated GT drift, repeated-scene aliases, changing surfaces, or a common learned-model bias. It does not prove GT wrong, RAP/Geo physically correct, or the joint-GT oracle physically recoverable. Official strict labels, KITTI ter/rer and aligned ATE stay unchanged. The independent result on sequence 10 already demonstrates that geometric fit can favor a GT-far alias.

## Verification and cost

The separate validator reconstructs all 265 point clouds, all 98 previous endpoints, the full available identity chain, calibration and relative poses, aggregate gates and resource checks. It brute-forces all 3,040,000 directed distances; maximum discrepancy is 3.221e-13 m. `validation.json` records the complete check groups and passed outcome. Bank, evaluation and validation total 62.748 s; validator 38.212 s; peak RSS 0.338 GiB; artifacts before reports 37,763,402 bytes. Resource caps pass. The earlier approval-service usage failure did not execute the validator; the authorized retry completed successfully.

## Consequence for the mainline

Further GT-driven tuning of 09 would be poorly grounded. Investigate a distinct GT-free RAP mechanism that retains directional information from generated point structure instead of reducing every loop to a rigid pose plus scalar quality. This is a research hypothesis, not an established uncertainty estimator or improvement. A bounded saved-flow engineering preflight precedes any label-based information screen or system test. All previous negative stops remain; no training, production/default/manuscript edit, commit or Git synchronization.

The [official KITTI evaluator](https://www.cvlibs.net/datasets/kitti/eval_odometry.php) notes historical ground-truth sensitivity on short segments; that general warning is not evidence about these exact 09 revisits. This local test is a geometry diagnostic, not a replacement benchmark.
