#!/bin/bash
# F2 detached run entrypoint (execution convenience; no analysis logic).
cd /mnt/e/githouse/RAP-SLAM
PYTHONPATH=/mnt/e/githouse/RAP-main /root/miniconda3/envs/rap-inference/bin/python scripts/structured_motion_dev.py "$1" > "/mnt/e/githouse/RAP-main/scripts/maintenance/f2_run$1.log" 2>&1
