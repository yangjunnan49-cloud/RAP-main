# NOC2: independently validated control prerequisite stop

Status **VALIDATED_PREREQUISITE_STOP**; decision **AFFINE_POSE_OBJECTIVE_CONTROL_DID_NOT_FIT**. Owner said "请按照你下一轮判断推进". The new tiny pose-objective pilot was implemented and frozen, and its mathematical checks and36-parameter control training were executed. The control failed its prospective translation threshold. RAP adapter fitting, native sampling and the real-window stage were therefore not executed. This is a control optimization prerequisite result, not a negative native pose-objective comparison.

This report corrects conditional-versus-completed wording in the first delivery report. All scientific source/input freezes, arrays, optimizer records, metrics, gates, resource accounts and the original53-entry delivery seal remain byte-identical. See SCOPE.md and this folder's checks/seal.

## Executed evidence

Same NOC0 known-transform synthetic task: three1000-point parts with copied native32-dimensional descriptors. Known mathematical transforms, not measured descriptor invariance.147 source/input entries were frozen before payload. Eight fit and16 evaluation CUDAfloat32 noise arrays were generated and sealed; neither noise set was used in any RAP update or evaluation because admission stopped at the control.

The objective decodes each output part using proper differentiable float64 SVD, restores metric coordinates, eliminates the common output gauge through relative poses, and uses translation/.05m and rotation/.2deg squared terms plus.001 target-free nonrigidity. It is engineering supervision, not calibrated likelihood. The36-parameter control has a separate affine matrix/bias per part, starts identity/zero bias and receives only normalized measured coordinates at forward time. It trains400 fixed AdamW1e-3/weight_decay1e-4/clip1 updates using known-transform supervision; no target-derived initialization or best-checkpoint selection.

| Final control output | Translation error | Rotation error | Fixed .005m/.05deg gate |
| --- | --- | --- | --- |
| part1 | .020441778m | .008898588deg | Fail: translation |
| part2 | .019929126m | .008613129deg | Fail: translation |

An analytic target affine representation matches within5.35139193e-8 normalized coordinates; this is an oracle representability check, not a learned performance candidate. Exact-target objective2.73910972e-13 and common-gauge loss difference3.86535248e-12 pass. Three float64 output-directional gradient finite differences differ at most2.86115217e-7 absolute. All mathematical checks independently repeat. These are bounded checks of this loss, not every possible derivative or a convergence proof.

Independent Horn geometry reconstructs the final control pose errors: maximum evaluator discrepancy3.915e-15 across translation(m)/rotation(deg), with affine forward reconstruction within2.98023224e-8 normalized coordinates. All400 update rows and sealed parameter/output identities are checked. No independent400-update AdamW replay or raw-preprocessing/descriptor inference.

## Interpretation and next judgment

The400th recorded loss is before its update, whereas the final errors above are after update400. The pre-update loss falls from325.175971 at update1 to.223681 at update400, but the last100 losses range .019218073 to1.237501008. Every unclipped gradient norm exceeds1 (minimum464.518311; maximum36621.410156), so global clipping is active throughout. This documents oscillation and unestablished fixed-budget convergence. It does not identify clipping, parameter units, weighting, common-gauge freedom or SVD as a unique cause. See CONTROL_OPTIMIZATION_AUDIT.md in the parent folder for the explicitly post-outcome scalar audit, zero additional optimizer/forward calls.

The family can represent the mathematical target and the bounded objective checks pass. The next priority is therefore a separate control-conditioning design: proper rigid relative-pose parameters in metric translation/radians with a fixed anchor gauge, independently verified gradients and prospectively fixed optimizer/stopping/resource rules. No such new control is implemented/frozen. Do not rescue NOC2 by additional updates, rates, seeds, initialization changes or threshold relaxation. Native learnability and objective usefulness remain untested by this stopped pilot.

## Implemented but unexecuted stages

The frozen proposal compares same-capacity443904-parameter V velocity-MSE and P relative-pose/shape fits, both reset to the exact NOC0 initial arrays, using identical eight pure-noise tau1 fit inputs and400 updates. Primary evaluation would use the unmodified native five-step sampler on16 new noises against both V and frozen B, with absolute capability and paired mean/sign/tail gates. A full independently validated synthetic conjunction would admit one original real00/t2 weak-reference window. Those adapter/control comparisons, cached neural forwards, neural gradient checks,72-trace prediction banks, per-draw native results and real inputs were not produced here. Their implementation is not execution or success evidence. No gradient through the production sampler's detached trajectories is claimed.

## Resources and preservation

Three successful recorded stages total58.790330601s, including control400 updates and independent stop audit. Peak GPU allocated/reserved17630208/23068672bytes; RSS1845690368bytes. All attempted RSS captured, no failed execution stage or numerical implementation repair.1800s/3GiB GPU/4GiB RSS/512MiB caps pass. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded; not production latency. The small final artifact account is recorded in the corrected delivery checks.

NOC0 all103 and NOC1 all188 delivery identities, original model/config/checkpoint and sibling helper, both HEADs/branches/two and nine tracked dirty sets are preserved. RAP checkpoint was hashed, not loaded; no RAP update/inference or descriptor-model load occurred. No nearby/trajectory, production/default/backbone-source/manuscript edit, official reference replacement, acquisition/install, commit or Git sync. Historical stops/seals and physical/reference/time/site/checkpoint unknowns persist. Conventional geometry is credited; no physical/system/generalization gain or original mechanism claim.
