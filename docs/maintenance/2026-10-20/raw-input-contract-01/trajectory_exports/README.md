# Complete fresh-raw trajectory-core G/K, 2026-10-20

36 complete trajectories: sequences00/05/06/07/09/10, G/K, repeats1/2/3. Each *_lidar.txt row contains the first three rows of a4x4 world-from-LiDAR pose, row-major, no alignment/scale fit. Append homogeneous row0 0 0 1. Units meters; frame index is original zero-based sequential scan index. Saved17-digit floats round-trip checked. No frames selected or dropped.

G is experimental fixed-E0 odometry plus native map closures and explicit source-frame anchor fine graph. Every repeat computes fresh E0 from original scans with certified original float32 correction; no cached eligibility poses supplied. K is native KISS-SLAM trajectory core. Minimal trajectory/evidence output only; full native CLI map/occupancy side-products omitted for both. Three fresh-process repeats are exposed development sequences, not independent scenes. First K00 is the single predeclared retained original complete control.

RESULTS.json contains all36 rows, three-repeat per-sequence summaries, six-sequence arithmetic means and separately reported mean objective/safety results. Aligned ATE uses LiDAR poses; KITTI ter/rer use camera calibration internally, but exported poses remain LiDAR and unaligned. OPERATIONAL_RESULTS reports measured batch cost/tail latency; not a guaranteed10Hz service. CONFIG_G/K preserve used configurations. No automatic default promotion/new RAP efficacy/generalization claim.

The precision/fixed-odometry/anchor modules are the tested components, not a standalone data loader or complete environment installer. Raw scans and GT are not included. Full provenance/failure/cost/seal records remain in the companion repository report. Existing library/default/reference/Git state was not changed.
