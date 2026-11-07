# Fixed dense-pose correction propagation screen

Owner authorization: 2026-10-05, proceed with the proposed mainline plan.
Status: design; execution requires this protocol, runner, independent validator,
synthetic preflight and input identities to be sealed in freeze.json first.

Question: does one fixed SE(3) correction interpolation improve saved E0 A
trajectory metrics while preserving ATE? Engineering diagnosis, not RAP novelty.
All 00/05/06/07/09/10 are now exposed research data, not new confirmation.
The existing planned gates are preserved without changes.

Inputs: saved E0 A odometry, optimized full trajectories (keyframe rows only
for construction), keyframe IDs and source-frame manifests. Freeze prior audit
freeze/results identities, production pose_graph.py and metric/GT/calibration
dependencies. Verify all overlapping input/source hashes against the audit
freeze before computation. Hashing GT bytes for identity is allowed; no GT
numeric parse occurs before the complete new trajectory bank is sealed.

O_s is odometry. K_a is the saved optimized pose at keyframe a.
P uses the frozen native function's C_a = K_a inv(O_a), constant on [a,b).
S uses C_s = C_a Exp(alpha Log(inv(C_a) C_b)), alpha=(s-a)/(b-a),
T_s=C_s O_s. GTSAM Pose3 Expmap/Logmap compute the single interpolation;
keyframe rows are copied exactly from K. No graph reoptimization, inference,
new loop selection, smoothing parameter or space/weight sweep. No estimated
pose projection is added. Reject nonfinite/invalid SE(3) beyond 1e-5 tolerance.
Saved-text roundoff is tolerated; report its actual maximum.

Preflight before full bank: deterministic 64 synthetic correction pairs,
SE(3) exp/log including zero and near-pi rotation; endpoints, near-endpoint
continuity, constant corrections, common left-gauge covariance. A separate
SciPy Rotation plus analytic SE(3) Jacobian implementation verifies the
interpolator without GTSAM. Check saved zero-loop sequence10 P/S/odom agreement
within 1e-5 before the full bank, using only source trajectories and IDs.
Synthetic records and this GT-free 10 preflight are frozen with the code.

Stage A: exclusive attempt-01 and INCOMPLETE marker; verify freeze first.
Generate P/S plus frame IDs and GT-free diagnostics on all six sequences.
Require native P vs saved optimized full <=1e-5, exact S anchor equality,
source IDs 0..N-1, finite SE(3), and sequence10 identity <=1e-5. Diagnostics
record correction-change translation/rotation at keyframe boundaries and
across adjacent scans; these gauge-dependent magnitudes are descriptive,
not an accuracy or causal contribution. SHA-seal the complete attempt
directory before importing/loading evaluator GT. Record stage UTC times.

Stage B: preserve existing evaluation conventions: calibrated LiDAR GT,
aligned LiDAR ATE; conjugate LiDAR poses to camera frame for KITTI ter/rer.
Evaluate odometry/P/S with the frozen existing metric code. Save every exact
100–800 m segment record, source endpoints, all-segment means by sequence,
and arithmetic per-sequence cohort means. Require P/odometry metrics to
reproduce the previous audit within 1e-5 absolute metric units. These small
tolerances check saved-text reconstruction, not the prospective gain gates.

Gate (all conditions required): S reduces each group's mean ter versus P
by >=0.01 percentage points; mean aligned ATE in each group worsens by <=2%;
each sequence ter worsens by <=0.01 percentage points and ATE by <=5%;
sequence10 P/S max pose-entry difference <=1e-5. Report all six effects.
Use raw float64 values for decisions, never rounded table values.

Independent validation: rehash exact freeze/seal inventories and timestamps;
reconstruct all S poses via the separate SciPy/analytic implementation;
independently reconstruct P, check anchors and frame IDs/SE(3)/10 identity;
recompute GT/calibration conversions, ATE by rigid Kabsch alignment without
scale, and all KITTI segments using independent strict endpoint enumeration;
check evaluator records/means and baseline reproduction; recompute every gate.
The validator must not import the runner's interpolation, metric or gate logic.
Report its numerical tolerances and largest cross-implementation differences.

CPU-only caps: sum of bank/evaluation/validation wall <=1200 seconds,
maximum stage peak RSS <=2 GiB, total experiment artifacts <=500,000,000 bytes.
Preflight/setup runtime is reported separately. No CUDA or model loading.
Stops/invariants/caps preserve INCOMPLETE and the original attempt. Frozen
code cannot be repaired in place; a separate amendment/new attempt is required.
Only independent validation permits removing INCOMPLETE and final sealing.

Pass: bounded engineering propagation gain; reserve an eligible trajectory
cohort for later method confirmation. Failure: stop this exact interpolation
route without a space/weight rescue. Generic correction/interpolation is
[prior art](https://arxiv.org/abs/2009.08724); neither outcome establishes a
new RAP method or complete causal attribution. No production/default edit,
training, manuscript change, commit or Git sync. Old banks remain immutable.
