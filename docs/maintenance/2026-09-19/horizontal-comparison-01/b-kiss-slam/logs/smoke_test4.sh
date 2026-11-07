#!/bin/bash
# Install matplotlib (second undeclared upstream dependency), refresh freeze,
# rerun smoke, and sanity-check the pose file.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
VENV=/root/venvs/kiss-slam-hc1/bin
DATA=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset

"$VENV/pip" install --quiet matplotlib
"$VENV/pip" freeze > "$HC/env/pip_freeze.txt"
echo "freeze updated ($(wc -l < "$HC/env/pip_freeze.txt") lines)"

rm -rf "$HC/smoke/kitti00/slam_output"
cd "$HC/smoke/kitti00"
"$VENV/kiss_slam_pipeline" "$DATA" --dataloader kitti --sequence 00 --n-scans 100 2>&1 | tail -12
OUT=$(ls -d "$HC"/smoke/kitti00/slam_output/20* | head -1)
echo "=== results dir: $OUT ==="
ls "$OUT"
echo "=== pose file: rows / first row ==="
wc -l "$OUT/00_poses_kitti.txt"
head -1 "$OUT/00_poses_kitti.txt"
echo "=== result_metrics.log ==="
cat "$OUT/result_metrics.log"
