# Metric-first research reassessment — 2026-09-29

Status: source review and research decision, no experiment frozen or run. This
revises the priority in the earlier [breakthrough memo](../breakthrough-reassessment-01/RESEARCH_MEMO.md):
a strong external pair matcher remains a useful conditional comparator, but
the immediate next step is to attribute **full-system metric** errors.
The owner's objective is a RAP-centred, original improvement in trajectory
metrics. No new inference, optimization, download, training, default edit or
Git sync occurred here.

## The error we should optimize

The [official KITTI odometry evaluation](https://www.cvlibs.net/datasets/kitti/eval_odometry.php)
averages relative translation/rotation errors over 100–800 m segments. Our
aligned LiDAR ATE measures the globally aligned trajectory. A loop may lower
ATE while increasing segment drift. Pairwise 1 m/5 degree success is a
mechanism diagnostic, not either system objective.

Existing [E0 development](../../2026-09-26/e0-frontend-01/REPORT.md) and
[held-out engineering-transfer](../../2026-09-27/e0-heldout-01/REPORT.md)
per-sequence results give these newly calculated descriptive means:

| Cohort | Odometry ter | Full ter | Odometry ATE | Full ATE |
| --- | ---: | ---: | ---: | ---: |
| 00/05/06 observed development, E0 A | 0.37455% | 0.38872% | 1.94383 m | 1.46066 m |
| 07/09/10 engineering transfer, E0 A | 0.47723% | 0.50563% | 0.77807 m | 0.72147 m |

In both groups, loops lower mean ATE while slightly worsening mean ter.
Sequence 10 accepts no loops, so its E0 improvement is front-end only.
Sequence 09's ten accepted loop transforms all fail the strict pair label,
but still improve aligned ATE and worsen ter versus odometry. This does
not mean inaccurate loops are safe; it shows why strict pair labels cannot
stand in for graph utility. E1's fixed NMS/weight/GNC alternatives had no
material metric gain, so routine backend tuning is a low-priority path.

There is also a **cohort/interface gap**. F2 uses balanced observed pairs,
six-part 8,000-point K4 RAP; E0 uses online retrieval, 4,000-point K1 RAP
and different candidate frequencies. F2's 41/75 missing strict hard08
candidates and M1's failed support-pose screen are valid pair evidence,
but neither quantifies opportunity to improve E0's trajectory. Improving
the hardest balanced pair is not automatically improving the mainline.

## Primary literature and what it changes

The table records mechanism, not transferable headline scores. The
closest full-text papers were inspected alongside official repositories
and abstracts for the others.

| Family | Primary works | Mechanism and boundary for us |
| --- | --- | --- |
| Local motion | [KISS-ICP](https://arxiv.org/abs/2209.15397), [KISS-SLAM](https://arxiv.org/html/2503.12660v1) | Strong scan-to-local-map odometry, then local-map loops. Same-data KISS-SLAM already has lower ter on 07/09/10. Loop-pair recall alone is unlikely to erase a local-motion gap. |
| Local temporal geometry | [CT-ICP](https://arxiv.org/abs/2109.12979), [GenZ-ICP](https://arxiv.org/abs/2411.06766), [GLIM](https://arxiv.org/html/2407.10344v1) | Continuous motion, degeneracy-aware weighting, and fixed-lag multi-frame matching target local drift. GLIM includes IMU, so its result cannot transfer to a LiDAR-only RAP arm. Prior KITTI deskew work here was negative. |
| Map representation | [PIN-SLAM](https://arxiv.org/abs/2401.09101), [GLIM](https://arxiv.org/html/2407.10344v1) | Scan-to-model or direct scan-matching factors retain geometry beyond a frozen pair pose. Replacing our pipeline wholesale would not demonstrate a RAP contribution. |
| Place retrieval | [Scan Context++](https://gisbi-kim.github.io/publications/gkim-2021-tro.pdf), [OverlapTransformer](https://arxiv.org/abs/2203.03397) | Better retrieval can help only where missed *graph-useful* revisits exist. |
| Structural pose | [KISS-SLAM](https://arxiv.org/html/2503.12660v1), [BEVPlace++](https://arxiv.org/abs/2408.01841), [RING++](https://arxiv.org/abs/2210.05984), [Quatro++](https://quatro-plusplus.github.io/) | BEV, ground structure and broad planar translation are substantial prior art against the earlier rotation-conditioned translation idea. |
| Joint place and pose | [LCDNet](https://arxiv.org/abs/2103.05056), [LCR-Net](https://arxiv.org/abs/2309.08086), [RING#](https://arxiv.org/abs/2409.00206) | Joint retrieval and pose estimation is established; wrapping one in RAP is not originality. |
| Cross-view matching | [GeoTransformer](https://github.com/qinzheng93/GeoTransformer), [UGP](https://github.com/peakpang/UGP), [Regor](https://openaccess.thecvf.com/content/CVPR2025/papers/Zhao_Progressive_Correspondence_Regenerator_for_Robust_3D_Registration_CVPR_2025_paper.pdf) | Strong conditional comparators for a demonstrated loop-pose bottleneck. Their cohorts/thresholds and legacy software stacks differ from ours. |
| Graph robustness | [Switchable Constraints](https://nikosuenderhauf.github.io/assets/papers/IROS12-switchableConstraints.pdf), [GNC](https://arxiv.org/abs/1909.08605) | Wrong-edge rejection is mature; E1's tested variants did not move our metric materially. |
| Graph utility and uncertainty | [Loop Closure Prioritization](https://arxiv.org/abs/2205.12402), [Reliable Graphs for SLAM](https://www.mit.edu/~mrrobot/assets/khosoussi19ijrr.pdf), [Deep Bayesian ICP Covariance](https://arxiv.org/abs/2202.11607) | Spend compute on graph-informative loops and model geometry-dependent confidence. Both concepts have prior art and RAP disagreement is not yet calibrated uncertainty. |

The especially close [2026 information-aware/retroactive-loop paper](https://arxiv.org/html/2607.13516v1)
already combines geometry-dependent odometry information, hierarchical
local maps, graph feedback and recovery of missed loops. It also separates
trajectory accuracy from revisit map consistency. Generic submap/retroactive
loop/uncertainty combinations should not be called novel here. RAP itself
already [directly generates multi-view registered points](https://arxiv.org/html/2512.01850v2),
so merely using its multi-view mode is also insufficient as a contribution.

## Revised next step: frozen system opportunity ledger

Before another external matcher or RAP variant, use saved E0 A trajectories,
retrieval/proposal logs and graph edges on 00/05/06/07/09/10. Freeze exact
inputs, calculations, resource caps and an independent validator before
case-level outcomes. This is an evaluator-only diagnostic, not method tuning.

1. Recompute per-segment 100–800 m ter/rer and aligned ATE for odometry
   and full system. Record frame IDs, spatial location, loop coverage and
   improvement/regression by sequence, not just aggregate means.
2. Re-optimize saved graphs with each accepted edge omitted once, using
   its unchanged measured pose/weight. Separately, replace the transform
   of a saved accepted edge with its GT relative transform at the **same
   endpoints** as a clearly labeled oracle diagnostic. This asks how much
   better loop poses on current edges could move the trajectory; it is not
   an executable selector or a general upper bound.
3. For online proposed pairs, count GT-valid revisits absent from retrieval,
   reached but rejected by RAP, and accepted with pose error. If testing
   a missed-loop oracle, limit it to those *already proposed* endpoints
   and label it as an evaluator-only ceiling. Do not search all GT pairs.
4. Locate high-contribution odometry intervals and compare same-data
   KISS-SLAM and our odometry errors while preserving their pipeline
   differences. Determine whether the gap is diffuse or concentrated in
   weakly constrained intervals; do not attribute it to RAP without a
   RAP local-motion intervention.

Leave-one-edge-out and oracle effects interact across the graph; they
are **not additive causal shares**. Preserve both ter and ATE. For every
proposed algorithm, require a later GT-blind executable result on actual
system candidates and a separately reserved trajectory confirmation.

## Conditional research branches

**If local drift dominates:** test RAP as a *local multi-view motion
estimator* on preselected high-contribution intervals, under equal scans,
points and compute versus geometric multi-scan optimization and the
saved KISS odometry. Require segment-level relative drift benefit and
stable-segment safety before a complete trajectory. A potentially
distinct contribution would have to exploit RAP-generated point-level
joint motion or a demonstrated direction-specific signal, not simply
add a model call. GLIM, PIN-SLAM and RAP are close prior art; no benefit
or novelty is established yet.

**If loop opportunity dominates aligned ATE:** focus on *actual retrieved
high-leverage revisits*, separating retrieval, pose generation, GT-blind
acceptance and graph effect. Compare RAP submap/multi-view use with a
direct BEV/submap matcher and single-scan RAP at matched cost. Only then
does an official GeoTransformer-style same-pair comparator become the
best use of effort. Its checkpoint provenance and old runtime are still
feasibility gates. An algorithm must beat the direct matcher on system
effect, not merely reproduce its pose.

**If neither has material ceiling:** recheck metric/frame correctness and
data roles; do not rename a negative pair outcome as a system improvement.
A different trajectory cohort or map-consistency objective would require
a separate owner-level scope decision.

The candidate original insight is an *interface gap*: RAP can generate
joint point-level structure, but the current system consumes a single
pair pose in a sparse graph and gets nearly all local motion from KISS-ICP.
This remains a hypothesis. The next audit determines whether bridging it
has metric headroom. Preserve E0 engineering transfer, E1/F2/P0/M1 stops,
manuscript pause and no Git sync.
