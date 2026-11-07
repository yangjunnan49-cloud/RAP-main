# After RLP2: value of the negative result and the next research decision

Date: 2026-10-09 (Asia/Shanghai).
Status: READ_ONLY_REASSESSMENT_COMPLETE.
Recommendation: TASK_ALIGNMENT_DESIGN_BEFORE_ANY_NEW_TRAINING.

The owner requested an assessment and next-step recommendation, then said to
continue. This turn reads existing reports, source and nine saved training
traces, and checks primary literature. It performs no model inference, fitting,
new point-cloud/GT payload computation or trajectory experiment. The closed
RLP2 protocol, sources, banks, decisions, failures and resource accounting remain
unchanged. This later descriptive accounting does not amend its recorded budget.

## Scientific value

The result has substantial route-selection and reproducibility value. It does
not establish a successful method, a universal impossibility theorem or an
independent generalization claim. Complete outputs and independent numerical
reconstruction make the observed failure interpretable within the fixed scope.
They do not prove optimizer convergence or identify the cause of poor accuracy.

All numbers below are from the sealed RLP2 report/results. Each window first
uses the median error across the three fixed seeds; cohort medians follow.

| Method | Exposed windows | Translation median (m) | Rotation median (deg) |
|---|---:|---:|---:|
| Direct descriptors D | 48 | 0.951464 | 0.606511 |
| Separated-context tokens I | 48 | 1.392460 | 0.698359 |
| Joint-context tokens J | 48 | 0.888431 | 0.552965 |
| Same-point geometry G3 | 48 | 0.097115 | 0.238968 |
| Identity/no motion | 48 | 0.854124 | 0.250591 |

J passes the full paired R/t and sequence conjunction against I. That is a
limited positive result. I is a possible one-part out-of-distribution ablation
and has different attention work, so this does not cleanly establish the useful
causal contribution of joint generative context. D has smaller effective active
capacity, another limitation of the comparisons.

J fails against D: paired rotation gain is only 0.007573 deg, with 26/48 positive
rotation signs; both cohort ratio conditions fail and 07/09 rotation safety
fails. This is not merely a small threshold miss. J is far worse than same-point
G3, and its cohort medians exceed identity for both components. On the separately
matched 36 KISS endpoints, J loses both components in every paired window.
KISS has a larger dense-map context, but G3 already exposes the absolute gap
without that input advantage. Cohort medians do not imply identity beats J in
every individual window.

The fixed token-row permutation strongly degrades predictions. This establishes
sensitivity to token/coordinate binding under that intervention, not physical
correspondence, calibrated confidence or useful motion information. It cannot
rescue failed practical accuracy gates.

## Additional read-only training-trace accounting

TRAINING_TRACE_ACCOUNTING.json binds all nine source trace hashes. First and
last 144-update blocks each contain the same 144 distinct fitting windows.
Mean online loss changes as follows:

| Seed | D: first -> last | I: first -> last | J: first -> last |
|---|---:|---:|---:|
| 20261007 | 16.609 -> 10.987 | 17.095 -> 11.780 | 14.701 -> 6.713 |
| 20261008 | 16.908 -> 10.009 | 16.749 -> 11.644 | 14.385 -> 6.849 |
| 20261009 | 16.866 -> 13.763 | 17.198 -> 12.182 | 14.941 -> 6.582 |

These losses were measured before individual optimizer steps at changing model
states. They are not fixed-checkpoint training errors. Every recorded
pre-clipping gradient norm exceeds the fixed clip threshold of one in all nine
fits; clipping activity alone does not diagnose an optimization failure.

The traces support learning progress under the training objective. They do not
show that the task was solved, that training converged, or that increasing the
budget would produce useful evaluation accuracy. No fixed-checkpoint fitting
accuracy or learning-curve convergence study was part of RLP2. Thus both
"the tokens cannot learn" and "more updates will fix this" exceed the evidence.

## What to change in our reasoning

