# RPC0 — reference and physical consistency diagnosis

Status: VALIDATED_BOUNDED_REFERENCE_PHYSICAL_DIAGNOSIS_COMPLETE_WITH_VALIDATOR_REPAIR.
Decision: AVAILABLE_BINDINGS_VALID_BROAD_09_CONFLICT_PHYSICAL_CAUSE_UNRESOLVED.

The fixed00/09 source/frame/time/calibration bindings and independent coordinate equations pass.09 retains a broad cross-visit reference-versus-observation conflict across every immediate-neighbour combination and every eligible source-return partition. Tight adjacent reference/odom motions agree, and the fixed intrinsic-correction representation does not remove the conflict. These results do not identify physical truth, prove the reference wrong, establish a unique synchronization/calibration/drift/dynamics cause, or demonstrate a metric improvement. Official reference, all admitted edges and all benchmark metrics remain.

## New evidence and its scope

Owner said "请执行下一步", then "请继续". OWNER_SCOPE and PROTOCOL authorize only this distinct bounded diagnostic. Earlier temporal-identity-audit-01 already checked190 longer local controls/full manifests; RPC0 adds source-return census, immediate Cartesian revisit combinations, representation/NN bounds and explicit coordinate-axis interpretation. It does not repeat the earlier temporal audit as independent sensing.

1910 original/input/source identities froze before numerical stages, including MGR0's1567 source/input identities, all344 deliveries and delivery seal. All old models/checkpoints are hashed only; no model deserialization. Fixed cases are original admitted index0:00(2429,3373),09(0,1574). Eleven raw XYZI scans contain1,380,000 original returns; all nonfinite/range/cap labels are retained.45056 selected returns use4096 deterministic source IDs per scan, without voxel/outlier/dynamic/normal filtering. RAW and float64+.205deg CORRECTED use identical IDs. Sixteen sensor azimuth/range/z partitions are fixed from RAW coordinates. They are not semantic ground/dynamic labels or independently authenticated common surfaces.

The complete13-file corpus sealed before new reference coordinate arithmetic. Reference/odom row counts at corpus construction were checked as text only. Fifteen revisit pairs(900,609) and seven immediate same-visit controls(400,309) include every available +/-1 endpoint;09 endpoint0's unavailable -1 is retained as one boundary exclusion. Future-neighbour tests are offline, noncausal diagnostics. Existing MGR0 N/RI/W/J/K poses are transferred with original KISS local motion, and reference direct/transport arms are fixed controls. No pose is fitted, selected or promoted.

## Cross-visit observations

The distance is symmetric nearest-point distance over all4096 retained returns in each direction. The table reports medians over the predefined pairs. G-minus-W gap is the median of paired differences, not the difference of marginal medians. W is the original fixed geometry bundle, with no new solver call.

| Sequence / representation | Pairs | Median G-minus-W distance (m) | Pairs gap>=.5m | Eligible strata gap>=.5m | Median G overlap<1m | Median W overlap<1m |
|---|---:|---:|---:|---:|---:|---:|
|00 RAW|9|0.149803628|0/9|0/183|94.0308%|94.3848%|
|00 CORRECTED|9|0.149845836|0/9|0/183|94.0186%|94.4092%|
|09 RAW|6|2.464157098|6/6|144/144|0.4272%|87.4451%|
|09 CORRECTED|6|2.462758691|6/6|144/144|0.4211%|87.4573%|

For09 RAW, all six G symmetric means are2.95582--3.00670m versus W0.48581--0.53626m. At the original09(0,1574), G/W RAW means2.964944510/.516652492m; CORRECTED2.963693308/.516942186m. G_transport preserves the large discrepancy(roughly2.93974--3.01585m RAW), so the direct versus KISS local transport distinction does not remove it in this fixed census.

The144 eligible partition records are repeated pair/direction strata over five source scans, not144 statistically independent scenes/replicates. All16 strata, including low-support/empty records, remain in results.json. Broad support conflict makes a single selected return patch an insufficient explanation within this sample; repeated surfaces, dynamics and upstream data/reference limitations remain possible. W's lower distance alone cannot certify the correct correspondence or physical pose.

Maximum observed intrinsic point displacement is.285322694m. Every directed NN change obeys the analytical source-displacement plus maximum-target-displacement bound, with the original rotation operator norm; the conservative selected-support bound is below.571m. The09 median contrast changes by only.001398408m between the two representations. This fixed intrinsic representation change does not explain away the observed2.46m contrast; it does not exclude other calibration or timing effects.

## Immediate motion and coordinate axes

| Sequence | Immediate controls | Median reference/odom translation disagreement | Median R disagreement |
|---|---:|---:|---:|
|00|4|0.017664765m|0.061745796deg|
|09|3|0.026015501m|0.102169634deg|

All immediate offsets are roughly.104s.09 absolute per-control translation disagreements are.01575--.05495m. Reference and odom give nearly equal local NN means(.389--.424m RAW09). These are local numerical/observational agreement, not independent timestamp provenance or a proof of correct scan motion compensation. Pose-implied80m-support one-frame envelopes are approximately1.062--1.261m for reference09; they are inter-frame pose bounds, not actual within-scan motion or uncertainty estimates. Existing deskew=false/zero point-time production path remains unchanged; upstream motion compensation of local bytes is not established.

