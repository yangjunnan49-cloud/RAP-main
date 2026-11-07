# Required next adapter/split annex

This is a readiness checklist, not a scored protocol or a claim of sample
adequacy. Do not silently replace PG-V1's failed09 confirmation with Boreas.

1. Bind the exact downloaded official reference/source hashes. Decode Velodyne
   files as six float32 fields, preserving point-time offsets; keep pose matrices
   and relative-pose calculations float64. Filename timestamps and CSV integers
   must match exactly. Do not infer timestamp units from the GPSTime header alone.
2. Verify the official orientation convention independently, including a
   nontrivial yaw/pitch/roll case, inverse/compose checks and a small real
   GT-aligned scan check. The supplied lidar_poses.csv describes LiDAR poses;
   do not apply T_applanix_lidar a second time. Preserve calibration identities.
3. Keep GNSS/IMU/pose/velocity information evaluator-only. Causal support transport
   must come from LiDAR-only motion, with an explicit initial-window policy.
   Point-time handling and any deskew must be frozen for both arms; never use
   GT motion to silently improve context inputs. Acquisition distortion is an
   engineering check, not a reason to search scores on confirmation outcomes.
4. Freeze one cross-session candidate protocol with qualified session/timestamp
   identities, non-GT retrieval, physical-query caps, support disjointness and
   exact four-stratum definitions. Across-session and within-session temporal
   separation require an explicit amendment, not a reused KITTI index assumption.
5. Use KITTI00 only as observed development discovery. The two Boreas sessions
   may supply a single cross-session confirmation role if adequacy is measured.
   They are correlated traversals of a shared route, not independent sites.
   No exclusion from RAP pretraining is claimed. NCLT remains reserved externally.
6. First estimate raw acquisition volume from remote object sizes and a fixed
   time-based acquisition plan; audit a bounded local-motion/format window before
   bulk download. Freeze maximum bytes/time, retries and resumable checksums.
   Downloaded2 scans are format probes and cannot establish four-stratum minima.
7. Once geometry/data eligibility passes, freeze exact membership and all sources
   before model outcomes. Retain PG-V1's same-data generation-versus-verification
   contrast, common anchor gate and fixed call/point budget. Keep a separately
   declared cost envelope if the new sensor requires different preprocessing.

No bulk acquisition, adapter implementation, new cohort or registration bank is
claimed complete by this file. Public download authorization already exists;
routine execution within a frozen bounded annex does not need another resource
permission discussion. Stop on an actual data/geometry/cap failure and record it.
