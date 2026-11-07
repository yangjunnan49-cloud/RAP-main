#!/bin/bash
# Dump the unmodified KISS-SLAM default config and run a 100-scan smoke test on
# KITTI 00 to verify the end-to-end path and output layout before full runs.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
VENV=/root/venvs/kiss-slam-hc1/bin
DATA=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset

cd "$HC/config"
rm -f kiss_slam.yaml default_config.yaml
"$VENV/kiss_slam_dump_config"
mv kiss_slam.yaml default_config.yaml
echo "=== default_config.yaml sha256 ==="
sha256sum default_config.yaml

echo "=== smoke test: kitti 00, first 100 scans ==="
mkdir -p "$HC/smoke/kitti00" && cd "$HC/smoke/kitti00"
"$VENV/kiss_slam_pipeline" "$DATA" --dataloader kitti --sequence 00 --n-scans 100 2>&1 | tail -25
echo "=== output tree ==="
find "$HC/smoke/kitti00" -type f | sort
