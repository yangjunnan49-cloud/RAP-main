# Fixed external odometry adapter

`fixed_odometry.py` is an exact AST extraction of the original frozen LMB FixedOdometry class. The only new module-level dependency statement is `import numpy as np`. It requires the existing Linux KISS-SLAM environment documented in the anchor component package; no package is installed or modified.

Instantiate `FixedOdometry(config.kiss_icp_config(), odometry_poses)` and assign it to the isolated KissSLAM object's `odometry` field before feeding frames. The poses are complete Nx4x4 source-frame odometry in exactly the scan order. `register_frame` uses the existing preprocessor/voxelizer/map, returns inv(O_anchor)*O_frame, and never calls the native odometry aligner. The native local-map pipeline resets `last_pose=I`; the adapter then binds the anchor to that current source frame. Record all reset IDs and direct map-frame memberships in any downstream integration.

The original14-frame known-odometry native pipeline was rerun using the imported standalone class, with loops disabled. Complete poses and relative expressions agree, expected resets3/6/9/12/13 match, odometry alignment calls0. This verifies import/state/API portability; no real scans, GT metric, new candidate or accuracy comparison. Full real validation remains the original sealed six-sequence experiment. No further graph/parameter choice is admitted by this component.

All execution is charged to the original cumulative LMB1800s/4GiB/128MiB-combined/GPU0 scope. Original12GiB host guard and all historical stops remain. A standalone module is not permission to replay an old stopped trial or bypass the launcher. Installed and production/default files remain unchanged.
