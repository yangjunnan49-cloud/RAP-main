#!/bin/bash
# Install pillow (missing upstream dependency of kiss_slam.occupancy_mapper),
# refresh pip freeze, rerun the 100-scan smoke test.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
VENV=/root/venvs/kiss-slam-hc1/bin
DATA=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset

"$VENV/pip" install --quiet pillow
"$VENV/pip" freeze > "$HC/env/pip_freeze.txt"
echo "pillow installed; freeze updated ($(wc -l < "$HC/env/pip_freeze.txt") lines)"

cd "$HC/smoke/kitti00"
"$VENV/kiss_slam_pipeline" "$DATA" --dataloader kitti --sequence 00 --n-scans 100 2>&1 | tail -20
echo "=== output tree ==="
find "$HC/smoke/kitti00" -type f | sort | head -40
