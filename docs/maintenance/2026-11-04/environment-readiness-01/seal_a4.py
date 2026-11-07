"""Seal A4 audit/guide evidence with explicit target and training holds."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent}


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    seal_path = PHASE / "DELIVERY_SEAL.json"
    assert not seal_path.exists(), "Refusing to replace a delivered seal"
    checks = json.loads((PHASE / "CHECKS.json").read_text(encoding="utf-8"))
    assert checks["passed"] is True and checks["next_stage"] == "A5"
    assert checks["temporary_WSL_sessions"] == 4 and checks["WSL_restored_initial_stopped_state"] is True
    assert checks["complete_training_resume_clean_rebuild_or_target_GPU_model_validated"] is False
    proof = json.loads((PHASE / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))
    snapshots = []
    for item in proof["current_files"]:
        source = ROOTS[item["root"]] / item["path"]
        assert source.stat().st_size == item["bytes"] and sha(source) == item["sha256"], source
        target = PHASE / "after" / item["root"] / item["path"]
        assert not target.exists() or sha(target) == item["sha256"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        assert sha(target) == item["sha256"]
        snapshots.append({**item, "snapshot": target.relative_to(PHASE).as_posix()})
    (PHASE / "CURRENT_DOCUMENT_SNAPSHOTS.json").write_text(json.dumps(snapshots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = {"stage": "A4", "status": "AUDIT_AND_GUIDE_COMPLETE_WITH_TRAINING_AND_TARGET_HOLDS", "local_date": "2026-11-04", "timezone": "Asia/Shanghai",
              "before_files": 931, "current_files": len(snapshots), "current_code_role_records": 903,
              "environment_metadata_scopes": 4, "linux_claim_occurrences_matched": 72, "linux_claim_paths": 9,
              "linux_preserved_files": 384, "linux_preserved_bytes": 332636737, "cpu_required_checks_passed": 17,
              "unit_tests_passed": 5, "muon_present": False, "pytorch3d_original_successful_build_commit_recovered": False,
              "training_entry_and_complete_resume_chain_validated": False, "clean_rebuild_or_target_GPU_model_validated": False,
              "temporary_WSL_sessions": 4, "WSL_restored_initial_stopped_state": True,
              "model_or_checkpoint_or_dataset_loads_training_or_research_runs": 0, "CUDA_initialized": False,
              "software_install_or_package_download_performed": False, "git_and_scientific_seals_unchanged": True,
              "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1,
              "PGC1_partial_accuracies_interpreted": False, "next_stage": "A5", "server_migration_complete": False}
    (PHASE / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    entries = []
    for path in sorted(PHASE.rglob("*")):
        if path.is_file() and path != seal_path:
            entries.append({"path": path.relative_to(PHASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    seal = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A4_AUDIT_WITH_HOLDS", "files": entries,
            "total_files": len(entries), "total_bytes": sum(r["bytes"] for r in entries),
            "live_authority": "AUTHORITY_PROOF.json", "checks": "CHECKS.json", "historical_scientific_claims_superseded": False}
    seal_path.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert json.loads(seal_path.read_text(encoding="utf-8")) == seal
    for item in entries:
        path = PHASE / item["path"]
        assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"]
    print(json.dumps({"sealed_files": len(entries), "sealed_bytes": seal["total_bytes"], "current_snapshots": len(snapshots),
                      "seal_sha256": sha(seal_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
