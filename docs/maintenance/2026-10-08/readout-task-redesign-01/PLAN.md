# Proposed motion-supervised readout pilot

DESIGN_ONLY / NOT_IMPLEMENTED / NOT_EXPERIMENT_FROZEN / NOT_AUTHORIZED.
All numerical settings below are a reviewable recommendation. Final source,
runner, independent validator and manifest must freeze prospectively before
any new eligible output. No RLP1 source, protocol, bank or gate is amended.

## Question and changed contract

Can equally optimized small readouts obtain useful coupled motion from frozen
joint J tokens beyond cross-view-separated I and direct descriptors D, when
supervision specifies a rigid transform rather than sparse point identities?

Three scan inputs and all three pair targets remain. The third scan still
provides J's context, but no sampled third-view support is a condition for a
training label. Supervision is only the relative pose, with the same disclosed
camera/LiDAR conversion and proper-rotation convention as RLP1. GT transforms,
labels and frame/sequence IDs are never network inputs.

## Concrete proposed readout

For each native row concatenate the unit feature (D32 padded to512, I/J512)
and the same9 common channels used previously. A common521->128 SiLU->64
unit-normalized projector defines scores S_ab=E_a E_b^T/.10. Remove the learned
overlap logit and dustbin: the new task provides no row-level supervision for
them. There are75072 nominal parameters; D has13632 effective parameters
because padding leaves61440 inactive weights. I/J active capacity is identical;
D is not claimed capacity matched. No learned head cross-attention is added.

Define positive latent weights as

    W_ab = softmax_rows(S_ab) * transpose(softmax_rows(transpose(S_ab))).

Normalize W by its total mass for numerical scale, then compute its two
weighted centroids and cross-covariance using ORIGINAL source/target points.
Use the unique proper weighted rigid solution, with the same double-precision
SVD and independent quaternion Horn objective-gap check (>1e-6 relative gap).
The output is one coupled R,t. W is a latent pose weight, not a calibrated
probability, identified physical match or static/dynamic annotation.

Use THIS continuous solver at inference too. Do not switch to a hard argmax/
20-mutual-match rule or introduce GT-based trimming/initialization. Record W,
marginals, effective row/column support, spectrum/gap and the pose for independent
reconstruction. Effective-support counts are diagnostics, not a replacement
positive-row admission threshold. Nonfinite values or nonunique solves remain
explicit failures; no identity/native pose substitution or silently skipped
zero-loss examples. Partial-overlap outliers can still harm the result.

From update1 supervise both t and R on each of the three pairs:

    L = mean_pairs[
          Huber(||t_hat-t_GT||/.20m, delta=1)
        + Huber(||R_hat-R_GT||_F/(sqrt(2)*radians(.2deg)), delta=1)].

No correspondence warmup, positive-row count, unmatched label, third-view label,
entropy schedule or later loss switch. The relative-pose targets are weak because
GT physical accuracy is unresolved. Coordinate/noise/common-channel shortcuts
remain possible and must be examined with the trained controls.

## One authorization, three immediate execution stages

1. Numerical/source preflight: recheck existing TR0/RLP1 engineering scientific
   seals and reuse their invariance result if extractor/model/grouping unchanged.
   Test the NEW continuous training/inference path with synthetic exact/planar/
   partial/unequal-sample/ambiguous/rank1 fixtures; Horn agreement and central
   finite-difference gradients on nondegenerate cases; expected degeneracy
   rejection. Check all three fixed random initializations on saved fitting-role
   00/05 inputs for finite forward/backward without optimizer updates. This is
   an implementation prerequisite, not a pose-accuracy or label-coverage gate.
   Any failure stops this attempt; do not select another initialization.
2. Fixed data and nine fits: reuse the ORIGINAL count-derived204-window manifest,
   original1000 rows/scan and big-endian LMF1 noise seeds.144 fit00-05,12 diagnostic
   dev06,48 historically exposed evaluation07-10. Extract D/I/J with unchanged
   native settings, seal complete GT-free banks and independently validate source
   bindings before full relative-pose labels. Stream one window at a time rather
   than loading the full feature bank into resident memory. Freeze/seal targets;
   only144 fit labels enter optimization. Three seeds20261007/08/09,1000 updates
   each arm, same initialized projector per seed, batch1,AdamW lr1e-3,wd1e-4,
   clip1 and the same hash-cyclic fit-window order. No best epoch/seed or tuning.
   Log all losses/gradients/invalids and backbone hashes before/after.
