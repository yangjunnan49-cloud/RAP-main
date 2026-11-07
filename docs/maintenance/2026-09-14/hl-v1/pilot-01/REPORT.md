# HL-V1 pilot-01: data adequacy result

2026-09-14. **INCONCLUSIVE — cohort minima fail before inference.**
HL0 engineering PASS remains valid. H1/H2 are not evaluated; this is neither
scientific falsification nor GO for a learned head. No new RAP hypotheses,
selector comparisons, oracle gaps, trained head or trajectory runs exist here.

## Fixed-protocol counts

| Sequence | Retained candidate union | SC proposals | Proximity proposals | Supported pairs | Selected |
|---|---:|---:|---:|---:|---:|
| KITTI05 discovery | 457 | 65 | 448 | 25 | 16 |
| KITTI06 confirmation data audit | 445 | 28 | 445 | 0 | 0 |

SC/proximity counts overlap and must not be added. Supported means both anchors
have two distinct causal support keyframes under the original protocol.

| Stratum | 05 population | 05 supported | 05 selected | 06 population | 06 selected |
|---|---:|---:|---:|---:|---:|
| Confusers | 8 | 1 | 1 | 0 | 0 |
| Ambiguous-positive proxy | 0 | 0 | 0 | 0 | 0 |
| Low overlap | 1 | 0 | 0 | 0 | 0 |
| Ordinary revisit | 422 | 24 | 15 | 445 | 0 |

Required on **each** sequence: >=60 selected pairs and >=10 in every stratum;
target 25 per stratum. Both fail. KITTI05 has 26 overlap-gap candidates retained
outside these strata, 406 unsupported stratum pairs and 9 query-cap exclusions.
KITTI06 excludes all 445 ordinary pairs for missing support. All exact reasons
and records are persisted; no threshold was relaxed and no sample was replaced.

## What was executed

Built descriptors on the frozen complete frontends: 374 keyframes for 05 and
202 for 06. Recorded every temporally eligible historical ring-key/proximity
distance, every top-20 ring shortlist SC score/rank, and the full deduplicated
union of per-query SC<=0.25 and top-five proximity<=30m candidates, separation
>=200 source frames. No production top-12 budget or registration gate was used.

GT overlap uses the mean of both 1m NN coverage fractions after GT alignment,
with minrange1.5, voxel0.4, outlier20/2.5 and cap4000/fixed seed42. It is stored
only with offline labels/sampling data. Ambiguity uses the fixed same-query
SC-distance gap and historical-source separation criterion. Selection applies
the exact hash ordering, priority strata, quota25 and shared query cap3.

Support uses frozen full-frame accumulated local odometry distance, the nearest
past keyframe crossing 2m/5m, distinct IDs, age<=5s and anchor exclusion. IDs,
timestamps and local transforms are persisted per candidate. Generation-input
files contain only anchor/support metadata, without GT, strata or ambiguity labels.

Candidate generation/GT labelling took 17.847s (05) and 10.580s (06) of CPU-stage
wall time, excluding separate independent validation, visual inspection and
documentation. RAP GPU time and hypothesis count are zero. Human labour was not
separately instrumented; no claim of a full two-working-day model comparison.

## Validation and sequence order

Boundary/unit checks cover strata, coverage, support-before-selection and shared
query-cap/quota behaviour. Independent validation reconstructs the full candidate
union and supports, replays sampling, checks GT-free inputs and compares scalar
SC against batched SC (maximum differences 2.30e-8 / 2.35e-8). Four fixed-label
visual examples across both sequences have exact overlap agreement using an
independent chunked brute-force distance calculation. Visual inspection found
no obvious mismatch in the shown projections; all memberships are unchanged.

KITTI05 report, visual audit, selection and data artifacts were hash-frozen in
discovery_frozen.json before starting the KITTI06 audit. The 06 process verified
that freeze on entry. No confirmation model outcomes were generated. Input scan
hashes were checked against HL0 before descriptor construction and again after
labelling; parent metadata and odometry hashes match the frozen parents.

Per-sequence reports: [05](05/REPORT.md), [06](06/REPORT.md).
Diagnostic projections: [05](05/strata_examples.png), [06](06/strata_examples.png).
The figures are GT-aligned XY diagnostics, not independent place-label truth.

## Interpretation and next decision

The selected cohort cannot answer whether useful alternative RAP hypotheses
exist or whether support chooses them. Do not import the historical all-safe
cohort or HL0 profile bank to fill this gap. Official RAP rigidity selection and
the B1/B4/S4/OR4/REJ evaluator were not implemented because the prerequisite
sample-size gate already failed. No omitted baseline is claimed as completed.

There are two observed bottlenecks. First, the declared retrieval population has
too few hard strata even before support filtering: 05 has only 8 confusers,
0 ambiguous positives and 1 low-overlap pair; 06 has none. Second, frozen
keyframes often make the 2m/5m targets collapse to one support, so available
anchors rarely connect as eligible loop pairs. Changing support alone cannot
make these populations pass the original minimum-per-stratum requirement.

[Data expansion decision](DATA_EXPANSION_DECISION.md): retain this INCONCLUSIVE
result and investigate additional real repeated-route data before another scored
pilot. Any changed data roles/support definition requires a frozen amendment;
do not relabel an amended run as unchanged HL-V1. No dataset download, new
training split, protocol modification or training was performed this turn.

Production/model source and defaults are unchanged. Only two isolated RAP-SLAM
audit scripts and maintenance evidence were added. Existing dirty worktrees
remain on main at 4055d92 / 6d3f2d2; no commit/push/pull/reset/cleanup.
