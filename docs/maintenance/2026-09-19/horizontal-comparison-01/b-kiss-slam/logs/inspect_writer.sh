#!/bin/bash
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== kiss_icp/pipeline.py lines 143-215 ==="
sed -n '143,215p' "$SP/kiss_icp/pipeline.py"
echo "=== write_poses / save_poses helpers ==="
grep -rn "def write_poses\|def save" "$SP/kiss_icp/tools/"*.py | head
