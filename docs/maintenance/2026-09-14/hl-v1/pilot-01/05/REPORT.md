# KITTI 05 HL1 data adequacy report

Decision: **INCONCLUSIVE**. Selected 16 pairs; requires >=60 total and >=10 in each stratum.

| Stratum | Population | Supported | Selected |
|---|---:|---:|---:|
| confuser | 8 | 1 | 1 |
| ambiguous_positive | 0 | 0 | 0 |
| low_overlap | 1 | 0 | 0 |
| ordinary | 422 | 24 | 15 |

Full retained candidate union: 457. Supported before strata/caps: 25.
Exclusion reasons: {'unsupported': 406, 'selected': 16, 'overlap_gap': 26, 'query_cap': 9}.

Candidate construction follows the frozen ring shortlist20, SC<=0.25, proximity30m/top5, separation200 and exact support2m/5m/age5s rules. Same-query cap3 applies across priority-ordered strata. All raw temporal-eligible ring/proximity distances and shortlisted SC distances are persisted. Label geometry uses fixed seed42, voxel0.4, outlier20/2.5, cap4000 and minrange1.5.

No RAP inference, selector score, oracle gap or training was run. The sample-size gate is checked before inference; inadequate data are not evidence that H1 or H2 is false. No relaxed threshold or synthetic replacement. These are already observed development sequences.

CPU data audit wall time 17.847s; RAP GPU time 0s. Human labour not independently instrumented.

Selected inputs are separated from evaluator-only GT/stratum records. Visual examples are diagnostic and cannot change membership. Independent validation and visual audit are required before removing INCOMPLETE.
