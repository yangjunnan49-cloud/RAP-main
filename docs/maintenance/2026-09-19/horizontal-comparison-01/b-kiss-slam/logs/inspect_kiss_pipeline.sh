#!/bin/bash
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== config.py tail (write_config) ==="
sed -n '80,200p' "$SP/kiss_slam/config/config.py"
echo "=== pipeline.py ==="
cat "$SP/kiss_slam/pipeline.py"
