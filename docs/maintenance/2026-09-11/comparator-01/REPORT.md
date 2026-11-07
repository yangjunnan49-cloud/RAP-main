# Matched ICP comparator

First-pose LiDAR APE RMSE (m); frozen frontend and candidate cohort.

| Sequence | Odometry | RAP | ICP identity (accepted) | ICP odometry (accepted) |
|---|---:|---:|---:|---:|
| poss_off | 8.257400 | 1.822264 | 1.857711 (4/4) | 1.912702 (4/4) |
| kitti06_off | 2.777067 | 2.446184 | 2.515556 (12/12) | 2.516162 (12/12) |
| kitti05 | 5.193528 | 3.417117 | 3.676126 (9/12) | 2.911334 (12/12) |
| kitti00 | 12.266655 | 11.432936 | 11.784916 (10/12) | 11.532597 (12/12) |

This development cohort is correlated and already observed. ICP odometry uses an additional pose prior. Identity ICP and RAP share no external pose prior but have different internal initialization. Results do not establish superiority over global classical registration. Runtime fields cover ICP registration only. See per-arm logs for all labels, rejected attempts and failures.

All 80 attempts completed without failure. Identity ICP produced 35 safe accepted
measurements and five dangerous rejected measurements; odometry ICP produced
40 safe accepted measurements. RAP improves over identity ICP on all four
sequences, while odometry-initialized ICP outperforms RAP on KITTI 05. These
results do not support universal RAP superiority. Different accepted edge sets
are part of this system comparison. Synthetic transform-direction, 125 input
hash rechecks and independent exact association checks for 75 edges passed.
