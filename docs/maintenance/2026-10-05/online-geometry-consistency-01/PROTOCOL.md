# Fixed all-online pose/scan geometric consistency diagnostic

Motivation is the validated comparator's shared09 translation discrepancy, not
an unseen hypothesis. Observed-development diagnostic; all71 pairs, no selected
favorable subset. No new inference, ICP, fitting, parameter search or gate.

Freeze code/independent validator and validated online input/prediction seals,
outcomes/validation,all71 clouds,all predicted/saved poses and GT/calibration/
odom source identities before NEW geometry results. Existing labels are exposed.
Evaluator-only actual GT allowed here; never alter any existing GT-free bank.

For every exact4000-per-scan pair compute symmetric NN overlap(distance<1m),
mean distance, pooled median/p95 under RAP,GeoTransformer,GT relative pose,
unoptimized odometry relative pose. Save complete directed distance vectors.
Compute RAP-vs-Geo relative translation and rotation disagreement. Same
corrected scans, same exact input points; no method tuning or pose refinement.

Descriptive predeclared09 shared geometry/label discrepancy screen: median
GT-minus-RAP mean distance>=0.5m AND median RAP-minus-GT overlap>=0.10 AND
median RAP-vs-Geo translation<=0.5m AND rotation<=2degrees across ALL12 attempts.
Report all six sequences and current58 accepted subset descriptively; do not
revise the09 gate. This can flag incompatible geometry/pose labels, ambiguity,
or preprocessing/timing; it cannot prove GT wrong or either matcher correct.
Never replace official metric GT or erase strict failure labels.

Independent validator reconstructs all calibration-relative poses, compares
all directed NN distances using brute-force SciPy cdist (not KDTree), recomputes
every statistic/disagreement/aggregate/gate and source/seal integrity. Cap300s,
RSS<2GiB,artifacts<100MB. No graph or metric efficacy claim, no training/default/
production/manuscript/Git changes. This diagnostic informs the next distinct
research question; its signal is not an original algorithm contribution.
