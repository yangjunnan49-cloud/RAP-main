# After RLP1: test motion supervision once, with a fixed stopping boundary

Date: 2026-10-08. Status: READ_ONLY_DESIGN_COMPLETE. The owner requested an
interpretation and next plan after the validated RLP1 prerequisite stop.
No new experiment, point-cloud/pose payload read, label computation, model
inference, optimizer update or trajectory execution was performed in this turn.

## What the result means

RLP1 did not test whether joint RAP tokens can learn useful motion. Its
mandatory supervision rule failed before any fitting: in the fixed06t200
window, adjacent scans199/198 have15 supported positive rows in each direction,
below the prospective20-row floor. The separate audit reproduces all saved
labels and counts. The primary199/200 pair has23/20 positives and meets that
floor; this does not override the all-pair requirement. Keep the stopped run,
its original gates, incomplete weak bank, failures and seals unchanged.

The20-row gate was a prospective engineering admission condition, not a theorem
about learnability or rigid-pose uniqueness. Fifteen geometric-positive rows
neither prove a unique well-conditioned pose nor prove an unusable pose. Their
spatial arrangement, ambiguity and physical correctness were not diagnosed by
this count. RLP1 correctly honored its contract, but a next task should avoid
making an arbitrary correspondence-count proxy the scientific conclusion.

Source confirms that a positive row requires BOTH a sampled partner within.30m
and sampled third-view support within.60m. Each scan contributes only its native
1000 processed points. The conjunction can discard observations in overlapping
scenes when sparse samples do not coincide. This is a plausible mechanism,
NOT an independently established cause of the06 shortage. Existing records do
not separate sampling, physical overlap, occlusion/dynamics, threshold effects
and short-segment GT uncertainty. No threshold sweep or new geometry audit was
run to manufacture a cause.

The useful positive result is engineering: joint J replays exactly, separated I
is independent throughout all five flow calls, and original measured rows are
bound to exported tokens. That interface can be reused after source/seal checks;
another generic inventory or repeat of identical engineering evidence is not
the next scientific question.

## Recommendation

Give the frozen representation one bounded, actual learning test under a
different target: **predict a coupled relative rigid motion using pose-level
supervision, with latent soft weights between original measured points**.
Remove explicit positive/unmatched/third-view row classification from the new
task. Retain direct descriptors D, separated tokens I and joint tokens J as
equally optimized controls. The recommended implementation is detailed in PLAN.

This is a new proposed experiment, not an amendment making RLP1 pass. It changes
the training target, removes the row-classification head, and uses the same
continuous original-point pose solver during training and inference. RLP1's
hard mutual-match decoder is not carried over. Its old15/20 outcome remains a
failure of the original task. New success gates concern complete predictions,
coupled motion accuracy, controls and cost; they are not selected to recategorize
those15 rows.

Why this direction first: it directly measures the unanswered scientific
quantity, needs no denser RAP input, new sensor, data acquisition or exact
cross-scan point identity, and reuses the validated token interface. Its risks
are real: partial overlap, soft-weight concentration, nonunique SVD derivatives,
weak GT and dataset shortcuts. Pose supervision can succeed with geometrically
ambiguous latent weights, so no physical correspondence/confidence claim follows.

## Alternatives considered

| Direction | Assessment |
|---|---|
| Lower20 to15, replace06, enlarge thresholds, keep only passing windows | Outcome-dependent rescue of the stopped task; do not execute |
| Increase native RAP input density | Changes the model experiment and cost; unnecessary before an actual representation-learning result |
| Dense-surface or patch-overlap supervision | Scientifically reasonable alternative, but needs a separate target construction and support-resolution study; not selected in parallel |
| Unsupervised cycle/identity agreement alone | Existing consistent-wrong examples defeat correctness claims; not sufficient supervision |
| Direct pose regression from globally pooled tokens | Cheap, but easier to exploit motion priors and abandons the measured-point solver; not selected |
| Pose-supervised soft original-point solve | Selected recommendation for one fixed-budget test; possible instability/ambiguity explicitly retained |

## Prior art and physical limits

DCP already couples soft matching with a differentiable SVD. Its official
training code uses rotation and translation losses, demonstrating that rigid
transform supervision need not require a list of exact point identities.
[DCP paper](https://openaccess.thecvf.com/content_ICCV_2019/html/Wang_Deep_Closest_Point_Learning_Representations_for_Point_Cloud_Registration_ICCV_2019_paper.html),
[authors' loss implementation](https://github.com/WangYueFt/dcp/blob/master/main.py).
RPM-Net already uses soft assignment and weighted rigid estimation, including
partial visibility. [RPM-Net paper](https://openaccess.thecvf.com/content_CVPR_2020/html/Yew_RPM-Net_Robust_Point_Matching_Using_Learned_Features_CVPR_2020_paper.html).
Patch-overlap supervision is also established in
[GeoTransformer](https://openaccess.thecvf.com/content/CVPR2022/html/Qin_Geometric_Transformer_for_Fast_and_Robust_Point_Cloud_Registration_CVPR_2022_paper.html).
These sources motivate feasibility, not a transferable performance guarantee.
No external implementation/checkpoint was acquired or reproduced.

The proposed small readout, soft solver and pose loss are therefore NOT an
original algorithm by themselves. A successful J-versus-I/D test would support
the value of frozen joint generative representations for measured motion. It
would not establish novelty of the whole construction. A RAP-specific causal
mechanism, strong controls and actual system benefit remain necessary for the
owner's original breakthrough goal.

KITTI explicitly changed evaluation to100-800m segments because very short
GPS/OXTS segments had large GT errors that biased evaluation.
[Official KITTI evaluation specification](https://www.cvlibs.net/datasets/kitti/eval_odometry.php).
Pose supervision does not eliminate this weakness. Small paired local gains are
exploratory scores against the supplied convention, not physical millimetre
accuracy. Preserve raw GT, the declared nearest-proper-rotation readout convention,
official system metrics, the09 discrepancy and unknown checkpoint membership.

## Scope and decision

Planning is complete; execution is not authorized by this planning request.
The former complete approval covered RLP1's fixed scope, which has closed at its
mandatory prerequisite. Main AGENTS explicitly requires a new request/scope for
the distinct task. A future authorization should cover the new numerical
preflight, fixed204 bank, nine fixed fits and complete local evaluation together.
It should not stop at another proxy-only study. System insertion is conditional
and separately scoped after a useful local result.

If the new fixed pilot does not beat trained controls in BOTH rotation and
translation, discontinue investment in this frozen-token/small-readout route
under the current project budget. This is a research priority decision, not a
proof that every architecture or training regime is impossible. If J beats I/D
but not G3/KISS, retain a representation result only and do not enter trajectories.
The plan deliberately does not preselect a sequence of fallback losses/heads.
