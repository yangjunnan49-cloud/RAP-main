# Independent rotation metric implementation correction

The original full independent validator stopped at an angular discrepancy:
0.345875 versus0.339560degrees, exceeding unchanged0.003degree verification
tolerance. It used matrix inverse for `R_est^{-1} R_gt`; the frozen evaluator
uses transpose `R_est^T R_gt`. Float32 learned rotations satisfy the unchanged
proper-pose guard but are not exact orthogonal matrices. Inverse and transpose
therefore differ slightly, and acos magnifies differences at small angles.

V2 independently computes the frozen evaluator's rotational trace through the
elementwise Frobenius inner product `sum(R_est * R_gt)`, equal to
`trace(R_est^T R_gt)`, instead of solving the noisy matrix inverse. This is a
verification implementation correction, not an outcome/threshold revision.
All tolerance values, pair labels, predictions, graph trajectories, evaluator
outputs and protocol gates remain unchanged. Original failed validator stays
frozen. No new neural inference or GT-based favorable selection occurs.

Freeze this document, V2 validator and amended entry point before rerunning
all final checks. Verify both earlier freeze and amendment identities as well.
