# Fixed identity and local temporal geometry audit

All98 unique endpoints from the validated71 online attempts, all six exposed
E0 A sequences. Previous/next10 absolute frames where in range; preserve
directed endpoint->support rows even if clouds/pairs are reused. Future controls
are noncausal diagnostics. No RAP/Geo inference, ICP, pose fitting, offset,
calibration or point-budget search. This is evaluator-only label/data diagnosis.

Freeze protocol,runner,independent validator,source loader/manifest/trajectory,
all raw required scans,times/calibration/GT identities(hash only),prior input/
geometry bank seals/validation before new construction. Check absolute filename
and GT/time row indexing, full sequences'0..N-1, timestamp equality against saved
E0 manifests and monotonicity. Record missing raw OXTS/sensor trigger/archive
provenance honestly. Local filesystem identity does not authenticate sensor sync.

GT-free input bank: exact corrected raw scans range>=1.5,no max,+0.205degrees,
Open3D0.19 voxel0.4,outlier20/2.5,fresh seed42 cap4000. Compare all98 endpoint
arrays byte-exact to prior validated input; independently regenerate every new
support array. Seal all clouds/row census before actual GT numerical evaluation.

Evaluator builds GT LiDAR poses Tr^-1 camera_pose Tr and saved odom relative
poses for every directed local control. NN threshold1m symmetric mean/overlap
and GT-vs-odom translation/rotation. Save directed distance vectors. Also
decompose GT-minus-RAP translation XYZ on all71 already-sealed cross-visit
poses; no new pose output. Frame axes are i's LiDAR axes, not world vertical.

Predeclare09 local-consistency gate across every09 local row: median absolute
GT-minus-odom symmetric mean distance<=0.10m,median absolute overlap difference
<=0.05,median GT-vs-odom translation<=0.20m and rotation<=1degree. This narrows
global versus local discrepancy; does not prove GT drift or exclude aliases.
Report every sequence and all failures. No threshold changes after outputs.
Cross09 z dominance descriptive flag: median |z error|/translation_norm>=0.8;
do not change official GT or reject/relax official strict labels.

Independent validator: all arrays via independent raw correction pipeline,
full manifest IDs/files/timestamps and calibration math, all GT/odom relative
poses, every directed NN distance via brute-force cdist,all metrics/aggregates/
gates and original bank identities. Cap900s construction+eval+validation,
RSS<2GiB,artifacts<100MB. Separate stages/seals and independent validation
required. Scope remains bounded if sensor/archive evidence missing; mark that
limit instead of indefinitely blocking a prospective RAP mechanism proposal.
No training,production/default edit,manuscript or Git sync. Earlier stops persist.
