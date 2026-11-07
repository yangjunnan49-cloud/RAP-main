# KC0 existing official devkit contract review

The original locally retained KITTI odometry devkit ZIP still matches its M2 SHA256. Its readme bytes exactly match the named ZIP member. This is existing primary-source review, with no network, image, point or numerical pose read.

The provider document identifies rectified grayscale image_0/image_1; Pi and Tr define LiDAR-to-rectified-camera projection. It states that the benchmark LiDAR exports are ego-motion-compensated for static-scene correspondence at camera triggers, with dynamic residual distortion. It describes camera-frame poses and synchronized image-pair timestamps. Its intended odometry-to-raw mapping places00 at drive2011_10_03_drive_0027/start0 and08 at2011_09_30_drive_0028/start1100.

These are provider statements and an intended association. They do not authenticate our local scan acquisition/extraction or any camera bytes, establish a calibrated independent uncertainty bound, or resolve09. The readme's approximate pose-accuracy claim is not a per-case variance model. Do not add synthetic point times/deskew or infer that E0's intrinsic correction duplicates the stated motion compensation.

This supplies a concrete projection/source contract for a possible appearance task. Images and image dimensions remain unavailable. A positive-camera-depth calculation can only bound potential support; it cannot prove actual image visibility or useful feature correspondence. No numerical camera test or efficacy runner is executed here.

The conservative600s source-review account begins06:28:53UTC, before the first read. CLOSE_CHECKS records its inclusive closing time. Setup/observer peaks are unknown; no all-process resource claim. Old source/family/default/reference/trust/install/Git/outreach/scheduler/goal-status limits remain.