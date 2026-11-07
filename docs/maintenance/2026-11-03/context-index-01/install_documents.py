"""Install only explicit, reviewable documentation targets, after byte-exact backups."""
import argparse
import hashlib
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
TARGETS = {
    "internal": {REPO / "AGENTS.md": "rap-main.AGENTS.md", REPO / "README.md": "rap-main.README.md",
                 REPO / "docs/maintenance/README.md": "maintenance.README.md"},
    "external": {REPO.parent / "AGENTS.md": "workspace.AGENTS.md", REPO.parent / "RAP-SLAM/README.md": "rap-slam.README.md",
                 REPO.parent / "RAP-SLAM/AGENTS.md": "rap-slam.AGENTS.md"}}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scope", choices=("internal", "external"))
    args = parser.parse_args()
    before = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    by_path = {str(Path(r["source"])).casefold(): r for r in before["backups"]}
    records = []
    for target, staged_name in TARGETS[args.scope].items():
        target = target.resolve()
        staged = PHASE / "updates" / staged_name
        backup = by_path.get(str(target).casefold())
        if target.exists():
            if backup is None or sha(target) != backup["sha256"]:
                raise RuntimeError("Target changed since backup; refusing replacement: " + str(target))
            if sha(PHASE / backup["backup"]) != backup["sha256"]:
                raise RuntimeError("Authority backup mismatch")
        elif target != (REPO.parent / "RAP-SLAM/AGENTS.md").resolve():
            raise RuntimeError("Expected existing document missing")
        staged_bytes = staged.read_bytes()
        records.append({"target": str(target), "staged": staged.relative_to(PHASE).as_posix(),
                        "new_sha256": hashlib.sha256(staged_bytes).hexdigest(), "new_bytes": len(staged_bytes),
                        "previous_sha256": backup["sha256"] if backup else None, "created": backup is None})
    # All guards run before the first replacement. Targets are fixed literal documents, no recursive operations.
    for record in records:
        target = Path(record["target"])
        target.write_bytes((PHASE / record["staged"]).read_bytes())
        if sha(target) != record["new_sha256"]:
            raise RuntimeError("Installed document mismatch")
    (PHASE / ("INSTALL_" + args.scope.upper() + ".json")).write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scope": args.scope, "documents_installed": len(records), "source_or_data_files_changed": False}))


if __name__ == "__main__":
    main()
