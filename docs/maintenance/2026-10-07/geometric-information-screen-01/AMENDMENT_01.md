# PFG1 amendment01: independent rigid-inverse reconstruction

Before evaluator GT, the original independent bank validator failed on the
first00 edge's H comparison. Original170-identity freeze, algorithm/driver/
validator, complete bank/seal, failure and root INCOMPLETE remain immutable.

Diagnosis on the sealed inputs: native serialized R has orthogonality defect
3.478373e-7. General4x4 inverse differs from the frozen algorithm's rigid inverse
R^T(p-t), also used by native GTSAM Pose3.inverse. H max delta0.142773 and
relative normalized-entry delta2.724791e-6; rigid-transpose reconstruction
reproduces original H exactly. This is a validator convention mismatch on
rounded native matrices. These are nominal rigid-transform Jacobians; an exact
derivative interpretation at the nonorthogonal serialized matrix is not claimed.

Separate attempt-02 freezes new protocol/driver/validator plus every original
source/bank identity before retry. Only the validator's reverse-point inverse
changes to the frozen rigid inverse. All58 poses must have orthogonality error
below the existing1e-5 SE3 tolerance and reproduce native Pose3.inverse to1e-12;
record general-inverse disagreement. No bank/model rerun, eigenvalue/normal/
match change, tolerance relaxation, cohort, gate, pose or acceptance edit.

Evaluator driver v2 only redirects output and validation dependency to the
separate attempt. It cannot generate a replacement bank. Original matrices/
trajectories remain exactly sealed. Evaluation proceeds only after separately
frozen independent retry validation. No GT value has been used in this repair.
