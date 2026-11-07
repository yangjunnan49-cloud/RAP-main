"""Fresh byte audit of all six current roots against the final A7 delivery."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
LAYOUT = {"rap-main": "RAP-main", "rap-slam": "RAP-SLAM", "reports": "RAP-SLAM-report",
          "datasets": "Datasets", "codex-records": "archives/Codex", "workspace-root": ""}


def native(path):
    path = str(path.absolute())
    return Path("\\\\?\\" + path) if os.name == "nt" and not path.startswith("\\\\?\\") else Path(path)


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    if (PHASE / "CURRENT_AUDIT.json").exists():
        raise SystemExit("Audit already exists")
    saved = json.loads((REPO / "docs/maintenance/2026-11-04/delivery-restore-01/BASELINE.json").read_text(encoding="utf-8"))
    roots = {rid: native(Path(path)) for rid, path in saved["source_roots"].items()}
    expected = {}
    with (REPO / ".maintenance-archive/migration/A7-20261104/DELIVERY_FILES.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            path = row["path"]
            if path.startswith("archives/source-versions/"):
                continue
            for rid, prefix in sorted(LAYOUT.items(), key=lambda item: -len(item[1])):
                if prefix and path.startswith(prefix + "/"):
                    expected[(rid, path[len(prefix) + 1:])] = row
                    break
            else:
                if "/" not in path:
                    expected[("workspace-root", path)] = row
                else:
                    raise ValueError("Unmapped delivery path: " + path)
    exclusions = {str(native(PHASE)).casefold(), str(native(REPO / ".maintenance-archive/migration")).casefold()}
    files, links, directories = [], [], []

    def walk(rid, folder, recursive=True):
        for entry in sorted(os.scandir(folder), key=lambda item: item.name.casefold()):
            path = Path(entry.path)
            if str(path).casefold() in exclusions:
                continue
            info = entry.stat(follow_symlinks=False)
            row = dict(root=rid, path=path.relative_to(roots[rid]).as_posix(), bytes=info.st_size,
                       mtime_ns=info.st_mtime_ns, windows_attributes=getattr(info, "st_file_attributes", 0))
            if row["windows_attributes"] & 0x400 or entry.is_symlink():
                links.append(row)
            elif entry.is_dir(follow_symlinks=False):
                if recursive:
                    directories.append(row)
                    walk(rid, path)
            else:
                files.append(row)

    for rid, root in roots.items():
        walk(rid, root, rid != "workspace-root")
    counts, total = Counter(), 0
    delta = []

    def read(row):
        path = roots[row["root"]] / row["path"]
        value = sha(path)
        info = path.stat()
        if info.st_size != row["bytes"] or info.st_mtime_ns != row["mtime_ns"]:
            raise RuntimeError("Source changed during byte read: " + str(path))
        old = expected.get((row["root"], row["path"]))
        kind = "NEW_CURRENT_IDENTITY" if old is None else "MATCH_A7_BYTES" if value == old["sha256"] else "CHANGED_CURRENT_BYTES"
        return dict(row, sha256=value, checksum_basis="A8_FRESH_BYTES", kind=kind,
                    A7_before_sha256=old["sha256"] if old else None)

    with (PHASE / "CURRENT_FILES.jsonl").open("x", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=2) as pool:
        for index, row in enumerate(pool.map(read, files), 1):
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            counts[row["kind"]] += 1
            total += row["bytes"]
            if row["kind"] != "MATCH_A7_BYTES":
                delta.append(row)
            if index % 5000 == 0:
                out.flush()
                progress = dict(files_freshly_hashed=index, bytes_freshly_hashed=total, delta_files=len(delta))
                (PHASE / "CURRENT_AUDIT_PROGRESS.json").write_text(json.dumps(progress) + "\n")
                print(json.dumps(progress), flush=True)
    identities = {(row["root"], row["path"]) for row in files}
    missing = [dict(root=rid, path=path, sha256=expected[(rid, path)]["sha256"]) for rid, path in sorted(set(expected) - identities)]
    for name, value in (("CURRENT_DELTA.json", delta), ("CURRENT_MISSING.json", missing),
                        ("CURRENT_LINKS.json", links), ("CURRENT_DIRECTORIES.json", directories)):
        (PHASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = dict(completed_utc=datetime.now(timezone.utc).isoformat(), complete=True,
                  files_freshly_hashed=len(files), bytes_freshly_hashed=total, counts=dict(counts),
                  delta_files=len(delta), delta_bytes=sum(row["bytes"] for row in delta),
                  missing_current_identities=len(missing), link_metadata_entries=len(links),
                  source_roots=saved["source_roots"], exclusions=[str(PHASE), str(REPO / ".maintenance-archive/migration")],
                  not_an_atomic_global_filesystem_snapshot=True, PGC1_partial_results_semantically_read=False,
                  source_assets_modified_or_deleted=False)
    (PHASE / "CURRENT_AUDIT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
