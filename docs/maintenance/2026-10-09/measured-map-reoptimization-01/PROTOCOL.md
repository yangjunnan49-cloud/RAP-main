# MMR0: bounded joint measured-map exploration

Date: 2026-10-09. Owner instruction: follow the first research mainline.
Exploratory engineering pilot, not final confirmation or a full SLAM deployment.

Scope: an isolated CPU numerical preflight and four source-bound development
windows. No learning, RAP inference, new loop/retrieval policy or full trajectory
replacement. Existing production files and scientific banks remain unchanged.
The continuation selects measured-point optimization; this protocol makes the
small geometry-only exploration concrete. No separate broad training or
whole-sequence execution permission is inferred.

## Observations and selection

Select the last eight saved E0 A keyframes at/before boundaries 00:200,00:800,
05:200,06:200. Selected before new geometry/GT outcomes:

- 00:200 = 137,146,154,162,170,178,187,197.
- 00:800 = 748,752,762,771,779,786,793,800.
- 05:200 = 141,145,152,162,170,178,186,194.
- 06:200 = 155,160,165,171,177,183,190,198.

These are historically exposed development sequences. The latest boundary
permits retrospective adjustment of all seven non-anchor poses in its window.
This is not a claim of zero-latency odometry or cross-site independence.

Read corrected raw scans: finite XYZ, original range between1.5 and80m,
existing +0.205deg vertical correction,0.5m voxel representatives. Keep first
input return per voxel, order representatives lexicographically by voxel,
uniformly subsample this ordered list to6000 if necessary. Even rows are
optimization points, odd rows are supplementary probe points. Twenty-neighbor
PCA uses the full retained representation; this sharing means probes are not
independent statistical evidence. A normal is usable when eigenvalue0/sum<.05
and eigenvalue1>1e-6. Bidirectional nearest associations inside1m, valid normals
at both endpoints and absolute normal agreement>=cos30deg. Directed temporal
edges have keyframe-index lag one or two. Minimum50 associations per directed
edge at every rematching round; otherwise fail this pilot rather than silently
drop an edge. No cross-visit or GT observations enter optimization.

Initial poses are the saved corrected E0 odometry, relative to first window
pose. Project their rounded rotations to nearest proper SO3 once, with the
maximum change recorded and required<1e-5. This defines a new numerical
interface, not a repair of old trajectories. O is that proper initial baseline.

## Objective and controls

For target scan a and source b, z=T_a^-1 T_b p_b and residual
r=n_a dot(z-p_a). All window poses except the first are variables. Normals
remain measured local normals; their world orientation changes with pose.
No fixed loop measurement or predicted covariance is used.

- O: unchanged proper initial poses.
- F: joint optimization with initial associations held fixed.
- R: same joint optimizer, associations refreshed before each outer round.

Both learned-free optimization arms use6 outer rounds with4 inner iterations.
Sum per-directed-edge mean pseudo-Huber cost with scale.20m. No odometry
factor/prior is added. IRLS analytic right-pose Jacobians, diagonal damping
1e-3*max(diag(H),1e-8), per-node step limit1deg/.20m, and backtracking scales
1,.5,.25,.125,.0625 ensure fixed-association cost does not increase. An iteration
with no accepted step is logged as a numerical no-op. Record Hessian spectrum;
inverse Hessian is not called a calibrated covariance. Maximum absolute
correction must remain<=1m/5deg, otherwise fail without fallback. Both arms
finish their declared rounds; no favorable early selection or parameter search.

Selected finite-difference Jacobian checks, common-gauge invariance, perfect
no-op, known-correspondence recovery and a wrong-consistent planar blind spot
must pass before real optimization. This is a conventional joint point-plane
optimizer, not a reproduction of BALM/GLIM or an original RAP mechanism.

## Outputs, evaluation and decisions

Freeze protocol, helper/runner and source inputs before computation. Save raw
processing identities, optimization/probe points, normals, initial poses and
all F/R pose outputs/traces. Seal all four windows before loading numeric GT.
Then report supplementary probe NN mean/p95/1m coverage, fixed-anchor relative
translation RMSE, mean/max relative rotation error and aligned eight-position
ATE. Reference GT uses the unchanged existing KITTI camera-to-LiDAR convention;
new rotation errors compare nearest-proper rotations. These short windows do
not constitute full-system KITTI ter/rer or trajectory benefit. Keep official
metrics and labels unchanged. No local good residual proves correct association.

Prospective descriptive signals: per window>=5% improvement in relative
translation RMSE and nonworsening mean rotation; probe mean-NN improvement>=5%.
Report every window and F/R, including invalids. A signal in>=3/4windows would
justify designing a complete-sequence mapping pilot. Failure is a narrow
exploratory outcome, not a universal geometry stop. In particular fixed versus
refreshed differences may be tiny because corrected KISS already starts nearby.

Lightweight validator independently checks the analytic residual via world
planes, selected derivatives, output SO3/gauge, source hashes, raw processing
on one scan per sequence, final association residuals and Horn alignment/GT
error arithmetic. No complete optimizer replay is required for this development
pilot. It must not be described as full independent execution reconstruction.

Combined recorded stage computation<=1800s including failed stages; CPU only,
RSS<=2GiB, artifacts<=512MiB. One BLAS/OpenMP thread. No auto budget extension,
parameter/cohort rescue, install/acquisition, model load, production/default/
manuscript change, commit or Git synchronization. This is a new isolated budget;
all prior experiment budgets remain closed and unchanged.
