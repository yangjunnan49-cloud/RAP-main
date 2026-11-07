#!/bin/bash
# Show kiss_slam config module and CLI source to learn output conventions.
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== config/config.py (head) ==="
sed -n '1,80p' "$SP/kiss_slam/config/config.py" 2>/dev/null || ls "$SP/kiss_slam/config/"
echo "=== tools/cli.py ==="
cat "$SP/kiss_slam/tools/cli.py"
