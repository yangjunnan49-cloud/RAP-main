"""Join logical bundles to completed payload volumes and publish portable metadata."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_checked(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists() or sha(target) == sha(source), target
    if not target.exists():
        shutil.copyfile(source, target)
    assert sha(target) == sha(source)


def main():
    baseline = load(PHASE / "BASELINE.json")
    package = Path(baseline["package_destination"])
    meta = load(package / "PACKAGE.json")
    verified = load(PHASE / "ARCHIVE_VERIFY.json")
    assert meta["complete"] and verified["passed"] and verified["unique_objects_verified"] == meta["unique_objects"]
    assert meta["source_files_fresh_byte_verified"] == baseline["ordinary_files"]
    objects = {r["sha256"]: r for r in rows(package / "OBJECTS.jsonl")}
    units = rows(PHASE / "BUNDLES.jsonl")
    assert all(r["package_volumes"] is None for r in units), "Bundle catalog already finalized"
    copy_checked(PHASE / "BUNDLES.jsonl", PHASE / "BUNDLES_BEFORE_VOLUME_JOIN.jsonl")
    linked = []
    for unit in units:
        members = rows(PHASE / unit["member_manifest"])
        ids = {r["sha256"] for r in members}
        assert ids <= set(objects)
        assert len(members) == unit["files"] and sum(r["bytes"] for r in members) == unit["logical_bytes"]
        unit["package_volumes"] = sorted({objects[key]["volume"] for key in ids})
        unit["unique_referenced_objects"] = len(ids)
        unit["unique_referenced_payload_bytes"] = sum(objects[key]["bytes"] for key in ids)
        unit["member_manifest_raw_bytes_and_payloads_verified"] = True
        linked.append(unit)
    assert sum(r["files"] for r in linked) == baseline["ordinary_files"]
    assert {v for r in linked for v in r["package_volumes"]} == {r["name"] for r in meta["volumes"]}
    (PHASE / "BUNDLES.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in linked), encoding="utf-8")
    for name in ("BUNDLES.jsonl", "DATASETS.json", "MODELS.json", "SOURCE_CLAIMS.json", "CATALOG_SUMMARY.json", "ARCHIVE_VERIFY.json"):
        copy_checked(PHASE / name, package / "metadata" / name)
    for path in sorted((PHASE / "bundles").glob("*.jsonl")):
        copy_checked(path, package / "metadata/bundles" / path.name)
    tool = PHASE / "updates/scripts/migration/content_bundle.py"
    copy_checked(tool, package / "recovery_tool.py")
    text = """# A5 原字节基础包

此目录包含六个 Windows 可见根的基础快照：111629 个普通文件、5141 个目录与27个链接元数据。所有物理文件重新读字节核对，SHA256相同内容只存一份；payload tar卷至多4GiB，所有卷和对象已独立读回校验。

需要 Python 3.10+ 标准库：

    python recovery_tool.py verify --package .
    python recovery_tool.py restore-files --package . --destination /new/restore --root datasets --prefix data_odometry_velodyne/dataset/sequences/00/

普通文件按 destination/root_id/relative/path 恢复；输出必须新建，不覆盖源目录。不自动重建链接或POSIX权限，也不运行任何模型或训练。

PACKAGE.json 绑定核心控制清单与全部卷；metadata/BUNDLES.jsonl 关联517份逻辑包及所需卷，metadata/bundles保存各自带SHA256的成员清单。DELIVERY_INDEX.json绑定恢复工具和附加元数据，接收时一并核对；核心verify检查PACKAGE覆盖的全部卷、对象和核心控制清单。

基础快照排除了A5自身和包目录。A5新控制面、后续A6最终组会及入口变更由A7最终增量汇总；WSL内未导出环境、整套wheel和VHDX不在此基础包。PGC1部分结果仅原字节保存，未解释或重跑；所有旧停止/失败/预算与来源限制保持。

本地包、部分普通文件恢复检查不代表服务器迁移、全量目标恢复、完整环境或训练就绪。原件没有删除/移动。
"""
    readme = package / "README.md"
    assert not readme.exists()
    readme.write_text(text, encoding="utf-8")
    extra = []
    for path in sorted((package / "metadata").rglob("*")) + [package / "recovery_tool.py", readme]:
        if path.is_file():
            extra.append({"path": path.relative_to(package).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    delivery = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
                "package_manifest": {"path": "PACKAGE.json", "sha256": sha(package / "PACKAGE.json")}, "extra_control_files": extra,
                "source_files": meta["source_files"], "unique_objects": meta["unique_objects"], "volumes": len(meta["volumes"]),
                "logical_bundles": len(linked), "full_server_link_permission_or_final_incremental_restore_validated": False}
    (package / "DELIVERY_INDEX.json").write_text(json.dumps(delivery, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {"package_directory": str(package), "package_manifest_sha256": sha(package / "PACKAGE.json"),
               "delivery_index_sha256": sha(package / "DELIVERY_INDEX.json"), "source_manifest_sha256": meta["source_manifest_sha256"],
               "objects_manifest_sha256": meta["objects_manifest_sha256"], "source_byte_checks_sha256": meta["source_byte_checks_sha256"],
               "ordinary_files_fresh_byte_verified": meta["source_files_fresh_byte_verified"], "logical_bytes": meta["logical_bytes"],
               "unique_payload_bytes": meta["unique_payload_bytes"], "archive_volume_bytes": sum(r["bytes"] for r in meta["volumes"]),
               "volumes": meta["volumes"], "logical_bundles": len(linked), "unique_objects": meta["unique_objects"],
               "links_raw_buffers_verified": 27, "packager_source_sha256": sha(tool), "scientific_results_interpreted_or_rerun": False}
    (PHASE / "PACKAGE_REFERENCE.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "volumes"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
