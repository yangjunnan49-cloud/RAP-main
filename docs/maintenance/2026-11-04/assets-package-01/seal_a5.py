"""Seal A5 control-plane evidence and bind the separately stored base payload."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    seal_path = PHASE / "DELIVERY_SEAL.json"
    assert not seal_path.exists(), "Refusing to replace a delivered seal"
    checks = load(PHASE / "CHECKS.json")
    assert checks["passed"] and checks["next_stage"] == "A6"
    assert checks["physical_source_files_fresh_byte_verified_in_build"] == 111629
    assert checks["unique_objects_full_readback_verified"] == 98854 and checks["tar_volumes_full_readback_verified"] == 30
    assert not checks["full_target_link_permission_or_final_incremental_restore_validated"]
    baseline = load(PHASE / "BASELINE.json")
    roots = {key: Path(value) for key, value in baseline["source_roots"].items()}
    package = Path(baseline["package_destination"])
    reference = load(PHASE / "PACKAGE_REFERENCE.json")
    assert sha(package / "PACKAGE.json") == reference["package_manifest_sha256"]
    assert sha(package / "DELIVERY_INDEX.json") == reference["delivery_index_sha256"]
    snapshots = []
    for item in load(PHASE / "AUTHORITY_PROOF.json")["current_files"]:
        source = roots[item["root"]] / item["path"]
        assert source.stat().st_size == item["bytes"] and sha(source) == item["sha256"]
        target = PHASE / "after" / item["root"] / item["path"]
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        assert sha(target) == item["sha256"]
        snapshots.append({**item, "snapshot": target.relative_to(PHASE).as_posix()})
    (PHASE / "CURRENT_DOCUMENT_SNAPSHOTS.json").write_text(json.dumps(snapshots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = {"stage": "A5", "status": "COMPLETE_WINDOWS_BASE_CONTENT_PACKAGE_WITH_PROVENANCE_AND_A7_HOLDS",
              "local_date": "2026-11-04", "timezone": "Asia/Shanghai", "before_files": 63, "current_files": len(snapshots),
              "current_code_role_records": 904, "ordinary_files_fresh_byte_verified": 111629, "source_directories": 5141,
              "native_links_raw_buffers_verified_without_following": 27, "logical_bytes": 134910234709,
              "unique_content_objects": 98854, "unique_content_bytes": 124999364971, "archive_volumes": 30,
              "archive_volume_bytes": 125075722240, "logical_bundles": 517, "zero_byte_ordinary_files_retained": 358,
              "real_restored_files_sha256_matched": 18, "real_restored_bytes": 690123401, "synthetic_tests_passed": 7,
              "member_manifest_digest_declarations_corrected_before_sealing": 517,
              "original_assets_deleted_or_moved": False, "source_provenance_reauthenticated": False,
              "PGC1_partial_accuracies_interpreted": False, "historical_source_digest_gaps_retained": 5,
              "historical_AGENTS_version_gaps_retained": 1, "research_state_changed": False,
              "WSL_GPU_model_training_or_research_operations": 0, "install_download_deploy_or_external_transfer_performed": False,
              "A4_training_and_target_holds_retained": True, "full_target_link_permission_restore_validated": False,
              "base_snapshot_excludes_A5_control_plane_and_own_package": True,
              "A5_A6_final_control_plane_and_source_increment_required_in_A7": True,
              "unexported_Linux_environment_wheel_or_VHDX_in_base": False, "server_migration_complete": False, "next_stage": "A6"}
    (PHASE / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    work = PHASE / "WORK_STATE.md"
    with work.open("a", encoding="utf-8") as handle:
        handle.write("\n## 最终交付接续\n\nA5 终验已通过；本文件上方为历史过程记录，其进行中/下一动作不再生效。最终状态以 STATUS.json、CHECKS.json 和 DELIVERY_SEAL.json 为准。111629 源文件新读、98854 对象/30卷全读回、517 逻辑包、18份真实恢复与7项合成测试通过；517处 Windows 换行摘要声明已纠正并留证。当前68权威文件与904代码索引已同步，下一步A6。A4训练/目标环境、来源缺口和A7全量链接/权限/最终增量继续保留；未启动WSL/GPU/研究或对外传输，无原件删除。\n")
    entries = []
    for path in sorted(PHASE.rglob("*")):
        assert not path.is_symlink(), "Unexpected link in control-plane evidence"
        if path.is_file() and path != seal_path:
            entries.append({"path": path.relative_to(PHASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    seal = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A5_BASE_PACKAGE_WITH_HOLDS", "files": entries,
            "total_files": len(entries), "total_bytes": sum(r["bytes"] for r in entries), "live_authority": "AUTHORITY_PROOF.json",
            "checks": "CHECKS.json", "separately_stored_payload_binding": "PACKAGE_REFERENCE.json",
            "package_manifest_sha256": reference["package_manifest_sha256"], "delivery_index_sha256": reference["delivery_index_sha256"],
            "historical_scientific_claims_superseded": False, "A7_final_increment_and_target_acceptance_required": True}
    seal_path.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in entries:
        path = PHASE / item["path"]
        assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"]
    print(json.dumps({"sealed_files": len(entries), "sealed_bytes": seal["total_bytes"], "current_snapshots": len(snapshots),
                      "separately_bound_volumes": 30, "seal_sha256": sha(seal_path)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
