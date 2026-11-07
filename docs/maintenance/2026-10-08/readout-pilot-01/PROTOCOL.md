# RLP1 fixed small-head pilot protocol

Owner approved the complete reviewed scope on 2026-10-08. The preserved DS0
TRAINING_ANNEX_DRAFT.md and readout-pilot-review-01/REVIEWED_SCOPE.md define the
scientific construction, settings and gates. The reviewed big-endian seed rule
supersedes the DS0 little-endian typo; G3/KISS sequence safety is included.
This file resolves implementation details before eligible outputs.

## Prospective stages and resource accounting

Each stage creates a fresh exclusive directory and its own source/protocol/
runtime/checkpoint/source-data freeze before outputs. No frozen implementation
is subsequently edited. Engineering preflight must seal and independently pass
before weak-label preflight; that must pass before the full 204-window bank.
Complete GT-free bank and same-point G3 references must independently pass before
full labels; labels must pass before fitting. All predictions seal before errors.
The original 204 indices and settings freeze in the first preflight, before labels.

All process stages, including freezes, validators and failed outputs, contribute
to the combined 3600-second compute budget through RESOURCE_LOG.json. GPU allocated
<=3 GiB, process RSS <=4 GiB, total new-study files <=4 GiB. Extraction <=1200s;
each fit including data/identity checks <=300s. No density, quantization or parameter
rescue. A failed cap/control/source/label/finite-number check stops this attempt.
Preserve originals and disclose any separately frozen correction.

## Engineering preflight

Use sealed TR0 00/05/06/07,t200 rows, source order[199,200,198]. New J outputs
must exactly equal TR0 raw/state/tokens/inputs. Save J,I,I-repeat,I-third-noise+1
arrays with passive last-layer tokens and all five flow pre-hook inputs/times.
I grouping is [[1000],[1000],[1000]], batch cuts[0,1000,2000,3000], unchanged
part cuts and anchors, shared scale repeated three times. All five states belong
to this grouping. No extra final t0 call. Verify the source-defined unused CUDA
length-one J versus length-three I vector draw, outer RNG restoration, unchanged
versions/flags, exact I repeat and exact unchanged parts0/1 after perturbing only
third-part noise. Independently reconstruct raw processed rows/descriptors/noise,
normalization and Horn fits; independent pose tolerance1e-8, identities/controls
exact. Runtime fields must match the freeze and existing strict344/58-key loading.

## Weak-label and solver preflight

Only after its engineering seal/validation, read the four fixed pose files for
labels. Camera/LiDAR conversion uses C^-1 G_a^-1 G_b C with general inverses;
labels use raw transforms on existing KITTI205 processed points. Only the new
readout angular truth maps raw R to nearest proper SO3, keeping translation.
Store both transforms. Six directions are computed separately, preserving any
rounding-induced forward/reverse numerical difference. Each packed boolean
positive mask has1000 columns, distances<=.30m; third support<=.60m; unmatched
pair minimum>=.60m with third support; intermediate/no support/nonfinite rows
ignored. Bit packing preserves exact booleans and does not quantize features.
Require >=20 positive rows per direction/pair/window on all four fixed windows.

Predeclared synthetic cases include exact rigid/calibration/direction, multiple
positives, unmatched with third support, third-view absence/dynamic toy, nonfinite
ignored rows, rank1 expected rejection, planar unique solve, rounded/reflected
proper rotations, and finite nondegenerate soft-SVD/readout gradients. Independent
brute-force labels and weighted quaternion Horn validate numerical construction,
not physical GT or real dynamic identity. Pose tolerance1e-8, label masks exact,
distance tolerance1e-10. Freeze and seal the synthetic and real banks separately.

## Readout and fitting details

The isolated helper implements the exact521->128 SiLU->64 normalized projection,
shared128->1 overlap logit and scalar dustbin,75202 parameters. D is unit32-D
features plus480 zeros; I/J are unit512-D features. Common9 channels are native
normalized conditionxyz,original noisexyz,anchorbit,log(scale),last nominalt=.2.
No joint states or coordinates enter D/I. Backbone/descriptor are frozen.

For a<b, scores[target-a,source-b] are dot/.10. Row and reverse softmax add
alpha-overlap for each dustbin. Per direction average present positive/unmatched
class terms; then average directions with supervised rows. Ignored rows have
zero loss. Full-window class counts are recorded; no class-driven window removal.
After100 warmup updates, add.05 coupled motion loss. W is the probability product
times both sigmoid overlap logits. Double-precision soft weighted SVD uses
original points, positive mass and Horn top gap/max(abs(eigenvalues),1e-12)>1e-6.
Only a degenerate auxiliary term is skipped; the motion denominator remains3.
Huber(delta1) of translation norm/.20m and Frobenius rotation norm/(sqrt2*.2deg)
are summed per pair. Nonfinite loss or any gradient stops. SVD precision is IEEE;
no identity fallback or pseudo-correspondence regularization.

Three fixed fit seeds20261007/08/09, same initial state per seed in D/I/J.
AdamW lr1e-3,weight_decay1e-4,gradient norm clip1,1000 updates,batch1 window.
Order is the144 fitting windows sorted by SHA256('RLP1-order|fitseed|seq|t'),
cycled for1000 steps. No label-dependent order, augmentation, epoch/seed selection
or diagnostic tuning. Only final1000-step heads are evaluated. Record every
window/update/loss/gradient norm and skipped auxiliary term, input-role hashes,
initial/final head hashes, and backbone checkpoint hashes before/after fits.

## Inference, independent evaluation and gates

Keep mutual real row/column argmax matches when both probabilities>=.05, remove
dustbin winners, require20 initial matches. Argmax uses first-index ties. Weighted
proper SVD on original points followed by two monotone .60m residual trims/refits.
Each refit requires positive mass, >=3 retained matches and proper-objective gap
>1e-6. Every invalid result stays in the denominator with its reason, never a
native/GT substitute. Save head embeddings, overlap, match rows/weights/trim mask
and pose or invalid marker for independent reconstruction.

There are432 primary poses:3 arms*3 seeds*48 windows. All must be valid for a
primary pass. Independent head forward tolerance5e-5, probabilities5e-5,
weighted solve/error tolerance1e-8; exact valid-match/trim membership required.
No success-only seed medians. Aggregate the three seed errors per window by
median, then all48 window paired gains, cohort medians and sequence means.
J must beat EACH I,D in R AND t: paired medians>=.005m/.01deg,cohort J medians
<=90% controls,positive fractions>=.60;each07/08/09/10 mean regression<=.005m/.02deg.
J must additionally beat G3 paired medians>=.005m/.01deg and KISS07/09/10
36 windows>=.002m/.005deg with J cohort medians<=90% KISS. G3 on07-10 and KISS
on07/09/10 also require per-sequence mean regressions<=.005m/.02deg.

Report all seeds, invalid counts, per-sequence tables and full compute. Missing
coverage is COVERAGE_INCONCLUSIVE. Joint gates failing stop this construction;
joint-only gain without G3/KISS usefulness is not system readiness. A full pass
still ends this pilot and requires a separately frozen system insertion/ter/ATE
protocol. No trajectory/default or originality claim follows automatically.
Historical exposure, preflight-shared frames, weak short-segment GT, I one-part
OOD possibility, unequal D capacity/attention work,unknown local checkpoint/site
membership,09 discrepancy and all old negative stops remain explicit.
