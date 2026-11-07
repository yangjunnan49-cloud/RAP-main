# Reviewable feasibility draft: native-point local-task adaptation

Date: 2026-10-09. DRAFT ONLY; NOT ADMITTED FOR TRAINING.
The current design decision is NO_ORIGINALITY_ADMISSION_FOR_CURRENT_ADAPTATION_DRAFT.
This document makes the contemplated engineering action concrete. It is not a
new approved experiment, an experiment freeze or an amendment to RLP2.

## Question and learner contract

Question: can a limited adaptation inside the generator produce useful coupled
local motion, and does an auxiliary pose objective outperform ordinary flow
fine-tuning and direct-point learners at a fixed budget?

Use the existing 204 count-selected windows/612 raw path bindings: 144 fitting
00-05, 12 unused-development06, 48 historically exposed evaluation07-10.
Retain input order [t-1,t,t-2], 1000 processed points per scan, original miniSpin
descriptors, centers and scale. Reuse existing scientific inputs only after
binding/seal checks. Do not regenerate I/J token banks, widen scan windows or
raise input density. Do not describe these old exposed windows as independent.
All evaluation references use exactly the same endpoints as RLP2.

Draft training seeds: 20261007/08/09. Exactly 1000 updates for each of four arms
and each seed: twelve learners, 12000 updates. Full independent numerical
replays have another 12000 updates; these are validation work, not additional
selected candidates. No development tuning, best seed/checkpoint selection,
early favorable stopping or extra schedule follows a failed gate.

F/G/Q start from the same original checkpoint and byte-identical adapter/MLP
initialization within each seed. Rank-eight updates in blocks 10/11 act only
on global_qkv_proj/global_out_proj. Delta W = BA, with A deterministically
initialized and B zero; alpha/r = 1. Velocity final_mlp weights/biases are
trainable copies. Every other original weight and miniSpin remains frozen.
All learners have batch one, AdamW lr=1e-4, weight_decay=1e-4, clip norm one,
zero dropout, no scheduler or mixed-precision gradient scaler. Keep original
attention precision; adapter parameters/velocity output are float32 and the
new pose/loss arithmetic is float64. A preflight must verify this choice.

## Proposed targets and pose decode

Let measured points be p_i, their existing centers c_i, and common scale s.
The native condition is u_i=(p_i-c_i)/s. Let weak proper rigid transforms
T_i=(R_i,t_i) map each part into part-zero coordinates, with T_0=identity.
Draft normalized targets are y_i=(R_i p_i+t_i-c_0)/s. They preserve each input
row, including partial/dynamic returns; they do not assert cross-view physical
matches or correct motion distortion. Use declared nearest-proper GT rotation
for these new targets, and retain raw poses/official metrics unchanged.

For generated q_i, solve proper Kabsch u_i -> q_i, obtaining A_i,b_i.
Metric pose P_i has rotation A_i and translation s*b_i-A_i*c_i.
Relative prediction a<-b is P_a^-1 P_b. The common output gauge cancels; no
common-window point-output gauge is assumed known at inference. Evaluation
uses the unchanged RLP2 relative-target convention, not a new replacement GT.
GT part targets and independently projected pair targets can have a small
rounding/proper-projection cycle discrepancy; record it before fitting, never
silently adjust old labels or angular conventions to make them cycle-exact.

All three pairs (0,1),(0,2),(1,2) contribute to fitting. A unique proper-objective
Horn relative top-eigengap >1e-6 is mandatory. Undefined/nonfinite cases fail;
there is no native/identity fallback, invalid loss skip or matching-weight
branch. Noncollinear planar/isotropic valid geometry must not be rejected just
because SVD vectors have nonunique internal bases. The new differentiable
solver needs a stable derivative for the unique rigid solution, independent
Horn reconstruction and finite-difference checks; do not edit the old solver.

## Four learned controls

For F/G, cycle training tau through [1,.8,.6,.4,.2] in fixed update order.
For each update, draw Z with a separately frozen seed from the training seed
and update index, with outer RNG restoration. F/G/Q share the same Z.
Teacher-forced X_tau=(1-tau)y+tau Z; v_target=Z-y.
These GT-derived states are permitted training supervision, never inference
inputs. Hold 07-10 targets outside the training loader. Hash-cyclic 144-window
order is identical across all arms within a seed.

L_FM=mean squared coordinate error between v and v_target.
Clean estimate q=X_tau-tau*v. Define L_pose as the mean over three pairs of
Huber(||t-t_GT||/.20m,delta=1) plus
Huber(||R-R_GT||F/(sqrt(2)*radians(.2deg)),delta=1).

| Arm | Trainable parameters | Training objective | Inference |
|---|---:|---|---|
| F | 443904 | L_FM on teacher-forced tau states | Native five-step Euler/rigidity feedback |
| G | 443904 | L_FM + L_pose(q), coefficient one | Identical native five-step inference |
| Q | 443904 | Same sum at tau=1, q=Z-v(Z,1) | One clean estimate and native-point rigid decode |
| N | 444067 | mean ||q-y||^2 + L_pose(q) | One deterministic point-output forward and rigid decode |

