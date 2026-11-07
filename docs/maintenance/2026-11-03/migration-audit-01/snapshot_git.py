"""Copy all original Git metadata/object bytes into a tar, including unreachable data."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tarfile
import time

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("asset_auditor", PHASE / "audit_assets.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def main():
    metadata = audit.metadata()
    hashes = {audit.key(r["root"], r["path"]): r for r in audit.load_jsonl(PHASE / "HASHES.jsonl")}
    receipts = []
    for root in ("rap-main", "rap-slam"):
        started = time.monotonic()
        members = [r for r in metadata if r["root"] == root and r["path"].startswith(".git/") and r["kind"] == "file"]
        target = PHASE / "git" / root / "git-directory.tar"
        if target.exists():
            raise RuntimeError("Refuse to overwrite original Git snapshot")
        with tarfile.open(target, "w", format=tarfile.PAX_FORMAT, dereference=False) as archive:
            for row in members:
                if row["reparse_point"]:
                    raise RuntimeError("Unexpected Git reparse object; do not follow")
                h = hashes[audit.key(root, row["path"])]
                if h["status"] != "sha256":
                    raise RuntimeError("Cannot preserve an unhashed Git source")
                source = audit.file_path(row)
                before = source.stat()
                if (before.st_size, before.st_mtime_ns) != (row["bytes"], h["mtime_ns"]):
                    raise RuntimeError("Git source changed after inventory")
                archive.add(source, arcname=row["path"], recursive=False)
                after = source.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise RuntimeError("Git source changed during snapshot")
        verified, byte_count = 0, 0
        by_name = {r["path"]: r for r in members}
        with tarfile.open(target, "r") as archive:
            for member in archive:
                row = by_name.pop(member.name)
                expected = hashes[audit.key(root, row["path"])]
                stream = archive.extractfile(member)
                observed = __import__("hashlib").file_digest(stream, "sha256").hexdigest()
                if observed != expected["sha256"] or member.size != row["bytes"]:
                    raise RuntimeError("Git archive member mismatch")
                verified += 1
                byte_count += member.size
        if by_name:
            raise RuntimeError("Missing Git archive member")
        receipt = {"root": root, "archive": target.relative_to(PHASE).as_posix(), "archive_bytes": target.stat().st_size,
                   "archive_sha256": audit.sha_file(target), "members_verified": verified,
                   "source_logical_bytes": byte_count, "all_members_sha256_match_original_inventory": True,
                   "includes_unreachable_and_temporary_objects": True, "source_repository_mutated": False,
                   "seconds": time.monotonic() - started}
        receipts.append(receipt)
        print(json.dumps(receipt), flush=True)
    audit.write_json("GIT_PRESERVATION.json", receipts)


if __name__ == "__main__":
    main()
