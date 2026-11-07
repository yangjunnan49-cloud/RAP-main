"""Restore layered research assets into a new, mapped workspace without execution."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import time

BLOCK = 8 * 1024 * 1024


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for b in iter(lambda: handle.read(BLOCK), b""):
            h.update(b)
    return h.hexdigest()


def safe_relative(value):
    if not isinstance(value, str) or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Unsafe relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(p in {"", ".", ".."} for p in value.split("/")):
        raise ValueError("Unsafe relative path")
    return Path(*path.parts)


def mapped(workspace, layout, row):
    workspace = Path(workspace).resolve()
    if row["root"] not in layout:
        raise ValueError("Unknown source root")
    prefix = Path() if layout[row["root"]] == "" else safe_relative(layout[row["root"]])
    target = workspace / prefix / safe_relative(row["path"])
    if not target.resolve().is_relative_to(workspace):
        raise ValueError("Mapped path escapes workspace")
    parent = target.parent
    while parent != workspace:
        if parent.exists() and (parent.is_symlink() or getattr(parent.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Reparse point in restore parent")
        parent = parent.parent
    return target


def validate_rows(records, layout):
    seen, mapped_paths, sizes = set(), set(), {}
    for r in records:
        key = (r["root"], r["path"])
        if key in seen or r["root"] not in layout:
            raise ValueError("Duplicate or unknown source identity")
        seen.add(key)
        safe_relative(r["path"])
        combined = (layout[r["root"]] + "/" + r["path"]).lstrip("/")
        if combined.casefold() in mapped_paths:
            raise ValueError("Mapped path collision")
        mapped_paths.add(combined.casefold())
        if not re.fullmatch(r"[0-9a-f]{64}", r["sha256"]) or type(r["bytes"]) is not int or r["bytes"] < 0:
            raise ValueError("Invalid source hash/size")
        if r["sha256"] in sizes and sizes[r["sha256"]] != r["bytes"]:
            raise ValueError("Digest has conflicting sizes")
        sizes[r["sha256"]] = r["bytes"]


class HashReader:
    def __init__(self, handle):
        self.handle, self.digest, self.count = handle, hashlib.sha256(), 0

    def read(self, size=-1):
        b = self.handle.read(size)
        self.digest.update(b)
        self.count += len(b)
        return b


def layer_controls(package):
    package = Path(package).resolve()
    meta = load(package / "PACKAGE.json")
    if meta.get("complete") is not True:
        raise ValueError("Incomplete layer")
    for name, digest in meta["control_sha256"].items():
        if safe_relative(name).name != name or sha(package / name) != digest:
            raise ValueError("Layer control mismatch")
    for name, field in (("SOURCE_FILES.jsonl", "source_manifest_sha256"), ("OBJECTS.jsonl", "objects_manifest_sha256"), ("SOURCE_BYTE_CHECKS.jsonl", "source_byte_checks_sha256")):
        if sha(package / name) != meta[field]:
            raise ValueError("Layer metadata mismatch")
    records = rows(package / "SOURCE_FILES.jsonl")
    objects = {r["sha256"]: r for r in rows(package / "OBJECTS.jsonl")}
    if len(objects) != meta["unique_objects"] or {r["sha256"] for r in records} != set(objects):
        raise ValueError("Layer object coverage differs")
    return meta, records, objects


def restore_layer(package, workspace, layout, *, overlay=False, expected_before=None, progress=None):
    """Read each whole volume, verify it, and restore every physical source identity."""
    package, workspace = Path(package).resolve(), Path(workspace).resolve()
    meta, records, objects = layer_controls(package)
    validate_rows(records, layout)
    if not overlay and workspace.exists():
        raise FileExistsError("Restore workspace must be new")
    if overlay and (not workspace.is_dir() or expected_before is None):
        raise ValueError("Overlay requires an existing checked base and explicit old manifest")
    before = {} if expected_before is None else {(r["root"], r["path"]): r for r in expected_before}
    wanted = {}
    for r in records:
        wanted.setdefault(r["sha256"], []).append(r)
    workspace.mkdir(parents=True, exist_ok=overlay)
    for r in rows(package / "SOURCE_DIRECTORIES.jsonl"):
        mapped(workspace, layout, r).mkdir(parents=True, exist_ok=True)
    restored, superseded, seen = [], [], set()
    started = time.monotonic()

    def new_target(row):
        target = mapped(workspace, layout, row)
        if target.exists() or target.is_symlink():
            old = before.get((row["root"], row["path"]))
            if not overlay or old is None or not target.is_file() or target.is_symlink() or sha(target) != old["sha256"]:
                raise ValueError("Unregistered overlay target")
            archive = workspace / "archives/source-versions/A5" / row["root"] / safe_relative(row["path"])
            if not archive.resolve().is_relative_to(workspace) or archive.exists():
                raise ValueError("Unsafe superseded-version target")
            archive.parent.mkdir(parents=True, exist_ok=True)
            target.rename(archive)  # Only a verified file in this new restore tree is moved.
            superseded.append({"path": archive.relative_to(workspace).as_posix(), "bytes": old["bytes"], "sha256": old["sha256"],
                               "source_root": row["root"], "source_path": row["path"]})
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    for volume in meta["volumes"]:
        if not re.fullmatch(r"payload-[0-9]{4}\.tar", volume["name"]):
            raise ValueError("Unsafe volume name")
        path = package / volume["name"]
        if path.stat().st_size != volume["bytes"]:
            raise ValueError("Volume size differs")
        with path.open("rb") as handle:
            stream = HashReader(handle)
            with tarfile.open(fileobj=stream, mode="r|", bufsize=BLOCK) as archive:
                for info in archive:
                    if not info.isfile() or not re.fullmatch(r"objects/[0-9a-f]{64}", info.name):
                        raise ValueError("Unexpected tar member")
                    digest = info.name.split("/")[1]
                    if digest in seen or digest not in wanted:
                        raise ValueError("Duplicate or unknown object")
                    obj = objects[digest]
                    if obj["volume"] != volume["name"] or obj["member"] != info.name or obj["bytes"] != info.size:
                        raise ValueError("Object manifest differs")
                    targets = wanted.pop(digest)
                    first = targets[0]
                    target = new_target(first)
                    reader, value, count = archive.extractfile(info), hashlib.sha256(), 0
                    with target.open("xb") as output:
                        for b in iter(lambda: reader.read(BLOCK), b""):
                            output.write(b)
                            value.update(b)
                            count += len(b)
                    if value.hexdigest() != digest or count != first["bytes"]:
                        raise ValueError("Restored object hash differs")
                    restored.append(first)
                    for row in targets[1:]:
                        duplicate = new_target(row)
                        with target.open("rb") as source, duplicate.open("xb") as output:
                            shutil.copyfileobj(source, output, BLOCK)
                        if sha(duplicate) != digest:
                            raise ValueError("Restored duplicate hash differs")
                        restored.append(row)
                    seen.add(digest)
            while stream.read(BLOCK):
                pass
            if stream.count != volume["bytes"] or stream.digest.hexdigest() != volume["sha256"]:
                raise ValueError("Full volume digest differs")
        if progress:
            progress({"stage": "volume_restored_and_byte_verified", "volume": volume["name"], "objects": len(seen), "files": len(restored),
                      "logical_bytes_written": sum(r["bytes"] for r in restored)})
    if wanted or len(restored) != len(records):
        raise ValueError("Incomplete layer restore")
    return {"passed": True, "ordinary_files_restored": len(restored), "logical_bytes": sum(r["bytes"] for r in restored),
            "unique_objects_and_volume_hashes_verified": len(seen), "volumes_full_hash_verified": len(meta["volumes"]),
            "superseded_base_versions_preserved": superseded, "wall_seconds": time.monotonic() - started,
            "links_or_permissions_restored_by_this_operation": False, "model_or_scientific_array_loading": False}


def check_files(records, workspace, layout, *, extra_records=None, progress=None):
    validate_rows(records, layout)
    total = 0
    for index, r in enumerate(records, 1):
        path = mapped(workspace, layout, r)
        if not path.is_file() or path.is_symlink() or path.stat().st_size != r["bytes"] or sha(path) != r["sha256"]:
            raise ValueError("Restored file differs: " + r["root"] + ":" + r["path"])
        total += r["bytes"]
        if progress and index % 5000 == 0:
            progress({"stage": "restored_tree_rehashed", "files": index, "bytes": total})
    for r in extra_records or []:
        path = Path(workspace) / safe_relative(r["path"])
        if path.stat().st_size != r["bytes"] or sha(path) != r["sha256"]:
            raise ValueError("Superseded base copy differs")
    return {"passed": True, "ordinary_files_freshly_rehashed": len(records), "bytes_freshly_rehashed": total,
            "superseded_versions_freshly_rehashed": len(extra_records or []), "scientific_or_model_loads": 0}


def apply_links(workspace, layout, link_plan, *, create=False):
    """Recreate only internal relative links; never copy personal-runtime junctions."""
    outcomes = []
    for row in link_plan:
        if row["action"] == "external_dependency_not_recreated":
            outcomes.append({"root": row["root"], "path": row["path"], "state": row["action"]})
            continue
        link = mapped(workspace, layout, row)
        target = mapped(workspace, layout, row["target_asset"])
        relative = os.path.relpath(target, link.parent)
        if not target.exists():
            raise ValueError("Internal link target missing")
        if create:
            if link.exists() or link.is_symlink():
                raise FileExistsError("Link destination already exists")
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(relative, target_is_directory=target.is_dir())
            if os.readlink(link) != relative or link.resolve() != target.resolve():
                raise ValueError("Relative link resolution differs")
        outcomes.append({"root": row["root"], "path": row["path"], "relative_target": relative,
                         "state": "created_and_resolved" if create else "metadata_only_not_created"})
    return outcomes


def project_controls(project_file):
    project_file = Path(project_file).resolve()
    project, parent = load(project_file), project_file.parent
    for item in project["control_files"]:
        path = parent / safe_relative(item["path"])
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise ValueError("Project control mismatch")
    return project, parent


def restore_project(project_file, destination, *, create_links=False, progress=None):
    project, parent = project_controls(project_file)
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError("Destination must be new")
    base = (parent / project["layers"][0]["directory"]).resolve()
    delta = (parent / project["layers"][1]["directory"]).resolve()
    for package, item in zip((base, delta), project["layers"]):
        if sha(package / "PACKAGE.json") != item["package_manifest_sha256"]:
            raise ValueError("Layer manifest binding differs")
    result_base = restore_layer(base, destination, project["layout"], progress=progress)
    result_delta = restore_layer(delta, destination, project["layout"], overlay=True, expected_before=rows(base / "SOURCE_FILES.jsonl"), progress=progress)
    final_records = rows(parent / "FINAL_FILES.jsonl")
    check = check_files(final_records, destination, project["layout"], extra_records=result_delta["superseded_base_versions_preserved"], progress=progress)
    links = apply_links(destination, project["layout"], load(parent / "LINK_PLAN.json"), create=create_links)
    permissions = load(parent / "PERMISSIONS.json")
    applied = 0
    if os.name == "posix":
        for row in final_records:
            path = mapped(destination, project["layout"], row)
            mode = permissions["git_tracked_modes"].get(row["root"] + ":" + row["path"], "100644")
            os.chmod(path, 0o755 if mode == "100755" else 0o644)
            applied += 1
    return {"base": result_base, "delta": result_delta, "fresh_restored_tree_check": check, "links": links,
            "POSIX_file_modes_applied": applied, "server_acceptance_validated": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="operation", required=True)
    c = sub.add_parser("check-tree")
    c.add_argument("--project", type=Path, required=True)
    c.add_argument("--workspace", type=Path, required=True)
    r = sub.add_parser("restore-project")
    r.add_argument("--project", type=Path, required=True)
    r.add_argument("--destination", type=Path, required=True)
    r.add_argument("--create-internal-links", action="store_true")
    a = p.parse_args()
    progress = lambda value: print(json.dumps(value, ensure_ascii=False), flush=True)
    if a.operation == "restore-project":
        result = restore_project(a.project, a.destination, create_links=a.create_internal_links, progress=progress)
    else:
        project, parent = project_controls(a.project)
        result = check_files(rows(parent / "FINAL_FILES.jsonl"), a.workspace, project["layout"], progress=progress)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
