# Offline optimization O1-O3 synthesis

All results below are development evidence, not held-out validation. None passed
its predeclared practical screen; production remains the fixed heuristic,
proximity-priority budget 12, RAP without ICP refinement, relfloor + Huber.

| Sequence | Baseline APE m | O1 RAP+ICP | O2 budget 40 | O3 balanced 6+6 |
|---|---:|---:|---:|---:|
| POSS | 1.822264 | 1.912266 | 1.822264 | 1.822264 |
| KITTI 06 | 2.446184 | 2.516788 | 2.558393 | 2.533434 |
| KITTI 05 | 3.417117 | 2.913561 | 3.487993 | 3.214084 |
| KITTI 00 | 11.432936 | 11.533925 | 10.931019 | 10.336943 |

First-pose LiDAR APE only; do not select a different winning arm for each sequence.
O1: ../2026-09-11/optimization-o1-01/REPORT.md.
O2: optimization-o2-01/REPORT.md. O3: optimization-o3-01/REPORT.md.

O3 allocates six SC slots on each KITTI sequence, adding 4/4/6 pairs outside the
respective top-12 proximity list (06/05/00). POSS saturates at four pairs. Forty
fresh measurements are all accepted/safe. These labels use 5 m / 10 degrees;
passing them does not imply unbiased constraints or universal trajectory gains.

O3 KITTI 05 first APE improves, but aligned APE worsens 1.129313 -> 1.168216 m
and camera translation drift worsens 0.703737 -> 0.715824%. KITTI 06 first APE
worsens, while aligned APE improves 0.868971 -> 0.862829 m and camera translation
drift improves 0.667058 -> 0.663797%. KITTI 00 improves all three: aligned APE
2.891543 -> 2.109192 m, camera translation drift 0.914171 -> 0.896651%.
Different metrics respond differently; no universal improvement claim is justified.

O3 changes RNG ordering on some common pairs. Post-hoc common-edge-fixed PGO
preserves exact O2 measurements on common pairs and O3 on new pairs, without GT
selection. Its APE is 1.822264 / 2.535805 / 3.213732 / 10.336943 m. The observed
O3 direction persists, so common-edge sampling differences do not explain the
sign of these results. This diagnostic does not isolate sampling on new pairs
or prove performance on unseen sites. See o3-common-fixed-01/REPORT.md.

No quota/threshold sweep is planned. The useful finding is that retrieval
allocation affects trajectory quality and metric tradeoffs; more accepted edges
and local ICP refinement are not universal solutions. Preserve the baseline and
report O3 as a measured alternative, not a replacement default.

Next bounded work: compare RAP against the already specified identity- and
odometry-initialized ICP on the exact O3 selected pairs and fixed gate/backend.
This tests whether the observed source-allocation arm is specific to the registrar
and extends the fair comparator to the newly admitted candidates. Predeclare the
comparison before execution; do not use GT to select methods or candidates.

## Matched comparator extension

The O3 cohort now has a matched identity/odometry ICP comparison. RAP has lower
first-pose APE on POSS/06/00; ICP is better on 05, and secondary metric orderings
differ. See [complete thesis tables](paper-evidence-v2/RESULTS.md). Default unchanged.
This completes the previously planned comparator step; next work is a thesis
results-section draft rather than another parameter sweep.
