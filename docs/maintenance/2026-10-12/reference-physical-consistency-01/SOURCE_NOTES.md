# Source boundary and primary documentation

The earlier temporal-identity audit's190 local controls and complete manifests narrowed gross association/calibration-convention problems, but did not provide independent OXTS/trigger archives. RPC0 adds tight adjacent revisit combinations and return-ID partitions; it is not independent sensing or a new reference.

KITTI's [official odometry description](https://www.cvlibs.net/datasets/kitti/eval_odometry.php) describes the benchmark/reference split and explains why short-segment GPS/OXTS sensitivity led to its longer-segment evaluator. That general warning does not prove a fault in these exact00/09 pairs; official labels/scoring remain.

The provider's [raw-data page](https://www.cvlibs.net/datasets/kitti/raw_data.php) distinguishes unsynchronized/raw from synchronized/rectified streams, and lists per-stream timestamps, GPS/IMU, calibration and tracklet metadata. Their availability on the provider site does not establish that our local odometry extraction contains them, nor authenticate this extraction. No archives are acquired here.

The officially linked [author PyKITTI odometry loader](https://raw.githubusercontent.com/utiasSTARS/pykitti/master/pykitti/odometry.py) reads Tr as LiDAR-to-rectified-camera0, pose rows as world-from-camera0 and times as frame timestamps. This independently corroborates the intended transformation convention. It does not certify physical time alignment or pose accuracy. Sensor10Hz details in the [official setup](https://www.cvlibs.net/datasets/kitti/setup.php) are general setup documentation, not per-point timing evidence for these files.

Observed local production source uses XYZI only, odometry deskew=false and zero point timestamps for that path. An azimuth timestamp helper exists for a different deskew=true path; it is synthetic, unused here, and no validation of actual scan timing follows. Upstream motion compensation of our local file bytes is not independently established from the current directory metadata.
