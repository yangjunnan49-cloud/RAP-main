# MDC0: why aligned positions and segment ter can disagree

Status **VALIDATED_ACCOUNTING**, evaluator-only and post-hoc to the observed LC0 pattern. It is not a new method, metric replacement or calibrated uncertainty result.

## Concrete finding

The development H oracle lowers both component energies under BOTH compulsory gauges, while total mean squared segment translation error increases. Its negative orientation/chord cross term becomes substantially less negative. Under aligned gauge A, P shows the same pattern. Thus lower aligned position error does not imply lower segment ter, and blaming only worse orientation is unsupported.

The exact identity is z=u+v and ||z||^2=||u||^2+||v||^2+2u dot v. z is the unchanged official segment translation error divided by nominal length. u is orientation-associated, v is endpoint-chord-associated. Rotation and translation errors can cancel. These are signed descriptive terms, not independent physical causes, covariance or nonnegative error shares.

## Complete cohort accounting

Units below are mean squared segment fractions times10000 (%^2), averaged equally across sequences within each cohort. Total is not the square of mean ter. F uses original first-pose gauge; A additionally rigidly aligns estimated camera positions, without scale or subsequent re-anchoring. A does not replace LiDAR ATE.

| Cohort | Gauge | Arm | Orientation | Chord | Signed cross | Total |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| development | F | N | 0.879030 | 0.591752 | -1.170708 | 0.300074 |
| development | F | C | 0.800778 | 0.563279 | -1.062552 | 0.301505 |
| development | F | P | 0.681079 | 0.714346 | -0.997632 | 0.397793 |
| development | F | H | 0.427373 | 0.189810 | -0.202276 | 0.414908 |
| development | A | N | 0.409658 | 0.285319 | -0.394903 | 0.300074 |
| development | A | C | 0.396606 | 0.277667 | -0.372768 | 0.301505 |
| development | A | P | 0.361041 | 0.087240 | -0.050489 | 0.397793 |
| development | A | H | 0.376807 | 0.090316 | -0.052215 | 0.414908 |
| transfer_exposed | F | N | 0.295638 | 0.268737 | -0.227214 | 0.337161 |
| transfer_exposed | F | C | 0.341992 | 0.315730 | -0.321132 | 0.336589 |
| transfer_exposed | F | P | 0.357086 | 0.259229 | -0.277315 | 0.339000 |
| transfer_exposed | F | H | 0.357086 | 0.259229 | -0.277315 | 0.339000 |
| transfer_exposed | A | N | 0.275837 | 0.166405 | -0.105081 | 0.337161 |
| transfer_exposed | A | C | 0.278949 | 0.142733 | -0.085093 | 0.336589 |
| transfer_exposed | A | P | 0.278482 | 0.141319 | -0.080801 | 0.339000 |
| transfer_exposed | A | H | 0.278482 | 0.141319 | -0.080801 | 0.339000 |

Aligned development N->H: orientation.409658->.376807, chord.285319->.090316, cross-.394903->-.052215, total.300074->.414908. Reductions in the first two terms are outweighed by the loss of cancellation. In F the components have different numerical values, while the same total/ter is preserved. Components must not be interpreted as unique causal shares.

P transfer mean ter improves slightly while mean squared segment error increases (.337161->.339000), showing why squared accounting cannot silently replace the official mean-norm criterion. All official LC0 metrics/gates remain exactly as validated.

## Source and independent validation

72 identities froze before52 NPZs:48 sequence/arm/gauge arrays and4 fixed analytic fixtures. All59184 segment-gauge vectors reconstruct independently from full4x4 relative errors; all29592 original segment identities and ter values remain. Native Kabsch alignment independently reproduces by Horn quaternion eigenanalysis (maxdelta1.705e-13); maxvector4.123e-15, maxsummary2.325e-14. Total gauge invariance and signed accounting closure pass. No failure/repair.

Fixtures include perfect, chord-only, orientation-only and constant-global-rotation cancellation. The last has nonzero component terms but zero total error, preventing an orientation component from being mistaken for an independently harmful measurement.

Successful stages4.878s,peak0.046GiB;1h/4GiB/100MiB caps pass. Only sealed LC0 trajectories and unchanged evaluator GT/calibration are read; no graph/inference/new feature/head/fit or new trajectory.

## Next decision

Prioritize a distinct source of accurate coupled local relative motion. TR0 is a four-window GT-free extraction/invariance preflight for the already inspected512-D joint-token interface, PLANNED_NOT_IMPLEMENTED. It can establish a source hook, not learnability. A later physically grounded small readout needs explicit fitting scope, matched trained descriptor/independent-token controls, both rotation and translation plus actual ter/ATE, and honest data exposure. See NEXT_ROUND_PLAN.md.

The accounting does not prescribe a new weight/uncertainty matrix, prove a backend defect, identify individual-edge causal effects, license old interpolation/shape/R3/feedback rescues or establish RAP originality.09 physical discrepancy and unknown checkpoint membership remain. No training, production/default/model/manuscript edit, acquisition/install, commit/Git.
