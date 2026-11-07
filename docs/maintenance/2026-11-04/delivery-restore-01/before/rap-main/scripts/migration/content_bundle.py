#!/usr/bin/env python3
"""Content-addressed tar volumes with raw-byte verification and safe partial restore."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import time

BLOCK = 8 * 1024 * 1024


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_rows(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(BLOCK), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def safe_relative(value):
    if not isinstance(value, str) or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Unsafe relative source path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or not parsed.parts or any(p in {".", ".."} for p in value.split("/")):
        raise ValueError("Unsafe relative source path: " + value)
    return parsed


def validate_records(records):
    seen = set()
    sizes = {}
    for row in records:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", row["root"]):
            raise ValueError("Unsafe source root ID")
        safe_relative(row["path"])
        key = (row["root"], row["path"])
        if key in seen:
            raise ValueError("Duplicate source identity")
        seen.add(key)
        if not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) or not isinstance(row["bytes"], int) or row["bytes"] < 0:
            raise ValueError("Invalid checksum or file size")
        if row["sha256"] in sizes and sizes[row["sha256"]] != row["bytes"]:
            raise ValueError("Same digest with inconsistent sizes")
        sizes[row["sha256"]] = row["bytes"]


def source_stat(path, row):
    value = path.lstat()
    if getattr(value, "st_file_attributes", 0) & 0x400 or path.is_symlink() or not path.is_file():
        raise ValueError("Source is no longer an ordinary file: " + str(path))
    if value.st_size != row["bytes"] or ("mtime_ns" in row and value.st_mtime_ns != row["mtime_ns"]):
        raise ValueError("Source changed since inventory: " + str(path))
    return value


class HashIO:
    def __init__(self, handle):
        self.handle = handle
        self.digest = hashlib.sha256()
        self.count = 0

    def read(self, size=-1):
        raw = self.handle.read(size)
        self.digest.update(raw)
        self.count += len(raw)
        return raw

    def write(self, raw):
        written = self.handle.write(raw)
        if written != len(raw):
            raise OSError("Short archive write")
        self.digest.update(raw)
        self.count += written
        return written

    def flush(self):
        self.handle.flush()


def build(inventory, package, max_volume_bytes=4 * 1024**3, progress=None):
    inventory, package = Path(inventory).resolve(), Path(package).resolve()
    baseline = read_json(inventory / "BASELINE.json")
    records = read_rows(inventory / "SOURCE_FILES.jsonl")
    validate_records(records)
    roots = {key: Path(value).resolve() for key, value in baseline["source_roots"].items()}
    if package.exists():
        raise FileExistsError("Package destination already exists; no overwrite or implicit resume")
    if max_volume_bytes < 32768:
        raise ValueError("Volume limit too small")
    unique_bytes = sum({r["sha256"]: r["bytes"] for r in records}.values())
    if shutil.disk_usage(package.parent if package.parent.exists() else inventory).free < unique_bytes + 1024**3:
        raise OSError("Insufficient space for unique payload and safety reserve")
    package.mkdir(parents=True)
    controls = ("SOURCE_FILES.jsonl", "SOURCE_DIRECTORIES.jsonl", "SOURCE_LINKS.jsonl", "SOURCE_LINKS_RAW.json", "BASELINE.json")
    for name in controls:
        shutil.copyfile(inventory / name, package / name)
    objects, volumes, verified = {}, [], []
    handle, stream, archive, partial = None, None, None, None
    members = []
    estimated = 0
    started = time.monotonic()

    def open_volume():
        nonlocal handle, stream, archive, partial, members, estimated
        name = f"payload-{len(volumes) + 1:04d}.tar"
        partial = package / (name + ".partial")
        handle = partial.open("xb")
        stream = HashIO(handle)
        archive = tarfile.open(fileobj=stream, mode="w|", format=tarfile.USTAR_FORMAT, bufsize=BLOCK, copybufsize=BLOCK)
        members, estimated = [], 0
        return name

    def close_volume():
        nonlocal handle, stream, archive, partial
        if archive is None:
            return
        archive.close()
        stream.flush()
        os.fsync(handle.fileno())
        handle.close()
        name = partial.name.removesuffix(".partial")
        target = package / name
        if target.parent != package or target.exists():
            raise ValueError("Unsafe archive finalization")
        partial.rename(target)
        volumes.append({"name": name, "bytes": stream.count, "sha256": stream.digest.hexdigest(), "objects": len(members)})
        if stream.count > max_volume_bytes:
            raise ValueError("Final tar exceeds declared volume limit")
        with (package / "COMPLETED_VOLUMES.jsonl").open("a", encoding="utf-8") as output:
            output.write(json.dumps(volumes[-1]) + "\n")
        if progress:
            progress({"stage": "volume_complete", **volumes[-1]})
        handle, stream, archive, partial = None, None, None, None

    volume_name = None
    try:
        with (package / "OBJECTS.jsonl").open("x", encoding="utf-8") as object_log, (package / "SOURCE_BYTE_CHECKS.jsonl").open("x", encoding="utf-8") as source_log:
            for index, row in enumerate(records):
                path = roots[row["root"]].joinpath(*safe_relative(row["path"]).parts)
                before = source_stat(path, row)
                store = row["sha256"] not in objects
                padded = 512 + (row["bytes"] + 511) // 512 * 512
                archive_bytes = lambda member_bytes: ((member_bytes + 1024 + 10239) // 10240) * 10240
                if store and archive_bytes(padded) > max_volume_bytes:
                    raise ValueError("Single object exceeds volume limit: " + row["root"] + ":" + row["path"])
                if store and archive is not None and archive_bytes(estimated + padded) > max_volume_bytes:
                    close_volume()
                if store and archive is None:
                    volume_name = open_volume()
                with path.open("rb") as source:
                    stat = os.fstat(source.fileno())
                    if stat.st_size != before.st_size or stat.st_ino != before.st_ino:
                        raise ValueError("Source identity changed while opening")
                    reader = HashIO(source)
                    if store:
                        member = "objects/" + row["sha256"]
                        info = tarfile.TarInfo(member)
                        info.size, info.mode, info.mtime = row["bytes"], 0o600, 0
                        archive.addfile(info, reader)
                    else:
                        while reader.read(BLOCK):
                            pass
                    # Covers growth as well as an exact expected-length read by tarfile.
                    if reader.read(1):
                        raise ValueError("Source grew during read")
                    if reader.count != row["bytes"] or reader.digest.hexdigest() != row["sha256"]:
                        raise ValueError("Source content does not match inventory: " + str(path))
                after = source_stat(path, row)
                if after.st_ino != before.st_ino:
                    raise ValueError("Source identity changed after read")
                if store:
                    obj = {"sha256": row["sha256"], "bytes": row["bytes"], "volume": volume_name,
                           "member": member, "canonical_source": row["root"] + ":" + row["path"]}
                    objects[row["sha256"]] = obj
                    members.append(row["sha256"])
                    estimated += padded
                    object_log.write(json.dumps(obj, ensure_ascii=False) + "\n")
                item = {"root": row["root"], "path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"], "fresh_raw_byte_match": True, "stored_new_object": store}
                source_log.write(json.dumps(item, ensure_ascii=False) + "\n")
                verified.append(item)
                if progress and index % 1000 == 0:
                    progress({"stage": "source_bytes_checked", "files": index + 1, "total_files": len(records), "objects": len(objects), "volumes_complete": len(volumes), "seconds": round(time.monotonic() - started, 1)})
            close_volume()
        result = {"schema_version": 1, "format": "USTAR_RAW_SHA256_OBJECTS", "complete": True,
                  "created_utc": datetime.now(timezone.utc).isoformat(), "source_manifest_sha256": sha(package / "SOURCE_FILES.jsonl"),
                  "objects_manifest_sha256": sha(package / "OBJECTS.jsonl"), "source_byte_checks_sha256": sha(package / "SOURCE_BYTE_CHECKS.jsonl"),
                  "source_files": len(records), "source_files_fresh_byte_verified": len(verified), "logical_bytes": sum(r["bytes"] for r in records),
                  "unique_objects": len(objects), "unique_payload_bytes": sum(r["bytes"] for r in objects.values()),
                  "max_volume_bytes": max_volume_bytes, "volumes": volumes, "links_followed": False,
                  "control_sha256": {name: sha(package / name) for name in controls},
                  "PGC1_results_semantically_read": False, "full_link_or_target_server_restore_validated": False}
        write_json(package / "PACKAGE.json", result)
        return result
    except BaseException as exc:
        if archive is not None:
            try:
                archive.close()
            except BaseException:
                pass
        if handle is not None and not handle.closed:
            handle.close()
        failure = {"complete": False, "error": repr(exc), "source_files_verified_before_failure": len(verified), "completed_volumes": volumes,
                   "partial_files_retained": [p.name for p in package.glob("*.partial")], "originals_modified_or_removed": False}
        with (package / "BUILD_FAILURE.json").open("x", encoding="utf-8") as output:
            json.dump(failure, output, ensure_ascii=False, indent=2)
        raise


def verify(package, progress=None):
    package = Path(package).resolve()
    meta = read_json(package / "PACKAGE.json")
    if meta.get("complete") is not True:
        raise ValueError("Incomplete package")
    for name, digest in meta["control_sha256"].items():
        safe_relative(name)
        if sha(package / name) != digest:
            raise ValueError("Control manifest digest mismatch: " + name)
    records = read_rows(package / "SOURCE_FILES.jsonl")
    validate_records(records)
    object_rows = read_rows(package / "OBJECTS.jsonl")
    objects = {r["sha256"]: r for r in object_rows}
    if len(objects) != len(object_rows) or set(objects) != {r["sha256"] for r in records}:
        raise ValueError("Object coverage or uniqueness mismatch")
    for name, key in (("SOURCE_FILES.jsonl", "source_manifest_sha256"), ("OBJECTS.jsonl", "objects_manifest_sha256"), ("SOURCE_BYTE_CHECKS.jsonl", "source_byte_checks_sha256")):
        if sha(package / name) != meta[key]:
            raise ValueError("Package metadata digest mismatch: " + name)
    checked_sources = read_rows(package / "SOURCE_BYTE_CHECKS.jsonl")
    expected = {(r["root"], r["path"]): (r["sha256"], r["bytes"]) for r in records}
    observed = {(r["root"], r["path"]): (r["sha256"], r["bytes"]) for r in checked_sources if r["fresh_raw_byte_match"] is True}
    if len(checked_sources) != len(expected) or expected != observed:
        raise ValueError("Fresh source check coverage mismatch")
    seen = set()
    for volume in meta["volumes"]:
        if not re.fullmatch(r"payload-[0-9]{4}\.tar", volume["name"]):
            raise ValueError("Unsafe volume filename")
        path = package / volume["name"]
        if path.stat().st_size != volume["bytes"]:
            raise ValueError("Volume size mismatch")
        with path.open("rb") as handle:
            hashed = HashIO(handle)
            with tarfile.open(fileobj=hashed, mode="r|", bufsize=BLOCK) as archive:
                for info in archive:
                    if not info.isfile() or not re.fullmatch(r"objects/[0-9a-f]{64}", info.name):
                        raise ValueError("Unexpected tar member")
                    digest = info.name.split("/")[1]
                    if digest in seen or digest not in objects:
                        raise ValueError("Duplicate or unknown tar object")
                    obj = objects[digest]
                    if obj["volume"] != volume["name"] or obj["member"] != info.name or obj["bytes"] != info.size:
                        raise ValueError("Tar/object manifest mismatch")
                    source = archive.extractfile(info)
                    value, size = hashlib.sha256(), 0
                    for raw in iter(lambda: source.read(BLOCK), b""):
                        value.update(raw)
                        size += len(raw)
                    if value.hexdigest() != digest or size != info.size:
                        raise ValueError("Object payload digest mismatch")
                    seen.add(digest)
            while hashed.read(BLOCK):
                pass
            if hashed.count != volume["bytes"] or hashed.digest.hexdigest() != volume["sha256"]:
                raise ValueError("Volume digest mismatch")
        if progress:
            progress({"stage": "volume_verified", "name": volume["name"], "objects_verified": len(seen), "total_objects": len(objects)})
    if seen != set(objects):
        raise ValueError("Object payload coverage incomplete")
    return {"passed": True, "source_files": len(records), "unique_objects_verified": len(seen), "volumes_verified": len(meta["volumes"]),
            "logical_bytes": meta["logical_bytes"], "unique_payload_bytes": meta["unique_payload_bytes"], "links_recreated": False, "server_restore_validated": False}


def restore_files(package, destination, root=None, prefix=None, max_bytes=None):
    """Restore selected regular files only; links require separate A7 reconstruction."""
    package, destination = Path(package).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError("Restore destination must be new")
    meta = read_json(package / "PACKAGE.json")
    if meta.get("complete") is not True:
        raise ValueError("Incomplete package")
    if sha(package / "SOURCE_FILES.jsonl") != meta["source_manifest_sha256"] or sha(package / "OBJECTS.jsonl") != meta["objects_manifest_sha256"]:
        raise ValueError("Restore metadata digest mismatch")
    records = read_rows(package / "SOURCE_FILES.jsonl")
    validate_records(records)
    selected = [r for r in records if (root is None or r["root"] == root) and (prefix is None or r["path"].startswith(prefix))]
    if max_bytes is not None:
        picked, total = [], 0
        for row in selected:
            if total + row["bytes"] <= max_bytes:
                picked.append(row)
                total += row["bytes"]
        selected = picked
    objects = {r["sha256"]: r for r in read_rows(package / "OBJECTS.jsonl")}
    wanted = {}
    for row in selected:
        wanted.setdefault(row["sha256"], []).append(row)
    destination.mkdir(parents=True)
    restored = []
    for volume in meta["volumes"]:
        if not any(objects[d]["volume"] == volume["name"] for d in wanted):
            continue
        if not re.fullmatch(r"payload-[0-9]{4}\.tar", volume["name"]):
            raise ValueError("Unsafe volume name")
        with tarfile.open(package / volume["name"], mode="r|", bufsize=BLOCK) as archive:
            for info in archive:
                if not info.isfile() or not re.fullmatch(r"objects/[0-9a-f]{64}", info.name):
                    raise ValueError("Unsafe archive member")
                digest = info.name.split("/")[1]
                if digest not in wanted:
                    continue
                rows = wanted.pop(digest)
                expected_obj = objects[digest]
                if info.size != expected_obj["bytes"] or expected_obj["volume"] != volume["name"]:
                    raise ValueError("Restore object manifest mismatch")
                first = rows[0]
                target = destination / first["root"] / Path(*safe_relative(first["path"]).parts)
                if not target.resolve().is_relative_to(destination):
                    raise ValueError("Restore path escapes destination")
                target.parent.mkdir(parents=True, exist_ok=True)
                reader, value, count = archive.extractfile(info), hashlib.sha256(), 0
                with target.open("xb") as output:
                    for raw in iter(lambda: reader.read(BLOCK), b""):
                        output.write(raw)
                        value.update(raw)
                        count += len(raw)
                if value.hexdigest() != digest or count != first["bytes"]:
                    raise ValueError("Restored payload digest mismatch")
                restored.append(first)
                for row in rows[1:]:
                    duplicate = destination / row["root"] / Path(*safe_relative(row["path"]).parts)
                    if not duplicate.resolve().is_relative_to(destination):
                        raise ValueError("Restore path escapes destination")
                    duplicate.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("rb") as source, duplicate.open("xb") as output:
                        shutil.copyfileobj(source, output, BLOCK)
                    if sha(duplicate) != digest:
                        raise ValueError("Restored duplicate digest mismatch")
                    restored.append(row)
    if wanted:
        raise ValueError("Missing restored objects")
    return {"restored_regular_files": len(restored), "bytes": sum(r["bytes"] for r in restored), "links_recreated": False,
            "mode_permission_or_full_target_restore_validated": False, "destination": str(destination)}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    b = sub.add_parser("build")
    b.add_argument("--inventory", type=Path, required=True)
    b.add_argument("--package", type=Path, required=True)
    b.add_argument("--volume-bytes", type=int, default=4 * 1024**3)
    v = sub.add_parser("verify")
    v.add_argument("--package", type=Path, required=True)
    r = sub.add_parser("restore-files")
    r.add_argument("--package", type=Path, required=True)
    r.add_argument("--destination", type=Path, required=True)
    r.add_argument("--root")
    r.add_argument("--prefix")
    r.add_argument("--max-bytes", type=int)
    args = p.parse_args()
    progress = lambda data: print(json.dumps(data, ensure_ascii=False), flush=True)
    if args.action == "build":
        result = build(args.inventory, args.package, args.volume_bytes, progress)
    elif args.action == "verify":
        result = verify(args.package, progress)
    else:
        result = restore_files(args.package, args.destination, args.root, args.prefix, args.max_bytes)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
