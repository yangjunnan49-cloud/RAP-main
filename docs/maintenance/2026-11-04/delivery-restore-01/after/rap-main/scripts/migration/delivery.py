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


def native_absolute(value):
    """Use Windows extended paths so a deeper new workspace preserves long names."""
    path = Path(value).resolve()
    text = str(path)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        text = "\\\\?\\UNC\\" + text[2:] if text.startswith("\\\\") else "\\\\?\\" + text
        path = Path(text)
    return path


def mapped(workspace, layout, row):
    workspace = native_absolute(workspace)
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
    package, workspace = Path(package).resolve(), native_absolute(workspace)
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
        path = native_absolute(workspace) / safe_relative(r["path"])
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


def apply_permissions(workspace, layout, records, directories, permissions):
    """Apply an explicit POSIX policy; it does not reconstruct unknown owners/ACLs."""
    if os.name != "posix":
        return {"applied": False, "files": 0, "directories": 0, "target_owner_or_ACL_certified": False}
    root = native_absolute(workspace)
    for row in records:
        path = mapped(root, layout, row)
        if not path.is_file() or path.is_symlink():
            raise ValueError("Permission target is not an ordinary restored file")
        mode = permissions["git_tracked_modes"].get(row["root"] + ":" + row["path"], "100644")
        if mode not in {"100644", "100755"}:
            raise ValueError("Nonregular Git mode requires separate handling")
        selected = 0o755 if mode == "100755" else 0o644
        os.chmod(path, selected)
        if path.stat().st_mode & 0o777 != selected:
            raise ValueError("POSIX file mode did not persist")
    folders = {root}
    folders.update(mapped(root, layout, row) for row in directories)
    for prefix in layout.values():
        if prefix:
            folder = root / safe_relative(prefix)
            while folder != root:
                folders.add(folder)
                folder = folder.parent
    for folder in sorted(folders, key=lambda p: len(p.parts)):
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("Permission target is not an ordinary directory")
        os.chmod(folder, 0o755)
        if folder.stat().st_mode & 0o777 != 0o755:
            raise ValueError("POSIX directory mode did not persist")
    return {"applied": True, "files": len(records), "directories": len(folders), "target_owner_or_ACL_certified": False}


def restore_project(project_file, destination, *, create_links=False, progress=None):
    project, parent = project_controls(project_file)
    destination = native_absolute(destination)
    if destination.exists():
        raise FileExistsError("Destination must be new")
    base = (parent / project["layers"][0]["directory"]).resolve()
    delta = (parent / project["layers"][1]["directory"]).resolve()
    for package, item in zip((base, delta), project["layers"]):
        if sha(package / "PACKAGE.json") != item["package_manifest_sha256"]:
            raise ValueError("Layer manifest binding differs")
        if item.get("extra_delivery_index_sha256"):
            if sha(package / "DELIVERY_INDEX.json") != item["extra_delivery_index_sha256"]:
                raise ValueError("Base extra-control index differs")
            for row in load(package / "DELIVERY_INDEX.json")["extra_control_files"]:
                path = package / safe_relative(row["path"])
                if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
                    raise ValueError("Base extra-control bytes differ")
    result_base = restore_layer(base, destination, project["layout"], progress=progress)
    result_delta = restore_layer(delta, destination, project["layout"], overlay=True, expected_before=rows(base / "SOURCE_FILES.jsonl"), progress=progress)
    final_records = rows(parent / "FINAL_FILES.jsonl")
    check = check_files(final_records, destination, project["layout"], extra_records=result_delta["superseded_base_versions_preserved"], progress=progress)
    permissions = apply_permissions(destination, project["layout"], final_records, rows(parent / "FINAL_DIRECTORIES.jsonl"), load(parent / "PERMISSIONS.json"))
    links = apply_links(destination, project["layout"], load(parent / "LINK_PLAN.json"), create=create_links)
    return {"base": result_base, "delta": result_delta, "fresh_restored_tree_check": check, "links": links,
            "POSIX_permission_policy": permissions, "server_acceptance_validated": False}


