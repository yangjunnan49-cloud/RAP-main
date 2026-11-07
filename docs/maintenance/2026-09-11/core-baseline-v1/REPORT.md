# Core offline optimization baseline v1

Audit-only work is closed for the scoped four-sequence offline core. All raw-scan reruns and necessary metric checks passed. Optimize against this baseline; keep legacy live/Spires/statistical claims deferred.

| Sequence | Frames | Loops | Odom APE m | RAP APE m | Aligned RAP APE m | Pipeline s |
|---|---:|---:|---:|---:|---:|---:|
| poss | 1419 | 4 | 8.257400 | 1.822264 | 0.666054 | 137.63 |
| kitti06 | 1101 | 12 | 2.777067 | 2.446184 | 0.868971 | 99.61 |
| kitti05 | 2761 | 12 | 5.193528 | 3.417117 | 1.129313 | 166.79 |
| kitti00 | 4541 | 12 | 12.266655 | 11.432935 | 2.891543 | 267.98 |

APE uses LiDAR first-pose alignment; aligned APE is a separate metric. No sequence pooling.

| Sequence | Drift frame | Odom translation % | RAP translation % | RAP rotation deg/100m | Segments |
|---|---|---:|---:|---:|---:|
| poss | LiDAR (custom POSS) | 3.859185 | 1.961403 | 1.978396 | 217 |
| kitti06 | camera | 0.643021 | 0.667058 | 0.316593 | 570 |
| kitti05 | camera | 0.772150 | 0.703737 | 0.342123 | 1806 |
| kitti00 | camera | 0.904738 | 0.914171 | 0.389455 | 3283 |

## Legacy reconciliation

All 18 saved-trajectory metric rows reproduce the earlier M2 corrected values within 1e-9. No new ROS/live acquisition identity is claimed.

| Sequence | Legacy PGO APE | Fresh frozen replay APE | Full rerun APE | Odom max element change | Same candidate order |
|---|---:|---:|---:|---:|---|
| poss | 1.820877 | 1.822264 | 1.822264 | 1e-10 | True |
| kitti06 | 2.441022 | 2.446184 | 2.446184 | 0 | True |
| kitti05 | 3.417050 | 3.417117 | 3.417117 | 1e-10 | True |
| kitti00 | 10.919673 | 11.432936 | 11.432935 | 1e-10 | True |

KITTI 00 legacy used budget 40; new core uses 12. This difference cannot be attributed to a numerical repair. Old drift used length-macro aggregation; use the M2 v2 all-segment values. Old map/crispness, conformal and N-way conclusions remain legacy unless independently regenerated.

Single-run timings include map export and warm reads. Production stages use time.time; differences from the monotonic subprocess duration (also saved in registry.json) indicate clock-accounting uncertainty. Do not use these stage totals as a precise throughput benchmark or rerun solely to improve timing precision. These are development sequences; no generalization guarantee. Source/config/input identities are in registry.json and each run manifest.

Next: optimize measured trajectory quality. First bounded experiment: RAP-initialized local ICP refinement with same candidates and remeasured gate diagnostics; then candidate coverage/budget if useful. Do not spend more time tuning robust kernels on this clean cohort (previous ablation was negligible).
