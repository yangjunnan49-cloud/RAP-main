# Full frontend core rerun v1

Declared before full-kitti06-01. KITTI 06 frames 0 through 1100 inclusive,
stride 1, all 1101 scans required. This is an already observed development
sequence, not a new holdout. Run the production offline pipeline from raw scans;
do not reuse odometry, descriptors or registrations. Save explicit source IDs,
timestamps if available, scan/calibration/GT hashes and source/checkpoint hashes.

KISS-ICP: range 1.5-80 m, voxel 0.8 m, deskew off, no fallback. Keyframes:
6 m / 12 degrees, force last. No 0.205-degree correction. Proximity + SC:
15 m, separation 200 frames, merged budget 12, SC threshold 0.25, shortlist 10,
20 rings / 60 sectors / radius 80 m. RAP: frozen weights, seed 42, five sampling
steps, one generation, voxel 0.4 m / cap 4000 / learned features enabled.
Heuristic overlap >= 0.7 and mean distance <= 2.5 m. Backend relfloor + Huber,
reference 1 m / cap 3 / Huber k 1 / NMS 0. No tuning after observing the run.

Use production stage timings: data loading; odometry; loop closure (retrieval,
model initialization, checkpoint hashing and verification together); PGO;
evaluation (including trajectory plot and map export). Keyframe selection and
other small work are included only in total. Record subprocess wall time as a
separate quantity including Python startup/imports. Hashing before/after the
process and post-run validation are excluded. File caches are not cleared;
preflight hashing warms scan reads. This is one observed run, not a cold-start
benchmark or latency distribution. OMP/OPENBLAS threads fixed to 4; other library
thread defaults retained. Do not compare these coarse timings to isolated ICP.

Primary first-pose LiDAR APE, secondary rigidly aligned APE; separately report
camera-frame KITTI segment drift via corrected evaluation. Check exact source
IDs/paths/timestamps, complete candidate events, same-measurement edge association,
rotation validity, independent metric recomputation and source stability.
Comparison to historical frontend is descriptive, not an exact-replay requirement.
Keep all outputs in a fresh directory; outer INCOMPLETE stays until validation.
