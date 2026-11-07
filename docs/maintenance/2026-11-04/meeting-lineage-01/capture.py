"""Freeze A6 authority and meeting/report assets without following reparse points."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A5 = REPO / "docs/maintenance/2026-11-04/assets-package-01"
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "reports": REPO.parent / "RAP-SLAM-report", "workspace-root": REPO.parent}
SCOPES = [("rap-main", "docs/meeting_20260921"), ("rap-main", "docs/meeting_20260930"),
          ("rap-main", "docs/meeting_20261011"), ("rap-main", "docs/meeting_20261018"),
          ("rap-main", "docs/meeting_20261025"), ("rap-main", "working files/decks"),
          ("rap-main", "working files/weekly_20261101"), ("reports", "advisor_report"),
          ("reports", "ppt"), ("reports", "ppt_weekly_20260823"), ("reports", "paper")]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for b in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def save(name, value):
    (PHASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    assert not (PHASE / "BASELINE.json").exists()
    assert sha(A5 / "DELIVERY_SEAL.json") == "1e05337547ffe58bf782899f37d45a4d611ae8b32c1f7000c60662f28805d0e9"
    previous = json.loads((A5 / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))
    backups = []
    for item in previous["current_files"]:
        source = ROOTS[item["root"]] / item["path"]
        assert sha(source) == item["sha256"]
        target = PHASE / "before" / item["root"] / item["path"]
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert sha(target) == item["sha256"]
        backups.append({**item, "backup": target.relative_to(PHASE).as_posix()})
    previous_assets = {}
    with (A5 / "SOURCE_FILES.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            r = json.loads(line)
            previous_assets[(r["root"], r["path"])] = r
    records, links, directories = [], [], []
    def walk(root, folder):
        for entry in sorted(os.scandir(folder), key=lambda e: e.name):
            path = Path(entry.path)
            stat = entry.stat(follow_symlinks=False)
            relative = path.relative_to(ROOTS[root]).as_posix()
            r = {"root": root, "path": relative, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                 "windows_attributes": getattr(stat, "st_file_attributes", 0)}
            if r["windows_attributes"] & 0x400 or entry.is_symlink():
                links.append(r)
            elif entry.is_dir(follow_symlinks=False):
                directories.append(r)
                walk(root, path)
            else:
                digest = sha(path)
                assert path.stat().st_size == stat.st_size and path.stat().st_mtime_ns == stat.st_mtime_ns
                old = previous_assets.get((root, relative))
                r.update({"sha256": digest, "A5_frozen_sha256": old["sha256"] if old else None,
                          "matches_A5_base": old is not None and old["sha256"] == digest,
                          "raw_hash_only_no_array_or_model_loading": True})
                records.append(r)
    for root, relative in SCOPES:
        walk(root, ROOTS[root] / relative)
    assert len({(r["root"], r["path"]) for r in records}) == len(records)
    (PHASE / "SOURCE_FILES.jsonl").write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records).encode("utf-8"))
    save("LINKS.json", links)
    save("DIRECTORIES.json", directories)
    save("BASELINE.json", {"created_utc": datetime.now(timezone.utc).isoformat(), "owner_request": "继续执行A6；继续",
         "previous_phase": A5.relative_to(REPO).as_posix(), "previous_seal_sha256": sha(A5 / "DELIVERY_SEAL.json"),
         "roots": {k: str(v) for k, v in ROOTS.items()}, "backups": backups,
         "scopes": [{"root": r, "path": p} for r, p in SCOPES], "ordinary_files": len(records),
         "logical_bytes": sum(r["bytes"] for r in records), "links_not_followed": len(links),
         "directories": len(directories), "all_source_bytes_match_A5_base": all(r["matches_A5_base"] for r in records),
         "production_source_or_history_modified": False, "research_or_training_run": False})
    print(json.dumps({"before": len(backups), "source_files": len(records), "bytes": sum(r["bytes"] for r in records),
                      "links_not_followed": len(links), "all_match_A5": all(r["matches_A5_base"] for r in records)}), flush=True)


if __name__ == "__main__":
    main()
