# O2 candidate budget comparison

Predeclared development screen passed: False. Production default unchanged.

| Sequence | Budget | Candidates / accepted | First APE m | Aligned APE m | Translation drift % | Verification s |
|---|---:|---:|---:|---:|---:|---:|
| poss | 12 | 4 / 4 | 1.822264 | 0.666054 | 1.961403 | 6.351 |
| poss | 40 | 4 / 4 | 1.822264 | 0.666054 | 1.961403 | 5.604 |
| kitti06 | 12 | 12 / 12 | 2.446184 | 0.868971 | 0.667058 | 16.935 |
| kitti06 | 40 | 40 / 40 | 2.558393 | 0.872033 | 0.672608 | 57.360 |
| kitti05 | 12 | 12 / 12 | 3.417117 | 1.129313 | 0.703737 | 18.030 |
| kitti05 | 40 | 40 / 40 | 3.487993 | 1.136006 | 0.729551 | 56.259 |
| kitti00 | 12 | 12 / 12 | 11.432936 | 2.891543 | 0.914171 | 17.268 |
| kitti00 | 40 | 40 / 40 | 10.931019 | 2.263891 | 0.913275 | 56.355 |

Drift is camera-frame for KITTI, custom LiDAR for POSS. First APE uses first-pose LiDAR alignment. Timings are warm loop verification only, not total pipeline throughput. Model startup and descriptor/retrieval/PGO costs are separate in JSON.

Both budgets regenerate measurements with seed 42 in candidate order. Candidate overlap and reference reproduction are recorded per sequence. These are development sequences; no independent risk calibration or generalization guarantee. All persisted attempts, gates, rotation validity, edge associations, saved trajectories and source hashes were checked.

## Coverage and reproduction checks

All 164 attempts across both arms were accepted and labeled safe. All 1428
source/input hashes were rechecked. Budget-12 candidate order matches each
full frontend run and first-pose APE agrees within 6.65e-7 m. All 40 common
pair transforms are exactly identical across budgets (coverage_validation.json).
Every merged candidate is from the proximity list; neither arm admits an
SC-only candidate. This motivates testing source allocation, not a claim that
source balancing will improve accuracy. Retain budget 12 as the default.
