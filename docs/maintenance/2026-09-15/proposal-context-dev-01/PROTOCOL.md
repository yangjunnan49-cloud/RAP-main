# PG-DEV-V1: bounded proposal-context development screen

Declared 2026-09-15 following the owner's explicit approval of the revised plan.
This prospectively changes the order in PG-V1: test method potential on observed
development data before further Boreas acquisition/adapter work. PG-V1's KITTI09
INCONCLUSIVE_DATA result and all earlier negative results remain unchanged.
Neither sequence here is independent confirmation. No training, threshold search,
support sweep, production replacement, or publication-level novelty claim.

## Fixed experiment

Use the exact existing 100 KITTI00 and 100 KITTI08 pairs, 25 per original stratum,
in saved order. Reuse the immutable 400 anchor hypotheses per sequence from
SC-V1.1 (00 bytes inherited from HL-V2). Preserve all original seeds and S4 scores.
Generate exactly four pooled hypotheses per pair with those same seeds. The two
parts are each the raw anchor plus its two original causal supports, transported
with saved local LiDAR odometry into that anchor's frame. Remove points below
1.5m range in their original scan frame before transport. Concatenate first,
then use unchanged 0.4m voxel/outlier20/2.5 preprocessing and a 4000-point cap
per part, frozen RAP five steps, learned features and protected rigid fitting.
No GT or cross-loop odometry transform enters generation or executable scoring.

Methods: A1, A-R4, A-S4, A-OR4, P1, P-R4, P-OR4. R4 minimizes official average
per-step rigidity within its bank; S4 uses the original support distance score;
OR4 minimizes max(RTE/1m,RRE/5deg) using evaluator-only GT. Ties choose lower
generation index. All methods use the same seed42 preprocessed anchor-only
clouds for acceptance: symmetric NN overlap >=0.7 and mean distance <=2.5m,
with the existing strict <1m NN inclusion convention. Never gate pooled results
on pooled overlap. This explicitly differs from historical sampled diagnostics.
Strict pose success is RTE<=1m AND RRE<=5deg. Report legacy 5m/10deg separately.
Invalid/missing generations remain in denominators (clipped error5), no retries.

## Prospective decision

Each sequence separately must have P-OR4 strict positive recall at least5pp above
A-OR4, P-R4 at least3pp above A-R4 and no lower than A-S4. Require ordinary
selection recall loss <=2pp versus both A-R4 and A-S4, and no newly incorrectly
accepted pair versus either comparator. Report all strata, clipped positive
errors, correct-accept recall and paired harmful/helpful transitions regardless.
All geometry conditions on BOTH sequences are necessary for DEVELOPMENT_SIGNAL.
Otherwise NO_DEVELOPMENT_CONTEXT_SIGNAL; do not pool away a failed sequence.
Engineering/data/resource failure is INCONCLUSIVE, not a scientific negative.

Equal six raw observations: P-R4 versus A-S4. Equal four calls and point cap:
P versus A. These are not exact equal runtime. Before outcomes, select the first
10 saved pairs of EACH sequence for bounded timing (saved order is round-robin).
Replay their four anchor requests solely for cost/reproduction, retaining old
banks for ALL selection. Replayed transforms must match saved values within1e-6;
failures stop execution. Alternate A/P execution order by pair index. Fresh
pair-local raw caches start empty for each arm; warm OS cache is not flushed.
Count reads, filtering, pooling/support preprocessing, generation, official R4
choice and common-gate evaluation; A-S4 adds all four unchanged S4 scores and its
selected gate. Exclude model load, evidence hashes/serialization and GT evaluation.
Gate P-R4 measured summed time <=1.25*A-S4 on each fixed ten-pair sample. Report
this only as sampled development cost, not full-cohort matched-time confirmation.
Cost failure prevents DEVELOPMENT_SIGNAL even if geometry passes; a signal only
justifies fresh external confirmation with full matched costs, not deployment.

## Execution and validation

Freeze protocol, exact memberships, parent manifests, model/dependency identities
and new source before generation. Synthetic nontrivial rotation/translation and
relative-frame checks; point cap and six-observation checks; no GT input fields.
The first10 pooled00 pairs form retained engineering preflight, with no labels
read until the complete00 bank is persisted. Stop for OOM/corrupt data or failed
preflight; preserve partial artifacts. Freeze00 results before08 generation,
although both remain development. Independently reconstruct every selection,
pose error and gate, all stratum aggregates and decision conditions. Verify raw
hashes and immutable parent manifests again before completion.

Caps: 800 new pooled generations plus80 timing-only anchor replays (880 total),
one RTX5070, two GPU-process hours total,12GiB allocated VRAM,20GiB new artifacts.
No extra pooled repeats or parameter changes. Intended delivery: one bounded
method-potential decision within1-2 working days, not a final paper deadline.
Use exclusively created output paths and keep INCOMPLETE until validation passes.
