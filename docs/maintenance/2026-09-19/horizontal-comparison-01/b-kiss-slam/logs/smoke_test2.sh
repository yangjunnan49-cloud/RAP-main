#!/bin/bash
# Install open3d runtime system libraries, then rerun the 100-scan smoke test.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
VENV=/root/venvs/kiss-slam-hc1/bin
DATA=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset

apt-get install -y -qq libusb-1.0-0 libgl1 libglib2.0-0 libgomp1 2>&1 | tail -1

cd "$HC/smoke/kitti00"
"$VENV/kiss_slam_pipeline" "$DATA" --dataloader kitti --sequence 00 --n-scans 100 2>&1 | tail -20
echo "=== output tree ==="
find "$HC/smoke/kitti00" -type f | sort | head -40
