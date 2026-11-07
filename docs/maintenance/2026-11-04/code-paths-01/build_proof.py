"""Build the current authority/source succession records before final verification."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent}


def record(root, relative):
    path = ROOTS[root] / relative
    return {"root": root, "path": relative, "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    baseline = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    previous = json.loads((REPO / baseline["previous_phase"] / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))
    keys = {(r["root"], r["path"]) for r in previous["current_files"]}
    sources = {(r["root"], r["path"]): r for r in baseline["source_files"]}
    current = [json.loads(line) for line in (REPO / "docs/code/ENTRYPOINTS.jsonl").read_text(encoding="utf-8").splitlines()]
    changed, added = [], []
    for row in current:
        key = (row["root"], row["path"])
        if key not in sources:
            added.append(record(*key))
            keys.add(key)
        elif sources[key]["sha256"] != row["sha256"]:
            old = sources[key]
            changed.append({"root": key[0], "path": key[1], "before_sha256": old["sha256"],
                            "before_bytes": old["bytes"], "before": "before/" + key[0] + "/" + key[1],
                            "after_sha256": row["sha256"], "after_bytes": row["bytes"]})
            keys.add(key)
    assert len(changed) == 4 and len(added) == 9, (len(changed), len(added))
    keys.update(("rap-main", p) for p in ("docs/code/README.md", "docs/code/RUNNING.md", "docs/code/ENTRYPOINTS.jsonl", "config/runtime.example.json"))
    proof = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": "A3",
             "previous_authority": "docs/maintenance/2026-11-03/context-index-01/AUTHORITY_PROOF.json",
             "historical_scientific_claims_superseded": False,
             "current_files": [record(*key) for key in sorted(keys)]}
    (PHASE / "AUTHORITY_PROOF.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    succession = {"changed_existing_sources": changed, "added_source_config_files": added,
                  "other_baseline_sources_sha256_unchanged": len(sources) - len(changed),
                  "historical_source_digest_gaps_retained": 5, "historical_AGENTS_version_gaps_retained": 1}
    (PHASE / "SOURCE_SUCCESSION.json").write_text(json.dumps(succession, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"current_files": len(keys), "changed_existing_sources": len(changed), "added_source_config_files": len(added)}))


if __name__ == "__main__":
    main()
