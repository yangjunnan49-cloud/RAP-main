# C6: causal loop-pose transport screen

Status: frozen only when `freeze.json` exists. This is an observed-development
candidate-information screen on the unchanged F2 00/08 pairs, not a registration
method or a thesis novelty claim. No inference, training, scan matching, gate
change, or system run is authorized by this protocol.

## Question and prior work

Can an already accepted earlier loop pose, carried through short local odometry
segments on both visits, create a strict pose candidate absent from F2 native K4?
Loop reuse and retroactive closure are established ideas; see
[DeepMapping2](https://openaccess.thecvf.com/content/CVPR2023/html/Chen_DeepMapping2_Self-Supervised_Large-Scale_LiDAR_Map_Optimization_CVPR_2023_paper.html)
and [retroactive loop closure](https://arxiv.org/abs/2607.13516).
C6 tests feasibility in RAP's fixed sample only.

## Frozen policy

- Exact F2 100 saved pairs each on KITTI 00/08. F2 selected native N/R4 pose
  minimizes `(rigidity_rmse_m, generation)` among valid four generations.
- A donor must be another F2 pair `(a,b)` with both `a<i`, `b<j`, both index
  gaps at most 50, and its selected N/R4 pose accepted by the **existing**
  F2 geometric gate. Donor choice minimizes `(max(i-a,j-b), (i-a)+(j-b), a, b)`.
  No GT field participates in choice. No chaining or use of later pairs.
- With saved loop pose `T_ab` mapping source b to target a, and saved unoptimized
  KISS-ICP odometry poses `O_k` mapping scan k to world, transport by
  `T_ij = inv(O_i) O_a T_ab inv(O_b) O_j` (source j to target i).
- Paired odometry-only control on precisely the same eligible queries is
  `inv(O_i) O_j`. Uncovered queries produce no candidate. Native K4 remains
  the reference and is never replaced by a transport pose.
- Freeze protocol, scripts, F2 records/gates/inputs and both odometry arrays.
  Generate and SHA-seal **all** GT-free candidates before parsing any F2
  evaluator outcomes or KITTI GT. Evaluate strict pose error at 1m/5deg.

The 50-frame window was chosen before inspecting evaluator labels. A read-only
GT-blind index/gate census found 00=22/100 and 08=15/100 covered. Subsequently,
before this freeze, the existing F2 label file was inspected for scope and showed
8 of 41 hard08 native-K4-unavailable positives covered. Thus this is explicitly
an observed-development screen and cannot serve as independent confirmation.

## Decision and bounds

`CANDIDATE_INFORMATION_SIGNAL` requires at least 2/8 strict transport
recoveries among those hard08 positives, at least 2 more such recoveries than
odometry-only, and all bank/validator checks passing. Otherwise
`NO_CAUSAL_TRANSPORT_SCREEN_SIGNAL`. Report all exposed strata and donors,
including incorrect accepted donor labels, only after bank seal. A positive
screen would license a separately frozen common-gate/safety test; it would not
justify use in the live system. Stop this exact donor/window policy on a
negative result; no post-hoc window enlargement or donor rescue.

Wall cap 10 minutes, peak RSS 2 GiB, artifacts 10 MB. Original F2 artifacts
are read-only. Original repository source/defaults and Git states stay intact.
