# CV1: one actual revisit, rigid versus joint internal-pose refinement

Owner instruction2026-10-09: "执行下一轮方案". This authorizes the concrete SMP2
NEXT_ROUND_PLAN isolated exposed-development pilot, not whole-sequence execution,
new RAP inference/training or production changes. Originality/rigor relaxation
continues; conventional geometry is eligible without an original-method claim.
This protocol resolves implementation details prospectively before new outputs.

## Fixed inputs and representation

Sequence00original E0 A accepted-loop array index0:2429->3373, measurement_id
ef08402bdc746147a081b1137926970c29f435d724db04ef096c8f11d475977e. Use only the
previously bound whitelist; source container historically exposed GT fields.
A keyframes2378/2384/2391/2398/2405/2413/2423/2429;
B3318/3324/3331/3338/3345/3352/3361/3373. No alternative edge/frame selection.
Freeze sources/protocol/16raw hashes/GT+calibration hashes before reading new
coordinates. Same finite XYZ/range1.5..80m/+ .205deg correction/.5m lex-first voxel/
ordered6000cap. Keep variable-length lists. No point-time invention or deskew.

Saved absolute O rotations and RAP Z are projected to proper SO3, original and
projected matrices/deltas retained. Express both visit shapes relative to their
own endpoints. Anchor A endpoint identity; initialize B endpoint with Z. O keeps
the original odometry relative endpoint placement. B denotes saved one-loop Z
alignment with fixed internal O shapes, not a replay of the complete E0 graph.
Use node order[Aendpoint,Aother7chronological,B8chronological]; groups0..7/8..15,
B endpoint15. Chronological edges(1,2)..(6,7),(7,0),(8,9)..(14,15),14total.
No temporal-gap edge. Every arm has the same points and frozen identities.

Eligible plane construction at B uses unchanged2m/shared_plane_map.py criteria.
Keep patches with observations in both visits, >=3contributing scans,total>=40,
per-scan>=6 and unchanged plane flatness/eigenvalue/offset criteria. Complete
patch hash UTF-8 `CV1|00|2429|3373|2|{kx},{ky},{kz}`, no spaces/newline; first4
SHA256 bytes unsigned BIG-ENDIAN, modulo4=0holdout. No ranking/forced split.
Support requires>=10training cross-visit patches,>=3contributing scans and>=100
training points per visit;>=5cross-visit holdout patches. Report all16scan coverage.
Failure stops this exact source before F/J, preserving an unsupported record.
No new edge,scale,hash,density,flatness or support-floor rescue.

## Solver and controls

O: original odometry placement. B: saved Z placement, both shapes fixed.
F:6variable B endpoint placement; A fixed and B_i=X_B L_Bi exactly. Map endpoint
right tangent to each B scan with Ad(L_Bi^-1). Same compact plane Schur system
as J, reduced by that variable mapping; analytic plane refitting each cost.
J:15free scan poses with A endpoint fixed; same cross-visit plane objective plus
only14within-visit edges, engineering scales .10m/.15deg, averaged by14.
Geometry cost .5mean(max(lambda_min,0))/.10m^2, equal patch/active-scan mass.
No RAP Z factor duplicates these observations. F has no shape prior because
its internal shape is fixed; its motion cost is numerically zero. Noise scales
are regularization choices, not calibrated independent covariance.

Both start B,24updates,1e-3diagonal damping with floor1e-8, per-variable rotation
step<=1deg/translation<=.2m, backtracking1/.5/.25/.125/.0625, no increase beyond
1e-13. Product right retraction; full rigid poses/proper inverses. Internal
endpoint-relative shape corrections<=1m/5deg; B endpoint correction from Z
<=5m/25deg. Invalid predictions remain saved without imputation. No fitting,
warm-start search, rematching, increased updates or optimizer rescue.

## Ordering, preflight, validation and metric decision

Synthetic preflight: compact vs explicit-point H/g; reduced F tangent gradients;
J geometry/prior FD; two separate motion-chain gauges/no-gap test; exact fixed
F internal shape; perfect/no-op and three-plane recovery; planar blind tangent.
All sources/synthetic choices freeze first. Seal complete raw/moment/O/B/F/J
bank before parsing new numeric evaluator poses. Independently check all16raw
preprocessing, retained membership/moments/cross-visit support/hash/coverage,
explicit costs/holdout, proper poses/corrections/traces/selected real gradients.
Bounded discovery checks, not full optimizer replay or rejected-feature census.

Only then use unchanged camera->LiDAR invTr*pose*Tr convention. Report endpoint
relative t/Rerror, joint16node rigid-aligned position ATE, each visit's internal
endpoint-relative tRMSE/mean R/rigid-aligned ATE and held-out balanced patch RMS.
Each visit uses endpoint anchoring and all7nonendpoint errors (the old local
errors helper receives endpoint first). Refitting holdout plane nuisance geometry
is reporting only, never a pose update/stop/selection. This is consistency with
O-selected membership, correlated observations and imperfect official short-
segment references, not statistically independent physical validation.

F or J versus B engineering conjunction: valid correction; jointATEgain>=5%
AND endpoint translation gain>=5%; endpoint Rregression<=.01deg; each visit
ATE/tRMSE regression<=5% and mean Rregression<=.02deg; holdout RMSratio<=1.01.
J versus F internal-pose claim requires same conjunction plus valid F/J.
Use all O/B/F/J even if none passes. If only F improves, report conventional
rigid refinement, not internal BA/RAP originality. Independently reconstruct
all metrics, gains and gates. A single case is not system utility/generalization.
If support fails, no new pose-reference evaluation is necessary or authorized
as a rescue; retain a validated prerequisite stop.

## Resources and stops

New combined measured-stage CPU wall1800s, each attempted process observed RSS
<=2GiB, dossier512MiB. Every failure/retry counts. RSS/time records in finally;
imports/WSL startup/design/docs/bookkeeping excluded and disclosed, not production
latency. No GPU/model/checkpoint load/training/RAP inference, acquisition/install,
production/default/backbone/manuscript changes, commits or Git sync. Both original
HEADs/branches/dirty sets and all old sources/seals/stops/official GT+metrics
preserved.09/checkpoint/site/exposure unknowns remain. Do not automatically run
the proposed00/05/06confirmation cohort or complete trajectory after this case.
Established prior art: [BALM](https://arxiv.org/abs/2209.08854).
