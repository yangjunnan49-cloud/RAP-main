"""Seal A7 project/control evidence; final tar/master receipts are outside this seal."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def main():
    spec = importlib.util.spec_from_file_location("sealing_delivery", REPO / "scripts/migration/delivery.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    seal_path = PHASE / "DELIVERY_SEAL.json"
    assert not seal_path.exists()
    checks = tool.load(PHASE / "CHECKS.json")
    assert checks["passed"] and checks["full_project_files_fresh_post_restore_rehash"] == 112682
    assert checks["WSL_restored_initial_stopped_state"] and not checks["server_migration_complete"]
    baseline = tool.load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["source_roots"].items()}
    for row in tool.load(PHASE / "CURRENT_DOCUMENT_SNAPSHOTS.json"):
        assert tool.sha(roots[row["root"]] / row["path"]) == row["sha256"] == tool.sha(PHASE / row["snapshot"])
    status = {"stage": "A7", "status": "LOCAL_PROJECT_AND_CURRENT_CONTROL_ACCEPTED_FINAL_EVIDENCE_MASTER_FINALIZATION_FOLLOWS_SEAL",
              "client_local_date": "2026-11-05", "timezone": "Asia/Shanghai", "before_files": 77, "current_authority_files": 81,
              "base_files_restored": 111629, "base_objects_and_full_volume_hashes_verified": 98854, "base_volumes": 30,
              "delta_files_restored": 1072, "delta_objects_verified": 833, "delta_volumes": 1,
              "project_files_freshly_rehashed": 112682, "project_bytes_freshly_rehashed": 135095691259,
              "superseded_base_versions_preserved": 19, "internal_relative_links_verified": 25, "external_junctions_not_recreated": 2,
              "POSIX_permission_function_small_fixture_passed": True, "actual_target_modes_owners_ACLs_validated": False,
              "bounded_WSL_filesystem_sessions": 1, "WSL_restored_initial_stopped_state": True, "relocated_path_checks_without_numeric_imports": 5,
              "current_code_role_records": 906, "old_code_config_files_byte_unchanged": 905, "delivery_tests_passed": 9,
              "source_originals_deleted_or_moved": False, "research_state_changed": False, "PGC1_partial_accuracies_interpreted": False,
              "GPU_model_training_or_new_research_runs": 0, "install_download_deploy_or_external_transfer_performed": False,
              "A4_A5_A6_and_server_holds_retained": True, "evidence_tar_master_and_evidence_restore_receipts_recorded_outside_phase_after_seal": True,
              "final_acceptance_location": "A7-20261104/FINAL_ACCEPTANCE.json", "server_selected": False, "server_migration_complete": False,
              "next_stage": "TARGET_SELECTION_AND_REMAINING_ACCEPTANCE"}
    (PHASE / "STATUS.json").write_bytes((json.dumps(status, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    with (PHASE / "WORK_STATE.md").open("ab") as handle:
        handle.write("\n## 封存接续\n\n上方为过程记录，已完成项目全量恢复/新读复核、链接/权限小夹具、路径与当前控制接续；原进行中动作不再生效。最终阶段状态见STATUS/CHECKS/seal。封存后还要在包目录生成并验证evidence.tar、最终DELIVERY/文件表和FINAL_ACCEPTANCE，不能回写本phase；最终交付以包内FINAL_ACCEPTANCE为准。真实目标/服务器/训练/来源版本保留项继续有效，无自动研究授权。\n".encode("utf-8"))
    entries = []
    native_phase = tool.native_absolute(PHASE)
    for path in sorted(native_phase.rglob("*")):
        assert not path.is_symlink() and not (getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
        if path.is_file() and path != native_phase / "DELIVERY_SEAL.json":
            entries.append({"path": path.relative_to(native_phase).as_posix(), "bytes": path.stat().st_size, "sha256": tool.sha(path)})
    seal = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A7_LOCAL_PROJECT_AND_CONTROL_WITH_TARGET_HOLDS", "files": entries,
            "total_files": len(entries), "total_bytes": sum(r["bytes"] for r in entries), "checks": "CHECKS.json", "live_authority": "AUTHORITY_PROOF.json",
            "previous_A6_seal_sha256": baseline["previous_seal_sha256"], "historical_scientific_claims_superseded": False,
            "post_seal_evidence_master_acceptance_recorded_in_package": True}
    seal_path.write_bytes((json.dumps(seal, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    for row in entries:
        path = native_phase / tool.safe_relative(row["path"])
        assert path.stat().st_size == row["bytes"] and tool.sha(path) == row["sha256"]
    print(json.dumps({"sealed_files": len(entries), "sealed_bytes": seal["total_bytes"], "seal_sha256": tool.sha(seal_path),
                      "post_seal_package_finalization_still_required": True}), flush=True)


if __name__ == "__main__":
    main()
