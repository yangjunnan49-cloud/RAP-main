# C1 descriptor-information audit — complete

2026-09-28. Decision: **NO_FEATURE_INFORMATION_SIGNAL** under the frozen
[protocol](PROTOCOL.md). This is an observed-development information
diagnostic of RAP's miniSpinNet input on the exact F2 KITTI00/08 cohorts.
It does not measure RAP's use of the feature channel, pose improvement,
or independent confirmation.

## Execution and validation

The protocol, runner, separate validator, source/weight/GT identities and
1,075 distinct files were SHA256-frozen before descriptor generation.
All 200 F2 pairs were processed in saved order. For every pair, all six
corrected scans regenerated the exact saved F2 8000 points, normalized
condition, part counts, centers and scale. miniSpinNet weights were loaded
with `weights_only=True`, `strict=True`; every extracted descriptor had
finite, nonzero norm. No RAP flow model or evaluator GT was loaded in
the bank runner. Full six-part descriptor artifacts were sealed at bank
SHA256 `b4771213a06e7de4bd9f3293e1ad2d4949168fcf46bf23364b5bd9f5c5932914`
before the separate evaluator used GT. Bank wall155.242s, peak allocated
GPU2.090GiB, artifacts189.99MB, all within frozen caps.

The independent [validation](validation.json) passed3,579 checks:
all frozen identities,200 descriptor hashes/shapes/norms, all200 pair
correspondence and16-permutation-control metrics, independent native K4
oracle labels from the four saved poses, all group/decision arithmetic,
and exact descriptor/point regeneration for eight fixed spot pairs.
`INCOMPLETE` was removed after the sealed bank and evaluator summary.

## Pair-level finding

The target/source anchors each have2000 F2 points. Geometric eligibility
means a source point has a target point within1m after the saved GT pose;
top-1 descriptor correctness requires the descriptor-selected target
to satisfy that same1m condition. Each pair's control is the mean of16
fixed target feature-to-coordinate shuffles. These are conditional
matching rates on eligible points, not loop recall or independent point
observations.

| Observed group | Pairs / adequately covered | Median eligible fraction | Median true top-1 | Median shuffled control | Median paired difference |
|---|---:|---:|---:|---:|---:|
| 08 native K4 unavailable | 41 / 33 | 28.9% | 0.90% | 0.10% | 0.82 pp |
| 08 native K4 available | 34 / 33 | 65.7% | 8.46% | 0.16% | 8.26 pp |
| 00 native K4 unavailable | 23 / 16 | 12.2% | 0.54% | 0.11% | 0.38 pp |
| 00 native K4 available | 52 / 52 | 51.5% | 7.67% | 0.15% | 7.50 pp |

Table medians use each whole group's pairs with at least one eligible
point; the adequate count uses >=10% eligibility. The **primary** frozen
criterion uses only the33 adequately covered 08 unavailable pairs: its
median true-minus-control recall is **1.132 pp**, versus the predeclared
>=10 pp information margin. Adequate coverage count passes (33>=20),
information margin fails. All41 unavailable pairs have nonzero eligible
points, so the decision is not driven by undefined recall. On08 ordinary
pairs the median true top-1 is9.00% versus0.13% control; on08 low-overlap
it is0.34% versus0.09%. Thus the descriptors contain some cross-visit
information on easier pairs, while the fixed top-1 signal is very weak
where native F2 generation lacks a correct candidate.

The available and unavailable groups also differ substantially in
geometric coverage and stratum mix. Their matching-rate gap is an
association, not proof that descriptors cause RAP's candidate failures.
A point-wise top-1 metric does not capture RAP's global attention or
multi-part use. The 1m radius, selected point budget and fixed miniSpinNet
are the boundaries of this diagnostic. Do not call this a general failure
of local features or infer the checkpoint's training domain.

## Next decision

Do not immediately replace the encoder, train on KITTI, modify the gate,
or run a broad descriptor sweep. The next distinct test should be a
separately frozen, small **feature-channel intervention**: on fixed F2
pairs with both ordinary and native-K4-unavailable positives, exactly
reproduce the saved native five-step generation0 with true descriptors,
then permute descriptor-to-point assignment within each of the six parts
using the same points/noise/weights/flow configuration. Compare raw flow
and decoded poses, with evaluator-only labels after a sealed bank. This
tests whether the RAP checkpoint uses the existing feature channel; a
negative C1 information margin alone cannot answer that. Predeclare
sample IDs, effect and cost margins before generation. Only then decide
whether an input representation study is justified. All previous stops,
the manuscript pause and no-Git-sync boundary persist.
