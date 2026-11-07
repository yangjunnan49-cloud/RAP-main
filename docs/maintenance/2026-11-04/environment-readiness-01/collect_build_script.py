"""Read the discovered legacy build script; never execute its commands."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

PHASE = Path(__file__).resolve().parent
source = Path("/root/build_pytorch3d.sh")
result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "source": str(source), "files": [], "executed": False}
if source.is_file():
    raw = source.read_bytes()
    assert len(raw) <= 1024 * 1024
    target = PHASE / "linux-preservation/build-evidence/root/build_pytorch3d.sh"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    result["files"].append({"source": str(source), "copy": target.relative_to(PHASE).as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    text = raw.decode("utf-8", errors="replace")
    result["script_text"] = text
    result["full_commit_candidates"] = sorted(set(re.findall(r"\b[0-9a-f]{40}\b", text, re.I)))
    result["correction_to_first_build_scan"] = "The first scan handled .log files only and incorrectly labelled this existing .sh file NOT_PRESENT. Its actual bytes are now preserved."
else:
    result["state"] = "NOT_PRESENT"
(PHASE / "BUILD_SCRIPT_EVIDENCE.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
