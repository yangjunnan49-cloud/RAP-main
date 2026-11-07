# M1: support-derived RAP pose-hypothesis availability screen

Freeze before constructing any real candidate output. This is a CPU-only,
GT-blind candidate-creation screen on the 200 exact F2 observed-development
KITTI00/08 pairs, four saved native N generations per pair. It uses only
the immutable F2 `N0..N3.npz` six per-part `raw_poses` and each pair's six
saved local `motions`. No new RAP inference, raw scan processing, training,
default edit or selector is part of M1.

## Geometric construction

The saved local motion `L_gk` maps scan k of visit g into that visit's
anchor frame (`L_g0=I`). The RAP per-part pose `G_gk` maps scan k into
the generated common frame. Each part independently proposes a pose for
its visit anchor: `H_gk = G_gk @ inv(L_gk)`. For a target visit `i`
and source visit `j`, form all nine source-to-target anchor transforms
`T_ab = inv(H_ia) @ H_jb`, a,b in {0,1,2}, in fixed target-major order.
Part indices are 0..2 and 3..5. Store four times nine matrices per pair;
do not pool, average, deduplicate or select after generation. `T_00` must
equal the original F2 native `N` pose exactly up to 1e-10. A synthetic
nontrivial SE(3) test must reproduce a known loop transform and common
gauge invariance before freeze. Assert proper finite SE(3) and source
identities. The bank runner may hash evaluator GT/labels but cannot parse
them. Seal the complete 200-pair candidate bank before evaluation.

## Evaluator and stop rule

Only after bank sealing, use the exact F2 relative truth
`inv(GT_i) @ GT_j`; strict correctness is translation <=1 m and rotation
<=5 degrees. Recompute each F2 native K4 oracle label from the `T_00`
rows and require exact agreement with saved evaluator-only decisions.
The primary group is the 41 KITTI08 positives without any strict native
N/K4 candidate. Count a pair as newly available if *any* of its other
35 support-derived candidates is strict. Also count interior successes
with translation <=0.8 m and rotation <=4 degrees. A material headroom
signal requires >=5/41 new strict pairs and >=3/41 new interior pairs.
If it fails, retire this exact support-transport candidate construction;
do not select a favorable support pair after seeing labels. If it passes,
it licenses a separate frozen GT-blind selection/acceptance study, not a
registration gain or novelty claim. Report 00 unavailable, available,
ordinary and confuser groups, including candidate counts and best-of-36
oracle diagnostics. The pair is the unit; 36 candidates are correlated.

## Validation and limits

Freeze this protocol, runner, separate validator, F2 source/validation,
all 800 native N files, 200 input/motion identities, evaluator GT and F2
label identities before real output. `INCOMPLETE` remains on any partial
run. Caps: <=5 min candidate bank wall, <=100 MiB new artifacts. The
independent validator rehashes all frozen identities, recomputes every
one of the 7,200 transported transforms and every GT label/decision,
including the T00/F2 binding. No acceptance gate or graph inference.

This is a low-cost mechanism question. Transporting multiview poses and
using consensus has substantial prior art; M1 does not assert novelty.
Its distinction from F2's S arm is retaining nine unpooled candidate
transforms from each native generated six-part output. Its distinction
from C6 is same-query F2 support predictions rather than a prior accepted
loop donor. The later selector, if warranted, must be compared with
native RAP, direct pooling, matched geometry and published multiview
consensus methods under the same input and cost budget.
