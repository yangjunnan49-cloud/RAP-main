# Matched ICP comparator

First-pose LiDAR APE RMSE (m); frozen frontend and candidate cohort.

| Sequence | Odometry | RAP | ICP identity (accepted) | ICP odometry (accepted) |
|---|---:|---:|---:|---:|
| poss | 8.257400 | 1.822264 | 1.857711 (4/4) | 1.912702 (4/4) |
| kitti06 | 2.777067 | 2.533434 | 2.576697 (12/12) | 2.581416 (12/12) |
| kitti05 | 5.193528 | 3.214084 | 3.179688 (9/12) | 3.137198 (12/12) |
| kitti00 | 12.266655 | 10.336943 | 10.512414 (11/12) | 10.567533 (12/12) |

This development cohort is correlated and already observed. ICP odometry uses an additional pose prior. Identity ICP and RAP share no external pose prior but have different internal initialization. Results do not establish superiority over global classical registration. Runtime fields cover ICP registration only. See per-arm logs for all labels, rejected attempts and failures.

Full aligned-APE and camera/LiDAR drift tables, acceptance interpretation and
thesis claims are consolidated in [thesis results](../paper-evidence-v2/RESULTS.md).
All 80 attempts completed; all 76 accepted edges are safe. The four dangerous
identity-ICP results were rejected. Persisted-output checks passed before the
INCOMPLETE marker was removed; see association_validation.json.
