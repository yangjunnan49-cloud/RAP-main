#!/bin/bash
# Archive run products: copy pose files to poses/, per-run config to config/,
# build manifest.json with sha256 of every archived artifact.
set -u
HC=/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam
PY=/root/venvs/kiss-slam-hc1/bin/python

for s in 00 05 06; do
  OUT=$(ls -d "$HC"/runs/kitti$s/slam_output/20* | head -1)
  cp "$OUT/${s}_poses_kitti.txt" "$HC/poses/kitti${s}_poses_kitti.txt"
  cp "$OUT/config.yml" "$HC/config/run_kitti${s}_config.yml"
  cp "$OUT/result_metrics.log" "$HC/logs/result_metrics_kitti${s}.log"
  cp "$OUT/trajectory.g2o" "$HC/runs/kitti$s/trajectory.g2o.copy" 2>/dev/null || true
  echo "closures($s): $(grep -c . "$OUT/result_metrics.log" >/dev/null; grep 'closures' "$OUT/result_metrics.log" | tr -s ' ')"
done

"$PY" - <<'EOF'
import hashlib, json
from pathlib import Path
hc = Path("/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam")
files = sorted(p for p in hc.rglob("*") if p.is_file() and "smoke" not in p.parts
               and p.name != "manifest.json")
manifest = {str(p.relative_to(hc)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}
(hc / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print(f"manifest: {len(manifest)} files")
EOF
