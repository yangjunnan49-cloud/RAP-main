"""Capture current entries and source bytes before A3 maintenance."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = PHASE / "BASELINE.json"
    if target.exists():
        raise SystemExit("Baseline already exists; refusing replacement")
    previous = REPO / "docs/maintenance/2026-11-03/context-index-01"
    proof = json.loads((previous / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))
    candidates = {(r["root"], r["path"]) for r in proof["current_files"]}
    sources = []
    suffixes = {".py", ".sh", ".ps1", ".yaml", ".yml", ".toml", ".xml", ".cfg", ".txt"}
    folders = {"rap-main": ["rectified_point_flow", "dataset_process", "config", "scripts"],
               "rap-slam": ["rap_slam", "scripts", "ros2"]}
    for root, groups in folders.items():
        paths = list(ROOTS[root].glob("*"))
        for folder in groups:
            paths.extend((ROOTS[root] / folder).rglob("*"))
        for path in sorted(set(paths)):
            if not path.is_file() or path.suffix.lower() not in suffixes or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(ROOTS[root]).as_posix()
            sources.append({"root": root, "path": relative, "bytes": path.stat().st_size, "sha256": digest(path)})
            candidates.add((root, relative))
    backups = []
    for root, relative in sorted(candidates):
        source = ROOTS[root] / relative
        dest = PHASE / "before" / root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        backups.append({"root": root, "path": relative, "backup": dest.relative_to(PHASE).as_posix(),
                        "bytes": source.stat().st_size, "sha256": digest(source)})
        assert digest(dest) == digest(source)
    for item in proof["current_files"]:
        assert digest(ROOTS[item["root"]] / item["path"]) == item["sha256"], item
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "owner_request": "继续执行A3",
              "previous_phase": previous.relative_to(REPO).as_posix(), "previous_authority_verified": True,
              "backups": backups, "source_files": sources, "git_mutation_authorized": False,
              "model_training_or_research_authorized": False}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"backups": len(backups), "source_files": len(sources)}))


if __name__ == "__main__":
    main()
