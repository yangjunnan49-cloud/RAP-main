# F2-V1: structured-motion generation development screen

Declared and owner-authorized on 2026-09-27 ("直接起草与执行，不需要我裁决。
启动"), following F1 PASS_ENGINEERING. F2 is a development mechanism screen on
observed development cohorts only. It is not independent confirmation, not a
novelty clearance, not a production change and not a publication claim. The
2026-09-15 research memo's F2 section governs; all HL/SC/PG stops and the
manuscript pause persist regardless of outcome. A credible development signal
only licenses a separately frozen fresh-confirmation protocol (KITTI 02/07-10
or Boreas under the standing public-download authorization); it never becomes
a thesis claim by itself.

This protocol, the runner, the validator and all input identities must be
hash-frozen before any generation. Failed gates are never replaced after
results. Engineering/data/resource failure is INCONCLUSIVE, not a scientific
negative.

## 1. Fixed cohorts (observed development; exact exposure declared)

- KITTI00: the immutable 100 pairs of HL-V2
  `2026-09-14/hl-v2/data-expansion-01/discovery_inputs.json`, 25 per stratum,
  in saved order. Strata from `discovery_evaluator.json` are never loaded by
  the runner.
- KITTI08: the immutable 100 pairs of SC-V1.1
  `2026-09-14/support-control-01/data/confirmation_inputs.json`, 25 per
  stratum, in saved order. Strata from `confirmation_evaluator.json` are never
  loaded by the runner.

Both sequences are observed development data (00/05/06 became development under
E0; 08 was the SC-V1.1/PG-DEV-V1 observed confirmation cohort and is likewise
development here). All strata are used; no replacement of unfavorable cases;
no pair is dropped for any method outcome. Each sequence is decided separately
and both must pass; do not pool away a failed sequence.

Each pair contributes six ordered parts [i, i_support1, i_support2, j,
j_support1, j_support2] with saved causal within-visit LiDAR local_pose
matrices (anchor = identity). local_pose provenance is re-verified against the
frozen odometry sources before generation: 00 via
`data-expansion-01/00/data.json` parent_hashes (full-kitti00-01 pipeline
odom_poses.txt), 08 via `support-control-01/data/08/odom.npy` hashed in the
freeze. local_pose matrices are historical estimates and are NOT re-estimated.

## 2. Declared data convention (corrected-data 0.205)

Unlike F1 (which deliberately preserved the old no-205 convention), F2 adopts
the development_baseline_v2 convention: every raw scan is loaded as float32
(N,4) xyz, filtered to range >= 1.5 m in the original scan frame, then
corrected with `real_dataset.kitti_vertical_correction` (0.205 deg, exact
CT-ICP convention), in this filter-then-correct order, matching the production
loader. Ranges/voxel are otherwise unchanged from the historical RAP
convention (min 1.5 m, voxel 0.4 m, statistical outlier 20/2.5); no deskew.

The saved local_pose matrices were estimated on uncorrected points. Using them
with corrected points is a declared convention mismatch, bounded by the fixed
sensitivity controls of section 7; it is part of estimated-motion error, not
hidden GT information. No cross-visit odometry prior, GNSS or GT enters
generation or executable scoring.

Preprocessing per part: `RAPBackend.preprocess` with cap sampling seed 42,
exact caps [2000,1000,1000,2000,1000,1000] (total 8000), no duplication or
replacement on shortage (stop instead). Learned miniSpinNet descriptors are
computed exactly once on the retained per-scan points and reused by every arm.

## 3. Arms and generation budget (K4)

Frozen RAP12/miniSpinNet, five Euler steps, no fine-tuning. K=4 generations
per pair per arm. Generation seeds
`seed(seq,i,j,k) = int(SHA256(f'F2|structured-motion|kitti|{seq}|{i}|{j}|{k}')[:8],16) mod 2^31`
for k in 0..3; noise_k is drawn under request_rng(seed_k) and each
generation k executes under request_rng(seed_k).

- N: native six-part sampling; decode per-part fits of the RAW final clean
  endpoint.
- F: reuses N's trajectory byte-identically; group-project only its RAW final
  endpoint. Declared free-rider control: its extra cost is projection only.
- S: group-project the RAW clean endpoint at every step; interpolate projected
  clean points with the same original noise into the next noisy state; decode
  final projected group poses. Raw endpoints/states are saved explicitly;
  endpoints are never silently substituted.
- P: two pooled parts using the EXACT same retained physical points
  transported into their anchor frames, reused corresponding descriptors, same
  ordered noise rows, own standard normalizer. Equal data/point/descriptor
  budget control, not the historical pooled-context preprocessing.
- A: two anchors only (2000 each), corresponding noise rows; reference only,
  not equal-data/equal-compute, never a decision comparator.

N/F/S share byte-identical points, descriptors, normalization and noise per k.
P keeps scan descriptors to avoid confounding with feature re-extraction.
Within a pair, arm execution order alternates by pair index parity
(even: N,S,P,A; odd: A,P,S,N) so reported costs are not cache-order artifacts.
Group math: q_gk=(L_gk p_gk - c_g)/scale; G fitted in normalized coordinates
by corresponding point index; physical G=(R, scale*t - R*c_g); TF32 protected
fits outside autocast; neural FP16 stays enabled.

## 4. Common selection score and common gate (executable, GT-free)

Selection per arm: R4 = argmin over valid generations of
(rigidity_rmse_m, generation index). rigidity_rmse_m is the official average
per-step rigidity RMSE, computed with unmodified model functions
(fit_transformations + compute_rigidity_rmse) on the arm's RAW pre-projection
end_point_trajectory. The same scoring residual is declared for every arm; the
enforced group-projection residual is never used as a score or certificate.
F shares N's raw trajectories and therefore N's scores (declared). P/A scores
come from their own native trajectories (the standard official computation).
Invalid/missing generations remain in denominators with clipped error 5.

Acceptance gate (common, anchor-only): seed42 geometry-only backend (voxel
0.4, outlier 20/2.5, cap 4000, no features) preprocesses the two corrected
anchor scans once per pair; symmetric NN overlap >= 0.7 AND mean distance
<= 2.5 m with the existing strict < 1 m NN inclusion convention
(_alignment_metrics, thresh=1.0). The same anchor clouds gate every arm;
pooled/projected clouds are never used for gating.

## 5. Evaluator-only metrics

After a sequence's generation bank is hash-frozen, and only then, the
evaluator loads `evaluator_gt.npy` and the stratum file. Per generation:
transform_label versus GT relative pose; strict = RTE <= 1 m AND RRE <= 5 deg;
error = max(RTE, RRE/5); clipped_error = min(5, error); invalid/missing = 5;
legacy 5m/10deg safe label reported separately. Per arm, mirroring the
PG-DEV-V1 metric definitions: strict positive recall of the common R4
selection (gate-independent; denominator 75 non-confuser positives),
correct-accept coverage (selected transform strict AND common-gate accepted),
strictly incorrect accepts over all 100 pairs (accepted AND not strict;
dangerous subset = failing legacy 5m/10deg), confuser accept rate, mean
clipped positive error of the selection, ordinary-stratum strict recall, and
oracle OR4 strict recall (diagnostic only, never a decision input).

## 6. Prospective decision (all conditions, both sequences)

DEVELOPMENT_MECHANISM_SIGNAL requires every condition below on BOTH sequences;
otherwise NO_DEVELOPMENT_MECHANISM_SIGNAL. success(X) = strict positive recall
of arm X's R4 selection (gate-independent, denominator 75); clip(X) = mean
clipped positive error of arm X's selection.

- C1 value over native: (success(S)-success(N))/75 >= 0.03 AND
  clip(S) <= 0.95 * clip(N).
- C2 beyond final-only projection: (success(S)-success(F))/75 >= 0.03 AND
  clip(S) <= 0.95 * clip(F).
- C3 beyond matched pooling: (success(S)-success(P))/75 >= 0.03 AND
  clip(S) <= 0.95 * clip(P).
- C4 safety guards: incorrect accepts of S <= those of N on each sequence;
  ordinary-stratum strict recall loss of S versus N <= 0.02 on each sequence.
- C5 engineering: all mandatory correctness checks pass and all caps of
  section 8 are met.

Rationale, from the memo: if per-step coupling provides no benefit beyond
pooling or final-only projection, this candidate fails its rationale; C2/C3
encode exactly that. A NO_DEVELOPMENT_MECHANISM_SIGNAL ends THIS
structured-motion route; it does not rescind the owner's continued-breakthrough
instruction and does not validate any other route. Oracle rows, per-stratum
tables and pair-level transitions are reported regardless of decision. No
post-hoc arm, margin or gate substitution; no threshold, seed, budget or
perturbation-strength search.

## 7. Fixed sensitivity controls (not tuning)

On the first 5 ordinary pairs per sequence in saved order, S arm only, K4:
left-compose every support local_pose (never anchors) by D+ and D-,
D = (+/-0.10 m x translation, +/-1 deg z yaw), matching F1's fixed
perturbations. Record per-pair selected-transform translation/rotation change
versus the unperturbed S selection, constraint residuals and finiteness. These
are sensitivity observations; no accuracy claim and no strength choice.

## 8. Engineering checks, execution order and caps

Before generation: synthetic float64 group-projection checks (20 trials:
nontrivial rotation/translation, gauge change, permutation, single-part
reduction); native custom-N versus official sample_rectified_flow max delta
<= 1e-6 on the first saved 00 pair (K1); reordered S replay delta <= 1e-6 on
that same fixed pair after its other arms complete; RNG/IEEE-matmul
restoration including an injected exception;
exact point budgets; finite outputs; rotation validity of every decoded pose.
During the run: the first 10 pairs of 00 in saved order form a retained
preflight (all checks green) before the remaining 00 pairs execute; the 00
bank is hash-frozen before any 08 generation.

Caps: one RTX 5070; <= 12 GiB allocated VRAM; total GPU-process wall across
both sequences <= 4 hours; new artifacts <= 20 GiB; no simultaneous GPU work;
no network; no production edits; no Git synchronization. Stop on shortage,
OOM, failed correctness or cap; preserve the failed attempt and its freeze;
correctness fixes require an explicit amendment and a new execution directory.

## 9. Independent validation (separate validator, after artifact freeze)

The validator recomputes, without trusting runner outputs: all freeze and
artifact hashes; cohort membership/order from the immutable bank files; raw
scan hashes against both data.json manifests; local_pose versus odometry
sources; exact point budgets; per-generation noise/cond identity across arms
from saved arrays; independent float64 group fits, decodes and constraint
residuals for every F/S generation; per-step rigidity from saved raw
trajectories and the R4 selection arithmetic; the common gate from corrected
raw anchors; GT labels, aggregates and the full decision arithmetic; recorded
reproduction/replay deltas; caps and INCOMPLETE handling. GT is loaded by the
validator only after artifact hash verification, mirroring the evaluator
ordering. INCOMPLETE is removed only when every check passes.

Intended delivery: one bounded mechanism decision plus full artifacts within
1-2 working days. Fresh confirmation afterwards remains a separate frozen
protocol decision for the owner.
