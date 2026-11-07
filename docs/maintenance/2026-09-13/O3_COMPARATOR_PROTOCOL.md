# Matched ICP on the O3 candidate cohort

Declared before execution on 2026-09-13. Reuse exactly the 40 ordered candidate
pairs from optimization-o3-01 (POSS 4, KITTI 06/05/00 12 each), fresh full-run
odometry/keyframes/source IDs and saved O3 RAP measurements. Do not regenerate
retrieval or RAP. Run both identity and odometry-initialized point-to-point ICP
on every pair, independently of RAP acceptance. Initial odometry is inv(T_i) T_j;
ICP maps scan j into scan i. No GT enters initialization, selection or gates.

Use the earlier comparator settings unchanged: Open3D 0.19, maximum correspondence
distance 2.5 m, 100 iterations, relative fitness/RMSE 1e-6. Production geometric
preprocessing: minimum range 1.5 m, voxel 0.4 m, statistical outlier removal,
deterministic cap 4000 with seed 42. ICP does not consume learned descriptors.
Gate: valid rotation, overlap >= 0.7 and mean distance <= 2.5 m, freshly measured
for each attempt. Backend: relfloor + Huber, NMS 0. No refinement or fallback.

Record all attempts, failures, rejected and accepted labels, exact source IDs,
initial/final transforms, preprocessing hashes and measurement-linked edges.
Validate source stability, transform direction, exact candidate order, gates,
labels, edge associations and saved-trajectory metrics. Hash code, parents,
GT/calibration and consumed scans; compare shared inputs with O3 manifests.
Use new exclusive output o3-comparator-01; keep INCOMPLETE until checks pass.

Report per-sequence first-pose/aligned LiDAR APE, camera KITTI drift (POSS custom
LiDAR drift), acceptance and labels for all three methods. Record ICP-only
monotonic registration times; do not compare them to RAP stage wall time as a
speed ratio. Use OMP/OPENBLAS 4. No tuning, per-sequence method selection or
automatic default change. Different accepted sets are part of the system
comparison, not registrar-only isolation. Odometry ICP has an extra pose prior.
These are observed development sequences, not independent statistical evidence.

After execution, consolidate the fair comparison and explain metric tradeoffs.
Do not infer universal superiority from a subset of metrics or sequences.
