# F1 structured-motion generation: engineering preflight

Decision: **PASS_ENGINEERING**.

This is a four-pair engineering result on observed KITTI00 data. It is not an efficacy screen, novelty clearance or independent confirmation.

## Implementation and fixed controls

An isolated RAP-SLAM sampler retains six scan-specific partitions and projects each visit into a common short-motion group at each clean-endpoint step. Upstream RAP and production defaults were not edited; no hooks or monkeypatches were installed.

The four exact pairs are 24/629, 210/1656, 422/3496 and 956/3859. Each uses two 2000-point anchors and four 1000-point supports. Saved causal within-visit LiDAR motion is the only motion input; GT is loaded only by a separate post-generation local-motion evaluator.

| Arm | Role | Points | Sampling wall sum over 4 pairs (s) |
|---|---|---:|---:|
| N | Native six-part | 8000 | 3.023702 |
| F | Final-only group projection; extra cost after reusing N | 8000 | 0.008400 |
| S | Group projection at every step | 8000 | 2.269114 |
| P | Matched-point pooling, reused scan descriptors | 8000 | 2.249285 |
| A | Anchor-only reference, not equal-data | 4000 | 1.243833 |

All use K1/five Euler steps. N/F/S share identical points, descriptors, normalization and noise. Pooling changes normalization and partitioning while retaining the same points/descriptors. F timing is incremental projection cost, not standalone inference latency. Timings are engineering measurements, not a speed-superiority claim.

## Correctness and resources

- Native sampler reproduction maximum endpoint/state delta: 0.
- Independent float64 projected-point maximum delta: 4.79249295e-07 normalized units.
- Independent decoded pose maximum matrix delta: 4.37462029e-06.
- Independent projected local-motion maximum matrix residual: 4.366143e-10.
- Process wall including model loading and preprocessing: 24.943s; peak allocated: 2.418GiB; peak reserved: 4.734GiB.
- Proper rotations, finite tensors, exact point budgets, normalization roundtrip, reordered replay and precision/RNG restoration checks passed.
- Raw versus projected clean endpoints and noisy trajectories are explicitly saved. Zero constraint residual is enforced geometry, not registration confidence.

## Estimated-motion sensitivity

Fixed support-only perturbations on the ordinary pair: jointly +/-0.10m x translation and +/-1 degree yaw. Relative to unperturbed S:

| Perturbation | Output translation change m | Output rotation change deg |
|---|---:|---:|
| Sminus | 0.167551 | 0.046343 |
| Splus | 0.164784 | 0.050451 |

Evaluator-only local-motion error over16 supports: maximum translation 0.098383m; maximum rotation 0.339194deg.

These are sensitivity observations, not accuracy or robustness gains. No loop transform was scored against GT. No strength/layer/gate search or learned selector was run.

## Next boundary

F1 establishes executability only. Freeze a separate F2 development protocol with exact cohort exposure, corrected-data convention, K4 seeds, decision margins, common gate, cost and strong comparator before any efficacy outcome. Fresh confirmation is still required. All previous HL/SC/PG stops persist; manuscript remains paused.
