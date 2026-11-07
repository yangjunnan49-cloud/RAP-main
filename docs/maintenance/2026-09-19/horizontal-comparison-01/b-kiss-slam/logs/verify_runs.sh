#!/bin/bash
# Verify frame counts and resource usage of the three full runs.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
for s in 00 05 06; do
  f=$(find "$HC/runs/kitti$s" -name "${s}_poses_kitti.txt" | head -1)
  echo "seq $s: $(wc -l < "$f") rows | $f"
done
echo "=== resource usage (GNU time) ==="
grep -H "Maximum resident\|Elapsed (wall" "$HC"/logs/run_kitti*.time | sed "s|$HC/logs/||"
