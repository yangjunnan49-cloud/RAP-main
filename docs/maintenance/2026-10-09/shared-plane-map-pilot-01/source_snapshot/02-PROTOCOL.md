# SMP1 shared-plane map pilot

Owner continuation: "继续主线推进". This authorizes the next isolated exploratory
shared-map stage described in the MMR0 continuation. No full trajectory, RAP or
learning/default change is inferred. Read the MMR0 next-round design as context.

Use its four existing exposed eight-scan banks, with the exact retained points
and proper initial O poses. The same windows have already been evaluated; this
is iterative development, never an independent data claim. Old MMR0 outputs,
sources, failure and gates remain unchanged. New budget: 1800 s recorded CPU
stages, 2 GiB RSS, 512 MiB dossier artifacts; failed stages count. One BLAS thread,
no acquisition/install. Stage timers exclude imports/WSL startup/design/docs.

## Fixed constructions

Scales are 2 m and 4 m, no other representation trials. Optimization uses even
retained point rows; odd rows are excluded from all training moments and plane
selection. Initial O transforms define fixed lexicographic world-voxel membership.
A contributing scan must supply >=6 even points. Require >=3 contributing scans
and >=40 total even points per patch. Compute a scan-balanced covariance (equal
mass per contributing scan), retain eigenvalue0/sum<.025, eigenvalue1>.005 m^2,
eigenvalue0<=.015 m^2, and max absolute per-scan mean plane offset<=.20 m.
These are selection rules, not physical plane identity or calibrated noise.

Groups and memberships stay fixed. Surface normal/center is analytically refit
at every cost/gradient evaluation. Equal scan mass prevents dense scan counts
from dominating but does not make correlated observations independent. Reject
a representation if <10 features or any scan has <100 retained training points;
record an invalid arm without density/threshold/window rescue.

O is unchanged. G optimizes shared geometry only. P adds adjacent relative motion
constraints from O, with fixed engineering scales sigma_t=.10 m, sigma_R=.15 deg.
Geometry cost = .5*mean_patch(min_eigenvalue)/(.10 m)^2. Prior cost = .5*mean_edge
(norm(rotation_log/sigma_R)^2+norm(relative_error_translation/sigma_t)^2).
Prior is correlated with point-cloud observations; these scales are regularizer
strengths, not estimated sensor uncertainties or independent likelihoods.

First pose fixed, seven others variables. Shared-plane nuisance parameters
(two normal tangents and offset) are Schur-eliminated in a Gauss-Newton system;
planes are re-estimated exactly for cost/backtracking. This is a conventional
BALM-inspired variable-projection prototype, not a full BALM solver reproduction.
The analytic compact-moment gradient is checked against finite differences and
an explicit point Jacobian/Schur construction. Relative prior Jacobians are
also checked separately. Fixed 24 updates, damping1e-3*max(diag(H),1e-8), per-node
step cap1deg/.20m, backtracking1,.5,.25,.125,.0625, nonincrease required. No best
iteration or convergence-based favorable selection. Final correction>1m/5deg
is an invalid outcome with poses retained, not fallback to O.

## Engineering and evaluation

Before real optimization: selected geometry/prior FD, moment versus explicit
point Schur, gauge invariance, proper rotations, exact no-op, three-plane
known-membership recovery and a planar translation blind spot. Freeze sources
and inputs first. If an implementation repair is needed, preserve frozen source
snapshots/failure, disclose the repair and refreeze/revalidate affected stages;
no scientific gate or representation changes under that repair.

Complete all eight window/scale feature banks and all sixteen G/P final outputs,
including invalids, before new accuracy evaluation. Numeric GT is not used in
features/optimizer despite historical exposure. Report unchanged MMR0 local
relative translation RMSE, mean/max rotation and eight-position aligned ATE.
No whole-sequence ter/rer/ATE claim.

Odd-row points are assigned to the same fixed initial voxel key, only where
that scan contributed training points. Evaluate their RMS plane residual under
refit training planes, all counts/coverage fixed. This removes MMR0's PCA sharing
but does not create independent statistical/physical validation. Also measure
leave-one-scan-out plane prediction using the other contributing scans; it is
a geometry diagnostic, not pose-reference accuracy or an admission oracle.

Local mapping-development eligibility for P, declared before new outcomes:
all four valid; aligned local ATE improves on >=3/4 windows with mean fractional
gain>=5%; no window ATE regression>5%; no relative tRMSE regression>5%; no mean
rotation regression>.02deg; mean odd-point RMS does not increase by>1%.
Both scales and G controls are fully reported. Fixed priority2m then4m chooses
an eligible P representation for a subsequent revisit design, not the greatest
observed gain. These new exploratory rules do not reclassify MMR0 or any old gate.

If no representation qualifies, do not run a complete trajectory or rescue sweep.
Analyze whether shared-plane observation consistency and motion regularization
changed the old objective/reference conflict. An ineligible small prototype is
not a universal shared-map or global BA stop. A qualified pilot would warrant a
concrete two-visit/internal-pose protocol next, not automatic production use.

Validate all compact moments against explicit point sums, plane cost/probe
arithmetic and selected gradients; independently reconstruct pose-error metrics.
No full optimizer replay is required for this discovery pilot. Preserve source
identities and the two repository HEADs/branches/2-and-9 tracked dirty sets.
