"""Bind A6 current authority and maintenance-source succession."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main():
    baseline = load(PHASE / "BASELINE.json")
    roots = {k: Path(v) for k, v in baseline["roots"].items()}
    previous = load(REPO / baseline["previous_phase"] / "AUTHORITY_PROOF.json")
    old_code = {(r["root"], r["path"]): r for r in rows(PHASE / "before/rap-main/docs/code/ENTRYPOINTS.jsonl")}
    code = rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    changed = [r for r in code if (r["root"], r["path"]) in old_code and r["sha256"] != old_code[(r["root"], r["path"])]["sha256"]]
    added = [r for r in code if (r["root"], r["path"]) not in old_code]
    assert len(old_code) == 904 and len(code) == 905
    assert [(r["root"], r["path"]) for r in changed] == [("rap-main", "scripts/maintenance/index_code_entries.py"), ("rap-main", "scripts/maintenance/render_current_state.py")]
    assert [(r["root"], r["path"]) for r in added] == [("rap-main", "scripts/meetings/materials.py")]
    keys = {(r["root"], r["path"]) for r in previous["current_files"]}
    keys.add(("rap-main", "scripts/meetings/materials.py"))
    keys.add(("reports", "README.md"))
    keys.update(("rap-main", p.relative_to(REPO).as_posix()) for p in (REPO / "docs/meetings").glob("*") if p.is_file())
    assert len(keys) == 77
    current = []
    for root, relative in sorted(keys):
        p = roots[root] / relative
        current.append({"root": root, "path": relative, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    proof = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A6_LINEAGE_AND_PORTABLE_PREPARATION_WITH_HOLDS",
             "previous_authority": baseline["previous_phase"] + "/AUTHORITY_PROOF.json", "current_files": current,
             "historical_scientific_claims_superseded": False}
    (PHASE / "AUTHORITY_PROOF.json").write_bytes((json.dumps(proof, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    succession = {"changed_maintenance_sources": [{"root": r["root"], "path": r["path"],
                  "before_sha256": old_code[(r["root"], r["path"])]["sha256"], "after_sha256": r["sha256"]} for r in changed],
                  "added_explicit_maintenance_tool": {k: added[0][k] for k in ("root", "path", "sha256", "bytes")},
                  "other_baseline_code_config_files_unchanged": 902, "production_or_training_source_changed": False,
                  "old_meeting_builder_or_artifact_modified": False, "A6_new_control_plane_and_copies_to_be_included_in": "A7_FINAL_INCREMENT"}
    (PHASE / "SOURCE_SUCCESSION.json").write_bytes((json.dumps(succession, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"current_authority": len(current), "code_records": len(code), "old_code_unchanged": 902}))


if __name__ == "__main__":
    main()
