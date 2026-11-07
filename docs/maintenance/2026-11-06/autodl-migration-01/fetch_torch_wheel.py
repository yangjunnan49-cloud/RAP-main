"""Fetch the official hash-pinned Torch wheel with bounded HTTP range workers."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import urllib.request

ROOT = Path("/root/autodl-tmp/rap-migration-20261106")
SOURCE = json.loads((ROOT / "TORCH_WHEEL_SOURCE.json").read_text())
TOTAL = int(SOURCE["content_range"].rsplit("/", 1)[1])
PART = 32 * 1024 * 1024
DEST = ROOT / "downloads"
DEST.mkdir(exist_ok=True)
PARTS = DEST / "torch-parts"
PARTS.mkdir(exist_ok=True)


def fetch(index):
    start, end = index * PART, min(TOTAL, (index + 1) * PART) - 1
    dest = PARTS / f"part-{index:04d}"
    size = end - start + 1
    if dest.exists() and dest.stat().st_size == size:
        return dest
    for attempt in range(3):
        try:
            request = urllib.request.Request(SOURCE["url"], headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(request, timeout=60) as response:
                assert response.status == 206
                assert response.headers["Content-Range"] == f"bytes {start}-{end}/{TOTAL}"
                temporary = dest.with_suffix(".partial")
                with temporary.open("wb") as out:
                    while block := response.read(256 * 1024):
                        out.write(block)
                assert temporary.stat().st_size == size
                temporary.replace(dest)
            print(json.dumps(dict(part=index, bytes=size, complete=True)), flush=True)
            return dest
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def main():
    started = time.monotonic()
    count = (TOTAL + PART - 1) // PART
    with ThreadPoolExecutor(max_workers=8) as pool:
        parts = list(pool.map(fetch, range(count)))
    wheel = DEST / "torch-2.7.0+cu128-cp310-cp310-manylinux_2_28_x86_64.whl"
    value = hashlib.sha256()
    with wheel.open("xb") as out:
        for part in parts:
            with part.open("rb") as source:
                while block := source.read(4 * 1024 * 1024):
                    value.update(block)
                    out.write(block)
    assert wheel.stat().st_size == TOTAL and value.hexdigest() == SOURCE["sha256"]
    (ROOT / "TORCH_RANGED_DOWNLOAD.json").write_text(json.dumps(dict(passed=True,
        completed_utc=datetime.now(timezone.utc).isoformat(), url=SOURCE["url"],
        sha256=value.hexdigest(), bytes=TOTAL, workers=8, path=str(wheel),
        wall_seconds=time.monotonic() - started), indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        (ROOT / "TORCH_RANGED_DOWNLOAD_FAILURE.json").write_text(json.dumps(dict(
            error=repr(exc), traceback=traceback.format_exc()), indent=2) + "\n")
        raise
