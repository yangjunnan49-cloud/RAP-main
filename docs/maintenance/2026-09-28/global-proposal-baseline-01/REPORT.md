# G0 fixed 2000-point global proposal comparator — complete

G0 tested official KISS-Matcher v1.0.2 with one fixed 0.3 m resolution on
the exact F2 corrected 2000-point anchors for all 100 saved pairs of KITTI
00 and 08. This is observed development and a matched-point component
comparator, not a full-scan benchmark or RAP innovation. The pinned PyPI
wheel matched its published SHA256; a synthetic source-to-target smoke test
passed before the 345-file protocol/source/input/package freeze. All 200
poses were sealed before GT/evaluator parsing. An independent validator
passed 552 identity, geometry, label and arithmetic checks. The INCOMPLETE
marker was removed administratively after the sealed bank and
summary were present, before independent validation; no source or outcomes
were changed.

Decision: **NO_GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL** under the frozen gate.

| Sequence | Native N/R4 strict /75 | KISS-Matcher strict /75 | Native K4-unavailable recovered | Native / matcher clipped positive error |
|---|---:|---:|---:|---:|
| 00 | 49 | 0 | 0/23 | 1.472846 / 4.999573 |
| 08 | 30 | 0 | 0/41 | 1.579930 / 4.995675 |

Every API result was finite SE(3), but that does not mean registration
succeeded: 68/100 and 72/100 pairs on 00/08 had zero final inliers, and
199/200 had fewer than five. The official synthetic quickstart itself uses
fewer than five inliers as a likely-failure indicator. Runtime for the 200
fixed calls was about 2.0 s, not evidence of a useful fast matching route.
The primary limitation of this test is severe sparsity for a feature-based
global matcher at this fixed 2000-point input and 0.3 m resolution.

This result stops G0's fixed input/configuration; it does not show that
KISS-Matcher fails on full raw scans or that independent global registration
cannot help RAP. There is no gate, accepted-loop or graph claim. A separate
full-scan comparator can establish the strong external baseline already
envisaged in the research memo, with its higher point and cost budget
reported explicitly. It must not be conflated with equal-point RAP gains.

Sources: [KISS-Matcher paper](https://arxiv.org/abs/2409.15615),
[official quickstart](https://github.com/MIT-SPARK/KISS-Matcher/blob/main/python/examples/quickstart.py),
[pinned PyPI release](https://pypi.org/project/kiss-matcher/).
