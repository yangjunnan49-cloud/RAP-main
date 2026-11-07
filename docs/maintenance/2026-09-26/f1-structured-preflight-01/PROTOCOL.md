# F1-V1 structured-motion generation engineering preflight

Owner approved E0 followed by F1 on 2026-09-26. Engineering only; no efficacy
decision, GT loop-error screen, selector, training or threshold tuning here.
Source/input execution freeze must precede model execution.

## Fixed observed-development inputs

Use the first saved KITTI00 pair in each stratum of the immutable HL-V2
data-expansion-01/discovery_evaluator.json, matching discovery_inputs.json.
Fixed run order: confuser 24/629; ambiguous_positive 210/1656; low_overlap
422/3496; ordinary 956/3859. Preserve their four saved past support IDs and
causal LiDAR local_pose matrices. No selection using RAP successes. Export a
sanitized inference-only input file; evaluator/GT files are not loaded by run.
Preserve old no-205, >=1.5m input convention and original local motion for this
engineering screen, independently of E0 outcomes. F2 must declare its convention.

Each pair has six ordered parts [i, i_support1, i_support2, j, j_support1,
j_support2], counts [2000,1000,1000,2000,1000,1000], total 8000. Existing .4m
voxel/outlier preprocessing, exact allocation required, no duplication or
replacement on shortage. Cap sampling seed42. Compute learned descriptors once
on the retained per-scan points. Seeds260926..260929 in fixed pair order; K1,
five Euler steps, frozen RAP12/miniSpinNet, no fine tuning.

## Controls and endpoint semantics

N: native six-part sampling; decode per-part fits of RAW final clean endpoint.
F: the same native trajectory, group-project only its RAW final endpoint.
S: group-project the RAW clean endpoint at every step, interpolate projected
clean points with the same original Gaussian noise into the next noisy state;
decode final projected group poses. Also save/decode raw final endpoint.
P: two pooled parts using EXACT same retained physical points transported into
their respective anchor frame; reuse corresponding descriptors, no resampling.
Normalize pooled parts with their own standard normalizer. Use the same ordered
noise values. This controls data/point/descriptor budget, not normalization.
A: two anchors only, same 2000 points each, descriptors and corresponding noise
rows; reference only, not equal-data/equal-compute.

N/F/S use byte-identical input points/descriptors/normalization/noise. F reuses
N's result; its extra projection cost is recorded separately. P keeps scan
descriptors intentionally to avoid confounding with feature re-extraction; it
is not the historical pooled-context preprocessing or a pure partition-only arm.

For group g, q_gk=(L_gk*p_gk-c_g)/scale. Fit G in normalized coordinates to
raw endpoints by corresponding point index; decode physical G=(R,scale*t-R*c_g).
All L are within-visit, L_anchor=I; no across-visit odometry or GT transform input.
Preserve six feature/attention partitions for S. Save raw/projected clean
trajectories and noisy states explicitly; never silently substitute endpoints.

## Engineering checks and bounded sensitivity

Implement in isolated RAP-SLAM module with direct model calls and no global
monkeypatch. Compare custom N with the official unmodified sampler using same
batch/noise; max endpoint/state delta <=1e-6. Reordered S replay must reproduce
within1e-6. No model method/hook changes; request RNG and IEEE matmul scopes
restore state after success and injected exception. Fit SVD outside autocast,
with TF32 disabled via existing cooperating lock; neural FP16 stays enabled.

Require finite outputs, proper rotations (orthogonality/determinant <=1e-5),
exact point allocations, reconstruction/normalization error <=1e-4m and
projected relative-motion matrix residual <=1e-4. Independently reconstruct
group fits with float64 NumPy, check max projected-point disagreement <=1e-4
normalized units and independent decoded pose agreement <=1e-3m/matrix units.
Synthetic checks must include nontrivial rotations/translations and gauge changes.

On the fixed ordinary pair only, perturb every support L (not anchors) by
left-composed +/-0.10m x translation and +/-1 degree z rotation, two fixed arms.
Record S transform change, rigidity and finite constraints; no accuracy claim
or perturbation-strength choice. After outputs freeze, evaluator may quantify
saved local-motion error against GT for those supports, never feed it into run.

## Budget and decision

One RTX5070, <=12GiB allocated, <=1800s process wall including model loading
and all GPU preprocessing/inference, <=2GiB artifacts. No simultaneous E0 GPU
run. Four pairs, N/F/S/P/A plus native reproduction, one reordered S replay
and the two specified sensitivity arms. Stop on shortage, failed correctness,
OOM or cap; preserve failed attempt and its freeze. Correctness fixes require
an explicit amendment before a new execution directory; never overwrite outputs.

PASS_ENGINEERING only when all mandatory checks pass. It licenses a separately
frozen F2 development protocol, not a contribution or performance claim. F2
must declare useful margins, K4 budget, common gate, local-motion sensitivity,
strong comparators and later fresh confirmation before inspecting new outcomes.
