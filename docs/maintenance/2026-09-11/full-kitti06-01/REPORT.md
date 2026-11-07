# Full KITTI 06 core rerun

1101 raw scans, source IDs 0-1100; fresh KISS-ICP, retrieval, RAP and PGO.

| Metric | Odometry | RAP + PGO |
|---|---:|---:|
| ape_unaligned_rmse (LiDAR m) | 2.777067 | 2.446184 |
| ape_aligned_rmse (LiDAR m) | 0.893350 | 0.868971 |

Keyframes: 202. Candidates/accepted: 12/12. Labels: {'safe': 12}.

Production stage wall times (seconds):

| Stage | Seconds |
|---|---:|
| sequence | 14.82 |
| odometry | 48.47 |
| loop_closure | 24.35 |
| pgo | 0.07 |
| evaluation | 11.88 |
| Pipeline total | 99.61 |
| Subprocess including startup | 100.40 |

Loop closure timing includes retrieval, model loading, hashing and inference; evaluation includes map exports. Preflight hashing warms file reads. One run, not a cold-cache or real-time latency benchmark. Separate camera-frame KITTI drift is saved in paper_metrics.json. This remains development evidence, not independent calibration.

Camera-frame KITTI all-segment drift (570 segments): translation 0.643021% ->
0.667058%; rotation 0.319708 -> 0.316593 degrees/100 m. Translation drift worsens
despite APE improvement. This is local training-sequence evaluation, not an
official benchmark submission.

All 1168 input/source hashes were rechecked; frame IDs, paths, available timestamps,
valid rotations and 12 exact measurement-to-edge associations passed. The fresh
odometry file is byte-identical to the historical KITTI 06 odometry. The optimized
file differs from the frozen replay, with APE matching to six decimals; no stronger
numerical equivalence is claimed. Maps and the diagnostic plot are retained in
the pipeline subdirectory. The plot is a run diagnostic, not a publication figure.
