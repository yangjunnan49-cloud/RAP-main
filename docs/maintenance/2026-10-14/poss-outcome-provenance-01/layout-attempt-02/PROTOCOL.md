# POP0 Separate Trajectory Layout Correction

Original freeze and census attempts remain immutable. Census stopped at the
first trajectory-structure assertion: both stored files have 2751 rows of 12
columns, not 8-column TUM. It did not interpret coordinates, match downstream
errors, fit, or calculate new metrics. Original failure/INCOMPLETE remain.

Derive exact AST variants from the frozen original driver and validator:
replace only integer 8 layout literals with 12 (two driver occurrences, one
validator occurrence), and each single dossier route with this subdirectory.
No other AST change, input/cohort/metric/rule/threshold change is permitted.
Bind the current save_kitti_poses and run_pipeline sources as corroborating
format evidence, without executing them or assuming historical source identity.

The complete original plus correction attempts share the original 600s,
512MiB RSS, zero GPU and 16MiB whole parent dossier caps. An independent
validator rechecks each 12-column row and all original outcome membership
assertions. No original stage is rerun or overwritten. This is a structural
parser correction, not an efficacy protocol or failed scientific-gate rescue.
