# Post-F2 action plan (2026-09-27)

Owner authorized planning and execution after F2's independently validated
NO_DEVELOPMENT_MECHANISM_SIGNAL. This plan does not reopen F2 or promote a
post-hoc arm.

## Stage 1 — saved-result diagnosis (execute first)

Run the frozen, read-only `PROTOCOL.md` in this directory on F2's saved
evaluator rows and gate geometry. Report, separately for KITTI 00 and 08:
native/structured/pooled proposal availability, selection misses, correct
rejections, incorrect accepts, and paired changes. Do not fit thresholds,
train a selector, rerun inference, or treat oracle choices as executable.
Record source hashes, a reproducible summary, and an independent aggregate
crosscheck. The diagnosis can localize observed losses but cannot establish
their physical cause or generalization.

## Stage 2 — independent system confirmation (prepare now; execute only after
exact cohort, data, code, metrics and cost are frozen)

Use E0's immutable development_baseline_v2 as the candidate. Audit exposure
and local availability for KITTI 07/09/10, or a separate Boreas session if
needed. KITTI 00/02/05/06/08 are previously observed here and cannot serve
as fresh confirmation. Freeze complete frame IDs, input and code hashes,
data convention, primary camera ter and aligned LiDAR ATE, per-sequence
results, measurement/edge identity, runtime and a same-data KISS-SLAM run.
The aim is to learn whether the current system gains transfer and where the
ATE gap remains. Confirmation is an engineering/system claim, not an
algorithmic novelty claim. No sequence can be chosen after seeing its
outcome. Any data acquisition needs its own byte/time cap and provenance.

## Stage 3 — one new mechanism question (conditional on Stage 1)

If a meaningful number of failed positives have geometrically recoverable
poses or correct generated candidates rejected under partial visibility,
draft a distinct visibility-aware pose-refinement hypothesis. It must change
the pose proposal when needed, not merely relax the acceptance threshold.
Compare on identical pairs/points/budget with native RAP, a strong local
registration baseline, and a no-refinement control. Predeclare gains in
strict pose success, correct accepts, incorrect accepts and system ATE.
Check literature and code for novelty before expensive execution. If the
saved evidence does not support recoverability, do not instantiate this
candidate; select a different, separately scoped question.

Preserve all HL/SC/PG/F2 negative decisions. No production/default change,
old result overwrite, automatic parameter sweep, Git synchronization or
manuscript claim follows from this plan.

## Execution record

Stage 1 completed under `f2-postmortem-01/REPORT.md`: 08 N has 41/75
positives without a correct K4 candidate, 4 selection misses, 13 selected
correct but rejected, 17 correct accepts and 10 incorrect accepts; independent
recount passed. Stage 2 completed under `e0-heldout-01/REPORT.md`: frozen
07/09/10 system comparison supports transfer of E0 arm A against O, with
mixed same-data KISS-SLAM results and declared earlier data exposure. Stage 3
first tested the required recoverability premise under the separate
`rap-refinement-feasibility-01/PROTOCOL.md`: fixed local ICP on all saved
00/08 pairs, no GT parsed or used for pose computation (frozen evaluator
files were byte-hashed for integrity; see R0-AMENDMENT_01). It failed its predeclared 08 feasibility
gate (30/75 before and after; clipped error worsened). Therefore no
visibility-aware local-refiner method is selected or launched. The next
research question must address candidate creation through a genuinely
different mechanism, after focused source/literature audit and a separate
prospective protocol. No automatic new sweep follows these completed stages.
