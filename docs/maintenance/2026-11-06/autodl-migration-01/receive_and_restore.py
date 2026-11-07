"""Wait for the sealed upload, hash it, then restore to a new Linux workspace.

No credential handling, installation, model, data interpretation, or research.
The authoritative A7 recovery implementation is executed only after its hash
and every other package file have matched the local sealed inputs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import time
import traceback


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def member(root, relative):
    name = PurePosixPath(relative)
    if name.is_absolute() or ".." in name.parts or "\\" in relative or not name.parts:
        raise ValueError("Unsafe expected path")
    path = root.joinpath(*name.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Expected path escapes transfer root")
    return path


def wait_upload(expected, transfer, receipts, timeout):
    verified, previous = {}, {}
    start = time.monotonic()
    rows = expected["files"]
    while True:
        waiting, received = [], 0
        for row in rows:
            path = member(transfer, row["path"])
            if not path.exists():
                waiting.append(row["path"])
                continue
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Uploaded member is not an ordinary file: " + row["path"])
            received += min(info.st_size, row["bytes"])
            signature = (info.st_size, info.st_mtime_ns)
            if info.st_size > row["bytes"]:
                raise ValueError("Uploaded member exceeds sealed size: " + row["path"])
            if verified.get(row["path"]) == signature:
                continue
            # A stable complete size across two polls avoids hashing an open upload.
            if info.st_size != row["bytes"] or previous.get(row["path"]) != signature:
                previous[row["path"]] = signature
                waiting.append(row["path"])
                continue
            if sha(path) != row["sha256"]:
                raise ValueError("Uploaded SHA256 differs: " + row["path"])
            verified[row["path"]] = signature
        status = dict(updated_utc=utc(), stage="WAITING_FOR_SEALED_UPLOAD",
                      verified_files=len(verified), expected_files=len(rows),
                      received_bytes_by_sealed_sizes=received, expected_bytes=expected["bytes"],
                      waiting_files=len(waiting), waiting_sample=waiting[:8])
        save(receipts / "STATUS.json", status)
        if not waiting:
            result = dict(passed=True, completed_utc=utc(), files=len(rows), bytes=expected["bytes"],
                          delivery_sha256=expected["delivery_sha256"], all_file_sha256_checked=True)
            save(receipts / "UPLOAD_VERIFIED.json", result)
            return result
        if time.monotonic() - start > timeout:
            raise TimeoutError("Sealed upload did not complete within the bounded wait")
        time.sleep(30)


def posix_check(package, workspace):
    project = json.loads((package / "PROJECT.json").read_text(encoding="utf-8"))
    links = json.loads((package / "LINK_PLAN.json").read_text(encoding="utf-8"))
    internal, skipped = 0, 0
    for row in links:
        path = workspace / project["layout"][row["root"]] / row["path"]
        if row["action"] == "relative_internal":
            assert path.is_symlink() and os.readlink(path) == row["relative_target"], str(path)
            target = workspace / project["layout"][row["target_asset"]["root"]] / row["target_asset"]["path"]
            assert path.resolve() == target.resolve() and target.exists(), str(path)
            internal += 1
        else:
            assert not os.path.lexists(path), str(path)
            skipped += 1
    checked, owners, bad_modes = 0, set(), []
    with (package / "DELIVERY_FILES.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            path = member(workspace, row["path"])
            info = path.lstat()
            checked += 1
            owners.add((info.st_uid, info.st_gid))
            if stat.S_IMODE(info.st_mode) != 0o644:
                bad_modes.append(dict(path=row["path"], mode=oct(stat.S_IMODE(info.st_mode))))
    assert internal == 25 and skipped == 2
    assert not bad_modes, bad_modes[:10]
    return dict(passed=True, ordinary_file_modes_checked=checked, ordinary_mode_policy="0644",
                observed_uid_gid=sorted(owners), internal_relative_links=internal,
                external_personal_junctions_absent=skipped, original_owner_or_ACL_authenticated=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--transfer", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--receipts", required=True, type=Path)
    parser.add_argument("--wait-hours", type=float, default=48)
    args = parser.parse_args()
    args.receipts.mkdir(parents=True, exist_ok=True)
    if (args.receipts / "STARTED.json").exists():
        parser.error("This receipt directory has already been used")
    if os.path.lexists(args.workspace):
        parser.error("Destination must not already exist")
    save(args.receipts / "STARTED.json", dict(started_utc=utc(), pid=os.getpid(),
         workspace=str(args.workspace), transfer=str(args.transfer), credentials_persisted=False,
         research_or_training=False))
    try:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        wait_upload(expected, args.transfer, args.receipts, args.wait_hours * 3600)
        package = args.transfer / "A7-20261104"
        assert sha(package / "DELIVERY.json") == expected["delivery_sha256"]
        sys.path.insert(0, str(package / "tools"))
        spec = importlib.util.spec_from_file_location("sealed_delivery", package / "tools/delivery.py")
        delivery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(delivery)

        def progress(row):
            print(json.dumps(dict(updated_utc=utc(), **row)), flush=True)
            save(args.receipts / "STATUS.json", dict(updated_utc=utc(), **row))

        project = delivery.restore_project(package / "PROJECT.json", args.workspace,
                                           create_links=True, progress=progress)
        evidence = delivery.install_evidence(package / "DELIVERY.json", args.workspace, progress=progress)
        save(args.receipts / "RESTORE.json", dict(project=project, evidence=evidence))
        final = delivery.check_delivery_tree(package / "DELIVERY.json", args.workspace, progress=progress)
        save(args.receipts / "FINAL_TREE_CHECK.json", final)
        filesystem = posix_check(package, args.workspace)
        save(args.receipts / "POSIX_CHECK.json", filesystem)
        result = dict(completed_utc=utc(), actual_server_file_restore_and_rehash_passed=True,
                      final_tree=final, filesystem=filesystem, environment_validated=False,
                      model_or_training_validated=False, original_local_assets_changed=False)
        save(args.receipts / "ACCEPTANCE.json", result)
        save(args.receipts / "STATUS.json", dict(updated_utc=utc(), stage="FILE_MIGRATION_ACCEPTED"))
    except BaseException as exc:
        save(args.receipts / "FAILURE.json", dict(failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc()))
        raise


if __name__ == "__main__":
    main()
