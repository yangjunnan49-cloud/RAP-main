# C2 feature-channel intervention — complete

2026-09-28. Decision: **POSE_LEVEL_FEATURE_RELIANCE** on a small fixed
observed-development subset. This establishes that the frozen RAP flow
responds to the per-point miniSpinNet channel under a deliberately severe
within-scan feature permutation. It does not establish that the existing
features are sufficient on hard loops, or that any replacement improves
RAP-SLAM.

## Execution and amendment

The original [protocol](PROTOCOL.md), runner, separate validator and316
input/source identities froze before generation. The fixed saved-order
indices selected28 F2 00/08 pairs. The model checkpoint used restricted
`weights_only=True` loading with explicitly enumerated standard
NumPy/OmegaConf classes; miniSpinNet used `weights_only=True` and strict
loading. All28 true-feature native five-step N0 raw and state trajectories
reproduced the saved F2 artifacts **exactly** (max delta0.0) with the
same points, feature arrays, explicit noise and seed. Arm Q permuted
feature-to-point assignment independently within each of six parts,
leaving point order, feature multiset, model and noise fixed. Its full
28-pair bank was sealed before evaluator labels at SHA256
`feca55849929d11ae4b0152d155bb5d6e981014eb611f996538fbf828c6647c1`.
Bank wall58.178s, peak allocated GPU2.414GiB, artifacts50.14MB; caps pass.

The original evaluator wrote all28 per-pair outcomes, then stopped at
its mistaken `ordinary==8` assertion. The fixed saved-order indices
actually contain **seven** ordinary pairs:00 has3,08 has4. Read
[AMENDMENT_01.md](AMENDMENT_01.md). Original files and the sealed bank
remain unchanged. An amendment hash-froze the partial outcomes and
separate v2 evaluator/validator before summary completion. The original
absolute response threshold **>=6 pairs** was retained, now a stricter
fraction of the observed ordinary group. No new pair or generation was
added. The independent amended [validation](validation_v2.json) passed
1,075 checks including all28 exact native reproductions, deterministic
six-part permutations, independent pose decoding, all28 gate/label and
decision calculations. `INCOMPLETE` was removed after the amended
summary. A second [amendment](AMENDMENT_02.md) corrected the evaluator-only
true-acceptance binding from F2's selected N/R4 to its actual N0 gate.
Distinct `outcomes_v3.json` and `summary_v3.json` preserve that correction;
[validation_v3.json](validation_v3.json) passed285 additional checks.
Accepted totals happen to be unchanged on these28 pairs. The v3 files
are authoritative for acceptance counts. No new generation or decision
change occurred.

## Observed response

The frozen material-pose criterion requires raw-final RMS>=0.005 in
normalized coordinates and pose change >=0.25m or >=0.25deg. **Six of
seven** ordinary pairs pass; six of seven also cross the raw threshold.
Across all28 pairs,27 cross the raw threshold and26 cross the pose
threshold. The large response is consistent with strong model reliance
on point-feature assignment, rather than an inactive channel.

On this fixed subset, shuffling degraded selected generation0 strict
counts:00 **7→2** and08 **6→2**. Accepted-loop counts changed00 **4→2**
and08 **6→3**; these totals include both correct and incorrect accepts
and are not a full-cohort safety analysis. All selected confusers remained
rejected. The permutation destroys feature-point coherence and is out
of the model's ordinary input distribution, so the degradation is a
mechanism check, not evidence that a new feature design will improve
performance. C1's top-1 descriptor information and C2's model reliance
together make input representation a plausible bottleneck on hard pairs,
but different geometric coverage and stratum mix prevent causal
attribution of the original F2 failures.

## Next decision

Retire shuffled descriptors as an intervention, not a candidate method.
Do not train or substitute an encoder in RAP from this small screen.
The next bounded question is whether **another fixed, nontrained local
geometric descriptor on the identical F2 anchor points** has materially
more cross-visit correspondence information than miniSpinNet on the08
native-K4-unavailable positives, under C1's same1m eligibility/top-1
metric and pair-level analysis. A single prospective comparator (for
example fixed-radius FPFH) can test whether useful local geometric
information is present in those point clouds at this budget, without
changing the RAP flow. Declare its exact radius, normals, input,
decision margin and validation before computation; do not sweep it.
Only a convincing information advantage would justify a separately
scoped interface/model adaptation study. The manuscript pause, prior
negative-route stops, original HEADs and no-Git-sync boundary persist.
