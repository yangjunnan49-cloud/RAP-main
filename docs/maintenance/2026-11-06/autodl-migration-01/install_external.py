"""Install only the two explicitly staged AGENTS pointers with old-byte guards."""
import hashlib
import json
from pathlib import Path

phase = Path(__file__).resolve().parent
repo = phase.parents[3]
baseline = json.loads((phase / "BASELINE.json").read_text(encoding="utf-8"))
old = {(row["root"], row["path"]): row for row in baseline["backups"]}
targets = [("workspace-root", repo.parent / "AGENTS.md"), ("rap-slam", repo.parent / "RAP-SLAM/AGENTS.md")]
result = []
for rid, target in targets:
    data = (phase / "staged-external" / (rid + ".AGENTS.md")).read_bytes()
    current = target.read_bytes()
    expected = old[(rid, "AGENTS.md")]
    observed = hashlib.sha256(current).hexdigest()
    new_sha = hashlib.sha256(data).hexdigest()
    assert observed in {expected["sha256"], new_sha}, str(target)
    assert hashlib.sha256((phase / expected["backup"]).read_bytes()).hexdigest() == expected["sha256"]
    if current != data:
        target.write_bytes(data)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == new_sha
    result.append(dict(root=rid, path="AGENTS.md", before_sha256=expected["sha256"], after_sha256=new_sha,
                       previous_bytes_preserved=expected["backup"]))
(phase / "INSTALL_EXTERNAL.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
