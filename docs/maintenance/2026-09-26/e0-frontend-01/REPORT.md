# E0 frontend alignment: validated development comparison

Decision: **FREEZE_DEVELOPMENT_SUCCESSOR**. Selected arm: **A**.

These sequences and the prior meeting combined arm were already observed. No independent confirmation or first-tier claim.

## Fresh odometry results

| Sequence | Arm | Camera ter % | Aligned LiDAR ATE m |
|---|---|---:|---:|
| 00 | O | 0.904738 | 3.938481 |
| 00 | A | 0.513202 | 3.741265 |
| 00 | B | 0.910897 | 4.084199 |
| 00 | C | 0.521580 | 3.280262 |
| 05 | O | 0.772150 | 1.868615 |
| 05 | A | 0.330504 | 1.652975 |
| 05 | B | 0.773947 | 1.768742 |
| 05 | C | 0.340752 | 1.455239 |
| 06 | O | 0.643021 | 0.893350 |
| 06 | A | 0.279935 | 0.437263 |
| 06 | B | 0.649524 | 0.905478 |
| 06 | C | 0.281194 | 0.417194 |

O: original; A: correction only; B: KISS ranges/voxel only; C: combined.

## Selected frontend and full system

| Sequence | Odom ter % | Full ter % | Odom ATE m | Full ATE m | Accepted |
|---|---:|---:|---:|---:|---:|
| 00 | 0.513202 | 0.518171 | 3.741265 | 2.754437 | 12 |
| 05 | 0.330504 | 0.320473 | 1.652975 | 1.294699 | 12 |
| 06 | 0.279935 | 0.327512 | 0.437263 | 0.332854 | 12 |

Historical full mean: {'ter': 0.7616552167961049, 'ate': 1.6299424485429512}. New full mean: {'ter': 0.38871841553411285, 'ate': 1.460663493498114}.

Accepted historical labels: {'safe': 36}; strict correct/incorrect: 34/2. Historical safe is not strict correctness or guaranteed graph benefit.

Frontend engineering gains must not be attributed to a new RAP method. Per-sequence and odometry-to-full regressions remain visible above. Original O trajectories reproduced within the frozen tolerance.

Source/input freeze, exact frame identities, geometry, NumPy alignment crosscheck, selection arithmetic and full measurement-edge consistency passed. New source snapshot identifies uncommitted execution code. No production edits or Git synchronization.

The full-system settings are K1, five steps, candidate budget12 and NMS0. Prior HC table K4/NMS10 introductory prose was incorrect; archived artifacts were not rewritten.

E0-AMENDMENT-01: the frozen validator's unanchored NumPy ATE crosscheck exceeded its 1e-8 tolerance due to float64 gauge conditioning (5.83e-7); anchored crosscheck agrees to 4.4e-12 and frozen-code recomputation matched exactly. See AMENDMENT_01.md.

Next research task: F1 engineering preflight; no backend tuning or extra frontend sweep is authorized by these results.
