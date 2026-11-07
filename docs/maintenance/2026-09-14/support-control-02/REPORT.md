# SC-V1.1 observation-versus-score control

Confirmation decision: **NO_SUPPORT_SIGNAL_UNDER_FIXED_SCORE**. **Neural expansion remains STOPPED.**

Both roles have 100 pairs, 25 per stratum, and 400 valid hypotheses. KITTI00 discovery reuses its already observed HL-V2 bank; KITTI08 is the new frozen confirmation membership. Discovery was independently checked and hash-frozen before KITTI08 inference. SC-V1 data insufficiency and HL-V2 H2 failure remain separate, unchanged results.

## Fixed contrasts

A4 uses the same clipped-distance objective as S4 on duplicated anchors. S4 uses four causal support combinations. P4 pools exactly the same support points; P4x2 repeats pooling scoring to match S4 NN query count. R4 uses official RAP trajectory rigidity. G4 changes only local transport to GT and is evaluator-only; OR4 is a GT pose oracle. No trained selector, threshold change or new rejection rule was introduced.

| Role | Method | Strict positive success | Correct accepts | Incorrect / accepted | Mean clipped positive error |
|---|---|---:|---:|---:|---:|
| discovery | B1 | 50/75 | 22 | 1/23 | 1.263181736 |
| discovery | B4 | 52/75 | 22 | 2/24 | 1.103923261 |
| discovery | R4 | 53/75 | 22 | 1/23 | 1.091010852 |
| discovery | A4 | 54/75 | 22 | 2/24 | 1.133144631 |
| discovery | S4 | 54/75 | 22 | 2/24 | 1.080597330 |
| discovery | P4 | 53/75 | 22 | 2/24 | 1.087966771 |
| discovery | P4x2 | 53/75 | 22 | 2/24 | 1.087966771 |
| discovery | G4 | 54/75 | 22 | 2/24 | 1.083239886 |
| discovery | OR4 | 57/75 | 22 | 2/24 | 0.937255448 |
| discovery | REJ | 0/75 | 0 | 0/0 | 5.000000000 |
| confirmation | B1 | 32/75 | 17 | 10/27 | 1.543525882 |
| confirmation | B4 | 34/75 | 17 | 10/27 | 1.268507725 |
| confirmation | R4 | 32/75 | 16 | 10/26 | 1.393695261 |
| confirmation | A4 | 33/75 | 17 | 10/27 | 1.269984013 |
| confirmation | S4 | 31/75 | 17 | 10/27 | 1.400363980 |
| confirmation | P4 | 32/75 | 17 | 10/27 | 1.401031220 |
| confirmation | P4x2 | 32/75 | 17 | 10/27 | 1.401031220 |
| confirmation | G4 | 31/75 | 16 | 10/26 | 1.402462151 |
| confirmation | OR4 | 37/75 | 16 | 10/26 | 1.226284942 |
| confirmation | REJ | 0/75 | 0 | 0/0 | 5.000000000 |

## Predeclared decision conditions

| Role | A4/oracle discrepant positives | Gap recovery | Ordinary recall loss | New incorrect vs A4 / R4 | No worse than R4 | Decision |
|---|---:|---:|---:|---:|---|---|
| discovery | 14 | 26.8250% | 0.0000% | 0 / 1 | True | NO_SUPPORT_SIGNAL_UNDER_FIXED_SCORE |
| confirmation | 10 | -298.3587% | 0.0000% | 0 / 0 | False | NO_SUPPORT_SIGNAL_UNDER_FIXED_SCORE |

The primary contrast is clipped positive error, not a post-hoc recall switch. All five conditions must pass. Harmful transitions are separate pair lists; beneficial transitions never cancel a newly incorrect accept.

## Every stratum

