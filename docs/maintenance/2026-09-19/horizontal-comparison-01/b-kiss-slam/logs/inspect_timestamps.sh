#!/bin/bash
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== kitti.py scans/timestamps ==="
sed -n '50,92p' "$SP/kiss_icp/datasets/kitti.py"
