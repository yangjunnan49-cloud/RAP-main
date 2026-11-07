# Shared-plane mainline progress: support preservation is the next concrete issue

Owner continuation: "继续主线推进". Date: 2026-10-09 (Asia/Shanghai).
Status: VALIDATED_EXPLORATORY_COMPLETE.
Decision: NO_ELIGIBLE_SHARED_PLANE_REVISIT_CANDIDATE.
Research finding: HALF_SPLIT_AND_CAPPING_REDUCE_SHARED_SURFACE_SUPPORT.

The shared-plane/motion-constraint prototype is implemented and executed. A
useful next issue has been located in the experimental representation: splitting
every retained scan into alternate training/probe rows severely reduces the
number of supported cross-scan surfaces. Restoring the already retained points
changes 2m shared-feature counts from 10/10/2/0 to 106/132/52/51 and makes all four
support checks pass. No new accuracy benefit is established by that count-only
comparison. The sparse-pilot pose results remain modest and ineligible.

This is a more actionable information gap than another iteration/threshold
sweep: preserve local surface evidence during map fitting and move geometric
validation to complete patches/scans. It does not establish a breakthrough,
explain every old negative, or demonstrate useful dense-map optimization yet.

## 1. Fixed experiment and actual outcome

The [protocol](PROTOCOL.md) froze two scales,2m/4m, before new outputs. Input is
exactly MMR0's four eight-scan banks and O poses:00:200,00:800,05:200,06:200.
These are exposed development data. No new raw points entered this optimization.