| Role | Stratum | A4/S4/P4/R4 strict successes | S4 minus A4 mean clipped error | S4 incorrect accepts |
|---|---|---:|---:|---:|
| discovery | confuser | 0/0/0/0 | N/A (not positives) | 0 |
| discovery | ambiguous_positive | 22/22/22/21 | -0.007853818 | 0 |
| discovery | low_overlap | 8/8/7/8 | -0.152104067 | 1 |
| discovery | ordinary | 24/24/24/24 | +0.002315981 | 1 |
| confirmation | confuser | 0/0/0/0 | N/A (not positives) | 0 |
| confirmation | ambiguous_positive | 15/13/13/14 | +0.386385823 | 0 |
| confirmation | low_overlap | 3/3/4/3 | +0.005934261 | 2 |
| confirmation | ordinary | 15/15/15/15 | -0.001180184 | 8 |

Confusers are excluded from positive-error and positive-recall denominators; all strata contain25 pairs. Full error quantiles, failure counts, accepted-confuser rates and exact pair transitions are retained in each role metrics/evaluator file.

## Local transport and pooling

- discovery: G4 minus S4 clipped error = +0.002642556; G4/S4 strict successes = 54/54. P4 minus S4 clipped error = +0.007369441.
- confirmation: G4 minus S4 clipped error = +0.002098171; G4/S4 strict successes = 31/31. P4 minus S4 clipped error = +0.000667241.

These contrasts test only the declared geometry and score. GT-motion sensitivity does not establish physical sensor-error causation. A failure to benefit does not prove that every possible support representation lacks information. P4x2 is identical in scores and selections to P4.

## Cost and validation

| Role | New RAP generations | Generation wall s | Preparation wall s | A4/S4/P4/P4x2 scoring wall s | Total study-process wall s | Peak allocated/reserved GiB |
|---|---:|---:|---:|---|---:|---|
| discovery | 0 | 0.000 | 15.579 | 7.046/6.898/3.774/7.552 | 115.689 | 0.000/0.000 |
| confirmation | 400 | 386.670 | 8.757 | 6.945/6.853/3.610/7.204 | 487.170 | 4.457/8.998 |

Shared preparation includes anchors and supports and is not a standalone deployment-time estimate for A4. P4/S4 use the same support points; P4x2/S4 match query count, while tree sizes and runtime differ. No exact equal-wall-time claim. Scores are CPU monotonic wall times; generation is CUDA synchronized. Total includes G4, I/O and initial loading, but excludes independent validation/reporting. Historical00 generation is not charged as new work. Active-kernel time and human labour are not measured.

- Synthetic transport, duplicate-anchor, pooled brute-force, empty and tie checks passed.
- All400 inherited S4 scores reproduce exactly; original discovery bank bytes and B1/B4/R4/S4 decisions are unchanged.
- Each role passed1000 independent selections, independent pose errors, all-stratum metrics and full decision recomputation.
- Rehashed all800 bank files and 796 distinct used raw scans; parent/source/protocol/input identities remain unchanged.
- Original observer wrapper/backend and relevant rigid-fit dependencies match preserved identities; prior RNG/hook invariance evidence is inherited.
- A pre-execution PowerShell input-list construction error was corrected before scoring. The declaration parent-count field is an array of one per file; manifest checks and independently counted totals are authoritative. Neither issue affected sampling, hashes, scores or gates.

## Research decision and next boundary

Retain this complete mechanism result; do not start a learned head, search score/acceptance/support parameters, or reuse08 as new confirmation after these outcomes. All00/02/08 are now observed development evidence. This bounded result does not establish a new method advantage over pooled RAP or strong registration/system baselines.

Next: synthesize HL-V2 and SC-V1.1 into a short direction decision, separating proposal headroom, ranking benefit and incorrect acceptance. Any new research mechanism or data role needs a justified prospective protocol and fresh confirmation before outcomes. Do not force another selector variant from these development results. Keep manuscript drafting paused pending the research-direction decision.

No weights, backbone, production defaults or upstream model sources changed. Two research helpers were added in RAP-SLAM, with maintenance documents/reporting in RAP-main. Original HEADs4055d92/6d3f2d2 and prior dirty changes remain; no commit/push/pull/reset/cleanup/download. No background experiment remains after validation.

![Fixed control results](results.png)
