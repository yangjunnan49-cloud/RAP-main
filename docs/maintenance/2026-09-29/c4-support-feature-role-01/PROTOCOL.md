# C4: isolate temporal-support feature use in RAP candidate creation

Freeze this protocol, runner, independent validator and exact inputs before
inference. C2 showed pose-level reliance on *all six* per-point feature
channels when shuffled together. C4 asks whether the **four temporal
support parts** themselves materially influence anchor-pair candidate
creation. It is a paired destructive model-use intervention, not a proposed
inference method, gain claim or independent test. C3's fixed FPFH route is
closed; C4 does not use FPFH.

## Cohort, inputs and arms

Use exactly C2's 28 saved-order F2 KITTI00/08 pairs: indices
`[0,1,25,26,27,28,50,51,52,53,75,76,77,78]` per sequence, including
seven actual ordinary pairs in total. Generation0 only. Load the exact F2
saved six-part points/normalization/noise and C1's exact six-part 32-D
miniSpinNet features; C1's extracted features were bit-identical to F2's.
No raw-scan regeneration, training, changed weights, changed points, changed
noise, motion support, gate tuning or candidate selection. The two anchor
parts are0 and3; temporal support parts are1,2,4,5. Use C2's existing
SHA256/PCG64 within-part permutation for each part so intervention strength
is matched to its validated all-part shuffle.

Arm T uses every true feature and must exactly reproduce saved F2 N0
five-step raw clean-endpoint and state trajectories (max absolute delta
<=1e-5) on all28 pairs. Failure ends `INCONCLUSIVE_REPRODUCTION` before
interpreting changed arms. Arm A shuffles features within anchors0 and3
only, leaving four support parts true. Arm S shuffles features within
support parts1,2,4,5 only, leaving anchors true. All arms use identical
point order, per-part feature multiset, explicit saved noise, seed, RAP12
checkpoint, native five-step Euler sampler and rigidity forcing. Load the
checkpoint with C2's restricted `weights_only=True` safe-global path and
miniSpinNet features from C1 sealed artifacts. Preserve RNG/precision scope.

Save full raw and noisy-state trajectories, exact permutations, decoded
source-to-target poses and paired raw-final RMS and pose changes. Verify
each changed batch has the exact same point coordinates, centers, scale,
counts, anchor mask and noise as T. Seal all outputs by SHA256 before any
GT or evaluator label parsing. No C1/C2/C3/F2 output may be overwritten.

## Prospective decision and scope

A material response to T requires raw-final RMS>=0.005 in normalized model
coordinates **and** relative pose change >=0.25m or >=0.25deg, exactly
as in C2. Anchor intervention A is a positive control: if fewer than five
of the seven ordinary pairs respond materially, decide
`INCONCLUSIVE_ANCHOR_CONTROL`. Otherwise, S demonstrates
`SUPPORT_FEATURE_CANDIDATE_RELIANCE` only if at least **six of seven**
ordinary pairs materially respond **and** S flips the strict (<={1m,5deg})
correctness of at least **three of the 22 positive** fixed pairs relative
to T. If the ordinary pose criterion passes but the candidate criterion
does not, decide `SUPPORT_FEATURE_POSE_RELIANCE_ONLY`; otherwise decide
`NO_MATERIAL_SUPPORT_FEATURE_RELIANCE`. These absolute small-cohort margins
are exploratory mechanism gates, not p-values or performance gains.

After the bank seal, compute evaluator-only strict labels for T/A/S using
the original F2 GT convention, report pair and stratum responses, strict
gains/losses separately and native-K4 availability. Do not choose a better
arm: shuffling is out of distribution and may fortuitously improve some
poses. The existing geometric acceptance gate is not part of this test;
no system or graph claim follows. A positive result localizes feature use
to temporal support and can justify a **separate** constructive context
method proposal only after prior-art audit. It does not license training,
default changes or a thesis novelty claim.

## Engineering and validation

Caps: <=10min bank wall, <=12GiB peak allocated VRAM, <=0.5GiB new
artifacts. Freeze protocol/runner/validator, source and checkpoints,
C1/C2 validation and per-pair feature/input/N0 identities, C2 all-part
permutations, F2 records/labels and GT identities. Bank runner must not
read evaluator GT or labels; hashing them only binds identity. The separate
validator checks every frozen hash, all28 T reproductions, each exact
per-part A/S permutation and unchanged other features, all trajectories,
independent CPU pose decoding and raw/pose deltas, GT strict/decision
arithmetic and no incomplete marker.

Relevant prior art: PREDATOR (CVPR2021) uses overlap-aware cross-cloud
attention; GeoTransformer (CVPR2022) uses pairwise/triplet geometric
context. C4 audits RAP's existing temporal context use, not either method.
