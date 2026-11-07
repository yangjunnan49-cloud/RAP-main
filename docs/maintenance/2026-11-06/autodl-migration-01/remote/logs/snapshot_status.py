"""Compact read-only status for the running migration, without credentials."""
from datetime import datetime, timezone
import json
from pathlib import Path

root = Path("/root/autodl-tmp/rap-migration-20261106")
def load(name):
    path = root / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

status = load("file-acceptance/STATUS.json") or {}
published = []
path = root / "logs/public-cache-volumes.jsonl"
if path.exists():
    published = [row for row in map(json.loads, path.read_text().splitlines()) if row.get("published_without_replacing_any_existing_path")]
value = dict(observed_utc=datetime.now(timezone.utc).isoformat(), stage=status.get("stage"),
    verified_files=status.get("verified_files"), expected_files=status.get("expected_files", 589),
    received_bytes=status.get("received_bytes_by_sealed_sizes"), expected_bytes=status.get("expected_bytes", 125499551391),
    latest_file_stage=status, public_cache_volumes_published=len(published),
    public_cache_rebuild_complete=load("PUBLIC_CACHE_REBUILD.json") is not None,
    environment_ready=load("ENVIRONMENT_READY.json") is not None,
    GPU_extension_fixture_passed=(load("GPU_EXTENSION_PROBE.json") or {}).get("passed", False),
    actual_file_acceptance=load("file-acceptance/ACCEPTANCE.json"),
    bounded_functional_acceptance=load("MIGRATION_ACCEPTANCE.json"), finalization=load("SERVER_FINALIZED.json"),
    failures={name:load(name) for name in ("file-acceptance/FAILURE.json", "PUBLIC_CACHE_REBUILD_FAILURE.json",
       "ENVIRONMENT_FAILURE.json", "FUNCTIONAL_FAILURE.json", "FINALIZATION_FAILURE.json") if (root/name).exists()})
(root / "LIVE_STATUS.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key:value[key] for key in ("observed_utc", "stage", "verified_files", "received_bytes", "public_cache_volumes_published", "environment_ready")}))
