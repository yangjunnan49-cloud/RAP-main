# Validated shared09 scan/pose geometry discrepancy

Decision **SHARED_09_GEOMETRY_LABEL_DISCREPANCY**. This is an evaluator-only
diagnostic, prompted by exposed comparator failures, not independent efficacy
confirmation, proof of GT error, or proof of matcher correctness.

138 identities froze before the new geometry scores. All71 actual online pairs
used exactly the validated4000 points per scan; RAP,Geo,GT and odometry poses
were compared without optimization/refinement. Full distance vectors sealed.
Independent brute-force SciPy cdist checks every2272000 directed NN distance,
maximum difference2.84e-13m; all statistics/poses/aggregates and frozen decision
are independently recomputed. All six sequences are reported, no subset choice.

|09 all12 attempts / pose|Median symmetric mean distance(m)|Median overlap(distance<1m)|
|---|---:|---:|
|RAP|0.850786|81.34375%|
|GeoTransformer|0.908269|78.50625%|
|Official trajectory GT relative pose|3.030330|2.50000%|
|Saved local odometry relative pose|1.741648|37.06875%|

Predeclared09 gate passes: median paired GT-minus-RAP mean distance2.198792m
(required>=0.5),median paired RAP-minus-GT overlap78.79375pp (>=10pp),
median RAP-vs-Geo translation0.199152m (<=0.5),rotation0.766336degrees (<=2).
Differences of medians are not the same as median paired differences.
On original ten accepted09 pairs: RAP/Geo/GT median overlap83.7375/79.7875/
2.8125%,mean distance0.771645/0.894297/2.985931m. This is agreement between
two distinct models and disagreement with official pair labels on these scans.

Other all-pair cohorts: median paired GT-minus-RAP mean distances
00=0.172855m,05=0.003034m,06=0.000818m,07=0.004863m. The09 discrepancy is
far larger. 10's11 GT-far attempts give nearly zero GT overlap and weak model
alignment (median RAP25.5%,Geo39.8%). Lower geometric residual alone can favor
perceptual aliases; the10 counterexample prevents inferring that either model
or a lower residual is automatically physically correct.

The observation is compatible with frame/time/calibration mismatch, trajectory
label drift, or a repeated-scene registration ambiguity. Current checks verify
saved identities, transformations and numerical distances but do not distinguish
these causes. Official ter/ATE and strict failure labels remain unchanged.
The earlier joint-GT graph headroom is a metric counterfactual; this diagnostic
shows why its physically recoverable extent cannot be assumed from that oracle.
07's real comparator regression and00 strict failures remain separate problems.
F2 hard08 labels/distribution are not invalidated by a09 online observation.

Recorded total17.604s,peakRSS0.066GiB,artifacts18.433MB before report; caps pass.
No new neural inference, graph run, training, default/production/manuscript edit
or Git sync. Next read NEXT_ROUND_PLAN.md for one bounded identity/temporal
consistency diagnostic before further registration mechanisms.