The plausible unresolved issue is task alignment across representation,
readout, weak supervision and optimization. All three learned arms performing
poorly makes a shared construction bottleneck plausible; it does not identify
which component causes it. RAP's documented and local-source objective predicts
point velocity toward a registered configuration. Its intermediate tokens were
not explicitly trained as cross-scan matching descriptors. Interpreting this
objective difference as a cause remains a hypothesis.
[RAP, training formulation](https://arxiv.org/html/2512.01850v1).
Local source: rectified_point_flow/modeling.py, _compute_flow_target/forward/loss.

Generic matching-matrix generation and weighted rigid solving already have
strong prior art, including
[Diff-Reg v2](https://arxiv.org/html/2503.04127v1).
Changing the small projector, temperature, soft/hard decoder or loss would not
by itself supply originality. Existing stopped mechanisms must not be renamed
as new experiments.

The next effort should therefore address whether a task-aligned representation
can supply useful measurements, rather than repeatedly interpreting frozen
tokens through another small matching head. The validated banks, row binding,
proper-pose checks, complete-coverage discipline and geometry controls are
reusable infrastructure. Identical extraction/invariance preflights need not be
repeated as new scientific evidence.

## One conditional next direction

Design a limited adaptation of the generative modules for local relative
motion. Retain RAP's native output contract: each original input point has a
generated target position, and the within-scan row binding supports rigid pose
fitting. Do not reuse the stopped cross-scan dual-softmax small-head contract.
The proposed change acts on the representation/velocity generator itself; it
requires a separately reviewed training scope and resource estimate.

Candidate hypothesis: task-aligned generative adaptation can improve coupled
local R/t beyond frozen RAP and a matched non-generative learner, while meeting
geometry baselines, sequence safety and a useful cost budget. This is a
feasibility hypothesis, not an established original mechanism. Ordinary
fine-tuning alone would be insufficient for the owner's originality goal.

Before any run, the design must specify:

1. The task-specific generated target, allowable trainable modules, treatment
   of partial visibility and weak GT, and exact inference contract. A weak pose
   can transform each input point for supervision without claiming exact
   physical point identity across scans. Such targets still inherit GT limits.
2. One measurable RAP-specific mechanism and a primary-literature comparison
   showing what distinguishes it from existing generative registration and
   ordinary task adaptation. If none is defensible, do not proceed under an
   originality claim.
3. Frozen RAP, an equally resourced non-generative learner, same-point G3 and
   endpoint-matched KISS controls. Match trainable capacity, data access and
   report total computation; do not repeat D's padding-capacity mismatch or
   treat I's one-part behavior as a clean causal experiment.
4. Separate prospective fitting-accuracy, held-out-accuracy and system gates.
   Record fixed-checkpoint training R/t as well as online loss, so failure to
   fit can be separated from failure to transfer. Fix coverage, seeds, compute
   limits, R/t conjunctions and every sequence safety rule before outcomes.
5. Honest data roles. Current 07-10 outcomes are historically exposed. Local
   checkpoint membership/site independence remains unknown. A new independent
   claim requires verified independent data; acquisition is not authorized by
   this planning turn. Preserve official GT, metrics and the 09 discrepancy.

The practical order is one concrete design, then one bounded authorized pilot,
then complete predeclared held-out assessment. Trajectory evaluation is
conditional on practical local accuracy and controls; it is not the next step
for the failed RLP2 heads. Resource limits for backbone adaptation cannot be
assumed to equal the closed small-head pilot's limits.

If the design offers only generic fine-tuning, or requires another round of
head/temperature/epoch/window tuning to explain RLP2, recommend closing this
local-motion branch rather than launching it. If the backbone must stay fully
frozen, the accumulated evidence does not justify another readout experiment.
The original breakthrough objective remains unresolved.

## Preserved boundary

RLP2 remains VALIDATED_NEGATIVE / NO_COUPLED_JOINT_READOUT_SIGNAL. Its exact
construction is stopped, without epoch/seed/temperature/loss/density/window/
cohort or decoder rescue. RLP1 and all previous R3/LMF1/RAD1/D1/FDI/PFG1/LC0
stops remain. This report recommends a design direction; no new executable
experiment, trainable-module selection, protocol freeze or budget is established.
No backbone/default/production/manuscript edit, acquisition/install, commit or
Git synchronization occurred.

Primary local evidence:
[RLP2 report](../../2026-10-08/motion-supervised-readout-01/REPORT.md),
[RLP2 protocol](../../2026-10-08/motion-supervised-readout-01/PROTOCOL.md),
and [descriptive trace accounting](TRAINING_TRACE_ACCOUNTING.json).
