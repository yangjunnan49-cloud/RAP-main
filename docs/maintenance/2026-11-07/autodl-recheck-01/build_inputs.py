"""Freeze a local, layered expectation for the independent server recheck."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
OLD = REPO / "docs/maintenance/2026-11-06/autodl-migration-01"
PACKAGES = REPO / ".maintenance-archive/migration"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

uploads = read(OLD / "EXPECTED_UPLOAD.json")
assert len(uploads["files"]) == 589
file_pin = next(r for r in uploads["files"] if r["path"] == "A7-20261104/DELIVERY_FILES.jsonl")
source = (PACKAGES / "A7-20261104/DELIVERY_FILES.jsonl").read_bytes()
assert digest(source) == file_pin["sha256"]
tree = {r["path"]: r for r in map(json.loads, source.splitlines())}
assert len(tree) == 112972
control_raw = (PACKAGES / "A8-20261106/CONTROL.json").read_bytes()
assert digest(control_raw) == "7027a69281873f069e0492ca19b98ef4896731a57e473919b670a27abfc70034"
control = json.loads(control_raw)
for row in control["files"]:
    if row["before_sha256"]:
        before = tree[row["path"]]
        assert before["sha256"] == row["before_sha256"]
        old_path = "archives/source-versions/A8-control/" + row["path"]
        tree[old_path] = dict(before, path=old_path, role="A8_superseded_bytes")
    tree[row["path"]] = dict(row, role="A8_control")
authority_raw = (OLD / "AUTHORITY_PROOF.json").read_bytes()
assert digest(authority_raw) == "5a7d5ab7d56787cc722801352c407a7b2cc135e7fae44bbd10c17f8ada12792f"
authority = json.loads(authority_raw)
layout = control["layout"]
local_roots = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM",
               "reports": REPO.parent / "RAP-SLAM-report", "workspace-root": REPO.parent}
local_results = []
for row in authority["current_files"]:
    target = "/".join(p for p in (layout[row["root"]], row["path"]) if p)
    tree[target] = dict(row, path=target, role="A8_final_authority")
    data = (local_roots[row["root"]] / row["path"]).read_bytes()
    local_results.append(dict(root=row["root"], path=row["path"],
        observed_sha256=digest(data), matches=digest(data) == row["sha256"]))
close_raw = (OLD / "CLOSEOUT.json").read_bytes()
assert digest(close_raw) == "5f71a2f2c8cdb936d4cf001a1ffd96ae3e9eeb613a34cb049dc05f961259b503"
close = json.loads(close_raw)
prefix = control["phase_prefix"]
for row in close["files"]:
    target = prefix + "/closeout/" + row["path"]
    tree[target] = dict(row, path=target, role="A8_late_evidence")
    if row["path"] == "HANDOFF_CN.md":
        tree[prefix + "/HANDOFF_CN.md"] = dict(row, path=prefix + "/HANDOFF_CN.md", role="A8_handoff")
receipt = (OLD / "LATE_EVIDENCE_RECEIPT.json").read_bytes()
tree[prefix + "/LATE_EVIDENCE_RECEIPT.json"] = dict(path=prefix + "/LATE_EVIDENCE_RECEIPT.json",
    bytes=len(receipt), sha256=digest(receipt), role="A8_late_evidence_receipt")
tree[prefix + "/AUTHORITY_PROOF.json"] = dict(path=prefix + "/AUTHORITY_PROOF.json",
    bytes=len(authority_raw), sha256=digest(authority_raw), role="A8_authority_manifest")
tree_path = OUT / "EXPECTED_TREE.jsonl.gz"
with tree_path.open("xb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
    for key in sorted(tree):
        row = tree[key]
        stream.write((json.dumps({k: row[k] for k in ("path", "bytes", "sha256", "role")}, ensure_ascii=False) + "\n").encode())
package_rows = list(uploads["files"])
for folder, names in (("A8-20261106", ("CONTROL.json", "control.tar.gz")),
                      ("A8-closeout-20261106", ("CLOSEOUT.json", "closeout.tar.gz", "ACCEPTANCE.json"))):
    for name in names:
        path = PACKAGES / folder / name
        data = (OLD / "LATE_EVIDENCE_RECEIPT.json").read_bytes() if name == "ACCEPTANCE.json" else path.read_bytes()
        package_rows.append(dict(path=folder + "/" + name, bytes=len(data), sha256=digest(data)))
assets = read(OLD / "remote-final/ENVIRONMENT_ASSETS_PRESERVED.json")
for row in assets["files"]:
    package_rows.append(dict(row, path="A8-environment-20261106/" + row["path"]))
pins = dict(created_utc=datetime.now(timezone.utc).isoformat(), expected_tree_sha256=digest(tree_path.read_bytes()),
    expected_tree_files=len(tree), expected_tree_bytes=sum(row["bytes"] for row in tree.values()),
    packages=package_rows, authority=authority, layout=layout,
    links=read(PACKAGES / "A7-20261104/LINK_PLAN.json"),
    gtsam=read(OLD / "remote-final/GTSAM_METADATA_REPAIR.json")["unchanged_members"],
    native_extension_sha256="64398968ef32bf2d35b77af3401f37043f034866ee1b38c7e24e19f6179ca37d",
    gpu_harness_sha256=digest((OLD / "gpu_model_probe_v2.py").read_bytes()),
    cpu_harness_sha256=digest((REPO / "scripts/environment/cpu_probe.py").read_bytes()),
    smoke_inputs=read(OLD / "SMOKE_INPUTS.json"),
    source_package_counts=dict(A5_A7=589, A8=2, closeout=3, environment_assets=len(assets["files"])))
save("PINS.json", pins)
save("LOCAL_AUTHORITY_READBACK.json", dict(files=83, all_match=all(row["matches"] for row in local_results), files_checked=local_results))
save("AUTHORIZATION.json", dict(date_local="2026-11-07", timezone="Asia/Shanghai",
    owner_request="登录服务器，再次验收校核迁移内容", scope="Full byte rehash, links and bounded engineering acceptance",
    original_assets_or_old_receipts_overwritten=False, training_or_new_research=False))
shutil.copyfile(OLD / "gpu_model_probe_v2.py", OUT / "gpu_model_probe.py")
print(json.dumps(dict(files=pins["expected_tree_files"], bytes=pins["expected_tree_bytes"],
    package_files=len(package_rows), compressed_manifest_bytes=tree_path.stat().st_size,
    pins_sha256=digest((OUT / "PINS.json").read_bytes()))))
