# Measured-map reoptimization: first mainline exploration

Date: 2026-10-09, Asia/Shanghai. Owner continuation: "按照你的第一条主线延伸探索".
Status: COMPLETE_WITH_PRESERVED_IMPLEMENTATION_FAILURE.
Scientific decision: NO_DECLARED_LOCAL_POINT_PLANE_SIGNAL.
Research recommendation: INVESTIGATE_SHARED_MAP_STRUCTURE_AND_REVISIT_CONSTRAINTS.

The selected direction is now an executed small geometry experiment, rather than
only a conceptual recommendation. Simultaneous adjustment of eight scan poses
against measured points runs correctly, but this conventional neighboring-scan
point-plane construction does not give a reliable pose improvement on the four
exposed development windows. Rematching alone changes little. There are useful
local map-shape gains, and a more informative finding: the same geometric loss
assigns a higher cost to the existing reference poses than to the initial poses
in every window. This shifts priority toward the observation model and map
structure before spending more iterations on this solver.

This is a narrow development result. It does not reject global map bundle
adjustment, prove an official GT defect, or establish a useful RAP contribution.
The owner relaxed originality and rigor as discovery admission criteria; the
new direction can deliberately use established map-optimization methods.

## 1. What actually ran

The prospective [protocol](PROTOCOL.md) selected four windows before new outcomes:

| Window | Original E0 A keyframe source IDs |
| --- | --- |
| 00:200 | 137,146,154,162,170,178,187,197 |
| 00:800 | 748,752,762,771,779,786,793,800 |
| 05:200 | 141,145,152,162,170,178,186,194 |
| 06:200 | 155,160,165,171,177,183,190,198 |

Thirty-two raw scans yielded 190332 retained representatives under fixed range
filtering, +0.205 degree correction, 0.5 m voxels and a 6000-point upper cap.
Even rows optimized; odd rows provided supplementary nearest-distance probes.
Twenty-neighbor normal estimation shares both sets, so probes are not independent
validation data. Acausal use of future scans was excluded at each listed boundary;
adjusting seven historical poses still introduces a window-retrospective output.

O is the saved E0 odometry projected to proper rotations and anchored at the first
window pose. F optimizes all seven other poses with initial associations fixed.
R uses the identical objective and optimizer, refreshing associations each outer
round. Both have 26 directed lag-one/two edges, 6 outer rounds x 4 inner iterations,
pseudo-Huber point-plane residuals, fixed numerical damping and backtracking.
No odometry prior, cross-visit observation, RAP call or learned parameter is used.
The algorithm is an isolated new RAP-SLAM helper; production is unchanged.

The original bank stage failed before its first optimization because orchestration
incorrectly stacked variable-length clouds. Its source/freeze/preflight/failure/
empty bank/INCOMPLETE marker remain intact. [AMENDMENT_01](AMENDMENT_01.md) changes
only list handling and numeric per-scan NPZ serialization. The canonical solver
is byte-identical. Attempt-02 reran the same numerical checks and all four windows,
then sealed all predictions and validated them before parsing numerical GT.
Original failed computation remains included in resource accounting.

## 2. Pose and local-map results

All values below are window-relative or locally aligned metrics. They are not
whole-sequence KITTI ter/rer or full-trajectory ATE. Translation is anchored
relative translation RMSE; rotation is mean relative angle. ATE rigidly aligns
eight positions and can absorb a global orientation difference.

| Window | O translation / rotation | F translation / rotation | R translation / rotation | O aligned ATE -> R aligned ATE |
| --- | --- | --- | --- | --- |
| 00:200 | 0.899403 m / 0.494756 deg | 0.868305 / 0.523014 | 0.864689 / 0.523928 | 0.080207 -> 0.062583 m (-21.97%) |
| 00:800 | 0.183091 / 0.204605 | 0.183625 / 0.188320 | 0.184590 / 0.186058 | 0.056836 -> 0.049898 m (-12.21%) |
| 05:200 | 0.198449 / 0.259764 | 0.222424 / 0.325502 | 0.224503 / 0.327945 | 0.059114 -> 0.063305 m (+7.09%) |
| 06:200 | 0.226504 / 0.034546 | 0.209329 / 0.093015 | 0.198301 / 0.106112 | 0.041382 -> 0.040675 m (-1.71%) |

