#!/bin/bash
# Inspect the installed kiss_slam package: layout, entry points, dump_config source.
set -u
SP=/root/venvs/kiss-slam-hc1/lib/python3.12/site-packages
echo "=== kiss_slam package files ==="
ls "$SP/kiss_slam/"
echo "=== entry_points.txt ==="
cat "$SP"/kiss_slam-*.dist-info/entry_points.txt
echo "=== dump_config source ==="
find "$SP/kiss_slam" -name "*.py" | xargs grep -ln "dump_config" | head -5
