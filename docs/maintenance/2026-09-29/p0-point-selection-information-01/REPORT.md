# P0 full point-selection information audit — complete

Decision: **NO_MATERIAL_INFORMATION_SIGNAL** under the prospectively frozen
[protocol](PROTOCOL.md). This is an observed-development input-information
diagnostic on the exact F2 KITTI 00/08 cohorts, not RAP pose generation,
loop recall, independent confirmation or an algorithmic contribution.

## Execution and validation

P0-01's unseeded engineering bank failed reproducibility and remains marked
incomplete. The separately frozen P0-02 correction passed all 261 preflight
checks, including exact regeneration of 24 point/feature parts. The full P0
protocol, runner, independent validator and 1,228 source/input identities
then froze before any full output. All 200 pairs retained the exact six-part
8,000-point F2 budget. The 0.25 m/FPS arm used complete pre-outlier voxel
support for 5 m miniSpinNet descriptors; F2/C1 files remained unchanged.

The complete GT-free bank was sealed at SHA256
`ac90351504e1a45b47312710a9a177564eb7aae5b6aef6687c63fa3c3c67033a`
before evaluator GT or labels were read. Bank wall 200.788 s, peak allocated
GPU memory 2.090 GiB and artifacts 208.136 MB passed the frozen 30-minute,
12-GiB and 1-GiB caps. Independent validation passed 3,252 checks across
all 200 bank artifacts and pair metrics/16 controls, reproduced F2/C1
metrics and the frozen decision, and matched the four full-bank preflight
pairs exactly to the separately validated P0-02 outputs. No `INCOMPLETE`
marker remains.

## Pair-level finding

For each arm, geometric coverage is the fraction of source anchor points
with a target anchor within 1 m under evaluator GT. Information is
conditional top-1 descriptor recall minus the mean of 16 fixed shuffled
target-coordinate controls. The pair is the sampling unit.

| Observed group | Pairs | F2 / P0 adequate | F2 / P0 median coverage | Median paired information gain |
| --- | ---: | ---: | ---: | ---: |
| 08 native K4 unavailable | 41 | 33 / 39 | 28.9% / 36.9% | +0.267 pp across all 41 |
| 08 native K4 available | 34 | 33 / 33 | 65.7% / 70.7% | -1.638 pp |
| 00 native K4 unavailable | 23 | 16 / 20 | 12.2% / 15.5% | +0.321 pp |
| 00 native K4 available | 52 | 52 / 52 | 51.5% / 56.6% | +0.069 pp |

The frozen primary comparison uses the **33** hard08 missing-candidate
positive pairs with >=10% eligibility in *both* arms. Their median
paired P0-minus-F2 information gain is **+0.334 percentage points**, far
below the predeclared **+10 percentage-point** requirement. Gains are
positive on 23/33 pairs, meeting the two-thirds sign condition, and the
common-adequacy count exceeds 20. Both ordinary controls pass their
no-material-regression guards: median paired gains are +0.716 pp on 00
and -1.455 pp on 08, each with 25/25 nonzero-eligibility pairs. The
primary magnitude condition fails, so the frozen decision is negative.

P0 increases geometric coverage on these cohorts but does not supply a
material conditional descriptor-information advantage on the hard08
common-eligible pairs. Coverage and information are reported separately;
more point support is not a demonstrated RAP candidate, acceptance or
graph improvement. The comparator jointly changes voxel size, FPS
keypoints and patch support, and uses fixed counts rather than the paper's
adaptive allocation. These results cannot identify an individual cause or
establish that the upstream paper recipe fails generally.

## Boundary

Retire this exact 0.25 m/FPS/full-support fixed-budget arm. Do not run a
P0-driven RAP-generation rescue, voxel/seed/count/radius sweep, training,
default change or paper-number comparison. The exact local 12-layer
checkpoint's training membership remains unknown; S1's ten-step route
and C/I negative stops persist. E0 arm A remains the held-out engineering
metric result. No RAP algorithmic gain or original breakthrough has been
established; the manuscript pause and no-Git-sync boundary persist.
Further research requires a distinct prospectively frozen candidate-creation
hypothesis with novelty audit and matched controls, or a thesis-scope
decision with the owner. No such next experiment is frozen here.
