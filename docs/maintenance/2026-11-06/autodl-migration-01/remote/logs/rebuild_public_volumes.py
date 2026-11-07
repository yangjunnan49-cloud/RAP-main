"""Recover exact sealed tar bytes from byte-identical read-only cache members.

Every raw member must match the original A5 SHA256 before being written. Every
tar stream must match its original sealed SHA256 before atomic no-replace
publication. The independent receiving/restoration gates remain mandatory.
No data array interpretation, source authentication, or scientific computation.
"""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import ctypes
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
from threading import Lock
import time
import traceback
import zipfile

ROOT = Path("/root/autodl-tmp/rap-migration-20261106")
PACKAGE = Path("/root/autodl-fs/rap-transfer-20261106/A5-20261104")
STAGING = PACKAGE.parent / ".public-cache-rebuild-20261106"
PUBLIC = Path("/autodl-pub/data/SemanticKITTI/data_odometry_velodyne.zip")
BLOCK = 8 * 1024 * 1024
LOCK = Lock()


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(BLOCK), b""):
            value.update(block)
    return value.hexdigest()


class HashWriter:
    def __init__(self, handle):
        self.handle, self.digest, self.count = handle, hashlib.sha256(), 0

    def write(self, data):
        count = self.handle.write(data)
        if count != len(data):
            raise OSError("Short archive write")
        self.digest.update(data)
        self.count += count
        return count

    def flush(self):
        self.handle.flush()


def append(name, row):
    with LOCK:
        with (ROOT / "logs" / name).open("a", encoding="utf-8") as out:
            out.write(json.dumps(row) + "\n")


def publish(source, target):
    library = ctypes.CDLL(None, use_errno=True)
    function = library.renameat2
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    status = function(-100, os.fsencode(source), -100, os.fsencode(target), 1)
    if status != 0:
        error = ctypes.get_errno()
        if error == 17:
            return False
        raise OSError(error, os.strerror(error))
    return True


def main():
    assert json.loads((ROOT / "PUBLIC_CACHE_PUBLISH_PROBE.json").read_text())["passed"]
    assert sha(PACKAGE / "PACKAGE.json") == "6e46398908c0acdbf0e279559dd662340d397ef4d4b7ce438cb653129eab2552"
    manifest = json.loads((PACKAGE / "PACKAGE.json").read_text())
    assert sha(PACKAGE / "OBJECTS.jsonl") == manifest["objects_manifest_sha256"]
    candidate = json.loads((ROOT / "PUBLIC_CACHE_CANDIDATES.json").read_text())
    assert all(row["matched_original_sha256"] for row in candidate["sample_byte_checks"])
    aliases = candidate["aliases_by_original_sha256"]
    objects = defaultdict(list)
    with (PACKAGE / "OBJECTS.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            objects[row["volume"]].append(row)
    pure = [volume for volume in manifest["volumes"] if all(row["sha256"] in aliases for row in objects[volume["name"]])]
    assert len(pure) == 19
    started = time.monotonic()

    def rebuild(volume):
        target = PACKAGE / volume["name"]
        if target.exists() or target.is_symlink():
            result = dict(volume=volume["name"], publication_skipped=True, reason="Existing native transfer target retained")
            append("public-cache-volumes.jsonl", result)
            return result
        if shutil.disk_usage(PACKAGE.parent).free < volume["bytes"] + 5 * 1024**3:
            raise OSError("Cloud-disk safety reserve would be exhausted")
        temporary = STAGING / (volume["name"] + ".partial")
        count = 0
        with zipfile.ZipFile(PUBLIC) as source, temporary.open("xb") as handle:
            writer = HashWriter(handle)
            with tarfile.open(fileobj=writer, mode="w|", format=tarfile.USTAR_FORMAT, bufsize=BLOCK, copybufsize=BLOCK) as archive:
                for row in objects[volume["name"]]:
                    alias = aliases[row["sha256"]]
                    data = source.read(alias["member"])
                    observed = hashlib.sha256(data).hexdigest()
                    if len(data) != row["bytes"] or observed != row["sha256"]:
                        raise ValueError("Public-cache bytes differ from the original object: " + alias["member"])
                    info = tarfile.TarInfo(row["member"])
                    info.size, info.mode, info.mtime = row["bytes"], 0o600, 0
                    archive.addfile(info, io.BytesIO(data))
                    count += 1
                    append("public-cache-object-checks.jsonl", dict(volume=volume["name"], member=alias["member"],
                           original_sha256=row["sha256"], observed_sha256=observed, bytes=len(data), passed=True))
            writer.flush()
            os.fsync(handle.fileno())
            assert writer.count == volume["bytes"] and writer.digest.hexdigest() == volume["sha256"], "Sealed tar stream differs"
        published = publish(temporary, target)
        result = dict(volume=volume["name"], objects_freshly_hashed=count, bytes=volume["bytes"], sha256=volume["sha256"],
            exact_original_tar_stream_hash_matched=True, published_without_replacing_any_existing_path=published,
            independent_receiver_readback_still_required=True, source_authentication_claimed=False)
        append("public-cache-volumes.jsonl", result)
        print(json.dumps(result), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(rebuild, pure))
    result = dict(completed_utc=datetime.now(timezone.utc).isoformat(), passed=True, public_cache=str(PUBLIC),
        volumes=results, bytes_reconstructed=sum(row.get("bytes", 0) for row in results),
        expected_pure_volumes=19, wall_seconds=time.monotonic()-started,
        public_cache_opened_read_only=True, original_packages_or_data_modified=False,
        dataset_arrays_or_PGC1_partial_results_interpreted=False, source_authentication_or_scientific_qualification_claimed=False)
    (ROOT / "PUBLIC_CACHE_REBUILD.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        (ROOT / "PUBLIC_CACHE_REBUILD_FAILURE.json").write_text(json.dumps(dict(error=repr(exc), traceback=traceback.format_exc()), indent=2) + "\n")
        raise
