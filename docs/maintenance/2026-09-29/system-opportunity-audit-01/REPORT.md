# E0 A full-system metric opportunity audit

Status: **VALIDATED evaluator-only diagnostic**. No new RAP inference, training or production edit.

| Sequence | Accepted/attempted | Odom ter % | Full ter % | Odom ATE m | Full ATE m |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00 | 12/12 | 0.513202 | 0.518171 | 3.741265 | 2.754437 |
| 05 | 12/12 | 0.330504 | 0.320473 | 1.652975 | 1.294699 |
| 06 | 12/12 | 0.279935 | 0.327512 | 0.437263 | 0.332854 |
| 07 | 12/12 | 0.383823 | 0.394673 | 0.366580 | 0.326400 |
| 09 | 10/12 | 0.519444 | 0.593652 | 1.204099 | 1.074523 |
| 10 | 0/11 | 0.528520 | 0.528520 | 0.763516 | 0.763516 |

Segment, leave-one-edge-out, same-endpoint GT replacement and online attempted-candidate records are in `results.json` and `evaluation-01`. Omission effects are nonadditive; oracle replacements are not executable improvements or a global ceiling.
The verification log covers RAP attempts, not the complete retrieval shortlist. F2 balanced pairs are a different distribution from this online E0 arm.
Independent validator passed 7 check groups. Bank+evaluator+validator wall 32.57s; maximum stage peak RSS 0.104GiB; audit artifact size 35.10MiB. These resources exclude prior E0 generation.
The owner requires an original RAP-centred metric improvement; this diagnostic alone makes no method claim.

## What the frozen interventions show

The arithmetic development means (00/05/06) are odometry/full ter
0.374547/0.388718% and aligned ATE 1.943835/1.460664m. The exposed
engineering-transfer means (07/09/10) are 0.477262/0.505615% and
0.778065/0.721480m. Loops therefore improve mean ATE while worsening
mean ter in both groups. Individual accepted-edge omissions are mixed:
33/58 included edges lower ATE versus omitting that edge, while 26/58
lower ter. These counts are not additive edge contributions.

The 58 accepted edges came from 71 online RAP attempts. All 12 attempts on
00/05/06/07 were accepted in each sequence; 09 accepted 10/12 and 10
accepted 0/11. Of the 13 rejections, the two on 09 were within the
saved 15m GT place-distance criterion; all 11 on 10 were farther than
15m. There were 46 strict (<1m,<5deg) accepted selected poses, including
10/12 on 00 and all 12 on each of 05/06/07, but 0/10 on 09. This ledger
contains RAP verification attempts, not the complete retrieval shortlist.
It does **not** estimate retrieval recall or how many graph-useful loops
were missed on 10.

On 09, the ten accepted measurements have 3.64–4.13m translation error
against their same-endpoint GT transforms, yet the full graph lowers
aligned ATE by 0.129576m and raises ter by 0.074208 percentage points
versus A odometry. Replacing each one edge with GT separately improves
ter by at most 0.002185 points; some replacements *worsen* ATE by up to
0.096347m. Across all sequences, the best one-edge GT replacement ter
gains are only 0.005049/0.002808/0.002938/0.007351/0.002185 points
for 00/05/06/07/09. ATE has more isolated headroom: the best such
single-edge replacement on 00 lowers ATE by 0.247772m, and on 09 by
0.054474m. Joint replacement could behave differently; these are
one-edge interventions, not an all-edge ceiling or an executable selector.

The worst 10% of the overlapping odometry segments carry
29%/21%/23%/22%/21%/21% of the segment translation-error sum on
00/05/06/07/09/10. This descriptive concentration does not reveal one
dominant isolated failure site. Segment records preserve every exact
start/end and 100–800m length for follow-up.

## Revised research choice

The prior review considered RAP-assisted local motion because same-data
KISS-SLAM **full-system** ter was below E0 A **full-system** ter on
07/09/10. Comparing like metric stages changes that interpretation:
E0 A *odometry* ter 0.383823/0.519444/0.528520% versus KISS-SLAM
*full-system* 0.386563/0.542063/0.525043% on 07/09/10. E0 A odometry
is already slightly better on 07 and 09; 10 differs by just 0.003477
points. The pipelines differ and KISS local odometry alone was not
isolated here, so this is not a controlled superiority claim. It removes
the evidence for a broad front-end deficit as the immediate bottleneck.

The narrower, metric-connected question is how optimized keyframes are
propagated to every scan. Current `pose_graph.propagate_to_full_trajectory`
assigns each interval a constant left correction from its preceding
keyframe; corrections can jump at the next keyframe. That is an interface
fact, **not** proof it caused the ter regression. A fixed smooth
keyframe-correction comparator on unchanged E0 graphs is the next bounded
engineering diagnostic. [Jang et al. (2020)](https://arxiv.org/abs/2009.08724)
already studied correcting non-keyframes and compared interpolation
methods on KITTI, so generic interpolation is not a new research
contribution. The [next-round plan](NEXT_ROUND_PLAN.md) states the
prospective comparison and stop gate. If it fails, stop the propagation
route. If it passes, keep the result as an engineering metric gain and
still require a separately frozen RAP-specific mechanism and confirmation
for the owner's original-breakthrough goal.

## Provenance and limits

`freeze.json` recorded 62 source/input hashes before output. The GT-free
bank sealed 77 files before the evaluator loaded GT. All six native E0
optimized trajectories reproduced within 7.56e-7 maximum pose-entry
difference, and the independent validator rehashed the freeze and bank,
recomputed every baseline metric and candidate label, and replayed one
omission/oracle per edge-bearing sequence. It passed seven check groups.
The 32.57s wall and 0.104GiB peak RSS are for this CPU-only audit, not
the original E0 inference. No production/default edit, training, Git
sync, manuscript change or RAP algorithmic gain occurred.
