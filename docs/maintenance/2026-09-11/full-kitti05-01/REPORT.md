# Full kitti05 core rerun

2761 raw scans, source IDs 0-2760; fresh KISS-ICP, retrieval, RAP and PGO.

| Metric | Odometry | RAP + PGO |
|---|---:|---:|
| ape_unaligned_rmse (LiDAR m) | 5.193528 | 3.417117 |
| ape_aligned_rmse (LiDAR m) | 1.868615 | 1.129313 |

Keyframes: 374. Candidates/accepted: 12/12. Labels: {'safe': 12}.

Production stage wall times (seconds):

| Stage | Seconds |
|---|---:|
| sequence | 34.93 |
| odometry | 82.08 |
| loop_closure | 23.63 |
| pgo | 0.11 |
| evaluation | 26.00 |
| Pipeline total | 166.79 |
| Subprocess including startup | 162.26 |

Loop closure timing includes retrieval, model loading, hashing and inference; evaluation includes map exports. Preflight hashing warms file reads. One run, not a cold-cache or real-time latency benchmark. Separate camera-frame KITTI drift is saved in paper_metrics.json. This remains development evidence, not independent calibration.
