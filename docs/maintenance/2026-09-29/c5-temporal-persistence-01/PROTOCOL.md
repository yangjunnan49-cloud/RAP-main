# C5: fixed temporal-persistence feature mask, small candidate screen

Freeze protocol, runner, separate validator and exact identities before
model inference. This is a constructive but intentionally small
observed-development test of C4's support-feature result. It is not a
novelty or system-performance claim. The question is whether **same-visit
repeatability**, computed without cross-visit GT, can keep more useful
temporal-support features for RAP's hard candidate creation than an equal
amount of arbitrary feature masking.

## Inputs, geometry and arms

Use exactly C4's fixed28 pairs, generation0, identical F2 points,
normalization, six-part C1 miniSpinNet descriptors, explicit noise/seed,
RAP12 five Euler steps and rigidity forcing. Do not regenerate scans or
descriptors, alter anchor parts0/3, train, tune the gate or inspect GT/labels
before the complete bank seal. F2 `inputs_{seq}.json` holds four causal
within-visit support-to-anchor local-pose matrices. Use each unchanged:
transform a support point to its visit anchor frame, then query its nearest
retained 2000-point anchor with float64 `cKDTree`. Mark it temporally
persistent iff distance<=**1.0m**. This fixed radius relates to F2's
1m correspondence and 0.4m voxel convention; it is not selected from C5
outcomes. No cross-visit alignment or evaluator GT enters the mask.

Arm T has every true feature and must exactly reproduce saved F2 N0 raw
and noisy-state trajectories (max delta<=1e-5). Arm P keeps true anchor
features and zeros nonpersistent support feature rows. Arm R keeps the
same number of support feature rows **within each radial bin of each part**
but chooses rows at random. Bins in support's own scanner frame are
`[0,10,20,30,40,60,80,100,+inf)` meters. For each pair/part/bin, use
NumPy PCG64 seeded by the first8 bytes of SHA256
`C5|pair|part|bin`; sample without replacement. Anchor features remain
true. Both masks leave the points/noise/order and number of active
descriptors fixed per part and radial bin; only their temporal persistence
status differs. Save masks and full trajectories. Zeros are an
out-of-distribution feature attenuation, so P versus R is necessary but
does not eliminate every distribution shift.

Before real inference, pass synthetic transform, mask and range-bin
tests. Use C2's restricted `weights_only=True` RAP loader. Preserve RNG
and precision scope. Hash-freeze protocol/code, model/source/config,
selected F2 inputs/N0 and C1 features, saved local poses and evaluator
GT/label identities. Bank runner may hash but must not parse GT/labels.
Create `INCOMPLETE` before work. Seal all28 P/R output artifacts before
evaluator access. No earlier artifact may be rerun or overwritten.

## Fixed evaluation and stop

Decode each arm's source-to-target pair pose by F2's unchanged per-part
raw-final fit. After bank seal, evaluate strict correctness (translation
<=1m and rotation<=5deg) against the saved F2 GT convention; report
pair-level T/P/R labels, gains/losses, strata and native K4 availability.
No acceptance gate or graph claim in this small candidate screen.

The fixed primary 08 set is the **six** positive C4 pairs with no strict
native K4 candidate; its membership was observed before C5 and is
declared, not selected from C5 outcomes. T is wrong on all six. Declare
`PROMISING_TEMPORAL_PERSISTENCE_SCREEN` only if:

1. Median retained fraction across all112 support parts lies in
   `[0.10,0.90]`; otherwise `INCONCLUSIVE_MASK_SUPPORT`.
2. P creates strict candidates on >=2 of those six, and P exceeds R's
   recoveries on that same set by >=2.
3. Relative to T, P loses at most one previously strict positive in each
   sequence, and at most one previously strict ordinary pair in each
   sequence. All predeclared guards must pass.

If mask support is adequate but any effect/safety guard fails, decide
`NO_TEMPORAL_PERSISTENCE_SCREEN_SIGNAL`. These small absolute margins
are exploratory, not significance tests. Do not retune the radius, bins,
zeroing or cohort after seeing results. A pass only licenses a separate
full F2 K4 development protocol with gate/safety and matched compute;
it does not license training, a default change or a thesis claim. Failure
retires this fixed persistence-mask route.

Caps: <=10min bank wall, <=12GiB peak allocated GPU, <=0.5GiB new
artifacts. Independent validator rehashes all frozen sources/bank,
recomputes all112 persistence and radial-matched masks, checks all28 T
reproductions and P/R trajectories/pose fits, GT labels, decision
arithmetic and no incomplete marker.

Related prior work already uses overlap-aware selection (PREDATOR),
geometric context (GeoTransformer) and temporally stable LiDAR mapping
(for example MULLS). C5 tests a specific interface to frozen RAP; a
plain temporal-static filter is not claimed as original.
