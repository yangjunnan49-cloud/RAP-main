"""Preserve the A7 authority before the authorized real-server migration."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
ROOTS = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM",
         "reports": REPO.parent / "RAP-SLAM-report", "workspace-root": REPO.parent}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = PHASE / "BASELINE.json"
    if baseline.exists():
        raise SystemExit("Baseline already exists; refusing to replace it")
    prior = REPO / "docs/maintenance/2026-11-04/delivery-restore-01/AUTHORITY_PROOF.json"
    rows = []
    for row in json.loads(prior.read_text(encoding="utf-8"))["current_files"]:
        source = ROOTS[row["root"]] / row["path"]
        data = source.read_bytes()
        observed = hashlib.sha256(data).hexdigest()
        if len(data) != row["bytes"] or observed != row["sha256"]:
            raise SystemExit(f"Current authority drift: {source}")
        dest = PHASE / "before" / row["root"] / row["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as out:
            out.write(data)
        rows.append(dict(row, backup=dest.relative_to(PHASE).as_posix()))
    packages = {}
    for name in ("A5-20261104", "A7-20261104"):
        root = REPO / ".maintenance-archive/migration" / name
        packages[name] = [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size,
                               sha256=digest(p) if p.suffix != ".tar" else None)
                          for p in sorted(root.rglob("*")) if p.is_file()]
    baseline.write_text(json.dumps({
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "owner_request": "Connect to the rented AutoDL SSH endpoint and execute the migration",
        "server": {"host": "connect.weste.seetacloud.com", "port": 23243, "user": "root"},
        "credentials_persisted": False,
        "previous_authority": str(prior.relative_to(REPO)),
        "previous_authority_sha256": digest(prior),
        "previous_delivery_sha256": digest(REPO / ".maintenance-archive/migration/A7-20261104/DELIVERY.json"),
        "backups": rows, "package_inventory": packages,
        "tar_hashes": "Bound by the sealed PACKAGE.json/DELIVERY.json; verify on the actual server",
        "authorization_scope": ["SSH/SFTP to named server", "restore complete assets and history",
                                "isolated target environment installation", "bounded migration acceptance"],
        "not_authorized": ["new research or training", "change scientific parameters or results",
                           "delete original assets", "change Git history", "purchase additional services"]
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"authority_files_preserved": len(rows), "baseline": str(baseline)}))


if __name__ == "__main__":
    main()
