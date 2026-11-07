# NOC2: fresh-noise relative-pose objective pilot

VALIDATED_PREREQUISITE_STOP; decision **AFFINE_POSE_OBJECTIVE_CONTROL_DID_NOT_FIT**. Owner said "请按照你下一轮判断推进". This is a distinct objective comparison, not more NOC1 draws or an old stop/gate amendment. Freeze147 sources/inputs before payload. Same exposed known-transform copied-descriptor task; real reference fixture executed: 0. 400 optimizer updates: control400 plus V/P400 each per admitted fixture. No nearby window or trajectory.

## Objective and result

B is frozen initialized native RAP. V/P reset to the exact same NOC0 initialized443904-parameter adapters/output MLP. Both use pure-noise tau1, the same eight predeclared noise arrays cycling400 updates, AdamW1e-4/weight_decay1e-4/clip1. V velocity MSE uses established1024 backward scaling/unscale; P metric relative-pose+target-free nonrigidity loss uses double proper SVD and no scaling. Both receive identical normalized observations. P gradient is through its first raw endpoint only; performance is measured with unchanged production five-step sampling, no detached-rollout gradient claim. First-ten-block cache is target-free and exact full forward. No target/teacher/cache at inference, output selector or ensemble.

The36-parameter affine control learns on normalized measured coordinates with pose loss, identity initialization and no reference initialization. Final control errors: [{'part': 1, 't_m': 0.020441778009420306, 'R_deg': 0.008898588289206396}, {'part': 2, 't_m': 0.019929126328269063, 'R_deg': 0.008613129414311464}]; fixed .005m/.05deg gate: False. Analytic affine target representation is an oracle mathematical capacity check only. Unequal architecture/capacity prevents native-versus-control efficacy conclusions.

Mean fifth-step t(m)/R(deg) on16 new evaluation noises, separate from eight fit noises:

| Fixture/part | Mean t B/V/P | Mean R B/V/P | P joint nonworse vs B / V | P absolute pass | Full cell |
| --- | --- | --- | --- | --- | --- |
| Native stages not admitted | - | - | - | - | - |

All selected cells require P absolute .05m/.2deg>=12/16, mean t gain>=10%, median paired t gain>=5mm, rotation mean harm<=.01deg/nonnegative median gain, joint t/R nonworse>=12/16, q90 t harm<=5%/R harm<=.02deg versus both B and V. This asks for incremental pose-objective usefulness under shared new noise coverage. No population test/calibrated safety/scene generalization. V and P differ objective and its explicit .001 shape term; objective alignment versus noise-coverage effects cannot be separately attributed relative to the older different-state NOC0 fit.

Native comparisons were not admitted, or all listed comparative checks passed; use the full-cell and status fields.

## First endpoint losses, not five-step efficacy

| Fixture/arm/noise scope | Mean pose objective | Mean velocity MSE |
| --- | --- | --- |
| Not admitted | - | - |

The saved first/fifth-step per-draw poses/errors and train/evaluation contrast remain in results files. Fitting a tau1 endpoint does not prove fitting intermediate tau states or the final sampler. A failure of the fifth-step conjunction cannot identify a unique state-shift/GT/calibration/capacity cause. A lower first-endpoint objective alone is not promotion evidence.

## Audit, resources and preservation

Objective exact target, known affine representation, common output gauge and three double output-directional finite differences checked before training and repeated independently. Independent Horn geometry versus evaluator SVD reconstructs the final control pose errors. The36-parameter affine output is independently reconstructed from saved parameters. Mathematical target/gauge/output-directional gradients are repeated; full details in validation_control.json. Native trace reconstruction, cache/forward replay and neural gradient checks were not reached. No full400-update AdamW replay, complete repeated census/raw preprocessing/descriptor inference. The failed prerequisite stops before RAP checkpoint loading, native updates/predictions or any real-window payload. Read CONTROL_OPTIMIZATION_AUDIT.md for the declared post-outcome scalar audit; no extra optimizer/forward calls. All attempted stage RSS/GPU recorded, no failure or implementation repair.

3 stages, combined recorded58.790331s, peak GPU allocated/reserved16.81/22.00MiB, RSS1.718933GiB.1800s/3GiB GPU/4GiB RSS/512MiB caps pass; imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Final artifact account in DELIVERY_SEAL.

NOC0 all103 and NOC1 all188 delivery identities, original model/config/checkpoint, sibling helper, both HEADs/branches/two and nine tracked dirty sets unchanged. No acquisition/install, production/default/backbone source/manuscript edit, official GT replacement, new scene/trajectory, commit/Git sync. Old RLP2/map stops, real calibration/timing/reference/checkpoint/site uncertainty persist. Conventional geometry/adaptation credited, no original mechanism or physical/system/generalization claim.
