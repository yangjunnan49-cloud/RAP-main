"""Overlay the verified project delta, then freshly hash the entire restored tree."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def main():
    spec = importlib.util.spec_from_file_location("used_delta_restore", PHASE / "used/delivery-longpath.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    base_receipt = tool.load(PHASE / "BASE_RESTORE.json")
    assert base_receipt["passed"] and base_receipt["ordinary_files_restored"] == 111629
    assert not (PHASE / "PROJECT_RESTORE.json").exists()
    package = Path(tool.load(PHASE / "BASELINE.json")["package"])
    project = tool.load(package / "PROJECT.json")
    destination = Path(tool.load(PHASE / "RESTORE_DESTINATION.json")["directory"]) / "workspace"
    def progress(value):
        value["observed_utc"] = datetime.now(timezone.utc).isoformat()
        with (PHASE / "PROJECT_RESTORE_PROGRESS.jsonl").open("ab") as handle:
            handle.write((json.dumps(value) + "\n").encode("utf-8"))
        print(json.dumps(value), flush=True)
    base_package = REPO / ".maintenance-archive/migration/A5-20261104"
    result = tool.restore_layer(package / "delta", destination, project["layout"], overlay=True,
                                expected_before=tool.rows(base_package / "SOURCE_FILES.jsonl"), progress=progress)
    (PHASE / "DELTA_RESTORE.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    checked = tool.check_files(tool.rows(package / "FINAL_FILES.jsonl"), destination, project["layout"],
                               extra_records=result["superseded_base_versions_preserved"], progress=progress)
    receipt = {"passed": True, "observed_utc": datetime.now(timezone.utc).isoformat(), "destination": str(destination),
               "base_receipt": "BASE_RESTORE.json", "delta_receipt": "DELTA_RESTORE.json", "fresh_restored_tree_check": checked,
               "base_and_delta_archives_full_hash_verified_while_restoring": True, "project_manifest_sha256": tool.sha(package / "PROJECT.json"),
               "source_originals_changed_or_deleted": False, "A7_final_authority_and_evidence_overlay_pending": True,
               "model_scientific_array_training_or_research_execution": False}
    (PHASE / "PROJECT_RESTORE.json").write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