def apply_control_snapshots(source_phase, workspace, layout, control_rows, before_records):
    """Apply declared current controls, preserving each registered old byte version."""
    phase, root = native_absolute(source_phase), native_absolute(workspace)
    before = {(r["root"], r["path"]): r for r in before_records}
    changes, preserved, unchanged = [], [], 0
    if len({(r["root"], r["path"]) for r in control_rows}) != len(control_rows):
        raise ValueError("Duplicate final control identity")
    for row in control_rows:
        source = phase / safe_relative(row["snapshot"])
        if source.stat().st_size != row["bytes"] or sha(source) != row["sha256"]:
            raise ValueError("Final control snapshot differs")
        target = mapped(root, layout, row)
        if target.exists():
            if target.is_symlink() or not target.is_file():
                raise ValueError("Final control target is not an ordinary file")
            digest = sha(target)
            if digest == row["sha256"]:
                unchanged += 1
                continue
            previous = before.get((row["root"], row["path"]))
            if previous is None or digest != previous["sha256"]:
                raise ValueError("Unregistered final-control overwrite")
            old = root / "archives/source-versions/A7-control" / row["root"] / safe_relative(row["path"])
            if old.exists() or not old.resolve().is_relative_to(root):
                raise ValueError("Final-control version target already exists")
            old.parent.mkdir(parents=True, exist_ok=True)
            target.rename(old)
            preserved.append({"path": old.relative_to(root).as_posix(), "bytes": previous["bytes"], "sha256": previous["sha256"],
                              "source_root": row["root"], "source_path": row["path"]})
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as src, target.open("xb") as out:
            shutil.copyfileobj(src, out, BLOCK)
        if sha(target) != row["sha256"]:
            raise ValueError("Final-control copy differs")
        if os.name == "posix":
            os.chmod(target, 0o644)
        changes.append({"root": row["root"], "path": row["path"], "sha256": row["sha256"]})
    return {"written": changes, "already_matching": unchanged, "superseded_versions_preserved": preserved}


def install_evidence(delivery_file, workspace, *, progress=None):
    """Verify/extract the sealed A7 evidence, then apply only declared final controls."""
    delivery_file = Path(delivery_file).resolve()
    delivery, package = load(delivery_file), delivery_file.parent
    evidence = delivery["evidence"]
    manifest_file = package / safe_relative(evidence["manifest"])
    if sha(manifest_file) != evidence["manifest_sha256"]:
        raise ValueError("Evidence manifest binding differs")
    manifest = load(manifest_file)
    expected = {r["path"]: r for r in manifest["files"]}
    if len(expected) != len(manifest["files"]):
        raise ValueError("Duplicate evidence identity")
    root = native_absolute(workspace)
    prefix = safe_relative(evidence["workspace_prefix"])
    seen = set()
    archive_path = package / safe_relative(evidence["archive"])
    with archive_path.open("rb") as handle:
        stream = HashReader(handle)
        with tarfile.open(fileobj=stream, mode="r|", bufsize=BLOCK) as archive:
            for item in archive:
                if not item.isfile() or item.name not in expected or item.name in seen:
                    raise ValueError("Unexpected evidence member")
                row = expected[item.name]
                target = root / prefix / safe_relative(item.name)
                if not target.resolve().is_relative_to(root):
                    raise ValueError("Evidence escapes workspace")
                target.parent.mkdir(parents=True, exist_ok=True)
                reader, digest, size = archive.extractfile(item), hashlib.sha256(), 0
                if target.exists():
                    if not target.is_file() or target.is_symlink() or sha(target) != row["sha256"]:
                        raise ValueError("Existing evidence differs")
                    output = None
                else:
                    output = target.open("xb")
                try:
                    for raw in iter(lambda: reader.read(BLOCK), b""):
                        digest.update(raw)
                        size += len(raw)
                        if output is not None:
                            output.write(raw)
                finally:
                    if output is not None:
                        output.close()
                if size != row["bytes"] or item.size != row["bytes"] or digest.hexdigest() != row["sha256"] or sha(target) != row["sha256"]:
                    raise ValueError("Evidence bytes differ")
                if os.name == "posix":
                    os.chmod(target, 0o644)
                    parent = target.parent
                    while parent != root:
                        os.chmod(parent, 0o755)
                        parent = parent.parent
                seen.add(item.name)
        while stream.read(BLOCK):
            pass
        if stream.count != evidence["archive_bytes"] or stream.digest.hexdigest() != evidence["archive_sha256"]:
            raise ValueError("Whole evidence archive differs")
    if seen != set(expected):
        raise ValueError("Incomplete evidence coverage")
    project_file = package / safe_relative(delivery["project_manifest"])
    if sha(project_file) != delivery["project_manifest_sha256"]:
        raise ValueError("Project manifest binding differs")
    project = load(project_file)
    phase = root / prefix
    control_rows = load(phase / "CURRENT_DOCUMENT_SNAPSHOTS.json") + load(phase / "LATE_GIT_SNAPSHOTS.json")
    applied = apply_control_snapshots(phase, root, project["layout"], control_rows, rows(package / "FINAL_FILES.jsonl"))
    if progress:
        progress({"stage": "sealed_evidence_and_controls_installed", "evidence_files": len(seen), "controls_written": len(applied["written"]), "controls_already_matching": applied["already_matching"]})
    return {"passed": True, "evidence_files_full_bytes_checked": len(seen), "evidence_archive_full_hash_verified": True,
            "final_controls_written": applied["written"], "final_controls_already_matching": applied["already_matching"],
            "superseded_current_versions_preserved": applied["superseded_versions_preserved"],
            "source_originals_changed": False, "server_acceptance_validated": False}