Both F and R score **0/4** on the prospective >=5% translation improvement plus
nonworsening rotation signal, and **0/4** on >=5% supplementary probe improvement.
R's probe mean-distance changes are +0.0232%, -0.0106%, -0.0956%, -0.0137% gains
in table order. Only 00:200 improves this probe, by a very small amount.

R improves translation in two windows, aligned-position ATE in three, and mean
rotation in one. In 06:200 its 12.45% translation gain accompanies rotation rising
from 0.034546 to 0.106112 degree. Do not describe this as no beneficial change
whatsoever, or select ATE after seeing results to turn the frozen signal into PASS.
The complementary metrics show a tradeoff worth understanding; centimeter-scale
eight-position aligned ATE is insufficient to promote a full mapping method.

Maximum pose corrections stay inside the frozen bounds: R translation 0.053344
to 0.079491 m and rotation 0.116912 to 0.423804 degree across the four windows.
The correction is modest rather than a recovered large-drift/relocalization event.
F/R similarity weighs against rematching itself as the missing breakthrough here.

## 3. What the post-outcome diagnosis adds

The separate [diagnosis scope](OBJECTIVE_DIAGNOSIS_SCOPE.md) is explicitly post-hoc
and executes **zero optimizers**. It evaluates existing poses and reference poses
under the same loss, including a five-point interpolation from R to the reference.
It cannot rescue this pilot or become an independent accuracy claim.

| Window | Initial O fixed-association cost | Reference cost on same associations | Reference/O ratio | R fresh-association cost / reference fresh-association cost |
| --- | --- | --- | --- | --- |
| 00:200 | 0.087801 | 0.207502 | 2.3633 | 0.084678 / 0.191461 |
| 00:800 | 0.109336 | 0.156852 | 1.4346 | 0.106425 / 0.153052 |
| 05:200 | 0.137639 | 0.157104 | 1.1414 | 0.133805 / 0.154989 |
| 06:200 | 0.160227 | 0.165759 | 1.0345 | 0.159564 / 0.165233 |

The fixed-association column is a common objective comparison. Fresh association
columns have different support selections and are only supplementary. Fixed
final-R costs along all four recorded interpolation curves also increase toward
the reference after the initial neighborhood. The final R gradient's reference
direction slopes are approximately -1.11e-5, -2.92e-13, +5.54e-7, +1.33e-6;
small slopes are consistent with a local stationary geometric solution, not proof
of the globally best or physically correct pose. Normalized Hessians have all
42 non-anchor dimensions above 1e-6, minimum eigenvalues 0.01186--0.02047.
Full rank does not establish reliable information or calibrated uncertainty.

These results support the inference that **more iterations on this identical
objective are a weak next investment**. A correctly reduced geometric loss can
move away from the trajectory reference. That conflict could reflect biased
normals/associations, repeated correlated returns, observation preprocessing,
reference limitations or combinations of them. This experiment does not identify
which explanation is true. In particular, it supplies no proof that official
KITTI GT, calibration, or all point-plane optimization is invalid.

## 4. How I would extend the mainline now

The stronger version of direction one is jointly estimating shared map structure
and scan poses, including observations from revisits. This pilot only optimizes
neighboring scan poses while treating each target's sampled normal as a local
surface. It has no common latent map feature, no distant revisit, no full sequence
and no observation independent of the original local neighborhood.

