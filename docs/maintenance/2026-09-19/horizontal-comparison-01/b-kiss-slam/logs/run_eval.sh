#!/bin/bash
# Evaluate archived KISS-SLAM pose files with the RAP baseline metric code.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
PY=/root/miniconda3/envs/rap-inference/bin/python
DATA=/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset

"$PY" /mnt/e/githouse/RAP-SLAM/scripts/eval_external_trajectory.py \
  --poses-dir "$HC/poses" \
  --dataset-root "$DATA" \
  --sequences 00,05,06 \
  --method-label "KISS-SLAM 0.0.2 (KISS-ICP 1.3.0 odometry + map_closures 2.1.0 + GTSAM PGO), unmodified default config" \
  --short-label "KISS-SLAM (same-data run, default cfg)" \
  --provenance '{"package": "kiss-slam 0.0.2 PyPI wheel", "kiss_icp": "1.3.0", "python": "3.12.3", "venv": "/root/venvs/kiss-slam-hc1", "pip_freeze": "env/pip_freeze.txt", "config_sha256": "a17813d28ee273739e0e685913025b3b1091f09229736a2c2cdaf1c566d19718", "config": "unmodified defaults (config/default_config.yaml)", "dataloader": "kitti (applies intrinsic vertical-angle correction, upstream default)", "closures": {"00": 7, "05": 5, "06": 4}, "wall_seconds": {"00": 173.14, "05": 109.39, "06": 49.64}, "peak_rss_bytes": {"00": 1091568, "05": 1073900, "06": 1066164}, "device": "CPU-only", "run_host": "WSL Ubuntu-24.04"}' \
  --out "$HC/eval_results.json"
