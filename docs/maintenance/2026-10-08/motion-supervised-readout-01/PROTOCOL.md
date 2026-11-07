# RLP2 motion-supervised readout execution protocol

Owner authorized the complete immediate scope in readout-task-redesign-01/PLAN.md.
That historical plan, original204 count-selected manifest and big-endian LMF1
noise rule are fixed. Three arms D/I/J,three fit seeds20261007/08/09,1000 updates
per fit,all three pair losses from update1,no fitting/epoch/seed/window selection.
RAP/miniSpin and native extraction settings remain frozen. Independent I uses
the existing validated full-flow grouping. No GT/frame/sequence identity enters
the head. All earlier stops and original scientific seals remain.

## Prospective stage boundaries

New numerical preflight must independently pass before full extraction. Complete
GT-free204 bank/source/G3 validation must seal before full relative GT targets.
Those targets validate before fitting. Each fit freezes inputs/settings/source
before optimizer updates; all nine fits must validate before predictions. All
primary predictions seal before fixed permutation diagnostics; both seal before
GT error scoring. Each stage freezes and preserves INCOMPLETE until independent
validation. Implementation-only failure corrections require disclosure and a new
attempt, never edit frozen sources or scientific settings.

Numerical preflight uses synthetic rigid/planar/partial/unequal-sample/ambiguous/
rank1/uniform-weight fixtures,proper/calibration controls,central finite-difference
gradients,all three initialized heads on saved00/05 fitting-sequence inputs and
their already exposed pose targets,without optimizer steps. It reuses the RLP1
engineering/source/invariance result only after all seals and frozen source
identities recheck. No new native model inference in numerical preflight.

## New head and solve

Unit features (D32+480zeros,I/J512)+identical9 common channels ->521->128 SiLU->64
unit embeddings.75072 nominal params,D13632effective,I/J identical active capacity.
No overlap/dustbin parameters. S=E_a E_b^T/.10 in float32 IEEE; W_raw is float32
row_softmax(S)*transpose(row_softmax(S^T)). Normalize W_raw in float64 by total
mass; solve on original source/target points in float64 using proper SVD. Horn
top gap/max(abs(eigenvalues),1e-12)>1e-6 is mandatory; nonpositive/nonfinite/
nonunique cases fail, no skipped zero loss or native/identity fallback. Same solve
at train/inference. Record marginal effective supports and spectrum as diagnostics,
not positive-row count gates. No hard-match decoder or residual trim.

Loss=mean of all3pairs [Huber(||t-t_GT||/.20m,delta1)+
Huber(||R-R_GT||F/(sqrt2*radians(.2deg)),delta1)]. AdamW lr1e-3,wd1e-4,clip1,
batch1,1000steps,hash-cyclic fit order from the prior plan. All gradients finite;
record pre-clipping norm and every loss. Save initial/final head arrays. Training
and final checkpoints validate by a separately implemented full fixed replay;
replay cost counts in the same global cap. No backbone is resident/optimized in
fits. Stream one feature window at a time (an uncompressed lossless NPZ bank),
without keeping the full204 feature bank in process memory.

## Lossless prediction encoding and validation

Storing every dense W plus feature banks would exceed the4GiB cap. BEFORE any
output, fix an exact encoding: save the two float32 embedding arrays, raw-W
SHA256, marginal arrays/mass/gap/spectrum and R,t. The frozen float32 IEEE
score/softmax/product operations reconstruct W_raw from embeddings. The
independent validator reconstructs W on the same pinned runtime/GPU and must
match the FULL matrix SHA256 EXACTLY, then uses independent float64 quaternion
Horn to reconstruct the pose. This encodes every weight without quantization,
reduced density or scientific approximation. Also independently reconstruct
head forward from sealed weights/features/common channels (embedding/probability
tol5e-5),numerical solve/error tol1e-8. Failure of exact weight reconstruction is
a stage failure, not permission to widen tolerances or drop matrices. Full W
need not be retained again after validation. Float32 raw W normalization is
specified identically in training and inference; raw mass is retained.

Synthetic small matrices are saved explicitly,including selected gradients;
finite-difference tol1e-6 and independent Horn tol1e-8. Original-point processing,
descriptor/noise and passive token bindings are checked independently for the
full GT-free bank. No new full native-flow replay is used as a proxy accuracy gate.

## Targets, references and outcomes

Relative targets use raw C^-1 G_a^-1 G_b C (general inverses of rounded arrays),
then nearest proper rotation ONLY for new angular target/loss;translation retained.
Keep both raw/proper targets. Official GT and old metrics untouched. Independent
quaternion polar projection/direction reconstruct targets to1e-8. G3 uses the
existing fixed same-point ICP construction on each of48 evaluation windows,with
independent brute-force/Horn validation before GT. KISS07/09/10 sources/endpoints
are frozen and checked for all36 windows;08 has no KISS requirement.

Primary432 predictions must all be valid. Fixed J permutation rotates tokens
by137 rows within each scan for all48windows/3seeds;coordinate/common rows fixed.
Save all144 diagnostics after primary seal; no alternative/selected output.
Identity baseline is evaluator-only. Aggregate all three seeds by per-window
median,then apply every conjunction and sequence cap exactly in the design plan.
J versus each I/D requires paired medians.005m/.01deg,cohort medians<=90%,positive
sign fractions>=.60,and each sequence mean regression<=.005m/.02deg. G3 paired
gain.005m/.01deg plus sequence safety;KISS36 paired gains.002m/.005deg,medians<=90%
plus sequence safety. Missing coverage is inconclusive;all invalids stay in denominator.
Novelty,physical identity/confidence and independent generalization remain unproven.

## Resources and stop

All process stages,failed attempts,freeze/validation/replay/diagnostics contribute
to RESOURCE_LOG:combined<=3600s,extraction<=1200s,each fit<=300s,GPU<=3GiB,RSS<=4GiB,
new study artifacts<=4GiB. Combined cap overrides individual maxima. Routine
implementation/documentation elapsed time is separate from process compute and
must be disclosed. No automatic cap extension or parameter/density/label rescue.
If a prerequisite fails,preserve it and validate the stop evidence if possible.
No trajectory follows a failure,representation-only gain or this approval alone.
