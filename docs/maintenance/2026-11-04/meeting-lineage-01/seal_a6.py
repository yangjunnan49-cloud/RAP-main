"""Seal A6 lineage/preparation evidence with explicit version and export holds."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for b in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def main():
    seal_path = PHASE / "DELIVERY_SEAL.json"
    assert not seal_path.exists(), "Refusing to replace a delivered seal"
    checks = load(PHASE / "CHECKS.json")
    assert checks["passed"] and checks["next_stage"] == "A7" and checks["unit_tests_passed"] == 6
    assert checks["meeting_report_source_files_fresh_sha256_verified"] == 1975
    assert not checks["all_meeting_final_variants_confirmed"] and not checks["native_document_or_pptd_build_export_visual_QA_validated"]
    baseline = load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["roots"].items()}
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
    (PHASE / "CURRENT_DOCUMENT_SNAPSHOTS.json").write_bytes((json.dumps(snapshots, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    status = {"stage": "A6", "status": "CATALOG_LINEAGE_AND_PORTABLE_PREPARATION_COMPLETE_WITH_VERSION_REFERENCE_AND_EXPORT_HOLDS",
              "local_date": "2026-11-04", "timezone": "Asia/Shanghai", "before_files": 68, "current_files": 77,
              "meeting_report_families": 10, "ordinary_files_fresh_byte_verified": 1975, "source_bytes": 2902199121,
              "all_source_assets_match_A5_base": True, "links_not_followed": 20,
              "Office_PDF_files_inspected": 46, "old_delivery_artifact_hashes_matched": 6,
              "editable_decks": 4, "active_editable_source_pages": 47, "embedded_media_relationships": 60,
              "media_relationships_with_same_byte_source_aliases": 44,
              "historical_source_bindings": 59, "original_path_matches": 57, "byte_alias_available": 1,
              "unrecovered_exact_reference_PDF": 1, "all_meeting_final_variants_confirmed": False,
              "portable_preparation_files": 72, "portable_preparation_bytes": 17121135,
              "portable_notes_syntax_and_module_import_passed": True,
              "new_Office_or_native_pptd_build_export_render_validated": False,
              "synthetic_tests_passed": 6, "current_code_role_records": 905,
              "production_training_or_old_builder_artifact_changed": False,
              "maintenance_classification_and_state_renderer_changed": True,
              "old_code_config_files_byte_unchanged": 902, "original_assets_deleted_or_moved": False,
              "research_state_changed": False, "PGC1_partial_accuracies_interpreted": False,
              "WSL_GPU_model_training_or_new_research_runs": 0, "install_download_deploy_or_external_transfer_performed": False,
              "A4_environment_training_and_A5_provenance_holds_retained": True,
              "A6_control_plane_and_prepared_copies_require_A7_final_increment": True,
              "full_target_restore_link_permission_or_server_acceptance_validated": False,
              "next_stage": "A7", "server_migration_complete": False}
    (PHASE / "STATUS.json").write_bytes((json.dumps(status, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    entries = []
    for path in sorted(PHASE.rglob("*")):
        assert not path.is_symlink(), "Unexpected control-plane link"
        if path.is_file() and path != seal_path:
            entries.append({"path": path.relative_to(PHASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    seal = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A6_LINEAGE_AND_PORTABLE_PREPARATION_WITH_HOLDS",
            "files": entries, "total_files": len(entries), "total_bytes": sum(r["bytes"] for r in entries),
            "live_authority": "AUTHORITY_PROOF.json", "checks": "CHECKS.json", "source_manifest": "SOURCE_FILES.jsonl",
            "historical_scientific_claims_superseded": False,
            "previous_A5_seal_sha256": baseline["previous_seal_sha256"], "A7_final_increment_and_target_acceptance_required": True}
    seal_path.write_bytes((json.dumps(seal, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    for item in entries:
        path = PHASE / item["path"]
        assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"]
    print(json.dumps({"sealed_files": len(entries), "sealed_bytes": seal["total_bytes"], "current_snapshots": len(snapshots),
                      "seal_sha256": sha(seal_path)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
