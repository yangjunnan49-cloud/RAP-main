# Explicit original-float32 KITTI correction component

Run `python -B validate_fixture.py` in an existing NumPy environment. No installation or data acquisition occurs. `legacy_f32_correction` accepts only Nx3 float32 points, reproducing the original E0 source correction's observed NumPy1.26 intermediate float32 arithmetic. Same0.205degree and near-vertical rule. The fixture contains10003 synthetic points and the actual original-runtime prepared output; full output bytes must match, including signed zero.

Validated on the two documented existing NumPy1.26.4/2.2.6 runtimes. The real certificate covers12296 original frames/1514179545 point occurrences/4542538635 XYZ components, matching every prepared count/hash in source order. Real raw/reference files are not distributed in this package. SHA equality establishes input byte correspondence, not physical sensor/reference authenticity, per-beam timing or training exclusion.

Apply this only to the original E0 frontend role. The old G map branch and native K reader retain their separate original numerical semantics. The frozen physical parameters do not change. This is a source compatibility component, not a new SLAM method or accuracy result. Existing KISS native ABI/backend behavior must still pass its original source-pose correspondence test. The original failed R0 run and individual G protections remain.

`reference_function.py` is the original source snapshot for reading, not a replacement for this explicit function under NumPy2. `observed_runtime` records the measured intermediate dtype difference. Future NumPy/platform versions need their own contract check; no universal floating-point equivalence is claimed.