3. Direct outcome: seal all432 final seed/arm/window poses before error scoring.
   Independently reconstruct the continuous solve, target convention and metrics.
   Report all seeds and invalids; per-window seed medians do not make independent
   samples. Do not filter failures, replace windows, select a best seed or use
   dev06 to change settings. The four earlier preflight windows are disclosed
   historical exposure, including their known label shortage and shared frames.

## Unchanged scientific usefulness requirements

Complete valid predictions in all three arms are required for a primary pass.
For J against EACH I,D on48 exposed windows require BOTH:

- Median paired translation gain>=.005m, J cohort median<=90% control;
- Median paired rotation gain>=.01deg, J cohort median<=90% control;
- Positive signs>=60% for each quantity/control;
- Per07/08/09/10 mean regression<=.005m/.02deg.

Useful motion additionally requires J vs same-point G3 paired medians
>=.005m/.01deg on48, and J vs KISS at identical07/09/10 endpoints on36:
paired medians>=.002m/.005deg with both J medians<=90% KISS. Retain the respective
per-sequence mean regression caps.005m/.02deg. Compute same-point references
under their unchanged declared construction; do not use an old method's average
from different windows. KISS dense-map work differs and must be disclosed.

Add two cheap diagnostics after predictions seal, not selectable inference
alternatives: the identity/no-motion pose on identical endpoints, and a fixed
within-scan token-row permutation in J for all48 windows/all seeds. For the
permutation rotate token row indices by137 modulo1000; hold measured coordinates,
common channels and pose solver fixed. If J stays equally good after destroying
token/measurement bindings, a row-specific representation claim is unsupported.
Report all144 permuted outcomes without GT-based repair. This diagnostic does
not by itself prove a causal mechanism: it changes the input distribution.
Full-flow I is also a possible one-part OOD ablation, so J>I alone is insufficient.

These numerical gains are against the supplied weak GT convention. They do not
replace official system metrics or establish physical point identity/accuracy.
No significance or independent generalization claim from this historically
exposed, checkpoint/site-unknown small evaluation set.

## Resources and conditional system path

Recommend retaining total process compute<=3600s,GPU<=3GiB,RSS<=4GiB,new pilot
artifacts<=4GiB; extraction<=1200s,each fit<=300s. The combined60-minute cap
overrides individual maxima; these are limits, not runtime promises. Include
preflight, extraction, validators, nine fits, diagnostics and failed outputs.
Stop on a cap, never quantize/reduce density/samples or extend a fit to rescue.
The existing engineering timing is too small to guarantee full-pilot runtime.

System work is a SEPARATE prospective stage only after all useful-local gates
pass. Use the readout's predicted consecutive-scan motion as an odometry
measurement, with fixed causal three-frame input [t-1,t,t-2]. Compare complete
fixed07/09/10 sequences with KISS and corresponding D/I/J controls. Do not select
only apparently favorable intervals. Freeze keyframe indices, retrieval attempts,
loop poses/admissions and graph noise; recompute chained odometry measurements
from each complete motion bank. Existing loop measurements may depend on the
original odometry/map, so this is a frozen-graph intervention with that limitation,
not an automatically deployable rebuilt SLAM pipeline. Handle beginning/bank
coverage boundaries identically in all arms and disclose them before execution.

Before that stage, finalize full-sequence cost/storage, all input/output bindings,
invalid policy and exact material ter/ATE gates using EXISTING results only.
The target must be coupled improvement in official100-800m translation/rotation
and aligned ATE with sequence safety. No loop-only ATE gain or sparse-window
local score is sufficient. No noise weighting, retrieval change, dense correction
interpolation or stopped-route rescue accompanies this intervention.

## Stop and interpretation

- Numeric/cap/source failure: preserve the attempt; implementation-only correction
  requires disclosed new freeze, not a scientific rescue.
- J fails I/D conjunction: stop investing in this fixed frozen-token/readout
  construction under the current project budget; no preset fallback sweep.
- J beats I/D but fails G3/KISS: representation evidence only, no trajectory stage.
- Useful local pass: justify and separately freeze the full-sequence intervention.
- System pass: still no originality or independent checkpoint/site claim without
  a RAP-specific mechanism and confirmation beyond current exposed evidence.

The selected next experiment is a hypothesis test, not a promise of improvement.
