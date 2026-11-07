# G1 full-scan global proposal comparator — complete

Under the prospective [protocol](PROTOCOL.md), the same official pinned
KISS-Matcher v1.0.2/0.3 m configuration as G0 ran once on the full corrected
raw anchor scans for every one of the F2 100 KITTI00 and 100 KITTI08 pairs.
The scan convention was range>=1.5 m before the unmodified 0.205 deg
correction. Mean retained points per target/source were 120,864/120,072
on00 and 123,510/122,953 on08, versus G0's 2,000/2,000.
The source, package and 421 distinct raw/input identities froze before
matching. The 200-pose bank was SHA256-sealed before GT/evaluator parsing;
independent validation passed 628 checks. The INCOMPLETE marker was removed
administratively after bank and summary completion, before validation. No
RAP inference, GPU, training, raw acquisition, production edit or Git sync.

Decision: **NO_GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL** under the same frozen
G0 decision gate.

| Sequence | RAP N/R4 strict /75 | Full-scan matcher strict /75 | Matcher gains / losses vs RAP | Recovered from native K4-unavailable | RAP / matcher clipped positive error |
|---|---:|---:|---:|---:|---:|
| 00 | 49 | 31 | 0 / 18 | 0/23 | 1.472846 / 3.09 |
| 08 | 30 | 20 | 0 / 10 | 0/41 | 1.579930 / 2.99 |

All matcher strict successes are a subset of RAP native strict successes.
It yielded no new strict candidate on either sequence, including 08's 41
native K4-unavailable positives. Low-overlap strict successes were 0/25 on
both sequences (RAP N/R4 had 3/25 each). API calls returned 200 finite
SE(3) matrices, but zero final inliers occurred on 33/100 (00) and 30/100
(08), and fewer than five on 55/100 and 50/100 respectively. Median final
inliers were 3 and 4. This is stronger input support than G0, yet still
uneven; a matrix return alone is not proof of reliable registration.

CPU bank wall was 39.2 s, peak RSS and other caps are in `bank_seal.json`;
validation and artifacts are in `validation.json`. The matcher had a much
larger point budget than RAP, so these figures are not equal-budget runtime
or algorithmic comparisons. On the fixed same-pair, full-scan test there
is no evidence that this external global matcher supplies RAP's missing
candidates. Do not integrate it as a RAP novelty claim or tune 0.3 after
this outcome. G0/G1 do not rule out other global registration designs.

The next research step must change the candidate-creation mechanism, with
source/novelty audit and a separate frozen experiment. Correct-pose rejection
and executable loop safety remain distinct from candidate availability;
neither G0 nor G1 evaluated the common acceptance gate or graph impact.
