# Full kitti00 core rerun

4541 raw scans, source IDs 0-4540; fresh KISS-ICP, retrieval, RAP and PGO.

| Metric | Odometry | RAP + PGO |
|---|---:|---:|
| ape_unaligned_rmse (LiDAR m) | 12.266655 | 11.432935 |
| ape_aligned_rmse (LiDAR m) | 3.938481 | 2.891543 |

Keyframes: 670. Candidates/accepted: 12/12. Labels: {'safe': 12}.

Production stage wall times (seconds):

| Stage | Seconds |
|---|---:|
| sequence | 58.66 |
| odometry | 137.93 |
| loop_closure | 28.79 |
| pgo | 0.14 |
| evaluation | 42.43 |
| Pipeline total | 267.98 |
| Subprocess including startup | 259.21 |

Loop closure timing includes retrieval, model loading, hashing and inference; evaluation includes map exports. Preflight hashing warms file reads. One run, not a cold-cache or real-time latency benchmark. Separate camera-frame KITTI drift is saved in paper_metrics.json. This remains development evidence, not independent calibration.
