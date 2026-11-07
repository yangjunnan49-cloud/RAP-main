# M2 saved-trajectory metric comparison

Historical edges and trajectories are unchanged. New metrics are not a full repaired-inference experiment.
APE is the LiDAR first-pose/aligned convention. KITTI camera drift is separately reported.
Live frame identity uses an explicit historical contiguous-index assumption; see JSON bindings.

| Run | Trajectory | First APE m | Aligned APE m | Legacy LiDAR ter % | V2 LiDAR ter % | Camera ter % | Segments |
|---|---|---:|---:|---:|---:|---:|---:|
| poss_off | odometry | 8.2574 | 2.5650 | 3.5891 | 3.8592 | — | 217 |
| poss_off | pgo | 1.8209 | 0.6654 | 1.3148 | 1.9623 | — | 217 |
| kitti06_off | odometry | 2.7771 | 0.8934 | 0.5829 | 0.6422 | 0.6430 | 570 |
| kitti06_off | pgo | 2.4410 | 0.8689 | 0.6061 | 0.6663 | 0.6671 | 570 |
| kitti05 | odometry | 5.1935 | 1.8686 | 0.7636 | 0.7714 | 0.7722 | 1806 |
| kitti05 | pgo | 3.4171 | 1.1285 | 0.6879 | 0.7033 | 0.7039 | 1806 |
| kitti00_bb | odometry | 12.2667 | 3.9385 | 0.9023 | 0.9043 | 0.9047 | 3283 |
| kitti00_bb | pgo | 10.9197 | 2.2636 | 0.9095 | 0.9126 | 0.9131 | 3283 |
| step3_poss_current | odometry | 8.2574 | 2.5650 | 3.5891 | 3.8592 | — | 217 |
| step3_poss_current | pgo | 1.7571 | 0.6506 | 1.3229 | 1.9830 | — | 217 |
| step3_kitti02_current | odometry | 31.6397 | 7.9534 | 1.2342 | 1.2275 | 1.2285 | 3453 |
| step3_kitti02_current | pgo | 26.0181 | 4.0350 | 1.2370 | 1.2327 | 1.2336 | 3453 |
| step3_kitti06_current | odometry | 2.7771 | 0.8934 | 0.5829 | 0.6422 | 0.6430 | 570 |
| step3_kitti06_current | pgo | 2.5815 | 0.8934 | 0.6315 | 0.6950 | 0.6959 | 570 |
| step3_kitti03 | odometry | 4.4279 | 0.8792 | 1.1190 | 0.9402 | 0.9411 | 184 |
| step3_kitti03 | pgo | 4.4279 | 0.8792 | 1.1190 | 0.9402 | 0.9411 | 184 |
| step3_kitti04 | odometry | 2.9573 | 0.4017 | 1.0639 | 0.9273 | 0.9301 | 43 |
| step3_kitti04 | pgo | 2.9573 | 0.4017 | 1.0639 | 0.9273 | 0.9301 | 43 |
