# C3 fixed FPFH information comparator — complete

2026-09-29. Decision: **NO_MATERIAL_GEOMETRY_INFORMATION_ADVANTAGE**
under the prospectively frozen [protocol](PROTOCOL.md). This observed-
development diagnostic compared one nontrained local geometric descriptor
against C1 miniSpinNet information on exactly the same saved F2 anchor
points and C1's exact 1m top-1 correspondence metric. It is not a RAP
registration result or independent confirmation.

## Provenance and execution

The [protocol](PROTOCOL.md), runner, separate validator and216 input/source
identities were SHA256-frozen before descriptor computation. Synthetic
transform and FPFH shape/finite checks passed. Open3D0.19.0 computed
source/target FPFH on the two saved 2000-point anchors for all200 F2 pairs,
using 2m/30 normal neighborhoods, normals oriented toward the LiDAR origin,
and 5m/100 descriptor neighborhoods. Points, point order, pair order,
normalization and C1's 1m geometry remained fixed. No GT or evaluator label
was parsed during bank generation. The complete descriptor bank was sealed
before evaluation at SHA256
`96c9ef79dabb59eeb2550195b19fa39ed9a83779baa00f71f07be9c1f892c278`.
Bank wall53.572s, peak RSS0.323GiB, artifacts195.075MB; all caps passed.

The independent [validation](validation.json) passed5,988 checks: frozen
identities, all200 artifact hashes/shapes/finite and zero counts, all200
pair metrics with16 fixed C1 shuffled controls each, C1/F2 pair and label
binding, group and decision arithmetic, and exact FPFH regeneration for
eight fixed pairs. `INCOMPLETE` is absent. No C1/C2 artifact or production
code was modified, no training/default edit or Git sync occurred.

## Observed information

| Group | Pairs | FPFH median true top-1 | FPFH median control | FPFH median true-control | Median paired FPFH-minus-C1 information |
|---|---:|---:|---:|---:|---:|
| 08 native K4 unavailable | 41 | 0.519% | 0.098% | 0.425 pp | −0.445 pp |
| 08 native K4 available | 34 | 1.978% | 0.148% | 1.824 pp | −6.360 pp |
| 00 native K4 unavailable | 23 | 0.222% | 0.123% | 0.097 pp | −0.388 pp |
| 00 native K4 available | 52 | 2.211% | 0.139% | 2.108 pp | −5.288 pp |

The frozen primary analysis uses the **33** adequately geometrically
covered 08 native-unavailable positives (>=10% eligible source points).
All33 also have >=95% nonzero descriptors in both anchors; target/source
nonzero counts in this group range1991–2000 of2000. Their median FPFH
true-minus-control recall is **0.427 pp**, below the frozen **10 pp** margin.
Their median paired FPFH-minus-C1 information is **−0.722 pp**, below the
required **+5 pp** margin. C1's own paired information median on these same
33 is **1.132 pp**. The decision is an effect-size failure with adequate
descriptor support, not a missing-neighborhood inconclusive result.

The weak FPFH result on available pairs also matters: this fixed descriptor
has substantially less top-1 information than miniSpinNet even where RAP
already had a strict native candidate. It provides no reason to replace the
encoder or expose these FPFH vectors to RAP. It does not prove that every
handcrafted descriptor, radius, source context or matching rule fails.
FPFH was computed only from the sparse saved anchors; C1 miniSpinNet had
full corrected scans available when computing features at those anchors.
That contextual asymmetry limits any broad descriptor ranking. The single
scale, LiDAR-origin normal orientation, top-1 metric, KITTI00/08 observed
development cohorts and 2000-point budget are further boundaries.

## Next boundary

Stop this fixed FPFH route: no retrospective radius, normal-orientation,
feature threshold or top-k rescue of C3. C1+C2+C3 establish model reliance
on miniSpinNet, weak hard-pair top-1 information, and failure of this one
anchor-only geometric alternative. They do **not** establish that feature
information alone caused F2 candidate failures. Before another GPU or
training study, formulate a distinct, prospectively frozen question that
isolates a different source of missing candidates or tests how RAP uses
spatial context, with a matched control and explicit stop margin. Existing
E0 held-out engineering transfer remains the positive metric result; the
manuscript pause and all earlier route stops persist.
