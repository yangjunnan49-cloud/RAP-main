"""Bind the exact existing A5/A7 files for server-side upload verification."""
import hashlib
import json
from pathlib import Path

phase = Path(__file__).resolve().parent
repo = phase.parents[3]
base = repo / ".maintenance-archive/migration"
inventory = json.loads((phase / "BASELINE.json").read_text(encoding="utf-8"))["package_inventory"]
hashes = {}
for relative in ("A5-20261104", "A7-20261104/delta"):
    package = json.loads((base / relative / "PACKAGE.json").read_text(encoding="utf-8"))
    for volume in package["volumes"]:
        hashes[relative + "/" + volume["name"]] = volume["sha256"]
delivery = json.loads((base / "A7-20261104/DELIVERY.json").read_text(encoding="utf-8"))
hashes["A7-20261104/" + delivery["evidence"]["archive"]] = delivery["evidence"]["archive_sha256"]
rows = []
for package, files in inventory.items():
    for row in files:
        path = package + "/" + row["path"]
        sha = row["sha256"] or hashes[path]
        rows.append(dict(path=path, bytes=row["bytes"], sha256=sha))
output = phase / "EXPECTED_UPLOAD.json"
data = dict(files=rows, file_count=len(rows), bytes=sum(r["bytes"] for r in rows),
            delivery_sha256=hashlib.sha256((base / "A7-20261104/DELIVERY.json").read_bytes()).hexdigest())
with output.open("x", encoding="utf-8") as stream:
    json.dump(data, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: data[k] for k in ("file_count", "bytes", "delivery_sha256")}))
