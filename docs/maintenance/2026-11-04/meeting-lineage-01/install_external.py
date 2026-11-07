"""Install guarded A6 navigation into parent, sibling and report roots."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-slam": REPO.parent / "RAP-SLAM", "workspace-root": REPO.parent, "reports": REPO.parent / "RAP-SLAM-report"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = json.loads((PHASE / "BASELINE.json").read_text(encoding="utf-8"))
    old = {(r["root"], r["path"]): r for r in baseline["backups"]}
    receipt_path = PHASE / "INSTALL_EXTERNAL.json"
    receipts = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else []
    previous = {(r["root"], r["path"]): r for r in receipts}
    pending = []
    for root, destination in ROOTS.items():
        folder = PHASE / "updates" / root
        if not folder.exists():
            continue
        for source in sorted(folder.rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(folder).as_posix()
            target = destination / relative
            assert target.resolve().is_relative_to(destination.resolve()), relative
            if source.suffix == ".py":
                compile(source.read_text(encoding="utf-8"), str(source), "exec")
            key = (root, relative)
            if key in previous:
                assert target.is_file() and sha(target) == previous[key]["new_sha256"], relative
                if sha(source) == sha(target):
                    continue
            elif key in old:
                assert sha(target) == old[key]["sha256"], relative
            else:
                assert not target.exists(), relative
            pending.append((source, target, root, relative))
    for source, target, root, relative in pending:
        old_sha = sha(target) if target.exists() else None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        assert sha(target) == sha(source)
        receipts.append({"root": root, "path": relative, "old_sha256": old_sha, "new_sha256": sha(target),
                         "bytes": target.stat().st_size, "installed_utc": datetime.now(timezone.utc).isoformat()})
    receipt_path.write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"installed_this_pass": len(pending), "total_receipts": len(receipts)}))


if __name__ == "__main__":
    main()
