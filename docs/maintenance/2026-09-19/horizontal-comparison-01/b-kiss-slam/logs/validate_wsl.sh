#!/bin/bash
# WSL-side validation: baseline recompute + external run recomputation.
set -u
/root/miniconda3/envs/rap-inference/bin/python \
  /mnt/e/githouse/RAP-main/scripts/maintenance/validate_horizontal_comparison.py \
  --checks baseline_recompute,external_runs
