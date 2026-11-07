#!/bin/bash
# F2 independent validation entrypoint, amended validator (execution convenience; no analysis logic).
cd /mnt/e/githouse/RAP-SLAM
/root/miniconda3/envs/rap-inference/bin/python /mnt/e/githouse/RAP-main/scripts/maintenance/validate_f2_structured_v2.py validate > /mnt/e/githouse/RAP-main/scripts/maintenance/f2_validate.log 2>&1
