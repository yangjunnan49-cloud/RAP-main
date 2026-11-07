# LMF1 complete causal local-motion accuracy screen

Decision: **NO_CAUSAL_LOCAL_MOTION_SIGNAL**. Both GT-free bank validation and
final independent GT/decision validation pass. Stop this exact native1000-point
per-scan,three-consecutive-scan,K1/five-step layout before any trajectory trial.
No window, seed, step, density, patch, initialization, gate or selection rescue.

## Prospective question and population

Owner authorized continuing after the successful LMF0 engineering preflight.
The question is whether RAP's native joint generation of unposed neighboring
scans supplies a material local motion improvement over the saved KISS reference
and equal-scan-budget geometric controls. No within-visit estimated motion is
imposed in RAP. This is distinct from stopped confidence-response tuning, F2
within-visit group projection and M1 support-pose transport.

The synthetic evaluator/calibration/direction/serialized-rotation and positive/
negative decision-arithmetic preflight passed before output (maximum independent
error discrepancy2.257e-15). Protocol, runner, evaluator, independent validator,
helpers and293 source/input identities froze before the full bank. The census
retains all58 windows, counts22/13/5/5/7/6 on00/05/06/07/09/10; t=200,400,...
with input order[t-1,t,t-2]. Six shared t=0 structural exclusions remain. No GT
error ranking or favorable segment selection. All data are exposed development;
six engineering windows were previously generated and checkpoint membership
is unknown. This is neither held-out confirmation nor paper reproduction.

R3 has three unposed1000-point scans, R2 the same first two scans/features/noise
with lower compute. G3 has the same physical3000-point/three-scan budget as R3,
using geometric oldest->previous transport and current->pooled-map ICP. G2 is
the fixed two-scan ICP. Saved unoptimized KISS uses its historical dense causal
map and therefore more support; it is the practical system reference rather
than equal-input causal isolation. Seeds, preprocessing, safe strict344/58-key
loading, patch support, model, five-step native flow and all controls retain
the validated LMF0 definitions. No model/production default was edited.

All58 new point/feature/noise/raw/noisy endpoint/pose/control files were sealed.
All six engineering repeats match their prior arrays exactly. Independent
GT-free validation reconstructed174 scans/174000 points/5568000 descriptor
values and every noise row exactly, Horn-fit all final poses and brute-forced
all ICP controls, including support transport. Across2806 iterations this
performs2,806,000 nearest-neighbor queries and3,406,000,000 pair-distance
evaluations (counts derived from sealed traces). Maximum independent pose/control
delta2.299e-13. Saved KISS identities match the earlier temporal-audit freeze.
This complete pre-GT validation was itself sealed before actual evaluator GT.

## Material result

All58 predictions have defined finite errors. Relative transform maps current
to previous, with calibrated official LiDAR GT unchanged. Translation uses
norm(inv(T_GT) T_pred translation). Only angle calculation recovers the nearest
proper rotation from serialized error rotation; no GT/pose/label is replaced.

Pooled errors below are descriptive summaries, not the paired gate statistic.

| Arm | Mean translation error (m) | Median translation (m) | Median rotation (deg) |
| --- | ---: | ---: | ---: |
| R3 three-scan RAP |0.096011|0.094945|0.168630|
| R2 two-scan RAP |0.104382|0.098416|0.160142|
| G2 two-scan geometry |0.109422|0.094904|0.213707|
| G3 three-scan geometry |0.093903|0.078036|0.206326|
| KISS saved dense-map odometry |0.020225|0.018766|0.041501|

Gains below are medians of paired control-minus-R3 errors, not differences
between separate medians. Relative gains use the frozen1e-6m denominator floor.

| Control | Median paired gain (m) | Median relative gain | Positive signs | Gate result |
| --- | ---: | ---: | ---: | --- |
| KISS |-0.076137|-384.47%|3/58 (5.17%)|fails all three primary conditions|
| G2 |+0.008199|+7.57%|32/58 (55.17%)|fails all three primary conditions|
| G3 |-0.002817|-2.81%|27/58 (46.55%)|fails all three primary conditions|
| R2 |+0.007209|+7.01% descriptive|33/58 (56.90%)|context magnitude passes; sign fraction fails|

KISS/G2/G3 each required paired median gain>=0.01m, median relative gain>=10%
and positive fraction>=60%. R2 context required>=0.005m and>=60% positive
signs. Thus no primary control passes, and the added-context conjunction also
fails. R3 has small descriptive translation improvements over R2/G2 and lower
rotation errors than the geometric controls; these do not satisfy material
improvement over both system and matched three-scan references.

## Sequence safety and exposure limits

| Sequence | n | R3 mean translation (m) | G3 mean (m) | KISS mean (m) |
| --- | ---: | ---: | ---: | ---: |
|00|22|0.088532|0.097025|0.021376|
|05|13|0.102048|0.095382|0.018671|
|06|5|0.111472|0.123360|0.015075|
|07|5|0.069592|0.077941|0.020067|
|09|7|0.108550|0.089049|0.023074|
|10|6|0.104857|0.073666|0.020471|

All six KISS safety comparisons fail both mean-translation<=+0.01m and paired
median-rotation<=+0.05deg guards. Further failures:09 vs G3 mean translation
+0.019501m;10 vs G2 +0.041241m and paired rotation+0.078577deg;10 vs G3
translation+0.031191m. Nine of18 sequence/control conjunctions fail. Remaining
geometric safety comparisons pass. Full per-row and sequence outcomes are in
results.json; no sequence is removed or used to rescue the global decision.
Equal-sequence mean translation R3/G3/KISS=0.097509/0.092737/0.019789m is also
descriptive and does not replace frozen pooled paired gates.

This sparse local one-step screen does not measure accumulated trajectory drift,
ter/ATE benefit, a full local-odometry ceiling, or all possible RAP mechanisms.
KISS has a larger historical map. Native multi-frame generation and geometric
multi-scan estimation are prior art. Neither the small context effect nor this
negative result establishes an original algorithm or a general impossibility.

## Independent validation and cost

Final independent parser reconstructs every raw GT/calibration relative pose,
uses polar decomposition/atan2 for rotations, and reproduces all errors,
aggregates, signs, material/context/safety decisions and seal-before-GT timing.
Maximum error/aggregate delta4.417e-12. No evaluator/validator repair or failed
command was needed in this screen; previous LMF0 failure remains disclosed
in its separate immutable records, and old banks were not changed.

Successful bank65.167s, GT-free validator28.013s, evaluator5.871s and final
validator5.581s total104.632s. Peak GPU allocated1.386GiB,RSS2.605GiB;
artifacts before reports60,710,565 bytes. Original1800s/12GiB-GPU/4GiB-RSS/250MB
caps pass. Duration includes final source/bank identity rechecks; freeze and
synthetic engineering preflight are separate from the104.632s figure.

## Mainline boundary

Do not replace KISS, promote R3 to a backend/trajectory trial, or improve this
decision through a different initialization, seed, point count or window after
GT. The native local-motion question now has a traceable negative answer for
this fixed layout. A distinct RAP-specific construction still requires an
explicit causal mechanism and prior-art/matched-control design; none is selected
or frozen by this report. NEXT_ROUND_PLAN.md records that design boundary only.
The owner's original breakthrough requirement remains unresolved.

Official GT/strict labels/ter/rer/ATE and all previous negative stops persist.
No training,download/install,production/default/model/manuscript edit,full
trajectory run,commit or Git synchronization. HEADs4055d92/6d3f2d2, branches
codex/meeting-20260930 / codex/e0-f1-20260926 and all prior dirty work remain.
