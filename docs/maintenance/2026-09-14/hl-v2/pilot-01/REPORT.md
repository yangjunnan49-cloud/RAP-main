# HL-V2 untrained hard-loop pilot

Final confirmation decision: **STOP_NEURAL_EXPANSION**. Original HL-V1 INCONCLUSIVE remains unchanged.

The explicitly amended data protocol supplies100 discovery and100 confirmation pairs,25 per fixed stratum. Both are previously observed KITTI development sequences. No independent-domain, pretraining-exclusion, calibrated-risk or publication claim.

| Role | Method | Positive success | Ungated recall | Correct positive accepts | Incorrect / accepted | Clipped positive error |
|---|---|---:|---:|---:|---:|---:|
| discovery | B1 | 50/75 | 66.67% | 22/75 | 1/23 | 1.263182 |
| discovery | B4 | 52/75 | 69.33% | 22/75 | 2/24 | 1.103923 |
| discovery | S4 | 54/75 | 72.00% | 22/75 | 2/24 | 1.080597 |
| discovery | R4 | 53/75 | 70.67% | 22/75 | 1/23 | 1.091011 |
| discovery | OR4 | 57/75 | 76.00% | 22/75 | 2/24 | 0.937255 |
| discovery | REJ | 0/75 | 0.00% | 0/75 | 0/0 | 5.000000 |
| confirmation | B1 | 26/75 | 34.67% | 15/75 | 24/39 | 1.815487 |
| confirmation | B4 | 26/75 | 34.67% | 14/75 | 26/40 | 1.933277 |
| confirmation | S4 | 25/75 | 33.33% | 14/75 | 26/40 | 1.937351 |
| confirmation | R4 | 27/75 | 36.00% | 15/75 | 25/40 | 1.807299 |
| confirmation | OR4 | 29/75 | 38.67% | 15/75 | 24/39 | 1.550009 |
| confirmation | REJ | 0/75 | 0.00% | 0/75 | 0/0 | 5.000000 |

B1=first;B4=same-pair overlap;S4=raw-support score;R4=official mean per-step rigidity criterion;OR4=GT-only oracle;REJ=reject-all. All share one immutable K4 bank. Official criterion availability is now implemented using the original RAP metric functions, not renamed B4.

| Role | Oracle/B4 discrepant positives | Oracle recall gain | Relative clipped-error reduction | S4 gap recovery | Ordinary recall loss | New incorrect pairs | H1 | H2 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| discovery | 18 | 6.67% | 15.10% | 40.00% | 0.00% | 0 | True | True |
| confirmation | 29 | 4.00% | 19.82% | -1.06% | 0.00% | 0 | True | False |

Exact decision metrics and precedence are frozen in the HL-V2 annex, retaining HL-V1 section7. Recall takes precedence when both H1 paths pass. Helpful transitions never offset a newly incorrect S4 acceptance. An oracle is diagnostic, not an executable selector.

## Every stratum

| Role | Stratum | B1 correct | B4 correct | S4 correct | R4 correct | OR4 correct | B4 incorrect accepts | S4 incorrect accepts |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| discovery | confuser | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| discovery | ambiguous_positive | 19 | 20 | 22 | 21 | 23 | 0 | 0 |
| discovery | low_overlap | 7 | 8 | 8 | 8 | 10 | 1 | 1 |
| discovery | ordinary | 24 | 24 | 24 | 24 | 24 | 1 | 1 |
| confirmation | confuser | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| confirmation | ambiguous_positive | 10 | 11 | 10 | 11 | 13 | 6 | 6 |
| confirmation | low_overlap | 3 | 2 | 2 | 3 | 3 | 8 | 8 |
| confirmation | ordinary | 13 | 13 | 13 | 13 | 13 | 12 | 12 |

Positive strata each have25 pairs. Confusers are not positive-recall denominators; their accepted counts/rates are reported in the per-role metrics. All continuous errors,90th percentiles, legacy5m/10deg labels, invalid/failure counts and exact harmful/helpful pair IDs remain in evaluator-only files.

## Runtime and reproducibility

- discovery:400 hypotheses, synchronized pair-wall total 384.864s, full bank-run wall 390.496s, peak allocated/reserved 4.457/8.998GiB; valid hypotheses/support 400/400.
- confirmation:400 hypotheses, synchronized pair-wall total 522.200s, full bank-run wall 527.545s, peak allocated/reserved 4.457/8.998GiB; valid hypotheses/support 400/400.

Pair timings include raw reads, all geometric/learned preprocessing, four generations, official rigidity statistics, support scores and writes. They are warmed-input end-to-end wall times, not isolated kernel-active GPU time. Data preparation, independent validation, literature work and human labour are not included in these bank timings; human labour was not separately instrumented.

The ten-pair amended-support preflight passed40/40; RNG repeat and observed-versus-original sampler transform deltas were exactly0. Two extra preflight requests are validation only. The800 scored hypotheses were generated once each under request-local seeds; no oracle retries or resampling. No GT-derived fields enter inference selectors.

KITTI00 discovery results and complete bank were independently verified and hash-frozen before KITTI02 inference. Final validation reverified that freeze and all data artifacts,800 seeds/transforms/support records, selection denominators and gate calculations. Independent pose errors used direct translation differences and scipy rotation magnitudes.

## Interpretation and scope

Data shortages were resolved through a prospective, documented expansion of real proposals and causal raw support. No GT threshold, strict correctness definition, H1/H2 criterion, model weight or production default was changed. The original pilot remains a separate inadequate-cohort result. This expanded case-control pool does not estimate production false-loop prevalence; low-overlap misses can also be rejected by the unchanged same-pair gate. Report ungated selection and gated acceptance separately.

R4 is a stronger same-input alternative than B4 and must remain visible. Any small S4 advantage over B4 alone does not establish a novel method or advantage over the official criterion. Same-data pooled-support and equal-compute controls plus new geographic/domain evidence remain required before learned-method claims.

MulRan official download access was checked and requires name/affiliation/email; none were invented or submitted. Local complete data were sufficient for this pilot, so additional raw downloads were unnecessary. The owner authorizes future public downloads. NCLT remains reserved for external testing.

Next: stop neural-head expansion. First diagnose fixed support-score failures, short-motion error and harmful transitions on these now-development data; any revised scoring proposal requires a new frozen protocol before confirmation. Do not silently tune thresholds.

No commit, push, pull, reset or cleanup; both worktrees keep existing dirty changes and original HEADs4055d92/6d3f2d2. Upstream source/production defaults unchanged.
