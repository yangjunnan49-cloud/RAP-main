# R0: fixed local-refinement recoverability preflight

Owner authorized execution of the post-F2 action plan on 2026-09-27. R0 is a
separate, narrow question prompted by the completed F2 postmortem: can a
standard local geometric refiner create correct poses from RAP's selected
native proposals on the saved 00/08 banks? ICP is prior art and a baseline,
not a proposed original method. This is observed-development feasibility,
not independent confirmation or graph-level efficacy. It does not reopen
F2's structured-motion/pooled arms, change F2's decision, or tune its gate.

## Frozen inputs and GT separation

Use all 100 saved pair identities on each F2 sequence 00/08, saved order,
without replacement. Runner reads only F2 `records.json` and each pair's
`inputs.npz`; never evaluator rows, strata, GT, or a cross-visit odometry
prior. Select the N generation by minimum saved valid raw rigidity RMSE,
breaking ties by generation index, exactly as F2 R4. Input anchor points
are `points[0:2000]` (target i) and `points[4000:6000]` (source j), from
the exact same corrected-data F2 retained set; do not transport supports.
The F2 pose maps j to i. Freeze all source/input hashes before any fit.

## One fixed baseline (no search)

From each saved N selected pose, run point-to-point ICP on the two 2000-point
anchors using Euclidean nearest neighbours, a strict <1.0 m correspondence
cutoff, minimum 50 correspondences, proper SE(3) SVD refit, and at most 30
iterations. Stop early when maximum matrix-element change <1e-6. If fewer
than 50 correspondences exist, return the original pose with an explicit
status. No learned weights, normals, robust loss, threshold adjustment,
multi-start, GT initialization, or post-hoc arm choice. Record the original
and refined transforms, correspondence count, RMSE, iteration count and
status for every pair. Runner seals this bank with a SHA256 before evaluator
labels are read.

The evaluator then uses the same frozen F2 strict <=1m and <=5deg pose
labels and clipped positive error, on all 75 positives and 25 confusers per
sequence. Report paired strict gains/losses, newly/resolved wrong poses,
no-correct-N-K4 cases recovered, error means, and per-stratum outcomes.
No acceptance or trajectory claim: the F2 4000-point common gate is not
recomputed from this 2000-point baseline. A refined pose is never silently
substituted into the completed F2 decision.

## Prospective use of the result

R0 provides a reason to investigate a distinct visibility-aware residual
method only if, on 08, ICP yields at least 3 net additional strict positives,
mean clipped positive error <=0.95 times native N, and at most one positive
pair loses strict correctness. On 00, at most one positive pair may lose
strict correctness. Report all confuser transformations, but without a
recomputed common gate they cannot be called accepted false closures.
Passing only licenses a separately scoped method
protocol and strong comparison; it does not make ICP novel or justify a
production change. Otherwise stop this simple local-refinement route and
select a genuinely different mechanism question. This is a descriptive
development gate, not a claim of statistical significance.

Separate validation must recompute source/input/bank hashes, selection
identities, SE(3), label arithmetic, paired transitions, margins and caps.
CPU-only; wall <=30 min, peak RSS <=4 GiB, new artifacts <=2 GiB; no network,
GPU inference, training, production edit or Git synchronization. Any
correctness repair needs an amendment and a new execution directory.
