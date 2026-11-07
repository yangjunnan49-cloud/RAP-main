# P0: fixed-budget 0.25 m/FPS engineering preflight

Frozen before new output. Use the first two saved F2 pairs in each of KITTI
00 and 08, in saved order, with all six corrected scans per pair. This is
GT-free: do not read evaluator GT, stratum or native-candidate labels. Saved
F2 points and C1 descriptors are the unchanged control.

Retain raw XYZ with range >=1.5 m, then apply the local +0.205-degree KITTI
correction. Open3D voxel-downsample at 0.25 m. Use the complete voxel cloud
as miniSpinNet support. Remove statistical outliers (20 neighbours, ratio
2.5) only from the FPS candidate cloud. Stop if a scan has fewer candidates
than its fixed point count or more than 400,000 voxel points. The latter is
the upstream inactive pre-FPS cap (20 times 20,000); no random pre-cap is
allowed. Batch six scans in saved order, call upstream `apply_batched_fps`
with PyTorch3D random start and global Torch seed 42, and keep exactly
`[2000,1000,1000,2000,1000,1000]` points in returned order. No fallback,
replacement or count reallocation.

Extract 32-D features at the selected keypoints using the complete
pre-outlier, pre-FPS voxel cloud, strict `weights_only=True` miniSpinNet
checkpoint load, 512 points per patch, global-Z alignment and 5 m radius.
All points/features must be finite and every feature norm >1e-8. Confirm
the saved F2 point counts and C1 descriptor validity. Save P0 points,
features, per-part voxel/outlier counts, timing and peak GPU memory. Freeze
this protocol, runner, validator, sources, weights, four saved F2 inputs,
four C1 feature files and 24 raw-scan references before running. Leave
`INCOMPLETE` on any failure. Caps: 20 minutes wall, 12 GiB allocated GPU
memory and 100 MiB new data artifacts.

The independent validator rehashes frozen sources and bank artifacts,
checks counts, finite/nonzero descriptors and keypoint membership, then
reprocesses first and last scans for exact point/descriptor repeatability.
Success permits only a separately frozen full 200-pair information audit.
This fixed-count arm is upstream-inspired, not the paper's adaptive recipe.
It jointly changes voxel scale, point placement and feature support. No RAP
generation, training, default edit, Git sync or efficacy claim in P0.
