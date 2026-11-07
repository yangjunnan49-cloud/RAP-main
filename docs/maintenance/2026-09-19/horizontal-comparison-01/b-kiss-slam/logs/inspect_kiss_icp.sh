#!/bin/bash
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== kiss_icp pipeline output methods ==="
grep -n "_create_output_dir\|_write_result_poses\|_write_gt_poses\|_write_cfg\|_write_log\|results_dir\|def _get" "$SP/kiss_icp/pipeline.py" | head -30
echo "=== _write_result_poses body ==="
awk '/def _write_result_poses/,/^    def [a-z_]+\(self[^_]/' "$SP/kiss_icp/pipeline.py" | head -30
echo "=== _create_output_dir body ==="
awk '/def _create_output_dir/,/^    def [a-z]/' "$SP/kiss_icp/pipeline.py" | head -25
echo "=== available dataloaders ==="
/root/venvs/kiss-slam-hc1/bin/python -c "from kiss_icp.datasets import available_dataloaders; print(sorted(available_dataloaders()))"
