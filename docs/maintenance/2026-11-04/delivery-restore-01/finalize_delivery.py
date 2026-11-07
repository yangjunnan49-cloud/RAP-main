"""After phase sealing, build/restore evidence and bind the complete final delivery."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import posixpath
import tarfile

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def main():
    spec = importlib.util.spec_from_file_location("finalizing_delivery", REPO / "scripts/migration/delivery.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    baseline = tool.load(PHASE / "BASELINE.json")
    package = Path(baseline["package"])
    assert (PHASE / "DELIVERY_SEAL.json").exists() and not (package / "DELIVERY.json").exists()
    phase_hash = tool.sha(PHASE / "DELIVERY_SEAL.json")
    seal = tool.load(PHASE / "DELIVERY_SEAL.json")
    entries = seal["files"] + [{"path": "DELIVERY_SEAL.json", "bytes": (PHASE / "DELIVERY_SEAL.json").stat().st_size, "sha256": phase_hash}]
    assert len({r["path"] for r in entries}) == len(entries)
    def save(path, value):
        path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    evidence = package / "evidence.tar"
    assert not evidence.exists()
    with tarfile.open(evidence, "w", format=tarfile.PAX_FORMAT) as out:
        for row in entries:
            source = tool.native_absolute(PHASE) / tool.safe_relative(row["path"])
            assert source.stat().st_size == row["bytes"] and tool.sha(source) == row["sha256"]
            info = tarfile.TarInfo(row["path"])
            info.size, info.mode, info.mtime = row["bytes"], 0o644, 0
            with source.open("rb") as handle:
                out.addfile(info, handle)
    save(package / "EVIDENCE_MANIFEST.json", {"phase_seal_sha256": phase_hash, "files": entries,
         "ordinary_files": len(entries), "total_bytes": sum(r["bytes"] for r in entries), "scientific_claims_superseded": False})
    project = tool.load(package / "PROJECT.json")
    final = {}
    def add(path, row, role, replace=False):
        tool.safe_relative(path)
        if path in final and not replace:
            assert final[path]["sha256"] == row["sha256"] and final[path]["bytes"] == row["bytes"], path
        final[path] = {"path": path, "bytes": row["bytes"], "sha256": row["sha256"], "role": role}
    def mapped_relative(row):
        return posixpath.join(project["layout"][row["root"]], row["path"])
    for row in tool.rows(package / "FINAL_FILES.jsonl"):
        add(mapped_relative(row), row, "project_source_identity")
    for row in tool.load(PHASE / "DELTA_RESTORE.json")["superseded_base_versions_preserved"]:
        add(row["path"], row, "preserved_previous_base_bytes")
    for row in tool.load(PHASE / "LOCAL_CONTROL_RESTORE.json")["applied"]["superseded_versions_preserved"]:
        add(row["path"], row, "preserved_previous_control_bytes")
    current = tool.load(PHASE / "CURRENT_DOCUMENT_SNAPSHOTS.json")
    late = tool.load(PHASE / "LATE_GIT_SNAPSHOTS.json")
    for row in current:
        add(mapped_relative(row), row, "final_current_authority", True)
    for row in late:
        add(mapped_relative(row), row, "late_Git_metadata_finite_freeze_without_attribution")
    prefix = "RAP-main/" + PHASE.relative_to(REPO).as_posix()
    for row in entries:
        add(prefix + "/" + row["path"], row, "A7_sealed_evidence")
    final_rows = [final[k] for k in sorted(final)]
    assert len({r["path"].casefold() for r in final_rows}) == len(final_rows)
    (package / "DELIVERY_FILES.jsonl").write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final_rows).encode("utf-8"))
    (package / "README.md").write_bytes("""# A7 本地交付

同时携带兄弟目录 A5-20261104 和本目录。PROJECT 为最新到A6的项目数据层；evidence为A7完整封存及最终当前入口，DELIVERY绑定两者和最终文件表。原件保留，服务器尚未选定。

仅需Python 3.10+标准库，在目标Linux显式恢复到新目录：

    python tools/delivery.py restore-delivery --delivery DELIVERY.json --destination /new/workspace --create-internal-links

单独重新读取最终文件树：

    python tools/delivery.py check-delivery-tree --delivery DELIVERY.json --workspace /new/workspace

Windows本机符号链接权限不足时，不使用create-internal-links；本轮在新恢复副本的25内部相对链接由一次有界WSL文件系统维护验证，2个人junction不创建。POSIX模式/所有者/ACL在真实目标另验；普通文件默认0644，目录0755，已知Git执行位按权限表处理，不猜扩展名。

