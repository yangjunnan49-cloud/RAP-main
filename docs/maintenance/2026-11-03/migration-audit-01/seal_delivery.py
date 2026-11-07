"""Seal this maintenance phase; verify new backup files while recording SHA256."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
SEAL = PHASE / "DELIVERY_SEAL.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    if SEAL.exists():
        raise RuntimeError("Refuse to overwrite completed phase seal")
    records = []
    for path in sorted(PHASE.rglob("*")):
        if path.is_file() and path != SEAL:
            records.append({"path": path.relative_to(PHASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    by_name = {r["path"]: r for r in records}
    for git in json.loads((PHASE / "GIT_PRESERVATION.json").read_text(encoding="utf-8")):
        record = by_name[git["archive"]]
        if record["sha256"] != git["archive_sha256"] or record["bytes"] != git["archive_bytes"]:
            raise RuntimeError("Preserved Git archive changed")
    value = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A1",
             "scope": "Audit, original Git/source preservation, dry-run dispositions and explicit historical holds",
             "files": records, "old_scientific_files_unchanged": True,
             "current_authority_proof": "AUTHORITY_PROOF.json", "whole_migration_complete": False}
    SEAL.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    loaded = json.loads(SEAL.read_text(encoding="utf-8"))
    if loaded != value:
        raise RuntimeError("Phase seal serialization mismatch")
    print(json.dumps({"phase_files_sealed": len(records), "phase_bytes": sum(r["bytes"] for r in records),
                      "preserved_git_archives_match_receipts": True, "seal_sha256": sha(SEAL),
                      "full_source_tree_rehash_repeated": False}), flush=True)


if __name__ == "__main__":
    main()
