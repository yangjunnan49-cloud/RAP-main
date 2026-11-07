# PG-DEV-V1: proposal-context development screen

Decision: **NO_DEVELOPMENT_CONTEXT_SIGNAL**.

Both KITTI00 and KITTI08 are observed development data. This screen
does not establish independent generalization, a new contribution,
or end-to-end SLAM improvement. All historical negative results remain.

| Sequence | Method | Strict successes /75 | Correct accepts /75 | Incorrect accepted /100 | Clipped positive error |
|---|---|---:|---:|---:|---:|
| 00 | A1 | 50 | 22 | 2 | 1.263181736 |
| 00 | A-R4 | 53 | 22 | 2 | 1.091010852 |
| 00 | A-S4 | 54 | 22 | 2 | 1.080597330 |
| 00 | A-OR4 | 57 | 22 | 2 | 0.937255448 |
| 00 | P1 | 56 | 23 | 1 | 1.209213294 |
| 00 | P-R4 | 55 | 22 | 2 | 1.125234297 |
| 00 | P-OR4 | 58 | 23 | 1 | 0.977557884 |
| 08 | A1 | 32 | 16 | 9 | 1.543525882 |
| 08 | A-R4 | 32 | 16 | 9 | 1.393695261 |
| 08 | A-S4 | 31 | 16 | 10 | 1.400363980 |
| 08 | A-OR4 | 37 | 16 | 9 | 1.226284942 |
| 08 | P1 | 36 | 16 | 9 | 1.284832812 |
| 08 | P-R4 | 35 | 17 | 9 | 1.348371041 |
| 08 | P-OR4 | 39 | 16 | 9 | 1.117199431 |

## Fixed conditions and paired transitions

### KITTI00

Decision: NO_DEVELOPMENT_CONTEXT_SIGNAL.

- oracle_gain_5pp: FAIL.
- executable_gain_3pp: FAIL.
- no_worse_than_S4: PASS.
- ordinary_loss_A-R4: PASS.
- no_new_incorrect_A-R4: PASS.
- ordinary_loss_A-S4: PASS.
- no_new_incorrect_A-S4: PASS.
- sampled_cost: PASS.

Versus A-R4: 2 positive successes gained, 0 lost; 0 newly incorrectly accepted pairs, 0 resolved. Helpful transitions do not cancel harm.

Versus A-S4: 2 positive successes gained, 1 lost; 0 newly incorrectly accepted pairs, 0 resolved. Helpful transitions do not cancel harm.

| Stratum | A-R4 successes | A-S4 successes | P-R4 successes |
|---|---:|---:|---:|
| ambiguous_positive | 21 | 22 | 23 |
| low_overlap | 8 | 8 | 8 |
| ordinary | 24 | 24 | 24 |
### KITTI08

Decision: NO_DEVELOPMENT_CONTEXT_SIGNAL.

- oracle_gain_5pp: FAIL.
- executable_gain_3pp: PASS.
- no_worse_than_S4: PASS.
- ordinary_loss_A-R4: PASS.
- no_new_incorrect_A-R4: PASS.
- ordinary_loss_A-S4: PASS.
- no_new_incorrect_A-S4: PASS.
- sampled_cost: PASS.

Versus A-R4: 4 positive successes gained, 1 lost; 0 newly incorrectly accepted pairs, 0 resolved. Helpful transitions do not cancel harm.

Versus A-S4: 5 positive successes gained, 1 lost; 0 newly incorrectly accepted pairs, 1 resolved. Helpful transitions do not cancel harm.

| Stratum | A-R4 successes | A-S4 successes | P-R4 successes |
|---|---:|---:|---:|
| ambiguous_positive | 14 | 13 | 15 |
| low_overlap | 3 | 3 | 5 |
| ordinary | 15 | 15 | 15 |

## Cost and validation

| Sequence | Timed pairs | A-R4 (s) | A-S4 (s) | P-R4 (s) | P/A-S4 |
|---|---:|---:|---:|---:|---:|
| 00 | 10 | 60.824 | 62.354 | 59.757 | 0.9584 |
| 08 | 10 | 40.341 | 41.843 | 40.732 | 0.9735 |

Costs use fixed first10 pairs per sequence, alternating execution order,
fresh pair-local raw caches and warm OS cache. They include preprocessing,
generation, selection and common-anchor gate, excluding evidence I/O/model
load. No separate GPU warmup was run; the first timed arm was A, so startup
overhead can favor P in the sampled ratio. No speed superiority is claimed.
These are sampled development costs, not full-cohort equal-time evidence.

Total process wall: 1040.995s; peak allocated memory: 4.457GiB.

800 new pooled generations,80 timing-only anchor replays and800 inherited
anchor hypotheses. All80 replays reproduce within1e-6; old banks remain the
selection source. Independent audits cover1400 selections,1600 candidate
gates, all stratum aggregates and decisions; 796 distinct raw files
and1664 historical artifacts were rehashed. KITTI00 was validated and frozen
before KITTI08 generation. Exact deltas are in the per-sequence validations.

## Decision boundary

The fixed pooled-context route does not pass the development screen.
Do not expand its Boreas acquisition, tune support distances/thresholds, or
train a selector to rescue this outcome. Preserve the positive and adverse
transitions as diagnostic evidence; do not claim all contextual methods fail.
Next is a scope/direction decision grounded in these measured limitations,
not another automatic variant or data acquisition campaign.
