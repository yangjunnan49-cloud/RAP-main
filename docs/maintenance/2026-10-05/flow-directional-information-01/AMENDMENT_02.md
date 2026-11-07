# FDI1 amendment 02: validator-only serialized rotation log convention

The first v2 independent validator stopped at its error-vector reproduction assertion on the first row. No validation file was produced. Original evaluator results-v2.json, every matrix/pose, cohort and threshold remain unchanged. Retain v2 validator and amendment_freeze.json exactly.

Read-only diagnosis demonstrates KITTI text relative rotations have small nonorthogonality after calibration: first-row max |R^T R-I|=6.367e-8. The evaluator's analytic SE(3) log uses SciPy Rotation.from_matrix, which implicitly recovers a proper rotation. The validator's general 4x4 matrix logarithm instead includes the tiny nonrigid serialization component. Its normalized-vector discrepancy is 8.596e-6. Independently projecting only the log input rotation to nearest SO(3) by SVD, retaining its translation, reduces discrepancy to 4.547e-13; other inspected rows behave likewise.

Validator v3 applies this independent SVD recovery before the GT error matrix logarithm. It does not change strict labels, raw GT files/calibration, evaluator output, bank, candidate poses, scores or any gate/tolerance. Generated-flow deletion logs already involve proper double-precision rigid fits and remain unchanged. This is a numerical-convention repair required to validate the evaluator that already used proper rotations. It is not a label correction or GT rescue.

Freeze v3/diagnostic/this note in amendment_02_freeze.json before validation. Recompute all 200 rows and retain the original 1e-6 error-vector, 1e-7 array/score tolerances. Document both failed attempts and final validation.
