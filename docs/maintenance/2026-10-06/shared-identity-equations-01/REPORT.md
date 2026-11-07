# SID0 shared-input identity equations: validated engineering preflight

Decision: **PASS_SHARED_IDENTITY_EQUATION_PREFLIGHT**, synthetic CPU only.
All330 frozen cases pass independent validation, including five expected
degeneracy/disconnected-input rejections. This licenses preparation of the
separate four-pair GT-free engineering stage, not an accuracy or novelty claim.

## What was tested

The prior design rejected a single shared rigid scan and tree incidences as
gauge-only native no-ops. The conditional dual-anchor construction projects
raw clean endpoint arrays jointly with unknown window gauges, returns the
rigid predictions to each local window and feeds them into the next state.
This stage tests those equations without a network or dataset.

Before output, the protocol, manifest, three isolated scripts, four original
design dependencies and Python executable were SHA-256 frozen (10 identities).
Runtime: Windows Python3.12.14, NumPy2.3.5. No new dependency was installed.
Freeze UTC06:48:19.843500; complete bank seal06:48:22.412055; independent
validation creation06:48:39.939682 on2026-10-06. All331 sealed files comprise
bank.json and330 NPZs. Frozen source and bank hashes are independently checked
before and after validation.

The32 predetermined geometries contain16 fullrank and16 planar inputs; each
has10 cases, with chain/star, wrong-consistent, five invalid and two analytic
toy cases added. No geometry was filtered, no sample/gate changed after output,
and no engineering failure or repair occurred.

## Evidence and meaning

| Check | Result | Interpretation |
| --- | --- | --- |
| Single window, one shared scan, chain/star tree | Native return preserved | No relative correction is available from this incidence |
| Dual consistent / idempotent input | No-op | Projection preserves its rigid consistent manifold |
| Dual conflicting contexts,32 cases | Minimum maxentry relative change0.035756565 | Effect is beyond common gauge, not a correctness result |
| Independent/common gauges, scales/centers, row/incidence permutations | All identities pass | Coordinate conversion and exact original row mapping verified |
| Unique-factor residual inflated by fixed50m perturbations | Shared traces/termination unchanged | Unique minimized constants do not become gauge votes |
| Coincident, collinear, collapsed target, reflected tie, disconnected graph | All five reject | Undefined fits/topology fail explicitly |
| Constant prescribed vector field toy | C=F=2m relative x | Commuting translation-subspace example |
| State-dependent analytic toy | C=3m,F=3.25m relative x; later raw predictions change | Feedback can differ from identical terminal synchronization |
| Consistent wrong relative pose | Residual effectively zero;2m synthetic error retained | Agreement does not certify truth |

The independent validator uses weighted Horn quaternion eigenproblems, not
the runner's Kabsch SVD, and imports neither projector nor runner. It rebuilds
seeded canonical input points; analytic endpoint transforms and perturbations;
normalized condition fits and physical translation s*t_normalized-R*c;
native fits; tree incidence propagation; every joint solver block/objective/
G/Z trace; variant identities; toy velocity/state/noise recurrence and terminal
control. Maximum independently recomputed array/objective discrepancy is
7.275957614183426e-12, below the frozen1e-9 comparison tolerance. Rotations
pass determinant/orthogonality1e-10.

The solver used at most5 of64 sweeps. The frozen shared-objective stopping
criterion is an objective criterion, not exact stationary-pose or global-
optimum certification. Independent next-block diagnostics remain nonzero:
maxentry pose change2.989509195056028e-7 over conflict cases and
7.735751164972271e-6 across all cases (the50m unique-residual stress example
amplifies a small gauge change in its unique poses). No claim of1e-9 proximity
to an optimum follows from the1e-9 identity/reconstruction checks.
Initialization already supplies almost all shared residual reduction in these
fixtures; subsequent shared-cost decrease spans3.52e-12..1.31e-10. This does
not establish a benefit from iterative rigid solving over initialization.

Bank wall1.157970s, independent validator wall2.167958s, combined3.325928s.
PeakRSS45,805,568 bytes (~43.68MiB); NPZ bank6,757,383 bytes. All fixed
120s/1GiB/20MB caps pass. No GPU, real point cloud, descriptors, checkpoint,
dataset GT, local-error evaluation, trajectory or accuracy metric was read/run.

## Design clarification and boundaries

Before the first freeze, read-only review identified that adding unique-factor
constant residuals to a relative stopping threshold could change termination.
The protocol explicitly discloses the shared-variable-objective stopping
clarification and tests its invariance. Proper-fit uniqueness checks include
raw-target collapse and reflected ties. These changes precede all outputs;
there is no failed original attempt or retrospective sample/threshold repair.

Close projected-denoising/synchronization prior art remains. Synthetic
noncommutation supplies neither added physical observation nor evidence of a
correct candidate. The local checkpoint's unknown training membership and
all historical negative stops remain. No training, production/default/model/
manuscript edit, download/install, commit or Git sync occurred. Original
breakthrough requirement remains unresolved.

Next: follow [NEXT_ROUND_PLAN.md](NEXT_ROUND_PLAN.md). Prepare/freeze one D1
four-pair real-input GT-free engineering stage with identical final-only,
uncoupled-window and native-union controls before model output. D1 is not
implemented/frozen/run in this phase. No candidate/selection/system promotion.

Traceable artifacts: [PROTOCOL.md](PROTOCOL.md), [manifest.json](manifest.json),
[freeze.json](freeze.json), [bank.json](bank.json), [bank_seal.json](bank_seal.json),
[validation.json](validation.json), [STATUS.json](STATUS.json).