def check_delivery_tree(delivery_file, workspace, *, progress=None):
    delivery_file = Path(delivery_file).resolve()
    delivery = load(delivery_file)
    manifest = delivery_file.parent / safe_relative(delivery["workspace_files_manifest"])
    if sha(manifest) != delivery["workspace_files_manifest_sha256"]:
        raise ValueError("Final workspace manifest differs")
    root, total, count = native_absolute(workspace), 0, 0
    for row in rows(manifest):
        path = root / safe_relative(row["path"])
        if not path.resolve().is_relative_to(root) or not path.is_file() or path.is_symlink() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise ValueError("Final workspace byte check failed: " + row["path"])
        count += 1
        total += row["bytes"]
        if progress and count % 5000 == 0:
            progress({"stage": "final_delivery_tree_rehashed", "files": count, "bytes": total})
    return {"passed": True, "files_freshly_rehashed": count, "bytes_freshly_rehashed": total, "server_acceptance_validated": False}


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
    d = sub.add_parser("restore-delivery")
    d.add_argument("--delivery", type=Path, required=True)
    d.add_argument("--destination", type=Path, required=True)
    d.add_argument("--create-internal-links", action="store_true")
    v = sub.add_parser("check-delivery-tree")
    v.add_argument("--delivery", type=Path, required=True)
    v.add_argument("--workspace", type=Path, required=True)
    e = sub.add_parser("install-evidence")
    e.add_argument("--delivery", type=Path, required=True)
    e.add_argument("--workspace", type=Path, required=True)
    a = p.parse_args()
    progress = lambda value: print(json.dumps(value, ensure_ascii=False), flush=True)
    if a.operation == "restore-delivery":
        release = load(a.delivery)
        project_path = a.delivery.resolve().parent / safe_relative(release["project_manifest"])
        if sha(project_path) != release["project_manifest_sha256"]:
            raise ValueError("Project manifest binding differs")
        project_result = restore_project(project_path, a.destination, create_links=a.create_internal_links, progress=progress)
        evidence_result = install_evidence(a.delivery, a.destination, progress=progress)
        result = {"project": project_result, "evidence": evidence_result, "server_acceptance_validated": False}
    elif a.operation == "install-evidence":
        result = install_evidence(a.delivery, a.workspace, progress=progress)
    elif a.operation == "check-delivery-tree":
        result = check_delivery_tree(a.delivery, a.workspace, progress=progress)
    elif a.operation == "restore-project":
        result = restore_project(a.project, a.destination, create_links=a.create_internal_links, progress=progress)
    else:
        project, parent = project_controls(a.project)
        result = check_files(rows(parent / "FINAL_FILES.jsonl"), a.workspace, project["layout"], progress=progress)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
