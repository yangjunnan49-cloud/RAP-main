"""Preserve A3 current files and code before A4 environment documentation."""
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
    target = PHASE / "BASELINE.json"
    assert not target.exists(), "Refusing to replace baseline"
    previous = REPO / "docs/maintenance/2026-11-04/code-paths-01"
    proof = json.loads((previous / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))
    code = [json.loads(line) for line in (REPO / "docs/code/ENTRYPOINTS.jsonl").read_text(encoding="utf-8").splitlines()]
    keys = {(r["root"], r["path"]) for r in proof["current_files"] + code}
    backups = []
    for root, relative in sorted(keys):
        source = ROOTS[root] / relative
        dest = PHASE / "before" / root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        digest = sha(source)
        assert sha(dest) == digest
        backups.append({"root": root, "path": relative, "backup": dest.relative_to(PHASE).as_posix(),
                        "bytes": source.stat().st_size, "sha256": digest})
    for r in proof["current_files"] + code:
        assert sha(ROOTS[r["root"]] / r["path"]) == r["sha256"], r
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "owner_request": "执行下一步（A4）",
              "previous_phase": previous.relative_to(REPO).as_posix(), "previous_authority_verified": True,
              "backups": backups, "code_files": [{k: r[k] for k in ("root", "path", "bytes", "sha256")} for r in code],
              "source_edits_or_installation_planned": False, "research_or_training_authorized": False}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"before_files": len(backups), "code_files": len(code)}))


if __name__ == "__main__":
    main()
