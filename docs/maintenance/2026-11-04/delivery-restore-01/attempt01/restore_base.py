"""Perform the actual complete A5 restore, keeping progress and exact tool binding."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
LAYOUT = {"rap-main": "RAP-main", "rap-slam": "RAP-SLAM", "reports": "RAP-SLAM-report", "datasets": "Datasets", "codex-records": "archives/Codex", "workspace-root": ""}


def main():
    baseline = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    used = PHASE / "used/delivery.py"
    assert not used.exists()
    used.parent.mkdir()
    used.write_bytes((PHASE / "updates/scripts/migration/delivery.py").read_bytes())
    spec = importlib.util.spec_from_file_location("actual_base_restore", used)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    destination = Path(baseline["restore_destination"]) / "workspace"
    assert not destination.exists()
    package = REPO / ".maintenance-archive/migration/A5-20261104"
    progress_file = PHASE / "BASE_RESTORE_PROGRESS.jsonl"
    def progress(value):
        value["observed_utc"] = datetime.now(timezone.utc).isoformat()
        with progress_file.open("ab") as handle:
            handle.write((json.dumps(value) + "\n").encode("utf-8"))
        print(json.dumps(value), flush=True)
    started = time.monotonic()
    try:
        result = tool.restore_layer(package, destination, LAYOUT, progress=progress)
        result.update({"observed_utc": datetime.now(timezone.utc).isoformat(), "destination": str(destination), "layout": LAYOUT,
                       "used_tool_sha256": hashlib.sha256(used.read_bytes()).hexdigest(),
                       "base_package_manifest_sha256": tool.sha(package / "PACKAGE.json"), "wall_seconds": time.monotonic() - started,
                       "full_post_restore_tree_rehash_pending_overlay": True, "source_originals_modified_or_removed": False})
        (PHASE / "BASE_RESTORE.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        print(json.dumps(result, ensure_ascii=False), flush=True)
    except Exception as error:
        (PHASE / "BASE_RESTORE_FAILURE.json").write_bytes((json.dumps({"error": repr(error), "partial_restore_retained": True,
             "source_originals_modified": False, "destination": str(destination)}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        raise


if __name__ == "__main__":
    main()
