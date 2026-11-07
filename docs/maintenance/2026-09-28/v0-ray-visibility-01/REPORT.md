# V0 fixed sensor-ray visibility screen — complete

2026-09-28. Decision: **NO_RAY_INFORMATION_SIGNAL** under the prospective
[protocol](PROTOCOL.md). This is an observed-development information screen
on the exact F2 KITTI00/08 cohorts, not independent confirmation or a RAP
method test. The fixed GT-free ray search did not create one new strictly
correct positive among either sequence's 75 positives. It did not change
the accepted correct/incorrect counts. Therefore the predeclared route to
visibility-guided RAP flow sampling is stopped; do not tune ray tolerances,
score, translation grid, or acceptance gate to rescue V0.

## Execution and result

Synthetic identity, nearer-ray, farther-ray, unseen-ray and known-transform
checks passed before freeze. The protocol, runner, independent validator,
reused loaders, geometric gate code and 291 distinct source/input identities
(including corrected-scan raw sources and evaluator GT files) were SHA-frozen
before any real pair was scored. The runner parsed no GT or stratum labels.
It scored all 27 fixed translations on each of 200 pairs, saved full ray
category counts and same-grid symmetric NN scores, and sealed `bank.json`
at SHA256 `427bb363c6c14cd3babf4459ed82d66c67985e31b0ddb153451754cdd9c9dc3d`
before evaluator-only GT loading. Every native N gate reproduced F2 saved
overlap/mean-distance within 1e-5 and exact acceptance.

Each scan supplied 4096 deterministic query points and its full corrected
raw scan as the ray and NN reference. Both directions were evaluated per
candidate; the native centre had >=0.10 comparable-ray coverage on 100/100
pairs in both sequences (median 0.9420 on00, 0.9551 on08). Thus sparse ray
support did not explain this particular failure. The visibility score chose
a non-centre translation on 22/100 pairs on00 and 15/100 on08; NN did so
on 34/100 in each sequence. V caused zero strict paired gains or losses;
NN caused zero on00 and one gain plus one loss on08 (net zero). Neither
method changed accepted correct/incorrect counts. The NN 08 gain/loss
were both low-overlap pairs with a correct candidate already present in
native K4; neither was accepted.

| Sequence / method | Strict positives /75 | Correct accepts | Incorrect accepts (all 100) | Confuser accepts | Mean clipped positive error |
|---|---:|---:|---:|---:|---:|
| 00 native N | 49 | 23 | 1 | 0 | 1.472846 |
| 00 visibility V | 49 | 23 | 1 | 0 | 1.463318 |
| 00 same-grid NN | 49 | 23 | 1 | 0 | 1.490669 |
| 08 native N | 30 | 17 | 10 | 0 | 1.579930 |
| 08 visibility V | 30 | 17 | 10 | 0 | 1.579930 |
| 08 same-grid NN | 30 | 17 | 10 | 0 | 1.583392 |

Per-stratum strict counts N/V/NN are identical: 00 ambiguous 21/21/21,
low-overlap 3/3/3, ordinary 25/25/25; 08 ambiguous 12/12/12,
low-overlap 3/3/3, ordinary 15/15/15. All 25 confusers per sequence are
strictly wrong and rejected by all three selected methods. Visibility
recovers 0/23 on00 and 0/41 on08 among positives lacking any strict native
K4 candidate. Correctly accepted counts by stratum likewise remain
00 ambiguous/low-overlap/ordinary = 3/0/20 and 08 = 3/0/14.

The slight 00 clipped-error reduction of 0.009528 is an observed secondary
metric, with zero strict or acceptance gain and no similar 08 effect. It
does not meet the frozen decision. The prospective conditions passed for
coverage, 00 safety, strict-regression guard and cost; they failed for 08
missing-candidate recovery, 08 correct-accept gain, and superiority over
the matched NN search. The unchanged 08 incorrect accepts are not a safety
improvement. All results use the original F2 gate, without graph replay.

Bank wall time was 118.319s, peak RSS 0.380GiB and completed V0 artifacts
about 2.5MB, within the 30min/4GiB/1GiB caps. Independent
[`validation.json`](validation.json) passed 715 checks, including all
frozen hashes, exact pair/grid/selection/score arithmetic, source pose and
gate identity, all labels and decision gates, plus independent corrected
raw scans and 216 candidate ray/NN recomputations (8 pairs × 27 offsets).
The temporary `INCOMPLETE` marker was removed after bank seal and summary,
before independent validation. No production/default edits, GPU inference,
training, download, prior-result rerun or Git synchronization occurred.

## Interpretation and boundary

This fixed full-scan ray score had ample angular coverage and sometimes
preferred a nearby translation, yet its executable selection did not cross
the strict 1m/5deg boundary or change acceptance on these two observed
development cohorts. This does not establish that visibility reasoning or
structured guidance fails in general. The chosen 0.4deg/0.75m ray bins,
0.02 regularizer, +/-1m integer grid, translation-only adjustment, static
single-return proxy and one point budget limit the scope. Those parameters
are frozen for this question; changing them would be a different prospectively
defined study, not a V0 continuation.

Do not launch the proposed visibility-guided RAP sampler, change the gate,
or select a post-hoc winner from these 27 offsets. Return to a distinct,
separately scoped RAP model/input-convention or data question before any
training or new GPU experiment. E0 arm A's held-out engineering transfer
remains positive, while F2, E1, R0, G0 and G1 negative decisions persist.
No new thesis mechanism claim is justified by V0.
