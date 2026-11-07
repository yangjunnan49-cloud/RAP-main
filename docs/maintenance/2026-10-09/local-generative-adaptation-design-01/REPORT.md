# Local generative adaptation: design and admission review

Date: 2026-10-09 (Asia/Shanghai).
Status: READ_ONLY_DESIGN_COMPLETE.
Decision: NO_ORIGINALITY_ADMISSION_FOR_CURRENT_ADAPTATION_DRAFT.

The owner said "执行下一步" after the recommendation to design local-motion
adaptation before deciding whether to train. That design/review step is complete.
The source supports a concrete limited adaptation and native-pose interface.
The current construction, however, remains ordinary task adaptation with pose
supervision. No sufficiently distinguished RAP-specific original mechanism was
identified in this bounded review. Under the owner's continuing originality AND
useful-metric objective, do not start this draft's training experiment.

This is a design judgment, not a negative experimental result about adaptation.
No adapter or learner was implemented, instantiated or trained. No cloud/numeric
pose payload was read; the checkpoint was hashed as an opaque file, not loaded.
Eight source/config files and the local checkpoint match RLP2's full-bank freeze.
Source snapshots, static parameter accounting and a bounded primary-literature
review are delivered. All prior experiments and stopping rules remain intact.

## Concrete source result

The local checkpoint/config uses twelve 512-D DiT blocks. Each block has part
attention, global attention and a feed-forward branch. The final velocity MLP
is 512 -> 512 -> 256 -> 3, with no last-layer bias. A draft adaptation can use
rank-eight residual updates in global QKV/output projections of blocks 10/11
(zero-based) and optimize an isolated copy of that velocity MLP.

| Component | Draft trainable parameters |
|---|---:|
| Last-two-block global QKV/output low-rank updates | 49,152 |
| Velocity MLP | 394,752 |
| Total per adapted RAP model | 443,904 |
| Standalone direct-point control | 444,067 |

These are source-derived counts, not runtime model counts. The direct control
uses two 128-D part/global attention blocks and a position-output MLP; all
declared channels/weights have an intended active role. Its trainable count is
0.037% larger, without zero-padded capacity. Equal trainable counts do NOT equal
total network capacity, pretraining, neural work or input distribution.

The original checkpoint and production code stay frozen on disk. Low-rank
modules inside the generator and updates to an isolated velocity MLP still
change the model's function; calling the original trunk weights frozen does
not make this an already-authorized frozen-feature readout experiment.

The generated output preserves within-scan input-row identity. Recover a pose
from each scan's original measured points to its own generated positions, then
form relative SE3. There is no cross-scan positive-row floor or soft matching
matrix. Draft weak targets are rigid transforms of the original input rows,
not claims of physical return identity between scans.

## Testable hypothesis and controls

The strongest concrete hypothesis in the present draft is: explicit coupled
relative-motion supervision of clean estimates across training noise levels
improves useful local R/t beyond ordinary flow-model fine-tuning.

PLAN_DRAFT makes it testable through four equally updated learners: F standard
flow adaptation, G flow adaptation plus native-pose loss, Q a one-pass
pretrained point-output control, and N a standalone non-generative point-output
learner. Frozen native RAP, G3, KISS and identity are separate references.
This avoids relying on RLP2's one-part I ablation for a causal claim.

G versus F measures the effect of an auxiliary task objective. G versus Q also
changes training noise levels and inference integration; it is not an isolated
proof of a generative mechanism. G versus N does not isolate pretraining from
architecture capacity. Even complete success would first establish engineering
usefulness of this adaptation construction. It would not itself establish the
original method required by the owner.

## Why originality admission fails

The original-point/generated-point pose contract is native RPF/RAP. Flow-model
fine-tuning is already documented by RPF's authors. Low-rank adaptation is
established. SE3 generative registration and diffusion-based LiDAR odometry
also precede this draft. PRIOR_ART.md links each source and states the limited
conclusion supported by it. This review does not prove that every possible
future adaptation is non-original, and it does not claim a paper has exactly
reproduced this draft. The present proposal simply lacks an affirmative,
distinguishing mechanism adequate for the continuing research objective.

Several tempting additions were considered and not selected:

- Per-step rigidity or returning rigidified points into the next flow state is
  native RAP, not a new mechanism.
- Shared-window identity/consensus feedback belongs to the stopped D1 route;
  consistent-wrong cases remain a correctness blind spot.
- New confidence, information-shape or support weights do not reopen stopped
  FDI/PFG/support routes or create calibrated uncertainty.
- Visibility/free-space constraints have registration prior art. The retained
  LiDAR exports also do not establish firing-time/beam provenance sufficient to
  treat a coarse ray proxy as a new verified physical correctness certificate.
- Adding semantic information to generative odometry has direct prior art in
  DiffLO, and no new semantic/sensor source was acquired in this review.

## Engineering conditions recorded for future review

The production sampler detaches recorded trajectories and its return value;
it cannot be used as a differentiable rollout merely by setting parameters
trainable. Frozen weights also do not eliminate gradients through changing
input states. Full five-step backpropagation would need earlier frozen blocks'
activation derivatives when earlier adapted outputs change the next input.

The concrete draft therefore uses independent teacher-forced training states
and differentiates only the last two blocks/velocity output. Its first ten
blocks can run without an autograd tape because those training input states do
not depend on the trainable modules. Operations after the first trainable
branch must retain their input gradients, including frozen branches. Native
five-step inference then remains a distinct operation. The training/inference
state-distribution mismatch is disclosed, not assumed solved.

AdamW parameter/gradient/moment storage is only a lower bound of 7,102,464 bytes
per adapted model. Historical 1.387GiB inference peak is NOT a training-memory
measurement. Runtime, gradient stability and the proposed 3GiB cap would need
a separately authorized numerical/engineering preflight before any optimizer
step. PLAN_DRAFT records a capped feasibility scope for possible future owner
review; it is not an executable protocol or a promise that its cap will pass.

## Recommendation and remaining objective

Do not spend the draft's proposed four-hour computation budget solely because
it is implementable. Close this current ordinary-adaptation proposal as a
candidate for an original-method breakthrough. It may be reconsidered only if
the owner explicitly chooses a separately scoped engineering-feasibility goal,
or a genuinely distinguished measurable mechanism is first supplied and
reviewed. Neither choice occurred in this turn.

The original useful-metric/originality objective remains unresolved. Independent
data/checkpoint/site membership, weak short-segment GT and the 09 discrepancy
remain unresolved too. Current 07-10 data remain historically exposed. No
trajectory, GT/metric replacement, stopped-arm rescue, backbone/default/
production/manuscript edit, acquisition/install, commit or Git sync followed.

Read PLAN_DRAFT.md, PRIOR_ART.md, PARAMETER_ACCOUNTING.json, SOURCE_AUDIT.json,
STATUS.json and HANDOFF.md for the reviewable scope and preserved boundaries.