Q retains pretrained RAP and Gaussian conditioning but has no ODE integration.
Call it a one-pass pretrained point regressor, not a fully non-generative
architecture. G-versus-Q combines training-time-state and integration changes.

N is the separately trained non-generative control: 37 inputs (32 descriptors,
normalized xyz, anchor bit, log scale), linear 37->128, two blocks each having
part/global four-head attention, FF128->256->128 and three affine layer norms,
then a pointwise MLP128->160->128->3. Attention/linear layers have biases;
activation is SiLU, no padding/no unused trainable channels. The output is a
point's target position, not an inter-scan matching matrix. N has no pretrained
RAP weights or Gaussian/time inputs. It has nearly matched trainable capacity
but not RAP's total frozen capacity/pretraining. Report that limitation.

N0 is the frozen original RAP reference; G3/KISS and identity are references,
not fallback arms. Do not reuse RLP2's separated-context I as a clean causal
control. No claim of generation-specific superiority follows G-versus-N alone.

## Gradient and native-interface safeguards

Do not backpropagate through the existing production sampler. It detaches
stored outputs and returns. The proposal differentiates a single independently
teacher-forced forward, using no autograd tape for blocks0-9. After the first
trainable branch, retain derivatives through all dependent operations, even
when their own weights are frozen. There is no truncated native-rollout
gradient represented as a full five-step gradient.

At inference, pass only processed measured inputs, descriptors and original
fixed per-window noise into isolated adapted models. F/G use the unchanged
five-step native schedule and original-noise reconstruction. Decode the final
raw clean estimate, as in the original native interface. No geometry initial
pose, ICP refinement, pose selector or new acceptance gate is introduced.

## Prospective prerequisites and complete diagnostics

Before an optimizer step, a separately frozen numerical/engineering preflight
would check structural parameter counts, disabled-adapter native replay,
zero-B output behavior, original-weight/descriptor invariance, allowed-gradient
bindings, RNG behavior, noncollinear planar/isotropic/proper-pose fixtures,
expected degenerate rejections, and selected finite differences (1e-6 gradient
tolerance, 1e-8 independent pose tolerance). Use only fixed exposed00/05 inputs
for real forward/backward feasibility checks. Failure preserves source/bank/
failure and stops; no layer/rank/precision/density change to pass the cap.

Full weak target construction must validate before fitting. Complete fixed
fitting accuracy is evaluated at the initial and final checkpoints, on all
144 fit windows and all three pairs. Online loss is supplementary. No new
06 development inference or tuning is proposed. Per-seed/per-window R/t
records must distinguish training fit from transfer; do not infer either from
online loss alone.

Final primary evaluation is 4 arms x 3 seeds x 48 windows =576 predictions on
the original0<-1 endpoints. Initial/final fit diagnostics contain
4 x 3 x 2 x 144 x 3 =10368 pair errors. Seal complete prediction banks before
new evaluation-error outcomes, recognizing fitting labels were already used
for fitting and historical evaluation outcomes were previously exposed.
Invalids stay in denominators. Independently reconstruct every pose/target/
error/aggregate and verify full fit histories, including optimizer state.

Draft fit diagnostic admission for G: final fitting median <=.10m/.20deg and
at least20% improvement in BOTH medians from its initial checkpoint for every
seed. These are finite-task feasibility conditions, not convergence or physical
accuracy guarantees. Record all arms regardless of this condition's outcome.

Draft primary G-versus-each-F/Q/N conjunction: paired median gains >=.005m/
.01deg, G cohort medians <=90% of control for each component, >=60% positive
paired signs for each component, and every sequence mean regression <=.005m/
.02deg. Apply seed medians per window before cohorts. G3 requires the same
paired-gain/safety conjunction. KISS uses the36 identical07/09/10 endpoints,
gains >=.002m/.005deg, both90% ratios and every sequence safety condition.
Identity is descriptive only. Full practical benefit requires all comparisons
and coverage. No favorable subset, secondary arm, threshold or GT change can
replace a failed primary conjunction. No trajectory is part of this draft.

## Resource proposal and stop

If the owner later selects this engineering-feasibility goal, a separate new
scope would propose combined recorded process computation <=14400s (240min),
including failed stages, freezes, numerical/source validators, all full fit
replays, initial/final fitting diagnostics, evaluation and closure. Per-fit
training and per-fit replay each <=600s. Numerical/real engineering preflight
<=600s combined, GPU peak <=3GiB, process RSS<=4GiB, new artifacts<=2GiB.
Caps are failure boundaries, not measured feasibility promises. No automatic
extension follows. The closed RLP2 105-minute account is not amended.

Static trainable-state storage is small; activation/attention/autograd workspace
and whole-process memory remain unmeasured. There is no runtime benchmark in
this design. Do not extrapolate old inference costs into a training guarantee.
Keep existing banks by reference and save adapter/velocity-MLP states, rather
than copying full checkpoints for every learner. No download/install, training
data acquisition, production/default/backbone-file/manuscript edit or Git sync.

Current stop occurs BEFORE all of these stages: the ordinary-adaptation draft
does not yet have originality admission. No pilot, protocol freeze, numerical
preflight, model loading/inference or fitting exists. A future explicit goal
change or newly distinguished mechanism must be reviewed before execution.
