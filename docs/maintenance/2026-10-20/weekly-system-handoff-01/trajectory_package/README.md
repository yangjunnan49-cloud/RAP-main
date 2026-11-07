# Experimental fixed-E0 system trajectories — October20

All six exposed development sequences, complete source-frame order. B is the existing E0/RAP graph. G is the isolated corrected-anchor native local-map bundle, using exactly the same fixed E0 odometry. G is a single global mode, not a GT-selected mixture. Every file contains one unaligned rigid pose per source frame, the top3x4 matrix as12 row-major numbers. Source IDs/timestamps are in each directory. LiDAR files are LiDAR world poses; camera files are Tr @ T_lidar @ inv(Tr), with the original KITTI calibration. No GT alignment or reference coordinate file is included.

New six-sequence mean target passes: G ATE0.648336m versus archived complete KISS-SLAM0.699689m, G ter0.446952% versus0.478614%. Additional individual protection fails07 ter and10 rer;06/10 ATE is >5% worse than KISS. G is delivered experimentally; production/default B is unchanged. Original strict00/05 tests remain FAILED. METRICS includes every sequence and gate, not only averages.

These trajectories reuse cached E0. They do not supply a new full raw-system runtime benchmark, RAP-specific gain, independent scenes, physical-reference authentication or training-exclusion evidence. The latest complete raw-system benchmark remainsOctober11. 09 is retained. Use poses for independent inspection with those limits. No original data, prediction or installed package was modified.

SOURCE_BINDINGS and FILE_SHA256 bind the source identities and exported bytes; EXPORT_CHECKS in the parent dossier records full serialization/inverse-coordinate roundtrip. The ZIP and directory contain the same files. This is a local artifact, not a published release.