Multiple scans contribute point clusters to a common plane. Equal mass per
contributing scan defines a pooled covariance; its minimum eigenvector/value
gives the analytic plane and its residual variance. Planes are refit during every
cost evaluation. A compact-moment Gauss-Newton system eliminates normal tangent
and offset nuisance variables with a Schur complement. This is a conventional
BALM-inspired prototype, not the full BALM second-order solver or an original RAP
mechanism. [BALM](https://arxiv.org/abs/2209.08854).

G uses shared geometry alone. P adds adjacent relative E0 motion constraints with
fixed engineering scales .10m/.15deg. Those are correlated regularizer strengths,
not calibrated independent sensor noise. First pose anchored;24updates; same
fixed damping/step limits/backtracking in both arms. Feature memberships stay
fixed at O, while the common surface itself changes with poses.

Training uses even rows only. Unlike MMR0, no odd row enters feature selection,
moments or plane fitting. A feature needs>=3scans,>=6points per contributing scan,
>=40points total and the frozen flatness/mean-offset criteria. At least10features
and100training points per scan are required to optimize that representation.

| Window | 2m features / minimum per-scan points | 4m features / minimum per-scan points | 4m outcome |
| --- | --- | --- | --- |
| 00:200 | 10 / 6 | 23 /187 | G correction2.150m invalid; P valid |
| 00:800 | 10 /26 | 38 /193 | G correction3.475m invalid; P valid |
| 05:200 | 2 /6 | 25 /91 | Support invalid; no G/P optimization |
| 06:200 | 0 /0 | 50 /363 | G correction1.195m invalid; P valid |

All eight window/scale representation records were sealed. Five were invalid
before optimization, leaving three G and three P numerical outputs. G fails the
frozen1m correction bound in all three; all poses/metrics are retained and clearly
marked invalid. There is no substituted baseline/fallback. Thus only three of
six generated optimized outputs are valid, and neither scale has all four valid
P windows. No representation is eligible for revisit design under the protocol.

## 2. What the motion constraint did and did not achieve

| 4m window | O aligned local ATE -> P | ATE gain | tRMSE gain | Mean rotation change |
| --- | --- | --- | --- | --- |
| 00:200 | .080207 -> .078874m | +1.661% | +.028% | -.000078deg |
| 00:800 | .056836 -> .054546m | +4.030% | -1.020% | +.005715deg |
| 06:200 | .041382 -> .041332m | +.121% | -.545% | +.004976deg |

P's maximum corrections are .008891--.013115m and .009104--.018288deg; it limits
the large free-geometry corrections. All three valid P windows show small aligned
ATE and odd-point/leave-one-scan-out geometry improvements. Mean fractional ATE
gain on these three is about1.94%,below the prospective5% criterion even before
accounting for the unsupported05window. Lowering its91-point support floor alone
would therefore not establish the required benefit. Rotation changes are within
the new .02deg development margin but not uniformly improvements.

These are eight-position aligned local metrics, not complete-sequence ATE or
KITTI ter/rer. Initial geometry cost at reference poses is5.563/2.224/1.062times
O on the three valid representations. Shared planes did not remove the earlier
objective/reference conflict. Plane membership and flatness were selected at O,
so this cost contrast is itself subject to initialization/selection bias. It does
not prove official GT incorrect or identify the physical cause.

## 3. Post-outcome support diagnosis

Two separately frozen count-only diagnostics run **zero optimizers** and compute
**no new pose-reference errors**. They cannot repair SMP1, validate a dense pose
method or consume former probe rows as an independent accuracy test.

The first compares old even-row points with an exact superset: all first-return
.5m voxel representatives after unchanged range/vertical correction, before the
6000cap and half split. The second adds all existing retained MMR0 points as an
intermediate scenario, separating those two losses of support. Every one of the
190332 retained points is checked unchanged in the full voxel superset,maximum
coordinate delta0. Source raw hashes match the original MMR0 identities.

| Window | 2m features: even-only | All retained points | Full .5m voxel superset |
| --- | --- | --- | --- |
| 00:200 | 10, unsupported | 106, supported |119, supported |
| 00:800 | 10, unsupported |132, supported |209, supported |
| 05:200 | 2, unsupported |52, supported |155, supported |
| 06:200 | 0, unsupported |51, supported |392, supported |

At4m the corresponding counts are23/38/25/50,then38/55/38/86,then42/59/46/151.
All-retained and full-voxel representations meet the same support rules in all
four windows at both scales. Restoring the odd rows alone already clears the
support failures. The6000cap further removes useful possible shared features,
especially in06, but the half split is a major factor here; attributing the entire
problem to the cap or to the network's token limit would be incorrect.

The32rawscans contain3917623points;range filtering keeps3917377;.5m voxels keep
286638representatives. SMP1 trained on95168points from the old190332retained bank.
This roughly threefold point-count difference can produce a much larger change
in qualifying surface count because thresholds require shared multi-scan support.

Normal-direction spread also improves in the denser census. For06at4m, the
minimum eigenvalue of the unit-normal scatter matrix rises from.000163 to.043442.
This describes surface orientation diversity, not pose observability or a
calibrated information increase. Additional points can also add mixed surfaces
or moving objects; support availability alone cannot predict accuracy.

These count diagnostics reuse the same feature implementation; they are source-
bound census computations with exact superset checks, not an independent full
feature-census reproduction. The optimizer's selected compact moments/costs are
independently checked using explicit raw point sums as described below.

## 4. Next mainline and the remaining unknowns

The next distinct map pilot should preserve all points within a chosen surface
cluster and hold out complete patches/scans for geometry checks. Start with the
already retained point bank and2m patches to isolate the half-split effect; do
not require millions of raw returns merely to repeat a count test. Compact
moments permit retaining geometry without giving every point to a neural model.

Keep the motion regularizer and its current strengths initially. A fresh
protocol must report every result and declare the new structural holdout before
optimization. Do not promote the count-only scenario or call it an independent
test. If useful, proceed to a specified actual revisit while keeping both maps'
internal poses. RAP alternative initialization remains later and must share the
same measured-geometry refinement.

[NEXT_ROUND_PLAN](NEXT_ROUND_PLAN.md) specifies this recommendation. No new dense
optimization, additional representation/parameter sweep, two-visit candidate or
complete trajectory was run automatically after the SMP1 failure.

The outstanding questions are now sharper:

- Can supported planes move poses toward the reference rather than only reduce
  their own variance? Initial-membership/flatness bias still matters.
- Which patch/scan holdout preserves structure yet gives a meaningful geometry
  check, and does not simply reproduce the same correlated evidence?
- How much regularization is required after structure is retained? Current
  strength prevents drift but the gain is small; it is not a measured covariance.
- Will real revisits add information unavailable from neighboring scans sharing
  a common drift? This turn still has no cross-visit observations.
- Do sensor/reference time, calibration and point preprocessing physically agree?
  Arithmetic checks alone cannot settle that; no synthetic deskew/GT repair.
- Can any local change improve whole-sequence mapping under unchanged official
  ter/rer and a stated ATE-primary safety rule? No system claim yet.

## 5. Validation and preserved boundaries

Preflight passes: compact versus explicit-point Hessian1.4211e-14/gradient9.1038e-15;
geometry/combined objective FD3.9524e-9/7.3896e-9;relative-prior Jacobian5.4875e-8;
gauge6.2172e-15;perfect no-op/three-plane recovery8.8818e-16;planar translation
blind spot remains rank3. Real-bank moments reconstruct exactly,explicit plane
cost5.1806e-14,odd probe2.3592e-16,selected real geometry FD6.5620e-10. Independent
pose metrics agree to2.5896e-14 and gates/selection reproduce.

No full optimizer replay was required. The28-entry source/input freeze includes
immutable source snapshots; all8representation files and summary seal before new
GT evaluation. No implementation failure or source repair occurred this round.
Two post-hoc analyses are separately bound and do not alter frozen outcomes.

See RESOURCE_AUDIT.json for all eight recorded CPU stages,including both census
stages. Caps1800s/2GiB/512MiB pass;noGPU. Timers exclude imports/WSLstartup/design/
documentation and are not production latency. Both original repositories retain
HEADs/branches and2/9tracked dirty sets. Only new isolated helper/maintenance
scripts/docs and mutable handoffs. No model/checkpoint load,training,RAPinference,
fulltrajectory,officialGT/metric replacement,acquisition/install,production/
default/backbone/manuscriptedit,commit/Gitsync. All old scientific banks/stops and
09/checkpoint/site/exposure unknowns persist;original breakthrough unachieved.
