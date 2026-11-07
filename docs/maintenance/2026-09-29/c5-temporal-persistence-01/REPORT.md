# C5 fixed temporal-persistence feature mask — complete

2026-09-29. Frozen decision: **NO_TEMPORAL_PERSISTENCE_SCREEN_SIGNAL**
under the [protocol](PROTOCOL.md). On the fixed small observed-development
cohort, a GT-blind same-visit persistence mask on temporal-support
miniSpinNet features generated **zero** new strict candidates among the
six hard08 positives lacking any native F2 K4 candidate. A radial-bin-
matched random mask also generated zero. This fixed constructive route
does not justify a full K4 screen, training or a default change.

## Execution and validation

Protocol, runner, independent validator and171 input/source identities
froze before inference. Synthetic support-to-anchor transform and mask
checks passed. On exactly C4's28 pairs, generation0 T kept true features,
P zeroed support features not repeated within1m under saved causal
within-visit odometry, and R zeroed the same number of randomly chosen
features within each support part/range bin. Two anchor parts, all points,
normalization, noise/seed, weights and five-step sampler stayed fixed.
No cross-visit GT or evaluator label entered mask construction or bank
generation. All28 T raw/state trajectories exactly reproduced saved F2
N0 (maximum delta0.0). The full bank was sealed before labels at SHA256
`e5b3ef0c678c0dbcaca2e8e22129a265113e7b901e9f56d4dfbc11b8c9635bb7`.
Bank wall61.494s, peak allocated GPU0.687GiB, artifact bytes74.56MB;
all caps passed.

Independent [validation](validation.json) passed751 checks: frozen
hashes, every support-to-anchor persistence mask and radial-matched
random mask, all28 T reproductions and P/R trajectories, independent
CPU final pose fits, GT strict labels and frozen decision arithmetic.
`INCOMPLETE` is absent. No earlier output, production code, default or
Git state was modified or synchronized.

## Observed candidate result

Across112 temporal-support parts, the median retained fraction was
**80.2%** (range55.8–91.9%), inside the predeclared 10–90% *median*
adequacy interval. Thus the decision is not the insufficient-mask
support outcome. In the fixed primary six08 native-K4-unavailable
positives, T/P/R strict successes were **0/0/0**. The required P
recoveries>=2 and advantage over R>=2 both fail. P lost one previously
strict00 ambiguous positive; it caused no other strict transitions in
this28-pair screen. Ordinary strict counts stayed00=3 and08=2 across
T/P/R. The mask's one loss and no gains give no positive information
about the usefulness of temporal repeatability for RAP candidate creation.

The inference intervention attenuates descriptors to zero, outside the
usual input distribution; R matches active descriptor counts per part
and radial bin, but does not prove P/R isolates all spatial or feature-
distribution effects. One radius, two supports per visit, generation0,
small exposed development set and anchor-only candidate labels limit
the conclusion. This is a negative for this exact mask, not proof that
temporal or static context cannot help registration.

## Next boundary

Stop this fixed same-visit 1m persistence-mask route. Do not alter radius,
range bins, zeroing strength or sample IDs to rescue C5. C4 showed
support features can affect hard poses, but C5 gives no GT-blind way to
turn that sensitivity into recovered hard08 candidates. A new research
direction must identify a genuinely different candidate-creation
mechanism, compare it with existing overlap-aware/geometric-context
methods and RAP's own global attention, and prospectively freeze safety
and cost gates before new inference. E0's held-out engineering transfer
remains the positive metric result; prior stops, manuscript pause and
no-Git-sync boundary persist. No C6 protocol or method has started.
