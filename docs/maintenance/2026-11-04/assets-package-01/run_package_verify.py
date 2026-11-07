"""Independently reread all finished tar volumes and store a bounded receipt."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time

PHASE = Path(__file__).resolve().parent


def main():
    base = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    tool = PHASE / "updates/scripts/migration/content_bundle.py"
    spec = importlib.util.spec_from_file_location("a5_bundle_reader", tool)
    bundle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bundle)
    assert not (PHASE / "ARCHIVE_VERIFY.json").exists(), "Refusing to replace a verification receipt"
    package = Path(base["package_destination"])
    started = time.monotonic()
    with (PHASE / "ARCHIVE_VERIFY_PROGRESS.jsonl").open("x", encoding="utf-8") as log:
        def progress(row):
            log.write(json.dumps(row) + "\n")
            log.flush()
            print(json.dumps(row), flush=True)
        result = bundle.verify(package, progress=progress)
    result.update(observed_utc=datetime.now(timezone.utc).isoformat(), wall_seconds=time.monotonic() - started,
                  package_manifest_sha256=bundle.sha(package / "PACKAGE.json"), verification_tool_sha256=hashlib.sha256(tool.read_bytes()).hexdigest(),
                  model_numpy_or_scientific_result_loads=0, implementation_independence_claimed=False)
    (PHASE / "ARCHIVE_VERIFY.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
