# NJE0 prospective G/P/J/W engineering comparison

Population is exactly NJC0's four maximal eligible components, in order05,00,07,09
(smallest technical group first, then sequence order). All29 view IDs and32
original loop measurements remain fixed. No adjacent/extra scans, changed groups,
seed/point-count/radius/anchor search, original-demo substitution or exclusions.
The other26 accepted measurements and13 unaccepted attempts remain outside this
component comparison, retained in all58/71 complete-system denominators.

Input is each exact frozen4000-point float32 cache. Verify finiteness, unique
coordinates and at least1000points; select1000 sorted row indices without
replacement using NumPy default_rng seed from SHA256('NJE0|seq|frame|rows')'s
first4bytes big-endian. Shared per-view standard Gaussian float32 noise uses the
same seed rule with suffix noise. No input re-preprocessing/coordinate transform.
All methods have access to the same29 parent clouds. MiniSpinNet uses4000 support
points,1000 selected keypoints, original512-point patch/des_r5/z-aligned encoder,
strict reviewed weights_only state loading, no zero-feature exception fallback.
Descriptors are computed once/view and reused identically for P and J.

The first ascending-ID view defines common scale1.5*maxabs(centered keypoints).
Each view is centered by its own keypoint mean and divided by that common scale.
This is algebraically the backend's _normalize_parts when all counts equal1000;
validate numerically before inference. P inherits the component's scale/center,
not pair-specific rescaling. J marks the first component view as anchor; each P
call marks its first ascending pair view. Anchor-flag changes are part of this
method comparison and prevent a pure attention-causality interpretation. Noise
rows, descriptors and coordinates are byte-identical per view across calls.

P: one independent native two-view RAP generation on each of32 original edges.
J: one native joint generation per group (3/9/10/7parts). Strict exact12-layer
checkpoint, eval, frozen no-grad, FP16 SDPA neural path, IEEE float32 rigid fits,
5Euler steps/rigidity forcing/n_generations1; no seeds chosen by outcomes. Retain
final normalized clouds, native fitted parts and independently fitted CPU parts.
Per-part original-sensor->joint transform is R,scale*t-R*center; relative i<-j
is inverse(part_i)*part_j. Independent quaternion Horn and SVD fits must agree
within1e-4 normalized units; native float32 fits within1e-3. Check SE3 validity.
No cycle residual from J is treated as accuracy/confidence.

G: strong unposed all-view geometry. Compute normals using KNN20 on each parent
4000-point cloud, orient towards its sensor origin. FPFH radius2/max_nn100 on the
parent, then select identical1000 keypoints/normals/descriptors. Every complete
pair in each component is registered (105 total). Two fixed GICP starts, identity
and FPFH-FGR. FGR seed20261015/division1.4/absolute scale/decrease_mu/2.5m/64iter/
tuple.95/max1000. GICP point covariance I-.999nnT,eps.001,L2,2.5m,max80iter,
relativefitness/rmse1e-6. Pick lower symmetric censored squared NN cost (clip2.5m),
ties prefer earlier start. No GT or RAP initialization.

W: practical stronger geometry on all4000points with identical parameters and
all105pairs, additionally initialized with each original frontend odometry
relative pose. W therefore receives additional previously available trajectory
information; it is not a pure unposed control. Choose among identity/FGR/odometry
by the same target-free cost. Report this information/work advantage explicitly.

For each G/W pair retain both-direction2.5m overlap. Include synchronization edges
only when min overlap>=.30. Maximum-support spanning forest initializes an
ordinary GTSAM robust pose graph, with first node of each connected component
fixed by1e-6prior, common sigmas[.1rad x3,.5m x3],Huber1.345,LM100iterations.
No independence/calibrated covariance claim from correlated all-pair factors.
Gd/Wd direct and Gs/Ws synchronized outputs are separate strong controls; if an
original endpoint pair lies across disconnected support components use its
direct result and explicitly count fallback. Ps applies the identical ordinary
graph to P's32 edges, all retained, and is also a required control. These are
ordinary baseline solvers, not a new SGC0 covariance allocation experiment.

Numerical fixed SE3/Horn/pose-composition/normalization controls precede real
inference. Freeze source/protocol, original inputs, reference file byte identities
(without numerically reading them), weights/config and repository state first.
Seal every G/P/J/W predicted transform and work/input record for all4groups
before any numerical reference read. No partial/favourable-group metric result.

Only after complete prediction seal: existing KITTI camera poses are conjugated
by original calib Tr (Tr^-1*pose*Tr). Compare i<-j with reference inv(Pi)*Pj.
Sequence09 remains present with unresolved physical/reference interpretation.
Report all32 per-edge RTE meters/RRE degrees, each group mean and aggregate;
include original odometry control. No ATE/system gain inferred from loop RTE.
Engineering admission requires J mean RTE<=.95*each of P/Ps/Gd/Gs/Wd/Ws,
each group's J RTE<=best control+.005m, and aggregate J RRE<=each control+.05deg.
This is a new prospective screen, never an amendment of historical gates. A
failure retires this exact frozen construction; no seed/point-count/group/
anchor/step/normalization rescue. A pass only supports a subsequent separately
designed system test; it does not prove novelty/generalization/physical truth.

Account complete work: preparation, encoder29calls, P32/J4generations (5forward
calls each), both full geometry controls/525GICPstarts/210FGRstarts/graph solves,
imports, failed attempts and validation. P and J share raw union/descriptor/noise
but have different multiplicity and attention work: sum global N^2 per native
step is P128,000,000 vs J239,000,000. No equal-work or latency benefit claim
without actual total costs; common input is not equal compute. Retain host/GPU
peaks and times, input/descriptor hashes and per-call row counts.

New scope caps, including every attempted enclosing child/import/failure:
2400s cumulative wall,6GiB Linux processRSS,8GiB allocated AND reserved CUDA,
256MiB complete dossier, Windows prelaunch commit headroom>=12GiB. Ordinary
setup/observer lifetime UNKNOWN, no all-native process-tree guarantee. GPU must
have>=9GiB free immediately before loading; otherwise retain a waiting receipt
and do independent CPU work. Never kill unrelated work. No automatic restart,
scope reset, cap expansion or partial numerical rerun after technical failure.
Exclusive writes; retain source/receipts/initial pending marker. No network,
install, external messages, production/default/reference/manuscript/Git changes.
