#!/bin/bash
# Check whether the kitti06 run survived; rerun it alone if incomplete.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
VENV=/root/venvs/kiss-slam-hc1/bin
DATA=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset

echo "=== running kiss processes ==="
ps aux | grep -i kiss | grep -v grep || echo "none"
echo "=== existing 06 outputs ==="
find "$HC/runs/kitti06" -type f 2>/dev/null | sort || echo "none"

POSES=$(find "$HC/runs/kitti06" -name "06_poses_kitti.txt" 2>/dev/null | head -1)
if [ -n "$POSES" ] && [ "$(wc -l < "$POSES")" -eq 1101 ]; then
  echo "06 already complete: $POSES"
else
  echo "=== rerun kitti 06 (start $(date -Is)) ==="
  rm -rf "$HC/runs/kitti06/slam_output"
  mkdir -p "$HC/runs/kitti06" && cd "$HC/runs/kitti06"
  /usr/bin/time -v "$VENV/kiss_slam_pipeline" "$DATA" --dataloader kitti --sequence 06 \
    > "$HC/logs/run_kitti06.log" 2> "$HC/logs/run_kitti06.time"
  echo "=== done kitti 06 (exit $?, $(date -Is)) ==="
  tail -4 "$HC/logs/run_kitti06.log"
fi
find "$HC/runs" -name "*_poses_kitti.txt" | sort
