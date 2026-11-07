"""Seal A3 evidence and immutable copies of the current authority files."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    seal_path = PHASE / "DELIVERY_SEAL.json"
    assert not seal_path.exists(), "Refusing to replace an existing delivery seal"
    checks = json.loads((PHASE / "CHECKS.json").read_text(encoding="utf-8"))
    assert checks["passed"] is True and checks["next_stage"] == "A4"
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
    status = {"stage": "A3", "status": "COMPLETE_ENTRY_PATH_REFACTOR_WITH_STATIC_BEHAVIOR_CHECKS",
              "local_date": "2026-11-04", "timezone": "Asia/Shanghai", "current_offline_tasks": 5,
              "baseline_backups": checks["before_files_verified"], "code_role_records": checks["code_role_records"],
              "changed_existing_sources": checks["changed_existing_sources"], "unit_tests_passed": checks["unit_tests_passed"],
              "guarded_cli_checks_passed": checks["guarded_cli_checks_passed"], "scientific_seals_unchanged": True,
              "known_historical_syntax_error_retained": True, "PGC1_partial_accuracies_interpreted": False,
              "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1,
              "WSL_GPU_model_training_or_research_started": False, "target_model_numerical_execution_validated": False,
              "next_stage": "A4", "server_selected": False, "server_migration_complete": False}
    (PHASE / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = []
    for path in sorted(PHASE.rglob("*")):
        if not path.is_file() or path == seal_path:
            continue
        files.append({"path": path.relative_to(PHASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    seal = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A3", "files": files,
            "total_files": len(files), "total_bytes": sum(r["bytes"] for r in files),
            "live_authority": "AUTHORITY_PROOF.json", "checks": "CHECKS.json",
            "historical_scientific_claims_superseded": False}
    seal_path.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    observed = json.loads(seal_path.read_text(encoding="utf-8"))
    assert observed == seal
    for item in observed["files"]:
        path = PHASE / item["path"]
        assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"]
    print(json.dumps({"sealed_files": len(files), "sealed_bytes": seal["total_bytes"],
                      "current_snapshots": len(snapshots), "seal_sha256": sha(seal_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
