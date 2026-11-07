# RAD1: raw endpoint association decoder development screen

Owner authorized planning, handoff and execution on 2026-10-07. This is a
distinct final-output decoder study, not D1/D2, FDI1, D0 or R0 rescue.
All earlier stops and sealed artifacts remain unchanged. No training, neural
inference, production/default/model/manuscript change, download or Git sync.

## Question and data

Can final pre-rigidification RAP coordinates propose useful cross-view row
associations for a pose fit on original measured points, beyond rigid-projected
coordinates, miniSpinNet descriptors and geometric re-selection of native poses?

Use all original100 F2 pairs each on00/08, saved order, exposed development.
Reuse exact six-part inputs, anchor parts0/3, four original N generations and
C1 features. Only final endpoints are associated. No step/noise/window/point/
feature change or cohort replacement. Parent hash seals and independent
validations bind arrays. Actual data inputs are the saved anchor rows; support
parts influenced inherited RAP outputs but are not new fitting observations.

Freeze this protocol, algorithm, runner, independent validator, manifest,
parent seals, GT/stratum file hashes and all used source/input identities before
any synthetic or real output. GT/stratum files are byte-hashed only at freeze;
their values are parsed only after the complete GT-free bank and GT-free
independent validation seal. No model/checkpoint loading is needed.

## Fixed construction

Four association arms R/P/D/Z, each with four generation slots:

- R: final raw endpoints for anchors0/3, multiplied by saved global scale.
- P: double-precision proper per-anchor rigid fits of original points to those
  same raw endpoints, then the resulting rigid images. This is the essential
  native-pose geometric matching control; numerical bridge to saved N is checked.
- D: saved unit miniSpinNet descriptors on identical anchor rows. Four identical
  descriptor slots are reported honestly; no independent samples are invented.
- Z: R coordinates independently permuted within each anchor by a PCG64 seed
  from SHA256('RAD1|pair|generation'), retaining original input row identity.
  This is an identity-destruction diagnostic, not an efficacy comparator.

For each representation, Euclidean top3 target neighbors and top3 source
neighbors must agree. Sort the mutual-top3 pairs by representation distance,
then persistent original row IDs, retain at most512. No distance cutoff or
point saliency threshold. Top3 ties use row IDs; no post-result top-k rescue.
Coordinates and descriptors are float64 for distances. Original physical
points, not generated positions, are the solver's source/target measurements.

Build an undirected compatibility graph: distinct target and source rows,
absolute difference between their interpoint distances <=1.0m. Diagonal is
excluded. Rank seeds by descending degree, representation distance and row
IDs; use the first32. For each seed, greedily add the highest-ranked compatible
remaining vertex, intersecting its compatibility set, until no vertex remains
or64 vertices are included. Fewer than3 vertices or centered source/target
second singular value <=1e-6 of the first is a degeneracy rejection.

Fit original source->target points by proper unweighted Kabsch. Perform three
consensus/refit iterations with correspondence residual <=1m, rejecting fewer
than3/noncollinear supports. Score valid proposals by descending final inlier
count, ascending mean min(residual,1)^2 rounded to12 decimal places solely
for numerical tie stability, then seed rank. Keep one pose per
generation. This is established robust geometry, not the novelty claim.
If no valid proposal exists, retain that generation's original native pose
and flag fallback. Failure counts remain in all denominators.

## GT-blind selection, gate and native controls

Reconstruct original F2 common geometry clouds from corrected raw anchors:
float32 XYZ, filter original range>=1.5m, +0.205deg vertical correction,
Open3D0.4m voxel, statistical outlier20/2.5, PCG64/default_rng seed42 cap4000.
Reconstruct the cap2000 anchors exactly to verify saved point binding.

For selection only, exclude common-cloud points within1e-5m of the fitting
anchor rows; require >=200 remaining points each. These points are unused by
the pose fit, but not independent sensor data or unseen model context.
Select among the four poses by maximum symmetric overlap at strict distance
<1m, then minimum symmetric mean NN distance, then generation index.
Compute final admission on the entire unchanged common clouds:
overlap>=0.7 AND mean_dist<=2.5m, exactly F2 semantics.

