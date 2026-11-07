#!/bin/bash
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== _calibrate_poses in kiss_icp/pipeline.py ==="
grep -n -B2 -A10 "_calibrate_poses\|def calibration" "$SP/kiss_icp/pipeline.py"
echo "=== kitti dataloader calibration ==="
grep -n -B3 -A25 "class KITTIOdometryDataset" "$SP/kiss_icp/datasets/kitti.py" | head -60
echo "=== calibration/apply_calibration in kitti.py ==="
grep -n -A12 "def apply_calibration\|def calibration\|def read_calib" "$SP/kiss_icp/datasets/kitti.py" | head -60
