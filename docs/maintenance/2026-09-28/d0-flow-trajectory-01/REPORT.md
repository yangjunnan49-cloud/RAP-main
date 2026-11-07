# D0 saved native flow trajectory audit — complete

2026-09-28. Decision: **NO_TRANSIENT_CANDIDATE_EVIDENCE** under the
prospective [protocol](PROTOCOL.md). On the 41 KITTI08 positives where
native F2 K4 had no strictly correct final candidate, only four had a
strict candidate at any earlier saved raw endpoint, below the declared
five-pair threshold. More importantly, the fixed executable penultimate
checkpoint produced no net strict gain on08 and substantial regressions
on00. Do not develop an early-checkpoint or step-selection rescue from
these observed-development outcomes.

## Provenance and execution

This audit decoded existing F2 native N trajectories only: 100 saved
pairs/sequence, four generations and five raw clean endpoints per
generation. No RAP inference, new raw acquisition, GPU, training or gate
change occurred. A synthetic normalized rigid decoding test passed;
the protocol, original runner/validator and 1,294 source/input identities
were SHA-frozen before real decoding. These included all 800 N trajectory
files, 200 normalized input files, raw anchor scans, F2 records/gates and
evaluator GT identities. The runner parsed no GT or stratum labels. Its
complete 4×5 pose bank was sealed at SHA256
`113f083ea3832b91d35944aa470a138e9686718bcafb617a1302815a98a45bfb`
before evaluator-only labels.

The first frozen runner stopped at pair 51 before producing a bank or
reading GT: CPU float64 refitting changed the final pose by up to ~5e-5
relative to the saved GPU float32 F2 fit, causing a 1e-5 gate
mean-distance assertion to fail. [AMENDMENT_01.md](AMENDMENT_01.md)
records the all-pair, GT-free numerical diagnosis. The original frozen
files were preserved. Separately hashed version-2 scripts retained the
<=1e-4 final decode crosscheck, used F2's *exact saved final pose* for
the baseline gate, and used refitted poses only for intermediate steps.
The final gate reproduced F2 exactly. The amendment was frozen before
the successful bank run; there was no parameter or outcome selection.

The completed bank took 23.607s, peak RSS 0.341GiB, new artifacts
4.18MB; all predeclared caps passed. Independent
[`validation.json`](validation.json) passed 5,484 checks: original and
amendment hashes, exact pair/generation/step identity, all labels and
decision arithmetic, final F2 pose/gate equivalence, and 160 independent
Torch CPU refits of saved raw endpoints plus 16 spot gate recomputations.
The `INCOMPLETE` marker was removed after bank seal and summary and before
validation.

## Results

Each step's K4 oracle count asks whether **any** of four saved generations
is strict at that step. It uses evaluator GT and is not an executable
selector. The fixed penultimate checkpoint uses the same generation that
F2 selected by its original R4 mean-rigidity rule, then applies the
unchanged F2 acceptance gate.

| Sequence | K4 oracle strict at steps 0→4 /75 | Final-K4-unavailable with any earlier strict candidate | Fixed step3 strict vs final /75 | Correct accepts step3 vs final | Incorrect accepts step3 vs final |
|---|---|---:|---|---|---|
| KITTI00 | 33, 30, 33, 41, 52 | 3/23 | 39 vs 49 | 18 vs 23 | 6 vs 1 |
| KITTI08 | 17, 21, 25, 32, 34 | 4/41 | 30 vs 30 | 16 vs 17 | 10 vs 10 |

On00, the fixed step3 selection had one strict gain and eleven losses,
including five ordinary losses. The same five previously correct accepts
became incorrect accepts. On08 it had three strict gains and three losses;
correct accepts lost one and no new incorrect accept appeared. All 25
confusers per sequence remained rejected. Mean clipped positive error
increased from final to step3: 00 1.472846→1.599212 and
08 1.579930→1.649307. The 08 transient four were
`08_2491_3880`, `08_2532_3838`, `08_2542_3838` and `08_720_1448`;
the 00 transient three are retained in `summary.json`. These are
post-hoc oracle facts, not selectable improvements. Of the four 08
transient pairs, only two became strict under the fixed selected step3;
the selected method still had no net gain.

The predeclared `transient_08` threshold and the executable step3,
acceptance-safety and 00 regression guards all failed; only cost passed.
This bounded negative result concerns the saved native five-step
trajectory, float64 readback and fixed step3 comparator on the two
observed-development sequences. It does not prove a different model,
training distribution or principled future checkpoint policy cannot
help. It gives no reason to select an earlier step using GT or tune an
intermediate rigidity score now.

## Research boundary

Stop this saved-checkpoint route. V0 visibility guidance remains stopped,
as do F2 structured-motion and the prior HL/SC/PG branches. The many
missing final candidates and generally rising oracle availability across
the five steps point back to the *conditional candidate generation*
problem, not premature stopping as a supported fix. The next useful
question should audit RAP's input and feature-conditioning conventions
against its released inference/training assumptions, then define one
separately frozen model-specific test only if that audit identifies a
concrete mismatch or mechanism. Do not infer a production change or
thesis novelty claim from D0. No Git synchronization occurred; original
HEADs and existing dirty work were preserved.