N: original native K4 selection by minimum saved average raw rigidity, index
tie. NG: identical four native poses selected by the new geometry rule.
NG isolates a changed selector. All association arms use the same solver,
proposal/correspondence caps, selector and gate. No GT oracle enters selection.

## Minimal synthetic preflight

Before real bank: nontrivial source->target rigid recovery, common output
gauge, independent input/output row permutation with persistent row IDs,
coordinate scaling with physical units restored, deterministic ties/repeat,
raw=rigid-projected association reduction, collinear/too-small rejection,
nondegenerate wrong2m observation mismatch, and exact periodic2m ambiguity.
The last demonstrates the remaining alias blind spot; no physical-consensus
correctness certificate is claimed. Save inputs/outputs and independently
reconstruct fits with Horn quaternion eigensystems and explicit distances.
No requirement for every real pair to change.

## Evaluator and prospective decision

After GT-free validation seal, load original LiDAR evaluator poses and
original F2 strata. Truth=inv(GT_i) GT_j. Error=inv(truth) predicted pose;
translation norm and atan2 proper-angle convention reproduce F2 labels.
Strict RTE<=1m AND RRE<=5deg; clipped error=min(5,max(RTE,RRE/5)).
Report selected strict positives (75), ordinary(25), correct accepts,
incorrect accepts(all100), confuser accepts(25), fallback, oracle availability
and fixed41 hard08 native-K4-unavailable selected recoveries. Native controls
must reproduce old N selection/labels/gates; original01m/5deg labels remain.

RAD1_DEVELOPMENT_SIGNAL requires all:

1. On08, R selected strict >=N+4 and >=P+3, >=D+3, >=NG+3.
2. R recovers >=5 of fixed41 hard08 with its selected pose; oracle-only
   availability cannot pass. R08 mean clipped error <=0.95*N08.
3. On00, R selected strict>=N and clipped error<=1.02*N.
4. Both sequences: R ordinary strict>=N, correct accepts>=N, incorrect
   accepts<=N and confuser accepts<=N. Stable good cases need not change.
5. Engineering checks pass; R incremental association/fitting/selection CPU
   wall <=25% of the original summed N generation wall from frozen GT-free
   F2 records. This is a historical cost reference, not a current live timing
   benchmark. Report original inference cost, analysis IO/common preprocessing,
   all-arm experiment cost and R incremental work separately.

Otherwise NO_RAW_ASSOCIATION_DECODER_SIGNAL. Correctness/resource failure is
INCOMPLETE/INCONCLUSIVE and requires disclosed separate repair, not scientific
negative. No seed/top-k/tolerance/solver/selector/cohort rescue after outcomes.
Stop before online inference,71-pair promotion, graph or trajectory on negative.
A positive screen licenses the separately frozen all71 stage; no thesis or
originality claim follows from this exposed-development screen alone.

## Independent validation, resources and handoff

Independent validator imports no decoder/runner. It rehashes every identity,
reconstructs gate input binding, associations, spatial compatibility, greedy
supports and consensus using explicit squared distances/Horn fits, checks all
saved poses, selections and gates, and checks native reproduction. First-pair
gate distances per sequence receive bounded brute-force crosschecks. This
GT-free validation seals before GT. A subsequent independent evaluation checks
all errors, original strata, aggregates and every decision gate.

Single CPU process; set OMP/OPENBLAS/MKL threads1, no GPU. Caps: preflight300s,
bank1800s, independent GT-free validation1800s, evaluator/final validation600s,
RSS4GiB and new artifacts300MiB. Initial source hashing/planning is separate.
Preserve INCOMPLETE until final independent validation passes. Every stage
records wall/RSS; stops/failures are preserved. New sources stay isolated;
algorithm lives in RAP-SLAM/scripts, orchestration in RAP-main maintenance.
Handoff records exact stage, freezes/seals, counts, decisions, failures,
remaining unknowns and both original Git HEADs/dirty state.
