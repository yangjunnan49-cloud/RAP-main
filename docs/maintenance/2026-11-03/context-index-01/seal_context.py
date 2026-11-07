"""Preserve the finished current documents and seal A2; no original asset mutations."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    checks = json.loads((PHASE / "CHECKS.json").read_text(encoding="utf-8"))
    if not checks["passed"]:
        raise RuntimeError("Cannot seal failed A2")
    proof = json.loads((PHASE / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))
    after = PHASE / "after"
    after.mkdir(exist_ok=False)
    snapshots = []
    for item in proof["current_files"]:
        source = ROOTS[item["root"]] / item["path"]
        if source.stat().st_size != item["bytes"] or sha(source) != item["sha256"]:
            raise RuntimeError("Current document changed after acceptance")
        target = (after / item["root"] / item["path"]).resolve()
        if not target.is_relative_to(after.resolve()):
            raise RuntimeError("Invalid snapshot path")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != item["sha256"]:
            raise RuntimeError("Current document snapshot mismatch")
        snapshots.append({**item, "backup": target.relative_to(PHASE).as_posix()})
    (PHASE / "CURRENT_DOCUMENT_SNAPSHOTS.json").write_text(json.dumps(snapshots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    seal_path = PHASE / "DELIVERY_SEAL.json"
    if seal_path.exists():
        raise RuntimeError("Refuse to overwrite completed seal")
    files = []
    for path in sorted(PHASE.rglob("*")):
        if path.is_file() and path != seal_path:
            files.append({"path": path.relative_to(PHASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    value = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A2_COMPLETE_DOCUMENTATION_AND_CATALOG",
             "files": files, "current_documents_preserved": len(snapshots),
             "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1,
             "scientific_evaluations_run": 0, "old_scientific_seals_unchanged": True,
             "next_stage": "A3", "whole_migration_complete": False}
    seal_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if json.loads(seal_path.read_text(encoding="utf-8")) != value:
        raise RuntimeError("Seal serialization mismatch")
    print(json.dumps({"stage": value["stage"], "phase_files_sealed": len(files), "phase_bytes": sum(f["bytes"] for f in files),
                      "current_document_snapshots_verified": len(snapshots), "seal_sha256": sha(seal_path),
                      "next_stage": "A3"}), flush=True)


if __name__ == "__main__":
    main()
