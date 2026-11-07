# Conditional plan after read-only reassessment

Status: PLANNED_ONLY, NOT_IMPLEMENTED, NOT_FROZEN, NOT_EXECUTED.
The owner requested brainstorming/research/planning, not experiments.
D1 remains VALIDATED_NEGATIVE; no D2 or old-arm rescue is licensed.

## First question

Can final pre-rigidification RAP endpoint coordinates propose cross-view
correspondences that improve a pose solved on original measured points beyond
the same decoder using rigidly projected coordinates and direct descriptors?

This is a new output-decoder question. It uses the final raw prediction, not
earlier-pose selection, response-derived uncertainty, shared-window projection,
new random seeds or support-pose transport. The current source already uses
raw endpoints for independent per-scan Kabsch fits; that remains the baseline.

## Suggested sequence: roughly one to two working weeks

1. **Days1-2: concrete design and minimal synthetic preflight, conditional on
   a subsequent execution instruction.** Specify one sparse association rule,
   one robust original-point solver, deterministic candidate caps and one
   GT-blind selector. Specify ties, normalization, minimum noncollinear support
   and degeneracy/failure behavior. Check common-gauge/row/scale identities,
   proper rotation and transform direction. Prove raw=rigid-projected reduction
   to native-pose geometric matching. Include nondegenerate wrong2m and exact
   periodic ambiguity controls. Prepare a compact independent validator and
   source/array binding. Do not require every real pair to change.
2. **Days3-4: one actual pose screen on saved F2 outputs.** Keep both complete
   exposed00/08 cohorts, original points/features/final native K4 endpoints,
   generation IDs and admission gate. Use matched correspondence/solver/
   candidate budgets for raw, projected and descriptor controls. A row-permuted
   raw control checks dependence on identity without becoming a competitor.
   Freeze numerical rules and outcome criteria before new outputs. Generate
   and seal the complete GT-blind candidate/selected-pose bank before labels.
   Reuse arrays rather than run the model again. Report actual CPU cost and
   inherited inference cost separately. A method that cannot select its gains
   without GT fails the executable screen.
3. **Days5-7: actual online and metric relevance, only if stage2 passes.** Use
   all71 original online attempts, not only09 or selected F2 recoveries.
   Establish whether existing E0 output artifacts retain adequate raw points;
   if inference is required, freeze native replay and budget separately. First
   compare changed poses with the unchanged graph/gate, then consider a
   physical-factor graph variant only if pose benefit is insufficient and the
   raw associations support it. Include direct geometry with identical factor
   construction. No automatic expansion from a failed online result.
4. **Days8-10 and later: frozen independent confirmation, conditional.** Pin
   the selected mechanism, sources, weights and all hyperparameters. Declare
   sequence/site/checkpoint exposure honestly before full trajectories.
   Measure ter/rer, aligned ATE, admission errors and total cost. Unknown
   checkpoint training membership prevents an unseen-domain claim based only
   on selecting a new sequence. Do not use an already exposed sequence as
   independent confirmation.

The schedule is an effort estimate, not a performance or completion guarantee.
Do not concurrently launch several candidate mechanisms.

## Proposed material decisions, not yet frozen

These are suggestions to finalize with the exact algorithm before outputs;
they are not retroactive amendments to previous protocols.

- Require the **selected**, GT-blind raw-output decoder to outperform the
  projected-output and direct-descriptor controls as well as native RAP.
  Record at least five new
  strict recoveries among the fixed41 hard08 cases as a useful candidate
  creation target; separately require a positive net selected-pose gain over
  all75 positives. Best-of-candidate success alone cannot pass.
- Keep ordinary00/08 performance within a predeclared small regression guard,
  and require no increase in incorrect common-gate admissions or confuser
  admissions. The existing threshold is retained for the first screen.
- Use actual cost, including association search/solver/selection. A suggested
  target is <=25% overhead over the matched native inference path; specify
  how amortized reused-bank analysis and eventual online cost are distinguished.
- For the eventual **both-metrics** claim, target >=0.01 percentage-point mean
  ter improvement and >=5% mean ATE improvement on the declared system cohort,
  with sequence safety guards and a later confirmation. ATE-only improvement
  may be useful evidence but must not be reported as a combined metric gain.
- Stop the new mechanism if raw and projected controls are equivalent in
  performance, if only GT-oracle selection gains, or if physical association
  quality fails to yield actual pose improvement. Do not rescue it with a
  step/weight/top-k/seed/window/cohort sweep after results.

## Separate graph diagnosis

Before a new graph experiment, inspect existing GT-free keyframe span and
correction metadata: scan count, traveled distance, angular motion and loop
coverage. Source's constant aggregated-odometry noise is a fact; its metric
harm is a hypothesis. Specify physical uncertainty propagation, frame
transport and correlated scan-to-map errors rather than arbitrary count-based
scaling. Use an analytic chain/sparsification consistency check before saved
graph replay. This is a new bounded engineering study, not an E1 weight sweep.

If exploring measurement-supported partial factors, use original geometry
and the same factor construction for RAP and direct associations. Do not infer
confidence from FDI1 matrices, mask a known error axis, use GT poses as priors,
or double-count pose and point residuals from the same observations. No such
factor implementation/protocol is selected or running.

## Alternatives if the first mechanism fails

A complete retrieval-opportunity ledger is justified only by a distinct
coverage question. O2's12->40 budget and O3's quota stops remain; listing the
complete proposal exposure is not authorization to expand those arms.

A small cross-view correspondence head on frozen RAP tokens could become a
separate training proposal. It would create correspondences, unlike the
stopped HL support selector. It requires a learnable signal, an explicit
training/data-split annex and a same-label/same-capacity non-RAP head control.
No training is authorized now. Camera evidence would change the current
LiDAR-focused scope and requires an explicit scope decision.
