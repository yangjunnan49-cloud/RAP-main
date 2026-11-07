# Controlled backend ablation

First-pose LiDAR APE RMSE (m). Same fresh edges and frozen frontend in every arm.

| Sequence | Odometry | Fixed | Fixed + Huber | Relfloor | Relfloor + Huber |
|---|---:|---:|---:|---:|---:|
| poss_off | 8.257400 | 1.821846 | 1.821781 | 1.822331 | 1.822264 |
| kitti06_off | 2.777067 | 2.446192 | 2.446184 | 2.446192 | 2.446184 |
| kitti05 | 5.193528 | 3.417115 | 3.417117 | 3.417115 | 3.417117 |
| kitti00 | 12.266655 | 11.432937 | 11.432936 | 11.432937 | 11.432936 |

All four default-arm trajectories reproduce core-replay-01 within 1e-8 absolute tolerance. All 40 input edges are labeled safe; this is not a false-loop robustness test.