At09's original anchor, unchanged G-minus-N translation norm3.724938295m has endpoint-i LiDAR components[-.556973826,2.043355467,-3.064252584]m. LiDAR0-world is almost the same because i=0; camera0-world is[-2.017614666,3.084151797,-.540744515]m. Absolute LiDAR0 z component/norm is82.2632%, but this coordinate axis is not independently certified gravity. At00 norm.786380759m, endpoint-i vector[.537085841,-.558688027,-.133421087]m becomes LiDAR0-world[.712788894,.301433320,-.139515634]m. These are interpretations of existing fixed pose errors, not new system metrics or a vertical-drift diagnosis.

Full available00/09 IDs/absolute scan paths/timestamps/row counts agree with original manifests; times are strictly increasing. Relative conjugation and absolute roundtrip independently agree within1.13687e-13; local/transport matrices within7.26364e-14. Original calibration/reference rotations have rounded orthogonality defects around8.08e-8--2.22e-7, retained without replacing poses or physical geometry. Algebraic direction checks do not authenticate the supplied calibration.

## Missing independent evidence

Scoped inventories of the exact00/09 sequence directories contain calib.txt/times.txt/velodyne. All22 predeclared OXTS/per-stream scan start/end timestamp/raw calibration/tracklet/label/receipt paths are absent there. XYZI exposes no measured per-return acquisition times under the existing schema. This is not a whole-computer inventory or a statement that provider archives do not exist. No dataset is downloaded and no provenance is invented.

The [official KITTI raw-data description](https://www.cvlibs.net/datasets/kitti/raw_data.php) describes raw versus synchronized/rectified streams and timestamp/GPS/IMU/calibration metadata. The [officially linked author odometry loader](https://raw.githubusercontent.com/utiasSTARS/pykitti/master/pykitti/odometry.py) supports the intended Tr/pose/time convention. Those sources describe formats; they do not validate our local extraction or these exact physical poses. The [official odometry evaluation page](https://www.cvlibs.net/datasets/kitti/eval_odometry.php) discusses short-segment reference sensitivity generally, without establishing a fault in these cases. SOURCE_NOTES preserves the documentation boundary.

An authenticated raw-drive/odometry mapping, archive identities, original OXTS/scan start-end records and verified calibration/rectification/motion-compensation lineage would provide new evidence. Another local point-count/radius/offset/patch sweep would not. Dynamics and true surface identity also remain unverified.

## Independent validation and retained repair

Eight synthetic coordinate/direction/gauge-transfer/Rodrigues fixtures independently pass. Final validator rebuilds all11 raw-ID selections/reason codes/correction/strata, full sequence bindings, all transforms, axes and every distance/statistic/classification without importing runner construction/statistics helpers. Brute-force chunked cdist checks deterministic nearest IDs and1,949,696 logical directed-distance records;1,703,936 unique records are recomputed, with30 explicit equal-transform aliases. Nearest distances differ<=3.55271e-15, stratum/statistic values<=8.88178e-16, transforms<=7.26364e-14, axis vectors<=6.43930e-15. No independent physical provenance or pose optimizer replay is claimed.

The first full validator failed at a local envelope difference1.594708720631388e-8m versus unchanged1e-8m tolerance. SciPy1.15.2 [tagged source](https://raw.githubusercontent.com/scipy/scipy/v1.15.2/scipy/spatial/transform/_rotation.pyx) orthogonalizes rounded rotation matrices before scalar angle extraction; the independent implementation had omitted that contract. Original failed source/freeze/output/receipts remain. AMENDMENT_01 and a13-entry separate amendment freeze bind an independent polar-eigendecomposition scalar-angle repair, with an extra14-matrix prerequisite and full validation attempt02. The original corpus/poses/results/criteria are unchanged; no raw census or fixed-pose evaluation is rerun. Final local-envelope max2.84217e-14m. Angle-only projection is explicit and never replaces the original reference/geometry matrices.

One amendment launch was not executed because automatic approval review was unavailable due to usage limits. User then said "请继续"; the identical scoped escalation succeeded normally after fresh host guard. No approval bypass, process/configuration change or missing child is inferred from that nonexecution. See EXECUTION_NOTE.

Nine supervised child attempts(eight success, one retained validation failure) have complete peak/time and Windows exit receipts. Combined payload108.281916375s, full process RSS120557568bytes, GPU0,900s/2GiB/256MiB new-dossier bounds pass. Imports/WSL startup/design/final bookkeeping are outside payload timing; full ru_maxrss includes process imports. Windows process wall126.8121495s is separate. Ordinary syntax/tool setup lacks a complete RSS ledger and is not claimed under an all-setup budget. Earlier MGR0/NOC supervision/resource gaps remain; this offline diagnostic is not production latency. RESOURCE_AUDIT/CHECKS/FINAL_IDENTITY_CHECK/DELIVERY_SEAL close only the new RPC0 marker.

## Consequence

Stop the exact local geometry/reference rescue family: no normal/radius/point-count/offset/calibration/selector/gate tuning, no09 deletion or corrected reference, and no repeated local diagnosis without genuinely new physical evidence. The diagnostic strengthens the evidence for a broad unresolved09 conflict, not for a new RAP mechanism or gain.

NEXT_ROUND_PLAN recommends a distinct causal observation-context/submap feasibility design, with original frontend/graph/reference/admitted edges and equal support/work controls retained. Generic submap geometry is prior art; later frozen-RAP residual/context contribution must be measured beyond strong geometry and equal-capacity controls. These remain DESIGN_ONLY, with no new protocol freeze, runner, model extraction, solver or trajectory execution. NOC4 remains INCOMPLETE and requires P backward reproducibility before native updates. Both original HEADs/branches/two-nine tracked dirty sets/all historical stops/seals/unknowns are preserved. No production/default/backbone/manuscript/reference/install/process restart/commit/Git sync.
