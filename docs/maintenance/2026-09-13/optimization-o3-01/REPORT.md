# O3 source allocation comparison

Predeclared development screen passed: False. Production default unchanged.

| Sequence | Policy | Candidates / accepted | First APE m | Aligned APE m | Translation drift % | Verification s |
|---|---:|---:|---:|---:|---:|---:|
| poss | proximity_priority | 4 / 4 | 1.822264 | 0.666054 | 1.961403 | 6.351 |
| poss | balanced_6_6 | 4 / 4 | 1.822264 | 0.666054 | 1.961403 | 5.254 |
| kitti06 | proximity_priority | 12 / 12 | 2.446184 | 0.868971 | 0.667058 | 16.935 |
| kitti06 | balanced_6_6 | 12 / 12 | 2.533434 | 0.862829 | 0.663797 | 12.485 |
| kitti05 | proximity_priority | 12 / 12 | 3.417117 | 1.129313 | 0.703737 | 18.030 |
| kitti05 | balanced_6_6 | 12 / 12 | 3.214084 | 1.168216 | 0.715824 | 11.657 |
| kitti00 | proximity_priority | 12 / 12 | 11.432936 | 2.891543 | 0.914171 | 17.268 |
| kitti00 | balanced_6_6 | 12 / 12 | 10.336943 | 2.109192 | 0.896651 | 12.603 |

Drift is camera-frame for KITTI, custom LiDAR for POSS. First APE uses first-pose LiDAR alignment. Timings are warm loop verification only, not total pipeline throughput. Model startup and descriptor/retrieval/PGO costs are separate in JSON.

O2 baseline is reused; the balanced arm regenerates measurements with seed 42 in selected order. Baseline timings are earlier O2 observations. Candidate overlap and reference reproduction are recorded per sequence. These are development sequences; no independent risk calibration or generalization guarantee. All persisted attempts, gates, rotation validity, edge associations, saved trajectories and source hashes were checked.
