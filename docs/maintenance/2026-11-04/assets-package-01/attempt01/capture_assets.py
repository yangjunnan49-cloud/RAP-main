"""Freeze a link-safe source inventory and preserve current authority before A5."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A1 = REPO / "docs/maintenance/2026-11-03/migration-audit-01"
PREVIOUS = REPO / "docs/maintenance/2026-11-04/environment-readiness-01"
PACKAGE = REPO / ".maintenance-archive/migration/A5-20261104"
ROOTS = {r["id"]: Path(r["local"]) for r in json.loads((A1 / "ROOT_MAPPING.json").read_text(encoding="utf-8"))["mapping"]}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    assert not (PHASE / "BASELINE.json").exists(), "Refusing baseline replacement"
    assert not PACKAGE.exists(), "Package destination already exists"
    current = load(PREVIOUS / "AUTHORITY_PROOF.json")["current_files"]
    backups = []
    for item in current:
        source = ROOTS[item["root"]] / item["path"]
        raw = source.read_bytes()
        assert len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], source
        target = PHASE / "before" / item["root"] / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        backups.append({**item, "backup": target.relative_to(PHASE).as_posix()})
    files, dirs, links, errors = [], [], [], []
    excluded = {str(PHASE.resolve()).casefold(), str(PACKAGE.resolve()).casefold()}

    def scan(root_id, directory, recursive=True):
        try:
            entries = sorted(os.scandir(directory), key=lambda e: e.name.casefold())
        except OSError as exc:
            errors.append({"path": str(directory), "error": repr(exc)})
            return
        for entry in entries:
            path = Path(entry.path)
            if str(path.resolve(strict=False)).casefold() in excluded:
                continue
            try:
                stat = entry.stat(follow_symlinks=False)
                relative = path.relative_to(ROOTS[root_id]).as_posix()
                item = {"root": root_id, "path": relative, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                        "file_id": str(stat.st_ino), "device": str(stat.st_dev), "mode": stat.st_mode,
                        "windows_attributes": getattr(stat, "st_file_attributes", None)}
                if getattr(stat, "st_file_attributes", 0) & 0x400:
                    item["reparse_tag"] = getattr(stat, "st_reparse_tag", None)
                    links.append(item)
                elif entry.is_dir(follow_symlinks=False):
                    if recursive:
                        dirs.append(item)
                        scan(root_id, path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(item)
                else:
                    errors.append({"path": str(path), "error": "Unsupported special entry"})
            except OSError as exc:
                errors.append({"path": str(path), "error": repr(exc)})

    for root, path in ROOTS.items():
        scan(root, path, recursive=root != "workspace-root")
    assert not errors, errors[:5]
    original = {(r["root"], r["path"]): r for r in rows(A1 / "HASHES.jsonl")}
    caches = {k: {"sha256": r["sha256"], "bytes": r["bytes"], "mtime_ns": r["mtime_ns"], "basis": "A1_FULL_HASH"} for k, r in original.items()}
    # Later sealed phases cover files introduced after A1, including large Git archives.
    phase_dirs = [REPO / "docs/maintenance/2026-11-03/migration-preflight-01", A1,
                  REPO / "docs/maintenance/2026-11-03/context-index-01", REPO / "docs/maintenance/2026-11-04/code-paths-01", PREVIOUS]
    for folder in phase_dirs:
        seal = load(folder / "DELIVERY_SEAL.json")
        for r in seal["files"]:
            source = folder / r["path"]
            stat = source.stat()
            assert stat.st_size == r["bytes"], source
            key = ("rap-main", source.relative_to(REPO).as_posix())
            caches[key] = {"sha256": r["sha256"], "bytes": r["bytes"], "mtime_ns": stat.st_mtime_ns,
                           "basis": "PRIOR_PHASE_SEAL:" + folder.name}
    for r in current:
        stat = (ROOTS[r["root"]] / r["path"]).stat()
        caches[(r["root"], r["path"])] = {"sha256": r["sha256"], "bytes": r["bytes"], "mtime_ns": stat.st_mtime_ns, "basis": "A4_AUTHORITY"}
    old_ledger = {(r["root"], r["path"]): r for r in rows(A1 / "ASSET_LEDGER.jsonl")}
    for r in files:
        key = (r["root"], r["path"])
        cached = caches.get(key)
        if cached and cached["bytes"] == r["bytes"] and cached["mtime_ns"] == r["mtime_ns"]:
            r.update(sha256=cached["sha256"], checksum_basis=cached["basis"], content_rehashed_in_A5_inventory=False)
        else:
            digest = hashlib.sha256()
            source = ROOTS[r["root"]] / r["path"]
            with source.open("rb") as handle:
                for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                    digest.update(block)
            after = source.stat()
            assert after.st_size == r["bytes"] and after.st_mtime_ns == r["mtime_ns"], source
            r.update(sha256=digest.hexdigest(), checksum_basis="A5_FRESH_HASH", content_rehashed_in_A5_inventory=True)
        prior = old_ledger.get(key, {})
        r["prior_category"] = prior.get("category")
        r["opaque_experiment"] = "portable_graph_20261031" in r["path"].lower()
    original_ids = set(original)
    current_ids = {(r["root"], r["path"]) for r in files}
    assert original_ids <= current_ids, list(original_ids - current_ids)[:5]
    assert len(links) == 27, len(links)
    for name, values in (("SOURCE_FILES.jsonl", files), ("SOURCE_DIRECTORIES.jsonl", dirs), ("SOURCE_LINKS.jsonl", links)):
        (PHASE / name).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in values), encoding="utf-8")
    total = sum(r["bytes"] for r in files)
    unique = {(r["sha256"], r["bytes"]) for r in files}
    unique_bytes = sum(size for _, size in unique)
    assert shutil.disk_usage(REPO).free > unique_bytes + 16 * 1024**3, "Insufficient workspace free space"
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "owner_request": "继续（A5）", "previous_phase": PREVIOUS.relative_to(REPO).as_posix(),
              "backups": backups, "source_roots": {k: str(v) for k, v in ROOTS.items()}, "ordinary_files": len(files), "directories": len(dirs), "links": len(links),
              "logical_bytes": total, "unique_content_objects": len(unique), "unique_content_bytes": unique_bytes,
              "root_counts": dict(Counter(r["root"] for r in files)), "checksum_basis_counts": dict(Counter(r["checksum_basis"] for r in files)),
              "package_destination": str(PACKAGE), "source_exclusions": [str(PHASE), str(PACKAGE)],
              "WSL_images_or_uncollected_Linux_environment_included": False, "metadata_reused_hashes_are_not_fresh_reads_of_all_duplicates": True,
              "PGC1_partial_results_semantically_read": False}
    (PHASE / "BASELINE.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"backups", "source_roots", "source_exclusions"}}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
