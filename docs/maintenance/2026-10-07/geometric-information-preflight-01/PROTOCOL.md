# PFG0 analytic geometric-information preflight

Owner requested further progress. PFG0 follows validated MC1, but is separately
frozen before output. It tests a conditional geometry-information shape, not
accuracy, physical alias correctness, calibrated covariance or originality.

Rotation-first right tangent: T maps q_j to p_i. Use both fixed point-plane
residual Jacobians: n_i^T R[-[q_j]x,I] and n_j^T[[T^-1 p_i]x,-I]. Sum H=J^T J.
Reference Sigma=diag(0.03^2*3,0.20^2*3); Omega=6H/trace(Sigma H). An exact
plane retains rank3, two perpendicular planes rank5, three planes rank6.
Normal-sign, row-order and complete-row-duplication changes preserve Omega.
Do not floor positive eigenvalues or select an axis using errors. Rank for
reporting uses 1e-10*lambda_max, without changing positive information.
Roundoff-negative eigenvalues only are clipped for the square root. Zero
trace <=1e-20 rejects the shape; no calibrated uncertainty assertion.

Freeze protocol, algorithm, runner and independent validator. Three geometries
times four deterministic nontrivial rigid poses produce 12 cases. Store inputs,
J/H/Omega/square-root and finite-difference/transport checks in complete NPZs.
Finite difference h=1e-6, tolerance2e-8; algebra/whitening tolerance1e-8.
Test inversion with Sigma transport, changed source/target coordinates,
millimeter units, fixed wrong tangential2m plane displacement, empty support,
PCA-normal estimator and deterministic nearest-neighbor tie selection.

Surface normals in the later real construction use20 nearest measured points
(including the query), distance/index tie order. Require lambda1>1e-12 and
lambda1-lambda0>1e-10*max(1,lambda2) to avoid a numerically nonunique normal.
No planarity/normal-angle/density optimization. Mutual nearest associations
inside squared distance<=1m^2; two Jacobians per association. The estimator
test uses a separated planar grid and line/duplicate rejection.

GTSAM Gaussian.SqrtInformation must support singular plane matrices; compare
factor errors and whitening against explicit quadratic forms. Store library
versions. Separate validator imports no experiment algorithm/runner, uses
SciPy matrix exponential for finite differences, direct outer products and
brute-force neighborhood/association construction. All cases must pass.

CPU-only, <=120s per stage, RSS1GiB, artifacts10MiB. No real scans/features,
inference, GT, trajectory, training, production/default/manuscript/Git changes.
Seal complete bank before independent validation. Preserve failures/freeze/
INCOMPLETE; any repair needs disclosed separate attempt. Only validated PFG0
admits a separately frozen PFG1 real-system screen from MC1 NEXT_ROUND_PLAN.
