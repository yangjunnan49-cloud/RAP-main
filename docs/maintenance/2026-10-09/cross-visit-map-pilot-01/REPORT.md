# CV1 actual revisit: translation/ATE benefit with a rotation tradeoff

Status **VALIDATED_EXPLORATORY_COMPLETE_WITH_IMPLEMENTATION_REPAIR**; decision
**NO_FULL_POSE_CROSS_VISIT_CONJUNCTION**. Owner instructed "执行下一轮方案".
The fixed00revisit2429->3373 and both eight-scan visits were executed. Rigid
map refinement yields the first material translation/jointATE effect in this
measured-map mainline, but fails the predeclared rotation guard. Joint internal
optimization adds little under this construction. No system gain, full-pose
conjunction, independent generalization or original breakthrough is established.

## Fixed source and results

Original accepted E0 A record0/measurement_id
ef08402bdc746147a081b1137926970c29f435d724db04ef096c8f11d475977e.
A2378/2384/2391/2398/2405/2413/2423/2429;
B3318/3324/3331/3338/3345/3352/3361/3373. All16raw inputs independently checked,
96000retained points with frozen preprocessing. Proper Oprojection maximum
4.799011188e-11; Zprojection 1.740879502e-07.
All216eligible2m patches span both visits;163training/53whole-patch holdout.
Training per-visit point coverage7075/6885,holdout2181/2126;all8scans supported
in each visit. No favorable replacement/hash/scale/window selection.

O retains original odometry relative placement. B uses saved RAP Z with fixed
internal O shapes (single relative-pose alignment, not complete E0 PGO replay).
F adjusts only six rigid placement variables. J frees15scan poses, fixes Aendpoint
and adds only14within-visit motion edges at.10m/.15deg averaged by14. No fabricated
temporal-gap edge or duplicate RAP pose factor. Both use identical training
cross-visit moments, analytic plane refit, Schur elimination and24updates.

| Arm | Joint16node aligned ATE(m) | Endpoint translation error(m) | Endpoint rotation error(deg) |
|---|---:|---:|---:|
| O | 0.621228 | 1.205342 | 0.619183 |
| B | 0.403028 | 0.786381 | 0.194126 |
| F | 0.381489 | 0.723821 | 0.220591 |
| J | 0.380282 | 0.721861 | 0.224886 |

F versus B:ATE **+5.344%**,endpoint translation **+7.955%**,rotation **+.026466deg**.
J versus B:ATE **+5.644%**,endpoint translation **+8.205%**,rotation **+.030760deg**.
Both meet the5%ATE/translation conditions, valid-correction/internal safety and
holdout conditions, but both exceed the **.01deg rotation regression** guard.
All conjunctions fail; do not retroactively relax that guard or present full
SE3improvement. Angles use the prospective proper-rotation convention; historical
accepted-loop GT fields and official metrics are unchanged, not reclassified.

J versus F improvesATE only **.316%** and endpoint translation **.271%**, with
rotation **+.004294deg**. It misses both5%requirements for internal-pose value.
J's A internalATE improves3.276%,B.435%;Binternal tRMSE regresses.792%, all
internal guards pass. This does not prove all BA useless, or separate its fixed
prior from geometry bias. It gives no evidence to expand this exact Jconstruction.

| Arm | Training balanced patch RMS(m) | Heldout balanced patch RMS(m) |
|---|---:|---:|
| O | 0.227111 | 0.225239 |
| B | 0.052995 | 0.051398 |
| F | 0.051638 | 0.050713 |
| J | 0.051365 | 0.050530 |

Heldout RMS F/B=.986665736,J/B=.983099155,J/F=.996385219. Those reporting-plane
nuisance fits never inform updates/backtracking/stopping. Membership/eligibility
were selected at B using all geometry, so O cost is evaluated on B-selected
support, not an unbiased comparison. Nearby surfaces/scan observations remain
correlated. Lower residual and good normal spread are not physical verification.

F endpoint correction.064062m/.079296deg,internal shape preserved to2.08e-12m.
J endpoint correction.066044m/.076965deg,maximum internal correction.012470m/
.020992deg. Both within prospective1m/5deg internal and5m/25deg placement bounds.

## Engineering repair and verification

Original51entryfreeze/sources/snapshots/RESOURCE_LOG/INCOMPLETE remain immutable.
Original preflight failed perfect-input no-op at F3.2007e-7,J8.8818e-16, before
real coordinates or new evaluator poses. Same-fixture diagnosis isolated F's
E' rigid_inverse(E) E endpoint recomposition, amplifying SO3roundoff repeatedly.
Separate implementation-only attempt-02 assigns the endpoint directly to E',
with identical mathematics/criteria/gates. Distinct helper and67entryfreeze;
original failure/diagnosis disclosed in AMENDMENT_01. No threshold change.

Same complete preflight now passes:explicit-vs-compact H/g1.4211e-14/7.7161e-15,
F/JgradientFD6.5609e-9/8.7622e-9, separate-chain gauge3.5527e-15, common gauge
1.9540e-14, no-gap exact, no-op1.1102e-14,recovery1.5099e-14, planar blind rank3.
CompleteO/B/F/Jbank seals before any new numeric pose-reference outcome.
Independent16raw preprocessing maxdelta1.4211e-14,selected moments exact,
explicit geometry5.6342e-13,cost1.5721e-13,selected realFD4.4815e-9. Proper poses,
hash/membership/mass/support,fixed internal shape,traces/corrections checked.
Independent camera->LiDAR/reference/HornATE/error reconstruction maxdelta
6.99995617e-14;all3conjunctions reproduced.
Bounded discovery verification,not full optimizer replay/rejected-patch census.

## Resources, interpretation and next hypothesis

All9original/failure/diagnostic/retry/validation stages counted once:
**9.447805s**,peakRSS **91922432bytes**,noGPU. New1800s/RSS2GiB/dossier512MiB caps
pass, including the original preflight failure. Imports/WSLstartup,design/docs/
delivery bookkeeping excluded; not production runtime. See RESOURCE_AUDIT.json.

We now have a concrete partial signal to develop:the shared map can improve
translation/position shape on an actual revisit. Its free rotational refinement
trades away some of the native RAP angle accuracy. Internal BA adds only marginal
gain in this case. A testable next restriction is to preserve RAP rotation and
both internal O shapes while refining map translation on a fixed00/05/06development
cohort. This reduced-variable hypothesis is proposed post-outcome, not executed
or admitted by a passing CV1gate; it might lose the observed translation gain.
See NEXT_ROUND_PLAN.md. No extra arm,cohort,full trajectory or production follows.

Physical patch identity/dynamics,initialization/membership bias,prior balance,
missing scan times/covariance/cross-correlations,calibration/reference conflict,
09discrepancy and checkpoint/site exposure remain unresolved. Conventional
[BALM](https://arxiv.org/abs/2209.08854) prior art is credited; owner originality
relaxation permits this engineering route without a new mechanism claim.

Both original HEADs/branches/2and9tracked dirty sets preserved. PriorSMP2
37,SMP142,MMR035delivery identities unchanged,
8model/config hashes and opaque checkpoint exact,not deserialized. New isolated
RAP-SLAM helpers/main maintenance/docs and mutable handoffs only;no GPU/modelload/
training/RAPinference/officialGTmetric replacement/acquisition/install/production/
default/backbone/manuscriptedit/commit/Gitsync.
