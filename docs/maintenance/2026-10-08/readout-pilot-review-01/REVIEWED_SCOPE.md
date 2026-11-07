# Proposed owner approval: RLP1 prerequisites and one fixed small-head pilot

**PENDING APPROVAL.** Read with the preserved DS0 TRAINING_ANNEX_DRAFT.md.
This supplement corrects seed byte order, clarifies full prediction coverage
and proposes additional G3/KISS sequence safety. All other annex settings and
stops remain. It is a reviewable execution scope, not an experiment freeze.

## Goals and stopping decisions

1. Validate separated full-flow I tokens, exact native J replay, weak-label
   construction and the original-point coupled SE3 solver before fitting.
2. Determine whether equally trained J improves both local translation and
   rotation over I and D, under fixed coverage and sequence safety.
3. Determine whether that signal is useful against same-point G3 and saved
   KISS at identical endpoints. Stop after local evaluation if either fails.
4. Only a pass permits proposing a separate full-system ter/ATE protocol.
   System execution and a novelty/independent-generalization claim are outside
   this approval. Hard-loop recovery is not the pilot's measured objective.

## Included implementation and data work

Implement isolated algorithm helpers in RAP-SLAM and orchestration/independent
validators in RAP-main. Create fresh exclusive output directories and freeze
exact code/runtime/checkpoint/source/settings identities before each stage's
outputs. Preserve RAP and miniSpin parameter hashes, mode metadata, native
defaults and all historical banks. Use existing dependencies and data only.

Four engineering windows are 00/05/06/07 t200, native order [199,200,198].
Reproduce sealed J outputs, repeat I, reconstruct grouping and all five times,
validate native length-one versus length-three unused CUDA draws and test the
specified third-scan-noise independence. Run the separately sealed weak-label,
proper-rotation and differentiable-solver preflight. Require the annex's 20
supported positive rows in every pair/direction on all four windows. Freeze
the exact real/synthetic preflight protocol before any new outputs.

Keep the same 204 count-selected windows: 144 fit on 00-05, 12 diagnostic
development on 06 and 48 historically exposed evaluation on 07-10. Preserve
native 1000 points/scan, 32-D descriptors, normalization, roles and five steps.
Use big-endian int.from_bytes(SHA256('LMF1|sequence|t')[:4], 'big'), matching the
sealed LMF1 source and TR0 integer seeds. Fit seeds remain
20261007/20261008/20261009; these are distinct from per-window input seeds.

Seal/independently validate the complete GT-free bank and same-point G3
references before full labels. Generate/seal/independently validate weak labels
under the original annex's 0.30/0.60 m, set-positive/unmatched/ignore/third-view
rules and disclosed readout-only angular convention. Permit only the 144 fit
windows' labels in gradient updates. Development and evaluation outcomes never
choose settings, membership, an epoch or a seed. Disclose the preflight's six
shared frame paths in three draft windows; preserve all selected windows.

Fit three arms D/I/J x three fixed seeds, each 1000 updates, using the annex's
head, optimizer, warmup, losses and original-point solver. RAP and miniSpin
remain frozen. Each arm has nominal 75202 parameters; disclose D's 13762
effective parameters and I's possible one-part distribution shift. Record
full costs rather than claim equal attention work from equal row counts.

Export/seal all primary predictions before evaluator error computation.
Require all 432 seed/window/arm primary poses valid; do not omit failed seeds
or windows. Independently reconstruct labels, input binding, fit/evaluation
separation, pose fits, errors, aggregates, coverage and gates. Saved KISS
07/09/10 has source/endpoint coverage; reverify its identities in the execution
freeze. Do not generate a new KISS08 run or make a KISS08 comparison.

## Exact admission gates

For each arm/window/quantity, aggregate the three fixed seed errors by median,
then use those 48 window values for paired gains, cohort medians and sequence
means. Report every seed result. Seeds are repetitions, not independent scenes.

| Test | Required translation AND rotation |
|---|---|
| J vs each I,D; all 48 | Median paired gains >=0.005 m / 0.01 degrees; median J error <=90% of control median for each; positive fraction >=60% for each |
| Sequence safety vs each I,D | Each 07/08/09/10 mean J-minus-control error <=0.005 m / 0.02 degrees |
| J vs G3; all 48 | Median paired gains >=0.005 m / 0.01 degrees |
| J vs saved KISS; 36 on 07/09/10 | Median paired gains >=0.002 m / 0.005 degrees; median J error <=90% of KISS median for each |
| Proposed added G3 safety | Each 07/08/09/10 mean J-minus-G3 error <=0.005 m / 0.02 degrees |
| Proposed added KISS safety | Each 07/09/10 mean J-minus-KISS error <=0.005 m / 0.02 degrees |

All conditions are conjunctive. Source/control/label/numerical/resource failure
stops before fitting or before a valid result, as applicable. Missing coverage
is COVERAGE_INCONCLUSIVE. A valid negative stops this fixed construction.
J>I/D without G3/KISS usefulness permits only a local readout signal report.
No outcome-dependent density, time, seed, threshold, architecture or window
rescue. Any repair must be separately disclosed and frozen, preserving the
original failure, sources and outputs; changed scientific scope needs review.

## Budget, deliverables and exclusions

Allocated GPU <=3 GiB, process RSS <=4 GiB, new-study artifacts <=4 GiB;
extraction <=20 minutes, each fit <=5 minutes, all compute <=60 minutes.
Compute includes extraction, descriptor/readout/solver work, controls and
validation, including rejected outputs. This is a compute cap, not a promise
that implementation and documentation finish within one hour. Preserve exact
float32 banks; no quantization/density reduction to rescue a resource failure.

Deliver protocol/freezes, preflight results, sealed banks/labels/checkpoints/
predictions, independent validations, all seeds and sequence tables, resource
audit, decision, report and handoff. Preserve failed work visibly.

Excluded: RAP/miniSpin retraining, full trajectory/graph execution, production
or default edits, official GT/old metric replacement, data acquisition,
installation, manuscript edits, commits, Git synchronization and old-arm rescue.

Owner options: approve this complete bounded scope (recommended); approve only
the four-window engineering/weak-label preflight with no full bank or fitting;
or retain the completed design/review without execution. Only the owner's
explicit choice changes the current authorization boundary.
