# LMF1 complete causal local-motion accuracy screen

Owner authorized continuation after validated LMF0. This observed-development
screen tests whether native unposed three-scan RAP supplies materially better
local motion than saved KISS and matched geometric controls. It is not original
algorithm evidence or a full-system trajectory trial. All earlier stops persist.

## Fixed population and physical budget

Use exactly LMF0's58 windows:22/13/5/5/7/6 on00/05/06/07/09/10, t in
range(0,N,200), with six shared t=0 structural exclusions. Inputs order
[t-1,t,t-2], own original LiDAR frames and causal times. No GT-error ranking,
favorable segment selection or method-specific deletion. All sequences are
previously exposed; six t=200 windows already have engineering output. Checkpoint
training membership remains unknown; no held-out or independent confirmation.

Reuse unchanged frozen local_motion_common.py. Range>=1.5m,+.205deg correction,
.4m voxel,outlier20/2.5,seed42 cap1000/scan,5m miniSpinNet patch support from
the same capped scan. Feature/noise seed SHA256('LMF1|seq|t') first4 bytes
big-endian. Strict weights_only RAP344/descriptor58 loading with reviewed explicit
metadata allowlist; no unrestricted fallback. K1,five Euler steps, per-part
rigidity forcing. No KISS/GT within-visit pose imposed in native RAP.

R3 uses3000 points/three scans. R2 uses the same first2000 points/features/noise,
with explicitly less context/compute. G2: identity-initialized current->previous
point-to-point ICP, distance<=3m,>=20 matches,max30 steps, maximum increment
entry difference from identity<1e-7 convergence. G3: same independent geometric
oldest->previous fit, pool previous1000+transported oldest1000, then register
current1000 initialized by G2. It receives the same physical3000-point/three-scan
budget as R3 and no privileged learned/GT/native motion. Saved unoptimized KISS
relative inv(O[t-1]) O[t] is a practical dense-map reference with greater context,
not equal-input causal isolation. All transforms map current points to previous.

## Stage separation and immutable evidence

Synthetic evaluator/calibration/direction/serialized-rotation and decision
arithmetic checks precede real output. Freeze protocol, runner, evaluator,
independent validator and their helpers, prior successful LMF0 identities/seals,
all174 raw scans, full manifests/times, saved odometry and GT/calibration files
before complete-window generation. GT files are hashed only until full bank is
sealed and GT-free bank validation is sealed. Bind odometry to the earlier
validated temporal-audit freeze. Freeze the unchanged seed/census and all gates.

Generate every window anew. Save points/features/noise, both RAP raw/noisy
five-step endpoints, centers/scales/counts/part transforms, all relative poses,
geometric support transport and iteration records. Reproduce all six previously
saved local engineering arrays within1e-5 without deleting any new window.
Require proper R3/R2/G2/G3 rotations within1e-8 and finite arrays. KISS serialized
rotation tolerance1e-5 is verification only, without altering stored poses.
Seal all58 NPZ files and bank manifest before evaluator GT. No fallback/drop.

Independent pre-GT validator reconstructs all174 capped scans using direct raw
correction and Open3D, directly reruns all descriptors with strict safe loading,
regenerates every declared seed/noise, verifies paths/time/order/census and
normalization, Horn-fits every final part/relative transform, brute-forces every
ICP iteration/control, verifies all saved KISS relative poses and six engineering
replays. Require byte-exact point/feature/noise/cond arrays, centers/scale1e-12,
independent poses/control traces1e-8. Seal this validation before evaluator GT.

## Evaluator and unchanged material gates

GT LiDAR poses: Tr^-1 camera_pose Tr. T_GT=inv(G[t-1]) G[t]. Preserve serialized
GT and translation math. For E=inv(T_GT) T_pred, translation error=norm(E[:3,3]);
rotation error=angle(nearest proper SO(3) to E[:3,:3]). Only the angle calculation
recovers a proper rotation, explicitly by SVD; it does not replace GT or graph
poses/labels. Synthetic anisotropic serialization verifies this convention.

For each X in KISS/G2/G3, primary pooled paired median (translation_X-
translation_R3)>=0.01m, median ((X-R3)/max(X,1e-6m))>=0.10 and fraction of strictly
positive paired gains>=0.60. Added-context gate versus R2: paired median
translation gain>=0.005m and strictly positive fraction>=0.60. Complete defined
coverage58/58 is mandatory. All primary and context gates must pass.

For each of six sequences and each KISS/G2/G3 control: mean translation_R3
minus mean translation_X<=0.01m; median paired rotation_R3-minus-X<=0.05deg.
All safety gates must pass. Report every row, per-sequence/pooled mean, median,
p90 and equal-sequence mean descriptively. Deterministic neighboring samples
are not independent draws; no significance or bootstrap guarantee claimed.
Failure decision NO_CAUSAL_LOCAL_MOTION_SIGNAL stops this fixed layout before a
trajectory rerun. Pass MATERIAL_CAUSAL_LOCAL_MOTION_SIGNAL only licenses a
separately frozen full causal trajectory experiment with unchanged retrieval,
graph/evaluator and material ter/ATE plus sequence safety. Never tune this bank
by window/seed/step/count/voxel/patch/initialization/gate rescue.

Final independent validator separately parses raw GT/calibration and odometry,
reconstructs relative direction, uses polar decomposition and atan2 rotation,
checks every error, independent aggregate/sign/material/safety decision and
seal-before-GT timing. Translation/rotation error reproduction1e-7; aggregates
1e-7. Preserve original failures and disclose any repair; no frozen-code edits.

Caps combined successful bank/pre-GT-validator/evaluator/final-validator<=1800s,
GPU allocated<12GiB,RSS<4GiB,artifacts<250MB. Include full final identity recheck
in each recorded duration. Record any failed-command overhead separately.
No training,production/default/model/manuscript edit,commit or Git sync.