My preferred next mechanism is conventional shared-plane/point-cluster bundle
adjustment: multiple scans observe the same plane, and the map plane is estimated
jointly with poses rather than trusting one scan's PCA plane. BALM provides an
established formulation that eliminates plane/edge geometry analytically and
uses compact point-cluster statistics. This is a legitimate engineering starting
point under the new owner objective, not an original method claim.
[BALM paper](https://arxiv.org/abs/2209.08854),
[author implementation](https://github.com/hku-mars/BALM).

Build this in the existing numerical environment first. Installing a ROS-based
system is not needed to test the essential shared-structure hypothesis. Restore
a declared, bounded motion constraint from the strong corrected frontend in the
new formulation; this pilot intentionally had none. Correlation with point-cloud
observations means that adding such a constraint is not automatically a valid
probabilistic fusion or uncertainty claim.

Then test two revisiting submaps while retaining their internal scan poses. A
single rigid submap-to-submap pose would repeat the existing compressed-factor
problem. Hold existing candidate identities and the initial geometry alignment
fixed for the first map comparison. RAP should enter later as an alternative
initialization for geometrically difficult revisits under the same refinement,
not as a replacement for the strong ordinary odometry.

The [next-round design](NEXT_ROUND_PLAN.md) lays out these distinct stages, a
small declared development search, a proposed ATE-primary system test with
visible ter/rer safety and a clear limit on conclusions. No new shared-map arm
or complete-sequence protocol is implemented, frozen or automatically executed.

## 5. The missing details are now more precise

| Unknown | Why it matters | Next discriminating observation |
| --- | --- | --- |
| Stability of a shared surface across scans | Single-scan PCA planes may be biased while still producing a full-rank Hessian | Multi-scan plane membership, per-scan mean offset and leave-one-scan-out prediction |
| Reference frame/time and point preprocessing provenance | Arithmetic agreement does not establish physical alignment to the sensor observation | Existing calibration/timestamp provenance and separate spatial residual patterns; no automatic GT correction |
| Common local drift versus revisit-correctable drift | Neighboring scans can share the same bias and still align well | A joint two-visit map test that keeps internal poses and actual common structures |
| Effect of a strong motion constraint | Free point-plane fitting trades translation and rotation | Distinct shared-map formulation with a declared motion constraint and full displayed tradeoffs |
| Which observations add independent information | Repeated returns and shared PCA supports undermine naive confidence counting | Per-scan feature contribution and held-out scan/region geometry checks |
| Metric relevance at sequence scale | Aligned small-window ATE absorbs orientation and cannot predict ter | Prospective ATE-primary full development test with unchanged official ter/rer and runtime |
| Remaining geometric capture basin and incremental RAP role | Current initial poses are already close and rematching adds little | Identical refinement for geometry/RAP initializations on specified difficult revisits |

Do not invent azimuth point times as the next fix. The CT-ICP authors explicitly
distinguish motion-compensated KITTI benchmark clouds from KITTI raw clouds with
meaningful relative point times. Our historical synthetic deskew route also
degraded results. Local dataset provenance is not established merely by a folder
named `data_odometry_velodyne`, but this literature and the old result weigh
against applying another unverified compensation.
[CT-ICP author README](https://github.com/jedeschaud/ct_icp/blob/master/readme.md).

## 6. Validation, cost and preserved boundaries

Synthetic checks pass: finite-difference Jacobian maximum 2.1688e-9, gauge
invariance, exact-pose no-op, known-correspondence recovery maximum 6.6613e-16,
and the intentionally invisible 0.2236 m planar translation with rank three.
Real-bank checks pass: independent world residual delta 2.5455e-13, selected
real Jacobian delta 8.0932e-9, independently reconstructed first scan per sequence
delta 1.4211e-14, selected normal projectors 8.8818e-16, world-coordinate probe
delta 2.6645e-14. Pose metrics independently agree to 2.5868e-14. A separate world
formula checks 52 post-hoc cost records to 1.1546e-14.

This is bounded mathematical/source verification, not a full independent replay
of every raw scan, association or optimizer update. The original 54-entry and
attempt-02 61-entry freezes remain; no scientific source was edited after freezing.

Eleven recorded stages, including original failed computation and post-hoc checks,
total 13.681322 s; peak RSS is 107728896 bytes (about 0.1003 GiB), no GPU. Artifacts
are about 9.2 MiB, comfortably below the new 1800 s/2 GiB/512 MiB caps. These
timers start after module imports and exclude WSL startup, reading/design work and
documentation; they are not end-to-end or production latency benchmarks.

Both original repositories retain their HEADs/branches and tracked dirty sets
(main 2, RAP-SLAM 9). No model/checkpoint load, learning, new RAP inference,
full trajectory, official metric replacement, acquisition/install, production/
default/backbone/manuscript change, commit or Git sync occurred. Old scientific
seals/stops, checkpoint/site/exposure unknowns and the 09 discrepancy remain.
