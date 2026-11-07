"""Preserve A6 authority before A7 packaging and local restore validation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]
A6 = REPO / "docs/maintenance/2026-11-04/meeting-lineage-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (PHASE / "BASELINE.json").exists()
    assert sha(A6 / "DELIVERY_SEAL.json") == "bafd69136024559a408d48f9af3b127582ea723eda5dbf54d62e371d55cc47fc"
    a5 = REPO / "docs/maintenance/2026-11-04/assets-package-01"
    roots = {k: Path(v) for k, v in json.loads((a5 / "BASELINE.json").read_text(encoding="utf-8"))["source_roots"].items()}
    authority = json.loads((A6 / "AUTHORITY_PROOF.json").read_text(encoding="utf-8"))["current_files"]
    backups = []
    for item in authority:
        source = roots[item["root"]] / item["path"]
        assert sha(source) == item["sha256"]
        target = PHASE / "before" / item["root"] / item["path"]
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert sha(target) == item["sha256"]
        backups.append({**item, "backup": target.relative_to(PHASE).as_posix()})
    package = REPO / ".maintenance-archive/migration/A7-20261104"
    restore = REPO / ".maintenance-archive/migration/A7-restore-20261104"
    assert not package.exists() and not restore.exists()
    disk = shutil.disk_usage(REPO)
    assert disk.free > 170 * 1024**3
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "owner_request": "执行下一步：按统一计划执行 A7",
              "previous_phase": A6.relative_to(REPO).as_posix(), "previous_seal_sha256": sha(A6 / "DELIVERY_SEAL.json"),
              "backups": backups, "source_roots": {k: str(v) for k, v in roots.items()}, "package": str(package),
              "restore_destination": str(restore), "initial_free_bytes": disk.free,
              "scope": "local final layout, incremental package, complete ordinary-file restore and link/permission handling; no server deployment",
              "server_selected": False, "original_assets_deleted_or_moved": False}
    (PHASE / "BASELINE.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    probe = PHASE / "link-probe"
    probe.mkdir()
    (probe / "target").mkdir()
    (probe / "target/file.txt").write_bytes(b"A7 isolated relative link fixture\n")
    try:
        (probe / "relative-link").symlink_to("target", target_is_directory=True)
        link = {"native_relative_symlink_creation": True, "readlink": str((probe / "relative-link").readlink()),
                "target_bytes_followed_match": (probe / "relative-link/file.txt").read_bytes() == (probe / "target/file.txt").read_bytes()}
    except OSError as error:
        link = {"native_relative_symlink_creation": False, "error": repr(error), "target_bytes_followed_match": False}
    link.update({"only_new_fixture_touched": True, "original_links_followed_or_modified": False, "WSL_started": False})
    (PHASE / "LINK_CAPABILITY.json").write_bytes((json.dumps(link, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"before_files": len(backups), "free_bytes": disk.free, "link_probe": link}, ensure_ascii=False))


if __name__ == "__main__":
    main()
