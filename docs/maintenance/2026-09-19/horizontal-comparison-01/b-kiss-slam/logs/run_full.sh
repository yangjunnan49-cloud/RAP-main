#!/bin/bash
# HC-V1 part B: full KISS-SLAM runs on KITTI 00/05/06 with unmodified defaults.
# Each sequence runs in its own work dir; slam_output lands there naturally.
# Records wall time and peak RSS via GNU time when available.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
VENV=/root/venvs/kiss-slam-hc1/bin
DATA=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset

if command -v /usr/bin/time >/dev/null 2>&1; then TIME=/usr/bin/time; else TIME=""; fi
echo "gnu time: ${TIME:-none}"

for SEQ in 00 05 06; do
  RUN="$HC/runs/kitti$SEQ"
  mkdir -p "$RUN"
  cd "$RUN"
  echo "=== KISS-SLAM full run: kitti $SEQ (start $(date -Is)) ==="
  if [ -n "$TIME" ]; then
    $TIME -v "$VENV/kiss_slam_pipeline" "$DATA" --dataloader kitti --sequence "$SEQ" \
      > "$HC/logs/run_kitti$SEQ.log" 2> "$HC/logs/run_kitti$SEQ.time"
  else
    S=$(date +%s)
    "$VENV/kiss_slam_pipeline" "$DATA" --dataloader kitti --sequence "$SEQ" \
      > "$HC/logs/run_kitti$SEQ.log" 2>&1
    echo "wall_seconds=$(( $(date +%s) - S ))" > "$HC/logs/run_kitti$SEQ.time"
  fi
  echo "=== done kitti $SEQ (exit $?, $(date -Is)) ==="
  tail -4 "$HC/logs/run_kitti$SEQ.log"
done
echo "=== all runs finished ==="
find "$HC/runs" -name "*_poses_kitti.txt" | sort
