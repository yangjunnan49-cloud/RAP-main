# M1 support-derived RAP pose hypotheses — complete

Decision: **NO_SUPPORT_HYPOTHESIS_HEADROOM** under the frozen
[protocol](PROTOCOL.md). The [arithmetic clarification](AMENDMENT_01.md)
notes a wording typo in the protocol: four generations times eight
non-anchor transforms give 32 additional support-derived candidates,
plus four original anchor-anchor transforms per pair.

The protocol, runner, independent validator, F2 source/bank and 813
input/evaluator identities froze before construction. A synthetic
nontrivial SE(3) check passed. All 200 exact F2 pairs produced four sets
of nine source-to-target poses from their six saved native per-part
outputs and saved within-visit motion. Every original `T_00` matched
the saved F2 N pose. The complete GT-free bank was SHA-sealed at
`be4df51cede277a9e1165ff48487cd5e1573d0de217ab40ad61821210a624b6e`
before evaluator GT/labels. Bank wall was 36.270 s, artifacts 0.718 MB,
both within caps. Independent validation passed 18,028 checks, including
all 7,200 transforms, source identities, original F2 candidate labels,
every new label and decision. No `INCOMPLETE` remains.

On 08, four of the 41 positive pairs lacking any strict original N/K4
candidate have a strict support-derived pose; only two have an interior
pose (translation <=0.8 m, rotation <=4 degrees). These fall short of
the frozen >=5 and >=3 headroom requirements. On 00 the corresponding
counts are 6/23 strict and 1/23 interior. The best-of-36 oracle totals
are 08 38/75 positive pairs versus original K4 34/75, and 00 58/75
versus original 52/75. On 08, ordinary oracle success stays 15/25;
all 25 confusers remain without a strict pose. These are evaluator-only
candidate availability counts: no GT-blind selector, acceptance gate or
graph outcome was run. The additional proposals are correlated and add
32 candidates per pair.

The exact unpooled support-transport construction stops here. Do not
choose favorable part pairs after seeing labels, weaken the interior
margin, or run a selector using this failed headroom signal. M1 does
show that the current six-part output contains a few unused valid
transforms, but their number and interior quality do not justify a
new method claim. This is distinct from F2's hard group projection and
C6's earlier-donor transport, yet multiview pose consensus is prior art.
No new RAP inference, training, production edit or Git sync occurred.
