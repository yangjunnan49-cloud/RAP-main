# O2: fixed candidate budget comparison

Declared before O2 execution on 2026-09-13. Compare budgets 12 and 40 on
the four full fresh frontends in 2026-09-11/full-{poss,kitti06,kitti05,kitti00}-01.
Reuse only odometry, keyframes and explicit source-frame binding. Regenerate
descriptors, proximity/SC retrieval, RAP measurements and PGO for both budgets.
Use the full frontend protocol settings: proximity 15 m, separation 200 frames,
SC threshold 0.25 and shortlist 10; apply the budget to each proposer and merge.
Proximity retains production priority. Record each proposer and merged ordering;
do not assume the larger merged list contains the smaller list.

Frozen RAP, voxel 0.4 m, cap 4000, five steps, learned features, one generation;
seed 42 reset before each sequence/budget verification. Shared RNG follows each
candidate order, so changed order may change measurements of overlapping pairs.
This is a budget-policy comparison, not a pure added-edge causal isolation.
Heuristic overlap >= 0.7 and mean distance <= 2.5 m, relfloor + Huber, NMS 0.
No ICP refinement, GT-based selection, parameter tuning or frontend rerun.

Run sequentially with OMP/OPENBLAS threads 4. Share regenerated descriptors
between the two budgets of a sequence. Record monotonic descriptor, retrieval,
verification and PGO seconds separately; model startup is shared and reported
separately. These warm single-run timings are not end-to-end throughput claims.

Validate source hashes against full-run manifests, frame IDs and lengths,
complete attempts/generations, gates, rigid transforms and exact edge references,
finite saved trajectories and recomputed metrics. Compare budget-12 candidate
order and APE to the full-run reference; report discrepancies rather than tune.
Preserve all failed/incomplete products under a marker. No legacy overwrite.

Report per-sequence first-pose/aligned LiDAR APE, separate camera KITTI drift
(POSS LiDAR custom drift), accepted/rejected safe/dangerous counts and candidate
overlap. Development screen: 40 improves first-pose APE on at least three of
four sequences, no regression exceeds 5%, and no dangerous edge is accepted.
If fewer candidates exist than requested, report saturation, not a failure.
Retain secondary metric regressions. This screen does not validate generalization
or statistical calibration and does not automatically change production defaults.
