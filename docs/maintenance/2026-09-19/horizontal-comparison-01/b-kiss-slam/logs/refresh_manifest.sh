#!/bin/bash
# Refresh manifest.json after eval_results.json and helper scripts were added.
set -u
PY=/root/venvs/kiss-slam-hc1/bin/python
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
