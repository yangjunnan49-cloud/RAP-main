# V0: fixed sensor-ray visibility information screen

Owner authorized execution of the post-brainstorm V0 decision. This is a
CPU-only, observed-development feasibility test on the exact F2 KITTI00/08
100 pairs each (25 per stratum, saved N order). It asks whether a fixed
GT-free sensor-ray score can create safe translation candidates from the
selected native N/R4 pose. It is neither a new RAP method, an independent
confirmation, nor a claim about flow guidance. Freeze this protocol, runner,
independent validator and all source/raw/input identities after synthetic
checks and before scoring any real pair. No tuning after outcome inspection.

## Input and deterministic candidates

For each target scan i and source scan j, load the full raw KITTI anchor
scans, float32 xyz, retain original-frame range>=1.5m, then apply the
unmodified `real_dataset.kitti_vertical_correction` (+0.205deg). Reuse G1's
frozen loader, F2 native N/R4 selected transform and identical pair order.
No supports, GT, cross-visit odometry, learned features, generation, or
outcome-dependent pair filtering. For each scan independently sample 4096
physical points without replacement using the first 8 SHA256 hex digits of
`V0|ray-query|{seq}|{frame}` as a NumPy default_rng seed. Full scans supply
the reference rays and nearest-neighbor trees. Use all 27 translations in
target-i coordinates with dx,dy,dz each in {-1,0,+1} metres around the
fixed native SE(3) pose; rotation is unchanged. The centre is exactly N/R4.
No iterative search, second stage, changed radius, or oracle offset.

## Sensor-ray classification and scores (fixed)

For each candidate T, project the 4096 source sampled points into target
sensor coordinates, and the 4096 target sampled points through inverse(T)
into source sensor coordinates. For each projected point, find the nearest
*angular* ray in the destination full scan using a unit-direction cKDTree.
If angular separation exceeds 0.4deg, classify unobserved. Otherwise let
q be projected range and r the reference ray's measured range. Classify
agreement when |q-r|<=0.75m; free-space contradiction when q<r-0.75m;
occluded when q>r+0.75m. Report the four counts separately, summed over
both directions (8192 queries). This is a discrete static-scene proxy, not
a differentiable LiDAR renderer; dynamics and rolling acquisition remain
limitations. Comparable-ray coverage=(agreement+free+occluded)/8192.

Visibility objective (lower is better):
`(free - agreement + 0.25*unobserved)/8192 + 0.02*||delta||^2`.
Occluded contributes zero. If centre coverage<0.10, keep the native centre
and mark insufficient support. Otherwise choose the minimum-score candidate
among those with coverage>=0.10, tie-breaking by smaller squared offset
then lexicographic (dx,dy,dz). This fixed rule avoids a low-support pose
winning simply by making geometry unobserved.

The comparator uses the *same 27 candidate poses*, same 4096 sampled points
and same 0.02*||delta||^2 penalty. Its objective is the mean over both
directions of nearest-neighbor Euclidean distance clipped at5m, querying
each full corrected destination scan with a cKDTree. Select the minimum,
same tie-break. This ordinary symmetric NN search distinguishes visibility
information from a generic local translation search.

For native and both selected poses, recompute the unchanged F2 common
acceptance gate: geometry-only `RAPBackend.preprocess` with voxel0.4,
statistical outlier20/2.5, seed42 cap4000 on the corrected anchors, then
`_alignment_metrics(thresh=1.0)`, accept iff overlap>=0.7 AND mean_dist<=2.5.
The native gate values must reproduce F2 saved `gates.json` within1e-5;
otherwise stop as INCONCLUSIVE_ENGINEERING. No gate threshold changes.

Synthetic checks before freeze: ray identity yields agreement and no free
contradiction; a same-ray point nearer than the observed surface is free,
farther is occluded, out-of-view is unobserved; a known rigid transform
scores better than a displaced transform. No real labels are read for this.

## GT separation, metrics and prospective decision

The runner may SHA-hash frozen evaluator/GT files for integrity but must
not parse them; it saves all 27 candidate score/count records and native,
visibility and NN selected poses/gates for all 200 pairs, then SHA-seals
the complete bank before any evaluator loads GT or strata. Failed pair
processing is an engineering stop, not a dropped pair.

Evaluator-only: same F2 truth `inv(gt[i]) @ gt[j]`, strict RTE<=1m and
RRE<=5deg, clipped positive error min(5,max(RTE,RRE/5)). Report paired
strict gains/losses and correct/incorrect accepts versus native, recoveries
among native K4-unavailable positives, ordinary and other strata, all
confusers, coverage, costs, and NN comparator. No graph inference.

Declare `RAY_INFORMATION_SIGNAL` only if all hold:
1. Centre comparable-ray coverage>=0.10 on at least90/100 pairs on each seq.
2. On08, visibility creates >=5 strict positives from the 41 native
   K4-unavailable pairs and yields >=5 net strict positives versus native.
3. On08, correct accepts gain >=2 versus native, with no newly incorrect
   accepts; on00, correct accepts lose <=1 and no newly incorrect accepts.
4. On00, net strict positives lose <=2; ordinary strict losses <=1 on each.
5. On08, visibility has >=3 net strict positives and >=1 net correct accept
   over the same-grid ordinary NN comparator.
6. CPU bank wall<=30min, peak RSS<=4GiB, artifacts<=1GiB.

These planning margins are not significance tests. If any fail, stop this
fixed visibility-guidance route; do not tune angular/range tolerances, score,
grid or gate. Passing only licenses isolated sampler engineering with the
same-score post-hoc search as a required baseline, followed by separately
frozen efficacy and fresh confirmation. Independent validation rehashes
sources/inputs/bank, verifies exact pair/order/candidate grid, pose/gate
geometry, labels, arithmetic, all conditions and caps. No GPU, training,
network, raw acquisition, production edit or Git sync.
