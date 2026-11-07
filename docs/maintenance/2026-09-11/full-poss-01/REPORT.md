# Full poss core rerun

1419 raw scans, source IDs 3850-5268; fresh KISS-ICP, retrieval, RAP and PGO.

| Metric | Odometry | RAP + PGO |
|---|---:|---:|
| ape_unaligned_rmse (LiDAR m) | 8.257400 | 1.822264 |
| ape_aligned_rmse (LiDAR m) | 2.564951 | 0.666054 |

Keyframes: 82. Candidates/accepted: 4/4. Labels: {'safe': 4}.

Production stage wall times (seconds):

| Stage | Seconds |
|---|---:|
| sequence | 11.01 |
| odometry | 101.32 |
| loop_closure | 15.20 |
| pgo | 0.07 |
| evaluation | 10.01 |
| Pipeline total | 137.63 |
| Subprocess including startup | 137.59 |

Loop closure timing includes retrieval, model loading, hashing and inference; evaluation includes map exports. Preflight hashing warms file reads. One run, not a cold-cache or real-time latency benchmark. Separate camera-frame KITTI drift is saved in paper_metrics.json. This remains development evidence, not independent calibration.
