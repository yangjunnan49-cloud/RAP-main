# Fresh loop-stage replay on frozen frontends

Uniform budget 12; one fresh registration per merged candidate; heuristic gate; NMS 0; relfloor + Huber. Odometry and keyframes are reused, not rerun.

| Sequence | Candidates | Accepted | Odom first APE m | Fresh first APE m | Odom aligned APE m | Fresh aligned APE m |
|---|---:|---:|---:|---:|---:|---:|
| poss_off | 4 | 4 | 8.2574 | 1.8223 | 2.5650 | 0.6661 |
| kitti06_off | 12 | 12 | 2.7771 | 2.4462 | 0.8934 | 0.8690 |
| kitti05 | 12 | 12 | 5.1935 | 3.4171 | 1.8686 | 1.1293 |
| kitti00 | 12 | 12 | 12.2667 | 11.4329 | 3.9385 | 2.8915 |

These naturally proposed candidates are budget-filtered and share sites/scans. They are not an independent calibration/test population. All individual events, source identities and measurements are retained.
