# CV2: fixed rotation, translation-only map refinement on three revisits

Owner2026-10-09: "执行下一轮方案" following CV1 NEXT_ROUND_PLAN. Execute the
new bounded exposed-development B/F/T phase. Prior CV1/SMP2 decisions remain.
This post-outcome reduced-variable hypothesis is explicitly motivated by CV1's
translation/ATE benefit with angle regression, not independent confirmation or
an original mechanism. Conventional geometry is admitted under owner relaxation.

## Inputs fixed before coordinate/optimization outcomes

Sequences00/05/06, each original E0 A accepted-loop array index0; project only
i,j,T_rel,measurement_id. No quality/overlap/GT sorting or substitute unsupported
case. Containers include historically exposed GT fields, not selected on them.
Last8keyframes ending at each endpoint, original source_frame_ids mapping; two
visits must contain16distinct raw paths. Freeze exact nodes/frames/raw hashes,
sources/protocol/calibration/GT-file identities before reading new coordinates.
00is already exposed CV1;05/06are also historically exposed development.

Same finite XYZ,range1.5..80m,+.205deg correction,.5m lex-first voxel,ordered6000
cap,variable point counts. Project saved absolute O and Z rotations to SO3,
retain original/projection deltas. Anchor Aendpoint at node0, otherA7chronological
nodes1..7, B8nodes8..15/Bendpoint15. B=saved RAP Z placement with fixed internal
O shapes. O original odometry is optional descriptive input, not another method.
No new RAP call/retrieval/acceptance/density/time/calibration changes.

Same2m eligible shared-plane criteria at B,complete per-scan moments; retain
patches observed in both visits with>=3contributing scans,total>=40,per-scan>=6
and unchanged flatness/eigenvalue/offset tests. Exact split generalizes CV1:
UTF-8 `CV1|{seq}|{i}|{j}|2|{kx},{ky},{kz}`,no spaces/newline;SHA256 first4bytes
unsigned BIG-ENDIAN modulo4=0holdout. Thus00membership/split is identical to CV1.
Training>=10crosspatches,>=3contributing scans and>=100points per visit;holdout
>=5crosspatches. Show all16scan coverage. No threshold/hash/window rescue.
Keep unsupported records, no optimization or new reference errors for them.

## One new restriction, matched fixed controls

B fixed saved RAP alignment. F matched six-DOF rigid placement refinement using
the byte-frozen validated cross_visit_map_attempt02.py helper; no J or motion-
prior sweep. T three translation variables in the fixed initial Zbody frame.
T holds every scan rotation byte-identical to B and shifts all Bscan positions
by the same world displacement, preserving internal shapes. Use analytic compact
plane Schur H/g reduced by the pure translation mapping; analytical plane nuisance
refit. No duplicate RAP pose factor; all arms share frozen training membership.

24updates,diagonal1e-3damping/floor1e-8,.2m translation steps and unchanged F1deg
rotation steps,backtrack1/.5/.25/.125/.0625,cost increase<=1e-13. Cost .5mean pooled
minimum eigenvalue(clamped0)/.10m^2,equal patch/contributing-scan mass. T explicitly
copies fixed rotations,never recomposes nominal identity rotations. No additional
iterations/warm start/stop rule/point count/search. T endpoint displacement<=5m,
exact fixed rotation, internal shape numerical delta<=1e-9m/1e-8deg. F existing
internal1m/5deg and placement5m/25deg bounds,plus fixed shape check<=1e-9m/1e-8deg.
Invalid outputs saved. Preserving rotation is construction, not evidence it is
physically correct or calibrated. Plane scale is an engineering objective weight.

## Ordering and checks

Numerical preflight before real point payload: Tmoment/explicit gradients and FD,
exact rotation/shape invariance, perfect-input no-op and pure translation recovery,
planar translation-blind tangent, common gauge. Frozen CV1 Fpreflight binds old F
implementation. Seal all3records/B/F/Tpredictions before new numeric reference
outcomes. Independent raw-preprocessing/membership/moment/hash/support/explicit
cost/holdout checks on all48scans; proper poses/traces/corrections and selected
real translation gradients. Reproduce00Finput/output against old validated CV1
bank. Bounded discovery verification,not full optimizer/rejected-feature replay.

Then use unchanged camera->LiDAR invTr*pose*Tr/proper angular/reference/Horn-aligned
ATE conventions:joint16node position ATE,endpoint t/Rerrors and each visit's
endpoint-relative tRMSE/meanR/rigid-alignedATE. Refitting heldout planes is reporting
only,no pose update/backtrack/stop/selection. O-selected/initial B-selected geometry
and correlated neighboring surfaces remain;not independent physical validation.
Unsupported cases stay missing/invalid,not zero or a selected reduced cohort.

## Primary cohort conjunction (T versus B)

All3supported/Tvalid;>=2/3cases improve BOTH jointATE and endpoint translation
(also show individual improvement counts); arithmetic mean fractional gains>=5%
for BOTH; no case ATE or endpoint-t regression>5%; allscan rotation change from
B<=1e-8deg with byte-identical matrices; each visit ATE/tRMSE regression<=5% and
meanRregression<=.02deg; EACH heldout balanced RMSratioT/B<=1.01. Ratios require
positive baseline denominators,otherwise invalid. Independent metrics/gates.
Show F/B,T/B,T/Fchanges but never choose F/TafterGT or promote F by this primary.
Pass means a bounded exposed development signal only,not fullsystem/independent
usefulness. Failure stops this exact fixed-rotation/cohort construction without
scale/hash/density/gate/seed/step/point/window/translation-axis rescue.

New CPU measured-stage combined wall1800s,observed RSS2GiB,dossier512MiB; all
failed/retry stages included. Imports/WSLstartup/design/docs/source-bookkeeping
excluded,not production runtime. No GPU/modelload/training/RAPinference,acquisition/
install,production/default/backbone/manuscript edits,commit/Gitsync. Both original
HEADs/branches/dirty sets,old sources/seals/stops/official metrics+GT persist.
No automatic full-system trajectory/cohort expansion.09/checkpoint/site/exposure/
physical identity/dynamics/calibration/time/covariance unknowns persist.
Established prior art [BALM](https://arxiv.org/abs/2209.08854),no originality claim.
