# Next round: fixed dense-pose propagation screen

Planning status: **not frozen or run**. The validated system audit is in
`REPORT.md`; its numerical results and prior banks must remain immutable.
The owner has authorized the metric-first direction and handoff planning.

## Why this is the next bounded question

E0 A odometry has lower ter than the loop-corrected full path in both
three-sequence groups, while the latter lowers aligned ATE. One-at-a-time
GT replacement of accepted loop transforms rarely moves ter materially.
The full trajectory is reconstructed by applying the last keyframe's
constant pose correction to every intervening scan, potentially introducing
keyframe-boundary jumps. This is an observed code path and an untested
cause. Generic non-keyframe correction/interpolation has published prior
art ([Jang et al., 2020](https://arxiv.org/abs/2009.08724)); any gain is
an engineering result, not by itself the requested original RAP method.

## One fixed paired intervention

Inputs: exact saved E0 A odometry, keyframe IDs and optimized keyframe
poses on 00/05/06/07/09/10. No RAP inference, loop selection, graph
reoptimization, GT-based trajectory construction, or parameter search.
Control P is the native piecewise-constant correction. Intervention S is
one SE(3) interpolation of left corrections: for scan `s` in keyframe
interval `[a,b]`, let `C_a=T_opt[a] inv(T_odom[a])`,
`C_b=T_opt[b] inv(T_odom[b])`, `alpha=(s-a)/(b-a)`, and
`C_s=C_a Exp(alpha Log(inv(C_a) C_b))`. Output `T_s=C_s T_odom[s]`.
Use the same optimized keyframe poses at every keyframe. No tuning of
alpha, neighborhoods, factors or correction strength. Preflight synthetic
SE(3) endpoint/continuity checks and zero-loop sequence10 exact identity
before the full bank.

Freeze the implementation, separate validator, source/input hashes,
runtime and resource caps before any real bank. Generate and SHA-seal all
six GT-free S trajectories and boundary-jump diagnostics first. Then an
evaluator computes exact existing camera KITTI ter/rer, aligned LiDAR
ATE and segment records for P/S/odometry. Independent validator checks
anchor equality, SE(3), source frame IDs, baseline reproduction, segment
enumeration, metrics and bank/evaluator separation. Limits: CPU-only,
20-minute wall, 2GiB peak RSS, 500MB artifacts.

Prospective signal gate for this screen: S lowers **each group's**
arithmetic mean ter by at least 0.01 percentage points versus native P;
each group's mean aligned ATE worsens by at most 2%; no sequence's ter
worsens by more than 0.01 points and no sequence's ATE worsens by more
than 5%; sequence10 S and P remain equal within 1e-5 pose-entry error.
Report all six sequence effects regardless of the gate. This is a
deliberately bounded engineering screen, not a novelty or deployment
gate. If it fails, stop this fixed interpolation route without trying
other spaces/weights. If it passes, seek a genuinely RAP-specific use
of generated multi-view geometry against an equal-budget geometric
control, and reserve independent trajectory confirmation before a thesis
method claim. Preserve the manuscript pause and no-default-edit/no-Git-sync
boundary.

## Incoming agent procedure

Read `AGENTS.md`, this audit's `PROTOCOL.md`, `REPORT.md`, `validation.json`,
`STATUS.json` and `HANDOFF.md`; inspect `git status --short`. Start a
new experiment directory with its own protocol, runner, validator and
freeze. Do not append generated results to this audited bank. The first
next-round action is code/source inspection and synthetic preflight, not
full trajectory scoring. Record every stage in the new status file; on
interruption keep an `INCOMPLETE` marker and exact hash/command context.
