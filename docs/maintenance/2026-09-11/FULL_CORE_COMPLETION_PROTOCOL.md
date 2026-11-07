# Core rerun completion and audit closure protocol

Declared before the remaining full runs, following the owner's explicit request
to finish necessary reruns and move promptly into system optimization.

Retain FULL_FRONTEND_PROTOCOL.md parameters and timing definitions. Complete:
POSS sequence 00 frames 3850-5268 (1419 frames, GT already LiDAR), KITTI 05
frames 0-2760 (2761), KITTI 00 frames 0-4540 (4541), all stride 1. KITTI uses
camera-to-LiDAR GT calibration; no KITTI205 correction, deskew or fallback.
Use merged candidate budget 12 uniformly, including KITTI 00 (historical 40 is
a different protocol). Reuse the already completed full KITTI 06 result.
Run sequentially to avoid GPU and memory contention. No parameter tuning.

Bounded acceptance: complete source frames, finite trajectories, valid rotations,
complete verification events and exact selected measurement/edge association,
corrected LiDAR APE and separate camera KITTI drift, source/input stability.
Do not rerun the already passed synthetic checks or KITTI 06 without a new failure.
Compare old/new metrics from the existing M2 correction table and fresh replay;
retain historic live/Spires and map tables as legacy, not fresh paper evidence.
Do not start full ROS/live/Spires reruns for a thesis core that does not use them.

Deliver one optimization baseline registry/table with all four fresh runs, fixed
protocol, code/input hashes and metric definitions. Existing independent backup,
training provenance, optional statistical guarantees and ROS/Spires work remain
explicitly deferred. They do not block optimization on this development cohort.
Maintenance M0-M5 is not declared universally complete; core rerun acceptance
closes the audit-only phase for the scoped offline thesis system.
