"""Bind current authority and maintenance-source succession after A4 auditing."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent}


def record(root, relative):
    path = ROOTS[root] / relative
    return {"root": root, "path": relative, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    baseline = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    previous = json.loads((REPO / baseline["previous_phase"] / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))
    code = [json.loads(line) for line in (REPO / "docs/code/ENTRYPOINTS.jsonl").read_text(encoding="utf-8").splitlines()]
    old = {(r["root"], r["path"]): r for r in baseline["code_files"]}
    keys = {(r["root"], r["path"]) for r in previous["current_files"]}
    changed, added = [], []
    for r in code:
        key = (r["root"], r["path"])
        if key not in old:
            added.append(record(*key))
            keys.add(key)
        elif old[key]["sha256"] != r["sha256"]:
            changed.append({"root": key[0], "path": key[1], "before_sha256": old[key]["sha256"], "after_sha256": r["sha256"],
                            "before": "before/" + key[0] + "/" + key[1]})
            keys.add(key)
    assert len(changed) == 2 and len(added) == 7
    keys.update(("rap-main", p.relative_to(REPO).as_posix()) for p in (REPO / "docs/environment").glob("*") if p.is_file())
    proof = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A4_AUDIT_WITH_HOLDS",
             "previous_authority": "docs/maintenance/2026-11-04/code-paths-01/AUTHORITY_PROOF.json",
             "historical_scientific_claims_superseded": False, "current_files": [record(*key) for key in sorted(keys)]}
    (PHASE / "AUTHORITY_PROOF.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PHASE / "SOURCE_SUCCESSION.json").write_text(json.dumps({"changed_maintenance_sources": changed, "added_tools_tests_reference_profiles": added,
                                                               "other_baseline_code_config_files_unchanged": len(old) - len(changed),
                                                               "production_or_training_source_changed": False}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    bindings = {"binding_collected_after_execution": True, "not_an_execution_time_signature": True,
                "scripts": [{"path": str(p.relative_to(REPO)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in (PHASE / "collect_linux.py", PHASE / "collect_supplement.py", REPO / "scripts/environment/cpu_probe.py")],
                "receipts": [{"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                             for p in (PHASE / "LINUX_OBSERVATION.json", PHASE / "LINUX_SUPPLEMENT.json", PHASE / "CPU_PROBE.json")]}
    (PHASE / "OBSERVATION_BINDINGS.json").write_text(json.dumps(bindings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"current_files": len(keys), "changed_maintenance_sources": len(changed), "added_code_reference_files": len(added)}))


if __name__ == "__main__":
    main()
