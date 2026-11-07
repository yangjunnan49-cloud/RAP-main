"""Freeze latest through A6 and derive a nonrecursive delta against the A5 base."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import posixpath
import shutil
import subprocess

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A5 = REPO / "docs/maintenance/2026-11-04/assets-package-01"
LAYOUT = {"rap-main": "RAP-main", "rap-slam": "RAP-SLAM", "reports": "RAP-SLAM-report", "datasets": "Datasets", "codex-records": "archives/Codex", "workspace-root": ""}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for b in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def write_rows(path, values):
    path.write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in values).encode("utf-8"))


def main():
    assert not (PHASE / "PROJECT_FREEZE.json").exists()
    baseline = load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["source_roots"].items()}
    base = {(r["root"], r["path"]): r for r in rows(A5 / "SOURCE_FILES.jsonl")}
    excluded = {str(PHASE.resolve()).casefold(), str((REPO / ".maintenance-archive/migration").resolve()).casefold()}
    files, dirs, links = [], [], []
    def walk(root, folder, recursive=True):
        for e in sorted(os.scandir(folder), key=lambda e: e.name.casefold()):
            p = Path(e.path)
            if os.path.abspath(p).casefold() in excluded:
                continue
            s = e.stat(follow_symlinks=False)
            row = {"root": root, "path": p.relative_to(roots[root]).as_posix(), "bytes": s.st_size, "mtime_ns": s.st_mtime_ns,
                   "mode": s.st_mode, "windows_attributes": getattr(s, "st_file_attributes", 0)}
            if row["windows_attributes"] & 0x400 or e.is_symlink():
                links.append(row)
            elif e.is_dir(follow_symlinks=False):
                if recursive:
                    dirs.append(row)
                    walk(root, p)
            else:
                files.append(row)
    for root, path in roots.items():
        walk(root, path, root != "workspace-root")
    assert len(links) == 27
    current_ids = {(r["root"], r["path"]) for r in files}
    assert set(base) <= current_ids, list(set(base) - current_ids)[:5]
    delta, counts = [], Counter()
    for index, row in enumerate(files):
        old = base.get((row["root"], row["path"]))
        if old and old["bytes"] == row["bytes"] and old["mtime_ns"] == row["mtime_ns"]:
            row["sha256"] = old["sha256"]
            row["checksum_basis"] = "A5_FULL_BYTE_VERIFICATION_AND_CURRENT_METADATA_MATCH"
        else:
            path = roots[row["root"]] / row["path"]
            row["sha256"] = sha(path)
            s = path.stat()
            assert s.st_size == row["bytes"] and s.st_mtime_ns == row["mtime_ns"], path
            row["checksum_basis"] = "A7_FRESH_BYTES"
        row["opaque_experiment"] = "portable_graph_20261031" in row["path"].lower()
        counts[row["checksum_basis"]] += 1
        if old is None or old["sha256"] != row["sha256"]:
            row["delta_kind"] = "NEW_IDENTITY" if old is None else "CHANGED_CURRENT_BYTES"
            row["A5_before_sha256"] = old["sha256"] if old else None
            delta.append(row)
        if index and index % 20000 == 0:
            print(json.dumps({"project_inventory_processed": index, "delta_files": len(delta)}), flush=True)
    write_rows(PHASE / "PROJECT_FILES.jsonl", files)
    write_rows(PHASE / "PROJECT_DIRECTORIES.jsonl", dirs)
    write_rows(PHASE / "PROJECT_LINKS.jsonl", links)
    inventory = PHASE / "delta-inventory"
    inventory.mkdir()
    write_rows(inventory / "SOURCE_FILES.jsonl", delta)
    write_rows(inventory / "SOURCE_DIRECTORIES.jsonl", dirs)
    write_rows(inventory / "SOURCE_LINKS.jsonl", links)
    (inventory / "SOURCE_LINKS_RAW.json").write_bytes((A5 / "SOURCE_LINKS_RAW.json").read_bytes())
    save(inventory / "BASELINE.json", {"source_roots": baseline["source_roots"], "source_freeze_is_latest_through_A6": True,
          "A7_current_authority_and_audit_evidence_delivered_as_final_control_overlay": True,
          "ordinary_files": len(delta), "PGC1_partial_results_semantically_read": False})
    link_plan = []
    for old in load(A5 / "SOURCE_LINKS_RAW.json"):
        row = {"root": old["root"], "path": old["path"], "original_target": old["target"], "original_raw_sha256": old["raw_sha256"]}
        if old["kind"] == "junction":
            row["action"] = "external_dependency_not_recreated"
        else:
            absolute = Path(old["target_local"])
            target_root = next(k for k, v in sorted(roots.items(), key=lambda kv: -len(str(kv[1]))) if absolute.is_relative_to(v))
            relative = absolute.relative_to(roots[target_root]).as_posix()
            row["target_asset"] = {"root": target_root, "path": relative}
            mapped_link = posixpath.join(LAYOUT[row["root"]], row["path"])
            mapped_target = posixpath.join(LAYOUT[target_root], relative)
            row["relative_target"] = posixpath.relpath(mapped_target, posixpath.dirname(mapped_link))
            row["action"] = "relative_internal"
        link_plan.append(row)
    save(PHASE / "LINK_PLAN.json", link_plan)

    git = Path("C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe")
    tracked, git_observations = {}, []
    for root in ("rap-main", "rap-slam"):
        index_path = roots[root] / ".git/index"
        before = sha(index_path)
        proc = subprocess.run([str(git), "-C", str(roots[root]), "ls-files", "--stage", "-z"], env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), capture_output=True, timeout=30)
        assert proc.returncode == 0 and sha(index_path) == before
        (PHASE / (root + "-tracked-modes.z")).write_bytes(proc.stdout)
        for record in proc.stdout.split(b"\0"):
            if not record:
                continue
            header, path = record.split(b"\t", 1)
            mode, obj, stage = header.decode("ascii").split()
            assert stage == "0" and mode in {"100644", "100755", "120000", "160000"}
            tracked[root + ":" + path.decode("utf-8")] = mode
        git_observations.append({"root": root, "index_sha256_before_and_after": before, "command": "ls-files --stage -z", "GIT_OPTIONAL_LOCKS": "0"})
    save(PHASE / "PERMISSIONS.json", {"git_tracked_modes": tracked, "mode_counts": dict(Counter(tracked.values())),
          "git_index_read_only_observations": git_observations, "untracked_file_policy": "0644; no execution inferred from extension",
          "directory_policy": "0755 on POSIX; not an NTFS ACL reconstruction", "original_Linux_mode_or_owner_for_all_untracked_files_known": False,
          "POSIX_target_application_still_requires_target_validation": True})
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "ordinary_files": len(files), "logical_bytes": sum(r["bytes"] for r in files),
              "directories": len(dirs), "links": len(links), "delta_files": len(delta), "delta_logical_bytes": sum(r["bytes"] for r in delta),
              "delta_kinds": dict(Counter(r["delta_kind"] for r in delta)), "checksum_basis_counts": dict(counts),
              "all_A5_identities_retained": True, "A7_current_and_evidence_overlay_pending": True, "source_exclusions": sorted(excluded), "layout": LAYOUT,
              "WSL_images_unexported_Linux_environment_or_wheel_in_project_layers": False, "model_or_scientific_array_loading": False}
    save(PHASE / "PROJECT_FREEZE.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
