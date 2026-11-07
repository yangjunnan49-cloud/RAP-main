# PFG1 fixed measured-information system screen

Owner requested an explicit plan and progress. MC1 and PFG0 independently pass.
Freeze this protocol, runner, independent validator, PFG0/source, parent seals,
all98 cached scan inputs, six E0 source poses/frames/keyframes/accepted edges,
evaluator/calibration/code identities before any new measured output. No new
RAP inference, retrieval, acceptance decision, pose refit or scan preprocessing.

## Fixed construction and controls

All58 accepted E0 A RAP loops on00/05/06/07/09/10 keep their original centers Z.
Read only GT-free accepted edge JSON and the independently validated online
input cache. Compute normals only for accepted endpoints; all98 inputs freeze.
Use PFG0's unchanged20-neighbor PCA/uniqueness rule and deterministic tie order.
Mutual nearest pairs inside1m at fixed Z produce two point-plane Jacobians,
rotation-first right tangent in the j frame. H=J^T J, Sigma=diag(native relfloor
sigmas squared), Omega=6H/trace(Sigma H). No positive eigenvalue floor, covariance
calibration, normal-angle/planarity threshold, robust correspondence refit or
rematching. Unsupported geometry uses native diagonal information, disclosed.

N: native replay, exact original pose factors. S: replace each native loop
Gaussian with the measured shape, same center. Q: whiten S with the native
diagonal sigmas, cyclically permute xyz separately in rotation/translation
using [1,2,0,4,5,3], and unwhiten. Q preserves eigenvalues and normalized trace.
S/N/Q retain identical scalar relfloor ref1/cap3, Huber1, odometry sigmas
[.05,.05,.05,.30,.30,.30], prior sigmas[.01]*6, same keyframes, loop order and
LM100 iterations. Only one loop factor per edge; no duplicate pose/point factor.
Use the unchanged piecewise-constant dense correction propagation. Sequence10
has no loop and must reproduce the native no-op.

This models directional curvature at a fixed center, discarding the original
surface-residual offset. It is not full point-plane BA, calibrated covariance,
independent-point probability or a physically verified pose. Wrong aliases can
remain consistent. Generic geometry/PGO prior art prevents a standalone RAP
originality claim. Existing checkpoints have unknown training membership.

## Separation and verification

Seal complete normal/shape/three-arm trajectory bank before any new evaluator
GT read. Independent validator imports no new runner or algorithm: reconstruct
all neighborhoods/nearest pairs by brute force, normals by SVD, both Jacobians
by cross products, Gram matrix by explicit row products, and every graph by
direct GTSAM construction. Compare all18 dense trajectories, factor information
and source identities. Tolerances: normal projectors1e-8; H relative1e-9 with
absolute1e-7; Omega/square roots1e-7; trajectory max entry1e-5; original native
saved replay1e-5. A shared GTSAM optimizer is used, not an independent global
optimality proof. No evaluator data enters bank or bank validator.

Only after its independent validation seal run unchanged aligned LiDAR ATE
and KITTI camera ter/rer. Independent historical scalar segment/Horn-equivalent
rigid-alignment code rechecks all segment identities and scores, aggregates,
gates and historical N metrics; tolerance1e-6 aggregate,1e-9 segment translation
fraction,1e-8 rotation per meter. No scale fit; all original frame IDs retained.

## Gates and stopping

For each of development00/05/06 and exposed-transfer07/09/10: S versus N must
gain >=.01pp mean ter AND >=5% mean aligned ATE. Directional attribution
requires S mean ter AND ATE strictly below Q in each cohort. Each sequence
ter regression<=.01pp and ATE regression<=5%;10 trajectory delta<=1e-5.
Cost gate: S incremental normal/shape processing plus S graph/propagation <=25%
of154.09s original loop_closure timing sum (42.41+29.65+22.62+20.48+22.38+16.55).
This is warmed cached-input incremental cost; exclude N/Q, validation/evaluation
and earlier source acquisition, report them separately. No original bank reads
of metrics during production. Per stage3600s, RSS4GiB, artifacts300MiB.

All gates are conjunctions. Failure gives NO_MEASURED_INFORMATION_SHAPE_SIGNAL
and stops this exact construction without radius/normal/eigenaxis/scalar/cohort
rescue. Passing gives a conditional engineering signal only; independent
confirmation and RAP-specific novelty remain separate. Neither result permits
default/manuscript promotion. Preserve all prior stops, sealed banks, original
failure disclosures, HEADs/branches/dirty work, official GT/metrics and09
physical discrepancy. No training, production/default/model/manuscript edit,
acquisition/install, commit or Git sync. Preserve any failure/INCOMPLETE and
use disclosed separately frozen repair rather than modifying frozen sources.
