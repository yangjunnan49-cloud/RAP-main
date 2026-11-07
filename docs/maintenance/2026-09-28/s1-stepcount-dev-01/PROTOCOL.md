# S1: native RAP 5-vs-10-step observed-development screen

S0 independently passed same-input/noise reproduction on eight fixed
pairs: all saved F2 five-step raw and state tensors matched exactly;
ten-step native sampling was finite and valid. The source-based question
is whether RAP's released ten-step inference convention improves the
RAP-SLAM native candidate bank under the *same* F2 points, descriptors,
noise, K4, selection rule and acceptance gate. This is engineering
configuration evidence, not a novel method claim or fresh confirmation.

## Cohort, sources and frozen execution

Use the exact F2 observed-development KITTI00/08 100 pairs each in saved
N order, 25 per stratum, all four original F2 seeds/noise arrays per
pair. F2 native N five-step `records.json`, `gates.json` and evaluator
rows are the frozen comparator; do not regenerate them or change F2.
Regenerate the six corrected scans and miniSpinNet features using F2's
unchanged filter/correction, sample caps [2000,1000,1000,2000,1000,1000],
seed42 preprocessing and normalized coordinates; assert saved F2
`inputs.npz` points/conditions/counts/centers/scale match exactly.
Frozen RAP12/miniSpinNet weights, Euler sampler, rigidity forcing and
request-local RNG/IEEE precision scope. Change only the isolated model
inference step count from5 to10 during generation, then restore5 even
on failure. For every k=0..3 use the corresponding saved explicit F2
noise. No GT, evaluator strata, pair replacement, local-motion change,
cross-visit prior, training or production-default edit.

Freeze this protocol, runner, independent validator, source/model/config
identities, F2 inputs/records/gates/evaluator/GT identities and every
required raw scan before real inference. S0's frozen engineering bank
and validation must pass. Score every10-step generation with the official
mean rigidity RMSE over all ten raw clean endpoints, as F2 scores its
five-step trajectories. Decode the final raw endpoint with the same
per-part Procrustes and physical centers. Select R4 by lowest mean score,
generation index tie-break. Save all ten raw clean endpoints and all
generation poses/scores. Recompute the exact F2 anchor-only gate on
corrected raw scans (seed42 geometry-only voxel0.4, outlier20/2.5,
cap4000; overlap>=0.7 AND mean_dist<=2.5). Assert a saved F2 native
reference pose reproduces its gate within1e-5. The runner may hash GT
and evaluator files, but must not parse them.

Seal every score, pose, gate and trajectory artifact by SHA256 before
evaluator-only GT. Then use F2 `inv(gt[i]) @ gt[j]`, strict RTE<=1m and
RRE<=5deg, clipped error min(5,max(RTE,RRE/5)). Report separately per
sequence/stratum: R4 and OR4 strict, paired gains/losses, new strict
candidates among F2 final-K4-unavailable positives, correct/incorrect
accepts, confuser accepts, ordinary losses, clipped error, timing and
cost. Also report matched-generation k0..3 changes independent of R4
selection. No pooling across sequences or post-hoc best step/seed.

## Prospective decision and limits

Declare `TEN_STEP_DEVELOPMENT_SIGNAL` only if all conditions hold:

1. On08, >=5/41 F2 native-K4-unavailable positives gain a strict
   ten-step candidate **and** selected R4 gains >=5 net strict positives.
2. On08, correct accepts gain >=2, with zero newly incorrect accepts.
3. On00, selected R4 net strict change >=-2, correct accepts lose <=1,
   zero newly incorrect accepts; ordinary strict losses <=1 on each seq.
4. Mean clipped positive error worsens by at most0.05 on each sequence.
5. All 800 ten-step generations valid; bank wall<=45min, peak allocated
   VRAM<=12GiB, new artifacts<=2GiB.

Failure of an efficacy guard is `NO_TEN_STEP_DEVELOPMENT_SIGNAL`; a source,
reproduction, validity or resource failure is `INCONCLUSIVE_ENGINEERING`.
These are planning margins, not significance tests. A pass only licenses
a separately frozen fresh-confirmation and full-system graph evaluation;
no default change or thesis novelty wording follows automatically. A
failure ends the fixed ten-step route: no step-count sweep or support,
score, gate, seed or point-budget rescue from this screen. Independent
validator rehashes sources and sealed bank, recomputes selected scores,
spot raw trajectories/pose fits and gate geometry, evaluator metrics and
all decision arithmetic. No Git sync or old artifact overwrite.
