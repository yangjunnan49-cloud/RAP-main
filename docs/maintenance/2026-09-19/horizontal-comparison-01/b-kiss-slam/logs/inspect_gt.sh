#!/bin/bash
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== kitti.py load_poses ==="
awk '/def load_poses/,/def [a-z_]+\(/' "$SP/kiss_icp/datasets/kitti.py" | head -25
echo "=== odometry pipeline has_gt / gt_poses init ==="
grep -n -B2 -A8 "has_gt\|self.gt_poses" "$SP/kiss_icp/pipeline.py" | head -40