FINAL_ACCEPTANCE记录本机完整项目字节复核、最终证据层和控制接续；它不是服务器驻留、GPU、环境重建或完整训练证明。未导出的Linux环境/wheel/WSL镜像不在项目数据层；来源/旧版本/组会差异继续保留。无模型/研究执行，无安装/下载/对外传输，原件未删除。
""".encode("utf-8"))
    controls = []
    for name in ("tools/delivery.py", "tools/content_bundle.py", "PROJECT.json", "FINAL_FILES.jsonl", "FINAL_DIRECTORIES.jsonl",
                 "LINK_PLAN.json", "PERMISSIONS.json", "EVIDENCE_MANIFEST.json", "DELIVERY_FILES.jsonl", "README.md"):
        path = package / name
        controls.append({"path": name, "bytes": path.stat().st_size, "sha256": tool.sha(path)})
    master = {"schema_version": 1, "client_local_date": "2026-11-05", "timezone": "Asia/Shanghai", "created_utc": datetime.now(timezone.utc).isoformat(),
              "status": "LOCAL_COMPLETE_LAYERED_DELIVERY_WITH_SERVER_TARGET_AND_RESEARCH_READINESS_HOLDS",
              "project_manifest": "PROJECT.json", "project_manifest_sha256": tool.sha(package / "PROJECT.json"), "control_files": controls,
              "workspace_files_manifest": "DELIVERY_FILES.jsonl", "workspace_files_manifest_sha256": tool.sha(package / "DELIVERY_FILES.jsonl"),
              "workspace_ordinary_files": len(final_rows), "workspace_logical_bytes": sum(r["bytes"] for r in final_rows),
              "evidence": {"archive": "evidence.tar", "archive_bytes": evidence.stat().st_size, "archive_sha256": tool.sha(evidence),
                           "manifest": "EVIDENCE_MANIFEST.json", "manifest_sha256": tool.sha(package / "EVIDENCE_MANIFEST.json"),
                           "phase_seal_sha256": phase_hash, "workspace_prefix": prefix},
              "required_sibling_base_package": "A5-20261104", "project_physical_files": 112682, "project_logical_bytes": 135095691259,
              "internal_relative_links": 25, "external_runtime_junctions_not_recreated": 2, "original_assets_deleted_or_moved": False,
              "server_selected": False, "server_migration_complete": False}
    save(package / "DELIVERY.json", master)
    workspace = Path(tool.load(PHASE / "RESTORE_DESTINATION.json")["directory"]) / "workspace"
    receipt = tool.install_evidence(package / "DELIVERY.json", workspace,
             progress=lambda value: print(json.dumps(value, ensure_ascii=False), flush=True))
    save(package / "EVIDENCE_RESTORE.json", receipt)
    observed, links = set(), []
    native_workspace = tool.native_absolute(workspace)
    def walk(folder):
        for entry in os.scandir(folder):
            path = Path(entry.path)
            value = entry.stat(follow_symlinks=False)
            relative = path.relative_to(native_workspace).as_posix()
            if getattr(value, "st_file_attributes", 0) & 0x400 or entry.is_symlink():
                links.append(relative)
            elif entry.is_dir(follow_symlinks=False):
                walk(path)
            else:
                observed.add(relative)
    walk(native_workspace)
    assert observed == set(final), (list(observed - set(final))[:5], list(set(final) - observed)[:5])
    assert len(links) == 25
    for row in current + late:
        path = tool.mapped(workspace, project["layout"], row)
        assert path.stat().st_size == row["bytes"] and tool.sha(path) == row["sha256"]
    for row in controls:
        assert (package / row["path"]).stat().st_size == row["bytes"] and tool.sha(package / row["path"]) == row["sha256"]
    assert tool.sha(PHASE / "DELIVERY_SEAL.json") == phase_hash
    acceptance = {"passed": True, "client_local_date": "2026-11-05", "timezone": "Asia/Shanghai", "observed_utc": datetime.now(timezone.utc).isoformat(),
                  "delivery_manifest_sha256": tool.sha(package / "DELIVERY.json"), "phase_seal_sha256": phase_hash,
                  "final_workspace_ordinary_files": len(final_rows), "final_workspace_logical_bytes": sum(r["bytes"] for r in final_rows),
                  "full_project_files_freshly_rehashed_before_registered_control_overlay": 112682, "full_project_bytes_freshly_rehashed": 135095691259,
                  "project_sha256_receipt": "PROJECT_RESTORE.json in sealed phase", "registered_control_rows_final_sha256_checked": len(current) + len(late),
                  "evidence_files_extracted_and_fresh_byte_checked": receipt["evidence_files_full_bytes_checked"],
                  "evidence_archive_full_sha256_verified": True, "physical_final_tree_has_exact_expected_ordinary_file_set": True,
                  "relative_internal_link_paths_retained": 25, "external_junctions_not_recreated": 2,
                  "all_final_file_bytes_covered_by_full_project_rehash_or_registered_control_evidence_checks": True,
                  "another_unconditional_135GB_read_after_control_changes_performed": False,
                  "evidence_archive_bytes": evidence.stat().st_size, "delta_archive_bytes": 144814080,
                  "source_originals_deleted_or_moved": False, "model_GPU_training_or_new_research_runs": 0,
                  "install_download_deploy_or_external_transfer_performed": False, "actual_Linux_target_permissions_owners_ACLs_environment_or_GPU_validated": False,
                  "A4_A5_A6_provenance_version_training_and_target_holds_retained": True, "server_selected": False, "server_migration_complete": False}
    save(package / "FINAL_ACCEPTANCE.json", acceptance)
    print(json.dumps(acceptance, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
