# Joint accepted-loop pose replacement diagnostic

Authorization: owner requested continuation of the mainline plan on 2026-10-05.
The independently validated fixed interpolation screen failed its material
gates. Stop that route; retain native propagation for this separate diagnostic.
Status: freeze required before real output. No executable method is tested.

Question: what trajectory effect results when every existing accepted loop
pose is replaced jointly by the same-endpoint GT transform? The earlier audit
replaced only one edge at a time. This tests coupled current-edge pose
headroom, not a global ceiling or additive attribution. An exact GT edge can
be less helpful than an inaccurate edge under graph/model mismatch.

Fixed cohort: all six saved E0 A 00/05/06/07/09/10 trajectories. All are exposed.
Freeze this protocol, runner, independent validator, old audit freeze/seal/
validation/results, previous screen validation, odometry, optimized trajectory,
keyframes, source-frame identities, sealed allowlisted old edges/baselines,
GT/calibration and metric/graph dependencies. Verify inherited hashes.

Stage A: create INCOMPLETE and exclusive attempt-01. Copy only old sealed
GT-free edge fields i,j,T_rel,overlap,mean_dist,measurement_id; no labels.
Replay native graphs from saved odometry and require saved baseline agreement
<=1e-5. Seal all six baseline trajectories, edge records and frame IDs before
any new numeric GT load. GT byte hashing for identity is permitted.

Stage B evaluator only: replace every existing edge T_rel with inv(GT[i])GT[j]
simultaneously. Hold endpoints, edge count/order, odometry, prior, initialization,
base Gaussian sigmas, relfloor parameters and Huber kernel settings fixed.
The robust effective influence may change naturally with residuals; it is not
claimed fixed. Keep overlap/mean_dist metadata unchanged; these now preserve
original noise levels, not recomputed geometry of the GT pose. No edge addition,
deletion, graph-parameter changes, inference, selection or GT search for pairs.
Use native constant propagation. Sequence10 is the no-loop identity control.

Save all oracle trajectories, replaced edge ledger, camera KITTI ter/rer,
aligned LiDAR ATE and all exact segment records. Report odometry, native P
and joint J per sequence and arithmetic cohort means. The GT oracle files
must stay in evaluation-01, never the GT-free attempt bank.

Prospective branch criterion (opportunity only): a cohort has a material
joint-pose signal if J improves mean ter by >=0.01 percentage points with
mean ATE worsening <=2%, OR improves mean ATE by >=5% with mean ter worsening
<=0.01 points. At least one cohort satisfying this warrants considering a
system-relevant strong fixed registrar comparator. Report all signs and
sequence effects even if neither cohort qualifies. This gate does not authorize
claiming RAP gains, true algorithmic limits, or independent confirmation.

Independent validator: rehash freeze/bank and verify GT-after-seal ordering;
reconstruct the entire native and oracle graphs explicitly with GTSAM factors
and frozen numerical defaults, independently calibrate GT and recompute all
replacement transforms; check every preserved edge field/base sigma and
oracle trajectory (<=1e-7 matrix-entry agreement), SE(3), source IDs and
sequence10 identity. Recompute ATE via Kabsch and every strict-endpoint KITTI
segment using the independently validated analytic screen validator's metric
functions, without importing this runner's graph/metric/gate functions.
Metrics must agree within 2e-6 and previous baselines within 1e-5.

CPU-only caps: bank+evaluation+validation <=1200 seconds, peak stage RSS<=2 GiB,
artifacts<=500,000,000 bytes. Stop with INCOMPLETE on invariant/cap failure;
frozen files cannot be repaired in place. Remove marker only after validation
and final report. No training, production/default edit, manuscript, commit or
Git sync; all older banks and negative stops persist.
