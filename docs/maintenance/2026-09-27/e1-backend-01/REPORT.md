# E1 bounded backend review

Decision: **NO_SUCCESSOR**.

Observed KITTI00/05/06 development evidence; no independent confirmation or novelty claim.

| Seq | Arm | Camera ter % | Aligned ATE m | First-pose APE m | Edges |
|---|---|---:|---:|---:|---:|
| 00 | O | 0.518171 | 2.754437 | 6.779069 | 12 |
| 00 | W1 | 0.515339 | 2.909611 | 6.855354 | 12 |
| 00 | W2 | 0.518171 | 2.754437 | 6.779069 | 12 |
| 00 | E1 | 0.519742 | 2.718503 | 6.754273 | 5 |
| 05 | O | 0.320473 | 1.294699 | 2.019164 | 12 |
| 05 | W1 | 0.333113 | 1.361797 | 2.184848 | 12 |
| 05 | W2 | 0.320473 | 1.294698 | 2.019161 | 12 |
| 05 | E1 | 0.326181 | 1.316927 | 2.217159 | 6 |
| 06 | O | 0.327512 | 0.332854 | 1.327196 | 12 |
| 06 | W1 | 0.330018 | 0.331090 | 1.260425 | 12 |
| 06 | W2 | 0.327512 | 0.332854 | 1.327196 | 12 |
| 06 | E1 | 0.324171 | 0.329957 | 1.338348 | 5 |

## Means and eligibility

| Arm | Mean ter % | Mean ATE m | Eligible |
|---|---:|---:|---|
| O | 0.388718 | 1.460664 | False |
| W1 | 0.392823 | 1.534166 | False |
| W2 | 0.388718 | 1.460663 | False |
| E1 | 0.390031 | 1.455129 | False |

Gate details: `decision.json`. No post-hoc arm, parameter search or combined arm.
W1 uses unit loop information with unchanged anisotropic odometry information; it is not a KISS-SLAM backend reproduction or a test of equal trust across all factors.
W2 uses the historical GNC-TLS defaults. E1 uses fixed NMS width 10. Accepted transforms are unchanged; evaluator fields were stripped before optimization.
O reproduced saved E0 trajectories within 1e-5; repeated O outputs are exactly identical. 18 validation checks passed; replay plus evaluation wall 8.687s.
Separate validator recomputed frozen metrics and independently crosschecked anchored APE and decision arithmetic. No new scans, inference, production change, Git commit or synchronization.
E0 development_baseline_v2 and historical core-baseline-v1 remain preserved. F2 requires a separate owner decision. Manuscript pause and all prior research stops persist.
