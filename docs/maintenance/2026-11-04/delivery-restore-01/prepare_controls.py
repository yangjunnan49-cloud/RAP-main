"""Snapshot final authority/late Git metadata and apply the registered local overlay."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def main():
    spec = importlib.util.spec_from_file_location("final_control_tool", REPO / "scripts/migration/delivery.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    baseline = tool.load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["source_roots"].items()}
    old = tool.load(REPO / baseline["previous_phase"] / "AUTHORITY_PROOF.json")
    code = tool.rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    old_code = {(r["root"], r["path"]): r for r in tool.rows(PHASE / "before/rap-main/docs/code/ENTRYPOINTS.jsonl")}
    assert len(old_code) == 905 and len(code) == 906
    changed = [r for r in code if (r["root"], r["path"]) in old_code and r["sha256"] != old_code[(r["root"], r["path"])]["sha256"]]
    added = [r for r in code if (r["root"], r["path"]) not in old_code]
    assert not changed and [(r["root"], r["path"]) for r in added] == [("rap-main", "scripts/migration/delivery.py")]
    keys = {(r["root"], r["path"]) for r in old["current_files"]}
    keys.add(("rap-main", "scripts/migration/delivery.py"))
    keys.update(("rap-main", "docs/migration/" + name) for name in ("DELIVERY.md", "RESTORE.md", "HANDOFF.md"))
    assert len(keys) == 81
    authority, snapshots = [], []
    for root, relative in sorted(keys):
        source = roots[root] / relative
        row = {"root": root, "path": relative, "bytes": source.stat().st_size, "sha256": tool.sha(source)}
        target = tool.native_absolute(PHASE / "after" / root / relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists() or tool.sha(target) == row["sha256"]
        target.write_bytes(source.read_bytes())
        authority.append(row)
        snapshots.append({**row, "snapshot": "after/" + root + "/" + relative})
    def save(name, value):
        (PHASE / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    save("AUTHORITY_PROOF.json", {"stage": "A7_LOCAL_DELIVERY_WITH_TARGET_HOLDS", "created_utc": datetime.now(timezone.utc).isoformat(),
         "previous_authority": baseline["previous_phase"] + "/AUTHORITY_PROOF.json", "current_files": authority, "historical_scientific_claims_superseded": False})
    save("CURRENT_DOCUMENT_SNAPSHOTS.json", snapshots)
    save("SOURCE_SUCCESSION.json", {"old_code_config_files_byte_unchanged": 905, "existing_production_or_maintenance_source_changed": False,
         "added_explicit_migration_tool": {k: added[0][k] for k in ("root", "path", "bytes", "sha256")},
         "default_dispatch_entries_unchanged": True, "model_training_or_scientific_behavior_changed": False})
    frozen = {(r["root"], r["path"]): r for r in tool.rows(PHASE / "PROJECT_FILES.jsonl")}
    late, metadata_only = [], 0
    for root in ("rap-main", "rap-slam"):
        for critical in (".git/HEAD", ".git/index"):
            assert tool.sha(roots[root] / critical) == frozen[(root, critical)]["sha256"]
        for folder, dirs, names in os.walk(roots[root] / ".git", followlinks=False):
            for name in names:
                source = Path(folder) / name
                stat = source.lstat()
                assert not source.is_symlink() and not (getattr(stat, "st_file_attributes", 0) & 0x400)
                relative = source.relative_to(roots[root]).as_posix()
                original = frozen.get((root, relative))
                if original is not None and original["bytes"] == stat.st_size and original["mtime_ns"] == stat.st_mtime_ns:
                    continue
                digest = tool.sha(source)
                if original is not None:
                    assert digest == original["sha256"], "Unexpected old Git byte mutation: " + relative
                    metadata_only += 1
                    continue
                row = {"root": root, "path": relative, "bytes": stat.st_size, "sha256": digest, "snapshot": "after-git/" + root + "/" + relative,
                       "origin_attributed": False, "present_at_final_control_freeze_utc": datetime.now(timezone.utc).isoformat()}
                target = tool.native_absolute(PHASE / row["snapshot"])
                target.parent.mkdir(parents=True, exist_ok=True)
                assert not target.exists() or tool.sha(target) == digest
                target.write_bytes(source.read_bytes())
                late.append(row)
    save("LATE_GIT_SNAPSHOTS.json", late)
    save("LATE_GIT_OBSERVATION.json", {"new_files_after_project_freeze": len(late), "bytes": sum(r["bytes"] for r in late),
         "old_metadata_only_byte_matches": metadata_only, "origin_attributed": False, "HEAD_index_or_commit_changed": False,
         "finite_control_freeze_not_a_dynamic_background_watch": True})
    package = Path(baseline["package"])
    project = tool.load(package / "PROJECT.json")
    workspace = Path(tool.load(PHASE / "RESTORE_DESTINATION.json")["directory"]) / "workspace"
    assert not (PHASE / "LOCAL_CONTROL_RESTORE.json").exists()
    applied = tool.apply_control_snapshots(PHASE, workspace, project["layout"], snapshots + late, tool.rows(package / "FINAL_FILES.jsonl"))
    save("LOCAL_CONTROL_RESTORE.json", {"passed": True, "observed_utc": datetime.now(timezone.utc).isoformat(), "current_control_count": len(snapshots),
         "late_git_count": len(late), "applied": applied, "project_full_byte_check_remains_valid_except_explicit_control_rows": True,
         "complete_A7_phase_evidence_installation_pending_seal": True, "source_originals_modified_or_removed": False})
    print(json.dumps({"current_authority": len(authority), "old_code_byte_unchanged": 905, "late_git_files": len(late),
                      "controls_written": len(applied["written"]), "controls_already_matching": applied["already_matching"],
                      "old_control_versions_preserved": len(applied["superseded_versions_preserved"])}), flush=True)


if __name__ == "__main__":
    main()
