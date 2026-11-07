# S1 native RAP 5-vs-10-step development screen — complete

2026-09-28. Decision: **NO_TEN_STEP_DEVELOPMENT_SIGNAL** under the
prospective [protocol](PROTOCOL.md). RAP's released inference config/demo
defaults to ten Euler steps; RAP-SLAM and F2 use five. S0 first verified
that regenerated five-step native trajectories exactly reproduce eight
saved F2 cases under identical inputs/noise. S1 then changed only the
isolated native sampler's step count on the exact F2 observed-development
KITTI00/08 cohorts, 100 pairs and K4 per sequence. The ten-step result
has a local 00 candidate-creation improvement, but no safe executable
transfer to08 and no correct-accept improvement. Do not promote ten steps
to the RAP-SLAM default or tune step count from this screen.

## Execution, separation and validation

The protocol, original runner/validator, source/config/model weights and
1,081 distinct input identities (including every required raw scan,
F2 inputs/records/gates/evaluator GT hashes) were SHA-frozen before new
inference. The original runner stopped at module import before any pair,
`INCOMPLETE` marker or GT access. [AMENDMENT_01.md](AMENDMENT_01.md)
preserves it and separately froze a path-only version-2 runner and
validator before generation. No outcome-dependent change occurred.

For every pair, the six corrected scans, points, descriptors, normalized
condition, centers, scale and four explicit noise arrays matched F2's
saved inputs; original five-step hypotheses were not rerun. All 800
ten-step native generations were finite and valid. Each ten-step
rigidity score averaged the same official per-step residual over ten
steps; K4 R4 selection and the original anchor-only F2 gate were kept.
The old selected pose reproduced its saved F2 gate within1e-5 for every
pair. Full ten-step trajectories, scores, poses and gates were sealed at
bank SHA256 `b152cad2560649fafb0e5c6cdd88b7391ce0699c4b7d5e128c2548cf658659b1`
before evaluator-only GT/strata parsing.

The bank wall was 1,313.666s (21.9min), peak allocated VRAM 2.413GiB,
artifacts 707MB, within the 45min/12GiB/2GiB caps. Descriptive summed
generation wall was 494.23s on00 and 483.30s on08, versus saved F2
five-step N times 230.96/229.61s; these are cross-run timing observations,
not a strictly paired latency benchmark. Independent
[`validation.json`](validation.json) passed 10,726 checks: original and
amended source hashes, all 800 artifact hashes, all 8,000 raw endpoint
rigidity refits (maximum residual delta 1.04e-5), all final pose refits
(maximum matrix delta 5.47e-5), selected gates spot-recomputed, F2
comparator identity, all labels, strata and decision arithmetic. The
`INCOMPLETE` marker was cleared after bank seal and summary, before
validation.

## Paired outcome

| Sequence / steps | Selected strict /75 | K4 oracle strict /75 | Correct accepts | Incorrect accepts /100 | Confuser accepts | Mean clipped positive error |
|---|---:|---:|---:|---:|---:|---:|
| 00 / 5 (F2 N) | 49 | 52 | 23 | 1 | 0 | 1.472846 |
| 00 / 10 | 50 | 55 | 21 | 3 | 0 | 1.453173 |
| 08 / 5 (F2 N) | 30 | 34 | 17 | 10 | 0 | 1.579930 |
| 08 / 10 | 29 | 34 | 17 | 10 | 0 | 1.583142 |

On00, ten steps created strict candidates on 5/23 positives with none
in the five-step K4 bank: four low-overlap and one ambiguous pair.
Selected strict outcomes gained four and lost three (net +1). Three
newly strict selected low-overlap poses were all rejected by the unchanged
gate, so there was no new correct accept. Two ordinary previously correct
accepted pairs became incorrect accepted (correct accepts 23→21,
incorrect accepts 1→3). The 00 low-overlap selected strict count rose
3→6, but ordinary fell 25→23. Matched-generation strict transitions
across all four seeds were 11 gains and six losses. The small 00 clipped
error improvement does not override these safety failures.

On08, ten steps created a strict candidate in only 1/41 five-step
K4-unavailable positives, which R4 did not select as strict. Selected
strict outcomes gained one and lost two (net -1); correct/incorrect
accepts stayed17/10. Matched-generation transitions were four gains and
four losses. Ambiguous selected strict fell12→11; low-overlap and
ordinary were unchanged. Both sequences still rejected all25 confusers.

The predeclared 08 candidate/strict and acceptance-gain conditions,
00 acceptance/ordinary guards all failed. Only the clipped-error and
resource guards passed. This negative decision is bounded to five versus
ten Euler steps, one RAP12 checkpoint, fixed F2 points/noise/K4 and
two observed-development sequences. It does not prove no integrator
schedule or model adaptation can help. The 00 local candidate improvement
is an observed diagnostic, not a selected ten-step route or thesis method.

## Next boundary

Stop this fixed step-count route: no post-hoc 6/8/12/20-step sweep,
gate relaxation, R4 score change or 00-only promotion. V0 visibility,
D0 early checkpoint, F2 structured motion and prior negative branches
remain stopped. The residual research question is more specific: why
RAP's conditional generation lacks candidates on many 08 positives
and why candidate improvements on low-overlap 00 do not yield safe
accepted loops. Next work should be a separately scoped conditioning/
feature-distribution diagnosis or an independently justified model
adaptation question, with the same GT separation and fresh confirmation
requirement. No production/default change, training, raw acquisition,
Git sync or overwrite of completed prior experiments occurred.
