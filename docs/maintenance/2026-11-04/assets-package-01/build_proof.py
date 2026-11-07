"""Bind A5 current authority to the preserved A4 authority and source freeze."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    baseline = load(PHASE / "BASELINE.json")
    roots = {key: Path(value) for key, value in baseline["source_roots"].items()}
    previous = load(REPO / baseline["previous_phase"] / "AUTHORITY_PROOF.json")
    old_code = {(r["root"], r["path"]): r for r in rows(PHASE / "before/rap-main/docs/code/ENTRYPOINTS.jsonl")}
    code = rows(REPO / "docs/code/ENTRYPOINTS.jsonl")
    changed, added = [], []
    for r in code:
        key = (r["root"], r["path"])
        if key not in old_code:
            added.append(r)
        elif r["sha256"] != old_code[key]["sha256"]:
            changed.append({"root": key[0], "path": key[1], "before_sha256": old_code[key]["sha256"],
                            "after_sha256": r["sha256"], "before": "before/" + key[0] + "/" + key[1]})
    assert len(old_code) == 903 and len(code) == 904
    assert [(r["root"], r["path"]) for r in changed] == [("rap-main", "scripts/maintenance/index_code_entries.py")]
    assert [(r["root"], r["path"]) for r in added] == [("rap-main", "scripts/migration/content_bundle.py")]
    keys = {(r["root"], r["path"]) for r in previous["current_files"]}
    keys.add(("rap-main", "scripts/migration/content_bundle.py"))
    keys.update(("rap-main", p.relative_to(REPO).as_posix()) for p in (REPO / "docs/assets").glob("*.md"))
    assert len(keys) == 68
    current = []
    for root, relative in sorted(keys):
        path = roots[root] / relative
        current.append({"root": root, "path": relative, "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    proof = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A5_BASE_PACKAGE_WITH_HOLDS",
             "previous_authority": baseline["previous_phase"] + "/AUTHORITY_PROOF.json",
             "historical_scientific_claims_superseded": False, "current_files": current}
    (PHASE / "AUTHORITY_PROOF.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    succession = {"changed_maintenance_sources": changed,
                  "added_explicit_maintenance_tools": [{k: r[k] for k in ("root", "path", "bytes", "sha256")} for r in added],
                  "other_baseline_code_config_files_unchanged": 902, "production_or_training_source_changed": False,
                  "frozen_base_includes_A4_versions": True, "A5_A6_control_plane_final_increment_deferred_to": "A7"}
    (PHASE / "SOURCE_SUCCESSION.json").write_text(json.dumps(succession, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"current_authority": len(current), "code_records": len(code), "changed_maintenance_sources": len(changed), "new_tools": len(added)}))


if __name__ == "__main__":
    main()
